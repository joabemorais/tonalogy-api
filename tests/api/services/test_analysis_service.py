import pytest
from unittest.mock import MagicMock, patch
from typing import List

# Classes to be tested or used
from api.services.analysis_service import TonalAnalysisService
from api.schemas.analysis_schemas import ProgressionAnalysisRequest, ProgressionAnalysisResponse
from core.domain.models import Chord, Tonality, Explanation, DetailedExplanationStep


@pytest.fixture
def mock_knowledge_base() -> MagicMock:
    """
    Creates a mock for TonalKnowledgeBase, simulating access to configuration
    and a list of known tonalities.
    """
    kb = MagicMock()

    # Simulate some known tonalities
    c_major = MagicMock(spec=Tonality)
    c_major.tonality_name = "C Major"
    g_major = MagicMock(spec=Tonality)
    g_major.tonality_name = "G Major"

    kb.all_tonalities = [c_major, g_major]
    kb.kripke_config = MagicMock()
    return kb


def test_analyze_progression_success_with_all_tonalities(mock_knowledge_base: MagicMock) -> None:
    """
    Tests the success flow when no specific tonality is requested,
    and the analyzer finds a result by testing against all known tonalities.
    """
    # GIVEN
    # Simulate that ProgressionAnalyzer will return success
    mock_analyzer_instance = MagicMock()
    success_explanation = Explanation()
    final_step = DetailedExplanationStep(
        formal_rule_applied="Overall Success",
        observation="Progression identified as tonal.",
        tonality_used_in_step=mock_knowledge_base.all_tonalities[0],  # C Major
        evaluated_functional_state=None,
        processed_chord=None,
    )
    success_explanation.steps.append(final_step)
    mock_analyzer_instance.check_tonal_progression.return_value = (True, success_explanation)

    # Patch to replace the ProgressionAnalyzer class with our mock instance
    with patch(
        "api.services.analysis_service.ProgressionAnalyzer", return_value=mock_analyzer_instance
    ):
        service: TonalAnalysisService = TonalAnalysisService(mock_knowledge_base)
        request: ProgressionAnalysisRequest = ProgressionAnalysisRequest(chords=["C", "G", "C"])

        # WHEN
        response: ProgressionAnalysisResponse = service.analyze_progression(request)

        # THEN
        assert response.is_tonal_progression is True
        assert response.identified_tonality == "C Major"
        assert response.error is None
        assert len(response.explanation_details) == 1

        # Verify that the analyzer was called with the correct arguments
        expected_chords: List[Chord] = [Chord("C"), Chord("G"), Chord("C")]
        expected_tonalities = mock_knowledge_base.all_tonalities  # All, since we didn't specify any
        mock_analyzer_instance.check_tonal_progression.assert_called_once_with(
            expected_chords, expected_tonalities
        )


def test_analyze_progression_failure(mock_knowledge_base: MagicMock) -> None:
    """
    Tests the failure flow, where the analyzer doesn't find a tonality.
    """
    # GIVEN
    mock_analyzer_instance = MagicMock()
    failure_explanation = Explanation()
    mock_analyzer_instance.check_tonal_progression.return_value = (False, failure_explanation)

    with patch(
        "api.services.analysis_service.ProgressionAnalyzer", return_value=mock_analyzer_instance
    ):
        service: TonalAnalysisService = TonalAnalysisService(mock_knowledge_base)
        request: ProgressionAnalysisRequest = ProgressionAnalysisRequest(chords=["C", "F#", "B"])

        # WHEN
        response: ProgressionAnalysisResponse = service.analyze_progression(request)

        # THEN
        assert response.is_tonal_progression is False
        assert response.identified_tonality is None
        assert response.error is None


def test_analyze_with_specific_tonalities_to_test(mock_knowledge_base: MagicMock) -> None:
    """
    Tests if the service correctly filters tonalities when specified in the request.
    """
    # GIVEN
    mock_analyzer_instance = MagicMock()
    mock_analyzer_instance.check_tonal_progression.return_value = (True, Explanation())

    with patch(
        "api.services.analysis_service.ProgressionAnalyzer", return_value=mock_analyzer_instance
    ):
        service: TonalAnalysisService = TonalAnalysisService(mock_knowledge_base)
        # Request to test only in G Major
        request: ProgressionAnalysisRequest = ProgressionAnalysisRequest(
            chords=["G", "D", "G"], tonalities_to_test=["G Major"]
        )

        # WHEN
        service.analyze_progression(request)

        # THEN
        # Verify that the analyzer was called only with G Major tonality
        call_args, _ = mock_analyzer_instance.check_tonal_progression.call_args
        passed_chords, passed_tonalities = call_args

        assert len(passed_tonalities) == 1
        assert passed_tonalities[0].tonality_name == "G Major"


def test_analyze_with_unknown_tonality_to_test(mock_knowledge_base: MagicMock) -> None:
    """
    Tests if the service returns an error when an unknown tonality is requested.
    """
    # GIVEN
    service: TonalAnalysisService = TonalAnalysisService(mock_knowledge_base)
    request: ProgressionAnalysisRequest = ProgressionAnalysisRequest(
        chords=["C", "G", "C"], tonalities_to_test=["D Major"]
    )  # Tonality not mocked

    # WHEN
    response: ProgressionAnalysisResponse = service.analyze_progression(request)

    # THEN
    assert response.is_tonal_progression is False
    assert response.error == "None of the specified tonalities are known by the system."
