"""
Translation system for TonalogyAPI.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from .locale_manager import locale_manager


class Translator:
    """Main translator class that handles message translation."""
    
    def __init__(self, locales_dir: Optional[Path] = None):
        if locales_dir is None:
            locales_dir = Path(__file__).parent / "locales"
        
        self.locales_dir = locales_dir
        self._translations: Dict[str, Dict[str, Any]] = {}
        self._load_translations()
    
    def _load_translations(self) -> None:
        """Load all available translation files."""
        if not self.locales_dir.exists():
            return
        
        for locale_file in self.locales_dir.glob("*.json"):
            locale_code = locale_file.stem
            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    self._translations[locale_code] = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: Could not load translations for {locale_code}: {e}")
    
    def translate(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        """
        Translate a message key to the specified locale.
        
        Args:
            key: Message key (dot-separated for nested keys)
            locale: Target locale (uses current locale if None)
            **kwargs: Variables for string formatting
            
        Returns:
            Translated message or original key if translation not found
        """
        if locale is None:
            locale = locale_manager.current_locale
        
        # Get translation from locale or fallback to default
        translation = self._get_nested_value(
            self._translations.get(locale, {}), key
        )
        
        # Fallback to default locale if not found
        if translation is None and locale != locale_manager.DEFAULT_LOCALE:
            translation = self._get_nested_value(
                self._translations.get(locale_manager.DEFAULT_LOCALE, {}), key
            )
        
        # Final fallback to key itself
        if translation is None:
            translation = key
        
        # Format with provided variables
        try:
            return translation.format(**kwargs)
        except (KeyError, ValueError):
            return translation
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Optional[str]:
        """Get value from nested dictionary using dot notation."""
        keys = key.split('.')
        value = data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value if isinstance(value, str) else None


# Global translator instance
_translator = Translator()


def get_translator() -> Translator:
    """Get the global translator instance."""
    return _translator


def T(key: str, locale: Optional[str] = None, **kwargs) -> str:
    """
    Convenience function for translation.
    
    Args:
        key: Message key
        locale: Target locale (optional)
        **kwargs: Variables for string formatting
        
    Returns:
        Translated message
    """
    return _translator.translate(key, locale, **kwargs)


def translate_tonality(tonality_name: str, locale: Optional[str] = None) -> str:
    """
    Translate a tonality name (e.g., 'C Major' -> 'Dó Maior').
    
    Args:
        tonality_name: The tonality name to translate
        locale: Target locale (optional)
        
    Returns:
        Translated tonality name
    """
    if not tonality_name:
        return tonality_name
        
    # Try to get translation from music.tonalities section
    translation_key = f"music.tonalities.{tonality_name}"
    translated = _translator.translate(translation_key, locale)
    
    # If no translation found, return original
    if translated == translation_key:
        return tonality_name
    
    return translated


def translate_function(function_name: str, locale: Optional[str] = None) -> str:
    """
    Translate a tonal function name (e.g., 'TONIC' -> 'TÔNICA').
    
    Args:
        function_name: The function name to translate
        locale: Target locale (optional)
        
    Returns:
        Translated function name
    """
    if not function_name:
        return function_name
        
    # Try to get translation from music.functions section
    translation_key = f"music.functions.{function_name}"
    translated = _translator.translate(translation_key, locale)
    
    # If no translation found, return original
    if translated == translation_key:
        return function_name
    
    return translated
