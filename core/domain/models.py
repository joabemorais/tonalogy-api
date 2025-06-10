from enum import Enum, auto
from typing import Set, Dict, Tuple
from dataclasses import dataclass, field


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
    essential for representing the accessibility relation R.
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
    # The Accessibility Relation R is a set of tuples, where each tuple
    # represents an allowed transition from one state to another.
    accessibility_relation_R: Set[Tuple[KripkeState, KripkeState]] = field(
        default_factory=set
    )
