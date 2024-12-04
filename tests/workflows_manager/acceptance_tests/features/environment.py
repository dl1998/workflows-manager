import io
import logging
import os
import shutil
import tempfile
from pathlib import Path

from behave.model import Scenario
from behave.runner import Context

from workflows_manager.dispatcher import WorkflowDispatcherBuilder


def copy_python_files(source_path: Path, destination_path: Path):
    for file in source_path.iterdir():
        if file.is_file() and file.suffix == '.py':
            file_destination = destination_path.joinpath(file.name)
            file_destination.write_text(file.read_text())


def get_logger(stream: io.StringIO):
    logger = logging.getLogger('workflows-manager')
    stream_handler = logging.StreamHandler(stream)
    logger.addHandler(stream_handler)
    return logger


def before_all(context: Context):
    context.parent_temp_path = Path(tempfile.gettempdir())
    current_path = Path(__file__)
    context.workflows_steps_path = current_path.parent.joinpath('workflows_steps')


def before_scenario(context: Context, scenario: Scenario):
    clean_name = scenario.name.replace(' ', '_').lower()
    context.temp_path = context.parent_temp_path.joinpath(clean_name)
    context.temp_path.mkdir()
    copy_python_files(context.workflows_steps_path, context.temp_path)
    context.workflow_builder = WorkflowDispatcherBuilder()
    context.logger_output = io.StringIO()
    logger = get_logger(context.logger_output)
    context.workflow_builder.logger(logger)
    os.chdir(context.temp_path)


def after_scenario(context: Context, scenario: Scenario):
    shutil.rmtree(context.temp_path)