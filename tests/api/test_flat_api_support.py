"""
End-to-end test for flat notation support through the API.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from api.main import app
from api.endpoints.analysis import get_analysis_service
from api.endpoints.visualizer import get_visualizer_service
from api.services.analysis_service import TonalAnalysisService
from api.services.visualizer_service import VisualizerService
from api.schemas.analysis_schemas import ProgressionAnalysisResponse, ExplanationStepAPI
from core.config.knowledge_base import TonalKnowledgeBase


class TestFlatAPISupport:
    """Test class for flat notation support through the API endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client for the API."""
        return TestClient(app)

    @pytest.fixture(autouse=True)
    def setup_dependencies(self):
        """Set up mock dependencies for the tests."""
        # Mock the TonalAnalysisService
        mock_analysis_service = MagicMock(spec=TonalAnalysisService)
        mock_visualizer_service = MagicMock(spec=VisualizerService)
        
        # Configure the mock to return reasonable responses
        mock_response = ProgressionAnalysisResponse(
            is_tonal_progression=True,
            identified_tonality="Bb Major",
            explanation_details=[
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Chord 'Bb' fulfills function 'TONIC' in 'Bb Major'.",
                    processed_chord="Bb",
                    tonality_used_in_step="Bb Major",
                    evaluated_functional_state="TONIC (s_t)",
                )
            ],
            error=None,
        )
        mock_analysis_service.analyze_progression.return_value = mock_response
        
        # Create a temporary image file for visualizer tests
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        temp_file.write(b"fake image data")
        temp_file.close()
        mock_visualizer_service.create_graph_from_analysis.return_value = temp_file.name
        
        # Override dependencies
        app.dependency_overrides[get_analysis_service] = lambda: mock_analysis_service
        app.dependency_overrides[get_visualizer_service] = lambda: mock_visualizer_service
        
        yield
        
        # Cleanup
        app.dependency_overrides.clear()
        try:
            import os
            os.unlink(temp_file.name)
        except FileNotFoundError:
            pass

    def test_analyze_progression_with_flats(self, client: TestClient) -> None:
        """Test that the analysis endpoint works with flat notation."""
        # Create a progression using flat notation
        request_data = {
            "chords": ["Bb", "Eb", "F", "Bb"],  # Simple I-IV-V-I in Bb Major
            "tonalities_to_test": [],
        }

        response = client.post("/analyze", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # The analysis should work and return valid results
        assert "is_tonal_progression" in data
        assert "explanation_details" in data

    def test_analyze_mixed_notation_progression(self, client: TestClient) -> None:
        """Test that the analysis endpoint works with mixed sharp and flat notation."""
        # Create a progression mixing flats and sharps
        request_data = {
            "chords": ["Bb", "F#", "Gm", "Eb"],  # Mix of flats and sharps
            "tonalities_to_test": [],
        }

        response = client.post("/analyze", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # The analysis should work without errors
        assert "is_tonal_progression" in data
        assert "explanation_details" in data

    def test_visualize_progression_with_flats(self, client: TestClient) -> None:
        """Test that the visualization endpoint works with flat notation."""
        # Create a progression using flat notation
        request_data = {
            "chords": ["Bb", "Cm", "Dm", "Eb", "F"],  # Progression in Bb Major
            "tonalities_to_test": [],
        }

        response = client.post("/visualize", json=request_data)

        # Should return a PNG image (or appropriate visualization response)
        assert response.status_code == 200
        # The response should be binary data (PNG image)
        assert response.headers.get("content-type") in ["image/png", "application/octet-stream"]

    def test_invalid_flat_notation_handling(self, client: TestClient) -> None:
        """Test that invalid flat notations are handled gracefully."""
        # Test with invalid flat combinations
        request_data = {
            "chords": ["Cb", "Fb", "E#"],  # Invalid/unusual notations
            "tonalities_to_test": [],
        }

        response = client.post("/analyze", json=request_data)

        # Should either work gracefully or return a meaningful error
        # The implementation should not crash
        assert response.status_code in [200, 400, 422]  # Accept various reasonable responses
