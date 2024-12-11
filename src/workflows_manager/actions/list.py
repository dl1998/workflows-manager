"""
Module contains list action that is responsible for listing all available workflows.
"""
from logging import Logger

from workflows_manager import configuration


class ListWorkflows:
    """
    A class to list all available workflows.

    :param logger: Logger instance.
    :type logger: Logger
    :param workflows_configuration: Configuration instance.
    :type workflows_configuration: configuration.Configuration
    """
    logger: Logger
    workflows_configuration: configuration.Configuration

    def __init__(self, logger: Logger, workflows_configuration: configuration.Configuration):
        self.logger = logger
        self.workflows_configuration = workflows_configuration

    def list(self):
        """
        A method that list all available workflows.
        """
        self.logger.info('Listing workflows')
        for workflow in self.workflows_configuration.workflows:
            print(workflow.name)
