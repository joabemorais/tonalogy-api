import os
import uuid
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from api.schemas.analysis_schemas import ExplanationStepAPI, ProgressionAnalysisResponse
from api.services.visualizer_service import VisualizerService, _extract_pivot_target_tonality
from visualizer.harmonic_graph import HarmonicGraph


class TestVisualizerService:
    """Test cases for VisualizerService class."""

    @pytest.fixture
    def visualizer_service(self) -> VisualizerService:
        """Create a VisualizerService instance for testing."""
        return VisualizerService()

    @pytest.fixture
    def mock_primary_progression_data(self) -> ProgressionAnalysisResponse:
        """Mock analysis data for a simple primary tonality progression."""
        steps = [
            ExplanationStepAPI(
                formal_rule_applied="P in L",
                observation="Chord 'C' fulfills function 'TONIC' in 'C Major'.",
                processed_chord="C",
                tonality_used_in_step="C Major",
                evaluated_functional_state="TONIC (s_t)",
                rule_type=None,
                tonal_function=None,
                pivot_target_tonality=None,
                raw_tonality_used_in_step=None,
            ),
            ExplanationStepAPI(
                formal_rule_applied="P in L",
                observation="Chord 'G' fulfills function 'DOMINANT' in 'C Major'.",
                processed_chord="G",
                tonality_used_in_step="C Major",
                evaluated_functional_state="DOMINANT (s_d)",
                rule_type=None,
                tonal_function=None,
                pivot_target_tonality=None,
                raw_tonality_used_in_step=None,
            ),
        ]
        return ProgressionAnalysisResponse(
            is_tonal_progression=True,
            identified_tonality="C Major",
            explanation_details=steps,
            error=None,
        )

    @pytest.fixture
    def mock_pivot_progression_data(self) -> ProgressionAnalysisResponse:
        """Mock analysis data for a progression with pivot modulation."""
        steps = [
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
        ]
        return ProgressionAnalysisResponse(
            is_tonal_progression=True,
            identified_tonality="C Major",
            explanation_details=steps,
            error=None,
        )

    @pytest.fixture
    def mock_secondary_progression_data(self) -> ProgressionAnalysisResponse:
        """Mock analysis data for a progression with secondary dominants."""
        steps = [
            ExplanationStepAPI(
                formal_rule_applied="P in L",
                observation="Chord 'D' fulfills function 'TONIC' in 'D Major'.",
                processed_chord="D",
                tonality_used_in_step="D Major",
                evaluated_functional_state="TONIC (s_t)",
            ),
            ExplanationStepAPI(
                formal_rule_applied="P in L",
                observation="Chord 'B' fulfills function 'DOMINANT' in 'E minor'.",
                processed_chord="B",
                tonality_used_in_step="E minor",
                evaluated_functional_state="DOMINANT (s_d)",
            ),
        ]
        return ProgressionAnalysisResponse(
            is_tonal_progression=True,
            identified_tonality="D Major",
            explanation_details=steps,
            error=None,
        )

    def test_extract_pivot_target_tonality_success(
        self, visualizer_service: VisualizerService
    ) -> None:
        """Test successful extraction of target tonality from pivot observation."""
        step = ExplanationStepAPI(
            formal_rule_applied="P in L",
            observation="Chord 'Dm' acts as pivot. It has function 'SUBDOMINANT' in 'C Major' and becomes the new TONIC in 'D minor'. (Reinforced by next chord: True)",
            processed_chord=None,
            tonality_used_in_step=None,
            evaluated_functional_state=None,
            rule_type=None,
            tonal_function=None,
            pivot_target_tonality="D minor",
            raw_tonality_used_in_step=None,
        )

        result = _extract_pivot_target_tonality(step)

        assert result == "D minor"

    def test_extract_pivot_target_tonality_no_match(
        self, visualizer_service: VisualizerService
    ) -> None:
        """Test extraction when observation doesn't contain target tonality pattern."""
        step = ExplanationStepAPI(
            formal_rule_applied="P in L",
            observation="Regular chord analysis without pivot information.",
            processed_chord=None,
            tonality_used_in_step=None,
            evaluated_functional_state=None,
            rule_type=None,
            tonal_function=None,
            pivot_target_tonality=None,
            raw_tonality_used_in_step=None,
        )

        result = _extract_pivot_target_tonality(step)

        assert result is None

    def test_extract_pivot_target_tonality_empty_string(
        self, visualizer_service: VisualizerService
    ) -> None:
        """Test extraction with empty observation string."""
        step = ExplanationStepAPI(
            formal_rule_applied="P in L",
            observation="",
            processed_chord=None,
            tonality_used_in_step=None,
            evaluated_functional_state=None,
            rule_type=None,
            tonal_function=None,
            pivot_target_tonality=None,
            raw_tonality_used_in_step=None,
        )

        result = _extract_pivot_target_tonality(step)

        assert result is None

    def test_create_graph_non_tonal_progression_raises_error(
        self, visualizer_service: VisualizerService
    ) -> None:
        """Test that non-tonal progression raises ValueError."""
        analysis_data = ProgressionAnalysisResponse(
            is_tonal_progression=False,
            identified_tonality=None,
            explanation_details=[],
            error="Not tonal",
        )

        with pytest.raises(ValueError, match="Cannot visualize a non-tonal progression"):
            visualizer_service.create_graph_from_analysis(analysis_data)

    def test_create_graph_no_identified_tonality_raises_error(
        self, visualizer_service: VisualizerService
    ) -> None:
        """Test that missing identified tonality raises ValueError."""
        analysis_data = ProgressionAnalysisResponse(
            is_tonal_progression=True, identified_tonality=None, explanation_details=[], error=None
        )

        with pytest.raises(
            ValueError, match="Cannot visualize a progression without an identified tonality"
        ):
            visualizer_service.create_graph_from_analysis(analysis_data)

    @patch("api.services.visualizer_service.HarmonicGraph")
    @patch("api.services.visualizer_service.get_theme_for_tonality")
    def test_create_graph_primary_progression_success(
        self,
        mock_get_theme: MagicMock,
        mock_harmonic_graph_class: MagicMock,
        visualizer_service: VisualizerService,
        mock_primary_progression_data: ProgressionAnalysisResponse,
    ) -> None:
        """Test successful graph creation for primary tonality progression."""
        # Setup mocks
        mock_theme = {"primary_stroke": "#4dabf7", "primary_fill": "#a5d8ff"}
        mock_get_theme.return_value = mock_theme
        mock_graph_instance = MagicMock()
        mock_graph_instance.render.return_value = "/fake/path/image.png"
        mock_harmonic_graph_class.return_value = mock_graph_instance

        # Execute
        result = visualizer_service.create_graph_from_analysis(mock_primary_progression_data)

        # Verify
        assert result == "/fake/path/image.png"
        mock_get_theme.assert_called_with("C Major")
        mock_harmonic_graph_class.assert_called_once()
        mock_graph_instance.add_primary_chord.assert_called()
        mock_graph_instance.render.assert_called_once()

    @patch("api.services.visualizer_service.HarmonicGraph")
    @patch("api.services.visualizer_service.get_theme_for_tonality")
    def test_create_graph_pivot_progression_detects_secondary_tonality(
        self,
        mock_get_theme: MagicMock,
        mock_harmonic_graph_class: MagicMock,
        visualizer_service: VisualizerService,
        mock_pivot_progression_data: ProgressionAnalysisResponse,
    ) -> None:
        """Test that pivot progressions correctly detect and use secondary tonalities."""
        # Setup mocks
        primary_theme = {
            "primary_stroke": "#4dabf7",
            "primary_fill": "#a5d8ff",
            "secondary_stroke": "#ffa94d",
            "annotation_gray": "#555555",
        }
        secondary_theme = {
            "primary_stroke": "#ffa94d",
            "primary_fill": "#ffd8a8",
            "secondary_stroke": "#4dabf7",
            "annotation_gray": "#555555",
        }

        def theme_side_effect(tonality: str) -> Dict[str, Any]:
            if tonality == "C Major":
                return primary_theme
            elif tonality == "D minor":
                return secondary_theme
            return {}

        mock_get_theme.side_effect = theme_side_effect
        mock_graph_instance = MagicMock()
        mock_graph_instance.render.return_value = "/fake/path/image.png"
        mock_harmonic_graph_class.return_value = mock_graph_instance

        # Execute
        result = visualizer_service.create_graph_from_analysis(mock_pivot_progression_data)

        # Verify
        assert result == "/fake/path/image.png"
        # Check that secondary tonality was detected and used
        assert mock_get_theme.call_count >= 2  # Called for both primary and secondary
        mock_get_theme.assert_any_call("C Major")
        mock_get_theme.assert_any_call("D minor")

        # Verify that secondary chord with theme was called
        assert mock_graph_instance.add_secondary_chord_with_theme.call_count > 0

    @patch("api.services.visualizer_service.HarmonicGraph")
    @patch("api.services.visualizer_service.get_theme_for_tonality")
    def test_create_graph_secondary_progression_uses_correct_theme(
        self,
        mock_get_theme: MagicMock,
        mock_harmonic_graph_class: MagicMock,
        visualizer_service: VisualizerService,
        mock_secondary_progression_data: ProgressionAnalysisResponse,
    ) -> None:
        """Test that secondary dominants use the correct secondary tonality theme."""
        # Setup mocks
        primary_theme = {
            "primary_stroke": "#69db7c",
            "primary_fill": "#b2f2bb",
            "secondary_stroke": "#ff8787",
            "annotation_gray": "#555555",
        }
        secondary_theme = {
            "primary_stroke": "#ff8787",
            "primary_fill": "#ffc9c9",
            "secondary_stroke": "#69db7c",
            "annotation_gray": "#555555",
        }

        def theme_side_effect(tonality: str) -> Dict[str, Any]:
            if tonality == "D Major":
                return primary_theme
            elif tonality == "E minor":
                return secondary_theme
            return {}

        mock_get_theme.side_effect = theme_side_effect
        mock_graph_instance = MagicMock()
        mock_graph_instance.render.return_value = "/fake/path/image.png"
        mock_harmonic_graph_class.return_value = mock_graph_instance

        # Execute
        result = visualizer_service.create_graph_from_analysis(mock_secondary_progression_data)

        # Verify
        assert result == "/fake/path/image.png"
        # Check that secondary theme was used for E minor tonality
        mock_get_theme.assert_any_call("D Major")
        mock_get_theme.assert_any_call("E minor")

        # Verify that secondary chord with specific theme was called
        assert mock_graph_instance.add_secondary_chord_with_theme.call_count > 0

    @patch("api.services.visualizer_service.uuid.uuid4")
    def test_create_graph_generates_unique_filename(
        self,
        mock_uuid: MagicMock,
        visualizer_service: VisualizerService,
        mock_primary_progression_data: ProgressionAnalysisResponse,
    ) -> None:
        """Test that each graph generation creates a unique filename."""
        mock_uuid.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")

        with patch("api.services.visualizer_service.HarmonicGraph") as mock_graph_class:
            mock_graph_instance = MagicMock()
            expected_path = str(
                Path(__file__).resolve().parent.parent.parent
                / "temp_images"
                / "12345678-1234-5678-1234-567812345678.png"
            )
            mock_graph_instance.render.return_value = expected_path
            mock_graph_class.return_value = mock_graph_instance

            result = visualizer_service.create_graph_from_analysis(mock_primary_progression_data)

            assert "12345678-1234-5678-1234-567812345678" in result

    def test_minor_tonality_uses_dashed_style(self, visualizer_service: VisualizerService) -> None:
        """Test that minor tonalities use dashed style variant."""
        analysis_data = ProgressionAnalysisResponse(
            is_tonal_progression=True,
            identified_tonality="A minor",
            explanation_details=[
                ExplanationStepAPI(
                    formal_rule_applied="P in L",
                    observation="Chord 'Am' fulfills function 'TONIC' in 'A minor'.",
                    processed_chord="Am",
                    tonality_used_in_step="A minor",
                    evaluated_functional_state="TONIC (s_t)",
                )
            ],
            error=None,
        )

        with patch("api.services.visualizer_service.HarmonicGraph") as mock_graph_class:
            mock_graph_instance = MagicMock()
            mock_graph_instance.render.return_value = "/fake/path/image.png"
            mock_graph_class.return_value = mock_graph_instance

            visualizer_service.create_graph_from_analysis(analysis_data)

            # Verify that primary chord was called with dashed_filled style
            mock_graph_instance.add_primary_chord.assert_called()
            call_args = mock_graph_instance.add_primary_chord.call_args
            assert call_args[1]["style_variant"] == "dashed_filled"

    def test_major_tonality_uses_solid_style(self, visualizer_service: VisualizerService) -> None:
        """Test that major tonalities use solid style variant."""
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
                )
            ],
            error=None,
        )

        with patch("api.services.visualizer_service.HarmonicGraph") as mock_graph_class:
            mock_graph_instance = MagicMock()
            mock_graph_instance.render.return_value = "/fake/path/image.png"
            mock_graph_class.return_value = mock_graph_instance

            visualizer_service.create_graph_from_analysis(analysis_data)

            # Verify that primary chord was called with solid_filled style
            mock_graph_instance.add_primary_chord.assert_called()
            call_args = mock_graph_instance.add_primary_chord.call_args
            assert call_args[1]["style_variant"] == "solid_filled"
