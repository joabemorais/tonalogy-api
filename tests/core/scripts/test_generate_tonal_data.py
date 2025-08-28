import json
from pathlib import Path
import pytest

# Import the classes and functions we want to test from the script
from scripts.generate_tonal_data import MajorTonality, MinorTonality, generate_tonal_data_json

# --- Tests for MajorTonality Class ---


def test_major_tonality_scale_generation():
    """
    Verifies if the major scale is generated correctly.
    """
    # GIVEN: A C Major tonality
    tonality = MajorTonality("C")

    # THEN: The scale should correspond to the C Major scale
    expected_scale = ["C", "D", "E", "F", "G", "A", "B"]
    assert tonality.scales["natural"] == expected_scale
    assert tonality.tonality_name == "C Major"


def test_major_tonality_harmonic_field():
    """
    Verifies if the major harmonic field assigns chords to the correct functions.
    """
    # GIVEN: A C Major tonality
    tonality = MajorTonality("C")
    harmonic_field = tonality.harmonic_field

    # THEN: The main chords should be in their correct functions
    assert "C" in harmonic_field["TONIC"]
    assert "Am" in harmonic_field["TONIC"]
    assert "G" in harmonic_field["DOMINANT"]
    assert "Dm" in harmonic_field["SUBDOMINANT"]
    assert "Bdim" in harmonic_field["DOMINANT"]


# --- Tests for MinorTonality Class ---


def test_minor_tonality_scales_generation():
    """
    Verifies if the three minor scales (natural, harmonic, melodic) are generated correctly.
    """
    # GIVEN: An A minor tonality
    tonality = MinorTonality("A")

    # THEN: The scales should be generated correctly
    expected_natural = ["A", "B", "C", "D", "E", "F", "G"]
    expected_harmonic = ["A", "B", "C", "D", "E", "F", "G#"]
    expected_melodic = ["A", "B", "C", "D", "E", "F#", "G#"]

    assert tonality.scales["natural"] == expected_natural
    assert tonality.scales["harmonic"] == expected_harmonic
    assert tonality.scales["melodic"] == expected_melodic
    assert tonality.tonality_name == "A minor"


def test_minor_tonality_harmonic_field_contains_all_modes():
    """
    Verifies if the minor harmonic field includes triads from all three scales.
    """
    # GIVEN: An A minor tonality
    tonality = MinorTonality("A")
    harmonic_field = tonality.harmonic_field

    # THEN: Representative chords from each mode should be present in their functions
    # From the natural scale
    assert "Am" in harmonic_field["TONIC"]  # i
    assert "C" in harmonic_field["TONIC"]  # bIII
    assert "G" in harmonic_field["DOMINANT"]  # bVII

    # From the harmonic scale
    assert "E" in harmonic_field["DOMINANT"]  # V (major)
    assert "G#dim" in harmonic_field["DOMINANT"]  # viidim

    # From the melodic scale
    assert "Bm" in harmonic_field["SUBDOMINANT"]  # ii
    assert "F#dim" in harmonic_field["SUBDOMINANT"]  # vidim
    assert "Caug" in harmonic_field["TONIC"]  # bIII+


# --- Test for Main JSON Generation Function ---


def test_generate_tonal_data_json(tmp_path: Path):
    """
    Tests the JSON file generation function.
    Uses pytest's 'tmp_path' fixture to create a temporary directory.
    """
    # GIVEN: a path to a temporary output file
    output_file = tmp_path / "test_tonalities.json"

    # WHEN: the generation function is called
    generate_tonal_data_json(str(output_file))

    # THEN:
    # 1. The file should exist
    assert output_file.exists()

    # 2. The file content should be valid JSON
    with open(output_file, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            pytest.fail("The generated file is not valid JSON.")

    # 3. The JSON should contain 24 tonalities (12 major, 12 minor)
    assert isinstance(data, list)
    assert len(data) == 24

    # 4. The structure of one of the tonalities should be correct
    c_major_data = next((item for item in data if item["tonality_name"] == "C Major"), None)
    assert c_major_data is not None
    assert "function_to_chords_map" in c_major_data
    assert "TONIC" in c_major_data["function_to_chords_map"]
    assert "C" in c_major_data["function_to_chords_map"]["TONIC"]
