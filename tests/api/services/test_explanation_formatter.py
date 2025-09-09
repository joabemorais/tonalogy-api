"""
Tests for the ExplanationFormatter service.
"""

import pytest

from api.schemas.analysis_schemas import ExplanationStepAPI, ProgressionAnalysisResponse
from api.services.explanation_formatter import ExplanationFormatter
from core.i18n.locale_manager import locale_manager


class TestExplanationFormatter:
    """Test cases for the ExplanationFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ExplanationFormatter()
        # Set default locale to English for consistent tests
        locale_manager.set_locale("en")

    def test_format_explanation_empty_steps(self):
        """Test formatting with no explanation steps."""
        analysis = ProgressionAnalysisResponse(
            is_tonal_progression=False,
            identified_tonality=None,
            explanation_details=[],
            human_readable_explanation=None,
            error=None,
        )

        result = self.formatter.format_explanation(analysis)
        assert "No analysis steps are available" in result

    def test_format_explanation_simple_tonal_progression(self):
        """Test formatting a simple tonal progression."""
        steps = [
            ExplanationStepAPI(
                formal_rule_applied="Analysis Start",
                observation="Testing progression with primary tonality: 'C Major'.",
                processed_chord=None,
                tonality_used_in_step="C Major",
                evaluated_functional_state=None,
            ),
            ExplanationStepAPI(
                formal_rule_applied="P in L",
                observation="Chord 'C' fulfills function 'TONIC' in 'C Major'.",
                processed_chord="C",
                tonality_used_in_step="C Major",
                evaluated_functional_state="TONIC (s_t)",
            ),
            ExplanationStepAPI(
                formal_rule_applied="P in L",
                observation="Chord 'F' fulfills function 'SUBDOMINANT' in 'C Major'.",
                processed_chord="F",
                tonality_used_in_step="C Major",
                evaluated_functional_state="SUBDOMINANT (s_sd)",
            ),
            ExplanationStepAPI(
                formal_rule_applied="Overall Success",
                observation="Progression identified as tonal, anchored in 'C Major'.",
                processed_chord=None,
                tonality_used_in_step="C Major",
                evaluated_functional_state=None,
            ),
        ]

        analysis = ProgressionAnalysisResponse(
            is_tonal_progression=True,
            identified_tonality="C Major",
            explanation_details=steps,
            human_readable_explanation=None,
            error=None,
        )

        result = self.formatter.format_explanation(analysis)

        # Check that key components are present
        assert "We're analyzing the chord progression" in result
        assert "C Major" in result
        assert "tonal" in result
        assert "C" in result and "F" in result
        assert "Overall" in result

    def test_format_explanation_non_tonal_progression(self):
        """Test formatting a non-tonal progression."""
        steps = [
            ExplanationStepAPI(
                formal_rule_applied="Analysis Start",
                observation="Testing progression with primary tonality: 'C Major'.",
                processed_chord=None,
                tonality_used_in_step="C Major",
                evaluated_functional_state=None,
            ),
            ExplanationStepAPI(
                formal_rule_applied="Overall Failure",
                observation="No valid analytical path found for the progression.",
                processed_chord=None,
                tonality_used_in_step=None,
                evaluated_functional_state=None,
            ),
        ]

        analysis = ProgressionAnalysisResponse(
            is_tonal_progression=False,
            identified_tonality=None,
            explanation_details=steps,
            human_readable_explanation=None,
            error=None,
        )

        result = self.formatter.format_explanation(analysis)

        # Check that it acknowledges non-tonal nature
        assert (
            "does not appear to follow traditional tonal patterns" in result
            or "non-tonal" in result.lower()
        )

    def test_format_explanation_with_pivot_modulation(self):
        """Test formatting with pivot modulation."""
        steps = [
            ExplanationStepAPI(
                formal_rule_applied="P in L",
                observation="Chord 'Dm' fulfills function 'SUBDOMINANT' in 'C Major'.",
                processed_chord="Dm",
                tonality_used_in_step="C Major",
                evaluated_functional_state="SUBDOMINANT (s_sd)",
            ),
            ExplanationStepAPI(
                formal_rule_applied="Pivot Modulation (Eq.5)",
                observation="Chord 'Dm' acts as pivot...",
                processed_chord="Dm",
                tonality_used_in_step="C Major",
                evaluated_functional_state=None,
                rule_type="pivot_modulation",
                pivot_target_tonality="F Major",
            ),
        ]

        analysis = ProgressionAnalysisResponse(
            is_tonal_progression=True,
            identified_tonality="C Major",
            explanation_details=steps,
            human_readable_explanation=None,
            error=None,
        )

        result = self.formatter.format_explanation(analysis)

        # Check that pivot modulation is mentioned
        assert "pivot" in result.lower()

    def test_portuguese_locale(self):
        """Test that Portuguese locale produces Portuguese text."""
        locale_manager.set_locale("pt_br")

        steps = [
            ExplanationStepAPI(
                formal_rule_applied="P in L",
                observation="Chord 'C' fulfills function 'TONIC' in 'C Major'.",
                processed_chord="C",
                tonality_used_in_step="Dó Maior",
                evaluated_functional_state="TONICA (s_t)",
            )
        ]

        analysis = ProgressionAnalysisResponse(
            is_tonal_progression=True,
            identified_tonality="Dó Maior",
            explanation_details=steps,
            human_readable_explanation=None,
            error=None,
        )

        result = self.formatter.format_explanation(analysis)

        # Check for Portuguese text
        assert "Estamos analisando" in result
        assert "Dó Maior" in result

    def test_authentic_cadence_pattern_detection(self):
        """Test detection of authentic cadence patterns."""
        # Test the private method directly
        functions = ["TONIC", "SUBDOMINANT", "DOMINANT", "TONIC"]
        result = self.formatter._is_authentic_cadence_pattern(functions)
        assert result is True

        # Test without authentic cadence
        functions = ["TONIC", "SUBDOMINANT", "TONIC"]
        result = self.formatter._is_authentic_cadence_pattern(functions)
        assert result is False

    def test_plagal_cadence_pattern_detection(self):
        """Test detection of plagal cadence patterns."""
        # Test the private method directly
        functions = ["TONIC", "SUBDOMINANT", "TONIC", "DOMINANT"]
        result = self.formatter._is_plagal_cadence_pattern(functions)
        assert result is True

        # Test without plagal cadence
        functions = ["TONIC", "DOMINANT", "TONIC"]
        result = self.formatter._is_plagal_cadence_pattern(functions)
        assert result is False

    def teardown_method(self):
        """Clean up after each test."""
        # Reset locale to English
        locale_manager.set_locale("en")
