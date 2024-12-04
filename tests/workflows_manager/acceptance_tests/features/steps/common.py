import contextlib
import io
import json
from typing import Optional

from behave import given, when, use_step_matcher
from behave.runner import Context

from workflows_manager.dispatcher import DispatcherAction

use_step_matcher('re')


@given(r'(?:a|an) (?P<file_type>yaml|json) workflow configuration')
def step_impl(context: Context, file_type: str):
    workflow_file = None
    if file_type == 'yaml':
        workflow_file = 'workflows.yaml'
    if file_type == 'json':
        workflow_file = 'workflows.json'
    if workflow_file is None:
        raise ValueError(f'Unsupported file type: {file_type}')
    context.workflow_file = context.temp_path.joinpath(workflow_file)
    with context.workflow_file.open('w') as file:
        file.write(context.text)


@given(r'the workflow has (?P<path_imports_status>disabled|enabled) current path import')
def step_impl(context: Context, path_imports_status: str):
    if path_imports_status == 'disabled':
        disabled = True
    else:
        disabled = False
    context.workflow_builder.disable_current_path_import(disabled)


@given(r'the workflow (?P<has_imports>with|without) the imports')
def step_impl(context: Context, has_imports: str):
    absolute_imports = []
    if has_imports == 'with' and context.text:
        imports = context.text.split('\n')
        for import_line in imports:
            absolute_imports.append(str(context.temp_path.joinpath(import_line).absolute().resolve()))
    context.workflow_builder.imports(absolute_imports)


@given(r'the workflow with (?:configuration file: (?P<configuration_file>.*)|default configuration file)')
def step_impl(context: Context, configuration_file: str):
    configuration_file = context.temp_path.joinpath(configuration_file)
    context.workflow_builder.configuration_file(configuration_file)


@given(r'the workflow to run: (?P<workflow>.*)')
def step_impl(context: Context, workflow: str):
    context.workflow_builder.workflow_name(workflow)


@given(r'the workflow (?:with status file: (?P<status_file>.*)|without status file)')
def step_impl(context: Context, status_file: Optional[str]):
    if status_file:
        status_file = context.temp_path.joinpath(status_file)
    context.workflow_builder.status_file(status_file)


@given(r'the workflow (?P<has_parameters>with|without) command line parameters')
def step_impl(context: Context, has_parameters: str):
    if has_parameters == 'with':
        parameters = json.loads(context.text)
    elif has_parameters == 'without':
        parameters = dict()
    else:
        raise ValueError(f'Unsupported parameters status: {has_parameters}')
    context.workflow_builder.parameters(parameters)


@when('build workflow dispatcher')
def step_impl(context: Context):
    context.workflow_dispatcher = context.workflow_builder.build()


@when('start workflow with action: (?P<action>run|validate)')
def step_impl(context: Context, action: str):
    dispatch_action = None
    if action == 'run':
        dispatch_action = DispatcherAction.RUN
    elif action == 'validate':
        dispatch_action = DispatcherAction.VALIDATE
    try:
        context.exception = None
        context.stdout = io.StringIO()
        context.stderr = io.StringIO()
        with contextlib.redirect_stdout(context.stdout), contextlib.redirect_stderr(context.stderr):
            context.workflow_dispatcher.dispatch(dispatch_action)
    except Exception as exception:
        context.exception = exception
