"""
This module is the entry point of the workflow engine. It contains the main function that is responsible for running
the workflows.
"""
import logging
import sys
from argparse import Namespace, ArgumentParser

from workflows_manager import __version__
from workflows_manager.dispatcher import WorkflowDispatcherBuilder, DispatcherAction
from workflows_manager.logger import get_logger

DEFAULT_STATUS_CODE = 0
DEFAULT_ERROR_STATUS_CODE = 1
EXCEPTION_TO_STATUS_CODE = {
    Exception: DEFAULT_ERROR_STATUS_CODE,
}


def get_args() -> Namespace:
    """
    Parse the command line arguments passed to the application.

    :return: Parsed arguments.
    :rtype: Namespace
    """
    parser = ArgumentParser()
    parser.add_argument('--imports', '-i', action='append', help='List of paths to the workflows modules.')
    parser.add_argument('--log-level', '-ll', type=str, choices=['debug', 'info', 'warning', 'error', 'critical'],
                        default='info', help='Logging level of the application.')
    parser.add_argument('--log-file', '-lf', type=str,
                        help='Path to the log file. If not provided, it won\'t log to a file.')
    parser.add_argument('--console-log-format', '-clf', type=str, choices=['text', 'json'], default='text',
                        help='Format of the log messages in the console.')
    parser.add_argument('--file-log-format', '-flf', type=str, choices=['text', 'json'], default='text',
                        help='Format of the log messages in the file.')
    parser.add_argument('--configuration-file', '-c', type=str, required=False,
                        help='Path to the configuration file with workflows and steps.  If not provided, then it will '
                             'try to search for workflows.yaml or workflows.json in the current working directory.')
    parser.add_argument('--disable-error-codes', action='store_true',
                        help='Disable error codes for exceptions. It changes behavior of the application to always '
                             'return 0 as an exit status code.')
    parser.add_argument('--disable-current-path-import', action='store_true',
                        help='Disable automatic import of the modules from the current path.')
    action_subparsers = parser.add_subparsers(dest='action', help='Subcommands for managing workflows.')
    action_subparsers.required = True
    action_subparsers.add_parser('version', help='Version of the application.')
    validate_subparser = action_subparsers.add_parser('validate', help='Validate the workflows configuration.')
    validate_subparser.add_argument('--workflow-name', '-w', type=str, required=False,
                                    help='Name of the workflow to validate. If not provided, it will validate that '
                                         'required parameters have been provided and all necessary steps have been '
                                         'registered.')
    run_subparser = action_subparsers.add_parser('run', help='Run the workflows.')
    run_subparser.add_argument('--status-file', '-sf', type=str,
                               help='Path to the file where the statuses of the particular steps will be stored.')
    run_subparser.add_argument('workflow_name', type=str, help='Name of the workflow to run.')
    return parser.parse_args()


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
