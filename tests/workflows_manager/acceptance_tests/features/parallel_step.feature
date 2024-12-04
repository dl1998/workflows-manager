Feature: Parallel Step
  As a user of the workflow manager
  I want to execute steps in parallel
  So that independent tasks can be executed simultaneously to improve efficiency

  Background:
    Given the workflow has enabled current path import
    And the workflow without the imports
    And the workflow with configuration file: workflows.yaml

  Scenario: Execute simple parallel steps successfully
    Given a yaml workflow configuration
      """
      workflows:
        parallel-workflow:
          steps:
            - name: Parallel Group
              type: parallel
              parallels:
                - name: Parallel Step 1
                  step: example-step
                  parameters:
                    - name: message
                      value: Step 1
                - name: Parallel Step 2
                  step: example-step
                  parameters:
                    - name: message
                      value: Step 2
      """
    And the workflow to run: parallel-workflow
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
      ^Validating parameters for the workflow: parallel-workflow$
      ^Validating parameters for the parallel: \(Parallel Group\)$
      ^Validating parameters for the parallel step: Parallel Step 1$
      ^Validating parameters for the parallel step: Parallel Step 2$
      ^Parameters validated successfully$
      ^Dispatcher validated$
      ^Initializing workflow context$
      ^Initializing steps statuses$
      ^Steps statuses initialized$
      ^Workflow context initialized$
      ^Running workflow: parallel-workflow$
      ^Running parallel steps$
      ^Running step: Parallel Step 1$
      ^Step 'Parallel Step 1' finished$
      ^Running step: Parallel Step 2$
      ^Step 'Parallel Step 2' finished$
      ^Workflow finished$
      ^Generating status file: (/[\w\.]+)+$
      ^Status file generated$
      """
    And step "Parallel Group:Parallel Step 1" shall have status: success
    And step "Parallel Group:Parallel Step 2" shall have status: success
    And step "Parallel Group" shall have status: success

  Scenario: One step in a parallel group fails
    Given a yaml workflow configuration
      """
      workflows:
        parallel-workflow:
          steps:
            - name: Parallel Group
              type: parallel
              parallels:
                - name: Failing Step
                  step: example-step
                  parameters:
                    - name: error
                      value: "Intentional failure"
                - name: Successful Step
                  step: example-step
                  parameters:
                    - name: message
                      value: Success
      """
    And the workflow to run: parallel-workflow
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
      ^Validating parameters for the workflow: parallel-workflow$
      ^Validating parameters for the parallel: \(Parallel Group\)$
      ^Validating parameters for the parallel step: Failing Step$
      ^Validating parameters for the parallel step: Successful Step$
      ^Parameters validated successfully$
      ^Dispatcher validated$
      ^Initializing workflow context$
      ^Initializing steps statuses$
      ^Steps statuses initialized$
      ^Workflow context initialized$
      ^Running workflow: parallel-workflow$
      ^Running parallel steps$
      ^Running step: Failing Step$
      ^Step 'Failing Step' failed$
      ^Running step: Successful Step$
      ^Step 'Successful Step' finished$
      ^Step 'Parallel Group' failed$
      ^Stopping workflow due to error$
      ^Workflow failed: Intentional failure$
      ^Workflow finished$
      ^Generating status file: (/[\w\.]+)+$
      ^Status file generated$
      """
    And step "Parallel Group:Failing Step" shall have status: failed
    And step "Parallel Group:Failing Step" shall have error: Intentional failure
    And step "Parallel Group:Successful Step" shall have status: success
    And step "Parallel Group" shall have status: failed
