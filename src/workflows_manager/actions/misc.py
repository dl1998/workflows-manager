"""
Module contains additional classes and functions that are used in actions.
"""
import inspect
from dataclasses import dataclass, field
from typing import Any, Type, List, Union

from workflows_manager import workflow


@dataclass
class InstanceParameter:
    """
    A class to represent the parameter of the step instance with its default value and type.

    :ivar name: The name of the parameter.
    :vartype name: str
    :ivar value: The default value of the parameter.
    :vartype value: Any
    :ivar type: The type of the parameter.
    :vartype type: Type
    """
    name: str
    value: Any
    type: Type


@dataclass
class InstanceParameters:
    """
    A class to represent the parameters of the step instance with their default values and types.

    :ivar parameters: The parameters of the step instance.
    :vartype parameters: List[InstanceParameter]
    """
    parameters: List[InstanceParameter] = field(default_factory=list)

    @classmethod
    def from_step(cls, step: workflow.Step) -> 'InstanceParameters':
        """
        A method to create an instance of the class from the step instance.

        :param step: The step instance.
        :type step: workflow.Step
        :return: The instance of the class created from the step instance.
        :rtype: InstanceParameters
        """
        parameters = inspect.signature(step.perform).parameters
        instance_parameters = cls()
        for name, parameter in parameters.items():
            instance_parameter = InstanceParameter(name, parameter.default, parameter.annotation)
            instance_parameters.parameters.append(instance_parameter)
        return instance_parameters

    def __iter__(self):
        return iter(self.parameters)

    def __getitem__(self, item: Union[int, str]):
        if isinstance(item, int):
            return self.parameters[item]
        for parameter in self.parameters:
            if parameter.name == item:
                return parameter
        return None

    def __delitem__(self, key):
        for index, parameter in enumerate(self.parameters):
            if parameter.name == key:
                del self.parameters[index]
                return
