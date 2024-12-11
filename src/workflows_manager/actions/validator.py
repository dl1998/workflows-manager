"""
Module contains validator for the workflows configuration.
"""
import inspect
from logging import Logger
from typing import List, Dict, Any, Set

from workflows_manager import configuration
from workflows_manager import workflow
from workflows_manager.actions.misc import InstanceParameters
from workflows_manager.configuration import Workflow, StepType, StepUnion
from workflows_manager.exceptions import MissingParameter, MissingStep


class Validator:
    """
    A class to validate the workflow's configuration.

    :ivar logger: Workflow engine logger.
    :vartype logger: Logger
    :ivar workflows_configuration: The configuration of the workflows.
    :vartype workflows_configuration: configuration.Configuration
    :ivar workflow_name: The name of the workflow to run.
    :vartype workflow_name: str
    :ivar parameters: The parameters provided to the workflow from command line arguments.
    :vartype parameters: Dict[str, Any]
    """
    logger: Logger
    workflows_configuration: configuration.Configuration
    workflow_name: str
    parameters: Dict[str, Any]

    def __init__(self, logger: Logger, workflows_configuration: configuration.Configuration, workflow_name: str,
                 parameters: Dict[str, Any]):
        self.logger = logger
        self.workflows_configuration = workflows_configuration
        self.workflow_name = workflow_name
        self.parameters = parameters

    def __validate_workflow_step_parameters(self, step_configuration: configuration.WorkflowStep, parameters: Set[str]):
        """
        A method to validate the parameters of a workflow step.

        :param step_configuration: The step configuration.
        :type step_configuration: configuration.WorkflowStep
        :param parameters: The parameters provided to the step from the parent.
        :type parameters: Set[str]
        """
        self.logger.info(
            f"Validating parameters for the workflow: {step_configuration.workflow} ({step_configuration.name})")
        self.__validate_steps_parameters(self.workflows_configuration.workflows[step_configuration.workflow],
                                         parameters)

    def __validate_parallel_step_parameters(self, step_configuration: configuration.ParallelStep, parameters: Set[str]):
        """
        A method to validate the parameters of a parallel step.

        :param step_configuration: The step configuration.
        :type step_configuration: configuration.ParallelStep
        :param parameters: The parameters provided to the step from the parent.
        :type parameters: Set[str]
        """
        self.logger.info(f"Validating parameters for the parallel: ({step_configuration.name})")
        for parallel_step in step_configuration.parallels:
            self.logger.info(f"Validating parameters for the parallel step: {parallel_step.name}")
            self.__validate_step_parameters(parallel_step, parameters)

    def __validate_normal_step_parameters(self, step_configuration: configuration.NormalStep, parameters: Set[str]):
        """
        A method to validate the parameters of a normal step.

        :param step_configuration: The step configuration.
        :type step_configuration: configuration.NormalStep
        :param parameters: The parameters provided to the step from the parent.
        :type parameters: Set[str]
        """
        step_instance = workflow.steps.steps_register[step_configuration.id]
        instance_parameters = InstanceParameters.from_step(step_instance)
        initialized_parameters = {}
        for name in self.parameters:
            instance_parameter = instance_parameters[name]
            if instance_parameter:
                initialized_parameters[name] = True
        for name in parameters:
            instance_parameter = instance_parameters[name]
            if instance_parameter:
                initialized_parameters[name] = True
        for parameter in instance_parameters:
            if parameter.value != inspect.Parameter.empty:
                initialized_parameters[parameter.name] = True
        step_name = step_configuration.name
        missing_parameters = []
        for parameter in instance_parameters:
            if not initialized_parameters.get(parameter.name, False):
                missing_parameters.append(parameter.name)
        if missing_parameters:
            raise MissingParameter(f"Step '{step_name}' is missing the following parameters: {missing_parameters}")

    def __validate_step_parameters(self, step_configuration: StepUnion, parameters: Set[str]):
        """
        A method to validate the parameters of a step. It checks if all required parameters are provided.

        :param step_configuration: The step configuration.
        :type step_configuration: StepUnion
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

    def __collect_normal_steps(self, steps: configuration.Steps) -> List[configuration.NormalStep]:
        """
        A method to collect the normal steps from the provided steps (including embedded into parallel steps).

        :param steps: The list of steps from which it will collect the normal steps.
        :type steps: configuration.Steps
        :return: The normal steps.
        :rtype: List[configuration.NormalStep]
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
