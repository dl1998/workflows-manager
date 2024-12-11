import inspect
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional
from unittest.mock import patch, MagicMock

import pytest

from workflows_manager import configuration, workflow, dispatcher
from workflows_manager.dispatcher import DispatcherAction, WorkflowDispatcher, WorkflowDispatcherBuilder, \
    ConfigurationFormat
from workflows_manager.exceptions import UnknownOption, InvalidConfiguration
from actions.conftest import WORKFLOW_NAME, PARAMETERS, test_configuration
from workflows_manager.workflow import steps


@steps.register(name='new-step')
class NewStep(workflow.Step):
    def perform(self, string: str, boolean: bool, integer: int, key: str, optional=None):
        print(string)
        print(boolean, file=sys.stderr)
        error = self.workflow_context.get('error')
        if error:
            raise Exception(error)
        if optional and isinstance(optional, str):
            self.workflow_context.set('error', optional)
        return integer


class TestDispatcherAction:
    @pytest.mark.parametrize('action, expected', [
        ('validate', DispatcherAction.VALIDATE),
        ('run', DispatcherAction.RUN),
    ], ids=[
        'validate action',
        'run action',
    ])
    def test_from_str(self, action: str, expected: DispatcherAction):
        assert DispatcherAction.from_str(action) == expected

    def test_from_str_error(self):
        with pytest.raises(UnknownOption):
            DispatcherAction.from_str('')


class TestWorkflowDispatcher:
    @pytest.mark.parametrize('expected_validation_result', [
        True,
        False
    ], ids=[
        'valid configuration',
        'invalid configuration',
    ])
    @patch('workflows_manager.dispatcher.Validator.validate')
    def test_validate(self, mock_validator, test_configuration: configuration.Configuration,
                      expected_validation_result: bool):
        mock_validator.return_value = expected_validation_result
        logger = logging.getLogger('validator')
        workflow_dispatcher = WorkflowDispatcher()
        workflow_dispatcher.logger = logger
        workflow_dispatcher.imports = []
        workflow_dispatcher.configuration = test_configuration
        workflow_dispatcher.workflow_name = WORKFLOW_NAME
        workflow_dispatcher.status_file = None
        workflow_dispatcher.parameters = PARAMETERS
        assert workflow_dispatcher.validate() == expected_validation_result
        mock_validator.assert_called_once()

    @pytest.mark.parametrize('validation_result', [
        True,
        False
    ], ids=[
        'valid configuration',
        'invalid configuration',
    ])
    @patch('workflows_manager.dispatcher.Runner')
    @patch('workflows_manager.dispatcher.Validator.validate')
    def test_run(self, mock_validator, mock_runner, test_configuration: configuration.Configuration,
                 validation_result: bool):
        mock_validator.return_value = validation_result
        with patch.object(mock_runner.return_value, 'run') as mock_run:
            root_logger = logging.getLogger('workflows-manager')
            logger = root_logger.getChild(workflow.Step.DEFAULT_LOGGER_PREFIX)
            workflow_dispatcher = WorkflowDispatcher()
            workflow_dispatcher.logger = root_logger
            workflow_dispatcher.imports = []
            workflow_dispatcher.configuration = test_configuration
            workflow_dispatcher.workflow_name = WORKFLOW_NAME
            workflow_dispatcher.status_file = Path('test.json')
            workflow_dispatcher.parameters = PARAMETERS
            workflow_dispatcher.run()
            if validation_result:
                mock_runner.assert_called_once_with(logger, test_configuration, WORKFLOW_NAME, PARAMETERS)
                assert mock_runner.return_value.status_file == workflow_dispatcher.status_file
                mock_run.assert_called_once()
            else:
                mock_runner.assert_not_called()
                mock_run.assert_not_called()

    @patch('workflows_manager.dispatcher.ListWorkflows')
    def test_list(self, mock_list, test_configuration: configuration.Configuration):
        root_logger = logging.getLogger('workflows-manager')
        workflow_dispatcher = WorkflowDispatcher()
        workflow_dispatcher.logger = root_logger
        workflow_dispatcher.configuration = test_configuration
        workflow_dispatcher.workflow_name = WORKFLOW_NAME
        workflow_dispatcher.status_file = Path('test.json')
        workflow_dispatcher.imports = []
        workflow_dispatcher.list()
        mock_list.assert_called_once_with(root_logger.getChild('list'), test_configuration)
        mock_list.return_value.list.assert_called_once()

    @pytest.mark.parametrize('action', [
        DispatcherAction.VALIDATE,
        DispatcherAction.RUN,
        DispatcherAction.LIST,
        None,
    ], ids=[
        'validate action',
        'run action',
        'list action',
        'unknown action',
    ])
    @patch.object(dispatcher.WorkflowDispatcher, 'list')
    @patch.object(dispatcher.WorkflowDispatcher, 'run')
    @patch.object(dispatcher.WorkflowDispatcher, 'validate')
    def test_dispatch(self, mock_validator: MagicMock, mock_runner: MagicMock, mock_list: MagicMock,
                      test_configuration: configuration.Configuration,
                      action: DispatcherAction):
        root_logger = logging.getLogger('workflows-manager')
        workflow_dispatcher = WorkflowDispatcher()
        workflow_dispatcher.logger = root_logger
        workflow_dispatcher.configuration = test_configuration
        workflow_dispatcher.workflow_name = WORKFLOW_NAME
        workflow_dispatcher.status_file = Path('test.json')
        workflow_dispatcher.imports = []
        missing_mock_path = MagicMock()
        missing_mock_path.exists.return_value = False
        workflow_dispatcher.imports.append(missing_mock_path)
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = False
        workflow_dispatcher.imports.append(mock_path)
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True
        mock_path.__str__.return_value = '/tmp/packages'
        workflow_dispatcher.imports.append(mock_path)
        with patch('os.walk', return_value=[('/tmp/packages', None, ['file.txt', 'file.py'])]), patch(
                'importlib.import_module'), patch.object(Path, 'relative_to') as mock_path_relative_to:
            mock_path_relative_to.return_value = 'packages/file.py'
            workflow_dispatcher.dispatch(action)
        if action == DispatcherAction.LIST:
            mock_list.assert_called_once()
            mock_validator.assert_not_called()
            mock_runner.assert_not_called()
        elif action == DispatcherAction.VALIDATE:
            mock_validator.assert_called_once()
            mock_runner.assert_not_called()
            mock_list.assert_not_called()
        elif action == DispatcherAction.RUN:
            mock_validator.assert_not_called()
            mock_runner.assert_called_once()
            mock_list.assert_not_called()
        else:
            mock_validator.assert_not_called()
            mock_runner.assert_not_called()
            mock_list.assert_not_called()


def create_path_with_default_cwd(default_path: Path, original_new):
    def mock_path(cls, *args, **kwargs):
        if not args and not kwargs:
            return default_path
        else:
            return original_new(cls, *args, **kwargs)

    return mock_path


def create_mock_path_joinpath(return_values: Dict):
    def mock_joinpath(path: str):
        return return_values.get(path, MagicMock())

    return mock_joinpath


class TestWorkflowDispatcherBuilder:
    def test_logger(self):
        logger = MagicMock()
        workflow_dispatcher_builder = WorkflowDispatcherBuilder()
        returned_object = workflow_dispatcher_builder.logger(logger)
        assert returned_object == workflow_dispatcher_builder
        assert logger == inspect.getattr_static(workflow_dispatcher_builder, "_WorkflowDispatcherBuilder__logger")

    def test_disable_current_path_import(self):
        workflow_dispatcher_builder = WorkflowDispatcherBuilder()
        expected_value = True
        returned_object = workflow_dispatcher_builder.disable_current_path_import(expected_value)
        assert returned_object == workflow_dispatcher_builder
        assert expected_value == inspect.getattr_static(workflow_dispatcher_builder,
                                                        "_WorkflowDispatcherBuilder__disable_current_path_import")

    @pytest.mark.parametrize('with_imports', [
        True,
        False
    ], ids=[
        'with imports',
        'without imports',
    ])
    def test_imports(self, with_imports: bool):
        workflow_dispatcher_builder = WorkflowDispatcherBuilder()
        imports = ['./module']
        path = MagicMock()
        with patch.object(Path, 'absolute') as mock_path_absolute:
            mock_path_resolve = MagicMock()
            mock_path_resolve.resolve.return_value = path
            mock_path_absolute.return_value = mock_path_resolve
            if not with_imports:
                imports = None
            returned_object = workflow_dispatcher_builder.imports(imports)
            current_imports = inspect.getattr_static(workflow_dispatcher_builder, "_WorkflowDispatcherBuilder__imports")
            assert returned_object == workflow_dispatcher_builder
            if with_imports:
                assert [path] == current_imports
                mock_path_absolute.assert_called_once()
                mock_path_resolve.resolve.assert_called_once()
            else:
                assert [] == current_imports
                mock_path_absolute.assert_not_called()
                mock_path_resolve.resolve.assert_not_called()

    @pytest.mark.parametrize("configuration_file, json_path_exists, yaml_path_exists, configuration_format", [
        (None, True, False, ConfigurationFormat.JSON),
        (None, False, True, ConfigurationFormat.YAML),
        ('file.json', False, False, ConfigurationFormat.JSON),
        ('file.yaml', False, False, ConfigurationFormat.YAML),
        ('file.yml', False, False, ConfigurationFormat.YAML),
    ], ids=[
        'configuration file not provided, json path exists',
        'configuration file not provided, yaml path exists',
        'json configuration file provided',
        'yaml configuration file provided',
        'yml configuration file provided',
    ])
    def test_configuration_file(self, configuration_file: Optional[str], json_path_exists: bool,
                                yaml_path_exists: bool, configuration_format: ConfigurationFormat):
        workflow_dispatcher_builder = WorkflowDispatcherBuilder()
        json_path = MagicMock()
        json_path.exists.return_value = json_path_exists
        yaml_path = MagicMock()
        yaml_path.exists.return_value = yaml_path_exists
        mapping = {
            'workflows.yaml': yaml_path,
            'workflows.json': json_path,
        }
        test_cwd = '/tmp/module'
        current_path = Path(test_cwd)
        path_new = Path.__new__
        with (patch.object(Path, '__new__', new=create_path_with_default_cwd(current_path, path_new)),
              patch.object(Path, 'joinpath', side_effect=create_mock_path_joinpath(return_values=mapping)),
              patch.object(Path, 'absolute', lambda original: original),
              patch.object(Path, 'resolve', lambda original: original)):
            if configuration_file:
                configuration_file = f'{test_cwd}/{configuration_file}'
            returned_object = workflow_dispatcher_builder.configuration_file(configuration_file)
            assert returned_object == workflow_dispatcher_builder
            current_configuration_file = inspect.getattr_static(workflow_dispatcher_builder,
                                                                "_WorkflowDispatcherBuilder__configuration_file")
            current_configuration_format = inspect.getattr_static(workflow_dispatcher_builder,
                                                                  "_WorkflowDispatcherBuilder__configuration_file_format")
            if configuration_file is None:
                if json_path_exists:
                    assert current_configuration_file == json_path
                elif yaml_path_exists:
                    assert current_configuration_file == yaml_path
            else:
                assert current_configuration_file == Path(configuration_file)
            assert current_configuration_format == configuration_format

    @pytest.mark.parametrize("json_path_exists, yaml_path_exists, expected_exception", [
        (True, True, InvalidConfiguration("Both workflows.yaml and workflows.json files found in the current path")),
        (False, False, InvalidConfiguration("No configuration file found in the current path")),
    ], ids=[
        'configuration file not provided, both json and yaml paths exist',
        'configuration file not provided, neither json nor yaml paths exist',
    ])
    def test_configuration_file_error(self, json_path_exists: bool, yaml_path_exists: bool,
                                      expected_exception):
        workflow_dispatcher_builder = WorkflowDispatcherBuilder()
        json_path = MagicMock()
        json_path.exists.return_value = json_path_exists
        yaml_path = MagicMock()
        yaml_path.exists.return_value = yaml_path_exists
        mapping = {
            'workflows.yaml': yaml_path,
            'workflows.json': json_path,
        }
        with patch.object(Path, 'joinpath', side_effect=create_mock_path_joinpath(return_values=mapping)):
            with pytest.raises(InvalidConfiguration) as exception:
                workflow_dispatcher_builder.configuration_file(None)
                assert str(exception.value) == str(expected_exception)

    def test_workflow_name(self):
        workflow_dispatcher_builder = WorkflowDispatcherBuilder()
        workflow_name = 'workflow'
        returned_object = workflow_dispatcher_builder.workflow_name(workflow_name)
        assert returned_object == workflow_dispatcher_builder
        assert workflow_name == inspect.getattr_static(workflow_dispatcher_builder,
                                                       "_WorkflowDispatcherBuilder__workflow_name")

    def test_status_file(self):
        workflow_dispatcher_builder = WorkflowDispatcherBuilder()
        status_file = 'test.json'
        test_cwd = '/tmp/module'
        with (patch.object(Path, 'absolute', lambda original: Path(test_cwd).joinpath(original)),
              patch.object(Path, 'resolve', lambda original: original)):
            returned_object = workflow_dispatcher_builder.status_file(status_file)
            expected_path = Path(f'{test_cwd}/{status_file}')
            assert returned_object == workflow_dispatcher_builder
            assert expected_path == inspect.getattr_static(workflow_dispatcher_builder,
                                                           "_WorkflowDispatcherBuilder__status_file")

    @pytest.mark.parametrize("disable_import, configuration_format", [
        (True, ConfigurationFormat.YAML),
        (False, ConfigurationFormat.JSON)
    ], ids=[
        'without current path import',
        'with current path import',
    ])
    @patch('workflows_manager.dispatcher.WorkflowDispatcher')
    @patch('workflows_manager.configuration.Configuration')
    def test_build(self, mock_configuration: MagicMock, mock_dispatcher: MagicMock, disable_import: bool,
                   configuration_format: ConfigurationFormat):
        logger = logging.getLogger('noop_logger')
        test_cwd = '/private/tmp/module'
        current_path = Path(test_cwd)
        imports = [
            Path(f'{test_cwd}/present'),
            Path(f'{test_cwd}/duplicated'),
        ]
        configuration_file = MagicMock()
        status_file = Path(f'{test_cwd}/status.json')
        workflow_name = 'workflow'
        workflow_dispatcher_builder = WorkflowDispatcherBuilder()
        workflow_dispatcher_builder._WorkflowDispatcherBuilder__configuration_file = configuration_file
        workflow_dispatcher_builder._WorkflowDispatcherBuilder__configuration_file_format = configuration_format
        workflow_dispatcher_builder._WorkflowDispatcherBuilder__imports = imports
        workflow_dispatcher_builder.logger(logger)
        workflow_dispatcher_builder.disable_current_path_import(disable_import)
        workflow_dispatcher_builder.status_file(status_file)
        workflow_dispatcher_builder.workflow_name(workflow_name)
        workflow_dispatcher_builder.parameters(PARAMETERS)
        os.environ[dispatcher.MODULE_IMPORTS_ENVIRONMENT_VARIABLE] = f'{test_cwd}/duplicated:{test_cwd}/environment'
        expected_imports = [
            Path(f'{test_cwd}/environment'),
            Path(f'{test_cwd}/present'),
            Path(f'{test_cwd}/duplicated'),
        ]
        if not disable_import:
            expected_imports.insert(1, current_path)
        path_new = Path.__new__
        with (patch.object(Path, '__new__', new=create_path_with_default_cwd(current_path, path_new)),
              patch.object(Path, 'resolve', lambda original: original),
              patch.object(Path, 'absolute', lambda original: original)):
            workflow_dispatcher_builder.build()
            mock_dispatcher = mock_dispatcher()
            assert mock_dispatcher.logger == logger
            assert mock_dispatcher.imports == expected_imports
            assert mock_dispatcher.status_file == status_file
            assert mock_dispatcher.workflow_name == workflow_name
            if configuration_format == ConfigurationFormat.JSON:
                mock_configuration.from_json.assert_called_once_with(configuration_file)
            elif configuration_format == ConfigurationFormat.YAML:
                mock_configuration.from_yaml.assert_called_once_with(configuration_file)
            mock_dispatcher.configuration.validate_all.assert_called_once()

    def test_build_error(self):
        logger = logging.getLogger('noop_logger')
        workflow_dispatcher_builder = WorkflowDispatcherBuilder()
        workflow_dispatcher_builder._WorkflowDispatcherBuilder__configuration_file_format = None
        workflow_dispatcher_builder._WorkflowDispatcherBuilder__imports = []
        workflow_dispatcher_builder.logger(logger)
        workflow_dispatcher_builder.disable_current_path_import(True)
        with pytest.raises(UnknownOption) as exception:
            workflow_dispatcher_builder.build()
            assert str(exception.value) == 'Unknown configuration file format: None'
