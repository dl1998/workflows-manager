Workflows is one of the core components of the workflows manager. It allows you to manage your workflows in a more
efficient way. You can create a new workflow by reusing the existing steps or workflows.

There are three types of steps that can be used in the workflows' configuration:

- **normal** - A normal step is a step that executes a single task that is defined in the code.
- **parallel** - A parallel step is a step that executes multiple steps in parallel.
- **workflow** - A workflow step is a step that executes another workflow.

The configuration of the workflows can be done using a `*.yaml` or `*.json` file. The file should contain the definition
of the workflows and its steps. You can check structure of the configuration file on
[Developers -> Workflows Syntax](../developers/workflows_syntax.md) page.

## Create a new workflow

To create a new workflow you need to create a new yaml file in your project. The file contains the definition of the
workflow and its steps.

Here is an example of a simple workflow that uses the `console-output` step:

=== "YAML"

    ```yaml title="workflows.yaml"
    workflows:
      simple-workflow:
        steps:
          - name: Say hello
            step: console-output
            parameters:
              - name: message
                value: "Hello, world!"
    ```

=== "JSON"

    ```json title="workflows.json"
    {
      "workflows": {
        "simple-workflow": {
          "steps": [
            {
              "name": "Say hello",
              "step": "console-output",
              "parameters": [
                {
                  "name": "message",
                  "value": "Hello, world!"
                }
              ]
            }
          ]
        }
      }
    }
    ```

- The `workflows` key is the root key of the yaml file. All workflows should be defined under this key.
- The `simple-workflow` key is the name of the workflow.
- The `steps` key contains the list of steps that should be executed in the workflow.
- The `name` key is the name of the step, it must be unique within the `steps`.
- The `step` key is the name of the step that should be executed. It shall match the name of the step defined in the
  step file.
- The `parameters` key contains the list of parameters that should be passed to the step.
- The `name` key is the name of the parameter that is expected by the step.
- The `value` key is the value of the parameter.

## Parallel Step

You can also create a parallel step that executes multiple steps in parallel. To create a parallel workflow you need
to define the steps under the `parallel` key.

Here is an example of a parallel workflow that executes two steps in parallel:

=== "YAML"

    ```yaml title="workflows.yaml"
    workflows:
      parallel-workflow:
        steps:
          - name: Capture message
            type: parallel
            parameters:
              - name: message
                value: "This message will be printed and logged."
            parallels:
              - name: Print message
                step: console-output
              - name: Log message
                step: log-message
    ```

=== "JSON"

    ```json title="workflows.json"
    {
      "workflows": {
        "parallel-workflow": {
          "steps": [
            {
              "name": "Capture message",
              "type": "parallel",
              "parameters": [
                {
                  "name": "message",
                  "value": "This message will be printed and logged."
                }
              ],
              "parallels": [
                {
                  "name": "Print message",
                  "step": "console-output"
                },
                {
                  "name": "Log message",
                  "step": "log-message"
                }
              ]
            }
          ]
        }
      }
    }
    ```

- The `type` key is used to define the type of the step. The `parallel` type is used to execute multiple steps in
  parallel.
- The `parallels` key contains the list of steps that should be executed in parallel.

In this example the `Capture message` step is a parallel step that print and logs the message in parallel. It has its
own set of parameters defined under the `parameters` key. This will automatically inject the parameters into the steps
that are executed in parallel.

## Workflow Step

You can also create a workflow step that executes another workflow.

Here is an example of a workflow `embedded-workflow` with the step that executes the `simple-workflow` workflow:

=== "YAML"

    ```yaml title="workflows.yaml"
    workflows:
      simple-workflow:
        steps:
          - name: Say hello
            step: console-output
      embedded-workflow:
        steps:
          - name: Execute simple workflow
            type: workflow
            workflow: simple-workflow
            parameters:
              - name: message
                value: "Hello, world!"
    ```

=== "JSON"

    ```json title="workflows.json"
    {
      "workflows": {
        "simple-workflow": {
          "steps": [
            {
              "name": "Say hello",
              "step": "console-output"
            }
          ]
        },
        "embedded-workflow": {
          "steps": [
            {
              "name": "Execute simple workflow",
              "type": "workflow",
              "workflow": "simple-workflow",
              "parameters": [
                {
                  "name": "message",
                  "value": "Hello, world!"
                }
              ]
            }
          ]
        }
      }
    }
    ```

- The `type` key is used to define the type of the step. The `workflow` type is used to execute another workflow.
- The `workflow` key is the name of the workflow that should be executed.

In this example the `Execute simple workflow` step is a workflow step that executes the `simple-workflow` workflow. It
has its own set of parameters defined under the `parameters` key. This will automatically inject the parameters into the
steps that are executed in the workflow.

## Template Data

You can also use template data in the workflow configuration. The template data can be used to inject dynamic values
into the workflow configuration. Currently, the template data is supported only for the following fields:

- `name`
- `step`
- `workflow`
- `parameters[*].value`

To inject the template data into the attribute, you need to define a new variable in the `parameters`. After that you 
can use the variable in the attribute by using the `{ variable_name }` syntax. Any variable of the type other than `str`
will be converted to a string before injecting it into the attribute, except of `parameters[*].value` that preserves the
original type. However, there is one exception: if the template variable is a string that contains additional text, it
will be treated as a string and will not be converted.

**Note:** To use `{` and `}` characters in the value of the parameter, you need to escape them by using double brackets
`{{` and `}}`.

**Example:** let's say you have a parameter `age` with the value `18` that you want to use in the `message` variable.
You can use the `age` variable in the `message` in the following way: `"Age, { age }"`, that will cause that value
assigned to message will be of `str` type, but if you use `"{ age }"` as a value for `message` variable, it will be
converted to `str`.

Here is an example of a workflow that uses the template data:

=== "YAML"

    ```yaml title="workflows.yaml"
    parameters:
      - name: name
        value: "John Doe"
    workflows:
      template-workflow:
        steps:
          - name: Say hello
            step: console-output
            parameters:
              - name: message
                value: "Hello, { name }!"
    ```

=== "JSON"

    ```json title="workflows.json"
    {
      "parameters": [
        {
          "name": "name",
          "value": "John Doe"
        }
      ],
      "workflows": {
        "template-workflow": {
          "steps": [
            {
              "name": "Say hello",
              "step": "console-output",
              "parameters": [
                {
                  "name": "message",
                  "value": "Hello, { name }!"
                }
              ]
            }
          ]
        }
      }
    }
    ```
