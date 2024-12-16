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

# Set working directory
WORKDIR /app

# Copy the built environment from the build stage
COPY --from=build /app/dist /app/dist

# Install the built environment
RUN pip install --no-cache-dir /app/dist/*.whl && rm -rf /app/dist

# Set the entrypoint
ENTRYPOINT ["workflows-manager"]
