"""
Tonality Data Generator for Tonalogy API

This module generates comprehensive tonal data for all 24 major and minor tonalities,
including their harmonic fields and chord-function mappings. The generated data is
used by the Tonalogy API for music theory analysis and chord progression suggestions.

Classes:
    TonalityGenerator: Abstract base class for generating tonality data
    MajorTonality: Generates harmonic field data for major tonalities
    MinorTonality: Generates harmonic field data for minor tonalities using 
                   natural and harmonic minor scales

Usage:
    Run this script from the tonalogy-api directory:
    $ python scripts/generate_tonal_data.py
    
    This will generate a tonalities.json file containing all tonality data.

Example:
    from scripts.generate_tonal_data import MajorTonality, MinorTonality
    
    # Generate C Major tonality data
    c_major = MajorTonality("C")
    print(c_major.to_dict())
    
    # Generate A minor tonality data
    a_minor = MinorTonality("A")
    print(a_minor.to_dict())
"""

import json
from typing import Dict, List, Any
from pathlib import Path
import logging
from core.domain.models import NOTE_NAMES


class TonalityGenerator:
    """
    Abstract base class for generating tonality data.
    """

    NOTE_NAMES = NOTE_NAMES

    def __init__(self, root_note: str):
        if root_note not in self.NOTE_NAMES:
            raise ValueError(f"Invalid tonality: {root_note}")
        self.root_note = root_note
        self.tonality_name: str = ""
        self.scales: Dict[str, List[str]] = {}
        # The harmonic field now maps a function to a dictionary of chord names and their origins
        self.harmonic_field: Dict[str, Dict[str, str]] = {}

    def _build_scale(self, steps: List[int]) -> List[str]:
        """Builds a scale based on the provided steps."""
        start_index = self.NOTE_NAMES.index(self.root_note)
        scale = [self.NOTE_NAMES[start_index]]
        current_index = start_index
        for step in steps[:-1]:
            current_index = (current_index + step) % len(self.NOTE_NAMES)
            scale.append(self.NOTE_NAMES[current_index])
        return scale

    def to_dict(self) -> Dict[str, Any]:
        """Converts the tonality data to a JSON-serializable dictionary."""
        return {
            "tonality_name": self.tonality_name,
            "function_to_chords_map": self.harmonic_field,
            "primary_scale_notes": list(self.scales.get("natural", [])),
        }


class MajorTonality(TonalityGenerator):
    """Generates the harmonic field and functions for a major tonality."""

    MAJOR_SCALE_STEPS = [2, 2, 1, 2, 2, 2, 1]

    DEGREE_LABELS = ["I", "ii", "iii", "IV", "V", "vi", "viidim"]

    DEGREE_INFO = {
        "I": {"quality": "", "function": "TONIC"},
        "ii": {"quality": "m", "function": "SUBDOMINANT"},
        "iii": {"quality": "m", "function": "TONIC"},
        "IV": {"quality": "", "function": "SUBDOMINANT"},
        "V": {"quality": "", "function": "DOMINANT"},
        "vi": {"quality": "m", "function": "TONIC"},
        "viidim": {"quality": "dim", "function": "DOMINANT"},
    }

    def __init__(self, root_note: str):
        super().__init__(root_note)
        self.tonality_name = f"{self.root_note} Major"
        self.scales["natural"] = self._build_scale(self.MAJOR_SCALE_STEPS)
        self.harmonic_field = self._build_harmonic_field()

    def _build_harmonic_field(self) -> Dict[str, Dict[str, str]]:
        """Builds the harmonic field, mapping chords to their 'natural' origin."""
        field: Dict[str, Dict[str, str]] = {"TONIC": {}, "SUBDOMINANT": {}, "DOMINANT": {}}

        for i, degree_label in enumerate(self.DEGREE_LABELS):
            note = self.scales["natural"][i]
            info = self.DEGREE_INFO[degree_label]
            quality = info["quality"]
            function_name = info["function"]

            chord_name = f"{note}{quality}"
            field[function_name][chord_name] = "natural"

        return field


class MinorTonality(TonalityGenerator):
    """
    Generates the harmonic field for a minor tonality, tracking the origin
    of each chord (natural, harmonic).
    """

    NATURAL_MINOR_STEPS = [2, 1, 2, 2, 1, 2, 2]

    DEGREE_INFO = {
        "i": {"quality": "m", "function": "TONIC", "source": "natural", "index": 0},
        "iidim": {"quality": "dim", "function": "SUBDOMINANT", "source": "natural", "index": 1},
        "bIII": {"quality": "", "function": "TONIC", "source": "natural", "index": 2},
        "iv": {"quality": "m", "function": "SUBDOMINANT", "source": "natural", "index": 3},
        "v": {"quality": "m", "function": "DOMINANT", "source": "natural", "index": 4},
        "V": {"quality": "", "function": "DOMINANT", "source": "harmonic", "index": 4},
        "bVI": {"quality": "", "function": "TONIC", "source": "natural", "index": 5},
        "bVII": {"quality": "", "function": "DOMINANT", "source": "natural", "index": 6},
        "viidim": {"quality": "dim", "function": "DOMINANT", "source": "harmonic", "index": 6},
    }

    def __init__(self, root_note: str):
        super().__init__(root_note)
        self.tonality_name = f"{self.root_note} minor"

        self.scales["natural"] = self._build_scale(self.NATURAL_MINOR_STEPS)

        harmonic_scale = self.scales["natural"][:]
        h_7th_idx = (self.NOTE_NAMES.index(harmonic_scale[6]) + 1) % len(self.NOTE_NAMES)
        harmonic_scale[6] = self.NOTE_NAMES[h_7th_idx]
        self.scales["harmonic"] = harmonic_scale

        self.harmonic_field = self._build_harmonic_field()

    def _build_harmonic_field(self) -> Dict[str, Dict[str, str]]:
        """Builds the harmonic field, mapping chords to their specific scale origin."""
        field: Dict[str, Dict[str, str]] = {"TONIC": {}, "SUBDOMINANT": {}, "DOMINANT": {}}

        for _, info in self.DEGREE_INFO.items():
            source_scale_name = info["source"]
            source_scale = self.scales[source_scale_name]
            note = source_scale[info["index"]]

            quality = info["quality"]
            function_name = info["function"]

            chord_name = f"{note}{quality}"
            field[function_name][chord_name] = source_scale_name

        return field


def generate_tonal_data_json(filepath: str):
    """Generates the tonalities.json file with all 24 major and minor tonalities."""
    output_path_obj = Path(filepath)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    all_tonalities = []
    root_notes = TonalityGenerator.NOTE_NAMES

    for note in root_notes:
        try:
            major_tonality = MajorTonality(note)
            all_tonalities.append(major_tonality.to_dict())

            minor_tonality = MinorTonality(note)
            all_tonalities.append(minor_tonality.to_dict())
        except ValueError as e:
            logging.error(f"Error generating tonality for {note}: {e}")

    with output_path_obj.open("w", encoding="utf-8") as f:
        json.dump(all_tonalities, f, indent=2, ensure_ascii=False)

    logging.info(f"File '{filepath}' generated successfully with {len(all_tonalities)} tonalities.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    # Assumes the script is run from the project root
    output_path = "core/config/data/tonalities.json"
    generate_tonal_data_json(output_path)

    logging.info(f"\nExample for D minor (with chords from all scales):")
    d_minor = MinorTonality("D")
    logging.info(json.dumps(d_minor.to_dict(), indent=2))
