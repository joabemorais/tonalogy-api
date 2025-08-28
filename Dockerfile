# Use a Python base image for your application.
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

# Create and activate a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the Python dependencies file to the container.
COPY requirements.txt .

# Install your application's Python dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code to the working directory.
COPY . .

# Expose the port that the FastAPI application will use.
EXPOSE 8000

# Define the command that will be executed to start the application.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
