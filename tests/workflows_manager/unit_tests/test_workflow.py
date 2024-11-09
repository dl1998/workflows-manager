import logging
from typing import Optional, List, Dict, Callable, Tuple

import pytest

from workflows_manager.configuration import StepType
from workflows_manager.workflow import StepPath, StepInformation, StepStatus, StepsInformation, WorkflowContext, Step, Steps


@pytest.fixture
def steps_information():
    workflow_step_path = StepPath(None, StepType.WORKFLOW, 'workflow_step')
    workflow_step = StepInformation(path=workflow_step_path, status=StepStatus.RUNNING)
    normal_step_path = StepPath(workflow_step_path, StepType.NORMAL, 'normal_step')
    normal_step = StepInformation(path=normal_step_path, status=StepStatus.FAILED)
    parallel_step_path = StepPath(workflow_step_path, StepType.PARALLEL, 'parallel_step')
    parallel_step = StepInformation(path=parallel_step_path, status=StepStatus.SUCCESS)
    parallel_child_step_path = StepPath(parallel_step_path, StepType.NORMAL, 'parallel_child_step')
    parallel_child_step = StepInformation(path=parallel_child_step_path, status=StepStatus.UNKNOWN)
    workflow_step.children = [normal_step, parallel_step]
    normal_step.parent = workflow_step
    parallel_child_step.parent = parallel_step
    parallel_step.children = [parallel_child_step]
    parallel_child_step.parent = parallel_step
    normal_step.next_step = parallel_step
    parallel_step.previous_step = workflow_step
    steps_information = StepsInformation()
    steps_information.steps[workflow_step.path] = workflow_step
    steps_information.steps[normal_step.path] = normal_step
    steps_information.steps[parallel_step.path] = parallel_step
    steps_information.steps[parallel_child_step.path] = parallel_child_step
    return steps_information


@pytest.fixture
def workflow_context(steps_information: StepsInformation):
    return WorkflowContext(steps_information=steps_information)


@pytest.fixture
def steps_information_dictionary():
    return [
        {
            'type': StepType.WORKFLOW.value,
            'name': 'workflow_step',
            'status': StepStatus.RUNNING.value,
            'parameters': None,
            'stdout': None,
            'stderr': None,
            'error': None,
            'return_value': None,
            'children': [
                {
                    'type': StepType.NORMAL.value,
                    'name': 'normal_step',
                    'status': StepStatus.FAILED.value,
                    'parameters': None,
                    'stdout': None,
                    'stderr': None,
                    'error': None,
                    'return_value': None,
                    'children': None,
                },
                {
                    'type': StepType.PARALLEL.value,
                    'name': 'parallel_step',
                    'status': StepStatus.SUCCESS.value,
                    'parameters': None,
                    'stdout': None,
                    'stderr': None,
                    'error': None,
                    'return_value': None,
                    'children': [
                        {
                            'type': StepType.NORMAL.value,
                            'name': 'parallel_child_step',
                            'status': StepStatus.UNKNOWN.value,
                            'parameters': None,
                            'stdout': None,
                            'stderr': None,
                            'error': None,
                            'return_value': None,
                            'children': None,
                        }
                    ]
                }
            ]
        }
    ]


class TestStepPath:
    def test_type(self):
        step_path = StepPath(None, StepType.NORMAL, 'step')
        assert step_path.type == StepType.NORMAL

    def test_name(self):
        step_path = StepPath(None, StepType.NORMAL, 'step')
        assert step_path.name == 'step'

    def test_hash(self):
        step_path = StepPath(None, StepType.NORMAL, 'step')
        assert step_path.__hash__() == hash((None, StepType.NORMAL, 'step'))

    @pytest.mark.parametrize(
        'path1, path2, expected',
        [
            (StepPath(None, StepType.NORMAL, 'step'), StepPath(None, StepType.NORMAL, 'step'), True),
            (None, StepPath(None, StepType.NORMAL, 'step'), False),
            (StepPath(None, StepType.NORMAL, 'step'), StepPath(None, StepType.WORKFLOW, 'step'), False),
            (StepPath(None, StepType.NORMAL, 'step'), StepPath(None, StepType.NORMAL, 'step1'), False),
            (StepPath(None, StepType.NORMAL, 'step'),
             StepPath(StepPath(None, StepType.WORKFLOW, 'parent'), StepType.NORMAL, 'step'), False),
        ], ids=[
            'both paths are the same',
            'first path is None',
            'types of paths are different',
            'names of paths are different',
            'parents of the paths are different'
        ]
    )
    def test_eq(self, path1: Optional[StepPath], path2: Optional[StepPath], expected: bool):
        is_equal = path1 == path2
        assert is_equal == expected


class TestStepInformation:
    def test_dict(self, steps_information: StepsInformation, steps_information_dictionary: List[Dict]):
        step_information = steps_information.steps[StepPath(None, StepType.WORKFLOW, 'workflow_step')]
        assert step_information.dict() == steps_information_dictionary


class TestStepsInformation:
    def test_get_step_status(self, steps_information: StepsInformation):
        step_path = StepPath(None, StepType.WORKFLOW, 'workflow_step')
        assert steps_information.get_step_information(step_path) == steps_information.steps[step_path]

    def test_get_step_status_not_found(self, steps_information: StepsInformation):
        step_path = StepPath(None, StepType.WORKFLOW, 'workflow_step1')
        assert steps_information.get_step_information(step_path) == StepInformation(path=step_path,
                                                                                    status=StepStatus.UNKNOWN)

    def test_first_step(self, steps_information: StepsInformation):
        assert steps_information.first_step == steps_information.steps[
            StepPath(None, StepType.WORKFLOW, 'workflow_step')]

    def test_first_step_not_found(self):
        steps_information = StepsInformation()
        assert steps_information.first_step is None

    def test_dict(self, steps_information: StepsInformation,
                                    steps_information_dictionary: List[Dict]):
        expected = {
            'steps': steps_information_dictionary
        }
        assert steps_information.dict() == expected


class TestWorkflowContext:
    def test_context(self, steps_information: StepsInformation):
        parameters = {'a': 1, 'b': 2}
        workflow_context = WorkflowContext(parameters, steps_information)
        assert workflow_context.get('a') == 1
        assert workflow_context.get('b') == 2
        assert workflow_context.steps_information == steps_information

    def test_context_default(self, steps_information: StepsInformation):
        workflow_context = WorkflowContext()
        assert workflow_context.get('a') is None
        assert workflow_context.get('b') is None
        assert workflow_context.steps_information != steps_information

    @pytest.mark.parametrize(
        'parameters, key, default, expected',
        [
            ({'a': 1}, 'a', None, 1),
            ({'a': 1}, 'b', None, None),
            ({'a': 1}, 'b', 3, 3),
        ],
        ids=[
            'key exists',
            'key does not exist, default is None',
            'key does not exist, default is not None',
        ]
    )
    def test_context_get(self, parameters, key, default, expected):
        workflow_context = WorkflowContext(parameters)
        if default is None:
            assert workflow_context.get(key) == expected
        else:
            assert workflow_context.get(key, default) == expected

    def test_context_set(self):
        workflow_context = WorkflowContext()
        workflow_context.set('a', 1)
        assert workflow_context.get('a') == 1
        workflow_context.set('a', 2)
        assert workflow_context.get('a') == 2

    def test_context_get_step_information(self, steps_information: StepsInformation,
                                                   workflow_context: WorkflowContext):
        step_path = StepPath(None, StepType.WORKFLOW, 'workflow_step')
        assert workflow_context.get_step_information(step_path) == steps_information.steps[step_path]

    def test_context_steps_information(self, steps_information: StepsInformation,
                                                workflow_context: WorkflowContext):
        assert workflow_context.steps_information == steps_information

    def test_context_global_lock(self):
        workflow_context = WorkflowContext()
        assert workflow_context.global_lock is not None


class TestStep:
    def test(self):
        step = Step('step-name')
        assert step.name == 'step-name'

    def test_default_logger_name(self):
        step = Step('step-name')
        assert step.default_logger_name == 'workflows-manager.runner.step-name'

    def test_information(self, steps_information: StepsInformation, workflow_context: WorkflowContext):
        step = Step('step-name')
        step.workflow_context = workflow_context
        step.path = StepPath(None, StepType.WORKFLOW, 'workflow_step')
        assert step.information == steps_information.steps[step.path]

    def test_configure_logger(self):
        step = Step('step-name')
        step.configure_logger()
        assert step.logger is not None
        assert step.logger.name == step.default_logger_name

    def test_perform(self):
        step = Step('step-name')
        with pytest.raises(NotImplementedError):
            step.perform()

    def test_success(self, workflow_context: WorkflowContext):
        step = Step('step-name')
        step.path = StepPath(None, StepType.WORKFLOW, 'workflow_step')
        step.workflow_context = workflow_context
        step.success()
        assert step.information.status == StepStatus.SUCCESS

    def test_fail(self, workflow_context: WorkflowContext):
        step = Step('step-name')
        step.path = StepPath(None, StepType.WORKFLOW, 'workflow_step')
        step.workflow_context = workflow_context
        step.fail()
        assert step.information.status == StepStatus.FAILED


class NewStep(Step):
    def perform(self, fail: bool) -> str:
        if fail:
            raise Exception('Error')
        return 'value'


class NoopLogger(logging.Logger):
    def __init__(self, name):
        super().__init__(name)
        self.addHandler(logging.NullHandler())


class TestSteps:
    def create_wrapped_step(self) -> Tuple[Step, Callable[[bool], str]]:
        step_path = StepPath(None, StepType.NORMAL, 'normal_step')
        step_information = StepInformation(step_path, StepStatus.NOT_STARTED)
        steps_information = StepsInformation()
        steps_information.steps[step_path] = step_information
        workflow_context = WorkflowContext(steps_information=steps_information)
        new_instance = NewStep()
        new_instance.workflow_context = workflow_context
        new_instance.path = workflow_context.steps_information.first_step.path
        new_instance.logger = NoopLogger('test')
        new_instance.logger.level = logging.DEBUG
        function_wrapper = Steps.wrap_step(new_instance)
        step = function_wrapper(new_instance.perform)
        return new_instance, step

    def test_register(self):
        steps = Steps()
        steps.register('new-step')(NewStep)
        assert steps.steps_register['new-step'] is not None

    def test_wrap_step(self):
        new_instance, step = self.create_wrapped_step()
        step(False)
        assert step is not None
        assert new_instance.information.return_value == 'value'
        assert new_instance.information.status == StepStatus.SUCCESS

    def test_wrap_step_error(self):
        new_instance, step = self.create_wrapped_step()
        try:
            step(True)
            assert False
        except Exception as exception:
            assert new_instance.information.status == StepStatus.FAILED
            assert new_instance.information.error == exception
            assert new_instance.information.return_value is None