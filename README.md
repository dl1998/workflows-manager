# Workflows Manager

<!-- [START BADGES] -->
<!-- Please keep comment here to allow auto update -->
[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://github.com/dl1998/workflows-manager/blob/main/LICENSE.md)
[![Language](https://img.shields.io/badge/Language-Python-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg?style=for-the-badge)](https://github.com/dl1998/workflows-manager/pulls)
[![TestPyPi 0.3.0](https://img.shields.io/badge/TestPyPi-0.3.0-brightgreen.svg?style=for-the-badge)](https://test.pypi.org/project/workflows-manager/)
[![PyPi 0.3.0](https://img.shields.io/badge/PyPi-0.3.0-brightgreen.svg?style=for-the-badge)](https://pypi.org/project/workflows-manager/)
[![Coverage 99%](https://img.shields.io/badge/Coverage-99%25-green.svg?style=for-the-badge)](https://codecov.io/gh/dl1998/workflows-manager)
[![dl1998/workflows-manager](https://img.shields.io/badge/Docker-dl1998%2Fworkflows--manager-blue?style=for-the-badge&logo=docker&color=%232496ED)](https://hub.docker.com/repository/docker/dl1998/workflows-manager)
<!-- [END BADGES] -->

Workflows manager is a tool that allows you to manage your workflows in a more efficient way. It provides a simple and
intuitive way to create a new workflow from the defined steps. You can create a new workflow by reusing the existing
steps or workflows.

## Official Documentation

The official documentation is available on [GitHub Pages](https://dl1998.github.io/workflows-manager/).

## Installation

You can install workflows manager using pip. It is recommended to use pip together with virtual environment (venv).

```shell
python3 -m pip install workflows-manager
```

## Usage

To run the workflows manager, you can use the following command:

```shell
workflows-manager -c <path_to_workflows_configuration> run <workflow_name>
```

More options are available, you can check them using the following command:

```shell
workflows-manager --help
```

Or, you can check [the official documentation](https://dl1998.github.io/workflows-manager/latest/setup/cli/) for more
information.
