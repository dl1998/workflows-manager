"""
This module contains the implementation of the base components which are parsed from the workflows configuration file.
"""
import json
import re
from collections import Counter
from dataclasses import field, dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Any, Union, Dict, Callable

import yaml

from workflows_manager.exceptions import InvalidConfiguration

PARAMETER_NAME_REGEX = re.compile(r'^[a-z0-9_]+$')
WORKFLOW_NAME_REGEX = re.compile(r'^[a-z0-9_-]+$')


@dataclass
class Parameter:
    """
    Class that represents a parameter.

    :param name: Name of the parameter.
    :type name: str
    :param value: Value of the parameter.
    :type value: Optional[Any]
    :param from_context: Name of the context from which the parameter should be taken.
    :type from_context: Optional[str]
    """
    name: str
    value: Optional[Any] = field(default=None)
    from_context: Optional[str] = field(default=None)

    @classmethod
    def from_dict(cls, data: dict) -> 'Parameter':
        """
        Create a new instance of the class from the dictionary.

        :param data: Dictionary with parameter data.
        :type data: dict
        :return: New instance of the class.
        :rtype: Parameter
        """
        try:
            return cls(**data)
        except Exception as exception:
            raise InvalidConfiguration(f"Invalid parameter configuration: {exception}")

    def validate_all(self):
        """
        Validate the parameter. Check if the name is not empty, if it is not reserved, and if it matches the regex.

        :raise InvalidConfigurationException: If the parameter is not valid.
        """
        if self.name is None or self.name == '':
            raise InvalidConfiguration("Parameter name cannot be empty.")
        if self.name == 'context':
            raise InvalidConfiguration("Parameter name 'context' is reserved.")
        if PARAMETER_NAME_REGEX.match(self.name) is None:
            raise InvalidConfiguration(
                "Parameter name can contain only lowercase letters, numbers, hyphens, and underscores.")


@dataclass
class Parameters:
    """
    Class that represents a list of parameters.

    :param elements: List of parameters.
    :type elements: List[Parameter]
    """
    elements: List[Parameter] = field(default_factory=list)

    def __iter__(self):
        return iter(self.elements)

    def __getitem__(self, item: int):
        return self.elements[item]

    @classmethod
    def from_dict(cls, data: List[Dict]) -> 'Parameters':
        """
        Create a new instance of the class from the dictionary.

        :param data: Dictionary with parameters data.
        :type data: List[Dict]
        :return: New instance of the class.
        :rtype: Parameters
        """
        try:
            return cls([Parameter.from_dict(parameter) for parameter in data])
        except Exception as exception:
            raise InvalidConfiguration(f"Invalid parameters configuration: {exception}")

    def validate_all(self):
        """
        Validate all parameters in the list.
        """
        for parameter in self.elements:
            parameter.validate_all()


@dataclass
class Steps:
    """
    Class that represents a list of steps.

    :param elements: List of steps.
    :type elements: List[Step]
    """
    elements: List['Step'] = field(default_factory=list)

    def __iter__(self):
        return iter(self.elements)

    def __getitem__(self, item: int):
        return self.elements[item]

    @classmethod
    def from_dict(cls, data: List[Dict]) -> 'Steps':
        """
        Create a new instance of the class from the dictionary.

        :param data: Dictionary with steps data.
        :type data: List[Dict]
        :return: New instance of the class.
        :rtype: Steps
        """
        try:
            return cls([Step.from_dict(step) for step in data])
        except Exception as exception:
            raise InvalidConfiguration(f"Invalid steps configuration: {exception}")

    def validate_all(self):
        """
        Validate all steps in the list.
        """
        if len(self.elements) == 0:
            raise InvalidConfiguration("Steps list cannot be empty.")
        counter = Counter([step.name for step in self.elements])
        for step in self.elements:
            if counter.get(step.name) > 1:
                raise InvalidConfiguration(
                    f"Step with a name '{step.name}' occurs multiple times within the same steps context.")
            step.validate_all()


class StepType(Enum):
    """
    Enum class that represents the type of the step.
    """
    NORMAL = 'normal'
    PARALLEL = 'parallel'
    WORKFLOW = 'workflow'

    @staticmethod
    def from_str(value: str) -> 'StepType':
        """
        Convert string to StepType enum.

        :param value: String representation of the step type.
        :type value: str
        :raise InvalidConfigurationException: If the step type is not valid enum value.
        :return: StepType enum.
        :rtype: StepType
        """
        for step_type in StepType:
            if step_type.value == value:
                return step_type
        raise InvalidConfiguration("Step type must be either 'normal', 'parallel', or 'workflow'.")


@dataclass
class Step:
    """
    Class that represents a step in the workflow.

    :param name: Name of the step.
    :type name: str
    :param id: ID of the step (name of the step used when registering the step).
    :type id: Optional[str]
    :param workflow: Name of the workflow that should be executed.
    :type workflow: Optional[str]
    :param parallels: List of parallel steps.
    :type parallels: Steps
    :param type: Type of the step.
    :type type: StepType
    :param capture_stdout: Flag that indicates whether the stdout should be captured.
    :type capture_stdout: bool
    :param capture_stderr: Flag that indicates whether the stderr should be captured.
    :type capture_stderr: bool
    :param parameters: List of step parameters.
    :type parameters: Parameters
    :param stop_on_error: Flag that indicates whether the workflow should stop on error.
    :type stop_on_error: bool
    """
    name: str
    id: Optional[str] = field(default=None)
    workflow: Optional[str] = field(default=None)
    parallels: Optional['Steps'] = field(default_factory=Steps)
    type: StepType = field(default=StepType.NORMAL)
    capture_stdout: bool = field(default=False)
    capture_stderr: bool = field(default=False)
    parameters: Parameters = field(default_factory=Parameters)
    stop_on_error: bool = field(default=True)

    def __post_init__(self):
        if self.name is None or self.name == '':
            if self.id is not None and self.id != '':
                self.name = self.id
            elif self.workflow is not None and self.workflow != '':
                self.name = self.workflow

    @classmethod
    def from_dict(cls, data: dict) -> 'Step':
        """
        Create a new instance of the class from the dictionary.

        :param data: Dictionary with step data.
        :type data: dict
        :return: New instance of the class.
        :rtype: Step
        """
        try:
            return cls(**{
                'name': data.get('name'),
                'id': data.get('step'),
                'workflow': data.get('workflow'),
                'type': StepType.from_str(data.get('type', 'normal')),
                'parameters': Parameters.from_dict(data.get('parameters', [])),
                'capture_stdout': data.get('capture_stdout', False),
                'capture_stderr': data.get('capture_stderr', False),
                'stop_on_error': data.get('stop_on_error', True),
                'parallels': Steps.from_dict(data.get('parallels', []))
            })
        except Exception as exception:
            raise InvalidConfiguration(f"Invalid step configuration: {exception}")

    def validate_all(self):
        """
        Validate the step. Check if the type is valid and if the step has all required attributes.
        """
        if not self.type or self.type not in StepType:
            raise InvalidConfiguration("Step type must be either 'normal', 'parallel', or 'workflow'.")
        if self.type == StepType.PARALLEL and (self.parallels is None or len(self.parallels.elements) == 0):
            raise InvalidConfiguration("Parallel step must have 'parallels' attribute.")
        elif self.type == StepType.WORKFLOW and self.workflow is None:
            raise InvalidConfiguration("Workflow step must have 'workflow' attribute.")
        elif self.type == StepType.NORMAL and self.id is None:
            raise InvalidConfiguration("Normal step must have 'step' attribute.")
        self.parameters.validate_all()


@dataclass
class Workflow:
    """
    Class that represents a workflow.

    :param name: Name of the workflow.
    :type name: str
    :param steps: List of steps in the workflow.
    :type steps: Steps
    :param parameters: List of workflow parameters.
    :type parameters: Parameters
    """
    name: str
    steps: Steps
    parameters: Parameters = field(default_factory=Parameters)

    @classmethod
    def from_dict(cls, data: dict) -> 'Workflow':
        """
        Create a new instance of the class from the dictionary.

        :param data: Dictionary with workflow data.
        :type data: dict
        :return: New instance of the class.
        :rtype: Workflow
        """
        try:
            return cls(**{
                'name': data.get('name'),
                'steps': Steps.from_dict(data.get('steps')),
                'parameters': Parameters.from_dict(data.get('parameters', []))
            })
        except Exception as exception:
            raise InvalidConfiguration(f"Invalid workflow configuration: {exception}")

    def validate_all(self):
        """
        Validate the workflow. Check if the name is valid and if all steps and parameters are valid.
        """
        if WORKFLOW_NAME_REGEX.match(self.name) is None:
            raise InvalidConfiguration(
                "Workflow name can contain only lowercase letters, numbers, hyphens, and underscores.")
        self.parameters.validate_all()
        self.steps.validate_all()


@dataclass
class Workflows:
    """
    Class that represents a list of workflows.

    :param elements: List of workflows.
    :type elements: List[Workflow]
    """
    elements: List[Workflow]

    def __iter__(self):
        return iter(self.elements)

    def __getitem__(self, item: Union[str, int]):
        if isinstance(item, int):
            return self.elements[item]
        for workflow in self.elements:
            if workflow.name == item:
                return workflow
        return None

    @classmethod
    def from_dict(cls, data: dict) -> 'Workflows':
        """
        Create a new instance of the class from the dictionary.

        :param data: Dictionary with workflows data.
        :type data: dict
        :return: New instance of the class.
        :rtype: Workflows
        """
        try:
            return cls([Workflow.from_dict({'name': workflow, **data[workflow]}) for workflow in data])
        except Exception as exception:
            raise InvalidConfiguration(f"Invalid workflows configuration: {exception}")

    def validate_all(self):
        """
        Validate all workflows in the list.
        """
        if len(self.elements) == 0:
            raise InvalidConfiguration("Workflows list cannot be empty.")
        for workflow in self.elements:
            workflow.validate_all()


@dataclass
class Configuration:
    """
    Class that represents the configuration of the workflows.

    :param workflows: List of workflows.
    :type workflows: Workflows
    :param parameters: List of configuration level parameters.
    :type parameters: Parameters
    """
    workflows: Workflows
    parameters: Parameters = field(default_factory=Parameters)

    @classmethod
    def from_dict(cls, data: dict) -> 'Configuration':
        """
        A method that creates a new instance of the class from the dictionary.

        :param data: Dictionary with configuration data.
        :type data: dict
        :return: New instance of the class.
        :rtype: Configuration
        """
        try:
            return cls(**{
                'workflows': Workflows.from_dict(data['workflows']),
                'parameters': Parameters.from_dict(data.get('parameters', []))
            })
        except Exception as exception:
            raise InvalidConfiguration(f"Invalid configuration file: {exception}")

    @classmethod
    def __from_file(cls, file_path: Union[str, Path], parser: Callable[[Any], dict]) -> 'Configuration':
        """
        A method that creates a new instance of the class from the file.

        :param file_path: Path to the file.
        :type file_path: Union[str, Path]
        :param parser: Function that parses the file.
        :type parser: Callable[[Any], dict]
        :return: New instance of the class.
        :rtype: Configuration
        """
        if isinstance(file_path, str):
            file_path = Path(file_path).absolute()
        with Path(file_path).open('r', encoding='utf-8') as file:
            data = parser(file.read())
            return cls.from_dict(data)

    @classmethod
    def from_yaml(cls, file_path: Union[str, Path]) -> 'Configuration':
        """
        A method that creates a new instance of the class from the YAML file.

        :param file_path: Path to the YAML file.
        :type file_path: Union[str, Path]
        :return: New instance of the class.
        :rtype: Configuration
        """
        return cls.__from_file(file_path, yaml.safe_load)

    @classmethod
    def from_json(cls, file_path: Union[str, Path]) -> 'Configuration':
        """
        A method that creates a new instance of the class from the JSON file.

        :param file_path: Path to the JSON file.
        :type file_path: Union[str, Path]
        :return: New instance of the class.
        :rtype: Configuration
        """
        return cls.__from_file(file_path, json.loads)

    def validate_all(self):
        """
        A method that validates the configuration. It validates all workflows and parameters.
        """
        self.workflows.validate_all()
