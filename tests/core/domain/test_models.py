import pytest
from enum import Enum, auto
from typing import Dict
import copy

from core.domain.models import (
    KripkeState,
    TonalFunction,
    KripkeStructureConfig,
    Chord,
    Tonality,
    Explanation,
    DetailedExplanationStep,
)

# --- Test Fixtures ---


# Kripke-related fixtures
@pytest.fixture
def sample_states() -> Dict:
    """Provides a dictionary of sample KripkeState objects for tests."""
    return {
        "s_t": KripkeState(state_id="s_t", associated_tonal_function=TonalFunction.TONIC),
        "s_d": KripkeState(state_id="s_d", associated_tonal_function=TonalFunction.DOMINANT),
        "s_sd": KripkeState(state_id="s_sd", associated_tonal_function=TonalFunction.SUBDOMINANT),
    }


@pytest.fixture
def kripke_config_empty() -> KripkeStructureConfig:
    """Provides an empty KripkeStructureConfig."""
    return KripkeStructureConfig(states=set(), accessibility_relation=set())


@pytest.fixture
def kripke_config_populated(sample_states: Dict) -> KripkeStructureConfig:
    """Provides a KripkeStructureConfig populated with sample states and relations."""
    s_t = sample_states["s_t"]
    s_d = sample_states["s_d"]
    s_sd = sample_states["s_sd"]

    states = {s_t, s_d, s_sd}
    # The relations here are inverted compared to the usual order to match the
    # directionality of the analysis in the context of tonal functions.
    relations = {
        (s_t, s_sd),  # Tonic -> Subdominant
        (s_t, s_d),  # Tonic -> Dominant
        (s_d, s_sd),  # Dominant -> Subdominant
    }
    return KripkeStructureConfig(states=states, accessibility_relation=relations)


# Tonality-related fixtures
@pytest.fixture
def c_major_tonality() -> Tonality:
    """Provides a sample C Major Tonality object."""
    return Tonality(
        tonality_name="C Major",
        function_to_chords_map={
            TonalFunction.TONIC: {Chord("C"), Chord("Am")},
            TonalFunction.DOMINANT: {Chord("G"), Chord("G7"), Chord("Bdim")},
            TonalFunction.SUBDOMINANT: {Chord("F"), Chord("Dm")},
        },
    )


@pytest.fixture
def g_major_tonality_partial() -> Tonality:
    """Provides a sample G Major Tonality with only Tonic and Dominant defined."""
    return Tonality(
        tonality_name="G Major Partial",
        function_to_chords_map={
            TonalFunction.TONIC: {Chord("G"), Chord("Em")},
            TonalFunction.DOMINANT: {Chord("D"), Chord("D7")},
        },
    )


# Explanation-related fixtures
@pytest.fixture
def sample_detailed_step(
    sample_states: Dict, c_major_tonality: Tonality
) -> DetailedExplanationStep:
    """A sample DetailedExplanationStep with all fields populated."""
    return DetailedExplanationStep(
        evaluated_functional_state=sample_states["s_t"],
        processed_chord=Chord("C"),
        tonality_used_in_step=c_major_tonality,
        formal_rule_applied="Eq.3 (P in L)",
        observation="Chord C fulfills Tonic in C Major.",
    )


@pytest.fixture
def sample_detailed_step_minimal() -> DetailedExplanationStep:
    """A sample DetailedExplanationStep with only mandatory fields."""
    return DetailedExplanationStep(
        formal_rule_applied="Analysis Start",
        observation="Beginning analysis for C Major.",
        evaluated_functional_state=None,
        processed_chord=None,
        tonality_used_in_step=None,
    )


@pytest.fixture
def empty_explanation() -> Explanation:
    """An empty Explanation object."""
    return Explanation()


@pytest.fixture
def explanation_with_one_step(sample_detailed_step: DetailedExplanationStep) -> Explanation:
    """An Explanation object with one sample step."""
    return Explanation(steps=[sample_detailed_step])


@pytest.fixture
def explanation_with_multiple_steps(
    sample_detailed_step: DetailedExplanationStep,
    sample_detailed_step_minimal: DetailedExplanationStep,
    sample_states: Dict,
    c_major_tonality: Tonality,
) -> Explanation:
    """An Explanation object with multiple diverse steps."""
    exp = Explanation()
    exp.add_step(  # Using add_step to ensure it's tested implicitly
        formal_rule_applied=sample_detailed_step_minimal.formal_rule_applied,
        observation=sample_detailed_step_minimal.observation,
        # Other fields will be None by default in add_step
    )
    exp.add_step(
        evaluated_functional_state=sample_detailed_step.evaluated_functional_state,
        processed_chord=sample_detailed_step.processed_chord,
        tonality_used_in_step=sample_detailed_step.tonality_used_in_step,
        formal_rule_applied=sample_detailed_step.formal_rule_applied,
        observation=sample_detailed_step.observation,
    )
    exp.add_step(
        evaluated_functional_state=sample_states["s_d"],
        processed_chord=Chord("G7"),
        tonality_used_in_step=c_major_tonality,
        formal_rule_applied="Eq.4/5 (P in L, φ in L)",
        observation="Chord G7 fulfills Dominant in C Major. Trying next state...",
    )
    return exp


# --- Tests for get_state_by_tonal_function ---


def test_get_state_by_tonal_function_found(
    kripke_config_populated: KripkeStructureConfig, sample_states: Dict
):
    """Test finding a state by a TonalFunction that exists."""
    tonic_state = kripke_config_populated.get_state_by_tonal_function(TonalFunction.TONIC)
    assert tonic_state is not None, "Should find a tonic state"
    assert tonic_state == sample_states["s_t"], "Should find the correct tonic state"

    dominant_state = kripke_config_populated.get_state_by_tonal_function(TonalFunction.DOMINANT)
    assert dominant_state == sample_states["s_d"], "Should find the correct dominant state"

    subdominant_state = kripke_config_populated.get_state_by_tonal_function(
        TonalFunction.SUBDOMINANT
    )
    assert subdominant_state == sample_states["s_sd"], "Should find the correct subdominant state"


def test_get_state_by_tonal_function_not_found(kripke_config_populated: KripkeStructureConfig):
    """Test finding a state by a TonalFunction that does not exist in any state."""

    # Define a TonalFunction value that is guaranteed not to be in use
    class MockNonExistentFunction(Enum):
        UNKNOWN_FUNCTION = auto()

    unknown_function_state = kripke_config_populated.get_state_by_tonal_function(
        MockNonExistentFunction.UNKNOWN_FUNCTION
    )
    assert unknown_function_state is None, "Should return None for a non-existent tonal function"


def test_get_state_by_tonal_function_empty_config(kripke_config_empty: KripkeStructureConfig):
    """Test on an empty KripkeStructureConfig."""
    tonic_state = kripke_config_empty.get_state_by_tonal_function(TonalFunction.TONIC)
    assert tonic_state is None, "Should return None when config has no states"


# --- Tests for get_successors_of_state ---


def test_get_successors_of_st(kripke_config_populated: KripkeStructureConfig, sample_states: Dict):
    """Test successors for s_sd (Subdominant), which has multiple distinct successors."""
    successors_of_st = kripke_config_populated.get_successors_of_state(sample_states["s_t"])
    expected_successors = {sample_states["s_d"], sample_states["s_sd"]}
    assert set(successors_of_st) == expected_successors, "Successors of s_t are incorrect"


def test_get_successors_of_sd_single_successor(
    kripke_config_populated: KripkeStructureConfig, sample_states: Dict
):
    """Test s_d (Dominant), which has exactly one successor."""
    successors_of_sd = kripke_config_populated.get_successors_of_state(sample_states["s_d"])
    expected_successors = {sample_states["s_sd"]}
    assert set(successors_of_sd) == expected_successors, "Successor of s_d should be s_sd"


def test_get_successors_of_ssd_no_successors(
    kripke_config_populated: KripkeStructureConfig, sample_states: Dict
):
    """Test s_sd (Subdominant), which has no successors."""
    successors_of_ssd = kripke_config_populated.get_successors_of_state(sample_states["s_sd"])
    assert not successors_of_ssd, "Subdominant state should have no successors"


def test_get_successors_unknown_state(kripke_config_populated: KripkeStructureConfig):
    """Test querying successors for a state object that isn't part of the config's states set at all."""
    unknown_state = KripkeState(state_id="s_unknown", associated_tonal_function=TonalFunction.TONIC)
    successors = kripke_config_populated.get_successors_of_state(unknown_state)
    assert successors == [], "An unknown state should have no successors from the defined relations"


def test_get_successors_empty_relations_config(sample_states: Dict):
    """Test when the accessibility_relation is empty, but states exist."""
    config_no_relations = KripkeStructureConfig(
        states=set(sample_states.values()), accessibility_relation=set()
    )
    successors = config_no_relations.get_successors_of_state(sample_states["s_t"])
    assert successors == [], "Should be no successors if R is empty"


def test_get_successors_empty_config_overall(kripke_config_empty: KripkeStructureConfig):
    """Test get_successors_of_state on a completely empty KripkeStructureConfig."""
    dummy_state = KripkeState(state_id="s_dummy", associated_tonal_function=TonalFunction.TONIC)
    successors = kripke_config_empty.get_successors_of_state(dummy_state)
    assert successors == [], "Should be no successors in an entirely empty config"


# --- Tests for Tonality Helper Methods ---


def test_tonality_get_chords_for_function_exists(c_major_tonality: Tonality):
    """Test getting chords for a function that exists in the tonality map."""
    tonic_chords = c_major_tonality.get_chords_for_function(TonalFunction.TONIC)
    expected_tonic_chords = {Chord("C"), Chord("Am")}
    assert tonic_chords == expected_tonic_chords, "Incorrect tonic chords for C Major"

    dominant_chords = c_major_tonality.get_chords_for_function(TonalFunction.DOMINANT)
    expected_dominant_chords = {Chord("G"), Chord("G7"), Chord("Bdim")}
    assert dominant_chords == expected_dominant_chords, "Incorrect dominant chords for C Major"


def test_tonality_get_chords_for_function_not_exists(g_major_tonality_partial: Tonality):
    """Test getting chords for a function that is not defined in the tonality map."""
    # g_major_tonality_partial does not have SUBDOMINANT defined
    subdominant_chords = g_major_tonality_partial.get_chords_for_function(TonalFunction.SUBDOMINANT)
    assert subdominant_chords == set(), "Should return an empty set for an undefined function"


def test_tonality_chord_fulfills_function_true(c_major_tonality: Tonality):
    """Test when a chord correctly fulfills a function."""
    assert (
        c_major_tonality.chord_fulfills_function(Chord("C"), TonalFunction.TONIC) is True
    ), "C should be Tonic in C Major"
    assert (
        c_major_tonality.chord_fulfills_function(Chord("G7"), TonalFunction.DOMINANT) is True
    ), "G7 should be Dominant in C Major"
    assert (
        c_major_tonality.chord_fulfills_function(Chord("Dm"), TonalFunction.SUBDOMINANT) is True
    ), "Dm should be Subdominant in C Major"


def test_tonality_chord_fulfills_function_false_wrong_chord(c_major_tonality: Tonality):
    """Test when a chord does not fulfill the specified function (wrong chord for function)."""
    assert (
        c_major_tonality.chord_fulfills_function(Chord("G"), TonalFunction.TONIC) is False
    ), "G should not be Tonic in C Major"
    assert (
        c_major_tonality.chord_fulfills_function(Chord("C"), TonalFunction.DOMINANT) is False
    ), "C should not be Dominant in C Major"


def test_tonality_chord_fulfills_function_false_function_not_in_tonality(
    g_major_tonality_partial: Tonality,
):
    """Test when the function itself is not defined for the tonality."""
    # SUBDOMINANT is not in g_major_tonality_partial
    assert (
        g_major_tonality_partial.chord_fulfills_function(Chord("C"), TonalFunction.SUBDOMINANT)
        is False
    ), "C cannot be Subdominant if Subdominant is not defined for the tonality"


def test_tonality_chord_fulfills_function_empty_chord_set_for_function():
    """Test a scenario where a function might exist but have an empty set of chords (edge case)."""
    empty_tonic_tonality = Tonality(
        tonality_name="Test Tonality", function_to_chords_map={TonalFunction.TONIC: set()}
    )
    assert (
        empty_tonic_tonality.chord_fulfills_function(Chord("C"), TonalFunction.TONIC) is False
    ), "C cannot be Tonic if Tonic set is empty"


# --- Tests for Explanation and DetailedExplanationStep ---


def test_detailed_explanation_step_creation_with_fixture(
    sample_detailed_step: DetailedExplanationStep, sample_states: Dict, c_major_tonality: Tonality
):
    """Test basic creation of a DetailedExplanationStep using a fixture."""
    step = sample_detailed_step
    assert step.evaluated_functional_state == sample_states["s_t"]
    assert step.processed_chord == Chord("C")
    assert step.tonality_used_in_step == c_major_tonality
    assert step.formal_rule_applied == "Eq.3 (P in L)"
    assert step.observation == "Chord C fulfills Tonic in C Major."


def test_detailed_explanation_step_minimal_creation(
    sample_detailed_step_minimal: DetailedExplanationStep,
):
    """Test creation of a minimal DetailedExplanationStep."""
    step = sample_detailed_step_minimal
    assert step.evaluated_functional_state is None
    assert step.processed_chord is None
    assert step.tonality_used_in_step is None
    assert step.formal_rule_applied == "Analysis Start"
    assert step.observation == "Beginning analysis for C Major."


def test_explanation_creation_empty_with_fixture(empty_explanation: Explanation):
    """Test creating an empty Explanation using a fixture."""
    exp = empty_explanation
    assert exp.steps == [], "New Explanation should start with an empty steps list"


def test_explanation_add_step_with_fixtures(
    empty_explanation: Explanation, sample_states: Dict, c_major_tonality: Tonality
):
    """Test the add_step method of the Explanation class using fixtures."""
    exp = empty_explanation
    s_t = sample_states["s_t"]
    c_chord = Chord("C")

    exp.add_step(
        evaluated_functional_state=s_t,
        processed_chord=c_chord,
        tonality_used_in_step=c_major_tonality,
        formal_rule_applied="Test Rule",
        observation="Test observation.",
    )
    assert len(exp.steps) == 1
    step1 = exp.steps[0]
    assert step1.evaluated_functional_state == s_t
    assert step1.processed_chord == c_chord
    assert step1.tonality_used_in_step == c_major_tonality
    assert step1.formal_rule_applied == "Test Rule"
    assert step1.observation == "Test observation."

    exp.add_step(
        formal_rule_applied="Another Rule",
        observation="Another observation, no specific state/chord/tonality.",
    )
    assert len(exp.steps) == 2
    step2 = exp.steps[1]
    assert step2.evaluated_functional_state is None
    assert step2.processed_chord is None
    assert step2.tonality_used_in_step is None


def test_explanation_clone_empty_with_fixture(empty_explanation: Explanation):
    """Test cloning an empty Explanation using a fixture."""
    exp_orig = empty_explanation
    exp_cloned = exp_orig.clone()

    assert exp_cloned is not exp_orig
    assert exp_cloned.steps == [], "Cloned empty Explanation should also have an empty steps list"
    assert exp_cloned.steps is not exp_orig.steps


def test_explanation_clone_with_one_step(
    explanation_with_one_step: Explanation, sample_detailed_step: DetailedExplanationStep
):
    """Test cloning an Explanation with one step."""
    exp_orig = explanation_with_one_step
    exp_cloned = exp_orig.clone()

    assert exp_cloned is not exp_orig
    assert exp_cloned.steps is not exp_orig.steps
    assert len(exp_cloned.steps) == 1
    assert exp_cloned.steps[0] == sample_detailed_step

    # Add a step to original, clone should not change
    exp_orig.add_step(formal_rule_applied="New Original Step", observation="Original changed")
    assert len(exp_orig.steps) == 2
    assert len(exp_cloned.steps) == 1


def test_explanation_clone_with_multiple_steps(explanation_with_multiple_steps: Explanation):
    """Test cloning an Explanation with multiple steps, ensuring deep enough copy."""
    exp_orig = explanation_with_multiple_steps
    original_steps_copy = copy.deepcopy(exp_orig.steps)

    exp_cloned = exp_orig.clone()

    assert exp_cloned is not exp_orig
    assert exp_cloned.steps is not exp_orig.steps
    assert len(exp_cloned.steps) == len(original_steps_copy)
    for i in range(len(original_steps_copy)):
        assert exp_cloned.steps[i] == original_steps_copy[i]
        assert exp_cloned.steps[i] is not original_steps_copy[i]

    # Modify the original's steps list
    exp_orig.add_step(
        processed_chord=Chord("G"),
        formal_rule_applied="Rule Added to Original",
        observation="Original Only",
    )
    assert len(exp_orig.steps) == len(original_steps_copy) + 1
    assert len(exp_cloned.steps) == len(
        original_steps_copy
    ), "Clone should not be affected by adding to original's steps list"

    # Modify the clone's steps list
    exp_cloned.add_step(
        processed_chord=Chord("F"),
        formal_rule_applied="Rule Added to Clone",
        observation="Clone Only",
    )
    assert len(exp_cloned.steps) == len(original_steps_copy) + 1
    assert len(exp_orig.steps) == len(original_steps_copy) + 1
    assert exp_orig.steps[-1].observation == "Original Only"
    assert exp_cloned.steps[-1].observation == "Clone Only"
