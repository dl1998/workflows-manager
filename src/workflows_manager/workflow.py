"""
This module contains the implementation of the base components which are Workflow and Step classes.
"""
import functools
import threading
from dataclasses import dataclass, field
from enum import Enum
from logging import Logger, getLogger, DEBUG
from threading import Lock
from typing import Any, Dict, Optional, List, Type, Callable

from workflows_manager.configuration import StepType
from workflows_manager.logger import APPLICATION_NAME


class StepStatus(Enum):
    """
    A class to represent the status of a step in a workflow.
    """
    UNKNOWN = 'unknown'
    NOT_STARTED = 'not_started'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'


class StepPath:
    """
    A class to represent the path to a step in a workflow.
    """

    __path: Optional['StepPath']
    __step_type: StepType
    __step_name: str

    def __init__(self, path: Optional['StepPath'], step_type: StepType, step_name: str):
        self.__path = path
        self.__step_type = step_type
        self.__step_name = step_name

    @property
    def type(self) -> StepType:
        """
        A property to get the type of the step.
        """
        return self.__step_type

    @property
    def name(self) -> str:
        """
        A property to get the name of the step.
        """
        return self.__step_name

    def __hash__(self):
        return hash((self.__path, self.__step_type, self.__step_name))

    def __eq__(self, other: Optional['StepPath']) -> bool:
        if self is None or other is None:
            return False
        else:
            is_path_match = self.__path == other.__path
            is_step_type_match = self.__step_type == other.__step_type
            is_step_name_match = self.__step_name == other.__step_name
            return is_path_match and is_step_type_match and is_step_name_match


@dataclass
class StepInformation:
    """
    A class to represent the information of a step in a workflow.

    :param path: The path to the step.
    :type path: StepPath
    :param status: The status of the step.
    :type status: StepStatus
    :param parameters: The parameters of the step.
    :type parameters: Optional[Dict]
    :param stdout: The standard output of the step.
    :type stdout: Optional[str]
    :param stderr: The standard error of the step.
    :type stderr: Optional[str]
    :param error: The error (exception) of the step.
    :type error: Optional[Exception]
    :param return_value: The return value of the step.
    :type return_value: Optional[Any]
    :param previous_step: The previous step in the workflow.
    :type previous_step: Optional[StepInformation]
    :param next_step: The next step in the workflow.
    :type next_step: Optional[StepInformation]
    :param parent: The parent step in the workflow.
    :type parent: Optional[StepInformation]
    :param children: The children steps in the workflow.
    :type children: Optional[List[StepInformation]]
    """
    path: StepPath
    status: StepStatus
    parameters: Optional[Dict] = field(default=None)
    stdout: Optional[str] = field(default=None)
    stderr: Optional[str] = field(default=None)
    error: Optional[Exception] = field(default=None)
    return_value: Optional[Any] = field(default=None)
    previous_step: Optional['StepInformation'] = field(default=None)
    next_step: Optional['StepInformation'] = field(default=None)
    parent: Optional['StepInformation'] = field(default=None)
    children: Optional[List['StepInformation']] = field(default=None)

    def dict(self) -> List[Dict]:
        """
        A method to convert the step information to a dictionary.

        :return: The step information as a dictionary.
        :rtype: List[Dict]
        """
        steps = []
        step = self
        while step:
            children = None
            if step.children and step.path.type == StepType.PARALLEL:
                children = []
                for child in step.children:
                    children.append(child.dict()[0])
            elif step.children and step.path.type == StepType.WORKFLOW:
                children = step.children[0].dict()
            data = {
                'type': step.path.type.value,
                'name': step.path.name,
                'status': step.status.value,
                'parameters': step.parameters,
                'stdout': step.stdout,
                'stderr': step.stderr,
                'error': str(step.error) if step.error else None,
                'return_value': step.return_value,
                'children': children,
            }
            steps.append(data)
            step = step.next_step
        return steps


@dataclass
class StepsInformation:
    """
    A class to represent the information of all steps in a workflow.

    :param steps: The dictionary of steps in the workflow.
    :type steps: Dict[StepPath, StepInformation]
    """
    steps: Dict[StepPath, StepInformation] = field(default_factory=dict)

    def get_step_information(self, step_path: StepPath) -> StepInformation:
        """
        A method to get the status of a step in the workflow.

        :param step_path: The path to the step.
        :type step_path: StepPath
        :return: The status of the step.
        :rtype: StepInformation
        """
        for key in self.steps.keys():
            if key == step_path:
                return self.steps[key]
        return StepInformation(path=step_path, status=StepStatus.UNKNOWN)

    @property
    def first_step(self) -> Optional[StepInformation]:
        """
        A property to get the first step in the workflow.

        :return: The first step in the workflow.
        :rtype: Optional[StepInformation]
        """
        for step in self.steps.values():
            if step.previous_step is None and step.parent is None:
                return step
        return None

    def dict(self) -> Dict:
        """
        A method to convert the steps information to a dictionary.

        :return: The steps information as a dictionary.
        :rtype: Dict
        """
        return {
            'steps': self.first_step.dict()
        }


class WorkflowContext:
    """
    A class to represent the context of a workflow. Context is a dictionary that stores the state of the workflow that
    is shared between steps.

    :param parameters: The parameters of the workflow.
    :type parameters: Optional[Dict]
    :param steps_information: The status of the steps in the workflow.
    :type steps_information: Optional[StepsInformation]
    """
    __lock: Lock
    __workflow_parameters: Dict
    __steps_information: StepsInformation

    def __init__(self, parameters: Optional[Dict] = None, steps_information: Optional[StepsInformation] = None):
        self.__lock = threading.Lock()
        if parameters is None:
            parameters = {}
        self.__workflow_parameters = parameters
        if steps_information is None:
            steps_information = StepsInformation()
        self.__steps_information = steps_information

    def get(self, key: str, default: Any = None) -> Any:
        """
        A method to get a value from the context.

        :param key: The key of the value to get from the context.
        :type key: str
        :param default: The default value to return if the key is not found in the context.
        :type default: Any
        :return: Value from the context, if the key is found, otherwise the default value.
        :rtype: Any
        """
        return self.__workflow_parameters.get(key, default)

    def set(self, key: str, value: Any):
        """
        A method to set a value to the context.

        :param key: The key of the value to set in the context.
        :type key: str
        :param value: The value to set in the context.
        :type value: Any
        """
        with self.__lock:
            self.__workflow_parameters[key] = value

    def get_step_information(self, step: StepPath) -> StepInformation:
        """
        A method to get the status of a step in the workflow.

        :param step: The path to the step.
        :type step: StepPath
        :return: The status of the step.
        :rtype: StepInformation
        """
        return self.__steps_information.get_step_information(step)

    @property
    def steps_information(self) -> StepsInformation:
        """
        A property to get the status of all steps in the workflow.
        """
        return self.__steps_information

    @property
    def global_lock(self) -> Lock:
        """
        A property to get the global lock of the workflow.
        """
        return self.__lock


class Step:
    """
    A class to represent a step instance that performs a specific task in a workflow.

    :param name: The name of the step (it's ID).
    :type name: str
    :ivar logger: The logger of the step.
    :vartype logger: Logger
    :ivar workflow_context: The context of the workflow.
    :vartype workflow_context: WorkflowContext
    :ivar path: The path to the step.
    :vartype step_path: StepPath
    :ivar name: The name of the step (it's ID).
    :vartype name: str
    """
    DEFAULT_LOGGER_PREFIX = 'runner'
    logger: Logger
    workflow_context: WorkflowContext
    path: StepPath
    name: str

    def __init__(self, name: str = ''):
        self.name = name

    @property
    def default_logger_name(self) -> str:
        """
        A property to get the default name of the logger that is composed of the default logger prefix and the name of
        the step.
        """
        return f'{APPLICATION_NAME}.{self.DEFAULT_LOGGER_PREFIX}.{self.name}'

    @property
    def information(self) -> StepInformation:
        """
        A property to get the information about the step.
        """
        return self.workflow_context.get_step_information(self.path)

    def configure_logger(self):
        """
        A method to configure the logger of the step.
        """
        self.logger = getLogger(self.default_logger_name)

    def perform(self, *args, **kwargs) -> Any:
        """
        A method to perform the task of the step.

        :param args: The positional arguments of the step.
        :param kwargs: The keyword arguments of the step.
        :raise NotImplementedError: The method 'perform' must be implemented in the child class.
        :return: The return value of the step.
        :rtype: Any
        """
        raise NotImplementedError("The method 'perform' must be implemented in the child class.")

    def __update_status(self, step_status: StepStatus):
        """
        A method to update the status of the step.

        :param step_status: The new status of the step.
        :type step_status: StepStatus
        """
        self.information.status = step_status

    def success(self):
        """
        A method to set the status of the step to 'success'.
        """
        self.__update_status(StepStatus.SUCCESS)

    def fail(self):
        """
        A method to set the status of the step to 'failed'.
        """
        self.__update_status(StepStatus.FAILED)


class Steps:
    """
    A class to manage the steps in the workflow.
    """
    steps_register: Dict[str, Step]

    def __init__(self):
        self.steps_register = {}

    def register(self, name: str) -> Callable[[Type[Step]], None]:
        """
        A method to register a step in the workflow.

        :param name: The name of the step.
        :type name: str
        :return: The class wrapper.
        :rtype: Callable[[Type[Step]], None]
        """

        def class_wrapper(cls: Type[Step]):
            """
            A function to wrap the class of the step.

            :param cls: The class of the step.
            :type cls: Type[Step]
            :return: The wrapped class of the step.
            """
            instance = cls(name)
            instance.perform = self.wrap_step(instance)(instance.perform)
            self.steps_register[name] = instance

        return class_wrapper

    @staticmethod
    def wrap_step(self: Step):
        """
        A method to wrap the step.

        :param self: The step to wrap.
        :type self: Step
        :return: The wrapped step.
        """

        def function_wrapper(function):
            """
            A function to wrap the function of the step.

            :param function: The function of the step.
            :type function: Any
            :return: The wrapped function of the step.
            :rtype: Any
            """

            @functools.wraps(function)
            def wrapper(*args, **kwargs):
                """
                A function to wrap the execution of the step. It sets the status of the step to 'success' if the step
                completes successfully, otherwise it sets the status of the step to 'failed'.

                :param args: The positional arguments of the step.
                :param kwargs: The keyword arguments of the step.
                :raise Exception: If step fails, it raises an exception.
                :return: The return value of the step.
                :rtype: Any
                """
                try:
                    self.information.return_value = function(*args, **kwargs)
                    if self.information.status not in [StepStatus.FAILED, StepStatus.SUCCESS]:
                        self.information.status = StepStatus.SUCCESS
                except Exception as exception:
                    if self.logger.level == DEBUG:
                        self.logger.exception(exception)
                    if self.information.status not in [StepStatus.FAILED, StepStatus.SUCCESS]:
                        self.information.status = StepStatus.FAILED
                    self.information.error = exception
                    raise exception

            return wrapper

        return function_wrapper


steps: Steps = Steps()
