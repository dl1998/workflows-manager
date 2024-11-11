```shell
workflows-manager [OPTIONS...] <action> [ACTION OPTIONS...]
```

## Main Parser

| Argument                         | Default | Required |                         Choices                         | Description                                                                                                                                                                     |
|----------------------------------|:-------:|:--------:|:-------------------------------------------------------:|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--imports` \| `-i`              |         | `false`  |                                                         | List of paths to the workflows modules                                                                                                                                          |
| `--log-level` \| `-ll`           | `info`  | `false`  | `debug` \| `info` \| `warning` \| `error` \| `critical` | Logging level of the application.                                                                                                                                               |
| `--log-file` \| `-lf`            |         | `false`  |                                                         | Path to the log file. If not provided, it won't log to a file.                                                                                                                  |
| `--console-log-format` \| `-clf` | `text`  | `false`  |                    `text` \| `json`                     | Format of the log messages in the console.                                                                                                                                      |
| `--file-log-format` \| `-flf`    | `text`  | `false`  |                    `text` \| `json`                     | Format of the log messages in the file.                                                                                                                                         |
| `--configuration-file` \| `-c`   |         | `false`  |                                                         | Path to the configuration file with workflows and steps. If not provided, then it will try to search for `workflows.yaml` or `workflows.json` in the current working directory. |
| `--disable-error-codes`          | `false` | `false`  |                                                         | Disable error codes for exceptions. It changes behavior of the application to always return 0 as an exit status code.                                                           |
| `--disable-current-path-import`  | `false` | `false`  |                                                         | Disable automatic import of the modules from the current path.                                                                                                                  |
| `action`                         |         |  `true`  |            `version` \| `validate` \| `run`             | Subcommands for managing workflows.                                                                                                                                             |

## Subparser: `action`

### Parser: `version`

This parser returns the version of the application.

### Parser: `validate`

This parser validates the configuration file.

| Argument                  | Default | Required | Choices | Description                                                                                                                                                   |
|---------------------------|:-------:|:--------:|:-------:|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--workflow-name` \| `-w` |         | `false`  |         | Name of the workflow to validate. If not provided, it will validate that required parameters have been provided and all necessary steps have been registered. |

### Parser: `run`

This parser runs the workflow.

| Argument                 | Default | Required | Choices | Description                                                                 |
|--------------------------|:-------:|:--------:|:-------:|-----------------------------------------------------------------------------|
| `--status-file` \| `-sf` |         | `false`  |         | Path to the file where the statuses of the particular steps will be stored. |
| `workflow_name`          |         |          |         | Name of the workflow to run.                                                |

