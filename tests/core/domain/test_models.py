import pytest
from enum import Enum, auto
from typing import Dict

from core.domain.models import (
    KripkeState,
    TonalFunction,
    KripkeStructureConfig,
)

# --- Test Fixtures ---

@pytest.fixture
def sample_states() -> Dict:
    """Provides a dictionary of sample KripkeState objects for tests."""
    return {
        "s_t": KripkeState(state_id="s_t", associated_tonal_function=TonalFunction.TONIC),
        "s_d": KripkeState(state_id="s_d", associated_tonal_function=TonalFunction.DOMINANT),
        "s_sd": KripkeState(state_id="s_sd", associated_tonal_function=TonalFunction.SUBDOMINANT),
        "s_t2": KripkeState(state_id="s_t2", associated_tonal_function=TonalFunction.TONIC), # Another tonic state
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
    s_t2 = sample_states["s_t2"]

    states = {s_t, s_d, s_sd, s_t2}
    relations = {
        (s_sd, s_d),  # Subdominant -> Dominant
        (s_d, s_t),   # Dominant -> Tonic
        (s_sd, s_t),  # Subdominant -> Tonic (alternative)
        (s_t, s_sd),  # Tonic (s_t) -> Subdominant
        (s_t, s_d),   # Tonic (s_t) -> Dominant
        # s_t2 has no outgoing relations defined here
    }
    return KripkeStructureConfig(states=states, accessibility_relation=relations)

# --- Tests for get_state_by_tonal_function ---

def test_get_state_by_tonal_function_found(kripke_config_populated: KripkeStructureConfig, sample_states: Dict):
    """Test finding a state by a TonalFunction that exists."""
    tonic_state = kripke_config_populated.get_state_by_tonal_function(TonalFunction.TONIC)
    assert tonic_state is not None, "Should find a tonic state"
    # Since iteration order over sets is not guaranteed, check if it's one of the expected ones.
    assert tonic_state in [sample_states["s_t"], sample_states["s_t2"]], "Returned tonic state is not one of the expected ones"

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

def test_get_state_by_tonal_function_multiple_matches_returns_one(kripke_config_populated: KripkeStructureConfig, sample_states: Dict):
    """
    Test that if multiple states have the same tonal function, one of them is returned.
    The current implementation returns the first one it encounters during iteration.
    """
    tonic_state = kripke_config_populated.get_state_by_tonal_function(TonalFunction.TONIC)
    assert tonic_state is not None, "A tonic state should be found"
    assert tonic_state.associated_tonal_function == TonalFunction.TONIC, "Returned state must have TONIC function"
    assert tonic_state == sample_states["s_t"] or tonic_state == sample_states["s_t2"], "Returned state must be one of the known tonic states"

# --- Tests for get_successors_of_state ---

def test_get_successors_of_sd(kripke_config_populated: KripkeStructureConfig, sample_states: Dict):
    """Test successors for s_sd (Subdominant), which has multiple distinct successors."""
    successors_of_ssd = kripke_config_populated.get_successors_of_state(sample_states["s_sd"])
    expected_successors = {sample_states["s_d"], sample_states["s_t"]}
    assert set(successors_of_ssd) == expected_successors, "Successors of s_sd are incorrect"

def test_get_successors_of_sd_single_successor(kripke_config_populated: KripkeStructureConfig, sample_states: Dict):
    """Test s_d (Dominant), which has exactly one successor."""
    successors_of_sd = kripke_config_populated.get_successors_of_state(sample_states["s_d"])
    expected_successors = {sample_states["s_t"]}
    assert set(successors_of_sd) == expected_successors, "Successor of s_d should be s_t"

def test_get_successors_of_st_multiple_successors(kripke_config_populated: KripkeStructureConfig, sample_states: Dict):
    """Test s_t (Tonic), which has multiple successors."""
    successors_of_st = kripke_config_populated.get_successors_of_state(sample_states["s_t"])
    expected_successors = {sample_states["s_sd"], sample_states["s_d"]}
    assert set(successors_of_st) == expected_successors, "Successors of s_t are incorrect"

def test_get_successors_of_st2_no_successors(kripke_config_populated: KripkeStructureConfig, sample_states: Dict):
    """Test s_t2 (another Tonic), which has no defined successors in R."""
    successors_of_st2 = kripke_config_populated.get_successors_of_state(sample_states["s_t2"])
    assert successors_of_st2 == [], "s_t2 should have no successors"

def test_get_successors_state_not_in_config_relations(kripke_config_populated: KripkeStructureConfig):
    """Test querying successors for a state object that isn't a source in any relation in R."""
    state_like_st2 = KripkeState(state_id="s_t2", associated_tonal_function=TonalFunction.TONIC)
    successors = kripke_config_populated.get_successors_of_state(state_like_st2)
    assert successors == [], "A state not acting as a source in R should have no successors"

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