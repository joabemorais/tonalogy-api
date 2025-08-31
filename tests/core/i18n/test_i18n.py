"""
Tests for the internationalization (i18n) system.
"""

import pytest
from core.i18n import T, LocaleManager, get_translator
from core.i18n.locale_manager import locale_manager


class TestTranslator:
    """Test cases for the translation system."""
    
    def test_english_translation(self):
        """Test translation in English (default)."""
        with locale_manager.locale_context("en"):
            result = T("api.welcome_message")
            expected = "Welcome to Tonalogy API. Visit /docs to see the API documentation."
            assert result == expected
    
    def test_portuguese_translation(self):
        """Test translation in Portuguese."""
        with locale_manager.locale_context("pt_br"):
            result = T("api.welcome_message")
            expected = "Bem-vindo à Tonalogy API. Visite /docs para ver a documentação da API."
            assert result == expected
    
    def test_translation_with_variables(self):
        """Test translation with variable substitution."""
        with locale_manager.locale_context("en"):
            result = T("analysis.messages.chord_fulfills_function",
                      chord_name="C", function_name="TONIC", tonality_name="C Major")
            expected = "Chord 'C' fulfills function 'TONIC' in 'C Major'."
            assert result == expected
        
        with locale_manager.locale_context("pt_br"):
            result = T("analysis.messages.chord_fulfills_function",
                      chord_name="C", function_name="TÔNICA", tonality_name="C Major")
            expected = "Acorde 'C' cumpre função 'TÔNICA' em 'C Major'."
            assert result == expected
    
    def test_fallback_to_english(self):
        """Test fallback to English when translation not found."""
        with locale_manager.locale_context("pt_br"):
            # Use a key that might not exist in Portuguese
            result = T("nonexistent.key")
            # Should fallback to the key itself since it doesn't exist in any language
            assert result == "nonexistent.key"
    
    def test_nested_keys(self):
        """Test nested key access."""
        with locale_manager.locale_context("en"):
            result = T("endpoints.analyze.summary")
            expected = "Analyzes a Tonal Harmonic Progression"
            assert result == expected


class TestLocaleManager:
    """Test cases for locale management."""
    
    def test_default_locale(self):
        """Test default locale is English."""
        assert locale_manager.DEFAULT_LOCALE == "en"
        assert locale_manager.current_locale == "en"
    
    def test_set_supported_locale(self):
        """Test setting a supported locale."""
        locale_manager.set_locale("pt_br")
        assert locale_manager.current_locale == "pt_br"
        
        # Reset to default
        locale_manager.set_locale("en")
        assert locale_manager.current_locale == "en"
    
    def test_set_unsupported_locale(self):
        """Test setting an unsupported locale falls back to default."""
        locale_manager.set_locale("fr")  # French not supported
        assert locale_manager.current_locale == "en"
    
    def test_locale_context_manager(self):
        """Test locale context manager."""
        # Start with English
        assert locale_manager.current_locale == "en"
        
        # Temporarily switch to Portuguese
        with locale_manager.locale_context("pt_br"):
            assert locale_manager.current_locale == "pt_br"
        
        # Should return to English
        assert locale_manager.current_locale == "en"
    
    def test_accept_language_parsing(self):
        """Test parsing of Accept-Language header."""
        # Test Portuguese preference
        result = locale_manager.get_locale_from_accept_language("pt-BR,pt;q=0.9,en;q=0.8")
        assert result == "pt_br"
        
        # Test English preference  
        result = locale_manager.get_locale_from_accept_language("en-US,en;q=0.9")
        assert result == "en"
        
        # Test unsupported language
        result = locale_manager.get_locale_from_accept_language("fr-FR,fr;q=0.9")
        assert result == "en"
        
        # Test None input
        result = locale_manager.get_locale_from_accept_language(None)
        assert result == "en"


class TestI18nIntegration:
    """Integration tests for the i18n system."""
    
    def test_error_messages_translation(self):
        """Test that error messages are properly translated."""
        with locale_manager.locale_context("en"):
            result = T("errors.chord_list_empty")
            assert "cannot be empty" in result
        
        with locale_manager.locale_context("pt_br"):
            result = T("errors.chord_list_empty")
            assert "não pode estar vazia" in result
    
    def test_analysis_messages_translation(self):
        """Test that analysis messages are properly translated."""
        with locale_manager.locale_context("en"):
            result = T("analysis.rules.analysis_start")
            assert result == "Analysis Start"
        
        with locale_manager.locale_context("pt_br"):
            result = T("analysis.rules.analysis_start")
            assert result == "Início da Análise"


if __name__ == "__main__":
    # Run basic tests if executed directly
    test_translator = TestTranslator()
    test_locale = TestLocaleManager()
    test_integration = TestI18nIntegration()
    
    print("Running basic i18n tests...")
    
    try:
        test_translator.test_english_translation()
        test_translator.test_portuguese_translation()
        test_locale.test_default_locale()
        test_locale.test_locale_context_manager()
        test_integration.test_error_messages_translation()
        print("✅ All basic tests passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
