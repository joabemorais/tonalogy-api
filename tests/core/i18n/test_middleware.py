"""
Tests for I18n middleware functionality.
"""

import pytest
from unittest.mock import MagicMock

try:
    from core.i18n.middleware import I18nMiddleware
    from core.i18n.locale_manager import locale_manager
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestI18nMiddleware:
    """Test cases for I18n middleware."""

    def test_middleware_instantiation(self):
        """Test that middleware can be instantiated."""
        middleware = I18nMiddleware(app=MagicMock())
        assert middleware is not None

    def test_middleware_with_mock_locale_manager(self):
        """Test middleware interaction with locale manager."""
        # Test that locale manager can be set
        original_locale = locale_manager.current_locale
        locale_manager.set_locale("pt_br")
        assert locale_manager.current_locale == "pt_br"
        
        # Reset
        locale_manager.set_locale(original_locale)


@pytest.mark.skipif(FASTAPI_AVAILABLE, reason="Testing dummy middleware when FastAPI unavailable")
def test_dummy_middleware():
    """Test dummy middleware when FastAPI is not available."""
    from core.i18n.middleware import I18nMiddleware
    
    # Should be able to instantiate without error
    middleware = I18nMiddleware()
    
    # Should be able to call without error
    middleware()
