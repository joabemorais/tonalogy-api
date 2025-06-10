import pytest
from enum import Enum, auto
from typing import Dict

from core.domain.models import (
    KripkeState,
    TonalFunction,
    KripkeStructureConfig,
    Chord,
    Tonality,
)

# --- Test Fixtures ---

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
        (s_t, s_d),   # Tonic -> Dominant
        (s_d, s_sd),  # Dominant -> Subdominant
    }
    return KripkeStructureConfig(states=states, accessibility_relation=relations)

@pytest.fixture
def c_major_key() -> Tonality:
    """Provides a sample C Major Key object."""
    return Tonality(
        tonality_name="C Major",
        function_to_chords_map={
            TonalFunction.TONIC: {Chord("C"), Chord("Am")},
            TonalFunction.DOMINANT: {Chord("G"), Chord("G7"), Chord("Bdim")},
            TonalFunction.SUBDOMINANT: {Chord("F"), Chord("Dm")}
        }
    )

@pytest.fixture
def g_major_key_partial() -> Tonality:
    """Provides a sample G Major Key with only Tonic and Dominant defined."""
    return Tonality(
        tonality_name="G Major Partial",
        function_to_chords_map={
            TonalFunction.TONIC: {Chord("G"), Chord("Em")},
            TonalFunction.DOMINANT: {Chord("D"), Chord("D7")}
        }
    )

# --- Tests for get_state_by_tonal_function ---

def test_get_state_by_tonal_function_found(kripke_config_populated: KripkeStructureConfig, sample_states: Dict):
    """Test finding a state by a TonalFunction that exists."""
    tonic_state = kripke_config_populated.get_state_by_tonal_function(TonalFunction.TONIC)
    assert tonic_state is not None, "Should find a tonic state"
    assert tonic_state == sample_states["s_t"], "Should find the correct tonic state"

    dominant_state = kripke_config_populated.get_state_by_tonal_function(TonalFunction.DOMINANT)
    assert dominant_state == sample_states["s_d"], "Should find the correct dominant state"

    subdominant_state = kripke_config_populated.get_state_by_tonal_function(TonalFunction.SUBDOMINANT)
    assert subdominant_state == sample_states["s_sd"], "Should find the correct subdominant state"

def test_get_state_by_tonal_function_not_found(kripke_config_populated: KripkeStructureConfig):
    """Test finding a state by a TonalFunction that does not exist in any state."""
    # Define a TonalFunction value that is guaranteed not to be in use
    class MockNonExistentFunction(Enum):
        UNKNOWN_FUNCTION = auto()
    
    unknown_function_state = kripke_config_populated.get_state_by_tonal_function(MockNonExistentFunction.UNKNOWN_FUNCTION)
    assert unknown_function_state is None, "Should return None for a non-existent tonal function"

def test_get_state_by_tonal_function_empty_config(kripke_config_empty: KripkeStructureConfig):
    """Test on an empty KripkeStructureConfig."""
    tonic_state = kripke_config_empty.get_state_by_tonal_function(TonalFunction.TONIC)
    assert tonic_state is None, "Should return None when config has no states"

# --- Tests for get_successors_of_state ---

def test_get_successors_of_t(kripke_config_populated: KripkeStructureConfig, sample_states: Dict):
    """Test successors for s_sd (Subdominant), which has multiple distinct successors."""
    successors_of_st = kripke_config_populated.get_successors_of_state(sample_states["s_t"])
    expected_successors = {sample_states["s_d"], sample_states["s_sd"]}
    assert set(successors_of_st) == expected_successors, "Successors of s_t are incorrect"

def test_get_successors_of_sd_single_successor(kripke_config_populated: KripkeStructureConfig, sample_states: Dict):
    """Test s_d (Dominant), which has exactly one successor."""
    successors_of_sd = kripke_config_populated.get_successors_of_state(sample_states["s_d"])
    expected_successors = {sample_states["s_sd"]}
    assert set(successors_of_sd) == expected_successors, "Successor of s_d should be s_sd"

def test_get_successors_of_ssd_no_successors(kripke_config_populated: KripkeStructureConfig, sample_states: Dict):
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
    config_no_relations = KripkeStructureConfig(states=set(sample_states.values()), accessibility_relation=set())
    successors = config_no_relations.get_successors_of_state(sample_states["s_t"])
    assert successors == [], "Should be no successors if R is empty"

def test_get_successors_empty_config_overall(kripke_config_empty: KripkeStructureConfig):
    """Test get_successors_of_state on a completely empty KripkeStructureConfig."""
    dummy_state = KripkeState(state_id="s_dummy", associated_tonal_function=TonalFunction.TONIC)
    successors = kripke_config_empty.get_successors_of_state(dummy_state)
    assert successors == [], "Should be no successors in an entirely empty config"

# --- Tests for Tonality Helper Methods ---

def test_key_get_chords_for_function_exists(c_major_key: Tonality):
    """Test getting chords for a function that exists in the key map."""
    tonic_chords = c_major_key.get_chords_for_function(TonalFunction.TONIC)
    expected_tonic_chords = {Chord("C"), Chord("Am")}
    assert tonic_chords == expected_tonic_chords, "Incorrect tonic chords for C Major"

    dominant_chords = c_major_key.get_chords_for_function(TonalFunction.DOMINANT)
    expected_dominant_chords = {Chord("G"), Chord("G7"), Chord("Bdim")}
    assert dominant_chords == expected_dominant_chords, "Incorrect dominant chords for C Major"

def test_key_get_chords_for_function_not_exists(g_major_key_partial: Tonality):
    """Test getting chords for a function that is not defined in the key map."""
    # g_major_key_partial does not have SUBDOMINANT defined
    subdominant_chords = g_major_key_partial.get_chords_for_function(TonalFunction.SUBDOMINANT)
    assert subdominant_chords == set(), "Should return an empty set for an undefined function"

def test_key_chord_fulfills_function_true(c_major_key: Tonality):
    """Test when a chord correctly fulfills a function."""
    assert c_major_key.chord_fulfills_function(Chord("C"), TonalFunction.TONIC) is True, "C should be Tonic in C Major"
    assert c_major_key.chord_fulfills_function(Chord("G7"), TonalFunction.DOMINANT) is True, "G7 should be Dominant in C Major"
    assert c_major_key.chord_fulfills_function(Chord("Dm"), TonalFunction.SUBDOMINANT) is True, "Dm should be Subdominant in C Major"

def test_key_chord_fulfills_function_false_wrong_chord(c_major_key: Tonality):
    """Test when a chord does not fulfill the specified function (wrong chord for function)."""
    assert c_major_key.chord_fulfills_function(Chord("G"), TonalFunction.TONIC) is False, "G should not be Tonic in C Major"
    assert c_major_key.chord_fulfills_function(Chord("C"), TonalFunction.DOMINANT) is False, "C should not be Dominant in C Major"

def test_key_chord_fulfills_function_false_function_not_in_key(g_major_key_partial: Tonality):
    """Test when the function itself is not defined for the key."""
    # SUBDOMINANT is not in g_major_key_partial
    assert g_major_key_partial.chord_fulfills_function(Chord("C"), TonalFunction.SUBDOMINANT) is False, "C cannot be Subdominant if Subdominant is not defined for the key"

def test_key_chord_fulfills_function_empty_chord_set_for_function():
    """Test a scenario where a function might exist but have an empty set of chords (edge case)."""
    empty_tonic_key = Tonality(
        tonality_name="Test Tonality",
        function_to_chords_map={TonalFunction.TONIC: set()}
    )
    assert empty_tonic_key.chord_fulfills_function(Chord("C"), TonalFunction.TONIC) is False, "C cannot be Tonic if Tonic set is empty"
