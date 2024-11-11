# Tutorial: Creating and Running a JSON Cleaning Workflow

### Objective

This workflow will read a JSON file, remove any fields with `null` values, and save the cleaned JSON data to a new file.

---

## Step 1: Create the Python Steps

1. **Create a Python file** to define the steps. In this example, we'll name it `steps.py`.

2. **Add the necessary imports**:

    ```python
    import json
    from workflows_manager.workflow import steps, Step
    ```

    - `steps` is a decorator to register the step classes.
    - `Step` is the base class for all steps.

3. **Implement the `LoadJSONStep`** to load the JSON file and store it in the workflow context.

    ```python
    @steps.register(name='load-json')
    class LoadJSONStep(Step):
        """
        Step that loads JSON data from a file and stores it in the context.
        """

        def perform(self, input_json: str) -> None:
            with open(input_json, 'r') as infile:
                data = json.load(infile)

            self.workflow_context.set("json_data", data)
            self.logger.info(f'JSON data loaded from {input_json}')
    ```

4. **Implement the `RemoveNullsStep`** to recursively remove `null` fields from the JSON data stored in the context.

    ```python
    @steps.register(name='remove-nulls')
    class RemoveNullsStep(Step):
        """
        Step that removes all fields with null values from JSON data in the context.
        """
        def remove_nulls(self, data):
            if isinstance(data, dict):
                return {key: self.remove_nulls(value) for key, value in data.items() if value is not None}
            elif isinstance(data, list):
                return [self.remove_nulls(item) for item in data]
            else:
                return data

        def perform(self) -> None:
            data = self.workflow_context.get("json_data")
            cleaned_data = self.remove_nulls(data)
            self.workflow_context.set("cleaned_json_data", cleaned_data)
            self.logger.info('Null fields removed from JSON data')
    ```

5. **Implement the `SaveJSONStep`** to save the cleaned JSON data back to a file.

    ```python
    @steps.register(name='save-json')
    class SaveJSONStep(Step):
        """
        Step that saves JSON data from the context to a file.
        """

        def perform(self, output_json: str) -> None:
            data = self.workflow_context.get("cleaned_json_data")

            with open(output_json, 'w') as outfile:
                json.dump(data, outfile, indent=4)

            self.logger.info(f'Cleaned JSON data saved to {output_json}')
    ```

6. Save `steps.py` in a known location.

---

## Step 2: Create the Workflow Configuration File

1. **Create a YAML or JSON file** to configure the workflow. Name this file `workflows.yaml` or `workflows.json`.

2. **Define the Parameters**:
    - `input_json`: Path to the input JSON file.
    - `output_json`: Path where the cleaned JSON will be saved.

3. **Define the Workflow** to include each step in the correct sequence.
       
    === "YAML"
        ```yaml title="workflows.yaml"
        parameters:
          - name: input_json
            value: '<project_path>/data/input.json'
          - name: output_json
            value: '<project_path>/data/output.json'

        workflows:
          clean-json:
            steps:
              - name: Load JSON
                step: load-json
              - name: Remove null values
                step: remove-nulls
              - name: Save JSON
                step: save-json
        ```

    === "JSON"
        ```json title="workflows.json"
        {
          "parameters": [
            {
              "name": "input_json",
              "value": "<project_path>/data/input.json"
            },
            {
              "name": "output_json",
              "value": "<project_path>/data/output.json"
            }
          ],
          "workflows": {
            "clean-json": {
              "steps": [
                {
                  "name": "Load JSON",
                  "step": "load-json"
                },
                {
                  "name": "Remove null values",
                  "step": "remove-nulls"
                },
                {
                  "name": "Save JSON",
                  "step": "save-json"
                }
              ]
            }
          }
        }
        ```

    Replace `<project_path>` with the actual path to your project directory.

4. Save `workflows.yaml` or `workflows.json` in the same directory as `steps.py` or a known path.

---

## Step 3: Prepare a Sample JSON File

**Create a sample JSON file** with some fields set to `null`. Save it as `input.json` in the specified location
(`<project_path>/data/input.json`).

Example `input.json` content:

```json
{
    "name": "Alice",
    "age": 30,
    "address": {
        "street": "123 Main St",
        "city": null,
        "state": "CA",
        "postal_code": null
    },
    "contacts": [
        {"type": "email", "value": "alice@example.com"},
        {"type": "phone", "value": null}
    ],
    "preferences": {
        "newsletter": true,
        "sms_alerts": null
    },
    "membership": null
}
```

---

## Step 4: Run the Workflow

1. **Open a terminal** and navigate to the directory where you saved `steps.py`, and `workflows.yaml` or `workflows.json`.

2. **Run the Workflow with `workflows-manager`**, specifying the imports and configuration file paths:

    ```shell
    workflows-manager -i <project_path>/steps.py -c <project_path>/workflows.yaml run clean-json
    ```

    - If you'd like more detailed logging output, add `--log-level debug`.
    - If you want to save logs to a file, use `--log-file /path/to/logfile.log`.

3. **Verify Output**:
    - After the workflow completes, check `<project_path>/data/output.json`.
    - The cleaned JSON file should have all `null` fields removed.

---

## Summary

You’ve now created a simple JSON cleaning workflow using `workflows-manager`! Here’s a recap of the steps:

1. Define Python steps for loading, cleaning, and saving JSON.
2. Configure the workflow in a `workflows.yaml` or `workflows.json` file.
3. Prepare an input JSON file with `null` fields.
4. Run the workflow from the command line to generate the cleaned JSON file.

This setup is easily extensible for more complex data processing workflows.
