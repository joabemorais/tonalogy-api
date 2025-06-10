from enum import Enum, auto
from typing import Set, Dict, Tuple, List, Optional
from dataclasses import dataclass, field
import copy


@dataclass(frozen=True)
class Chord:
  """
  Represents an individual chord symbol (e.g., "Am", "G").
  'dataclass' automatically generates methods like __init__, __repr__, etc.
  'frozen=True' makes objects of this class immutable. Once created, a
  chord cannot be changed. This is good for data consistency.
  Since it's 'frozen', Python automatically generates __eq__ and __hash__ methods,
  which allows us to use Chord objects in sets and as dictionary keys.
  """

  name: str


class TonalFunction(Enum):
  """
  Represents the abstract functional categories (Tonic, Dominant, Subdominant).
  Using an Enum ensures we can only use these defined values, avoiding errors.
  """

  TONIC = auto()
  DOMINANT = auto()
  SUBDOMINANT = auto()


@dataclass(frozen=True)
class KripkeState:
  """
  Represents a state 's' in the Kripke structure (e.g., s_t, s_d, s_sd).
  Associates a state ID with a tonal function.
  'frozen=True' also generates __eq__ and __hash__ for us, allowing
  KripkeState to be used in sets and as dictionary keys, which is
  essential for representing the accessibility relation.
  """

  state_id: str
  associated_tonal_function: TonalFunction


@dataclass
class Tonality:
  """
  Represents a Tonality, which is a labeling function L_i in the formalism.
  Maps tonal functions to sets of chords that can fulfill them.
  We don't use 'frozen=True' here, as we might want to add or
  modify chord mappings in the future, although it's unlikely.
  """

  tonality_name: str
  function_to_chords_map: Dict[TonalFunction, Set[Chord]]

  def get_chords_for_function(self, func: TonalFunction) -> Set[Chord]:
    """Returns the set of chords for a given tonal function."""
    return self.function_to_chords_map.get(func, set())

  def chord_fulfills_function(
    self, test_chord: Chord, target_function: TonalFunction
  ) -> bool:
    """Checks if a chord fulfills a specific function in this tonality."""
    return test_chord in self.get_chords_for_function(target_function)


@dataclass
class KripkeStructureConfig:
  """
  Defines the static part of the Kripke structure: <S, S0, SF, R>.
  This configuration is the foundation upon which different Tonalities (L_i) operate.
  'field(default_factory=set)' is used to ensure that a new empty set
  is created for each instance if no value is provided, avoiding
  issues with mutable objects as defaults in classes.
  """

  states: Set[KripkeState] = field(default_factory=set)
  initial_states: Set[KripkeState] = field(default_factory=set)
  final_states: Set[KripkeState] = field(default_factory=set)
  # The Accessibility Relation is a set of tuples, where each tuple
  # represents an allowed transition from one state to another.
  accessibility_relation: Set[Tuple[KripkeState, KripkeState]] = field(
    default_factory=set
  )

  def get_state_by_tonal_function(self, func: TonalFunction) -> Optional[KripkeState]:
    """
    Finds and returns the first KripkeState in this configuration
    that is associated with the given TonalFunction.
    Returns None if no such state is found.
    This is used, for example, to find the 'Tonic' state to start an analysis.
    """
    for state in self.states:
      if state.associated_tonal_function == func:
        return state
    return None # No state found for the given function

  def get_successors_of_state(self, source_state: KripkeState) -> List[KripkeState]:
    """
    Returns a list of KripkeStates that are directly accessible
    from the given source_state, according to the accessibility_relation.
    This is crucial for traversing the Kripke structure during analysis.
    """
    successors: List[KripkeState] = [
      r_target for r_source, r_target in self.accessibility_relation
      if r_source == source_state
    ]
    return successors


@dataclass
class DetailedExplanationStep:
  """
  Represents a single detailed step in the analysis explanation.
  Using Optional for some fields as they might not be relevant for all step types
  (e.g., an "Analysis Start" step might not have a specific KripkeState or Chord).
  """
  # Using Optional since some steps (like 'Analysis Start' or 'Overall Failure')
  # might not have all these fields populated.
  evaluated_functional_state: Optional[KripkeState]
  processed_chord: Optional[Chord]
  tonality_used_in_step: Optional[Tonality]
  formal_rule_applied: str  # e.g., "Eq.3 (L)", "Analysis Start", "Base (Empty Seq)"
  observation: str          # Human-readable message for this step

@dataclass
class Explanation:
  """
  Collects a sequence of DetailedExplanationStep objects to trace the
  derivation of a tonal progression analysis.
  """
  steps: List[DetailedExplanationStep] = field(default_factory=list)

  def add_step(
    self,
    formal_rule_applied: str,
    observation: str,
    evaluated_functional_state: Optional[KripkeState] = None,
    processed_chord: Optional[Chord] = None,
    tonality_used_in_step: Optional[Tonality] = None,
  ):
    """
    Adds a new detailed step to the explanation.
    The order of parameters is slightly changed for convenience,
    making rule and observation mandatory.
    """
    step = DetailedExplanationStep(
      evaluated_functional_state=evaluated_functional_state,
      processed_chord=processed_chord,
      tonality_used_in_step=tonality_used_in_step,
      formal_rule_applied=formal_rule_applied,
      observation=observation
    )
    self.steps.append(step)

  def clone(self) -> 'Explanation':
    """
    Creates a deep enough copy of this Explanation object.
    This is crucial for the recursive evaluation, allowing different
    analysis paths to have independent explanation trails.
    The list of steps is deep copied, but the objects within the steps
    (KripkeState, Chord, Tonality) are immutable or treated as such (Tonality might not be frozen),
    so a shallow copy of those is sufficient if they are not modified after creation.
    However, DetailedExplanationStep itself is a dataclass and will be copied.
    Using copy.deepcopy for the list of steps ensures that new DetailedExplanationStep
    objects are created for the clone.
    """
    # `copy.deepcopy` will create new DetailedExplanationStep objects
    # and a new list to hold them.
    # Since Chord and KripkeState are frozen (immutable), and Tonality is typically
    # treated as immutable once configured for an analysis branch,
    # deepcopying the steps list itself is the main concern.
    return Explanation(steps=copy.deepcopy(self.steps))
