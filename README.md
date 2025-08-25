# Tonalogy API v2.0

*Backend Service for Tonal Analysis and Visualization*

## Overview

This API implements a computational model for tonality analysis in harmonic progressions, based on Possible Worlds Semantics. It offers two main endpoints:

1.  `/analyze`: Returns a detailed analysis in JSON format, explaining step by step how the tonality of a chord progression was identified.
2.  `/visualize`: Returns a PNG image that visually represents the analysis, illustrating concepts like tonicization and pivot chords through a "two worlds" narrative.

## Project Structure

-   **`main.py`**: Entry point of the FastAPI application.
-   **`api/`**: Contains the API logic (endpoints, services, schemas).
    -   `endpoints/`: Defines the `/analyze` and `/visualize` routes.
    -   `services/`: Orchestrates business logic. `analysis_service` calls the core, while `visualizer_service` translates the analysis into a diagram.
-   **`core/`**: The inference engine for formal harmonic analysis.
-   **`visualizer/`**: The rendering module that translates analysis data into `graphviz` diagrams with custom SVGs.
-   **`temp_images/`**: Temporary directory to store generated images before sending them to the client.

## How to Run

1.  **Install dependencies:**
    ```bash
    pip install "fastapi[all]" pandas cairosvg python-graphviz
    ```

2.  **Start the server:**
    ```bash
    uvicorn main:app --reload
    ```

3.  **Access the interactive documentation:**
    Navigate to `http://127.0.0.1:8000/docs` to test the endpoints.

## Example Usage of the `/visualize` Endpoint

Send a `POST` request to `http://127.0.0.1:8000/visualize` with the following JSON body:

```json
{
  "chords": [
    "Em",
    "A",
    "Dm",
    "G",
    "C"
  ]
}
