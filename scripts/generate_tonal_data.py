"""
Tonality Data Generator for Tonalogy API

This module generates comprehensive tonal data for all 24 major and minor tonalities,
including their harmonic fields and chord-function mappings. The generated data is
used by the Tonalogy API for music theory analysis and chord progression suggestions.

Classes:
    TonalityGenerator: Abstract base class for generating tonality data
    MajorTonality: Generates harmonic field data for major tonalities
    MinorTonality: Generates harmonic field data for minor tonalities using 
                   natural, harmonic, and melodic minor scales

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
from typing import Dict, List, Set, Any
from pathlib import Path # Import the Path class for path manipulation
import logging

class TonalityGenerator:
    """
    Abstract base class for generating tonality data.
    """
    NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    def __init__(self, root_note: str):
        if root_note not in self.NOTE_NAMES:
            raise ValueError(f"Invalid tonality: {root_note}")
        self.root_note = root_note
        self.tonality_name: str = ""
        # Dictionary to store different scales (natural, harmonic, etc.)
        self.scales: Dict[str, List[str]] = {}
        self.harmonic_field: Dict[str, Set[str]] = {}

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
        serializable_map = {
            func_name: sorted(list(chords))
            for func_name, chords in self.harmonic_field.items()
        }
        return {
            "tonality_name": self.tonality_name,
            "function_to_chords_map": serializable_map
        }

class MajorTonality(TonalityGenerator):
    """Generates the harmonic field and functions for a major tonality."""
    MAJOR_SCALE_STEPS = [2, 2, 1, 2, 2, 2, 1]
    
    DEGREE_LABELS = ["I", "ii", "iii", "IV", "V", "vi", "viidim"]

    DEGREE_INFO = {
        "I":      {"quality": "",    "function": "TONIC"},
        "ii":     {"quality": "m",   "function": "SUBDOMINANT"},
        "iii":    {"quality": "m",   "function": "TONIC"},
        "IV":     {"quality": "",    "function": "SUBDOMINANT"},
        "V":      {"quality": "",    "function": "DOMINANT"},
        "vi":     {"quality": "m",   "function": "TONIC"},
        "viidim": {"quality": "dim", "function": "DOMINANT"}
    }
    
    def __init__(self, root_note: str):
        super().__init__(root_note)
        self.tonality_name = f"{self.root_note} Major"
        self.scales['natural'] = self._build_scale(self.MAJOR_SCALE_STEPS) # The major scale is the "natural" scale for this mode
        self.harmonic_field = self._build_harmonic_field()

    def _build_harmonic_field(self) -> Dict[str, Set[str]]:
        field: Dict[str, Set[str]] = {"TONIC": set(), "SUBDOMINANT": set(), "DOMINANT": set()}
        
        for i, degree_label in enumerate(self.DEGREE_LABELS):
            note = self.scales['natural'][i]
            info = self.DEGREE_INFO[degree_label]
            quality = info["quality"]
            function_name = info["function"]
            
            chord_name = f"{note}{quality}"
            field[function_name].add(chord_name)
            
        return field

class MinorTonality(TonalityGenerator):
    """
    Generates the harmonic field and functions for a minor tonality, using
    chords from the natural, harmonic, and melodic scales.
    """
    NATURAL_MINOR_STEPS = [2, 1, 2, 2, 1, 2, 2]
    
    # Complete mapping of common degrees and their origins
    DEGREE_INFO = {
        # Degree: (Quality, Function, Scale Source, Index in Source Scale)
        "i":      {"quality": "m",   "function": "TONIC",       "source": "natural",  "index": 0},
        "iidim":  {"quality": "dim", "function": "SUBDOMINANT", "source": "natural",  "index": 1},
        "ii":     {"quality": "m",   "function": "SUBDOMINANT", "source": "melodic",  "index": 1},
        "bIII":   {"quality": "",    "function": "TONIC",       "source": "natural",  "index": 2},
        "bIII+":  {"quality": "aug", "function": "TONIC",       "source": "melodic",  "index": 2}, # New: augmented 3rd degree from melodic
        "iv":     {"quality": "m",   "function": "SUBDOMINANT", "source": "natural",  "index": 3},
        "IV":     {"quality": "",    "function": "SUBDOMINANT", "source": "melodic",  "index": 3},
        "v":      {"quality": "m",   "function": "DOMINANT",    "source": "natural",  "index": 4},
        "V":      {"quality": "",    "function": "DOMINANT",    "source": "harmonic", "index": 4},
        "bVI":    {"quality": "",    "function": "TONIC",       "source": "natural",  "index": 5},
        "vidim":  {"quality": "dim", "function": "SUBDOMINANT", "source": "melodic",  "index": 5}, # New: diminished 6th degree from melodic
        "bVII":   {"quality": "",    "function": "DOMINANT",    "source": "natural",  "index": 6},
        "viidim": {"quality": "dim", "function": "DOMINANT",    "source": "harmonic", "index": 6},
    }
    DEGREE_LABELS = list(DEGREE_INFO.keys())

    def __init__(self, root_note: str):
        super().__init__(root_note)
        self.tonality_name = f"{self.root_note} minor"
        
        # 1. Build the natural minor scale as base
        self.scales['natural'] = self._build_scale(self.NATURAL_MINOR_STEPS)
        
        # 2. Build the harmonic minor scale (raised 7th) from the natural
        harmonic_scale = self.scales['natural'][:]
        h_7th_idx = (self.NOTE_NAMES.index(harmonic_scale[6]) + 1) % len(self.NOTE_NAMES)
        harmonic_scale[6] = self.NOTE_NAMES[h_7th_idx]
        self.scales['harmonic'] = harmonic_scale

        # 3. Build the melodic minor scale (raised 6th and 7th) from the natural
        melodic_scale = self.scales['natural'][:]
        m_6th_idx = (self.NOTE_NAMES.index(melodic_scale[5]) + 1) % len(self.NOTE_NAMES)
        m_7th_idx = (self.NOTE_NAMES.index(melodic_scale[6]) + 1) % len(self.NOTE_NAMES)
        melodic_scale[5] = self.NOTE_NAMES[m_6th_idx]
        melodic_scale[6] = self.NOTE_NAMES[m_7th_idx]
        self.scales['melodic'] = melodic_scale
        
        self.harmonic_field = self._build_harmonic_field()

    def _build_harmonic_field(self) -> Dict[str, Set[str]]:
        field: Dict[str, Set[str]] = {"TONIC": set(), "SUBDOMINANT": set(), "DOMINANT": set()}

        for degree_label, info in self.DEGREE_INFO.items():
            # Select the correct scale (natural, harmonic or melodic)
            source_scale = self.scales[info["source"]]
            # Get the root note of the chord from the correct degree in that scale
            note = source_scale[info["index"]]
            
            quality = info["quality"]
            function_name = info["function"]
            
            chord_name = f"{note}{quality}"
            field[function_name].add(chord_name)
        
        return field

def generate_tonal_data_json(filepath: str):
    """
    Generates the tonalities.json file with all 24 major and minor tonalities.
    """
    # Convert the file path from string to a Path object for more robust handling.
    output_path_obj = Path(filepath)

    # Ensure the parent directory exists before trying to write the file.
    # parents=True creates any necessary parent directories.
    # exist_ok=True doesn't raise an error if the directory already exists.
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
            
    # Use the Path object to open the file.
    with output_path_obj.open('w', encoding='utf-8') as f:
        json.dump(all_tonalities, f, indent=2, ensure_ascii=False)
        
    logging.info(f"File '{filepath}' generated successfully with {len(all_tonalities)} tonalities.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    output_path = "core/config/data/tonalities.json"
    generate_tonal_data_json(output_path)

    logging.info("\nExample for C Major (Triads):")
    c_major = MajorTonality("C")
    logging.info(json.dumps(c_major.to_dict(), indent=2))
    
    logging.info("\nExample for A minor (with chords from all scales):")
    a_minor = MinorTonality("A")
    logging.info(json.dumps(a_minor.to_dict(), indent=2))
