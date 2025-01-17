import os
import time
import json
import threading
import logging
from queue import Queue
from api import app
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from db.database import Database
from config.config import Config

class LogHandler(FileSystemEventHandler):
    def __init__(self, queue, db):
        self.queue = queue
        self.db = db

    def on_modified(self, event):
        logging.debug(f"File modified: {event.src_path}")
        if event.src_path == Config.LOG_FILE_PATH:
            self.process_log_file()

    def process_log_file(self):
        logging.debug(f"Processing log file: {Config.LOG_FILE_PATH}")
        with open(Config.LOG_FILE_PATH, 'r') as file:
            lines = file.readlines()
            for line in lines:
                self.process_log_entry(line)

    def process_log_entry(self, line):
        logging.debug(f"Processing log entry: {line}")
        for entry in Config.MONITORED_LOG_ENTRIES:
            if entry in line:
                logging.debug(f"Matched entry: {entry}")
                try:
                    timestamp = line.split(' ')[0]
                    if not self.db.swing_exists(timestamp):
                        json_str = line.split(f"{entry}: ")[1]
                        swing_data = json.loads(json_str)
                        swing_data['timestamp'] = timestamp
                        filtered_data = {field: swing_data.get(field) for field in Config.JSON_FIELDS}
                        filtered_data['timestamp'] = timestamp
                        self.queue.put(filtered_data)
                        logging.debug(f"Queued swing data: {filtered_data}")
                    else:
                        logging.debug(f"Duplicate entry found for timestamp: {timestamp}")
                except (IndexError, json.JSONDecodeError) as e:
                    logging.error(f"Failed to parse log entry: {line}, error: {e}")

def database_worker(queue, db, lock):
    logging.info("Database worker started")
    while True:
        swing_data = queue.get()
        if swing_data is None:
            logging.info("Database worker received exit signal")
            break
        logging.debug(f"Inserting swing data into database: {swing_data}")
        try:
            with lock:
                db.insert_swing(swing_data)
        except Exception as e:
            logging.error(f"Error inserting swing data: {e}", exc_info=True)
        queue.task_done()

def main():
    db = Database()
    queue = Queue()
    lock = threading.Lock()
    event_handler = LogHandler(queue, db)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(Config.LOG_FILE_PATH), recursive=False)
    observer.start()

    worker_thread = threading.Thread(target=database_worker, args=(queue, db, lock))
    worker_thread.start()
    logging.info("Worker thread started")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        queue.put(None)  # Signal the worker thread to exit
        worker_thread.join()
    observer.join()

if __name__ == "__main__":
    logging.basicConfig(
        level=Config.LOG_LEVEL,  # Set to DEBUG to capture all log messages
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("swing_logger.log"),
            logging.StreamHandler()
        ]
    )
    # Run the main function in a background thread
    thread = threading.Thread(target=main)
    thread.daemon = True
    thread.start()
    logging.info("Swing logger started")

    # Run the Flask app in the main thread
    logging.info("Starting API server")
    app.run(debug=True, port=9210)