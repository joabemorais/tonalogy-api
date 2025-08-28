# Use a Python base image for your application.
# The "slim" image is a lighter version of the official image.
FROM python:3.13-slim

# Set the working directory inside the container.
WORKDIR /app

# Install necessary system dependencies.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        graphviz \
        libcairo2-dev \
        libpango1.0-dev \
        libffi-dev \
        libgirepository1.0-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry to manage Python dependencies.
RUN pip install poetry

# Copy Poetry dependency files to the container.
COPY pyproject.toml poetry.lock ./

# Install your application's Python dependencies using Poetry.
# '--without dev' ensures only production dependencies are installed.
RUN poetry install --no-root --no-interaction --no-ansi --without dev

# Copy the rest of your application code to the working directory.
COPY . .

# Expose the port that the FastAPI application will use.
EXPOSE 8000

# Define the command that will be executed to start the application.
# Poetry runs Uvicorn inside the managed virtual environment.
CMD ["poetry", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
