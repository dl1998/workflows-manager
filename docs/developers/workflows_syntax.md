Workflows Manager implements both `*.yaml` and `*.json` file formats for defining workflows. The following sections
describe the structure of each file format.

## `parameters`
---

| Required | Type  | Default | Description                                                                                                                                                                                                                                 |
|:--------:|:-----:|---------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|    No    | array |         | Parameters section allows to define top-level parameters that will be propagated to all workflows. See also [workflow-level parameters](#workflowsworkflowparameters) and [step-level](#workflowsworkflowstepsparameters) for more details. |

!!! example "Example"

    === "YAML"
        ```yaml
        parameters:
          - name: parameter_name
            value: parameter_value
            from_context: context_variable
        ```
    
    === "JSON"
        ```json
        {
          "parameters": [
            {
              "name": "parameter_name",
              "value": "parameter_value",
              "from_context": "context_variable"
            }
          ]
        }
        ```

## `parameters[*].name`
---

| Required |  Type  | Default | Description            |
|:--------:|:------:|---------|------------------------|
|   Yes    | string |         | Name of the parameter. |

!!! example "Example"

    === "YAML"
        ```yaml
        parameters:
          - name: parameter_name
            value: parameter_value
            from_context: context_variable
        ```
    
    === "JSON"
        ```json
        {
          "parameters": [
            {
              "name": "parameter_name",
              "value": "parameter_value",
              "from_context": "context_variable"
            }
          ]
        }
        ```

## `parameters[*].value`
---

| Required |                           Type                            | Default | Description                                                                  |
|:--------:|:---------------------------------------------------------:|---------|------------------------------------------------------------------------------|
|    No    | string \| integer \| number \| boolean \| array \| object |         | Value of the parameter. Can be omitted, if `from_context` has been provided. |

!!! example "Example"

    === "YAML"
        ```yaml
        parameters:
          - name: string_parameter
            value: Example value.
          - name: integer_parameter
            value: 123
          - name: float_parameter
            value: 123.456
          - name: boolean_parameter
            value: true
          - name: list_parameter
            value:
              - item1
              - item2
          - name: dictionary_parameter
            value:
              key1: value1
              key2: value2
        ```
    
    === "JSON"
        ```json
        {
          "parameters": [
            {
              "name": "string_parameter",
              "value": "Example value."
            },
            {
              "name": "integer_parameter",
              "value": 123
            },
            {
              "name": "float_parameter",
              "value": 123.456
            },
            {
              "name": "boolean_parameter",
              "value": true
            },
            {
              "name": "list_parameter",
              "value": ["item1", "item2"]
            },
            {
              "name": "dictionary_parameter",
              "value": {
                "key1": "value1",
                "key2": "value2"
              }
            }
          ]
        }
        ```

## `parameters[*].from_context`
---

| Required |  Type  | Default | Description                                                                                                                                                                                                                             |
|:--------:|:------:|---------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|    No    | string |         | Name of the context variable to get the value from. Can be omitted, if `value` has been provided. If both `value` and `from_context` are provided, then `value` works as default value when `from_context` variable has not been found. |

!!! example "Example"

    === "YAML"
        ```yaml
        parameters:
          - name: parameter_name
            value: parameter_value
            from_context: context_variable
        ```
    
    === "JSON"
        ```json
        {
          "parameters": [
            {
              "name": "parameter_name",
              "value": "parameter_value",
              "from_context": "context_variable"
            }
          ]
        }
        ```

## `workflows`
---

| Required |  Type  | Default | Description                                                                             |
|:--------:|:------:|---------|-----------------------------------------------------------------------------------------|
|   Yes    | object |         | Workflows section allows to define multiple workflows, each containing a list of steps. |

!!! example "Example"

    === "YAML"
        ```yaml
        workflows:
          workflow_name:
            steps:
              - name: step_name
                step: registered_step_name
        ```
    
    === "JSON"
        ```json
        {
          "workflows": {
            "workflow_name": {
              "steps": [
                {
                  "name": "step_name",
                  "step": "registered_step_name"
                }
              ]
            }
          }
        }
        ```

## `workflows.<workflow>`
---

| Required |  Type  | Default | Description                                                             |
|:--------:|:------:|---------|-------------------------------------------------------------------------|
|   Yes    | object |         | Workflow object that contains workflow's steps and optional parameters. |

!!! example "Example"

    === "YAML"
        ```yaml
        workflows:
          workflow_name:
            parameters:
              - name: parameter_name
                value: parameter_value
            steps:
              - name: step_name
                step: registered_step_name
        ```
    
    === "JSON"
        ```json
        {
          "workflows": {
            "workflow_name": {
              "parameters": [
                {
                  "name": "parameter_name",
                  "value": "parameter_value"
                }
              ],
              "steps": [
                {
                  "name": "step_name",
                  "step": "registered_step_name"
                }
              ]
            }
          }
        }
        ```

## `workflows.<workflow>.parameters`
---

| Required | Type  | Default | Description                                                                                                                                                                                                                             |
|:--------:|:-----:|---------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|    No    | array |         | Parameters section allows to define workflow-specific parameters that will override top-level parameters. See also [top-level parameters](#parameters) and [step-level parameters](#workflowsworkflowstepsparameters) for more details. |

!!! example "Example"

    === "YAML"
        ```yaml
        workflows:
          workflow_name:
            parameters:
              - name: parameter_name
                value: parameter_value
                from_context: context_variable
            steps:
              - name: step_name
                step: registered_step_name
        ```
    
    === "JSON"
        ```json
        {
          "workflows": {
            "workflow_name": {
              "parameters": [
                {
                  "name": "parameter_name",
                  "value": "parameter_value",
                  "from_context": "context_variable"
                }
              ],
              "steps": [
                {
                  "name": "step_name",
                  "step": "registered_step_name"
                }
              ]
            }
          }
        }
        ```

## `workflows.<workflow>.steps`
---

| Required | Type  | Default | Description                                                        |
|:--------:|:-----:|---------|--------------------------------------------------------------------|
|   Yes    | array |         | List of steps that will be executed in the order they are defined. |

!!! example "Example"

    === "YAML"
        ```yaml
        workflows:
          workflow_name:
            steps:
              - name: step_name
                step: registered_step_name
        ```
    
    === "JSON"
        ```json
        {
          "workflows": {
            "workflow_name": {
              "steps": [
                {
                  "name": "step_name",
                  "step": "registered_step_name"
                }
              ]
            }
          }
        }
        ```

## `workflows.<workflow>.steps[*].name`
---

| Required |  Type  | Default | Description                                                    |
|:--------:|:------:|---------|----------------------------------------------------------------|
|   Yes    | string |         | Name of the step. It must be unique within the workflow scope. |

!!! example "Example"

    === "YAML"
        ```yaml
        workflows:
          workflow_name:
            steps:
              - name: step_name
                step: registered_step_name
        ```
    
    === "JSON"
        ```json
        {
          "workflows": {
            "workflow_name": {
              "steps": [
                {
                  "name": "step_name",
                  "step": "registered_step_name"
                }
              ]
            }
          }
        }
        ```

## `workflows.<workflow>.steps[*].step`
---

| Required |  Type  | Default | Description                                                                                      |
|:--------:|:------:|---------|--------------------------------------------------------------------------------------------------|
|   Yes    | string |         | Name of the step registered in the code that will be executed. It is required for `normal` type. |

!!! example "Example"

    === "YAML"
        ```yaml
        workflows:
          workflow_name:
            steps:
              - name: step_name
                step: registered_step_name
        ```
    
    === "JSON"
        ```json
        {
          "workflows": {
            "workflow_name": {
              "steps": [
                {
                  "name": "step_name",
                  "step": "registered_step_name"
                }
              ]
            }
          }
        }
        ```

## `workflows.<workflow>.steps[*].type`
---

| Required |  Type  | Default | Description                                                                                                                                                                                                                                                                |
|:--------:|:------:|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|    No    | string | normal  | Type of the step. It can be either `normal`, `workflow`, or `parallel`.<br/><ul><li>`normal` - requires `step` field to be provided</li><li>`workflow` - requires `workflow` field to be provided</li><li>`parallel` - requires `parallels` field to be provided</li></ul> |

!!! example "Example"

    === "YAML"
        ```yaml
        workflows:
          workflow_name:
            steps:
              - name: step_name
                step: registered_step_name
                type: normal
        ```
    
    === "JSON"
        ```json
        {
          "workflows": {
            "workflow_name": {
              "steps": [
                {
                  "name": "step_name",
                  "step": "registered_step_name",
                  "type": "normal"
                }
              ]
            }
          }
        }
        ```

## `workflows.<workflow>.steps[*].workflow`
---

| Required |  Type  | Default | Description                                                                                     |
|:--------:|:------:|---------|-------------------------------------------------------------------------------------------------|
|    No    | string |         | Name of the workflow, it shall exist in the workflows file. It is required for `workflow` type. |

!!! example "Example"

    === "YAML"
        ```yaml
        workflows:
          workflow_name:
            steps:
              - name: step_name
                workflow: defined_workflow_name
                type: workflow
        ```
    
    === "JSON"
        ```json
        {
          "workflows": {
            "workflow_name": {
              "steps": [
                {
                  "name": "step_name",
                  "workflow: "defined_workflow_name",
                  "type": "workflow"
                }
              ]
            }
          }
        }
        ```

## `workflows.<workflow>.steps[*].parallels`
---

| Required | Type  | Default | Description                                                                                                                                                                                                                |
|:--------:|:-----:|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|    No    | array |         | List of steps that will be executed in parallel. It is required for `parallel` type. Refer to [`workflows.<workflow>.steps[*]`](#workflowsworkflowsteps) to see full list of supported parameters for the `parallel` step. |

!!! example "Example"

    === "YAML"
        ```yaml
        workflows:
          workflow_name:
            steps:
              - name: step_name
                parallels:
                  - name: parallel_step1
                    step: registered_parallel_step1
                  - name: parallel_step2
                    step: registered_parallel_step2
                type: parallel
        ```
    
    === "JSON"
        ```json
        {
          "workflows": {
            "workflow_name": {
              "steps": [
                {
                  "name": "step_name",
                  "parallels": [
                    {
                      "name": "parallel_step1",
                      "step": "registered_parallel_step1"
                    },
                    {
                      "name": "parallel_step2",
                      "step": "registered_parallel_step2"
                    }
                  ],
                  "type": "parallel"
                }
              ]
            }
          }
        }
        ```

## `workflows.<workflow>.steps[*].capture_stdout`
---

| Required |  Type  | Default | Description                                                                               |
|:--------:|:------:|---------|-------------------------------------------------------------------------------------------|
|    No    | string | false   | The flag used to specify whether to capture standard output stream into step information. |

!!! example "Example"

    === "YAML"
        ```yaml
        workflows:
          workflow_name:
            steps:
              - name: step_name
                step: registered_step_name
                capture_stdout: true
        ```
    
    === "JSON"
        ```json
        {
          "workflows": {
            "workflow_name": {
              "steps": [
                {
                  "name": "step_name",
                  "step": "registered_step_name",
                  "capture_stdout": true
                }
              ]
            }
          }
        }
        ```

## `workflows.<workflow>.steps[*].capture_stderr`
---

| Required |  Type  | Default | Description                                                                              |
|:--------:|:------:|---------|------------------------------------------------------------------------------------------|
|    No    | string | false   | The flag used to specify whether to capture standard error stream into step information. |

!!! example "Example"

    === "YAML"
        ```yaml
        workflows:
          workflow_name:
            steps:
              - name: step_name
                step: registered_step_name
                capture_stderr: true
        ```
    
    === "JSON"
        ```json
        {
          "workflows": {
            "workflow_name": {
              "steps": [
                {
                  "name": "step_name",
                  "step": "registered_step_name",
                  "capture_stderr": true
                }
              ]
            }
          }
        }
        ```

## `workflows.<workflow>.steps[*].parameters`
---

| Required | Type  | Default | Description                                                                                                                                                                                                                                           |
|:--------:|:-----:|---------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|    No    | array |         | Parameters section allows to define step-specific parameters that will override workflow-level and top-level parameters. See also [workflow-level parameters](#workflowsworkflowparameters) and [top-level parameters](#parameters) for more details. |

!!! example "Example"

    === "YAML"
        ```yaml
        workflows:
          workflow_name:
            steps:
              - name: step_name
                step: registered_step_name
                parameters:
                  - name: parameter_name
                    value: parameter_value
                    from_context: context_variable
        ```
    
    === "JSON"
        ```json
        {
          "workflows": {
            "workflow_name": {
              "steps": [
                {
                  "name": "step_name",
                  "step": "registered_step_name",
                  "parameters": [
                    {
                      "name": "parameter_name",
                      "value": "parameter_value",
                      "from_context": "context_variable"
                    }
                  ]
                }
              ]
            }
          }
        }
        ```

## `workflows.<workflow>.steps[*].stop_on_error`
---

| Required |  Type  | Default | Description                                                                        |
|:--------:|:------:|---------|------------------------------------------------------------------------------------|
|    No    | string | false   | The flag used to specify whether to stop the workflow execution if the step fails. |

!!! example "Example"

    === "YAML"
        ```yaml
        workflows:
          workflow_name:
            steps:
              - name: step_name
                step: registered_step_name
                stop_on_error: true
        ```
    
    === "JSON"
        ```json
        {
          "workflows": {
            "workflow_name": {
              "steps": [
                {
                  "name": "step_name",
                  "step": "registered_step_name",
                  "stop_on_error": true
                }
              ]
            }
          }
        }
        ```
