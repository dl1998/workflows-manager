Workflows manager is a tool that allows you to manage your workflows in a more efficient way. It provides a simple and
intuitive way to create a new workflow from the defined steps. You can create a new workflow by reusing the existing
steps or workflows.

## Using PyPi (recommended)

Workflows manager is available as [PyPi](https://pypi.org) package. You can install it using pip, it is recommended to
use pip together with virtual environment (venv).

=== "latest"

    ```shell
    python3 -m pip install workflows-manager
    ```

=== "specific version"

    ```shell
    python3 -m pip install workflows-manager=={{workflows_version}}
    ```

## Using source code

You can also install workflows manager from the source code. You can clone the repository and install it using pip.
You may need to install [Hatch](https://hatch.pypa.io/latest/) prior to installing the workflows-manager this way.

```shell
git clone
cd workflows-manager
python3 -m pip install .
```

## Using wheel

You can also install workflows manager from the wheel file.

```shell
python3 -m pip install workflows_manager-{{workflows_version}}-py3-none-any.whl
```