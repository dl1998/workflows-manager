"""
Module contains the runner class that is used to run the workflow.
"""
import contextlib
import inspect
import io
import json
import sys
from logging import Logger
from pathlib import Path
from threading import Thread
from typing import List, Dict, Any, Optional

from workflows_manager import configuration
from workflows_manager import workflow
from workflows_manager.actions.misc import InstanceParameters
from workflows_manager.configuration import Workflow, Parameters, StepType, StepUnion
from workflows_manager.exceptions import MissingParameter
from workflows_manager.workflow import StepsInformation, StepStatus, StepInformation, StepPath, WorkflowContext


class ExceptionThread(Thread):
    """
    A class to run a thread that can catch exceptions.

    :ivar exception: The exception caught by the thread.
    :vartype exception: Optional[Exception]
    """
    exception: Optional[Exception]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exception = None

    def run(self):
        """
        A method to run the thread and catch exceptions.
        """
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
        except Exception as exception:
            self.exception = exception


class Runner:
    """
    A class to run the workflow.

    :ivar logger: Workflow engine logger.
    :vartype logger: Logger
    :ivar workflows_configuration: The configuration of the workflows.
    :vartype workflows_configuration: configuration.Configuration
    :ivar workflow_name: The name of the workflow to run.
    :vartype workflow_name: str
    :ivar status_file: The path to the file where the statuses of the particular steps will be stored.
    :vartype statuses_file: Optional[Path]
    :ivar parameters: The parameters provided to the workflow from command line arguments.
    :vartype parameters: Dict[str, Any]
    :ivar __workflow_context: The context of the workflow.
    :vartype __workflow_context: WorkflowContext
    """
    logger: Logger
    workflows_configuration: configuration.Configuration
    workflow_name: str
    status_file: Optional[Path]
    parameters: Dict[str, Any]
    __workflow_context: WorkflowContext

    def __init__(self, logger: Logger, workflows_configuration: configuration.Configuration, workflow_name: str,
                 parameters: Dict[str, Any]):
        self.logger = logger
        self.workflows_configuration = workflows_configuration
        self.workflow_name = workflow_name
        self.status_file = None
        self.parameters = parameters

    def __initialize_step_information(self, statuses: StepsInformation, step: StepUnion,
                                      previous_step: Optional[StepInformation] = None,
                                      parent: Optional[StepInformation] = None) -> StepInformation:
        """
        A method to initialize a step's information.

        :param statuses: The statuses of the steps.
        :type statuses: StepsInformation
        :param step: The step configuration.
        :type step: StepUnion
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

    def __initialize_steps_information(self, statuses: StepsInformation, steps: List[StepUnion],
                                       previous_step: Optional[StepInformation] = None,
                                       parent: Optional[StepInformation] = None):
        """
        A method to initialize the information of the steps in the workflow.

        :param statuses: The statuses of the steps.
        :type statuses: StepsInformation
        :param steps: The steps' configuration.
        :type steps: List[StepUnion]
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

    def __get_step_parameters(self, step: workflow.Step, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        A method to get the parameters required by the step instance.

        :param step: The step instance.
        :type step: workflow.Step
        :param parameters: The parameters provided to the step.
        :type parameters: Dict[str, Any]
        :return: The parameters required by the step instance.
        :rtype: Dict[str, Any]
        """
        instance_parameters = InstanceParameters.from_step(step)
        selected_parameters = {}
        missing_parameters = []
        for instance_parameter in instance_parameters:
            has_type = instance_parameter.type != inspect.Parameter.empty
            if instance_parameter.name in self.parameters.keys() and (not has_type or isinstance(
                    self.parameters[instance_parameter.name], instance_parameter.type)):
                selected_parameters[instance_parameter.name] = self.parameters[instance_parameter.name]
                continue
            if instance_parameter.name in parameters.keys() and (not has_type or isinstance(
                    parameters[instance_parameter.name], instance_parameter.type)):
                selected_parameters[instance_parameter.name] = parameters[instance_parameter.name]
                continue
            if instance_parameter.value != inspect.Parameter.empty:
                selected_parameters[instance_parameter.name] = instance_parameter.value
                continue
            missing_parameters.append(instance_parameter.name)
        if missing_parameters:
            raise MissingParameter(
                f"Missing the following required parameters: {missing_parameters}")
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

    def __run_normal_step(self, step: configuration.NormalStep, step_status: StepInformation,
                          parameters: Dict[str, Any]):
        """
        A method to run a normal step.

        :param step: The step configuration.
        :type step: configuration.NormalStep
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

    def __run_workflow_step(self, step: configuration.WorkflowStep, step_status: StepInformation,
                            parameters: Dict[str, Any]):
        """
        A method to run a workflow step.

        :param step: The step configuration.
        :type step: configuration.WorkflowStep
        :param step_status: The status of the step.
        :type step_status: StepInformation
        :param parameters: The parameters provided to the step.
        :type parameters: Dict[str, Any]
        """
        self.logger.info(f"Running workflow: {step.workflow}")
        self.__run_steps(self.workflows_configuration.workflows[step.workflow], parameters, step_status.path)

    def __run_parallel_steps(self, step: configuration.ParallelStep, step_status: StepInformation,
                             parameters: Dict[str, Any]):
        """
        A method to run parallel steps.

        :param step: The step configuration.
        :type step: configuration.ParallelStep
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

    def __run_step(self, step: StepUnion, parent_step_path: Optional[StepPath], parameters: Dict[str, Any]):
        """
        A method to run a step.

        :param step: The step configuration.
        :type step: StepUnion
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
            json.dump(self.__workflow_context.steps_information.to_dict(), file, indent=4)

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
