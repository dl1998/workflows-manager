# Stage 1: Build dependencies and prepare the application
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-alpine AS build

# Set working directory
WORKDIR /app

# Install build tools and hatch
RUN pip install --no-cache-dir hatch

# Copy project configuration and source files
COPY pyproject.toml .
COPY LICENSE.md .
COPY README.md .
COPY src ./src

# Use hatch to build the environment and install the project
RUN hatch build

FROM python:${PYTHON_VERSION}-alpine AS runtime

# Declare a build argument for the version
ARG VERSION
ARG REVISION
ARG CREATION_DATE

# Set labels
LABEL maintainer="dima.leshcenko1998@gmail.com"
LABEL description="A Docker image for Python CLI application that allows to run custom workflows."
LABEL license="MIT"
LABEL version=$VERSION

LABEL org.opencontainers.image.title="workflows-manager"
LABEL org.opencontainers.image.description="A Docker image for Python CLI application that allows to run custom workflows."
LABEL org.opencontainers.image.version=$VERSION
LABEL org.opencontainers.image.documentation="https://dl1998.github.io/workflows-manager"
LABEL org.opencontainers.image.source="https://github.com/dl1998/workflows-manager"
LABEL org.opencontainers.image.revision=$REVISION
LABEL org.opencontainers.image.created=$CREATION_DATE

# Set working directory
WORKDIR /app

# Copy the built environment from the build stage
COPY --from=build /app/dist /app/dist

# Install the built environment
RUN pip install --no-cache-dir /app/dist/*.whl && rm -rf /app/dist

# Set the entrypoint
ENTRYPOINT ["workflows-manager"]
