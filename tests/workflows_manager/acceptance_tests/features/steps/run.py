import json
import re
from typing import Dict, Optional, List

from behave import given, when, then, use_step_matcher
from behave.runner import Context

use_step_matcher('re')


def find_step(steps: List, step_path: List):
    for step in steps:
        if step.get('name', None) == step_path[0]:
            if len(step_path) == 1:
                return step
            else:
                return find_step(step.get('children', []), step_path[1:])



def get_step(status: Dict, step_path: List) -> Optional[Dict]:
    return find_step(status.get('steps', []), step_path)


@when(r'read status file: (?P<status_file>.*)')
def step_impl(context: Context, status_file: str):
    status_file = context.temp_path.joinpath(status_file)
    with status_file.open('r', encoding='utf-8') as file:
        context.status = json.load(file)


@then(r'the (?P<stream>stdout|stderr|log) shall contain text')
def step_impl(context: Context, stream: str):
    if stream == 'stdout':
        actual_text = context.stdout.getvalue().strip()
    elif stream == 'stderr':
        actual_text = context.stderr.getvalue().strip()
    elif stream == 'log':
        actual_text = context.logger_output.getvalue().strip()
    else:
        raise ValueError(f'Unsupported stream: {stream}')
    for actual, expected in zip(actual_text.split('\n'), context.text.split('\n')):
        assert re.match(expected, actual), f'Expected Pattern: {expected}, Actual Text: {actual}'


@then(r'step "(?P<step_name>.*)" shall have (?P<field>\w+): (?P<value>.*)')
def step_impl(context: Context, step_name: str, field: str, value: str):
    step = get_step(context.status, step_name.split(':'))
    if step is None:
        raise ValueError(f'Step {step_name} not found in status file')
    actual = step.get(field, None)
    if actual and isinstance(actual, str):
        actual = actual.strip()
    elif actual and isinstance(actual, int):
        value = int(value)
    assert actual == value, f'Expected: {value}, Actual: {actual}'
