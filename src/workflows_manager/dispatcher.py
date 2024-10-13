"""
This module contains the classes and functions to dispatch and run workflows.
"""
import contextlib
import importlib
import inspect
import io
import json
import os
import sys
from pathlib import Path
from enum import Enum
from logging import getLogger, Logger
from threading import Thread
from typing import Union, List, Dict, Any, Optional, Set

import workflows_manager.configuration as configuration
import workflows_manager.workflow as workflow
from workflows_manager.configuration import Workflow, Parameters, StepType
from workflows_manager.exceptions import MissingStep, MissingParameter, UnknownOption, InvalidConfiguration
from workflows_manager.workflow import StepsInformation, StepStatus, StepInformation, StepPath, WorkflowContext

MODULE_IMPORTS_ENVIRONMENT_VARIABLE = 'WORKFLOWS_MANAGER_IMPORTS'


def get_instance_parameters(instance: workflow.Step) -> Dict[str, Any]:
    """
    A method to get the parameters of a step instance with its default values.

    :param instance: The step instance.
    :type instance: workflow.Step
    :return: The parameters of the step instance with default value.
    :rtype: Dict[str, Any]
    """
    parameters = inspect.signature(instance.perform).parameters
    instance_parameters = {}
    for name, parameter in parameters.items():
        instance_parameters[name] = parameter.default
    return instance_parameters


class ExceptionThread(Thread):
    exception: Optional[Exception]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exception = None

    def run(self):
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
        except Exception as exception:
            self.exception = exception


class DispatcherAction(Enum):
    """
    A class to represent the actions that can be performed by the dispatcher.
    """
    VALIDATE = 'validate'
    RUN = 'run'

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


class Validator:
    """
    A class to validate the workflow's configuration.

    :ivar logger: Workflow engine logger.
    :vartype logger: Logger
    :ivar workflows_configuration: The configuration of the workflows.
    :vartype workflows_configuration: configuration.Configuration
    :ivar workflow_name: The name of the workflow to run.
    :vartype workflow_name: str
    """
    logger: Logger
    workflows_configuration: configuration.Configuration
    workflow_name: str

    def __init__(self, logger: Logger, workflows_configuration: configuration.Configuration, workflow_name: str):
        self.logger = logger
        self.workflows_configuration = workflows_configuration
        self.workflow_name = workflow_name

    def __validate_workflow_step_parameters(self, step_configuration: configuration.Step, parameters: Set[str]):
        """
        A method to validate the parameters of a workflow step.

        :param step_configuration: The step configuration.
        :type step_configuration: configuration.Step
        :param parameters: The parameters provided to the step from the parent.
        :type parameters: Set[str]
        """
        self.logger.info(
            f"Validating parameters for the workflow: {step_configuration.workflow} ({step_configuration.name})")
        self.__validate_steps_parameters(self.workflows_configuration.workflows[step_configuration.workflow],
                                         parameters)

    def __validate_parallel_step_parameters(self, step_configuration: configuration.Step, parameters: Set[str]):
        """
        A method to validate the parameters of a parallel step.

        :param step_configuration: The step configuration.
        :type step_configuration: configuration.Step
        :param parameters: The parameters provided to the step from the parent.
        :type parameters: Set[str]
        """
        self.logger.info(f"Validating parameters for the parallel: ({step_configuration.name})")
        for parallel_step in step_configuration.parallels:
            self.logger.info(f"Validating parameters for the parallel step: {parallel_step.name}")
            self.__validate_step_parameters(parallel_step, parameters)

    @staticmethod
    def __validate_normal_step_parameters(step_configuration: configuration.Step, parameters: Set[str]):
        """
        A method to validate the parameters of a normal step.

        :param step_configuration: The step configuration.
        :type step_configuration: configuration.Step
        :param parameters: The parameters provided to the step from the parent.
        :type parameters: Set[str]
        """
        step_instance = workflow.steps.steps_register[step_configuration.id]
        instance_parameters = get_instance_parameters(step_instance)
        for parameter in parameters:
            try:
                instance_parameters.pop(parameter)
            except KeyError:
                continue
        parameters_to_remove = []
        for parameter, value in instance_parameters.items():
            if value != inspect.Parameter.empty:
                parameters_to_remove.append(parameter)
        for parameter in parameters_to_remove:
            instance_parameters.pop(parameter)
        if instance_parameters:
            step_name = step_configuration.name
            missing_parameters = list(instance_parameters.keys())
            raise MissingParameter(f"Step '{step_name}' is missing the following parameters: {missing_parameters}")

    def __validate_step_parameters(self, step_configuration: configuration.Step, parameters: Set[str]):
        """
        A method to validate the parameters of a step. It checks if all required parameters are provided.

        :param step_configuration: The step configuration.
        :type step_configuration: configuration.Step
        :param parameters: The parameters provided to the step from the parent.
        :type parameters: Set[str]
        """
        step_parameters = parameters | {parameter.name for parameter in step_configuration.parameters}
        if step_configuration.type == StepType.WORKFLOW:
            self.__validate_workflow_step_parameters(step_configuration, step_parameters)
        elif step_configuration.type == StepType.PARALLEL:
            self.__validate_parallel_step_parameters(step_configuration, step_parameters)
        elif step_configuration.type == StepType.NORMAL:
            self.__validate_normal_step_parameters(step_configuration, step_parameters)

    def __validate_steps_parameters(self, workflow_configuration: Workflow, parameters: Set[str]):
        """
        A method to validate the parameters of the steps in the workflow.

        :param workflow_configuration: The workflow configuration.
        :type workflow_configuration: Workflow
        :param parameters: The parameters provided to the workflow.
        :type parameters: Set[str]
        """
        step_parameters = parameters | {parameter.name for parameter in workflow_configuration.parameters}
        for step_configuration in workflow_configuration.steps:
            self.__validate_step_parameters(step_configuration, step_parameters)

    def __collect_normal_steps(self, steps: configuration.Steps) -> List[configuration.Step]:
        """
        A method to collect the normal steps from the provided steps (including embedded into parallel steps).

        :param steps: The list of steps from which it will collect the normal steps.
        :type steps: configuration.Steps
        :return: The normal steps.
        """
        normal_steps = []
        for step in steps.elements:
            if step.type == StepType.NORMAL:
                normal_steps.append(step)
            elif step.type == StepType.PARALLEL:
                normal_steps.extend(self.__collect_normal_steps(step.parallels))
        return normal_steps

    def __validate_registered_steps(self):
        """
        A method to validate if all steps from the configuration have been registered in the Steps class.
        """
        for workflow_configuration in self.workflows_configuration.workflows.elements:
            normal_steps = self.__collect_normal_steps(workflow_configuration.steps)
            for normal_step in normal_steps:
                is_step_present = normal_step.id in workflow.steps.steps_register
                if not is_step_present:
                    raise MissingStep(f"Step '{normal_step.id}' is not registered in the Steps class")

    def validate(self) -> bool:
        """
        A method to validate the configuration provided to the dispatcher.

        :return: True if the configuration is valid, otherwise False.
        :rtype: bool
        """
        is_valid = True
        self.logger.info("Validating dispatcher")
        try:
            self.__validate_registered_steps()
            if self.workflow_name:
                parameters = {param.name for param in self.workflows_configuration.parameters}
                self.logger.info(f"Validating parameters for the workflow: {self.workflow_name}")
                self.__validate_steps_parameters(self.workflows_configuration.workflows[self.workflow_name], parameters)
            self.logger.info("Parameters validated successfully")
        except Exception as exception:
            self.logger.error(f"Validation failed: {exception}")
            is_valid = False
        self.logger.info("Dispatcher validated")
        return is_valid


class Runner:
    """
    A class to run the workflow.

    :ivar logger: Workflow engine logger.
    :vartype logger: Logger
    :ivar workflows_configuration: The configuration of the workflows.
    :vartype workflows_configuration: configuration.Configuration
    :ivar workflow_context: The context of the workflow.
    :vartype workflow_context: WorkflowContext
    :ivar workflow_name: The name of the workflow to run.
    :vartype workflow_name: str
    :ivar status_file: The path to the file where the statuses of the particular steps will be stored.
    :vartype statuses_file: Optional[Path]
    """
    logger: Logger
    workflows_configuration: configuration.Configuration
    workflow_context: WorkflowContext
    workflow_name: str
    status_file: Optional[Path]

    def __init__(self, logger: Logger, workflows_configuration: configuration.Configuration, workflow_name: str):
        self.logger = logger
        self.workflows_configuration = workflows_configuration
        self.workflow_name = workflow_name
        self.status_file = None

    def __initialize_step_information(self, statuses: StepsInformation, step: configuration.Step,
                                      previous_step: Optional[StepInformation] = None,
                                      parent: Optional[StepInformation] = None) -> StepInformation:
        """
        A method to initialize a step's information.

        :param statuses: The statuses of the steps.
        :type statuses: StepsInformation
        :param step: The step configuration.
        :type step: configuration.Step
        :param previous_step: The previous step in the workflow.
        :type previous_step: Optional[StepInformation]
        :param parent: The parent step in the workflow.
        :type parent: Optional[StepInformation]
        :return: The status of the step.
        :rtype: StepInformation
        """
        parent_step_path = parent.path if parent else None
        step_path = StepPath(parent_step_path, step.type, step.name)
        step_status = StepInformation(step_path, StepStatus.NOT_STARTED, previous_step=previous_step, parent=parent)
        statuses.steps[step_path] = step_status
        if step.type == StepType.WORKFLOW:
            self.__initialize_steps_information(statuses, self.workflows_configuration.workflows[step.workflow].steps,
                                                None, step_status)
        elif step.type == StepType.PARALLEL:
            self.__initialize_steps_information(statuses, step.parallels.elements, None, step_status)
        if previous_step:
            previous_step.next_step = step_status
        if parent:
            if parent.children is None:
                parent.children = []
            parent.children.append(step_status)
        return step_status

    def __initialize_steps_information(self, statuses: StepsInformation, steps: List[configuration.Step],
                                       previous_step: Optional[StepInformation] = None,
                                       parent: Optional[StepInformation] = None):
        """
        A method to initialize the information of the steps in the workflow.

        :param statuses: The statuses of the steps.
        :type statuses: StepsInformation
        :param steps: The steps' configuration.
        :type steps: List[configuration.Step]
        :param previous_step: The previous step in the workflow.
        :type previous_step: Optional[StepInformation]
        :param parent: The parent step in the workflow.
        :type parent: Optional[StepInformation]
        """
        for step in steps:
            previous_step = self.__initialize_step_information(statuses, step, previous_step, parent)

    def __initialize_workflow_context(self):
        """
        A method to initialize the workflow context.
        """
        self.logger.info("Initializing workflow context")
        self.logger.info("Initializing steps statuses")
        statuses = StepsInformation()
        self.__initialize_steps_information(statuses, self.workflows_configuration.workflows[self.workflow_name].steps)
        self.logger.info("Steps statuses initialized")
        self.__workflow_context = WorkflowContext(steps_information=statuses)
        self.logger.info("Workflow context initialized")

    @staticmethod
    def __get_step_parameters(step: workflow.Step, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        A method to get the parameters required by the step instance.

        :param step: The step instance.
        :type step: workflow.Step
        :param parameters: The parameters provided to the step.
        :type parameters: Dict[str, Any]
        :return: The parameters required by the step instance.
        :rtype: Dict[str, Any]
        """
        instance_parameters = get_instance_parameters(step)
        selected_parameters = {}
        for parameter, value in parameters.items():
            if parameter in instance_parameters.keys():
                selected_parameters[parameter] = value
                instance_parameters.pop(parameter)
        parameters_to_remove = []
        for parameter, value in instance_parameters.items():
            if value != inspect.Parameter.empty:
                selected_parameters[parameter] = value
                parameters_to_remove.append(parameter)
        for parameter in parameters_to_remove:
            instance_parameters.pop(parameter)
        if instance_parameters:
            raise MissingParameter(
                f"Missing the following required parameters: {list(instance_parameters.keys())}")
        return selected_parameters

    def __evaluate_parameters(self, parameters: Parameters,
                              parent_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        A method to evaluate the parameters and combine them with the parent parameters.

        :param parameters: The parameters to evaluate.
        :type parameters: Parameters
        :param parent_parameters: The parent parameters.
        :type parent_parameters: Optional[Dict[str, Any]]
        :return: The evaluated parameters.
        :rtype: Dict[str, Any]
        """
        evaluated_parameters = {}
        parent_parameters = parent_parameters or {}
        for parameter, value in parent_parameters.items():
            evaluated_parameters[parameter] = value
        for parameter in parameters:
            if parameter.from_context:
                value = self.__workflow_context.get(parameter.from_context, parameter.value)
                evaluated_parameters[parameter.name] = value
            else:
                evaluated_parameters[parameter.name] = parameter.value
        return evaluated_parameters

    def __run_normal_step(self, step: configuration.Step, step_status: StepInformation, parameters: Dict[str, Any]):
        """
        A method to run a normal step.

        :param step: The step configuration.
        :type step: configuration.Step
        :param step_status: The status of the step.
        :type step_status: StepInformation
        :param parameters: The parameters provided to the step.
        :type parameters: Dict[str, Any]
        """
        self.logger.info(f"Running step: {step.name}")
        step_instance = workflow.steps.steps_register[step.id]
        step_instance.workflow_context = self.__workflow_context
        step_instance.path = step_status.path
        step_status.parameters = self.__get_step_parameters(step_instance, parameters)
        step_instance.configure_logger()
        captured_stdout = io.StringIO() if step.capture_stdout else sys.stdout
        captured_stderr = io.StringIO() if step.capture_stderr else sys.stderr
        try:
            with (contextlib.redirect_stdout(captured_stdout) if step.capture_stdout else contextlib.nullcontext(),
                  contextlib.redirect_stderr(captured_stderr) if step.capture_stderr else contextlib.nullcontext()):
                step_instance.perform(**step_status.parameters)
            self.logger.info(f"Step '{step.name}' finished")
        finally:
            if step.capture_stdout:
                step_status.stdout = captured_stdout.getvalue()
            if step.capture_stderr:
                step_status.stderr = captured_stderr.getvalue()

    def __run_workflow_step(self, step: configuration.Step, step_status: StepInformation, parameters: Dict[str, Any]):
        """
        A method to run a workflow step.

        :param step: The step configuration.
        :type step: configuration.Step
        :param step_status: The status of the step.
        :type step_status: StepInformation
        :param parameters: The parameters provided to the step.
        :type parameters: Dict[str, Any]
        """
        self.logger.info(f"Running workflow: {step.workflow}")
        self.__run_steps(self.workflows_configuration.workflows[step.workflow], parameters, step_status.path)

    def __run_parallel_steps(self, step: configuration.Step, step_status: StepInformation, parameters: Dict[str, Any]):
        """
        A method to run parallel steps.

        :param step: The step configuration.
        :type step: configuration.Step
        :param step_status: The status of the step.
        :type step_status: StepInformation
        :param parameters: The parameters provided to the step.
        :type parameters: Dict[str, Any]
        """
        self.logger.info("Running parallel steps")
        parallel_threads = []
        for parallel_step in step.parallels:
            thread = ExceptionThread(target=self.__run_step, name=f'{step.name}-{parallel_step.name}',
                                     args=(parallel_step, step_status.path, parameters))
            parallel_threads.append(thread)
            thread.start()
        for thread in parallel_threads:
            thread.join()
            if thread.exception:
                raise thread.exception

    def __run_step(self, step: configuration.Step, parent_step_path: Optional[StepPath], parameters: Dict[str, Any]):
        """
        A method to run a step.

        :param step: The step configuration.
        :type step: configuration.Step
        :param parent_step_path: The path to the parent step.
        :type parent_step_path: Optional[StepPath]
        :param parameters: The parameters provided to the step.
        :type parameters: Dict[str, Any]
        """
        step_path = StepPath(parent_step_path, step.type, step.name)
        step_status = self.__workflow_context.get_step_information(step_path)
        step_status.status = StepStatus.RUNNING
        evaluated_parameters = self.__evaluate_parameters(step.parameters, parameters)
        try:
            if step.type == StepType.NORMAL:
                self.__run_normal_step(step, step_status, evaluated_parameters)
            elif step.type == StepType.WORKFLOW:
                self.__run_workflow_step(step, step_status, evaluated_parameters)
            elif step.type == StepType.PARALLEL:
                self.__run_parallel_steps(step, step_status, evaluated_parameters)
            if step_status.status == StepStatus.RUNNING:
                step_status.status = StepStatus.SUCCESS
        except Exception as exception:
            if step_status.status == StepStatus.RUNNING:
                step_status.status = StepStatus.FAILED
            step_status.error = str(exception)
            self.logger.error(f"Step '{step.name}' failed")
            if step.stop_on_error:
                raise exception

    def __run_steps(self, workflow_configuration: Workflow, parameters: Dict[str, Any],
                    parent_step_path: Optional[StepPath] = None):
        """
        A method to run the steps in the workflow.

        :param workflow_configuration: The workflow configuration.
        :type workflow_configuration: Workflow
        :param parameters: The parameters provided to the workflow.
        :type parameters: Dict[str, Any]
        :param parent_step_path: The path to the parent step.
        :type parent_step_path: Optional[StepPath]
        """
        for step in workflow_configuration.steps:
            try:
                self.__run_step(step, parent_step_path, parameters)
            except Exception as exception:
                if step.stop_on_error:
                    self.logger.error("Stopping workflow due to error")
                    raise exception

    def __generate_status_file(self):
        """
        A method to generate the status file.
        """
        with self.status_file.open('w', encoding='utf-8') as file:
            json.dump(self.__workflow_context.steps_information.dict(), file, indent=4)

    def run(self):
        """
        A method to run the workflow.
        """
        self.__initialize_workflow_context()
        workflow_configuration = self.workflows_configuration.workflows[self.workflow_name]
        self.logger.info(f"Running workflow: {workflow_configuration.name}")
        parameters = self.__evaluate_parameters(self.workflows_configuration.parameters)
        parameters = self.__evaluate_parameters(workflow_configuration.parameters, parameters)
        try:
            self.__run_steps(workflow_configuration, parameters)
        except Exception as exception:
            self.logger.error(f"Workflow failed: {exception}")
        self.logger.info("Workflow finished")
        if self.status_file:
            self.logger.info(f"Generating status file: {self.status_file}")
            self.__generate_status_file()
            self.logger.info("Status file generated")


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
        validator = Validator(self.logger.getChild('validator'), self.configuration, self.workflow_name)
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
                        self.workflow_name)
        if self.status_file:
            runner.status_file = self.status_file
        runner.run()

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
        elif yaml_file.exists():
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
                configuration_file = Path(configuration_file).absolute()
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

    def status_file(self, status_file: Union[str, Path]):
        """
        A method to set the status file.

        :param status_file: The path to the file where the statuses of the particular steps will be stored.
        :type status_file: Union[str, Path]
        :return: WorkflowDispatcherBuilder instance.
        :rtype: WorkflowDispatcherBuilder
        """
        if isinstance(status_file, str):
            status_file = Path(status_file).absolute()
        self.__status_file = status_file
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
        return dispatcher
