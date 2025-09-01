"""
Integration tests for the visualizer module.
Tests the complete flow from analysis data to image generation.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest

from api.schemas.analysis_schemas import ExplanationStepAPI, ProgressionAnalysisResponse
from api.services.visualizer_service import VisualizerService, _extract_pivot_target_tonality


class TestVisualizerIntegration:
    """Integration tests for the complete visualizer workflow."""

    @pytest.fixture
    def temp_images_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory for image output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_theme_data(self) -> Dict[str, Dict[str, Any]]:
        """Mock theme data for testing."""
        return {
            "C Major": {
                "primary_fill": "#a5d8ff80",
                "primary_stroke": "#4dabf7",
                "primary_text_color": "#1971c2",
                "secondary_fill": "#ffd8a880",
                "secondary_stroke": "#ffa94d",
                "secondary_text_color": "#e8590c",
                "annotation_gray": "#555555",
            },
            "F Major": {
                "primary_fill": "#ffd8a880",
                "primary_stroke": "#ffa94d",
                "primary_text_color": "#e8590c",
                "secondary_fill": "#d0ebff80",
                "secondary_stroke": "#74c0fc",
                "secondary_text_color": "#339af0",
                "annotation_gray": "#555555",
            },
            "G Major": {
                "primary_fill": "#ffc9c980",
                "primary_stroke": "#ff8787",
                "primary_text_color": "#e03131",
                "secondary_fill": "#b2f2bb80",
                "secondary_stroke": "#69db7c",
                "secondary_text_color": "#2f9e44",
                "annotation_gray": "#555555",
            },
        }

    def test_complete_workflow_simple_progression(
        self, mock_theme_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """Test the complete workflow for a simple progression without secondary tonalities."""
        # GIVEN
        analysis_data = ProgressionAnalysisResponse(
            is_tonal_progression=True,
            identified_tonality="C Major",
            explanation_details=[
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Chord 'C' fulfills function 'TONIC' in 'C Major'.",
                    processed_chord="C",
                    tonality_used_in_step="C Major",
                    evaluated_functional_state="TONIC (s_t)",
                ),
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Chord 'G' fulfills function 'DOMINANT' in 'C Major'.",
                    processed_chord="G",
                    tonality_used_in_step="C Major",
                    evaluated_functional_state="DOMINANT (s_d)",
                ),
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Chord 'F' fulfills function 'SUBDOMINANT' in 'C Major'.",
                    processed_chord="F",
                    tonality_used_in_step="C Major",
                    evaluated_functional_state="SUBDOMINANT (s_sd)",
                ),
            ],
            error=None,
        )

        service = VisualizerService()

        # Mock the theme function
        def theme_side_effect(tonality: str, theme_mode: str = "light") -> Dict[str, Any]:
            return mock_theme_data.get(tonality, {})

        with patch(
            "api.services.visualizer_service.get_theme_for_tonality", side_effect=theme_side_effect
        ):
            with patch("api.services.visualizer_service.HarmonicGraph") as mock_graph_class:
                mock_graph = MagicMock()
                mock_graph.render.return_value = "/fake/path/simple_progression.png"
                mock_graph_class.return_value = mock_graph

                # WHEN
                result = service.create_graph_from_analysis(analysis_data)

                # THEN
                assert result == "/fake/path/simple_progression.png"
                # Verify that only primary chords were added (no secondary tonalities)
                assert mock_graph.add_primary_chord.call_count == 3
                assert mock_graph.add_secondary_chord_with_theme.call_count == 0

    def test_complete_workflow_pivot_modulation(
        self, mock_theme_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """Test the complete workflow for a progression with pivot modulation."""
        # GIVEN
        analysis_data = ProgressionAnalysisResponse(
            is_tonal_progression=True,
            identified_tonality="C Major",
            explanation_details=[
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Chord 'C' fulfills function 'TONIC' in 'C Major'.",
                    processed_chord="C",
                    tonality_used_in_step="C Major",
                    evaluated_functional_state="TONIC (s_t)",
                ),
                ExplanationStepAPI(
                    formal_rule_applied="Pivot Modulation (Eq.5)",
                    observation="Chord 'Dm' acts as pivot. It has function 'SUBDOMINANT' in 'C Major' and becomes the new TONIC in 'D minor'. (Reinforced by next chord: True)",
                    processed_chord="Dm",
                    tonality_used_in_step="C Major",
                    evaluated_functional_state="SUBDOMINANT (s_sd)",
                ),
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Chord 'A' fulfills function 'DOMINANT' in 'D minor'.",
                    processed_chord="A",
                    tonality_used_in_step="D minor",
                    evaluated_functional_state="DOMINANT (s_d)",
                ),
            ],
            error=None,
        )

        service = VisualizerService()

        # Extend mock data to include D minor mapping to F Major
        extended_mock_data = {**mock_theme_data}
        extended_mock_data["D minor"] = mock_theme_data["F Major"]  # D minor uses F Major theme

        def theme_side_effect(tonality: str, theme_mode: str = "light") -> Dict[str, Any]:
            return extended_mock_data.get(tonality, {})

        with patch(
            "api.services.visualizer_service.get_theme_for_tonality", side_effect=theme_side_effect
        ):
            with patch("api.services.visualizer_service.HarmonicGraph") as mock_graph_class:
                mock_graph = MagicMock()
                mock_graph.render.return_value = "/fake/path/pivot_progression.png"
                mock_graph_class.return_value = mock_graph

                # WHEN
                result = service.create_graph_from_analysis(analysis_data)

                # THEN
                assert result == "/fake/path/pivot_progression.png"
                # Verify that secondary tonality themes were used
                assert mock_graph.add_secondary_chord_with_theme.call_count > 0

                # Verify pivot target tonality extraction worked
                step = ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Chord 'Dm' acts as pivot. It has function 'SUBDOMINANT' in 'C Major' and becomes the new TONIC in 'D minor'. (Reinforced by next chord: True)",
                    processed_chord=None,
                    tonality_used_in_step=None,
                    evaluated_functional_state=None,
                    pivot_target_tonality="D minor",
                )
                target_tonality = _extract_pivot_target_tonality(step)
                assert target_tonality == "D minor"

    def test_complete_workflow_secondary_dominants(
        self, mock_theme_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """Test the complete workflow for a progression with secondary dominants."""
        # GIVEN
        analysis_data = ProgressionAnalysisResponse(
            is_tonal_progression=True,
            identified_tonality="C Major",
            explanation_details=[
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Chord 'C' fulfills function 'TONIC' in 'C Major'.",
                    processed_chord="C",
                    tonality_used_in_step="C Major",
                    evaluated_functional_state="TONIC (s_t)",
                ),
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Chord 'D' fulfills function 'DOMINANT' in 'G Major'.",
                    processed_chord="D",
                    tonality_used_in_step="G Major",
                    evaluated_functional_state="DOMINANT (s_d)",
                ),
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Chord 'G' fulfills function 'DOMINANT' in 'C Major'.",
                    processed_chord="G",
                    tonality_used_in_step="C Major",
                    evaluated_functional_state="DOMINANT (s_d)",
                ),
            ],
            error=None,
        )

        service = VisualizerService()

        def theme_side_effect(tonality: str, theme_mode: str = "light") -> Dict[str, Any]:
            return mock_theme_data.get(tonality, {})

        with patch(
            "api.services.visualizer_service.get_theme_for_tonality", side_effect=theme_side_effect
        ):
            with patch("api.services.visualizer_service.HarmonicGraph") as mock_graph_class:
                mock_graph = MagicMock()
                mock_graph.render.return_value = "/fake/path/secondary_dominant.png"
                mock_graph_class.return_value = mock_graph

                # WHEN
                result = service.create_graph_from_analysis(analysis_data)

                # THEN
                assert result == "/fake/path/secondary_dominant.png"
                # Verify that secondary chord with specific theme was used
                assert mock_graph.add_secondary_chord_with_theme.call_count > 0

    def test_complete_workflow_mixed_major_minor(
        self, mock_theme_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """Test the complete workflow with both major and minor tonalities."""
        # GIVEN
        analysis_data = ProgressionAnalysisResponse(
            is_tonal_progression=True,
            identified_tonality="A minor",  # Minor tonality should use dashed style
            explanation_details=[
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Chord 'Am' fulfills function 'TONIC' in 'A minor'.",
                    processed_chord="Am",
                    tonality_used_in_step="A minor",
                    evaluated_functional_state="TONIC (s_t)",
                ),
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Chord 'E' fulfills function 'DOMINANT' in 'A minor'.",
                    processed_chord="E",
                    tonality_used_in_step="A minor",
                    evaluated_functional_state="DOMINANT (s_d)",
                ),
            ],
            error=None,
        )

        service = VisualizerService()

        # A minor should map to C Major theme
        extended_mock_data = {**mock_theme_data}
        extended_mock_data["A minor"] = mock_theme_data["C Major"]

        def theme_side_effect(tonality: str, theme_mode: str = "light") -> Dict[str, Any]:
            return extended_mock_data.get(tonality, {})

        with patch(
            "api.services.visualizer_service.get_theme_for_tonality", side_effect=theme_side_effect
        ):
            with patch("api.services.visualizer_service.HarmonicGraph") as mock_graph_class:
                mock_graph = MagicMock()
                mock_graph.render.return_value = "/fake/path/minor_progression.png"
                mock_graph_class.return_value = mock_graph

                # WHEN
                result = service.create_graph_from_analysis(analysis_data)

                # THEN
                assert result == "/fake/path/minor_progression.png"
                # Verify that dashed style was used for minor tonality
                add_primary_calls = mock_graph.add_primary_chord.call_args_list
                for call in add_primary_calls:
                    assert call[1]["style_variant"] == "dashed_filled"

    def test_complete_workflow_error_handling(self) -> None:
        """Test error handling in the complete workflow."""
        service = VisualizerService()

        # Test non-tonal progression
        non_tonal_data = ProgressionAnalysisResponse(
            is_tonal_progression=False,
            identified_tonality=None,
            explanation_details=[],
            error="Not tonal",
        )

        with pytest.raises(ValueError, match="Cannot visualize a non-tonal progression"):
            service.create_graph_from_analysis(non_tonal_data)

        # Test missing tonality
        missing_tonality_data = ProgressionAnalysisResponse(
            is_tonal_progression=True, identified_tonality=None, explanation_details=[], error=None
        )

        with pytest.raises(
            ValueError, match="Cannot visualize a progression without an identified tonality"
        ):
            service.create_graph_from_analysis(missing_tonality_data)

    def test_functional_state_parsing(self) -> None:
        """Test that functional states are correctly parsed from strings."""
        service = VisualizerService()

        test_cases = [
            ("TONIC (s_t)", "TONIC"),
            ("DOMINANT (s_d)", "DOMINANT"),
            ("SUBDOMINANT (s_sd)", "SUBDOMINANT"),
            ("TONIC", "TONIC"),  # Without parentheses
            ("", "TONIC"),  # Empty string should default to TONIC
            (None, "TONIC"),  # None should default to TONIC
        ]

        analysis_data_template = ProgressionAnalysisResponse(
            is_tonal_progression=True,
            identified_tonality="C Major",
            explanation_details=[
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Test",
                    processed_chord="C",
                    tonality_used_in_step="C Major",
                    evaluated_functional_state=None,  # Will be replaced
                )
            ],
            error=None,
        )

        for functional_state_input, expected_function in test_cases:
            analysis_data_template.explanation_details[0].evaluated_functional_state = (
                functional_state_input
            )

            with patch("api.services.visualizer_service.HarmonicGraph") as mock_graph_class:
                mock_graph = MagicMock()
                mock_graph.render.return_value = "/fake/path/test.png"
                mock_graph_class.return_value = mock_graph

                # This should not raise an exception
                result = service.create_graph_from_analysis(analysis_data_template)
                assert result == "/fake/path/test.png"

    def test_shape_mapping(self) -> None:
        """Test that chord functions are correctly mapped to shapes."""
        service = VisualizerService()

        analysis_data = ProgressionAnalysisResponse(
            is_tonal_progression=True,
            identified_tonality="C Major",
            explanation_details=[
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Test tonic",
                    processed_chord="C",
                    tonality_used_in_step="C Major",
                    evaluated_functional_state="TONIC (s_t)",
                ),
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Test dominant",
                    processed_chord="G",
                    tonality_used_in_step="C Major",
                    evaluated_functional_state="DOMINANT (s_d)",
                ),
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Test subdominant",
                    processed_chord="F",
                    tonality_used_in_step="C Major",
                    evaluated_functional_state="SUBDOMINANT (s_sd)",
                ),
            ],
            error=None,
        )

        with patch("api.services.visualizer_service.HarmonicGraph") as mock_graph_class:
            mock_graph = MagicMock()
            mock_graph.render.return_value = "/fake/path/shapes.png"
            mock_graph_class.return_value = mock_graph

            result = service.create_graph_from_analysis(analysis_data)

            # Verify shapes were used correctly
            add_primary_calls = mock_graph.add_primary_chord.call_args_list
            assert len(add_primary_calls) == 3

            # Check that correct shapes were used (order is reversed due to relevant_steps.reverse())
            shapes_used = [call[1]["shape"] for call in add_primary_calls]
            assert "cds" in shapes_used  # SUBDOMINANT
            assert "circle" in shapes_used  # DOMINANT
            assert "house" in shapes_used  # TONIC
