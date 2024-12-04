import logging
import sys
from typing import Any

from workflows_manager.workflow import steps, Step


@steps.register(name='example-step')
class ExampleStep(Step):
    def perform(self, error: str = None, stderr_message: str = None, stdout_message: str = None, log_level: str = 'info',
                log_message: str = None, return_value: int = None, status: str = None) -> Any:
        if status and status == 'fail':
            self.fail()
        elif status and status == 'success':
            self.success()
        if stderr_message:
            print(stdout_message)
        if stderr_message:
            print(stderr_message, file=sys.stderr)
        if log_message:
            self.logger.log(logging._nameToLevel.get(log_level.upper()), log_message)
        if error:
            raise Exception(error)
        return return_value


@steps.register(name='get-from-context')
class GetFromContextStep(Step):
    def perform(self, key: str) -> Any:
        return self.workflow_context.get(key)


@steps.register(name='set-in-context')
class SetInContextStep(Step):
    def perform(self, key: str, value) -> None:
        self.workflow_context.set(key, value)
