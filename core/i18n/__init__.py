"""Internationalization (i18n) package for TonalogyAPI."""

from .locale_manager import locale_manager, LocaleManager
from .translator import get_translator, T, translate_tonality, translate_function

__all__ = [
    "locale_manager",
    "LocaleManager",
    "get_translator",
    "T",
    "translate_tonality",
    "translate_function",
]

from .translator import get_translator, T
from .locale_manager import LocaleManager

try:
    from .middleware import I18nMiddleware

    __all__ = ["get_translator", "T", "LocaleManager", "I18nMiddleware"]
except ImportError:
    __all__ = ["get_translator", "T", "LocaleManager"]
