import json
from pathlib import Path
from typing import List, Dict, Set, Tuple

# Import domain models that will serve as "templates" for the loaded data
from core.domain.models import (
  Chord, TonalFunction, KripkeState, Tonality, KripkeStructureConfig
)

class TonalKnowledgeBase:
  """
  Loads, validates and provides access to the Kripke structure configuration
  and tonality definitions from external files (JSON).
  
  This class acts as a Single Source of Truth for the rules of our tonal universe.
  """
  def __init__(self, kripke_config_path: Path, tonalities_config_path: Path):
    """
    Initializes the knowledge base by loading data from the specified files.

    Args:
      kripke_config_path: The path to the Kripke structure JSON file.
      tonalities_config_path: The path to the tonalities JSON file.
    """
    self._kripke_config = self._load_kripke_config(kripke_config_path)
    self._all_tonalities = self._load_tonalities(tonalities_config_path)

  @property
  def kripke_config(self) -> KripkeStructureConfig:
    """Property to access the loaded Kripke structure configuration."""
    return self._kripke_config

  @property
  def all_tonalities(self) -> List[Tonality]:
      """Property to access the list of all loaded tonalities."""
      return self._all_tonalities

  def _load_kripke_config(self, file_path: Path) -> KripkeStructureConfig:
    """
    Loads the Kripke structure from a JSON file and transforms it
    into a KripkeStructureConfig object.
    """
    try:
      with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
      raise IOError(f"Error reading or parsing Kripke config file at {file_path}: {e}")

    # Map state ID strings to KripkeState objects for easy reference
    states_map: Dict[str, KripkeState] = {
      s_data['state_id']: KripkeState(
        state_id=s_data['state_id'],
        associated_tonal_function=TonalFunction[s_data['associated_tonal_function']]
      )
      for s_data in data['states']
    }
    
    # Build the accessibility relation using the KripkeState objects
    relation: Set[Tuple[KripkeState, KripkeState]] = {
      (states_map[r['from']], states_map[r['to']])
      for r in data['accessibility_relation']
    }

    # Build the final configuration object
    return KripkeStructureConfig(
      states=set(states_map.values()),
      initial_states={states_map[s_id] for s_id in data['initial_states']},
      final_states={states_map[s_id] for s_id in data['final_states']},
      accessibility_relation=relation
    )

  def _load_tonalities(self, file_path: Path) -> List[Tonality]:
    """
    Loads tonality definitions from a JSON file and transforms them
    into a list of Tonality objects.
    """
    try:
      with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
      raise IOError(f"Error reading or parsing tonalities config file at {file_path}: {e}")

    loaded_tonalities = []
    for t_data in data:
      function_map: Dict[TonalFunction, Set[Chord]] = {
        TonalFunction[func_name]: {Chord(chord_name) for chord_name in chords}
        for func_name, chords in t_data['function_to_chords_map'].items()
      }
      loaded_tonalities.append(
        Tonality(
          tonality_name=t_data['tonality_name'],
          function_to_chords_map=function_map
        )
      )
    return loaded_tonalities
