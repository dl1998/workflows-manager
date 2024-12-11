"""
This module contains the classes and functions to dispatch and run workflows.
"""
import importlib
import os
import sys
from enum import Enum
from logging import getLogger, Logger
from pathlib import Path
from typing import Union, List, Dict, Any, Optional

from workflows_manager import configuration
from workflows_manager import workflow
from workflows_manager.actions.list import ListWorkflows
from workflows_manager.actions.runner import Runner
from workflows_manager.actions.validator import Validator
from workflows_manager.exceptions import UnknownOption, InvalidConfiguration

MODULE_IMPORTS_ENVIRONMENT_VARIABLE = 'WORKFLOWS_MANAGER_IMPORTS'


class DispatcherAction(Enum):
    """
    A class to represent the actions that can be performed by the dispatcher.
    """
    VALIDATE = 'validate'
    RUN = 'run'
    LIST = 'list'

    @staticmethod
    def from_str(action: str) -> 'DispatcherAction':
        """
        A method to get the dispatcher action from the provided string.

        :param action: The action to perform.
        :type action: str
        :raise UnknownOption: If the action is unknown.
        :return: The dispatcher action.
        :rtype: DispatcherAction
        """
        for dispatcher_action in DispatcherAction:
            if dispatcher_action.value == action:
                return dispatcher_action
        raise UnknownOption(f"Unknown action: {action}")


class WorkflowDispatcher:
    """
    A class to dispatch and run workflows.

    :ivar logger: Workflow engine logger.
    :vartype logger: Logger
    :ivar imports: The paths to the packages with modules.
    :vartype imports: List[Path]
    :ivar configuration: The configuration of the workflows.
    :vartype configuration: configuration.Configuration
    :ivar workflow_name: The name of the workflow to run.
    :vartype workflow_name: str
    :ivar status_file: The path to the file where the statuses of the particular steps will be stored.
    :vartype status_file: Path
    """
    logger: Logger
    imports: List[Path]
    configuration: configuration.Configuration
    workflow_name: str
    status_file: Optional[Path]
    parameters: Dict[str, Any]

    @staticmethod
    def __collect_modules_from_path(path: Path) -> List[str]:
        """
        A method to collect the modules from the provided path.

        :param path: The path to the package with modules.
        :type path: Path
        :return: The modules from the provided path.
        :rtype: List[str]
        """
        modules = []
        for root, _, files in os.walk(path):
            for file in files:
                full_path = Path(root, file)
                if full_path.suffix != '.py':
                    continue
                relative_path = str(full_path.relative_to(path))
                relative_path = relative_path.replace('.py', '')
                module_path = relative_path.replace(os.sep, '.')
                modules.append(module_path)
        return modules

    def __load_modules(self, package_path: Path):
        """
        A method to load the modules from the provided path.

        :param package_path: The path to the package with modules.
        :type package_path: Path
        """
        if not package_path.exists():
            self.logger.warning(f"Path {str(package_path)} does not exist, skipping it")
            return
        if not package_path.is_dir():
            self.logger.warning(f"Path {str(package_path)} is not a directory, skipping it")
            return
        if str(package_path) not in sys.path:
            self.logger.info(f"Adding {package_path} to sys.path")
            sys.path.append(str(package_path))
        self.logger.info(f"Importing modules from {package_path}")
        for module in self.__collect_modules_from_path(package_path):
            self.logger.info(f"Importing module {module}")
            importlib.import_module(module)
        self.logger.info(f"All modules from {package_path} have been imported")

    def __load_packages(self, import_paths: List[Path]):
        """
        A method to load the modules from the provided paths.

        :param import_paths: The paths to the packages with modules.
        :type import_paths: List[Path]
        """
        self.logger.info("Importing packages")
        for import_path in import_paths:
            self.__load_modules(import_path)
        self.logger.info("All packages have been imported")

    def validate(self):
        """
        A method to validate the configuration provided to the dispatcher.
        """
        validator = Validator(self.logger.getChild('validator'), self.configuration, self.workflow_name,
                              self.parameters)
        return validator.validate()

    def run(self):
        """
        A method to run the workflow.
        """
        is_valid = self.validate()
        if not is_valid:
            self.logger.error('Dispatcher cannot be started due to validation errors')
            return
        runner = Runner(self.logger.getChild(workflow.Step.DEFAULT_LOGGER_PREFIX), self.configuration,
                        self.workflow_name, self.parameters)
        if self.status_file:
            runner.status_file = self.status_file
        runner.run()

    def list(self):
        """
        A method to list the workflows.
        """
        list_workflows = ListWorkflows(self.logger.getChild('list'), self.configuration)
        list_workflows.list()

    def dispatch(self, action: DispatcherAction):
        """
        A method to dispatch the workflow.

        :param action: The action to perform.
        :type action: DispatcherAction
        """
        self.__load_packages(self.imports)
        if action == DispatcherAction.VALIDATE:
            self.validate()
        elif action == DispatcherAction.RUN:
            self.run()
        elif action == DispatcherAction.LIST:
            self.list()
        else:
            self.logger.error(f"Unknown action: {action}")


class ConfigurationFormat(Enum):
    """
    A class to represent the configuration file formats.
    """
    YAML = 'yaml'
    JSON = 'json'


class WorkflowDispatcherBuilder:
    """
    A class to build the workflow dispatcher.
    """
    __logger: Logger
    __disable_current_path_import: bool
    __imports: List[Path]
    __configuration_file: Path
    __configuration_file_format: ConfigurationFormat
    __workflow_name: str
    __status_file: Optional[Path]
    __parameters: Dict[str, Any]

    def __init__(self):
        self.__logger = getLogger(__name__)

    def logger(self, logger: Logger) -> 'WorkflowDispatcherBuilder':
        """
        A method to set the logger.

        :param logger: Workflow engine logger.
        :type logger: Logger
        :return: WorkflowDispatcherBuilder instance.
        :rtype: WorkflowDispatcherBuilder
        """
        self.__logger = logger
        return self

    def disable_current_path_import(self, disable: bool) -> 'WorkflowDispatcherBuilder':
        """
        A method to disable the automatic import of the modules from the current path.

        :param disable: True if the current path import should be disabled, otherwise False.
        :type disable: bool
        :return: WorkflowDispatcherBuilder instance.
        :rtype: WorkflowDispatcherBuilder
        """
        self.__disable_current_path_import = disable
        return self

    def imports(self, imports: Optional[List[str]]) -> 'WorkflowDispatcherBuilder':
        """
        A method to set the imports.

        :param imports: The paths to the packages with modules.
        :type imports: Optional[List[str]]
        :return: WorkflowDispatcherBuilder instance.
        :rtype: WorkflowDispatcherBuilder
        """
        if imports is None:
            imports = []
        self.__imports = [Path(import_path).absolute().resolve() for import_path in imports]
        return self

    def __set_default_configuration_file(self):
        """
        A method to set the default configuration file.

        :raise InvalidConfiguration: If no configuration file is found in the current path or both configuration
        files are found.
        """
        current_path = Path().absolute().resolve()
        yaml_file = current_path.joinpath('workflows.yaml')
        json_file = current_path.joinpath('workflows.json')
        if yaml_file.exists() and json_file.exists():
            raise InvalidConfiguration("Both workflows.yaml and workflows.json files found in the current path")
        if yaml_file.exists():
            self.__configuration_file = yaml_file
            self.__configuration_file_format = ConfigurationFormat.YAML
        elif json_file.exists():
            self.__configuration_file = json_file
            self.__configuration_file_format = ConfigurationFormat.JSON
        else:
            raise InvalidConfiguration("No configuration file found in the current path")

    def configuration_file(self, configuration_file: Optional[Union[str, Path]] = None) -> 'WorkflowDispatcherBuilder':
        """
        A method to set the configuration file.

        :param configuration_file: The path to the configuration file.
        :type configuration_file: Optional[Union[str, Path]]
        :return: WorkflowDispatcherBuilder instance.
        :rtype: WorkflowDispatcherBuilder
        """
        if configuration_file is None:
            self.__set_default_configuration_file()
        else:
            if isinstance(configuration_file, str):
                configuration_file = Path(configuration_file).absolute().resolve()
            self.__configuration_file = configuration_file
            if configuration_file.suffix == '.json':
                self.__configuration_file_format = ConfigurationFormat.JSON
            elif configuration_file.suffix in ['.yaml', '.yml']:
                self.__configuration_file_format = ConfigurationFormat.YAML
        return self

    def workflow_name(self, workflow_name: str) -> 'WorkflowDispatcherBuilder':
        """
        A method to set the workflow name.

        :param workflow_name: The name of the workflow to run.
        :type workflow_name: str
        :return: WorkflowDispatcherBuilder instance.
        :rtype: WorkflowDispatcherBuilder
        """
        self.__workflow_name = workflow_name
        return self

    def status_file(self, status_file: Optional[Union[str, Path]]):
        """
        A method to set the status file.

        :param status_file: The path to the file where the statuses of the particular steps will be stored.
        :type status_file: Optional[Union[str, Path]]
        :return: WorkflowDispatcherBuilder instance.
        :rtype: WorkflowDispatcherBuilder
        """
        if isinstance(status_file, str):
            status_file = Path(status_file).absolute().resolve()
        self.__status_file = status_file
        return self

    def parameters(self, parameters: Dict[str, Any]) -> 'WorkflowDispatcherBuilder':
        """
        A method to set the parameters.

        :param parameters: The parameters to set.
        :type parameters: Dict[str, Any]
        :return: WorkflowDispatcherBuilder instance.
        :rtype: WorkflowDispatcherBuilder
        """
        self.__parameters = parameters
        return self

    def __get_combined_imports(self) -> List[Path]:
        """
        A method to get the combined imports (current path, imports from the environment, and provided imports).

        :return: The combined imports.
        :rtype: List[Path]
        """
        environment_imports = os.getenv(MODULE_IMPORTS_ENVIRONMENT_VARIABLE, '')
        import_paths = [Path(path).absolute().resolve() for path in environment_imports.split(os.path.pathsep) if path]
        current_path = Path().absolute().resolve()
        if not self.__disable_current_path_import and current_path not in import_paths:
            import_paths.append(current_path)
        elif self.__disable_current_path_import:
            self.__logger.info("Import from the current path is disabled")
        for import_path in self.__imports:
            if import_path in import_paths:
                import_paths.remove(import_path)
            import_paths.append(import_path)
        return import_paths

    def build(self) -> WorkflowDispatcher:
        """
        A method to build the workflow dispatcher.
        :return: WorkflowDispatcher instance.
        :rtype: WorkflowDispatcher
        """
        dispatcher = WorkflowDispatcher()
        dispatcher.logger = self.__logger
        dispatcher.imports = self.__get_combined_imports()
        if self.__configuration_file_format == ConfigurationFormat.JSON:
            dispatcher.configuration = configuration.Configuration.from_json(self.__configuration_file)
        elif self.__configuration_file_format == ConfigurationFormat.YAML:
            dispatcher.configuration = configuration.Configuration.from_yaml(self.__configuration_file)
        else:
            raise UnknownOption(f"Unknown configuration file format: {self.__configuration_file_format}")
        dispatcher.configuration.validate_all()
        dispatcher.status_file = self.__status_file
        dispatcher.workflow_name = self.__workflow_name
        dispatcher.parameters = self.__parameters
        return dispatcher
