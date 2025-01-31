""" Main module to start the log handler and database worker """
# Compilation mode, support OS-specific options
# nuitka-project-if: {OS} in ("Windows", "Linux", "FreeBSD"):
#    nuitka-project: --onefile
# nuitka-project-if: {OS} in ("Darwin"):
#   nuitka-project: --mode=app
# nuitka-project-else:
#    nuitka-project: --mode=standalonealone
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/../config.yaml=config.yaml
# nuitka-project: --file-description=swinglogger
# nuitka-project: --file-version=1.0
# nuitka-project: --product-name=Swing-Logger
# nuitka-project: --product-version=1.0.0.0

import argparse
import os
import json
import threading
import logging
import sqlite3
from queue import Queue
import pymysql
import yaml
from polling import poll
from api import create_app
from db.database import Database
from db.shot_database import ShotDatabase

class LMHandler():
    """ Class to handle file system events for the log file """
    def __init__(self, queue, db, config):
        self.queue = queue
        self.db = db
        self.config = config
        self.json_fields = config['json_fields']
        self.monitored_log_entries = config['monitored_log_entries']
        self.last_modified = None
        logging.debug("LMHandler initialized with config: %s", config)

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
                        logging.debug("Duplicate entry for timestamp: %s", timestamp)
                except (IndexError, json.JSONDecodeError) as e:
                    logging.error("Failed to parse log entry: %s error: %s", line, e)

class GSProHandler():
    """ Class to handle file system events for the log file """
    def __init__(self, queue, db, config):
        self.queue = queue
        self.db = db
        self.config = config
        self.last_modified = None
        self.log_file_path = self.config['gspro']['log_file_path']
        logging.debug("GSProHandler initialized with config: %s", config)

    def check_file_modified(self):
        """ Check if the log file has been modified """
        try:
            modified_time = os.path.getmtime(self.log_file_path)
            if self.last_modified is None or modified_time > self.last_modified:
                self.last_modified = modified_time
                logging.debug("File modified: %s", self.log_file_path)
                self.on_modified()
        except FileNotFoundError:
            logging.error("Log file not found: %s", self.log_file_path)

    def on_modified(self):
        """ Process the log file when it's modified """
        logging.info("Processing log file: %s", self.log_file_path)
        with open(self.log_file_path, 'r', encoding="utf-8") as file:
            lines = file.readlines()
            for line in lines:
                self.process_log_entry(line)

    def process_log_entry(self, line):
        """ Process a single log entry """
        logging.debug("Processing log entry: %s", line)
        try:
            # Remove any leading/trailing whitespace
            line = line.strip()
            if 'ShotKey' in line and 'BallData' in line:
                # Parse the JSON string into a Python dictionary
                shot_data = json.loads(line)
                # Validate that this is a shot entry
                if 'ShotKey' in shot_data and 'BallData' in shot_data:
                    self.queue.put(shot_data)
                    logging.debug("Queued swing: %s", shot_data['ShotKey'])
                else:
                    print("Line does not contain valid shot data")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

def mysql_worker(queue, db, lock):
    """ Worker function to insert swing data into mysql database """
    logging.info("Database worker started")
    while True:
        swing_data = queue.get()
        if swing_data is None:
            logging.info("Database worker received exit signal")
            break
        logging.debug("Inserting shot data into database: %s", swing_data)
        try:
            with lock:
                db.insert_shot(swing_data)
        except pymysql.err.IntegrityError as e:
            if e.args[0] == 1062:  # MySQL error code for duplicate entry
                # silently ignore
                pass
            else:
                logging.error("Error inserting shot data: %s", e)
        except pymysql.DatabaseError as e:
            logging.error("Error inserting shot data: %s", e)
        queue.task_done()

def sqlite_worker(queue, db, lock):
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
    # if using mysql for long term storage, connect and initialize it here
    if config['data_store'] == 'mysql':
        db = ShotDatabase(config)
    else:
        db = Database()
    queue = Queue()
    lock = threading.Lock()

    # which file we are monitoring
    if config['data_source'] == 'gspro':
        event_handler = GSProHandler(queue, db, config)
        target=mysql_worker
    else:
        event_handler = LMHandler(queue, db, config)
        target=sqlite_worker

    worker_thread = threading.Thread(target=target, args=(queue, db, lock))
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
    logging.info("Swing logger started in %s mode.", settings['data_source'])

    # Run the Flask app in the main thread
    addr = settings['listen_address']
    port = settings['port']
    logging.info("Starting API server on %s:%s.", addr, port)

    if settings['data_store'] == 'mysql':
        database = ShotDatabase(settings)
        app = create_app(database,'mysql')
    else:
        database = Database()
        app = create_app(database,'sqlite')
    app.run(debug=False, host=settings['listen_address'], port=settings['port'])
