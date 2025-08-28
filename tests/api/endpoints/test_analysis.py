from typing import Any, Dict
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api.endpoints.analysis import get_analysis_service

# Import our FastAPI application and the dependencies we'll replace
from api.main import app
from api.schemas.analysis_schemas import ProgressionAnalysisResponse
from api.services.analysis_service import TonalAnalysisService

# --- Test Setup ---

# Create a test client that can make calls to our API
client = TestClient(app)

# --- Endpoint Tests ---


def test_analyze_endpoint_success() -> None:
    """
    Tests a successful call to the /analyze endpoint.
    """
    # GIVEN
    # Create a mock of the analysis service that returns a predictable success response
    mock_service = MagicMock(spec=TonalAnalysisService)
    mock_response_data: Dict[str, Any] = {
        "is_tonal_progression": True,
        "identified_tonality": "C Major",
        "explanation_details": [
            {
                "formal_rule_applied": "Overall Success",
                "observation": "Progression identified as tonal.",
                "tonality_used_in_step": "C Major",
                "processed_chord": "C",
                "evaluated_functional_state": "TONIC (s_t)",
            }
        ],
        "error": None,
    }
    # Use our Pydantic schema to create the response object
    mock_service.analyze_progression.return_value = ProgressionAnalysisResponse(
        **mock_response_data
    )

    # Replace the real dependency with our mock using FastAPI's mechanism
    app.dependency_overrides[get_analysis_service] = lambda: mock_service

    # The request body we'll send
    request_payload: Dict[str, Any] = {"chords": ["C", "G", "C"]}

    # WHEN
    response = client.post("/analyze", json=request_payload)

    # THEN
    assert response.status_code == 200
    response_data: Dict[str, Any] = response.json()
    assert response_data["is_tonal_progression"] is True
    assert response_data["identified_tonality"] == "C Major"
    assert "explanation_details" in response_data


def test_analyze_endpoint_bad_request_known_error() -> None:
    """
    Tests if the endpoint returns a 400 error when the service detects a known problem.
    """
    # GIVEN
    # Simulate the service returning a known error (e.g., tonality not found)
    mock_service = MagicMock(spec=TonalAnalysisService)
    mock_response_data: Dict[str, Any] = {
        "is_tonal_progression": False,
        "identified_tonality": None,
        "explanation_details": [],
        "error": "Tonality 'D Major' is not known.",
    }
    mock_service.analyze_progression.return_value = ProgressionAnalysisResponse(
        **mock_response_data
    )
    app.dependency_overrides[get_analysis_service] = lambda: mock_service

    request_payload: Dict[str, Any] = {"chords": ["C"], "tonalities_to_test": ["D Major"]}

    # WHEN
    response = client.post("/analyze", json=request_payload)

    # THEN
    assert response.status_code == 400
    assert response.json()["detail"] == "Tonality 'D Major' is not known."


def test_analyze_endpoint_invalid_payload() -> None:
    """
    Tests if FastAPI returns a 422 error (Unprocessable Entity) for an invalid payload,
    such as an empty chord list.
    """
    # GIVEN: a payload that violates Pydantic rules (chords cannot be empty)
    # Set up a mock service so the dependency is properly overridden
    mock_service = MagicMock(spec=TonalAnalysisService)
    app.dependency_overrides[get_analysis_service] = lambda: mock_service

    request_payload: Dict[str, Any] = {"chords": []}  # min_items=1 is violated

    # WHEN
    response = client.post("/analyze", json=request_payload)

    # THEN
    assert response.status_code == 422  # FastAPI handles this automatically


def test_analyze_endpoint_internal_server_error() -> None:
    """
    Tests if the endpoint returns a 500 error for an unexpected exception in the service.
    """
    # GIVEN
    # Simulate an unexpected exception being raised by the service
    mock_service = MagicMock(spec=TonalAnalysisService)
    mock_service.analyze_progression.side_effect = ValueError("Something unexpected happened!")
    app.dependency_overrides[get_analysis_service] = lambda: mock_service

    request_payload: Dict[str, Any] = {"chords": ["C"]}

    # WHEN
    response = client.post("/analyze", json=request_payload)

    # THEN
    assert response.status_code == 500
    assert "internal server error" in response.json()["detail"]


def test_root_endpoint():
    """
    Test the root endpoint to ensure the API is responding correctly.
    """
    # GIVEN: The test client

    # WHEN: A GET request is made to the root "/"
    response = client.get("/")

    # THEN: The response should be 200 OK and contain the welcome message
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to Tonalogy API. Visit /docs to see the API documentation."
    }


# --- Dependency Cleanup ---


@pytest.fixture(autouse=True)
def cleanup_dependencies():
    """
    A fixture that ensures dependency overrides are cleaned up
    after each test execution, ensuring test isolation.
    """
    yield
    app.dependency_overrides = {}
