from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from workflows_manager.configuration import Parameter, Parameters, Steps, Step, StepType, Workflow, Workflows, \
    Configuration
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
        step = Step('name', 'id', parameters=parameters)
        steps = Steps([step])
        assert len(steps.elements) == 1
        assert steps.elements[0] == step

    def test_default(self):
        steps = Steps()
        assert steps.elements == []

    def test_iter(self):
        steps = Steps([Step('name', 'id')])
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
        steps = Steps([Step('name', 'id')])
        try:
            steps.validate_all()
        except InvalidConfiguration:
            assert False

    @pytest.mark.parametrize('steps, expected_error', [
            (Steps([Step('name', 'id'), Step('name', 'id')]), "Step with a name 'name' occurs multiple times within the same steps context."),
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
        step = Step('name', 'id', parameters=parameters, type=StepType.NORMAL, capture_stderr=True, capture_stdout=True,
                    stop_on_error=False, workflow='workflow', parallels=Steps())
        assert step.name == 'name'
        assert step.id == 'id'
        assert step.parameters == parameters
        assert step.type == StepType.NORMAL
        assert step.capture_stderr is True
        assert step.capture_stdout is True
        assert step.stop_on_error is False
        assert step.workflow == 'workflow'
        assert step.parallels == Steps()

    def test_default(self):
        step = Step('name', 'id')
        assert step.name == 'name'
        assert step.id == 'id'
        assert step.parameters == Parameters()
        assert step.type == StepType.NORMAL
        assert step.capture_stderr is False
        assert step.capture_stdout is False
        assert step.stop_on_error is True
        assert step.workflow is None
        assert step.parallels == Steps()

    @pytest.mark.parametrize('name, step, workflow, expected_name', [
        ('name', '', '', 'name'),
        ('', 'step', '', 'step'),
        ('', '', 'workflow', 'workflow')
    ], ids=[
        'with step name',
        'with step id',
        'with workflow name'
    ])
    def test_name(self, name: str, step: str, workflow: str, expected_name: str):
        step = Step(name=name, id=step, workflow=workflow)
        assert step.name == expected_name

    def test_from_dict(self):
        elements = {
            'name': 'name',
            'step': 'id',
            'parameters': [
                {'name': 'name', 'value': 'value', 'from_context': 'from_context'}
            ],
            'type': 'normal',
            'capture_stderr': True,
            'capture_stdout': True,
            'stop_on_error': False,
            'workflow': 'workflow',
            'parallels': []
        }
        step = Step.from_dict(elements)
        assert step.name == elements['name']
        assert step.id == elements['step']
        assert step.parameters.elements[0].name == elements['parameters'][0]['name']
        assert step.parameters.elements[0].value == elements['parameters'][0]['value']
        assert step.parameters.elements[0].from_context == elements['parameters'][0]['from_context']
        assert step.type == StepType.NORMAL
        assert step.capture_stderr is True
        assert step.capture_stdout is True
        assert step.stop_on_error is False
        assert step.workflow == 'workflow'
        assert step.parallels.elements == []

    def test_from_dict_error(self):
        try:
            Step.from_dict({'type': 'incorrect'})
            assert False
        except InvalidConfiguration as exception:
            assert str(
                exception) == "Invalid step configuration: Step type must be either 'normal', 'parallel', or 'workflow'."

    def test_validate_all(self):
        step = Step('name', 'id')
        try:
            step.validate_all()
        except InvalidConfiguration:
            assert False

    @pytest.mark.parametrize('step_type, expected_error', [
        ('', "Step type must be either 'normal', 'parallel', or 'workflow'."),
        (StepType.WORKFLOW, "Workflow step must have 'workflow' attribute."),
        (StepType.PARALLEL, "Parallel step must have 'parallels' attribute."),
        (StepType.NORMAL, "Normal step must have 'step' attribute."),
    ], ids=[
        'incorrect type',
        'workflow step without workflow name',
        'parallel step without parallels',
        'normal step without step id',
    ])
    def test_validate_all_error(self, step_type: StepType, expected_error: str):
        step = Step('name', type=step_type)
        try:
            step.validate_all()
            assert False
        except InvalidConfiguration as exception:
            assert str(exception) == expected_error


class TestWorkflow:
    def test(self):
        steps = Steps([Step('name', 'id')])
        parameters = Parameters([Parameter('name', 'value', 'from_context')])
        workflow = Workflow('name', steps, parameters)
        assert workflow.name == 'name'
        assert workflow.steps == steps
        assert workflow.parameters == parameters

    def test_default(self):
        steps = Steps([Step('name', 'id')])
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
        workflow = Workflow('name', Steps([Step('name', 'id')]),
                            Parameters([Parameter('name', 'value', 'from_context')]))
        try:
            workflow.validate_all()
        except InvalidConfiguration:
            assert False

    def test_validate_all_error(self):
        workflow = Workflow('incorrect-name!', Steps([Step('name', 'id'), ]),
                            Parameters([Parameter('name', 'value', 'from_context')]))
        try:
            workflow.validate_all()
            assert False
        except InvalidConfiguration as exception:
            assert str(
                exception) == "Workflow name can contain only lowercase letters, numbers, hyphens, and underscores."


class TestWorkflows:
    def test(self):
        workflows = Workflows([Workflow('name', Steps([Step('name', 'id')]))])
        assert len(workflows.elements) == 1

    def test_iter(self):
        workflows = Workflows([Workflow('name', Steps([Step('name', 'id')]))])
        for workflow in workflows:
            assert workflow.name == 'name'
            assert len(workflow.steps.elements) == 1
            assert workflow.steps.elements[0].name == 'name'
            assert workflow.steps.elements[0].id == 'id'

    def test_getitem(self):
        workflows = Workflows([Workflow('name', Steps([Step('name', 'id')]))])
        assert workflows['name'].name == 'name'

    def test_getitem_not_found(self):
        workflows = Workflows([Workflow('name', Steps([Step('name', 'id')]))])
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
        workflows = Workflows([Workflow('name', Steps([Step('name', 'id')]))])
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
        steps = Steps([Step('name', 'id', parameters=parameters)])
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
        workflows = Workflows([Workflow('name', Steps([Step('name', 'id')]))])
        configuration = Configuration(workflows)
        try:
            configuration.validate_all()
        except InvalidConfiguration:
            assert False
