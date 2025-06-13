import logging


def setup_logger():
    logging_format = "%(asctime)s [%(levelname)s] %(message)s"

    logging.basicConfig(level=logging.INFO, format=logging_format)
    logging.basicConfig(level=logging.ERROR, format=logging_format)
    logging.basicConfig(level=logging.WARNING, format=logging_format)
