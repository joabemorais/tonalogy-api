from unittest.mock import MagicMock
from typing import Any

import pytest

from core.domain.models import Chord, Explanation, Tonality
from core.logic.progression_analyzer import ProgressionAnalyzer

# We'll use fixtures for the mocks. In your real project, the fixtures for
# mock_kripke_config, c_major_tonality_mock, etc., could be moved
# to a central test file (conftest.py).


@pytest.fixture
def mock_kripke_config() -> MagicMock:
    """Creates a mock of the Kripke configuration."""
    config = MagicMock()
    mock_tonic_state = MagicMock()
    config.get_state_by_tonal_function.return_value = mock_tonic_state
    return config


@pytest.fixture
def c_major_tonality_mock() -> MagicMock:
    """Creates a mock for C Major tonality."""
    tonality = MagicMock(spec=Tonality)
    tonality.tonality_name = "C Major"
    return tonality


@pytest.fixture
def g_major_tonality_mock() -> MagicMock:
    """Creates a mock for G Major tonality."""
    tonality = MagicMock(spec=Tonality)
    tonality.tonality_name = "G Major"
    return tonality


# --- Tests ---


def test_check_progression_returns_true_on_first_tonality(
    mocker: Any, mock_kripke_config: MagicMock, c_major_tonality_mock: MagicMock
) -> None:
    """
    Verifies if the analyzer returns True when the first tested tonality is successful.
    """
    # GIVEN: a mock of SatisfactionEvaluator that always returns success
    mock_evaluator_instance = MagicMock()
    mock_evaluator_instance.evaluate_satisfaction_recursive.return_value = (True, Explanation())

    # We replace the SatisfactionEvaluator class with our mock.
    # Whenever the class is instantiated, it will return our 'mock_evaluator_instance'.
    mocker.patch(
        "core.logic.progression_analyzer.SatisfactionEvaluator",
        return_value=mock_evaluator_instance,
    )

    # WHEN: we create the ProgressionAnalyzer and run the analysis
    analyzer = ProgressionAnalyzer(mock_kripke_config, [c_major_tonality_mock])
    progression = [Chord("C"), Chord("G7")]

    success, _ = analyzer.check_tonal_progression(progression, [c_major_tonality_mock])

    # THEN: the result should be success
    assert success is True
    # We verify that the evaluator was called correctly
    mock_evaluator_instance.evaluate_satisfaction_recursive.assert_called_once()


def test_check_progression_returns_true_on_second_tonality(
    mocker: Any,
    mock_kripke_config: MagicMock,
    c_major_tonality_mock: MagicMock,
    g_major_tonality_mock: MagicMock,
) -> None:
    """
    Verifies if the analyzer continues to the second tonality if the first one fails.
    """
    # GIVEN: a mock of the evaluator that fails on the first call and succeeds on the second
    mock_evaluator_instance = MagicMock()
    mock_evaluator_instance.evaluate_satisfaction_recursive.side_effect = [
        (False, Explanation()),  # Result for the first call (C Major)
        (True, Explanation()),  # Result for the second call (G Major)
    ]
    mocker.patch(
        "core.logic.progression_analyzer.SatisfactionEvaluator",
        return_value=mock_evaluator_instance,
    )

    # WHEN: we run the analysis with two tonalities
    tonalities_to_test = [c_major_tonality_mock, g_major_tonality_mock]
    analyzer = ProgressionAnalyzer(mock_kripke_config, tonalities_to_test)  # type: ignore[arg-type]
    progression = [Chord("G"), Chord("D7")]

    success, _ = analyzer.check_tonal_progression(progression, tonalities_to_test)  # type: ignore[arg-type]

    # THEN: the final result is success and the evaluator was called twice
    assert success is True
    assert mock_evaluator_instance.evaluate_satisfaction_recursive.call_count == 2


def test_check_progression_returns_false_if_all_tonalities_fail(
    mocker: Any, mock_kripke_config: MagicMock, c_major_tonality_mock: MagicMock
) -> None:
    """
    Verifies if the analyzer returns False if no tonality satisfies the progression.
    """
    # GIVEN: a mock of the evaluator that always returns failure
    mock_evaluator_instance = MagicMock()
    mock_evaluator_instance.evaluate_satisfaction_recursive.return_value = (False, Explanation())
    mocker.patch(
        "core.logic.progression_analyzer.SatisfactionEvaluator",
        return_value=mock_evaluator_instance,
    )

    # WHEN: we run the analysis
    analyzer = ProgressionAnalyzer(mock_kripke_config, [c_major_tonality_mock])
    progression = [Chord("C"), Chord("F#")]

    success, _ = analyzer.check_tonal_progression(progression, [c_major_tonality_mock])

    # THEN: the result is failure
    assert success is False


def test_check_progression_handles_empty_sequence(
    mock_kripke_config: MagicMock, c_major_tonality_mock: MagicMock
) -> None:
    """
    Verifies the edge case of an empty chord progression.
    """
    # WHEN: we run the analysis with an empty list
    analyzer = ProgressionAnalyzer(mock_kripke_config, [c_major_tonality_mock])
    success, explanation = analyzer.check_tonal_progression([], [c_major_tonality_mock])

    # THEN: the result is failure and the explanation reflects the error
    assert success is False
    assert "empty" in explanation.steps[0].observation.lower()
