import logging
from datetime import datetime
from unittest.mock import patch

import pytest

from workflows_manager.logger import JSONLogFormatter, get_logger


class TestJSONLogFormatter:
    @pytest.mark.parametrize('log_level, expected_text', [
        ('INFO', '{"level": "INFO", "message": "test message", "time": "2000-01-01 12:00:00", "name": "root"}'),
        ('DEBUG', '{"level": "DEBUG", "message": "test message", "time": "2000-01-01 12:00:00", "name": "root", '
                  '"filename": "test_logger.py", "lineno": 10, "funcName": "test_func"}'),
    ], ids=[
        'info level',
        'debug level',
    ])
    def test_format(self, log_level: str, expected_text: str):
        formatter = JSONLogFormatter(datefmt='%Y-%m-%d %H:%M:%S')
        formatter.log_level = log_level
        record = logging.makeLogRecord({
            'name': 'root',
            'filename': 'test_logger.py',
            'lineno': 10,
            'funcName': 'test_func',
        })
        record.msg = 'test message'
        record.levelname = log_level
        record.created = datetime.strptime('2000-01-01 12:00:00', '%Y-%m-%d %H:%M:%S').timestamp()
        assert formatter.format(record) == expected_text


class Test:
    @patch('logging.FileHandler', return_value=logging.NullHandler())
    @patch('logging.StreamHandler', return_value=logging.NullHandler())
    def test_get_logger(self, mock_steam_handler, mock_file_handler):
        logger = get_logger('info', 'file.log', 'text', 'json')

        assert logger is not None
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 2
        assert isinstance(logger.handlers[0].formatter, logging.Formatter)
        assert isinstance(logger.handlers[1].formatter, JSONLogFormatter)
        mock_steam_handler.assert_called_once()
        mock_file_handler.assert_called_once_with('file.log')
