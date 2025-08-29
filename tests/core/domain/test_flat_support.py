"""
Tests for flat notation support in chord parsing.
"""

import pytest
from core.domain.models import Chord, normalize_note_name


class TestFlatSupport:
    """Test class for flat notation support functionality."""

    def test_normalize_note_name_flats_to_sharps(self) -> None:
        """Test that flat notes are correctly converted to their sharp equivalents."""
        assert normalize_note_name("Db") == "C#"
        assert normalize_note_name("Eb") == "D#"
        assert normalize_note_name("Gb") == "F#"
        assert normalize_note_name("Ab") == "G#"
        assert normalize_note_name("Bb") == "A#"

    def test_normalize_note_name_preserves_natural_and_sharp_notes(self) -> None:
        """Test that natural and sharp notes are preserved unchanged."""
        natural_notes = ["C", "D", "E", "F", "G", "A", "B"]
        sharp_notes = ["C#", "D#", "F#", "G#", "A#"]
        
        for note in natural_notes + sharp_notes:
            assert normalize_note_name(note) == note

    def test_chord_parsing_with_flats(self) -> None:
        """Test that chords with flat notation are parsed correctly."""
        # Test major chords with flats
        bb_major = Chord("Bb")
        expected_bb_notes = {"A#", "D", "F"}  # Bb major = A# major enharmonically
        assert bb_major.notes == expected_bb_notes

        eb_major = Chord("Eb")
        expected_eb_notes = {"D#", "G", "A#"}  # Eb major = D# major enharmonically
        assert eb_major.notes == expected_eb_notes

    def test_chord_parsing_with_flat_minors(self) -> None:
        """Test that minor chords with flat notation are parsed correctly."""
        bb_minor = Chord("Bbm")
        expected_bbm_notes = {"A#", "C#", "F"}  # Bb minor = A# minor enharmonically
        assert bb_minor.notes == expected_bbm_notes

        db_minor = Chord("Dbm")
        expected_dbm_notes = {"C#", "E", "G#"}  # Db minor = C# minor enharmonically
        assert db_minor.notes == expected_dbm_notes

    def test_chord_parsing_with_flat_diminished(self) -> None:
        """Test that diminished chords with flat notation are parsed correctly."""
        gb_dim = Chord("Gbdim")
        expected_gbdim_notes = {"F#", "A", "C"}  # Gb dim = F# dim enharmonically
        assert gb_dim.notes == expected_gbdim_notes

    def test_chord_quality_with_flats(self) -> None:
        """Test that chord quality detection works correctly with flat notation."""
        assert Chord("Bb").quality == "Major"
        assert Chord("Ebm").quality == "minor"
        assert Chord("Abdim").quality == "diminished"

    def test_enharmonic_equivalence(self) -> None:
        """Test that enharmonic equivalent chords produce the same notes."""
        # Test major chords
        assert Chord("Bb").notes == Chord("A#").notes
        assert Chord("Db").notes == Chord("C#").notes
        assert Chord("Eb").notes == Chord("D#").notes
        assert Chord("Gb").notes == Chord("F#").notes
        assert Chord("Ab").notes == Chord("G#").notes

        # Test minor chords
        assert Chord("Bbm").notes == Chord("A#m").notes
        assert Chord("Dbm").notes == Chord("C#m").notes
        assert Chord("Ebm").notes == Chord("D#m").notes

        # Test diminished chords
        assert Chord("Bbdim").notes == Chord("A#dim").notes
        assert Chord("Dbdim").notes == Chord("C#dim").notes

    def test_invalid_flat_combinations(self) -> None:
        """Test that unusual flat combinations are handled correctly."""
        # Notes that are less common but valid enharmonic equivalents
        cb_chord = Chord("Cb")  # Should be equivalent to B
        # Cb is now in ENHARMONIC_MAP, so it should map to B and parse correctly
        expected_cb_notes = {"B", "D#", "F#"}  # B major chord
        assert cb_chord.notes == expected_cb_notes

        fb_chord = Chord("Fb")  # Should be equivalent to E
        # Fb is now in ENHARMONIC_MAP, so it should map to E and parse correctly
        expected_fb_notes = {"E", "G#", "B"}  # E major chord
        assert fb_chord.notes == expected_fb_notes
