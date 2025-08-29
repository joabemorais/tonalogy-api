import copy
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTE_MAP = {name: i for i, name in enumerate(NOTE_NAMES)}

# Enharmonic equivalents mapping: flat to sharp
ENHARMONIC_MAP = {
    "Db": "C#",
    "Eb": "D#",
    "Gb": "F#",
    "Ab": "G#",
    "Bb": "A#",
    # Less common but valid enharmonic equivalents
    "Cb": "B",
    "Fb": "E",
    "E#": "F",
    "B#": "C"
}


def normalize_note_name(note_name: str) -> str:
    """
    Normalizes a note name by converting flat notation to sharp notation.
    
    Args:
        note_name: The note name (e.g., "Bb", "A#", "C")
    
    Returns:
        The normalized note name using sharp notation
    """
    return ENHARMONIC_MAP.get(note_name, note_name)


@dataclass(frozen=True)
class Chord:
    """Represents an individual chord symbol. Immutable and hashable."""

    name: str
    _notes_cache: Optional[Set[str]] = field(default=None, init=False, compare=False)

    @property
    def quality(self) -> str:
        """Determines the chord's quality (Major, minor, diminished) from its name."""
        if "dim" in self.name:
            return "diminished"
        elif "m" in self.name:
            return "minor"
        else:
            return "Major"

    @property
    def notes(self) -> Set[str]:
        if self._notes_cache is None:
            object.__setattr__(self, "_notes_cache", self._parse_notes())
        return self._notes_cache  # type: ignore[return-value]

    def _parse_notes(self) -> Set[str]:
        """
        Parses the chord name to return the set of notes it contains.
        This implementation supports major, minor, and diminished triads.
        It also supports both sharp (#) and flat (b) notation, converting flats to their enharmonic sharp equivalents.
        """
        # Updated regex to match both sharp (#) and flat (b) notations
        match = re.match(r"([A-G][#b]?)", self.name)
        if not match:
            return set()

        root_note_name = match.group(1)
        # Normalize the note name (convert flats to sharps)
        normalized_root = normalize_note_name(root_note_name)
        root_note_index = NOTE_MAP.get(normalized_root)

        if root_note_index is None:
            return set()

        if self.name.endswith("dim"):
            # Diminished: T + 3st + 6st
            intervals = [0, 3, 6]
        elif self.name.endswith("m"):
            # Minor: T + 3st + 7st
            intervals = [0, 3, 7]
        else:
            # Major: T + 4st + 7st
            intervals = [0, 4, 7]

        chord_notes = set()
        for interval in intervals:
            note_index = (root_note_index + interval) % 12
            chord_notes.add(NOTE_NAMES[note_index])

        return chord_notes


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
    primary_scale_notes: Set[str] = field(default_factory=set)

    @property
    def quality(self) -> str:
        """Determines the tonality's quality from its name."""
        if "minor" in self.tonality_name:
            return "minor"
        return "Major"

    def get_chords_for_function(self, func: TonalFunction) -> Set[Chord]:
        """Returns the set of chords for a given tonal function."""
        return set(self.function_to_chords_map.get(func, {}).keys())

    def chord_fulfills_function(self, test_chord: Chord, target_function: TonalFunction) -> bool:
        """
        Checks if a chord fulfills a specific function in this tonality.
        This method supports enharmonic equivalence by comparing chord notes.
        """
        function_chords = self.function_to_chords_map.get(target_function, {})
        
        # First try direct comparison (for exact matches)
        if test_chord in function_chords:
            return True
        
        # If no direct match, check for enharmonic equivalence by comparing notes
        test_chord_notes = test_chord.notes
        for chord in function_chords.keys():
            if chord.notes == test_chord_notes:
                return True
        
        return False

    def get_chord_origin_for_function(
        self, test_chord: Chord, target_function: TonalFunction
    ) -> Optional[str]:
        """Gets the scale origin (e.g., 'harmonic') for a chord fulfilling a function."""
        return self.function_to_chords_map.get(target_function, {}).get(test_chord)

    def get_scale_notes(self) -> Set[str]:
        """Returns the set of primary scale notes for this tonality."""
        return self.primary_scale_notes


@dataclass
class KripkeStructureConfig:
    """Defines the static part of the Kripke structure: <S, S0, SF, R>."""

    states: Set[KripkeState] = field(default_factory=set)
    initial_states: Set[KripkeState] = field(default_factory=set)
    final_states: Set[KripkeState] = field(default_factory=set)
    accessibility_relation: List[Tuple[KripkeState, KripkeState]] = field(default_factory=list)

    def get_state_by_tonal_function(self, func: TonalFunction) -> Optional[KripkeState]:
        """Finds the KripkeState associated with a given TonalFunction."""
        for state in self.states:
            if state.associated_tonal_function == func:
                return state
        return None

    def get_successors_of_state(self, source_state: KripkeState) -> List[KripkeState]:
        """Returns a list of KripkeStates accessible from a source state."""
        return [
            r_target
            for r_source, r_target in self.accessibility_relation
            if r_source == source_state
        ]


@dataclass
class KripkePath:
    """
    Represents a path π through the Kripke structure.
    As noted in Aragão's work, paths are inverted due to the accessibility relations.

    This class tracks the sequence of states and tonalities traversed during
    the analysis of a chord progression, providing a formal representation
    of the analytical path taken.
    """

    states: List[KripkeState] = field(default_factory=list)
    tonalities: List[Tonality] = field(default_factory=list)
    explanations: List[str] = field(default_factory=list)

    def add_step(self, state: KripkeState, tonality: Tonality, explanation: str) -> None:
        """Add a step to the path."""
        self.states.append(state)
        self.tonalities.append(tonality)
        self.explanations.append(explanation)

    def clone(self) -> "KripkePath":
        """Create a deep copy of the path."""
        return KripkePath(
            states=self.states.copy(),
            tonalities=self.tonalities.copy(),
            explanations=self.explanations.copy(),
        )

    def get_current_state(self) -> Optional[KripkeState]:
        """Get the current (last) state in the path."""
        if not self.states:
            return None
        return self.states[-1]

    def get_current_tonality(self) -> Optional[Tonality]:
        """Get the current (last) tonality in the path."""
        return self.tonalities[-1] if self.tonalities else None

    def to_readable_format(self) -> str:
        """Convert path to readable format for debugging/logging."""
        if not self.states:
            return "Empty path"

        path_str = "Path: "
        for i, (state, tonality) in enumerate(zip(self.states, self.tonalities)):
            path_str += f"[{state.associated_tonal_function.name} in {tonality.tonality_name}]"
            if i < len(self.states) - 1:
                path_str += " → "
        return path_str

    def get_length(self) -> int:
        """Returns the length of the path (number of states)."""
        return len(self.states)

    def is_empty(self) -> bool:
        """Checks if the path is empty."""
        return len(self.states) == 0


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
    ) -> None:
        """Adds a new detailed step to the explanation."""
        step = DetailedExplanationStep(
            evaluated_functional_state,
            processed_chord,
            tonality_used_in_step,
            formal_rule_applied,
            observation,
        )
        self.steps.append(step)

    def clone(self) -> "Explanation":
        """Creates a deep copy of the Explanation object."""
        return Explanation(steps=copy.deepcopy(self.steps))
