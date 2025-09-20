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
            "does not establish a clear tonal center" in result
            or "modal, atonal, or follow non-traditional harmonic patterns" in result
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

    def test_format_non_tonal_progression(self):
        """Test handling non-tonal progression results."""
        # GIVEN: Empty progression
        result = ProgressionAnalysisResponse(
            is_tonal_progression=False,
            explanation_details=[],
            human_readable_explanation="Non-tonal progression"
        )
        
        # WHEN: Formatting the explanation
        formatted = self.formatter.format_explanation(result)
        
        # THEN: Should handle empty progression gracefully
        assert formatted is not None
        assert isinstance(formatted, str)

    def test_connect_descriptions_with_transitions_single(self):
        """Test connecting single description."""
        descriptions = ["First description"]
        result = self.formatter._connect_descriptions_with_transitions(descriptions)
        assert result == "First description"

    def test_connect_descriptions_with_transitions_multiple(self):
        """Test connecting multiple descriptions with transitions."""
        descriptions = ["First", "Second", "Third", "Fourth"]
        result = self.formatter._connect_descriptions_with_transitions(descriptions)
        # Should contain all descriptions and transition words
        assert "First" in result
        assert "Second" in result
        assert "Third" in result
        assert "Fourth" in result

    def test_group_by_tonality_empty(self):
        """Test grouping empty steps."""
        result = self.formatter._group_by_tonality([])
        assert result == []

    def test_group_by_tonality_with_steps(self):
        """Test grouping steps by tonality."""
        # Create mock steps with different tonalities
        step1 = ExplanationStepAPI(
            step_number=1,
            processed_chord="C",
            evaluated_functional_state="Tonic I",
            tonality_used_in_step="C major",
            raw_chord="C",
            observation="First chord",
            formal_rule_applied="Rule 1"
        )
        step2 = ExplanationStepAPI(
            step_number=2,
            processed_chord="F",
            evaluated_functional_state="Subdominant IV",
            tonality_used_in_step="C major",
            raw_chord="F",
            observation="Second chord",
            formal_rule_applied="Rule 2"
        )
        step3 = ExplanationStepAPI(
            step_number=3,
            processed_chord="Am",
            evaluated_functional_state="Tonic i",
            tonality_used_in_step="A minor",
            raw_chord="Am",
            observation="Third chord",
            formal_rule_applied="Rule 3"
        )
        
        result = self.formatter._group_by_tonality([step1, step2, step3])
        
        # Should have two groups
        assert len(result) == 2
        assert result[0][0] == "C major"  # First group tonality
        assert len(result[0][1]) == 2    # Two chords in first group
        assert result[1][0] == "A minor"  # Second group tonality
        assert len(result[1][1]) == 1    # One chord in second group

    def test_describe_function_sequence_simple(self):
        """Test describing simple function sequence."""
        chord_functions = [("C", "I"), ("G", "V")]
        result = self.formatter._describe_function_sequence(chord_functions, "C major")
        assert "C major" in result

    def test_describe_function_sequence_complex(self):
        """Test describing complex function sequence."""
        chord_functions = [("C", "I"), ("Am", "vi"), ("F", "IV"), ("G", "V")]
        result = self.formatter._describe_function_sequence(chord_functions, "C major")
        assert "C major" in result

    def test_identify_progression_patterns_single_chord(self):
        """Test pattern identification with single chord."""
        chord_functions = [("C", "I")]
        result = self.formatter._identify_progression_patterns(chord_functions, "C major")
        assert "C major" in result

    def test_identify_progression_patterns_with_cadences(self):
        """Test pattern identification with cadences."""
        # V-I progression (authentic cadence)
        chord_functions = [("G", "V"), ("C", "I")]
        result = self.formatter._identify_progression_patterns(chord_functions, "C major")
        assert "C major" in result

    def test_identify_all_cadences_empty(self):
        """Test cadence identification with empty progression."""
        result = self.formatter._identify_all_cadences([])
        assert result == ""

    def test_identify_all_cadences_single_chord(self):
        """Test cadence identification with single chord."""
        chord_functions = [("C", "I")]
        result = self.formatter._identify_all_cadences(chord_functions)
        assert result == ""

    def teardown_method(self):
        """Clean up after each test."""
        # Reset locale to English
        locale_manager.set_locale("en")
