The workflows-manager provides a Docker image that can be used to run the workflows in a Docker container. The image is
based on the `python:3.9-alpine` image and contains the workflows-manager package and its dependencies.

To use the Docker image, you need to have Docker installed on your machine. You can install Docker by following the
instructions on the [official Docker website](https://docs.docker.com/get-docker/).

To run the workflows in a Docker container, you need to mount the directory containing the workflows to the container.
By default, the container will look for the steps and workflows in the `/app` directory.

!!! example
    
    === "latest"
        ```bash
        docker run --rm -v <path to the workflow and steps on local machine>:/app dl1998/workflows-manager:latest run <workflow-name>
        ```

    === "specific version"
        ```bash
        docker run --rm -v <path to the workflow and steps on local machine>:/app dl1998/workflows-manager:{{workflows_version}} run <workflow-name>
        ```
    
    Replace `<path to the workflow and steps on local machine>` with the path to the directory containing the workflows and
    steps on your local machine, and `<workflow-name>` with the name of the workflow you want to run.

If you have your own Python dependencies that you want to use in the workflows, you can create a custom Docker image
based on the workflows-manager image. You can create a `Dockerfile` in the same directory as your workflows and steps
with the following content:

=== "latest"
    ```Dockerfile
    FROM dl1998/workflows-manager:latest

    # Install additional Python dependencies
    COPY requirements.txt /app

    RUN pip install -r requirements.txt
    ```

=== "specific version"
    ```Dockerfile
    FROM dl1998/workflows-manager:{{workflows_version}}

    # Install additional Python dependencies
    COPY requirements.txt /app

    RUN pip install -r requirements.txt
    ```

You can then build the custom Docker image using the following command, you need to run it in the same directory as the
`Dockerfile`:

```bash
docker build -t <new-workflows-manager-image> .
```

Replace `<new-workflows-manager-image>` with the name you want to give to the new Docker image. You can then use this
image to run the workflows in a Docker container.
