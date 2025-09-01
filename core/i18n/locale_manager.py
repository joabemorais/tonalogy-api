"""
Locale Manager for handling language settings and detection.
"""

import os
from contextlib import contextmanager
from threading import local
from typing import Generator, Optional


class LocaleManager:
    """Manages locale/language settings for the application."""

    DEFAULT_LOCALE = "en"
    SUPPORTED_LOCALES = {"en", "pt_br"}

    def __init__(self) -> None:
        self._local = local()
        self._local.current_locale = self.DEFAULT_LOCALE

    @property
    def current_locale(self) -> str:
        """Get the current locale for this thread."""
        return getattr(self._local, "current_locale", self.DEFAULT_LOCALE)

    def set_locale(self, locale: str) -> None:
        """Set the locale for current thread."""
        if locale in self.SUPPORTED_LOCALES:
            self._local.current_locale = locale
        else:
            # Fallback to default if unsupported locale
            self._local.current_locale = self.DEFAULT_LOCALE

    def get_locale_from_accept_language(self, accept_language: Optional[str]) -> str:
        """
        Parse Accept-Language header and return best matching locale.

        Args:
            accept_language: HTTP Accept-Language header value

        Returns:
            Best matching supported locale or default locale
        """
        if not accept_language:
            return self.DEFAULT_LOCALE

        # Simple parsing - in production, you might want to use a more robust parser
        languages = []
        for lang_range in accept_language.split(","):
            lang_parts = lang_range.strip().split(";")
            lang = lang_parts[0].strip().lower()

            # Handle quality factor
            quality = 1.0
            if len(lang_parts) > 1 and "q=" in lang_parts[1]:
                try:
                    quality = float(lang_parts[1].split("q=")[1])
                except (ValueError, IndexError):
                    quality = 1.0

            languages.append((lang, quality))

        # Sort by quality (highest first)
        languages.sort(key=lambda x: x[1], reverse=True)

        # Find best match
        for lang, _ in languages:
            # Exact match
            if lang in self.SUPPORTED_LOCALES:
                return lang

            # Try to match language part only (e.g., 'pt' for 'pt-BR')
            lang_code = lang.split("-")[0]
            for supported in self.SUPPORTED_LOCALES:
                if supported.startswith(lang_code):
                    return supported

        return self.DEFAULT_LOCALE

    @contextmanager
    def locale_context(self, locale: str) -> Generator[None, None, None]:
        """Context manager for temporary locale changes."""
        old_locale = self.current_locale
        self.set_locale(locale)
        try:
            yield
        finally:
            self.set_locale(old_locale)


# Global instance
locale_manager = LocaleManager()
