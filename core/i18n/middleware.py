"""
FastAPI middleware for internationalization support.
"""

from typing import Any, Callable, Optional

try:
    from fastapi import Request, Response
    from fastapi.middleware.base import BaseHTTPMiddleware  # type: ignore[import-not-found]

    FASTAPI_AVAILABLE = True
except ImportError:
    # Fallback for when FastAPI is not available
    FASTAPI_AVAILABLE = False

    class Request:  # type: ignore
        pass

    class Response:  # type: ignore
        pass

    class BaseHTTPMiddleware:  # type: ignore
        pass


from .locale_manager import locale_manager

if FASTAPI_AVAILABLE:

    class I18nMiddleware(BaseHTTPMiddleware):
        """Middleware to handle locale detection and setting."""

        async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
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

            return response  # type: ignore[no-any-return]

else:

    class I18nMiddleware:  # type: ignore
        """Dummy middleware when FastAPI is not available."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def __call__(self, *args: Any, **kwargs: Any) -> None:
            pass
