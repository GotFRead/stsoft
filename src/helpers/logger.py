# coding: utf-8

import logging
import logging.handlers
import os

terminal_logger_enable = False


def get_file_handler(filename: str, maxBytes: int = 10 * 1024 * 1024, backupCount: int = 50):
    return logging.handlers.RotatingFileHandler(
        filename, maxBytes=maxBytes, backupCount=backupCount)


def create_logger(filename, logger_name='logger', level=logging.INFO):
    global terminal_logger_enable
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s (%(module)s:%(process)d) | %(message)s', '%Y-%m-%d %H:%M:%S')
    filename = os.path.join('.', 'var', 'log', filename)
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    try:
        file_handler = get_file_handler(filename)
    except FileNotFoundError:
        file_handler = get_file_handler(filename)

    file_handler.setFormatter(formatter)
    if not terminal_logger_enable:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.addHandler(file_handler)
    terminal_logger_enable = True
    return logger
