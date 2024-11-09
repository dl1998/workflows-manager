One of the main features of the workflows-manager is the ability to create new workflows by reusing the existing steps.
To create a new step you need to create a new Python file in your project. The file should contain a class that inherits
from the [`Step`][workflows_manager.workflow.Step] class.

The [`Step`][workflows_manager.workflow.Step] class is a base class for all steps. It provides a simple interface to define the step behavior. The class
contains two methods: [`perform`][workflows_manager.workflow.Step.perform] and
[`configure_logger`][workflows_manager.workflow.Step.configure_logger]. The
[`perform`][workflows_manager.workflow.Step.perform] method is the main method that should contain the step logic, it
must be implemented in the child class. The [`configure_logger`][workflows_manager.workflow.Step.configure_logger]
method is used to configure the logger for the step.

Here is an example of a simple step that prints a message to the console:

```py linenums="1"
Steps.register(name="console-output") # (1)
class ConsoleOutput(Step): # (2)
    def perform(self, message: str): # (3)
        print(message) # (4)
```

1. Register the step with the name `console-output`.
2. Create a new class `ConsoleOutput` that inherits from the [`Step`][workflows_manager.workflow.Step] class.
3. Implement the [`perform`][workflows_manager.workflow.Step.perform] method that receives a string with message and
   then prints it to the console.
4. Print the message to the console.

## Configure the logger for the step

The [`configure_logger`][workflows_manager.workflow.Step.configure_logger] method is used to configure the logger for
the step. By default, the step is configured to use the parent logger from the workflows-manager. You can override this
method to configure the logger for the step.

Here is an example of a step that configures the logger to print the message to the console:

```py linenums="1"
Steps.register(name="log-message")
class LogMessage(Step):
    def configure_logger(self):
        self.logger = logging.getLogger("log-message") # (1)
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
   
    def perform(self, message: str):
        self.logger.info(message) # (2)
```

1. Create a new logger with the name `log-message` and configure it.
2. Use the logger to print the message to the console.
