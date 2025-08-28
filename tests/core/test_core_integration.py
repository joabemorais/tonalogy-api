import pytest
from typing import List

# Import all real classes from our core
from core.domain.models import (
    Chord, TonalFunction, KripkeState, Tonality, KripkeStructureConfig
)
from core.logic.progression_analyzer import ProgressionAnalyzer

# --- Fixtures with Real Data ---
# These fixtures create the real configuration and tonality objects that
# our analyzer will use.

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
def aragao_kripke_config(tonic_state, dominant_state, subdominant_state) -> KripkeStructureConfig:
    """
    Creates the Kripke structure configuration with INVERTED accessibility relations,
    according to the direct suggestion from author Aragão.
    """
    return KripkeStructureConfig(
        states={tonic_state, dominant_state, subdominant_state},
        # In real analysis, the initial state is always the Tonic.
        initial_states={tonic_state},
        final_states={dominant_state, subdominant_state},
        accessibility_relation={
            (tonic_state, dominant_state),      # s_t -> s_d
            (tonic_state, subdominant_state),   # s_t -> s_sd
            (dominant_state, subdominant_state) # s_d -> s_sd
        }
    )

# --- Main Integration Test ---

def test_full_analysis_of_complex_progression(
    aragao_kripke_config, c_major_tonality, d_minor_tonality
):
    """
    This is a complete integration test for the core. It validates the analysis of
    the progression "C G Dm A7 Em" (already inverted), which requires all three strategies
    from our SatisfactionEvaluator.
    """
    # GIVEN: A real ProgressionAnalyzer with known configuration and tonalities.
    all_tonalities = [c_major_tonality, d_minor_tonality]
    analyzer = ProgressionAnalyzer(aragao_kripke_config, all_tonalities)

    # The original progression is Em A Dm G C.
    # In "check_tonal_progression", we analyze it in reverse order.
    progression_to_analyze: List[Chord] = [
        Chord("Em"),
        Chord("A"),
        Chord("Dm"),
        Chord("G"),
        Chord("C"),
    ]
    
    # The analysis should start by testing C Major tonality.
    tonalities_to_test = [c_major_tonality]

    # WHEN: The analysis is executed
    success, explanation = analyzer.check_tonal_progression(progression_to_analyze, tonalities_to_test)

    # THEN: The result should be success
    assert success is True, "The progression should be identified as tonal."

    # AND: The generated explanation should reflect the logic we expect
    
    # 1. Verify initial direct continuation in C Major
    # The step for 'C' should be in C Major as Tonic
    step_c = next(s for s in explanation.steps if s.processed_chord == Chord("C"))
    assert step_c.tonality_used_in_step.tonality_name == "C Major"
    assert step_c.evaluated_functional_state.associated_tonal_function == TonalFunction.TONIC

    # The step for 'G' should be in C Major as Dominant
    step_g = next(s for s in explanation.steps if s.processed_chord == Chord("G"))
    assert step_g.tonality_used_in_step.tonality_name == "C Major"
    assert step_g.evaluated_functional_state.associated_tonal_function == TonalFunction.DOMINANT
    assert (
        "Tonicization Pivot" not in step_g.formal_rule_applied
    ), "The G chord should not trigger a pivot since it is a direct continuation in C Major."

    # 2. Verify Tonicization Pivot with 'Dm'
    # There should be a "Pivot Modulation (Eq.5)" step for the Dm chord
    pivot_step = next(s for s in explanation.steps if "Pivot" in s.formal_rule_applied and "Eq.5" in s.formal_rule_applied)
    assert pivot_step.processed_chord == Chord("Dm")
    assert "becomes the new TONIC in 'D minor'" in pivot_step.observation

    # 3. Verify continuation in D minor for 'A'
    # The step for 'A' should occur in D minor tonality
    step_a = next(s for s in explanation.steps if s.processed_chord == Chord("A"))
    assert step_a.tonality_used_in_step.tonality_name == "D minor"
    assert step_a.evaluated_functional_state.associated_tonal_function == TonalFunction.DOMINANT

    # 4. Verify Re-anchoring back to C Major for 'Em'
    # There should be a "Attempt Eq.4B" step before the 'Em' step
    reanchor_steps = [s for s in explanation.steps if "Eq.4B" in s.formal_rule_applied]
    assert len(reanchor_steps) > 0, "Should have at least one re-anchor step"
    
    step_em = next(s for s in explanation.steps if s.processed_chord == Chord("Em"))
    assert step_em.processed_chord == Chord("Em")
    assert step_em.tonality_used_in_step.tonality_name == "C Major"
    assert step_em.evaluated_functional_state.associated_tonal_function == TonalFunction.TONIC
