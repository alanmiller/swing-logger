""" Main module to start the log handler and database worker """
import argparse
import os
import json
import threading
import logging
import sqlite3
from queue import Queue
import yaml
from polling import poll
from api import app
from db.database import Database

class LogHandler():
    """ Class to handle file system events for the log file """
    def __init__(self, queue, db, config):
        self.queue = queue
        self.db = db
        self.config = config
        self.json_fields = config['json_fields']
        self.monitored_log_entries = config['monitored_log_entries']
        self.last_modified = None
        logging.debug("LogHandler initialized with config: %s", config)

    def check_file_modified(self):
        """ Check if the log file has been modified """
        try:
            modified_time = os.path.getmtime(self.config['log_file_path'])
            if self.last_modified is None or modified_time > self.last_modified:
                self.last_modified = modified_time
                logging.debug("File modified: %s", self.config['log_file_path'])
                self.on_modified()
        except FileNotFoundError:
            logging.error("Log file not found: %s", self.config['log_file_path'])

    def on_modified(self):
        """ Process the log file when it's modified """
        logging.info("Processing log file: %s", self.config['log_file_path'])
        with open(self.config['log_file_path'], 'r', encoding="utf-8") as file:
            lines = file.readlines()
            for line in lines:
                self.process_log_entry(line)

    def process_log_entry(self, line):
        """ Process a single log entry """
        logging.debug("Processing log entry: %s", line)
        for entry in self.monitored_log_entries:
            if entry in line:
                logging.debug("Matched entry: %s", entry)
                try:
                    timestamp = line.split(' ')[0]
                    logging.debug("Extracted timestamp: %s", timestamp)
                    if not self.db.swing_exists(timestamp):
                        json_str = line.split(f"{entry}: ")[1]
                        logging.debug("Extracted JSON string: %s", json_str)
                        swing_data = json.loads(json_str)
                        swing_data['timestamp'] = timestamp
                        filtered_data = {
                            field: swing_data.get(field) for field in self.json_fields
                        }
                        filtered_data['timestamp'] = timestamp
                        self.queue.put(filtered_data)
                        logging.debug("Queued swing data: %s", filtered_data)
                    else:
                        logging.debug("Duplicate entry found for timestamp: %s", timestamp)
                except (IndexError, json.JSONDecodeError) as e:
                    logging.error("Failed to parse log entry: %s error: %s", line, e)

def database_worker(queue, db, lock):
    """ Worker function to insert swing data into the database """
    logging.info("Database worker started")
    while True:
        swing_data = queue.get()
        if swing_data is None:
            logging.info("Database worker received exit signal")
            break
        logging.debug("Inserting swing data into database: %s", swing_data)
        try:
            with lock:
                db.insert_swing(swing_data)
        except sqlite3.DatabaseError as e:
            logging.error("Error inserting swing data: %s", e)
        queue.task_done()

def load_config(config_file):
    """ Load the configuration from the given file """
    with open(config_file, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
        config['log_level'] = str(config['log_level']).upper()
        return config

def main(config):
    """ Main function to start the log handler and database worker """
    db = Database()
    queue = Queue()
    lock = threading.Lock()

    event_handler = LogHandler(queue, db, config)

    worker_thread = threading.Thread(target=database_worker, args=(queue, db, lock))
    worker_thread.start()
    logging.info("Worker thread started")
    try:
        poll(event_handler.check_file_modified, step=1, poll_forever=True)
    except KeyboardInterrupt:
        queue.put(None)  # Signal the worker thread to exit
        worker_thread.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Swing Logger")
    parser.add_argument('--conf', type=str, default='config.yaml',
                        required=False, help='Path to the config file.')
    args = parser.parse_args()

    settings = load_config(args.conf)
    logging.basicConfig(
        level=getattr(logging, settings['log_level']),
        format='%(asctime)s - %(thread)d - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("swing_logger.log"),
            logging.StreamHandler()
        ]
    )

    # Run the main function in a background thread
    thread = threading.Thread(target=main, args=(settings,))
    thread.daemon = True
    thread.start()
    logging.info("Swing logger started")

    # Run the Flask app in the main thread
    logging.info("Starting API server")
    app.run(debug=False, host=settings['listen_address'], port=settings['port'])
