import logging
from typing import Dict

import pytest

from workflows_manager import configuration

TEST_LOGGER_NAME = 'noop_logger'
WORKFLOW_NAME = 'workflow'
PARAMETERS = {
    'key': 'value'
}


def setup_module(_):
    logger = logging.getLogger(TEST_LOGGER_NAME)
    logger.addHandler(logging.NullHandler())


@pytest.fixture
def test_configuration():
    return configuration.Configuration.from_dict({
        'workflows': {
            'test-workflow': {
                'steps': [
                    {
                        'name': 'Parallel Step',
                        'type': 'parallel',
                        'parallels': [
                            {
                                'name': 'Normal Step',
                                'step': 'new-step',
                                'parameters': [
                                    {
                                        'name': 'string',
                                        'value': 'test'
                                    },
                                    {
                                        'name': 'boolean',
                                        'value': True
                                    },
                                    {
                                        'name': 'integer',
                                        'value': 1
                                    }
                                ],
                                'capture_stdout': True,
                                'capture_stderr': True,
                            }
                        ]
                    }
                ]
            },
            WORKFLOW_NAME: {
                'steps': [
                    {
                        'name': 'Workflow Step',
                        'type': 'workflow',
                        'workflow': 'test-workflow',
                        'parameters': [
                            {
                                'name': 'optional',
                                'value': 'error message'
                            }
                        ],
                    },
                    {
                        'name': 'Another Workflow Step',
                        'type': 'workflow',
                        'workflow': 'test-workflow',
                        'stop_on_error': False,
                        'parameters': [
                            {
                                'name': 'optional',
                                'from_context': 'error'
                            }
                        ]
                    }
                ]
            }
        }
    })


@pytest.fixture
def test_expected_status() -> Dict:
    return {
        'steps': [
            {
                'children': [
                    {
                        'children': [
                            {
                                'error': None,
                                'name': 'Normal Step',
                                'parameters': {
                                    'boolean': True,
                                    'integer': 1,
                                    'key': 'value',
                                    'optional': 'error message',
                                    'string': 'test'
                                },
                                'return_value': 1,
                                'status': 'success',
                                'stderr': 'True\n',
                                'stdout': 'test\n',
                                'type': 'normal'
                            }
                        ],
                        'error': None,
                        'name': 'Parallel Step',
                        'parameters': None,
                        'status': 'success',
                        'type': 'parallel'
                    }
                ],
                'error': None,
                'name': 'Workflow Step',
                'parameters': None,
                'status': 'success',
                'type': 'workflow'
            },
            {
                'children': [
                    {
                        'children': [
                            {
                                'error': 'error message',
                                'name': 'Normal Step',
                                'parameters': {
                                    'boolean': True,
                                    'integer': 1,
                                    'key': 'value',
                                    'optional': 'error message',
                                    'string': 'test'
                                },
                                'return_value': None,
                                'status': 'failed',
                                'stderr': 'True\n',
                                'stdout': 'test\n',
                                'type': 'normal'
                            }
                        ],
                        'error': 'error message',
                        'name': 'Parallel Step',
                        'parameters': None,
                        'status': 'failed',
                        'type': 'parallel'
                    }
                ],
                'error': 'error message',
                'name': 'Another Workflow Step',
                'parameters': None,
                'status': 'failed',
                'type': 'workflow',
            }
        ]
    }
