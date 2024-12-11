import contextlib
import io
import logging

import pytest

from workflows_manager.actions.list import ListWorkflows
from workflows_manager.configuration import Configuration, Workflows
from conftest import TEST_LOGGER_NAME


class TestListWorkflows:
    @pytest.mark.parametrize('workflows_configuration, expected_output', [
        (Configuration.from_dict({'workflows': {'workflow': {'steps': []}}}), 'workflow\n'),
        (Configuration.from_dict({'workflows': {'workflow1': {'steps': []}, 'workflow2': {'steps': []}}}),
         'workflow1\nworkflow2\n'),
    ], ids=[
        'single workflow',
        'multiple workflows',
    ])
    def test_list(self, workflows_configuration: Configuration, expected_output: str):
        logger = logging.getLogger(TEST_LOGGER_NAME)
        list_workflows = ListWorkflows(logger, workflows_configuration)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            list_workflows.list()
        assert stdout.getvalue() == expected_output
