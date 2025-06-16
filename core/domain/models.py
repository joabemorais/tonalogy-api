from enum import Enum, auto
from typing import Set, Dict, Tuple, List, Optional
from dataclasses import dataclass, field
import copy


@dataclass(frozen=True)
class Chord:
    """Represents an individual chord symbol. Immutable and hashable."""
    name: str


class TonalFunction(Enum):
    """Represents the abstract functional categories."""
    TONIC = auto()
    DOMINANT = auto()
    SUBDOMINANT = auto()


@dataclass(frozen=True)
class KripkeState:
    """Represents a state in the Kripke structure. Immutable and hashable."""
    state_id: str
    associated_tonal_function: TonalFunction


@dataclass
class Tonality:
    """
    Represents a Tonality (a labeling function L_i).
    Maps tonal functions to chords and their scale origins.
    """
    tonality_name: str
    function_to_chords_map: Dict[TonalFunction, Dict[Chord, str]]

    def get_chords_for_function(self, func: TonalFunction) -> Set[Chord]:
        """Returns the set of chords for a given tonal function."""
        return set(self.function_to_chords_map.get(func, {}).keys())

    def chord_fulfills_function(self, test_chord: Chord, target_function: TonalFunction) -> bool:
        """Checks if a chord fulfills a specific function in this tonality."""
        return test_chord in self.function_to_chords_map.get(target_function, {})

    def get_chord_origin_for_function(self, test_chord: Chord, target_function: TonalFunction) -> Optional[str]:
        """Gets the scale origin (e.g., 'melodic') for a chord fulfilling a function."""
        return self.function_to_chords_map.get(target_function, {}).get(test_chord)


@dataclass
class KripkeStructureConfig:
    """Defines the static part of the Kripke structure: <S, S0, SF, R>."""
    states: Set[KripkeState] = field(default_factory=set)
    initial_states: Set[KripkeState] = field(default_factory=set)
    final_states: Set[KripkeState] = field(default_factory=set)
    accessibility_relation: Set[Tuple[KripkeState, KripkeState]] = field(default_factory=set)

    def get_state_by_tonal_function(self, func: TonalFunction) -> Optional[KripkeState]:
        """Finds the KripkeState associated with a given TonalFunction."""
        for state in self.states:
            if state.associated_tonal_function == func:
                return state
        return None

    def get_successors_of_state(self, source_state: KripkeState) -> List[KripkeState]:
        """Returns a list of KripkeStates accessible from a source state."""
        return [
            r_target for r_source, r_target in self.accessibility_relation
            if r_source == source_state
        ]


@dataclass
class DetailedExplanationStep:
    """Represents a single detailed step in the analysis explanation."""
    evaluated_functional_state: Optional[KripkeState]
    processed_chord: Optional[Chord]
    tonality_used_in_step: Optional[Tonality]
    formal_rule_applied: str
    observation: str


@dataclass
class Explanation:
    """Collects a sequence of DetailedExplanationStep objects."""
    steps: List[DetailedExplanationStep] = field(default_factory=list)

    def add_step(
        self,
        formal_rule_applied: str,
        observation: str,
        evaluated_functional_state: Optional[KripkeState] = None,
        processed_chord: Optional[Chord] = None,
        tonality_used_in_step: Optional[Tonality] = None,
    ):
        """Adds a new detailed step to the explanation."""
        step = DetailedExplanationStep(
            evaluated_functional_state,
            processed_chord,
            tonality_used_in_step,
            formal_rule_applied,
            observation
        )
        self.steps.append(step)

    def clone(self) -> 'Explanation':
        """Creates a deep copy of the Explanation object."""
        return Explanation(steps=copy.deepcopy(self.steps))
