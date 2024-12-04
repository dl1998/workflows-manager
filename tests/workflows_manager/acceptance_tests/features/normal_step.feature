Feature: Normal Step
  As a user of the workflow manager
  I want to execute steps
  So that I can perform specific tasks

  Scenario: Run a normal step with yaml configuration
    Given an yaml workflow configuration
      """
      workflows:
        normal-step:
          steps:
            - name: Normal step
              step: example-step
      """
    And the workflow has enabled current path import
    And the workflow without the imports
    And the workflow with configuration file: workflows.yaml
    And the workflow to run: normal-step
    And the workflow without status file
    And the workflow with command line parameters
      """
      {
        "stdout_message": "Stdout message",
        "stderr_message": "Stderr message",
        "return_value": 123
      }
      """
    When build workflow dispatcher
    And start workflow with action: run
    Then the log shall contain text
        """
        ^Importing packages$
        ^Adding (/\w+)+ to sys.path$
        ^Importing modules from (/\w+)+$
        ^Importing module steps$
        ^All modules from (/\w+)+ have been imported$
        ^All packages have been imported$
        ^Validating dispatcher$
        ^Validating parameters for the workflow: normal-step$
        ^Parameters validated successfully$
        ^Dispatcher validated$
        ^Initializing workflow context$
        ^Initializing steps statuses$
        ^Steps statuses initialized$
        ^Workflow context initialized$
        ^Running workflow: normal-step$
        ^Running step: Normal step$
        ^Step 'Normal step' finished$
        ^Workflow finished$
        """
    And the stdout shall contain text
        """
        Stdout message
        """
    And the stderr shall contain text
        """
        Stderr message
        """

  Scenario: Run a normal step with json configuration
    Given a json workflow configuration
      """
      {
        "workflows": {
          "normal-step": {
            "steps": [
              {
                "name": "Normal step",
                "step": "example-step"
              }
            ]
          }
        }
      }
      """
    And the workflow has enabled current path import
    And the workflow without the imports
    And the workflow with configuration file: workflows.json
    And the workflow to run: normal-step
    And the workflow without status file
    And the workflow with command line parameters
      """
      {
        "stdout_message": "Stdout message",
        "stderr_message": "Stderr message",
        "return_value": 123
      }
      """
    When build workflow dispatcher
    And start workflow with action: run
    Then the log shall contain text
        """
        ^Importing packages$
        ^Adding (/\w+)+ to sys.path$
        ^Importing modules from (/\w+)+$
        ^Importing module steps$
        ^All modules from (/\w+)+ have been imported$
        ^All packages have been imported$
        ^Validating dispatcher$
        ^Validating parameters for the workflow: normal-step$
        ^Parameters validated successfully$
        ^Dispatcher validated$
        ^Initializing workflow context$
        ^Initializing steps statuses$
        ^Steps statuses initialized$
        ^Workflow context initialized$
        ^Running workflow: normal-step$
        ^Running step: Normal step$
        ^Step 'Normal step' finished$
        ^Workflow finished$
        """
    And the stdout shall contain text
        """
        Stdout message
        """
    And the stderr shall contain text
        """
        Stderr message
        """

  Scenario: Run a normal step with an exception
    Given an yaml workflow configuration
      """
      workflows:
        normal-step:
          steps:
            - name: Normal step
              step: example-step
      """
    And the workflow has enabled current path import
    And the workflow without the imports
    And the workflow with configuration file: workflows.yaml
    And the workflow to run: normal-step
    And the workflow with status file: status.json
    And the workflow with command line parameters
      """
      {
        "error": "Exception message"
      }
      """
    When build workflow dispatcher
    And start workflow with action: run
    And read status file: status.json
    Then the log shall contain text
      """
      ^Importing packages$
      ^Adding (/\w+)+ to sys.path$
      ^Importing modules from (/\w+)+$
      ^Importing module steps$
      ^All modules from (/\w+)+ have been imported$
      ^All packages have been imported$
      ^Validating dispatcher$
      ^Validating parameters for the workflow: normal-step$
      ^Parameters validated successfully$
      ^Dispatcher validated$
      ^Initializing workflow context$
      ^Initializing steps statuses$
      ^Steps statuses initialized$
      ^Workflow context initialized$
      ^Running workflow: normal-step$
      ^Running step: Normal step$
      ^Step 'Normal step' failed$
      ^Stopping workflow due to error$
      ^Workflow failed: Exception message$
      ^Workflow finished$
      """
    And step "Normal step" shall have status: failed
    And step "Normal step" shall have error: Exception message

  Scenario: Run a normal step with capturing data
    Given an yaml workflow configuration
      """
      workflows:
        normal-step:
          steps:
            - name: Normal step
              step: example-step
              capture_stdout: true
              capture_stderr: true
      """
    And the workflow has disabled current path import
    And the workflow with the imports
      """
      ./
      """
    And the workflow with configuration file: workflows.yaml
    And the workflow to run: normal-step
    And the workflow with status file: status.json
    And the workflow with command line parameters
      """
      {
        "stdout_message": "stdout text",
        "stderr_message": "stderr text",
        "log_message": "log text",
        "log_level": "debug",
        "status": "fail",
        "return_value": 123
      }
      """
    When build workflow dispatcher
    And start workflow with action: run
    And read status file: status.json
    Then the log shall contain text
      """
      ^Import from the current path is disabled$
      ^Importing packages$
      ^Adding (/\w+)+ to sys.path$
      ^Importing modules from (/\w+)+$
      ^Importing module steps$
      ^All modules from (/\w+)+ have been imported$
      ^All packages have been imported$
      ^Validating dispatcher$
      ^Validating parameters for the workflow: normal-step$
      ^Parameters validated successfully$
      ^Dispatcher validated$
      ^Initializing workflow context$
      ^Initializing steps statuses$
      ^Steps statuses initialized$
      ^Workflow context initialized$
      ^Running workflow: normal-step$
      ^Running step: Normal step$
      ^Step 'Normal step' finished$
      ^Workflow finished$
      """
    And step "Normal step" shall have status: failed
    And step "Normal step" shall have stdout: stdout text
    And step "Normal step" shall have stderr: stderr text
    And step "Normal step" shall have return_value: 123

  Scenario: Run a workflow with multiple normal steps
    Given an yaml workflow configuration
      """
      workflows:
        normal-step:
          steps:
            - name: Set data in the context
              step: set-in-context
              parameters:
                - name: key
                  value: context_key
                - name: value
                  value: 123
            - name: Get data from the context
              step: get-from-context
              parameters:
                - name: key
                  value: context_key
      """
    And the workflow has enabled current path import
    And the workflow without the imports
    And the workflow with configuration file: workflows.yaml
    And the workflow to run: normal-step
    And the workflow with status file: status.json
    And the workflow without command line parameters
    When build workflow dispatcher
    And start workflow with action: run
    And read status file: status.json
    Then the log shall contain text
      """
      ^Importing packages$
      ^Adding (/\w+)+ to sys.path$
      ^Importing modules from (/\w+)+$
      ^Importing module steps$
      ^All modules from (/\w+)+ have been imported$
      ^All packages have been imported$
      ^Validating dispatcher$
      ^Validating parameters for the workflow: normal-step$
      ^Parameters validated successfully$
      ^Dispatcher validated$
      ^Initializing workflow context$
      ^Initializing steps statuses$
      ^Steps statuses initialized$
      ^Workflow context initialized$
      ^Running workflow: normal-step$
      ^Running step: Set data in the context$
      ^Step 'Set data in the context' finished$
      ^Running step: Get data from the context$
      ^Step 'Get data from the context' finished$
      ^Workflow finished$
      """
    And step "Set data in the context" shall have status: success
    And step "Get data from the context" shall have status: success
    And step "Get data from the context" shall have return_value: 123