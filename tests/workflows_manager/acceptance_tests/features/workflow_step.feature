Feature: Workflow Step
  As a user of the workflow manager
  I want to be able to execute reusable group of steps (workflow)
  So that I can reduce complexity

  Background:
    Given the workflow has enabled current path import
    And the workflow without the imports
    And the workflow with configuration file: workflows.yaml

  Scenario: Run a workflow step
    Given a yaml workflow configuration
      """
      workflows:
        normal-step:
          steps:
            - name: Normal step
              step: example-step
        workflow-step:
          steps:
            - name: Workflow step
              workflow: normal-step
              type: workflow
      """
    And the workflow to run: workflow-step
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
        ^Validating parameters for the workflow: workflow-step$
        ^Validating parameters for the workflow: normal-step \(Workflow step\)$
        ^Parameters validated successfully$
        ^Dispatcher validated$
        ^Initializing workflow context$
        ^Initializing steps statuses$
        ^Steps statuses initialized$
        ^Workflow context initialized$
        ^Running workflow: workflow-step$
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

    Scenario: Execute full workflow with failed step
      Given a yaml workflow configuration
        """
        workflows:
          normal-step:
            steps:
              - name: Failing step
                step: example-step
                stop_on_error: false
                parameters:
                  - name: error
                    value: Error message
              - name: Normal step
                step: example-step
          workflow-step:
            steps:
              - name: Workflow step
                workflow: normal-step
                type: workflow
        """
      And the workflow to run: workflow-step
      And the workflow without command line parameters
      And the workflow with status file: status.json
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
          ^Validating parameters for the workflow: workflow-step$
          ^Validating parameters for the workflow: normal-step \(Workflow step\)$
          ^Parameters validated successfully$
          ^Dispatcher validated$
          ^Initializing workflow context$
          ^Initializing steps statuses$
          ^Steps statuses initialized$
          ^Workflow context initialized$
          ^Running workflow: workflow-step$
          ^Running workflow: normal-step$
          ^Running step: Failing step$
          ^Step 'Failing step' failed$
          ^Running step: Normal step$
          ^Step 'Normal step' finished$
          ^Workflow finished$
          ^Generating status file: (/[\w\.]+)+$
          ^Status file generated$
          """
      And step "Workflow step:Failing step" shall have status: failed
      And step "Workflow step:Failing step" shall have error: Error message
      And step "Workflow step:Normal step" shall have status: success
      And step "Workflow step" shall have status: success
