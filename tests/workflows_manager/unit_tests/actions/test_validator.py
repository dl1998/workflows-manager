import logging

from workflows_manager import configuration, dispatcher
from conftest import TEST_LOGGER_NAME, WORKFLOW_NAME, PARAMETERS
from workflows_manager.configuration import Parameters


class TestValidator:
    def test(self, test_configuration: configuration.Configuration):
        logger = logging.getLogger(TEST_LOGGER_NAME)
        validator = dispatcher.Validator(logger, test_configuration, WORKFLOW_NAME, PARAMETERS)
        assert validator.logger == logger
        assert validator.workflows_configuration == test_configuration
        assert validator.workflow_name == WORKFLOW_NAME
        assert validator.parameters == PARAMETERS

    def test_validate(self, test_configuration: configuration.Configuration):
        logger = logging.getLogger(TEST_LOGGER_NAME)
        validator = dispatcher.Validator(logger, test_configuration, WORKFLOW_NAME, PARAMETERS)
        assert validator.validate() == True

    def test_validate_error_registered_steps(self, test_configuration: configuration.Configuration):
        logger = logging.getLogger(TEST_LOGGER_NAME)
        test_configuration.workflows[0].steps[0].parallels[0].id = 'missing-step'
        validator = dispatcher.Validator(logger, test_configuration, WORKFLOW_NAME, PARAMETERS)
        assert validator.validate() == False

    def test_validate_error_missing_parameter(self, test_configuration: configuration.Configuration):
        logger = logging.getLogger(TEST_LOGGER_NAME)
        test_configuration.workflows[0].steps[0].parallels[0].parameters[0].name = 'unknown-parameter'
        test_configuration.workflows[WORKFLOW_NAME].steps[0].parameters = Parameters([])
        validator = dispatcher.Validator(logger, test_configuration, WORKFLOW_NAME, PARAMETERS)
        assert validator.validate() == False
