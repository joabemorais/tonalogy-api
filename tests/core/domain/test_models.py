# tonalogy-api/tests/core/domain/test_models.py

import pytest
from enum import Enum, auto
from typing import Dict

from core.domain.models import KripkeState, TonalFunction, KripkeStructureConfig

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
    return KripkeStructureConfig(states=set(), accessibility_relation_R=set())

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
    return KripkeStructureConfig(states=states, accessibility_relation_R=relations)
