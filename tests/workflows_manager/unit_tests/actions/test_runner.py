import logging
from pathlib import Path
from typing import Dict
from unittest.mock import patch, mock_open

from workflows_manager import configuration, dispatcher
from conftest import TEST_LOGGER_NAME, WORKFLOW_NAME, PARAMETERS
from workflows_manager.configuration import Parameters


class TestRunner:
    def test(self, test_configuration: configuration.Configuration):
        path = Path('test.json')
        logger = logging.getLogger(TEST_LOGGER_NAME)
        runner = dispatcher.Runner(logger, test_configuration, WORKFLOW_NAME, PARAMETERS)
        runner.status_file = path
        assert runner.logger == logger
        assert runner.workflows_configuration == test_configuration
        assert runner.workflow_name == WORKFLOW_NAME
        assert runner.status_file == path
        assert runner.parameters == PARAMETERS

    @patch('json.dump')
    @patch('pathlib.Path.open', new_callable=mock_open)
    def test_run(self, mock_file_open, mock_dump, test_configuration: configuration.Configuration,
                 test_expected_status: Dict):
        path = Path('test.json')
        logger = logging.getLogger(TEST_LOGGER_NAME)
        runner = dispatcher.Runner(logger, test_configuration, WORKFLOW_NAME, PARAMETERS)
        runner.status_file = path
        runner.run()
        assert mock_dump.call_args[0][0] == test_expected_status
        assert mock_dump.call_args[0][1] == mock_file_open()

    @patch('json.dump')
    @patch('pathlib.Path.open', new_callable=mock_open)
    def test_run_error_missing_parameters(self, mock_file_open, mock_dump,
                                          test_configuration: configuration.Configuration,
                                          test_expected_status: Dict):
        test_configuration.workflows['test-workflow'].steps[0].parallels[0].parameters = \
            test_configuration.workflows['test-workflow'].steps[0].parallels[0].parameters[:2]
        test_configuration.workflows[WORKFLOW_NAME].steps[0].parameters = Parameters([])
        expected_error = 'Missing the following required parameters: [\'integer\']'
        expected_status = 'failed'
        expected_step = {
            'children': None,
            'error': expected_error,
            'name': 'Normal Step',
            'parameters': None,
            'return_value': None,
            'status': expected_status,
            'stderr': None,
            'stdout': None,
            'type': 'normal'
        }
        test_expected_status['steps'][0]['children'][0]['children'][0] = expected_step
        test_expected_status['steps'][0]['children'][0]['error'] = expected_error
        test_expected_status['steps'][0]['children'][0]['status'] = expected_status
        test_expected_status['steps'][0]['error'] = expected_error
        test_expected_status['steps'][0]['status'] = expected_status
        test_expected_status['steps'][1]['children'][0]['children'][0]['error'] = None
        test_expected_status['steps'][1]['children'][0]['children'][0]['parameters'] = None
        test_expected_status['steps'][1]['children'][0]['children'][0]['status'] = 'not_started'
        test_expected_status['steps'][1]['children'][0]['children'][0]['stderr'] = None
        test_expected_status['steps'][1]['children'][0]['children'][0]['stdout'] = None
        test_expected_status['steps'][1]['children'][0]['error'] = None
        test_expected_status['steps'][1]['children'][0]['status'] = 'not_started'
        test_expected_status['steps'][1]['error'] = None
        test_expected_status['steps'][1]['status'] = 'not_started'
        path = Path('test.json')
        logger = logging.getLogger(TEST_LOGGER_NAME)
        runner = dispatcher.Runner(logger, test_configuration, WORKFLOW_NAME, PARAMETERS)
        runner.status_file = path
        runner.run()
        assert mock_dump.call_args[0][0] == test_expected_status
        assert mock_dump.call_args[0][1] == mock_file_open()

    @patch('json.dump')
    @patch('pathlib.Path.open', new_callable=mock_open)
    def test_run_error_workflow_fail(self, mock_file_open, mock_dump,
                                     test_configuration: configuration.Configuration,
                                     test_expected_status: Dict):
        test_configuration.workflows[WORKFLOW_NAME].steps[1].stop_on_error = True
        test_expected_status['steps'][1]['status'] = 'failed'
        test_expected_status['steps'][1]['error'] = 'error message'
        test_expected_status['steps'][1]['children'][0]['status'] = 'failed'
        test_expected_status['steps'][1]['children'][0]['error'] = 'error message'
        test_expected_status['steps'][1]['children'][0]['children'][0]['status'] = 'failed'
        test_expected_status['steps'][1]['children'][0]['children'][0]['error'] = 'error message'
        path = Path('test.json')
        logger = logging.getLogger(TEST_LOGGER_NAME)
        runner = dispatcher.Runner(logger, test_configuration, WORKFLOW_NAME, PARAMETERS)
        runner.status_file = path
        runner.run()
        assert mock_dump.call_args[0][0] == test_expected_status
        assert mock_dump.call_args[0][1] == mock_file_open()
