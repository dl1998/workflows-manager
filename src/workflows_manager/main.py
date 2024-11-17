"""
This module is the entry point of the workflow engine. It contains the main function that is responsible for running
the workflows.
"""
import logging
import sys
from argparse import Namespace, ArgumentParser

from workflows_manager import __version__
from workflows_manager.command_arguments import get_args, get_parameters
from workflows_manager.dispatcher import WorkflowDispatcherBuilder, DispatcherAction
from workflows_manager.logger import get_logger

DEFAULT_STATUS_CODE = 0
DEFAULT_ERROR_STATUS_CODE = 1
EXCEPTION_TO_STATUS_CODE = {
    Exception: DEFAULT_ERROR_STATUS_CODE,
}


def main(arguments: Namespace) -> int:
    """
    Main function of the application (entrypoint).

    :param arguments: Arguments passed to the application.
    :type arguments: Namespace
    :return: Exit status code of the application.
    :rtype: int
    """
    logger = get_logger(arguments.log_level, arguments.log_file, arguments.console_log_format,
                        arguments.file_log_format)
    try:
        logger.info('Starting the workflow engine')
        dispatcher = (WorkflowDispatcherBuilder()
                      .logger(logger)
                      .disable_current_path_import(arguments.disable_current_path_import)
                      .imports(arguments.imports)
                      .configuration_file(arguments.configuration_file)
                      .workflow_name(arguments.workflow_name)
                      .status_file(arguments.status_file)
                      .parameters(get_parameters(arguments))
                      .build())
        dispatcher.dispatch(DispatcherAction.from_str(arguments.action))
        logger.info('Stop the workflow engine.')
        return DEFAULT_STATUS_CODE
    except Exception as exception:
        if logger.level == logging.DEBUG:
            logger.exception(exception)
        else:
            logger.error(exception)
        status_code = EXCEPTION_TO_STATUS_CODE.get(type(exception), DEFAULT_ERROR_STATUS_CODE)
        if arguments.disable_error_codes:
            status_code = DEFAULT_STATUS_CODE
        return status_code


def main_cli():
    """
    Main function of the application (entrypoint) for the command line interface.
    """
    args = get_args()
    if args.action == 'version':
        print(f'v{__version__.__version__}')
        sys.exit(0)
    sys.exit(main(args))


if __name__ == '__main__':
    main_cli()
