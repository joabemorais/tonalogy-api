# tonalogy-api/tests/core/logic/test_kripke_evaluator.py

import pytest
from typing import List, Optional

# Import the classes we will test and use as dependencies
from core.domain.models import (
    Chord, TonalFunction, KripkeState, Tonality,
    KripkeStructureConfig, Explanation, DetailedExplanationStep
)
from core.logic.kripke_evaluator import SatisfactionEvaluator

# --- Fixtures to create a consistent test environment ---
# These fixtures provide reusable objects for our tests.

@pytest.fixture
def tonic_state() -> KripkeState:
    return KripkeState(state_id="s_t", associated_tonal_function=TonalFunction.TONIC)

@pytest.fixture
def dominant_state() -> KripkeState:
    return KripkeState(state_id="s_d", associated_tonal_function=TonalFunction.DOMINANT)

@pytest.fixture
def subdominant_state() -> KripkeState:
    return KripkeState(state_id="s_sd", associated_tonal_function=TonalFunction.SUBDOMINANT)

@pytest.fixture
def c_major_tonality() -> Tonality:
    return Tonality(
        tonality_name="C Major",
        function_to_chords_map={
            TonalFunction.TONIC: {Chord("C"), Chord("Am"), Chord("Em")},
            TonalFunction.DOMINANT: {Chord("G"), Chord("G7"), Chord("Bdim")},
            TonalFunction.SUBDOMINANT: {Chord("F"), Chord("Dm")}
        }
    )

@pytest.fixture
def d_minor_tonality() -> Tonality:
    return Tonality(
        tonality_name="D minor",
        function_to_chords_map={
            TonalFunction.TONIC: {Chord("Dm"), Chord("F")},
            TonalFunction.DOMINANT: {Chord("A"), Chord("A7")},
            TonalFunction.SUBDOMINANT: {Chord("Gm"), Chord("Bb")}
        }
    )

@pytest.fixture
def aragao_kripke_config(
    tonic_state: KripkeState,
    dominant_state: KripkeState,
    subdominant_state: KripkeState
    ) -> KripkeStructureConfig:
    """
    Creates the Kripke structure configuration with INVERTED accessibility relations,
    according to the direct suggestion from author Aragão.
    """
    return KripkeStructureConfig(
        states={tonic_state, dominant_state, subdominant_state},
        initial_states={tonic_state},
        final_states={dominant_state, subdominant_state},
        accessibility_relation={
            (tonic_state, dominant_state),
            (tonic_state, subdominant_state),
            (dominant_state, subdominant_state)
        }
    )

# --- Tests for the SatisfactionEvaluator Class ---

def test_base_case_empty_sequence(
    aragao_kripke_config: KripkeStructureConfig, 
    c_major_tonality: Tonality, 
    tonic_state: KripkeState
) -> None:
    """
    Tests the simplest base case: an empty chord sequence should be satisfied.
    """
    # GIVEN: an evaluator and an empty progression
    evaluator = SatisfactionEvaluator(aragao_kripke_config, [c_major_tonality], c_major_tonality)
    empty_progression: List[Chord] = []
    
    # WHEN: the evaluation is executed
    success, _ = evaluator.evaluate_satisfaction_recursive(
        current_tonality=c_major_tonality,
        current_state=tonic_state,
        remaining_chords=empty_progression,
        recursion_depth=0,
        parent_explanation=Explanation()
    )
    
    # THEN: the result should be success
    assert success is True

def test_single_valid_chord_in_tonic(
    aragao_kripke_config: KripkeStructureConfig, 
    c_major_tonality: Tonality, 
    tonic_state: KripkeState
) -> None:
    """
    Tests Aragão's Eq. 3: a progression with a single chord that is valid in the tonic.
    """
    # GIVEN: an evaluator and a progression with a valid chord
    evaluator = SatisfactionEvaluator(aragao_kripke_config, [c_major_tonality], c_major_tonality)
    progression: List[Chord] = [Chord("C")]
    
    # WHEN: the evaluation is executed
    success, explanation = evaluator.evaluate_satisfaction_recursive(
        current_tonality=c_major_tonality,
        current_state=tonic_state,
        remaining_chords=progression,
        recursion_depth=0,
        parent_explanation=Explanation()
    )
    
    # THEN: the result should be success
    assert success is True
    assert "P in L" in explanation.steps[-1].formal_rule_applied
    assert "End of sequence" in explanation.steps[-1].observation

def test_direct_continuation_success_V_I(
    aragao_kripke_config: KripkeStructureConfig, 
    c_major_tonality: Tonality, 
    tonic_state: KripkeState
) -> None:
    """
    Tests ATTEMPT 1 (Eq. 4A): a V-I cadence (inverted to C G).
    This should follow the path s_t -> s_d.
    """
    # GIVEN: an evaluator and the inverted progression [C, G]
    evaluator = SatisfactionEvaluator(aragao_kripke_config, [c_major_tonality], c_major_tonality)
    progression: List[Chord] = [Chord("C"), Chord("G")]
    
    # WHEN: the evaluation is executed
    success, explanation = evaluator.evaluate_satisfaction_recursive(
        current_tonality=c_major_tonality,
        current_state=tonic_state,
        remaining_chords=progression,
        recursion_depth=0,
        parent_explanation=Explanation()
    )
    
    # THEN: the result should be success
    assert success is True
    # The explanation trace should show P='C' in L='Lc' and then P='G' in L='Lc'
    assert explanation.steps[0].processed_chord == Chord("C")
    assert explanation.steps[1].processed_chord == Chord("G")
    assert "P in L" in explanation.steps[1].formal_rule_applied

def test_direct_continuation_failure_no_path(
    aragao_kripke_config: KripkeStructureConfig, 
    c_major_tonality: Tonality, 
    tonic_state: KripkeState
) -> None:
    """
    Tests a progression that is harmonically plausible (G Dm) but for which
    there is no path in our Accessibility Relation R (there's no s_d -> s_sd inverted, but s_d->s_sd yes).
    In our current R: s_d -> s_sd. The progression G Dm (inverted) is Dm G.
    Dm is s_sd. G is s_d. Starting at s_t -> Dm(s_sd). s_sd has no successor, so it fails.
    """
    # GIVEN: an evaluator and the inverted progression [Dm, G]
    evaluator = SatisfactionEvaluator(aragao_kripke_config, [c_major_tonality], c_major_tonality)
    progression: List[Chord] = [Chord("Dm"), Chord("G")]
    
    # WHEN: the evaluation is executed at the tonic
    success, _ = evaluator.evaluate_satisfaction_recursive(
        current_tonality=c_major_tonality,
        current_state=tonic_state,
        remaining_chords=progression,
        recursion_depth=0,
        parent_explanation=Explanation()
    )
    
    # THEN: the result should be failure, since direct continuation doesn't work and pivot/re-anchoring
    # won't find a simple solution.
    assert success is False

def test_tonicization_pivot_success_complex_progression(
    aragao_kripke_config: KripkeStructureConfig,
    c_major_tonality: Tonality,
    d_minor_tonality: Tonality,
    tonic_state: KripkeState
) -> None:
    """
    Tests the user's complex progression: C G Dm A7 Em.
    This should validate ATTEMPT 2 (Tonicization/Pivot).
    """
    # GIVEN: an evaluator with multiple tonalities and the complete progression
    all_tonalities: List[Tonality] = [c_major_tonality, d_minor_tonality]
    # Analysis starts in C Major
    evaluator = SatisfactionEvaluator(aragao_kripke_config, all_tonalities, c_major_tonality)

    # The original progression is Em A7 Dm G C. The inverted is C G Dm A7 Em.
    progression: List[Chord] = [Chord("C"), Chord("G"), Chord("Dm"), Chord("A7"), Chord("Em")]
    
    # WHEN: the evaluation is executed
    success, explanation = evaluator.evaluate_satisfaction_recursive(
        current_tonality=c_major_tonality,
        current_state=tonic_state,
        remaining_chords=progression,
        recursion_depth=0,
        parent_explanation=Explanation()
    )

    # THEN: the result should be success
    assert success is True

    # Let's check some key points in the explanation to confirm the logic
    # We expect to see a tonicization to Dm.
    pivot_step: Optional[DetailedExplanationStep] = next((step for step in explanation.steps if "Tonicization Pivot" in step.formal_rule_applied), None)
    assert pivot_step is not None
    assert pivot_step.processed_chord == Chord("Dm")
    assert "becomes the new TONIC in 'D minor'" in pivot_step.observation
    
    # The following chord (A7) should be processed in D minor.
    a7_step: Optional[DetailedExplanationStep] = next((step for step in explanation.steps if step.processed_chord == Chord("A7")), None)
    assert a7_step is not None
    assert a7_step.tonality_used_in_step.tonality_name == "D minor"

    # The final chord (Em) should be re-anchored back to C Major.
    em_step: Optional[DetailedExplanationStep] = next((step for step in explanation.steps if step.processed_chord == Chord("Em")), None)
    assert em_step is not None
    assert em_step.tonality_used_in_step.tonality_name == "C Major"
    assert "Re-anchor" in explanation.steps[explanation.steps.index(em_step) - 1].formal_rule_applied
