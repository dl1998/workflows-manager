"""
Module for parsing command line arguments.
"""
import json
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from typing import List, Any, Dict, Optional, Callable

from workflows_manager.exceptions import InvalidParameter

PARAMETERS_DELIMITER = ':'


def __create_configuration_group(parser: ArgumentParser):
    """
    Create a group of configuration parameters for the subparser.

    :param parser: Subparser to which the configuration group will be added.
    :type parser: ArgumentParser
    """
    configuration_group = parser.add_argument_group('Configuration', 'Configuration of the workflows manager.')
    configuration_group.add_argument('--imports', '-i', action='append', help='List of paths to the workflows modules.')
    configuration_group.add_argument('--configuration-file', '-c', type=str, required=False,
                                     help='Path to the configuration file with workflows and steps. If not provided, '
                                          'then it will try to search for workflows.yaml or workflows.json in the '
                                          'current working directory.')
    configuration_group.add_argument('--disable-error-codes', action='store_true',
                                     help='Disable error codes for exceptions. It changes behavior of the application '
                                          'to always return 0 as an exit status code.')
    configuration_group.add_argument('--disable-current-path-import', action='store_true',
                                     help='Disable automatic import of the modules from the current path.')


def __create_logging_group(parser: ArgumentParser):
    """
    Create a group of logging parameters for the subparser.

    :param parser: Subparser to which the logging group will be added.
    :type parser: ArgumentParser
    """
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


def __create_parameters_group(parser: ArgumentParser):
    """
    Create a group of parameters for the subparser.

    :param parser: Subparser to which the parameters group will be added.
    :type parser: ArgumentParser
    """
    parameter_description = [
        'Parameter for the workflow. Format: "<name>:<type>:<value>". Supported types:',
        '- str - string',
        '- int - integer',
        '- bool - boolean',
        '- float - float',
        '- list - list (delimiter: ",")',
        '- dict - dictionary (JSON format)',
    ]
    parameters_group = parser.add_argument_group('Parameters', 'Parameters for the workflow.')
    parameters_group.add_argument('--parameter', '-p', action='append',
                                  help='\n'.join(parameter_description))
    parameters_group.add_argument('--string-parameter', '-sp', action='append',
                                  help='String parameter for the workflow. Format: "<name>:<value>".')
    parameters_group.add_argument('--integer-parameter', '-ip', action='append',
                                  help='Integer parameter for the workflow. Format: "<name>:<value>".')
    parameters_group.add_argument('--boolean-parameter', '-bp', action='append',
                                  help='Boolean parameter for the workflow. Format: "<name>:<value>".')
    parameters_group.add_argument('--float-parameter', '-fp', action='append',
                                  help='Float parameter for the workflow. Format: "<name>:<value>".')
    parameters_group.add_argument('--list-parameter', '-lp', action='append',
                                  help='List parameter for the workflow (delimiter: ","). Format: "<name>:<value>".')
    parameters_group.add_argument('--dict-parameter', '-dp', action='append',
                                  help='Dictionary parameter for the workflow (JSON format). Format: "<name>:<value>".')


def __configure_run_action_subparser(parser):
    """
    Configure the subparser for the run action.

    :param parser: Parser to which the subparser will be added.
    """
    run_subparser = parser.add_parser('run', help='Run the workflows.', formatter_class=RawTextHelpFormatter)
    run_subparser.add_argument('--status-file', '-sf', type=str,
                               help='Path to the file where the statuses of the particular steps will be stored.')
    __create_configuration_group(run_subparser)
    __create_logging_group(run_subparser)
    __create_parameters_group(run_subparser)
    run_subparser.add_argument('workflow_name', type=str, help='Name of the workflow to run.')


def __configure_validate_action_subparser(parser):
    """
    Configure the subparser for the validate action.

    :param parser: Parser to which the subparser will be added.
    """
    validate_subparser = parser.add_parser('validate', help='Validate the workflows configuration.',
                                           formatter_class=RawTextHelpFormatter)
    validate_subparser.add_argument('--workflow-name', '-w', type=str, required=False,
                                    help='Name of the workflow to validate. If not provided, it will validate that '
                                         'required parameters have been provided and all necessary steps have been '
                                         'registered.')

    __create_configuration_group(validate_subparser)
    __create_logging_group(validate_subparser)
    __create_parameters_group(validate_subparser)


def __configure_list_action_subparser(parser):
    """
    Configure the subparser for the list action.

    :param parser: Parser to which the subparser will be added.
    """
    list_subparser = parser.add_parser('list', help='List the workflows.', formatter_class=RawTextHelpFormatter)
    configuration_group = list_subparser.add_argument_group('Configuration', 'Configuration of the workflows manager.')
    configuration_group.add_argument('--configuration-file', '-c', type=str, required=False,
                                     help='Path to the configuration file with workflows and steps. If not provided, '
                                          'then it will try to search for workflows.yaml or workflows.json in the '
                                          'current working directory.')
    __create_logging_group(list_subparser)


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
    __configure_list_action_subparser(action_subparsers)
    __configure_version_action_subparser(action_subparsers)


def get_args() -> Namespace:
    """
    Parse the command line arguments passed to the application.

    :return: Parsed arguments.
    :rtype: Namespace
    """
    parser = ArgumentParser()
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
    __add_parameters(getattr(namespace, 'parameter', None), parameters)
    __add_parameters(getattr(namespace, 'string_parameter', None), parameters, types_mapping['str'])
    __add_parameters(getattr(namespace, 'integer_parameter', None), parameters, types_mapping['int'])
    __add_parameters(getattr(namespace, 'boolean_parameter', None), parameters, types_mapping['bool'])
    __add_parameters(getattr(namespace, 'float_parameter', None), parameters, types_mapping['float'])
    __add_parameters(getattr(namespace, 'list_parameter', None), parameters, types_mapping['list'])
    __add_parameters(getattr(namespace, 'dict_parameter', None), parameters, types_mapping['dict'])
    return parameters
