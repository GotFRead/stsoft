# coding: utf-8

import logging
import logging.handlers
import os
from typing import Callable
from datetime import datetime

terminal_logger_enable = False


def get_file_handler(
    filename: str, maxBytes: int = 10 * 1024 * 1024, backupCount: int = 50
):
    return logging.handlers.RotatingFileHandler(
        filename, maxBytes=maxBytes, backupCount=backupCount
    )


def create_logger(filename, logger_name="logger", level=logging.INFO):
    global terminal_logger_enable
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s (%(module)s:%(process)d) | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    filename = os.path.join(".", "var", "log", filename)
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
    logger = add_support_function(logger)
    return logger


def add_support_function(logger):
    add_to_logger_method_start(logger)
    add_to_logger_method_complete_successful(logger)
    add_to_logger_method_caught_exception(logger)
    return logger


def add_to_logger_method_start(logger):
    def log_start(func: Callable, params):
        return logger.info(
            f"Start '{func.__name__}' with params {params}. Time - {datetime.now()}"
        )

    logger.log_start = log_start


def add_to_logger_method_complete_successful(logger):
    def log_complete(func: Callable, params):
        return logger.info(
            f"Function - '{func.__name__}' with params {params} complete success! Time - {datetime.now()}"
        )

    logger.log_complete = log_complete


def add_to_logger_method_caught_exception(logger):
    def log_exception(func: Callable, params, err: Exception):
        return logger.info(
            f"Function - '{func.__name__}' with params {params} raise exception - {err} ! Time - {datetime.now()}"
        )

    logger.log_exception = log_exception
