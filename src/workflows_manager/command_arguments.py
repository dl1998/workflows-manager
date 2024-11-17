"""
Module for parsing command line arguments.
"""
import json
from argparse import ArgumentParser, Namespace
from typing import List, Any, Dict, Optional, Callable

from workflows_manager.exceptions import InvalidParameter

PARAMETERS_DELIMITER = ':'


def __create_parameters_group(subparser: ArgumentParser):
    """
    Create a group of parameters for the subparser.

    :param subparser: Subparser to which the parameters group will be added.
    :type subparser: ArgumentParser
    """
    parameters_group = subparser.add_argument_group('Parameters', 'Parameters for the workflow.')
    parameters_group.add_argument('--parameter', '-p', action='append', help='Parameters for the workflow.')
    parameters_group.add_argument('--string-parameter', '-sp', action='append',
                                  help='String parameters for the workflow.')
    parameters_group.add_argument('--integer-parameter', '-ip', action='append',
                                  help='Integer parameters for the workflow.')
    parameters_group.add_argument('--boolean-parameter', '-bp', action='append',
                                  help='Boolean parameters for the workflow.')
    parameters_group.add_argument('--float-parameter', '-fp', action='append',
                                  help='Float parameters for the workflow.')
    parameters_group.add_argument('--list-parameter', '-lp', action='append', help='List parameters for the workflow.')
    parameters_group.add_argument('--dict-parameter', '-dp', action='append',
                                  help='Dictionary parameters for the workflow.')


def __configure_run_action_subparser(parser):
    """
    Configure the subparser for the run action.

    :param parser: Parser to which the subparser will be added.
    """
    run_subparser = parser.add_parser('run', help='Run the workflows.')
    run_subparser.add_argument('--status-file', '-sf', type=str,
                               help='Path to the file where the statuses of the particular steps will be stored.')
    __create_parameters_group(run_subparser)
    run_subparser.add_argument('workflow_name', type=str, help='Name of the workflow to run.')


def __configure_validate_action_subparser(parser):
    """
    Configure the subparser for the validate action.

    :param parser: Parser to which the subparser will be added.
    """
    validate_subparser = parser.add_parser('validate', help='Validate the workflows configuration.')
    validate_subparser.add_argument('--workflow-name', '-w', type=str, required=False,
                                    help='Name of the workflow to validate. If not provided, it will validate that '
                                         'required parameters have been provided and all necessary steps have been '
                                         'registered.')
    __create_parameters_group(validate_subparser)


def __configure_version_action_subparser(parser):
    """
    Configure the subparser for the version action.

    :param parser: Parser to which the subparser will be added.
    """
    parser.add_parser('version', help='Version of the application.')


def __configure_action_subparsers(parser):
    """
    Configure the subparsers for the actions.

    :param parser: Parser to which the subparsers will be added.
    """
    action_subparsers = parser.add_subparsers(dest='action', help='Subcommands for managing workflows.')
    action_subparsers.required = True
    __configure_run_action_subparser(action_subparsers)
    __configure_validate_action_subparser(action_subparsers)
    __configure_version_action_subparser(action_subparsers)


def get_args() -> Namespace:
    """
    Parse the command line arguments passed to the application.

    :return: Parsed arguments.
    :rtype: Namespace
    """
    parser = ArgumentParser()
    configuration_group = parser.add_argument_group('Configuration', 'Configuration of the workflows manager.')
    configuration_group.add_argument('--imports', '-i', action='append', help='List of paths to the workflows modules.')
    configuration_group.add_argument('--configuration-file', '-c', type=str, required=False,
                                     help='Path to the configuration file with workflows and steps.  If not provided, '
                                          'then it will try to search for workflows.yaml or workflows.json in the '
                                          'current working directory.')
    configuration_group.add_argument('--disable-error-codes', action='store_true',
                                     help='Disable error codes for exceptions. It changes behavior of the application '
                                          'to always return 0 as an exit status code.')
    configuration_group.add_argument('--disable-current-path-import', action='store_true',
                                     help='Disable automatic import of the modules from the current path.')
    logging_group = parser.add_argument_group('Logging', 'Logging configuration of the application.')
    logging_group.add_argument('--log-level', '-ll', type=str,
                               choices=['debug', 'info', 'warning', 'error', 'critical'],
                               default='info', help='Logging level of the application.')
    logging_group.add_argument('--log-file', '-lf', type=str,
                               help='Path to the log file. If not provided, it won\'t log to a file.')
    logging_group.add_argument('--console-log-format', '-clf', type=str, choices=['text', 'json'], default='text',
                               help='Format of the log messages in the console.')
    logging_group.add_argument('--file-log-format', '-flf', type=str, choices=['text', 'json'], default='text',
                               help='Format of the log messages in the file.')
    __configure_action_subparsers(parser)
    return parser.parse_args()


types_mapping = {
    'str': str,
    'int': int,
    'bool': lambda value: value.lower() == 'true',
    'float': float,
    'list': lambda value: value.split(','),
    'dict': json.loads,
}


def __update_parameter(name: str, value: str, parameter_type: Callable[[str], Any], parameters: Dict[str, Any]):
    """
    Update the parameters dictionary with the new parameter.

    :param name: Name of the parameter.
    :type name: str
    :param value: Value of the parameter.
    :type value: str
    :param parameter_type: Type of the parameter.
    :type parameter_type: Callable[[str], Any]
    :param parameters: Parameters dictionary that will be updated.
    :type parameters: Dict[str, Any]
    """
    if name and name in parameters:
        raise InvalidParameter(f'Duplicated parameter: {name}')
    if name and value and parameter_type:
        parameters[name] = parameter_type(value)


def __add_parameters(parameters: Optional[List[str]], destination: Dict[str, Any],
                     parameter_type: Optional[Callable[[str], Any]] = None):
    """
    Add parameters to the destination dictionary.

    :param parameters: List of parameters.
    :type parameters: Optional[List[str]]
    :param destination: Destination dictionary where the parameters will be added.
    :type destination: Dict[str, Any]
    :param parameter_type: Type of the parameters.
    :type parameter_type: Optional[Callable[[str], Any]]
    """
    with_parameter_type = parameter_type is not None
    if parameters:
        for parameter in parameters:
            if with_parameter_type:
                name, value = parameter.split(PARAMETERS_DELIMITER, 1)
            else:
                name, parameter_type_name, value = parameter.split(PARAMETERS_DELIMITER, 2)
                parameter_type = types_mapping.get(parameter_type_name, None)
            __update_parameter(name, value, parameter_type, destination)


def get_parameters(namespace: Namespace) -> Dict[str, Any]:
    """
    Get parameters from the namespace.

    :param namespace: Namespace with the parameters.
    :type namespace: Namespace
    :return: Parameters from the namespace.
    :rtype: Dict[str, Any]
    """
    parameters = {}
    __add_parameters(namespace.parameter, parameters)
    __add_parameters(namespace.string_parameter, parameters, types_mapping['str'])
    __add_parameters(namespace.integer_parameter, parameters, types_mapping['int'])
    __add_parameters(namespace.boolean_parameter, parameters, types_mapping['bool'])
    __add_parameters(namespace.float_parameter, parameters, types_mapping['float'])
    __add_parameters(namespace.list_parameter, parameters, types_mapping['list'])
    __add_parameters(namespace.dict_parameter, parameters, types_mapping['dict'])
    return parameters
