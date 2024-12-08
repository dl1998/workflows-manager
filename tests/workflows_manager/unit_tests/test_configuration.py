from pathlib import Path
from typing import Type
from unittest.mock import patch, mock_open

import pytest

from workflows_manager.configuration import Parameter, Parameters, Steps, Step, StepType, Workflow, Workflows, \
    Configuration, NormalStep, WorkflowStep, ParallelStep
from workflows_manager.exceptions import InvalidConfiguration


class TestParameter:
    def test(self):
        parameter = Parameter('name', 'value', 'from_context')
        assert parameter.name == 'name'
        assert parameter.value == 'value'
        assert parameter.from_context == 'from_context'

    def test_default(self):
        parameter = Parameter('name')
        assert parameter.name == 'name'
        assert parameter.value is None
        assert parameter.from_context is None

    def test_from_dict(self):
        parameter = Parameter.from_dict({'name': 'name', 'value': 'value', 'from_context': 'from_context'})
        assert parameter.name == 'name'
        assert parameter.value == 'value'
        assert parameter.from_context == 'from_context'

    def test_from_dict_default(self):
        parameter = Parameter.from_dict({'name': 'name'})
        assert parameter.name == 'name'
        assert parameter.value is None
        assert parameter.from_context is None

    def test_validate_all(self):
        parameter = Parameter('name', 'value', 'from_context')
        assert parameter.validate_all() is None

    def test_validate_all_empty_name(self):
        parameter = Parameter('')
        try:
            parameter.validate_all()
            assert False
        except InvalidConfiguration as exception:
            assert str(exception) == 'Parameter name cannot be empty.'

    def test_validate_all_reserved_name(self):
        parameter = Parameter('context')
        try:
            parameter.validate_all()
            assert False
        except InvalidConfiguration as exception:
            assert str(exception) == "Parameter name 'context' is reserved."

    def test_validate_all_incorrect_name(self):
        parameter = Parameter('name value')
        try:
            parameter.validate_all()
            assert False
        except InvalidConfiguration as exception:
            assert str(
                exception) == "Parameter name can contain only lowercase letters, numbers, hyphens, and underscores."


class TestParameters:
    def test(self):
        parameters_list = [Parameter('name1', 'value1', 'from_context1'), Parameter('name2', 'value2', 'from_context2')]
        parameters = Parameters(parameters_list)
        assert parameters.elements == parameters_list

    def test_default(self):
        parameters = Parameters()
        assert parameters.elements == []

    def test_iter(self):
        parameters = Parameters([Parameter('name', 'value', 'from_context')])
        for parameter in parameters:
            assert parameter.name == 'name'
            assert parameter.value == 'value'
            assert parameter.from_context == 'from_context'

    def test_from_dict(self):
        elements = [
            {'name': 'name1', 'value': 'value1', 'from_context': 'from_context1'},
            {'name': 'name2', 'value': 'value2', 'from_context': 'from_context2'}
        ]
        parameters = Parameters.from_dict(elements)
        assert parameters.elements[0].name == elements[0]['name']
        assert parameters.elements[0].value == elements[0]['value']
        assert parameters.elements[0].from_context == elements[0]['from_context']
        assert parameters.elements[1].name == elements[1]['name']
        assert parameters.elements[1].value == elements[1]['value']
        assert parameters.elements[1].from_context == elements[1]['from_context']

    def test_from_dict_default(self):
        parameters = Parameters.from_dict([])
        assert parameters.elements == []

    def test_from_dict_error(self):
        try:
            Parameters.from_dict([{None: None}])
            assert False
        except InvalidConfiguration as exception:
            assert str(
                exception) == "Invalid parameters configuration: Invalid parameter configuration: keywords must be strings"

    def test_validate_all(self):
        parameters = Parameters(
            [Parameter('name1', 'value1', 'from_context1'), Parameter('name2', 'value2', 'from_context2')])
        try:
            parameters.validate_all()
        except InvalidConfiguration:
            assert False


class TestSteps:
    def test(self):
        parameters = Parameters([Parameter('name', 'value', 'from_context')])
        normal_step = NormalStep('name', id='step', parameters=parameters)
        workflow_step = WorkflowStep('name', workflow='workflow', parameters=parameters)
        parallel_step = ParallelStep('name', parallels=Steps([normal_step]))
        steps = Steps([normal_step, workflow_step, parallel_step])
        assert len(steps.elements) == 3
        assert steps.elements[0] == normal_step
        assert steps.elements[1] == workflow_step
        assert steps.elements[2] == parallel_step

    def test_default(self):
        steps = Steps()
        assert steps.elements == []

    def test_iter(self):
        steps = Steps([NormalStep('name', id='id')])
        for step in steps:
            assert step.name == 'name'
            assert step.id == 'id'

    def test_from_dict(self):
        elements = [
            {
                'name': 'name',
                'step': 'id',
                'parameters': [
                    {'name': 'name', 'value': 'value', 'from_context': 'from_context'}
                ]
            }
        ]
        steps = Steps.from_dict(elements)
        assert len(steps.elements) == 1
        assert steps.elements[0].name == elements[0]['name']
        assert steps.elements[0].id == elements[0]['step']
        assert steps.elements[0].parameters.elements[0].name == elements[0]['parameters'][0]['name']
        assert steps.elements[0].parameters.elements[0].value == elements[0]['parameters'][0]['value']
        assert steps.elements[0].parameters.elements[0].from_context == elements[0]['parameters'][0]['from_context']

    def test_validate_all(self):
        steps = Steps([NormalStep('name', id='id')])
        try:
            steps.validate_all()
        except InvalidConfiguration:
            assert False

    @pytest.mark.parametrize('steps, expected_error', [
        (Steps([NormalStep('name', id='id'), NormalStep('name', id='id')]),
         "Step with a name 'name' occurs multiple times within the same steps context."),
        (Steps([]), "Steps list cannot be empty."),
    ], ids=[
        'duplicated step name',
        'empty steps list'
    ])
    def test_validate_all_duplicated_step_name(self, steps: Steps, expected_error: str):
        try:
            steps.validate_all()
            assert False
        except InvalidConfiguration as exception:
            assert str(exception) == expected_error


class TestStepType:
    @pytest.mark.parametrize('type_name, expected_type', [
        ('normal', StepType.NORMAL),
        ('parallel', StepType.PARALLEL),
        ('workflow', StepType.WORKFLOW)
    ], ids=[
        'normal step type',
        'parallel step type',
        'workflow step type'
    ])
    def test_from_str(self, type_name: str, expected_type: StepType):
        step_type = StepType.from_str(type_name)
        assert step_type == expected_type

    def test_from_str_invalid(self):
        try:
            StepType.from_str('invalid')
            assert False
        except InvalidConfiguration as exception:
            assert str(exception) == "Step type must be either 'normal', 'parallel', or 'workflow'."


class TestStep:
    def test(self):
        parameters = Parameters([Parameter('name', 'value', 'from_context')])
        step = Step('name', parameters=parameters, stop_on_error=False)
        assert step.name == 'name'
        assert step.parameters == parameters
        assert step.stop_on_error is False

    def test_default(self):
        step = Step('name')
        assert step.name == 'name'
        assert step.parameters == Parameters()
        assert step.stop_on_error is True

    @pytest.mark.parametrize('step_dict, expected_type', [
        [{'type': 'normal'}, NormalStep],
        [{'type': 'workflow'}, WorkflowStep],
        [{'type': 'parallel'}, ParallelStep],
        [{'name': 'name', 'step': 'id'}, NormalStep],
        [{'name': 'name', 'workflow': 'workflow'}, WorkflowStep],
        [{'name': 'name', 'parallels': []}, ParallelStep]
    ], ids=[
        'with type normal step',
        'with type workflow step',
        'with type parallel step',
        'without type normal step',
        'without type workflow step',
        'without type parallel step'
    ])
    def test_from_dict(self, step_dict: dict, expected_type: Type):
        step = Step.from_dict(step_dict)
        assert isinstance(step, expected_type)

    def test_from_dict_error(self):
        try:
            Step.from_dict({'type': 'incorrect'})
            assert False
        except InvalidConfiguration as exception:
            assert str(
                exception) == "Invalid step configuration: Step (None) type must be either 'normal', 'parallel', or 'workflow'."

    def test_validate_all(self):
        step = Step('name')
        try:
            step.validate_all()
        except InvalidConfiguration:
            assert False


class TestNormalStep:
    @pytest.mark.parametrize('name, expected_name', [
        ['name', 'name'],
        [None, 'id'],
        ['', 'id']
    ], ids=[
        'with name',
        'None name',
        'empty name'
    ])
    def test(self, name: str, expected_name: str):
        parameters = Parameters([Parameter('name', 'value', 'from_context')])
        step = NormalStep(name, id='id', parameters=parameters, capture_stdout=True, capture_stderr=True)
        assert step.name == expected_name
        assert step.id == 'id'
        assert step.parameters == parameters
        assert step.capture_stdout is True
        assert step.capture_stderr is True

    def test_default(self):
        step = NormalStep('name')
        assert step.name == 'name'
        assert step.id is None
        assert step.parameters == Parameters()
        assert step.capture_stdout is False
        assert step.capture_stderr is False

    def test_from_dict(self):
        elements = {
            'name': 'name',
            'step': 'id',
            'parameters': [
                {'name': 'name', 'value': 'value', 'from_context': 'from_context'}
            ],
            'capture_stdout': True,
            'capture_stderr': True
        }
        step = NormalStep.from_dict(elements)
        assert step.name == elements['name']
        assert step.id == elements['step']
        assert step.parameters.elements[0].name == elements['parameters'][0]['name']
        assert step.parameters.elements[0].value == elements['parameters'][0]['value']
        assert step.parameters.elements[0].from_context == elements['parameters'][0]['from_context']
        assert step.capture_stdout is True
        assert step.capture_stderr is True

    def test_from_dict_error(self):
        try:
            NormalStep.from_dict(None)
            assert False
        except InvalidConfiguration as exception:
            assert str(
                exception) == "Invalid step configuration: 'NoneType' object has no attribute 'get'"

    def test_validate_all(self):
        step = NormalStep('name', id='id')
        try:
            step.validate_all()
        except InvalidConfiguration:
            assert False

    def test_validate_all_error(self):
        step = NormalStep('name')
        try:
            step.validate_all()
            assert False
        except InvalidConfiguration as exception:
            assert str(
                exception) == "Step ID cannot be empty."


class TestWorkflowStep:
    def test(self):
        parameters = Parameters([Parameter('name', 'value', 'from_context')])
        step = WorkflowStep('name', workflow='workflow', parameters=parameters)
        assert step.name == 'name'
        assert step.workflow == 'workflow'
        assert step.parameters == parameters

    def test_default(self):
        step = WorkflowStep('name')
        assert step.name == 'name'
        assert step.workflow is None
        assert step.parameters == Parameters()

    def test_from_dict(self):
        elements = {
            'name': 'name',
            'workflow': 'workflow',
            'parameters': [
                {'name': 'name', 'value': 'value', 'from_context': 'from_context'}
            ]
        }
        step = WorkflowStep.from_dict(elements)
        assert step.name == elements['name']
        assert step.workflow == elements['workflow']
        assert step.parameters.elements[0].name == elements['parameters'][0]['name']
        assert step.parameters.elements[0].value == elements['parameters'][0]['value']
        assert step.parameters.elements[0].from_context == elements['parameters'][0]['from_context']

    def test_from_dict_error(self):
        try:
            WorkflowStep.from_dict(None)
            assert False
        except InvalidConfiguration as exception:
            assert str(
                exception) == "Invalid step configuration: 'NoneType' object has no attribute 'get'"

    def test_validate_all(self):
        step = WorkflowStep('name', workflow='workflow')
        try:
            step.validate_all()
        except InvalidConfiguration:
            assert False

    def test_validate_all_error(self):
        step = WorkflowStep('name')
        try:
            step.validate_all()
            assert False
        except InvalidConfiguration as exception:
            assert str(
                exception) == "Workflow name cannot be empty."


class TestParallelStep:
    def test(self):
        steps = Steps([NormalStep('name', id='id')])
        step = ParallelStep('name', parallels=steps)
        assert step.name == 'name'
        assert step.parallels == steps

    def test_default(self):
        step = ParallelStep('name')
        assert step.name == 'name'
        assert step.parallels == Steps()

    def test_from_dict(self):
        elements = {
            'name': 'name',
            'parallels': [
                {
                    'name': 'name',
                    'step': 'id',
                    'parameters': [
                        {'name': 'name', 'value': 'value', 'from_context': 'from_context'}
                    ]
                }
            ]
        }
        step = ParallelStep.from_dict(elements)
        assert step.name == elements['name']
        assert len(step.parallels.elements) == 1
        assert step.parallels.elements[0].name == elements['parallels'][0]['name']
        assert step.parallels.elements[0].id == elements['parallels'][0]['step']
        assert step.parallels.elements[0].parameters.elements[0].name == elements['parallels'][0]['parameters'][0][
            'name']
        assert step.parallels.elements[0].parameters.elements[0].value == elements['parallels'][0]['parameters'][0][
            'value']
        assert step.parallels.elements[0].parameters.elements[0].from_context == elements['parallels'][0]['parameters'][
            0]['from_context']

    def test_from_dict_error(self):
        try:
            ParallelStep.from_dict(None)
            assert False
        except InvalidConfiguration as exception:
            assert str(
                exception) == "Invalid step configuration: 'NoneType' object has no attribute 'get'"

    def test_validate_all(self):
        step = ParallelStep('name', parallels=Steps([NormalStep('name', id='id')]))
        try:
            step.validate_all()
        except InvalidConfiguration:
            assert False

    def test_validate_all_error(self):
        step = ParallelStep('name')
        try:
            step.validate_all()
            assert False
        except InvalidConfiguration as exception:
            assert str(
                exception) == "Steps list cannot be empty."


class TestWorkflow:
    def test(self):
        steps = Steps([NormalStep('name', id='id')])
        parameters = Parameters([Parameter('name', 'value', 'from_context')])
        workflow = Workflow('name', steps, parameters)
        assert workflow.name == 'name'
        assert workflow.steps == steps
        assert workflow.parameters == parameters

    def test_default(self):
        steps = Steps([NormalStep('name', id='id')])
        workflow = Workflow('name', steps)
        assert workflow.name == 'name'
        assert workflow.steps == steps

    def test_from_dict(self):
        elements = {
            'name': 'name',
            'steps': [
                {
                    'name': 'name',
                    'step': 'id',
                    'parameters': [
                        {'name': 'name', 'value': 'value', 'from_context': 'from_context'}
                    ]
                }
            ],
            'parameters': [
                {'name': 'name', 'value': 'value', 'from_context': 'from_context'}
            ]
        }
        workflow = Workflow.from_dict(elements)
        assert workflow.name == elements['name']
        assert workflow.steps.elements[0].name == elements['steps'][0]['name']
        assert workflow.steps.elements[0].id == elements['steps'][0]['step']
        assert workflow.steps.elements[0].parameters.elements[0].name == elements['steps'][0]['parameters'][0]['name']
        assert workflow.steps.elements[0].parameters.elements[0].value == elements['steps'][0]['parameters'][0]['value']
        assert workflow.steps.elements[0].parameters.elements[0].from_context == elements['steps'][0]['parameters'][0][
            'from_context']
        assert workflow.parameters.elements[0].name == elements['parameters'][0]['name']
        assert workflow.parameters.elements[0].value == elements['parameters'][0]['value']
        assert workflow.parameters.elements[0].from_context == elements['parameters'][0]['from_context']

    def test_from_dict_error(self):
        try:
            Workflow.from_dict({})
            assert False
        except InvalidConfiguration as exception:
            assert str(
                exception) == "Invalid workflow configuration: Invalid steps configuration: 'NoneType' object is not iterable"

    def test_validate_all(self):
        workflow = Workflow('name', Steps([NormalStep('name', id='id')]),
                            Parameters([Parameter('name', 'value', 'from_context')]))
        try:
            workflow.validate_all()
        except InvalidConfiguration:
            assert False

    def test_validate_all_error(self):
        workflow = Workflow('incorrect-name!', Steps([NormalStep('name', id='id')]),
                            Parameters([Parameter('name', 'value', 'from_context')]))
        try:
            workflow.validate_all()
            assert False
        except InvalidConfiguration as exception:
            assert str(
                exception) == "Workflow name can contain only lowercase letters, numbers, hyphens, and underscores."


class TestWorkflows:
    def test(self):
        workflows = Workflows([Workflow('name', Steps([NormalStep('name', id='id')]))])
        assert len(workflows.elements) == 1

    def test_iter(self):
        workflows = Workflows([Workflow('name', Steps([NormalStep('name', id='id')]))])
        for workflow in workflows:
            assert workflow.name == 'name'
            assert len(workflow.steps.elements) == 1
            assert workflow.steps.elements[0].name == 'name'
            assert workflow.steps.elements[0].id == 'id'

    def test_getitem(self):
        workflows = Workflows([Workflow('name', Steps([NormalStep('name', id='id')]))])
        assert workflows['name'].name == 'name'

    def test_getitem_not_found(self):
        workflows = Workflows([Workflow('name', Steps([NormalStep('name', id='id')]))])
        assert workflows['missing'] is None

    def test_from_dict(self):
        elements = {
            'workflow': {
                'name': 'name',
                'steps': [
                    {
                        'name': 'name',
                        'step': 'id',
                        'parameters': [
                            {'name': 'name', 'value': 'value', 'from_context': 'from_context'}
                        ]
                    }
                ]
            }
        }
        workflows = Workflows.from_dict(elements)
        assert len(workflows.elements) == 1
        assert workflows.elements[0].name == elements['workflow']['name']
        assert len(workflows.elements[0].steps.elements) == 1
        assert workflows.elements[0].steps.elements[0].name == elements['workflow']['steps'][0]['name']
        assert workflows.elements[0].steps.elements[0].id == elements['workflow']['steps'][0]['step']
        assert len(workflows.elements[0].steps.elements[0].parameters.elements) == 1
        assert workflows.elements[0].steps.elements[0].parameters.elements[0].name == \
               elements['workflow']['steps'][0]['parameters'][0]['name']
        assert workflows.elements[0].steps.elements[0].parameters.elements[0].value == \
               elements['workflow']['steps'][0]['parameters'][0]['value']
        assert workflows.elements[0].steps.elements[0].parameters.elements[0].from_context == \
               elements['workflow']['steps'][0]['parameters'][0]['from_context']

    def test_from_dict_error(self):
        try:
            Workflows.from_dict({'workflow': {}})
            assert False
        except InvalidConfiguration as exception:
            assert str(
                exception) == "Invalid workflows configuration: Invalid workflow configuration: Invalid steps configuration: 'NoneType' object is not iterable"

    def test_validate_all(self):
        workflows = Workflows([Workflow('name', Steps([NormalStep('name', id='id')]))])
        try:
            workflows.validate_all()
        except InvalidConfiguration:
            assert False

    def test_validate_all_error(self):
        workflows = Workflows([])
        try:
            workflows.validate_all()
            assert False
        except InvalidConfiguration as exception:
            assert str(exception) == "Workflows list cannot be empty."


class TestConfiguration:
    def test(self):
        parameters = Parameters([Parameter('name', 'value', 'from_context')])
        steps = Steps([NormalStep('name', id='id', parameters=parameters)])
        workflows = Workflows([Workflow('name', steps, parameters)])
        configuration = Configuration(workflows)
        assert configuration.workflows == workflows

    def test_default(self):
        workflows = Workflows(elements=[])
        configuration = Configuration(workflows)
        assert configuration.workflows == workflows

    def test_from_dict(self):
        elements = {
            'workflows': {
                'workflow': {
                    'name': 'name',
                    'steps': [
                        {
                            'name': 'name',
                            'step': 'id',
                            'parameters': [
                                {'name': 'name', 'value': 'value', 'from_context': 'from_context'}
                            ]
                        }
                    ]
                }
            }
        }
        configuration = Configuration.from_dict(elements)
        assert len(configuration.workflows.elements) == 1
        assert configuration.workflows.elements[0].name == elements['workflows']['workflow']['name']
        assert len(configuration.workflows.elements[0].steps.elements) == 1
        assert configuration.workflows.elements[0].steps.elements[0].name == \
               elements['workflows']['workflow']['steps'][0][
                   'name']
        assert configuration.workflows.elements[0].steps.elements[0].id == \
               elements['workflows']['workflow']['steps'][0][
                   'step']
        assert len(configuration.workflows.elements[0].steps.elements[0].parameters.elements) == 1
        assert configuration.workflows.elements[0].steps.elements[0].parameters.elements[0].name == \
               elements['workflows']['workflow']['steps'][0]['parameters'][0]['name']
        assert configuration.workflows.elements[0].steps.elements[0].parameters.elements[0].value == \
               elements['workflows']['workflow']['steps'][0]['parameters'][0]['value']
        assert configuration.workflows.elements[0].steps.elements[0].parameters.elements[0].from_context == \
               elements['workflows']['workflow']['steps'][0]['parameters'][0]['from_context']

    def test_from_dict_error(self):
        try:
            Configuration.from_dict({})
            assert False
        except InvalidConfiguration as exception:
            assert str(exception) == "Invalid configuration file: 'workflows'"

    @patch('pathlib.Path.open', new_callable=mock_open, read_data='{workflows: {workflow: {steps: []}}}')
    @patch('pathlib.Path.absolute', return_value=Path('/mocked/path'))
    def test_from_yaml(self, mock_absolute, mock_open_object):
        config = Configuration.from_yaml('/mocked/path/config.yaml')

        mock_absolute.assert_called_once()
        mock_open_object.assert_called_once_with('r', encoding='utf-8')
        assert config.workflows.elements[0].name == 'workflow'
        assert len(config.workflows.elements[0].steps.elements) == 0

    @patch('pathlib.Path.open', new_callable=mock_open, read_data='{"workflows": {"workflow": {"steps": []}}}')
    @patch('pathlib.Path.absolute', return_value=Path('/mocked/path'))
    def test_from_json(self, mock_absolute, mock_open_object):
        config = Configuration.from_json('/mocked/path/config.json')

        mock_absolute.assert_called_once()
        mock_open_object.assert_called_once_with('r', encoding='utf-8')
        assert config.workflows.elements[0].name == 'workflow'
        assert len(config.workflows.elements[0].steps.elements) == 0

    def test_validate_all(self):
        workflows = Workflows([Workflow('name', Steps([NormalStep('name', id='id')]))])
        configuration = Configuration(workflows)
        try:
            configuration.validate_all()
        except InvalidConfiguration:
            assert False
