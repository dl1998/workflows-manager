"""
This module provides a logger for the workflow-engine application.
"""
import json
import logging
from typing import Optional

APPLICATION_NAME = 'workflows-manager'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class JSONLogFormatter(logging.Formatter):
    """
    A class to format the log records in JSON format.

    :ivar log_level: Logging level of the log record.
    :vartype log_level: str
    """
    log_level: str

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record in JSON format.

        :param record: Log record to be formatted.
        :type record: logging.LogRecord
        :return: Log record in JSON format.
        :rtype: str
        """
        log_record = {
            'level': record.levelname,
            'message': record.getMessage(),
            'time': self.formatTime(record, self.datefmt),
            'name': record.name,
        }
        if self.log_level.upper() == 'DEBUG':
            log_record['filename'] = record.filename
            log_record['lineno'] = record.lineno
            log_record['funcName'] = record.funcName
        return json.dumps(log_record)


def __set_formatter(handler: logging.Handler, format_type: str, log_level: str):
    """
    Set the formatter for the handler.

    :param handler: Handler for the logger.
    :type handler: logging.Handler
    :param format_type: Type of the formatter.
    :type format_type: str
    :param log_level: Logging level of the log record.
    :type log_level: str
    """
    if format_type == 'json':
        formatter = JSONLogFormatter(datefmt=LOG_DATETIME_FORMAT)
        formatter.log_level = log_level
    else:
        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATETIME_FORMAT)
    handler.setFormatter(formatter)


def get_logger(log_level: str, log_file_path: Optional[str] = None, console_format: str = 'text',
               file_format: str = 'text') -> logging.Logger:
    """
    Get the logger for the application.

    :param log_level: Logging level of the application.
    :type log_level: str
    :param log_file_path: Path to the file where the logs will be stored.
    :type log_file_path: str
    :param console_format: Format of the logs in the console.
    :type console_format: str
    :param file_format: Format of the logs in the file.
    :type file_format: str
    :return: Logger for the application.
    :rtype: logging.Logger
    """
    logger = logging.getLogger(APPLICATION_NAME)
    logger.setLevel(log_level.upper())

    console_handler = logging.StreamHandler()
    __set_formatter(console_handler, console_format, log_level)
    logger.addHandler(console_handler)

    if log_file_path:
        file_handler = logging.FileHandler(log_file_path)
        __set_formatter(file_handler, file_format, log_level)
        logger.addHandler(file_handler)

    return logger
