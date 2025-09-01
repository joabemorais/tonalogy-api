"""
Integration test for flat notation support in progression analysis.
"""

import pytest

from core.domain.models import Chord, TonalFunction, Tonality


class TestFlatIntegration:
    """Test class for integration of flat notation support with the rest of the system."""

    @pytest.fixture
    def bb_major_tonality(self) -> Tonality:
        """Create a Bb Major tonality for testing (equivalent to A# Major)."""
        return Tonality(
            tonality_name="Bb Major",
            function_to_chords_map={
                TonalFunction.TONIC: {
                    Chord("Bb"): "natural",  # Should work with flat notation
                    Chord("Gm"): "natural",
                    Chord("Dm"): "natural",
                },
                TonalFunction.DOMINANT: {Chord("F"): "natural", Chord("F7"): "natural"},
                TonalFunction.SUBDOMINANT: {
                    Chord("Eb"): "natural",  # Should work with flat notation
                    Chord("Cm"): "natural",
                },
            },
        )

    def test_chord_fulfills_function_with_flats(self, bb_major_tonality: Tonality) -> None:
        """Test that chords with flat notation fulfill their functions correctly."""
        # Test that Bb chord fulfills Tonic function
        bb_chord = Chord("Bb")
        assert bb_major_tonality.chord_fulfills_function(bb_chord, TonalFunction.TONIC)

        # Test that Eb chord fulfills Subdominant function
        eb_chord = Chord("Eb")
        assert bb_major_tonality.chord_fulfills_function(eb_chord, TonalFunction.SUBDOMINANT)

        # Test that these are equivalent to their sharp counterparts
        a_sharp_chord = Chord("A#")
        d_sharp_chord = Chord("D#")

        # These should be considered the same due to enharmonic equivalence in the notes
        assert bb_chord.notes == a_sharp_chord.notes
        assert eb_chord.notes == d_sharp_chord.notes

    def test_progression_with_mixed_notation(self) -> None:
        """Test that progressions can mix flat and sharp notation."""
        # Create a progression that mixes flats and sharps
        progression = [
            Chord("Bb"),  # Flat notation
            Chord("F"),  # Natural
            Chord("Gm"),  # Natural
            Chord("D#"),  # Sharp notation (enharmonic to Eb)
        ]

        # All chords should parse correctly and have valid notes
        for chord in progression:
            assert len(chord.notes) > 0, f"Chord {chord.name} should have notes"
            assert chord.quality in [
                "Major",
                "minor",
                "diminished",
            ], f"Chord {chord.name} should have valid quality"

        # Test enharmonic equivalence in the progression
        bb_chord = Chord("Bb")
        a_sharp_chord = Chord("A#")
        assert bb_chord.notes == a_sharp_chord.notes

        eb_chord = Chord("Eb")
        d_sharp_chord = Chord("D#")
        assert eb_chord.notes == d_sharp_chord.notes

    def test_flat_minor_chords_in_progression(self) -> None:
        """Test that flat minor chords work correctly in progressions."""
        progression = [
            Chord("Bbm"),  # Bb minor
            Chord("Ebm"),  # Eb minor
            Chord("Fm"),  # F minor
            Chord("Gm"),  # G minor
        ]

        for chord in progression:
            assert chord.quality == "minor", f"Chord {chord.name} should be minor"
            assert len(chord.notes) == 3, f"Chord {chord.name} should have 3 notes"

        # Test enharmonic equivalence
        assert Chord("Bbm").notes == Chord("A#m").notes
        assert Chord("Ebm").notes == Chord("D#m").notes

    def test_flat_diminished_chords(self) -> None:
        """Test that flat diminished chords work correctly."""
        flat_dim_chords = [
            Chord("Bbdim"),
            Chord("Ebdim"),
            Chord("Abdim"),
            Chord("Dbdim"),
            Chord("Gbdim"),
        ]

        for chord in flat_dim_chords:
            assert chord.quality == "diminished", f"Chord {chord.name} should be diminished"
            assert len(chord.notes) == 3, f"Chord {chord.name} should have 3 notes"

        # Test enharmonic equivalence
        assert Chord("Bbdim").notes == Chord("A#dim").notes
        assert Chord("Ebdim").notes == Chord("D#dim").notes
        assert Chord("Abdim").notes == Chord("G#dim").notes
        assert Chord("Dbdim").notes == Chord("C#dim").notes
        assert Chord("Gbdim").notes == Chord("F#dim").notes
