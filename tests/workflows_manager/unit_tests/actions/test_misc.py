import inspect

from workflows_manager.actions.misc import InstanceParameter, InstanceParameters
from workflows_manager.workflow import steps


class TestInstanceParameter:
    def test(self):
        parameter = InstanceParameter(name='name', value='value', type=str)
        assert parameter.name == 'name'
        assert parameter.value == 'value'
        assert parameter.type == str


class TestInstanceParameters:
    def test(self):
        parameter = InstanceParameter(name='name', value='value', type=str)
        parameters = InstanceParameters([
            parameter,
        ])
        assert len(parameters.parameters) == 1
        assert parameters.parameters[0] == parameter

    def test_from_step(self):
        step = steps.steps_register['new-step']
        parameters = InstanceParameters.from_step(step)
        expected_parameters = InstanceParameters()
        expected_parameters.parameters.append(InstanceParameter('string', inspect.Parameter.empty, str))
        expected_parameters.parameters.append(InstanceParameter('boolean', inspect.Parameter.empty, bool))
        expected_parameters.parameters.append(InstanceParameter('integer', inspect.Parameter.empty, int))
        expected_parameters.parameters.append(InstanceParameter('key', inspect.Parameter.empty, str))
        expected_parameters.parameters.append(InstanceParameter('optional', None, inspect.Parameter.empty))
        assert parameters == expected_parameters

    def test_iter(self):
        parameter = InstanceParameter(name='name', value='value', type=str)
        parameters = InstanceParameters([
            parameter,
        ])
        for index, parameter in enumerate(parameters):
            assert parameter == parameters[index]

    def test_getitem(self):
        parameter = InstanceParameter(name='name', value='value', type=str)
        parameters = InstanceParameters([
            parameter,
        ])
        assert parameters[0] == parameter
        assert parameters[parameter.name] == parameter

    def test_delitem(self):
        parameter = InstanceParameter(name='name', value='value', type=str)
        parameters = InstanceParameters([
            parameter,
        ])
        del parameters['name']
        assert len(parameters.parameters) == 0
