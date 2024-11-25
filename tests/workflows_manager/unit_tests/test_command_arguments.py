from argparse import Namespace
from unittest.mock import patch

import pytest

from workflows_manager.command_arguments import get_args, get_parameters
from workflows_manager.exceptions import InvalidParameter


class Test:
    PROGRAM_NAME = 'workflows-manager'

    def test_get_args_imports_argument(self):
        with patch('sys.argv', [self.PROGRAM_NAME, 'run', '--imports', 'path1', '--imports', 'path2', 'workflow-name']):
            args = get_args()
            expected = Namespace(
                imports=['path1', 'path2'],
                log_level='info',
                log_file=None,
                console_log_format='text',
                file_log_format='text',
                configuration_file=None,
                disable_error_codes=False,
                disable_current_path_import=False,
                parameter=None,
                string_parameter=None,
                integer_parameter=None,
                boolean_parameter=None,
                float_parameter=None,
                list_parameter=None,
                dict_parameter=None,
                status_file=None,
                action='run',
                workflow_name='workflow-name',
            )
            assert args == expected

    def test_get_args_log_level_argument(self):
        with patch('sys.argv', [self.PROGRAM_NAME, 'run', '--log-level', 'debug', 'workflow-name']):
            args = get_args()
            assert args.log_level == 'debug'
            assert args.action == 'run'

    def test_get_args_subcommand_version(self):
        with patch('sys.argv', [self.PROGRAM_NAME, 'version']):
            args = get_args()
            assert args.action == 'version'

    def test_get_args_subcommand_validate_with_workflow_name(self):
        with patch('sys.argv', [self.PROGRAM_NAME, 'validate', '--workflow-name', 'my_workflow']):
            args = get_args()
            assert args.action == 'validate'
            assert args.workflow_name == 'my_workflow'

    def test_get_args_run_subcommand_with_workflow_name_and_status_file(self):
        with patch('sys.argv', [self.PROGRAM_NAME, 'run', '--status-file', 'status.log', 'example_workflow']):
            args = get_args()
            assert args.action == 'run'
            assert args.status_file == 'status.log'
            assert args.workflow_name == 'example_workflow'

    def test_get_args_default_values(self):
        with patch('sys.argv', [self.PROGRAM_NAME, 'run', 'workflow-name']):
            args = get_args()
            assert args.log_level == 'info'
            assert args.console_log_format == 'text'
            assert args.file_log_format == 'text'
            assert args.log_file is None

    def test_get_args_disable_error_codes_flag(self):
        with patch('sys.argv', [self.PROGRAM_NAME, 'run', '--disable-error-codes', 'workflow-name']):
            args = get_args()
            assert args.disable_error_codes

    def test_get_args_invalid_log_level(self):
        with patch('sys.argv', [self.PROGRAM_NAME, '--log-level', 'verbose', 'version']):
            with pytest.raises(SystemExit):
                get_args()

    def test_get_parameters(self):
        namespace = Namespace(
            parameter=['dynamic_str:str:Dynamic String', 'dynamic_int:int:123', 'dynamic_float:float:123.456',
                       'dynamic_bool:bool:True', 'dynamic_list:list:dynamic1,dynamic2',
                       'dynamic_dict:dict:{"key": "value"}'],
            string_parameter=['string:Static String'],
            integer_parameter=['integer:42'],
            boolean_parameter=['boolean:False'],
            float_parameter=['float:3.14'],
            list_parameter=['list:1,2,3'],
            dict_parameter=['dict:{"key": "value"}'],
        )
        assert get_parameters(namespace) == {
            'dynamic_str': 'Dynamic String',
            'dynamic_int': 123,
            'dynamic_float': 123.456,
            'dynamic_bool': True,
            'dynamic_list': ['dynamic1', 'dynamic2'],
            'dynamic_dict': {'key': 'value'},
            'string': 'Static String',
            'integer': 42,
            'boolean': False,
            'float': 3.14,
            'list': ['1', '2', '3'],
            'dict': {'key': 'value'},
        }

    def test_get_parameters_error_duplicate(self):
        namespace = Namespace(
            parameter=['key:str:value', 'key:str:value'],
        )
        with pytest.raises(InvalidParameter) as exception:
            get_parameters(namespace)
            assert str(exception) == 'Duplicated parameter: key'