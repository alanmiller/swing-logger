""" Main module to start the log handler and database worker """
import argparse
import threading
import logging
from logging.handlers import TimedRotatingFileHandler
from queue import Queue
import psycopg2
import yaml
from polling import poll
try:
    # Try relative imports first (for module execution)
    from .api import create_app
    from .db.shot_database import ShotDatabase
    from .db.gspro_database import GSProDatabaseHandler
except ImportError:
    # Fall back to absolute imports (for direct execution)
    from api import create_app
    from db.shot_database import ShotDatabase
    from db.gspro_database import GSProDatabaseHandler

class GSProDatabasePollingHandler():
    """ Class to handle GSPro database polling for shot data """
    def __init__(self, queue, db, config):
        self.queue = queue
        self.db = db
        self.config = config
        self.gspro_db = GSProDatabaseHandler(config)
        logging.info("GSProDatabasePollingHandler initialized")

    def check_file_modified(self):
        """ Poll GSPro database for new shot data """
        try:
            new_shots, new_rounds = self.gspro_db.check_for_new_data()
            
            for shot_data in new_shots:
                logging.info("New shot from GSPro database: Shot %s", shot_data.get('ShotNumber'))
                self.queue.put(shot_data)
                
            if new_rounds:
                logging.info("New rounds detected: %s", len(new_rounds))
                
        except Exception as e:
            logging.error("Error polling GSPro database: %s", e)

def postgres_worker(queue, db, lock):
    """ Worker function to insert swing data into PostgreSQL database """
    logging.info("Database worker started")
    while True:
        swing_data = queue.get()
        if swing_data is None:
            logging.info("Database worker received exit signal")
            break
        logging.info("Processing shot data from queue: %s", swing_data)
        try:
            with lock:
                inserted = db.insert_shot(swing_data)
                if inserted:
                    logging.info("Successfully inserted shot data into database")
                else:
                    gspro_id = swing_data.get('gspro_shot_id', 'unknown')
                    logging.debug(f"Skipped duplicate shot (gspro_shot_id: {gspro_id})")
        except psycopg2.IntegrityError as e:
            # PostgreSQL duplicate entry error
            logging.debug("Duplicate entry ignored: %s", e)
        except psycopg2.DatabaseError as e:
            logging.error("Database error inserting shot data: %s", e)
        except KeyError as e:
            logging.error("Missing required field in shot data: %s. Available fields: %s", e, list(swing_data.keys()))
        except Exception as e:
            logging.error("Unexpected error inserting shot data: %s", e)
            import traceback
            logging.error("Full traceback: %s", traceback.format_exc())
        queue.task_done()

def load_config(config_file):
    """ Load the configuration from the given file """
    with open(config_file, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
        config['log_level'] = str(config['log_level']).upper()
        return config

def main(config):
    """ Main function to start the log handler and database worker """
    try:
        logging.info("Starting swing logger with PostgreSQL storage")
        logging.info("PostgreSQL config: %s", config.get('postgres'))
            
        # Connect to PostgreSQL
        db = ShotDatabase(config)
        queue = Queue()
        lock = threading.Lock()

        # Initialize GSPro database monitoring
        event_handler = GSProDatabasePollingHandler(queue, db, config)

        worker_thread = threading.Thread(target=postgres_worker, args=(queue, db, lock))
        worker_thread.start()
        logging.info("Worker thread started")
        try:
            poll(event_handler.check_file_modified, step=1, poll_forever=True)
        except KeyboardInterrupt:
            queue.put(None)  # Signal the worker thread to exit
            worker_thread.join()
    except Exception as e:
        logging.error("Error in main function: %s", e)
        import traceback
        logging.error("Full traceback: %s", traceback.format_exc())
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Swing Logger")
    parser.add_argument('--conf', type=str, default='config.yaml',
                        required=False, help='Path to the config file.')
    args = parser.parse_args()

    settings = load_config(args.conf)
    
    # Log which config file was loaded and the database host
    print(f"Loading config from: {args.conf}")
    
    # Get log file path from config, with default fallback
    log_file_path = settings.get('log_file', 'swinglogger.log')
    
    # Set up daily rotating log handler
    file_handler = TimedRotatingFileHandler(
        log_file_path,
        when='midnight',
        interval=1,
        backupCount=30  # Keep 30 days of logs
    )
    file_handler.suffix = '%Y-%m-%d'  # Add date suffix to rotated files
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(thread)d - %(levelname)s - %(message)s'))
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(thread)d - %(levelname)s - %(message)s'))
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings['log_level']),
        handlers=[file_handler, console_handler]
    )

    # Run the main function in a background thread
    thread = threading.Thread(target=main, args=(settings,))
    thread.daemon = True
    thread.start()
    logging.info("Swing logger started - monitoring GSPro database")

    # Run the Flask app in the main thread
    addr = settings['listen_address']
    port = settings['port']
    logging.info("Starting API server on %s:%s.", addr, port)

    try:
        database = ShotDatabase(settings)
        app = create_app(database, 'postgres')
        app.run(debug=False, host=settings['listen_address'], port=settings['port'])
    except Exception as e:
        logging.error("Failed to start application: %s", e)
        import traceback
        logging.error(traceback.format_exc())
        raise
