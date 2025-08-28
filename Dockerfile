# Use a base Python image for your application.
FROM python:3.13-slim

# Set the working directory inside the container.
WORKDIR /app

# Install necessary system dependencies.
# 'fontconfig' is essential for the system to recognize fonts.
# The other libraries are dependencies for Graphviz and CairoSVG.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        graphviz \
        libcairo2-dev \
        libpango1.0-dev \
        libffi-dev \
        libgirepository1.0-dev \
        fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create and activate a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the Python dependency file to the container.
COPY requirements.txt .

# Install the application's Python dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# --- Steps for installing the MuseJazzText.otf font ---
# 1. Create a custom directory for the fonts inside the container.
RUN mkdir -p /usr/share/fonts/truetype/custom

# 2. Copy the font file from your local project to the container's font directory.
#    Note: This assumes the path `assets/fonts/MuseJazzText.otf` is correct.
COPY assets/fonts/MuseJazzText.otf /usr/share/fonts/truetype/custom/

# 3. Update the system's font cache to make the new font available.
#    This ensures Graphviz can find and use the font.
RUN fc-cache -f -v
# -----------------------------------------------------

# Copy the rest of the application's code into the working directory.
COPY . .

# Expose the port that the FastAPI application will use.
EXPOSE 8000

# Define the command that will be executed to start the application.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
