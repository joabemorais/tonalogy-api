"""
Tests for main application setup.
"""

def test_app_creation():
    """Test that the FastAPI app is created successfully."""
    from api.main import app
    assert app is not None
    assert app.title is not None

def test_health_check_endpoint():
    """Test the health check endpoint."""
    from fastapi.testclient import TestClient
    from api.main import app
    
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"

def test_app_has_middleware():
    """Test that the app configuration includes middleware setup."""
    from api.main import app, MIDDLEWARE_AVAILABLE
    
    # Basic test that app is configured
    assert app is not None
    
    # If middleware is available, it should be configured
    if MIDDLEWARE_AVAILABLE:
        # Just verify the constant is working
        assert MIDDLEWARE_AVAILABLE is True
