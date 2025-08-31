"""
FastAPI middleware for internationalization support.
"""

try:
    from fastapi import Request, Response
    from fastapi.middleware.base import BaseHTTPMiddleware
    from typing import Callable

    FASTAPI_AVAILABLE = True
except ImportError:
    # Fallback for when FastAPI is not available
    FASTAPI_AVAILABLE = False
    Request = None
    Response = None
    BaseHTTPMiddleware = object
    Callable = None

from .locale_manager import locale_manager


if FASTAPI_AVAILABLE:

    class I18nMiddleware(BaseHTTPMiddleware):
        """Middleware to handle locale detection and setting."""

        async def dispatch(self, request: Request, call_next: Callable) -> Response:
            """Process request and set appropriate locale."""

            # Try to get locale from query parameter first
            locale = request.query_params.get("lang")

            # If not in query params, try header
            if not locale:
                accept_language = request.headers.get("accept-language")
                locale = locale_manager.get_locale_from_accept_language(accept_language)

            # Set locale for current request
            locale_manager.set_locale(locale)

            # Process request
            response = await call_next(request)

            # Optionally add locale info to response headers
            response.headers["Content-Language"] = locale_manager.current_locale

            return response

else:

    class I18nMiddleware:
        """Dummy middleware when FastAPI is not available."""

        def __init__(self, *args, **kwargs):
            pass

        def __call__(self, *args, **kwargs):
            pass
