import json
from pathlib import Path
import pytest

# Import the classes we are going to test and those needed for assertions
from core.config.knowledge_base import TonalKnowledgeBase
from core.domain.models import (
    KripkeStructureConfig, Tonality, TonalFunction, Chord, KripkeState
)

# --- Fixtures to create temporary configuration files ---

@pytest.fixture
def temp_kripke_config_file(tmp_path: Path) -> Path:
    """
    Creates a temporary kripke_structure.json file for tests.
    """
    kripke_data = {
        "states": [
            {"state_id": "s_t", "associated_tonal_function": "TONIC"},
            {"state_id": "s_d", "associated_tonal_function": "DOMINANT"},
            {"state_id": "s_sd", "associated_tonal_function": "SUBDOMINANT"}
        ],
        "initial_states": ["s_t"],
        "final_states": ["s_t"],
        "accessibility_relation": [
            {"from": "s_t", "to": "s_d"},
            {"from": "s_d", "to": "s_sd"}
        ]
    }
    file_path = tmp_path / "kripke_structure.json"
    file_path.write_text(json.dumps(kripke_data))
    return file_path

@pytest.fixture
def temp_tonalities_config_file(tmp_path: Path) -> Path:
    """
    Creates a temporary tonalities.json file for tests.
    """
    tonalities_data = [
        {
            "tonality_name": "Test Major",
            "function_to_chords_map": {
                "TONIC": ["C", "Am"],
                "DOMINANT": ["G"],
                "SUBDOMINANT": ["F", "Dm"]
            }
        },
        {
            "tonality_name": "Test minor",
            "function_to_chords_map": {
                "TONIC": ["Cm"],
                "DOMINANT": ["G", "Bdim"],
                "SUBDOMINANT": ["Fm"]
            }
        }
    ]
    file_path = tmp_path / "tonalities.json"
    file_path.write_text(json.dumps(tonalities_data))
    return file_path

# --- Tests for TonalKnowledgeBase Class ---

def test_knowledge_base_loads_successfully(temp_kripke_config_file, temp_tonalities_config_file):
    """
    Tests if TonalKnowledgeBase loads and interprets configuration files correctly.
    """
    # GIVEN: Paths to valid configuration files
    kripke_path = temp_kripke_config_file
    tonalities_path = temp_tonalities_config_file
    
    # WHEN: TonalKnowledgeBase is instantiated
    knowledge_base = TonalKnowledgeBase(kripke_path, tonalities_path)
    
    # THEN: Properties should be loaded and have the correct types
    assert isinstance(knowledge_base.kripke_config, KripkeStructureConfig)
    assert isinstance(knowledge_base.all_tonalities, list)
    assert len(knowledge_base.all_tonalities) == 2
    assert all(isinstance(t, Tonality) for t in knowledge_base.all_tonalities)

def test_kripke_config_parsing(temp_kripke_config_file, temp_tonalities_config_file):
    """
    Verifies if Kripke structure data was parsed to the correct domain objects.
    """
    # GIVEN: A loaded TonalKnowledgeBase
    knowledge_base = TonalKnowledgeBase(temp_kripke_config_file, temp_tonalities_config_file)
    k_config = knowledge_base.kripke_config

    # THEN: The internal structure should be correct
    assert len(k_config.states) == 3
    
    # Verify if one of the states was created correctly
    tonic_state = next(s for s in k_config.states if s.state_id == "s_t")
    assert isinstance(tonic_state, KripkeState)
    assert tonic_state.associated_tonal_function == TonalFunction.TONIC
    
    # Verify the accessibility relation
    dominant_state = next(s for s in k_config.states if s.state_id == "s_d")
    subdominant_state = next(s for s in k_config.states if s.state_id == "s_sd")
    expected_relation = (tonic_state, dominant_state)
    assert expected_relation in k_config.accessibility_relation

def test_tonalities_parsing(temp_kripke_config_file, temp_tonalities_config_file):
    """
    Verifies if tonality data was parsed to the correct domain objects.
    """
    # GIVEN: A loaded TonalKnowledgeBase
    knowledge_base = TonalKnowledgeBase(temp_kripke_config_file, temp_tonalities_config_file)
    test_major = next(t for t in knowledge_base.all_tonalities if t.tonality_name == "Test Major")
    
    # THEN: The internal structure of the tonality should be correct
    assert isinstance(test_major, Tonality)
    
    tonic_chords = test_major.function_to_chords_map[TonalFunction.TONIC]
    assert isinstance(tonic_chords, set)
    assert Chord("C") in tonic_chords
    assert Chord("Am") in tonic_chords

def test_load_raises_error_for_missing_kripke_file(tmp_path: Path, temp_tonalities_config_file):
    """
    Tests if an error is raised when the Kripke configuration file doesn't exist.
    """
    # GIVEN: An invalid path to the Kripke file
    invalid_path = tmp_path / "non_existent.json"
    
    # THEN: Should raise an IOError
    with pytest.raises(IOError, match="Error reading or parsing Kripke config file"):
        # WHEN: TonalKnowledgeBase is instantiated with the invalid path
        TonalKnowledgeBase(invalid_path, temp_tonalities_config_file)

def test_load_raises_error_for_missing_tonalities_file(tmp_path: Path, temp_kripke_config_file):
    """
    Tests if an error is raised when the tonalities configuration file doesn't exist.
    """
    # GIVEN: An invalid path to the tonalities file
    invalid_path = tmp_path / "non_existent.json"
    
    # THEN: Should raise an IOError
    with pytest.raises(IOError, match="Error reading or parsing tonalities config file"):
        # WHEN: TonalKnowledgeBase is instantiated with the invalid path
        TonalKnowledgeBase(temp_kripke_config_file, invalid_path)

def test_load_raises_error_for_malformed_json(tmp_path: Path):
    """
    Tests if an error is raised when a configuration file is malformed.
    """
    # GIVEN: A JSON file with invalid syntax
    malformed_file = tmp_path / "malformed.json"
    malformed_file.write_text('{"key": "value",}') # extra comma
    
    # THEN: Should raise an IOError that mentions JSONDecodeError
    with pytest.raises(IOError, match="JSONDecodeError"):
        # WHEN: TonalKnowledgeBase tries to read the malformed file
        TonalKnowledgeBase(malformed_file, malformed_file)

