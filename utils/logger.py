import logging
from config.settings import LOG_FILE

def get_logger(name="municipal_ai"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE)
        fmt = "%(asctime)s - %(levelname)s - %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
