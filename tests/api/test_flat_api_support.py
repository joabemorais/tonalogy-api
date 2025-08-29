"""
End-to-end test for flat notation support through the API.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app


class TestFlatAPISupport:
    """Test class for flat notation support through the API endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client for the API."""
        return TestClient(app)

    def test_analyze_progression_with_flats(self, client: TestClient) -> None:
        """Test that the analysis endpoint works with flat notation."""
        # Create a progression using flat notation
        request_data = {
            "chords": ["Bb", "Eb", "F", "Bb"],  # Simple I-IV-V-I in Bb Major
            "tonalities_to_test": []
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
            "tonalities_to_test": []
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
            "tonalities_to_test": []
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
            "tonalities_to_test": []
        }

        response = client.post("/analyze", json=request_data)
        
        # Should either work gracefully or return a meaningful error
        # The implementation should not crash
        assert response.status_code in [200, 400, 422]  # Accept various reasonable responses
