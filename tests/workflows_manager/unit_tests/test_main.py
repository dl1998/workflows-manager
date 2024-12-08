import contextlib
import io
import logging
from argparse import Namespace
from unittest.mock import patch, MagicMock

import pytest

from workflows_manager import __version__
from workflows_manager.main import DEFAULT_STATUS_CODE, main, main_cli


class Test:
    @patch("workflows_manager.main.get_logger")
    @patch("workflows_manager.main.WorkflowDispatcherBuilder")
    @patch("workflows_manager.main.DispatcherAction.from_str")
    def test_main(self, mock_from_str, mock_dispatcher_builder, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_dispatcher = MagicMock()
        mock_dispatcher_builder.return_value.logger.return_value.disable_current_path_import.return_value.imports.return_value.configuration_file.return_value.workflow_name.return_value.status_file.return_value.parameters.return_value.build.return_value = mock_dispatcher

        mock_action = MagicMock()
        mock_from_str.return_value = mock_action

        arguments = Namespace(
            log_level='info',
            log_file='logfile.log',
            console_log_format='text',
            file_log_format='text',
            disable_current_path_import=True,
            imports=['module1', 'module2'],
            configuration_file='config.yaml',
            workflow_name='workflow1',
            status_file='status.txt',
            action='run',
            disable_error_codes=False,
            parameter=['key:str:value'],
            string_parameter=[],
            integer_parameter=[],
            boolean_parameter=[],
            float_parameter=[],
            list_parameter=[],
            dict_parameter=[],
        )

        result = main(arguments)

        mock_get_logger.assert_called_once_with('info', 'logfile.log', 'text', 'text')
        mock_logger.info.assert_any_call('Starting the workflow engine')

        mock_dispatcher_builder.assert_called_once()
        logger_mock = mock_dispatcher_builder.return_value.logger
        logger_mock.assert_called_once_with(mock_logger)
        disable_current_path_import_mock = logger_mock.return_value.disable_current_path_import
        disable_current_path_import_mock.assert_called_once_with(True)
        imports_mock = disable_current_path_import_mock.return_value.imports
        imports_mock.assert_called_once_with(['module1', 'module2'])
        configuration_file_mock = imports_mock.return_value.configuration_file
        configuration_file_mock.assert_called_once_with('config.yaml')
        workflow_name_mock = configuration_file_mock.return_value.workflow_name
        workflow_name_mock.assert_called_once_with('workflow1')
        status_file_mock = workflow_name_mock.return_value.status_file
        status_file_mock.assert_called_once_with('status.txt')
        parameters_mock = status_file_mock.return_value.parameters
        parameters_mock.assert_called_once_with({'key': 'value'})
        build_mock = parameters_mock.return_value.build
        build_mock.assert_called_once()

        mock_from_str.assert_called_once_with('run')
        mock_dispatcher.dispatch.assert_called_once_with(mock_action)

        mock_logger.info.assert_any_call('Stop the workflow engine.')
        assert result == DEFAULT_STATUS_CODE

    @pytest.mark.parametrize('logging_level', [
        'debug',
        'info',
    ], ids=[
        'debug logging enabled',
        'info logging enabled',
    ])
    @patch("workflows_manager.main.get_logger")
    @patch("workflows_manager.main.WorkflowDispatcherBuilder")
    @patch("workflows_manager.main.DispatcherAction.from_str")
    def test_main_error(self, _, mock_dispatcher_builder, mock_get_logger, logging_level: str):
        mock_logger = MagicMock()
        if logging_level == 'debug':
            mock_logger.level = logging.DEBUG
        elif logging_level == 'info':
            mock_logger.level = logging.INFO
        mock_get_logger.return_value = mock_logger
        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch.side_effect = ValueError("Test error")
        mock_dispatcher_builder.return_value.logger.return_value.disable_current_path_import.return_value.imports.return_value.configuration_file.return_value.workflow_name.return_value.status_file.return_value.build.return_value = mock_dispatcher

        arguments = Namespace(
            log_level=logging_level,
            log_file=None,
            console_log_format='json',
            file_log_format='text',
            disable_current_path_import=False,
            imports=None,
            configuration_file=None,
            workflow_name=None,
            status_file=None,
            action='validate',
            disable_error_codes=True
        )

        with pytest.raises(Exception) as exception:
            result = main(arguments)

            mock_get_logger.assert_called_once_with(logging_level, None, 'json', 'text')
            mock_logger.info.assert_any_call('Starting the workflow engine')
            if logging_level == 'debug':
                mock_logger.exception.assert_called_once_with(exception)
            elif logging_level == 'info':
                mock_logger.error.assert_called_once_with(exception)
            assert result == DEFAULT_STATUS_CODE

    @pytest.mark.parametrize('action, expected_status_code', [
        ('run', 0),
        ('validate', 1),
        ('version', 0),
    ], ids=[
        'run action with status code 0',
        'validate action with status code 1',
        'version action with status code 0',
    ])
    @patch('sys.exit')
    @patch('workflows_manager.main.get_args')
    @patch('workflows_manager.main.main')
    def test_main_cli(self, mock_main, mock_get_args, mock_exit, action: str, expected_status_code: int):
        mock_get_args.return_value = Namespace(action=action)
        mock_main.return_value = expected_status_code
        mock_exit.side_effect = SystemExit
        buffer = io.StringIO()

        with pytest.raises(SystemExit), contextlib.redirect_stdout(buffer):
            main_cli()
        stdout = buffer.getvalue()

        if action == 'version':
            assert stdout == f'v{__version__.__version__}\n'
        else:
            mock_main.assert_called_once()
        mock_get_args.assert_called_once()
        mock_exit.assert_called_once_with(expected_status_code)


