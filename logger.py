import logging
import sys

LOGGER_NAME = "Logger"
LOGGER_FILE_NAME = "logs.log"


def create_logger():
    """Creates a logger with settings"""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)

    # Create Formatter
    formatter = logging.Formatter(
        '%(asctime)s-%(levelname)s-FILE:%(filename)s-FUNC:%(funcName)s-LINE:%(lineno)d-%(message)s')

    # create a file handler and add it to logger
    file_handler = logging.FileHandler(LOGGER_FILE_NAME)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.ERROR)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger


logger = create_logger()
