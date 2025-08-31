"""Internationalization (i18n) package for TonalogyAPI."""

from .locale_manager import LocaleManager, locale_manager
from .translator import T, get_translator, translate_function, translate_tonality

__all__ = [
    "locale_manager",
    "LocaleManager",
    "get_translator",
    "T",
    "translate_tonality",
    "translate_function",
]

from .locale_manager import LocaleManager
from .translator import T, get_translator

try:
    from .middleware import I18nMiddleware

    __all__ = ["get_translator", "T", "LocaleManager", "I18nMiddleware"]
except ImportError:
    __all__ = ["get_translator", "T", "LocaleManager"]
