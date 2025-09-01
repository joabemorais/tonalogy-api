"""
Tests for Unicode musical symbols in visualizer output.
"""

import pytest

from api.schemas.analysis_schemas import ExplanationStepAPI, ProgressionAnalysisResponse
from api.services.visualizer_service import VisualizerService
from core.domain.models import FLAT_SYMBOL, SHARP_SYMBOL


class TestUnicodeSymbolsInVisualizer:
    """Test class for Unicode musical symbols in visualizer."""

    @pytest.fixture
    def visualizer_service(self) -> VisualizerService:
        """Create a visualizer service instance."""
        return VisualizerService()

    @pytest.fixture
    def flat_progression_analysis(self) -> ProgressionAnalysisResponse:
        """Create a sample analysis with flat notation chords."""
        return ProgressionAnalysisResponse(
            is_tonal_progression=True,
            identified_tonality="A# Major",
            explanation_details=[
                ExplanationStepAPI(
                    formal_rule_applied="Analysis Start",
                    observation="Testing progression with primary tonality: 'A# Major'.",
                    processed_chord=None,
                    tonality_used_in_step="A# Major",
                    evaluated_functional_state=None,
                ),
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Chord 'Bb' fulfills function 'TONIC' in 'A# Major'.",
                    processed_chord="Bb",
                    tonality_used_in_step="A# Major",
                    evaluated_functional_state="TONIC (s_t)",
                ),
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Chord 'Eb' fulfills function 'SUBDOMINANT' in 'A# Major'.",
                    processed_chord="Eb",
                    tonality_used_in_step="A# Major",
                    evaluated_functional_state="SUBDOMINANT (s_sd)",
                ),
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Chord 'F#' fulfills function 'DOMINANT' in 'A# Major'.",
                    processed_chord="F#",
                    tonality_used_in_step="A# Major",
                    evaluated_functional_state="DOMINANT (s_d)",
                ),
            ],
            error=None,
        )

    def test_unicode_symbols_conversion_in_visualizer(
        self,
        visualizer_service: VisualizerService,
        flat_progression_analysis: ProgressionAnalysisResponse,
    ) -> None:
        """Test that the visualizer converts ASCII symbols to Unicode symbols."""
        # The visualizer should not crash and should process the analysis
        try:
            # Get the DOT source instead of rendered PNG
            dot_source = visualizer_service.get_graph_dot_source(flat_progression_analysis)

            # The output should be a valid DOT string
            assert isinstance(dot_source, str), "Visualizer should return a string"
            assert len(dot_source) > 0, "DOT source should not be empty"

            # The DOT source should contain Unicode musical symbols instead of ASCII symbols
            assert FLAT_SYMBOL in dot_source, f"DOT should contain flat symbol {FLAT_SYMBOL}"
            assert SHARP_SYMBOL in dot_source, f"DOT should contain sharp symbol {SHARP_SYMBOL}"

            # Verify that specific chord labels with Unicode symbols are present
            # Bb should become B♭
            assert f"B{FLAT_SYMBOL}" in dot_source, f"Should contain B{FLAT_SYMBOL}"
            # Eb should become E♭
            assert f"E{FLAT_SYMBOL}" in dot_source, f"Should contain E{FLAT_SYMBOL}"
            # F# should become F♯
            assert f"F{SHARP_SYMBOL}" in dot_source, f"Should contain F{SHARP_SYMBOL}"

        except Exception as e:
            pytest.fail(f"Visualizer should handle Unicode symbols gracefully: {e}")

    def test_mixed_notation_unicode_conversion(self, visualizer_service: VisualizerService) -> None:
        """Test Unicode conversion with mixed sharp and flat notation."""
        mixed_analysis = ProgressionAnalysisResponse(
            is_tonal_progression=True,
            identified_tonality="C Major",
            explanation_details=[
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Mixed notation test.",
                    processed_chord="C#",
                    tonality_used_in_step="C Major",
                    evaluated_functional_state="TONIC (s_t)",
                ),
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Mixed notation test.",
                    processed_chord="Bb",
                    tonality_used_in_step="C Major",
                    evaluated_functional_state="SUBDOMINANT (s_sd)",
                ),
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Mixed notation test.",
                    processed_chord="F#",
                    tonality_used_in_step="C Major",
                    evaluated_functional_state="DOMINANT (s_d)",
                ),
            ],
            error=None,
        )

        try:
            dot_source = visualizer_service.get_graph_dot_source(mixed_analysis)

            # Should contain both Unicode symbols
            assert FLAT_SYMBOL in dot_source, "Should contain Unicode flat symbol"
            assert SHARP_SYMBOL in dot_source, "Should contain Unicode sharp symbol"

            # Verify specific conversions
            assert f"C{SHARP_SYMBOL}" in dot_source, f"Should contain C{SHARP_SYMBOL}"
            assert f"B{FLAT_SYMBOL}" in dot_source, f"Should contain B{FLAT_SYMBOL}"
            assert f"F{SHARP_SYMBOL}" in dot_source, f"Should contain F{SHARP_SYMBOL}"

        except Exception as e:
            pytest.fail(f"Visualizer should handle mixed notation: {e}")
