import logging
import os

def setup_logger(log_file: str) -> logging.Logger:
    if not os.path.exists(os.path.dirname(log_file)):
        os.makedirs(os.path.dirname(log_file))
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def log_info(message: str) -> None:
    logger = logging.getLogger(__name__)
    logger.info(message)

def log_error(message: str) -> None:
    logger = logging.getLogger(__name__)
    logger.error(message)

def log_warning(message: str) -> None:
    logger = logging.getLogger(__name__)
    logger.warning(message)