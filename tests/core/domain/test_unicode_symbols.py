"""
Tests for Unicode musical symbols support.
"""

import pytest
from core.domain.models import (
    Chord, 
    to_unicode_symbols, 
    from_unicode_symbols, 
    SHARP_SYMBOL, 
    FLAT_SYMBOL,
    normalize_note_name
)


class TestUnicodeSymbolSupport:
    """Test class for Unicode musical symbols functionality."""

    def test_to_unicode_symbols_conversion(self) -> None:
        """Test conversion from ASCII to Unicode symbols."""
        assert to_unicode_symbols("C#") == f"C{SHARP_SYMBOL}"
        assert to_unicode_symbols("Bb") == f"B{FLAT_SYMBOL}"
        assert to_unicode_symbols("F#m") == f"F{SHARP_SYMBOL}m"
        assert to_unicode_symbols("Ebdim") == f"E{FLAT_SYMBOL}dim"
        assert to_unicode_symbols("C") == "C"  # No change for natural notes

    def test_from_unicode_symbols_conversion(self) -> None:
        """Test conversion from Unicode to ASCII symbols."""
        assert from_unicode_symbols(f"C{SHARP_SYMBOL}") == "C#"
        assert from_unicode_symbols(f"B{FLAT_SYMBOL}") == "Bb"
        assert from_unicode_symbols(f"F{SHARP_SYMBOL}m") == "F#m"
        assert from_unicode_symbols(f"E{FLAT_SYMBOL}dim") == "Ebdim"
        assert from_unicode_symbols("C") == "C"  # No change for natural notes

    def test_roundtrip_conversion(self) -> None:
        """Test that ASCII -> Unicode -> ASCII preserves the original."""
        test_chords = ["C#", "Bb", "F#m", "Ebdim", "G#", "Db"]
        
        for chord in test_chords:
            unicode_version = to_unicode_symbols(chord)
            back_to_ascii = from_unicode_symbols(unicode_version)
            assert back_to_ascii == chord

    def test_chord_parsing_with_unicode_symbols(self) -> None:
        """Test that chords with Unicode symbols are parsed correctly."""
        # Test major chords with Unicode symbols
        bb_unicode = Chord(f"B{FLAT_SYMBOL}")
        bb_ascii = Chord("Bb")
        assert bb_unicode.notes == bb_ascii.notes

        cs_unicode = Chord(f"C{SHARP_SYMBOL}")
        cs_ascii = Chord("C#")
        assert cs_unicode.notes == cs_ascii.notes

    def test_chord_parsing_with_unicode_minors(self) -> None:
        """Test that minor chords with Unicode symbols are parsed correctly."""
        bbm_unicode = Chord(f"B{FLAT_SYMBOL}m")
        bbm_ascii = Chord("Bbm")
        assert bbm_unicode.notes == bbm_ascii.notes

        csm_unicode = Chord(f"C{SHARP_SYMBOL}m")
        csm_ascii = Chord("C#m")
        assert csm_unicode.notes == csm_ascii.notes

    def test_chord_parsing_with_unicode_diminished(self) -> None:
        """Test that diminished chords with Unicode symbols are parsed correctly."""
        bbdim_unicode = Chord(f"B{FLAT_SYMBOL}dim")
        bbdim_ascii = Chord("Bbdim")
        assert bbdim_unicode.notes == bbdim_ascii.notes

        csdim_unicode = Chord(f"C{SHARP_SYMBOL}dim")
        csdim_ascii = Chord("C#dim")
        assert csdim_unicode.notes == csdim_ascii.notes

    def test_chord_quality_with_unicode_symbols(self) -> None:
        """Test that chord quality detection works with Unicode symbols."""
        assert Chord(f"B{FLAT_SYMBOL}").quality == "Major"
        assert Chord(f"C{SHARP_SYMBOL}m").quality == "minor"
        assert Chord(f"E{FLAT_SYMBOL}dim").quality == "diminished"

    def test_enharmonic_mapping_with_unicode_symbols(self) -> None:
        """Test that enharmonic mapping works with Unicode symbols."""
        # Test Unicode flat symbols are properly mapped
        assert normalize_note_name(f"D{FLAT_SYMBOL}") == "C#"
        assert normalize_note_name(f"E{FLAT_SYMBOL}") == "D#"
        assert normalize_note_name(f"B{FLAT_SYMBOL}") == "A#"

        # Test Unicode sharp symbols work correctly
        assert normalize_note_name(f"E{SHARP_SYMBOL}") == "F"
        assert normalize_note_name(f"B{SHARP_SYMBOL}") == "C"

    def test_mixed_notation_handling(self) -> None:
        """Test that mixed ASCII and Unicode notation works."""
        progression = [
            Chord("C#"),                    # ASCII sharp
            Chord(f"E{FLAT_SYMBOL}"),      # Unicode flat
            Chord("F"),                     # Natural
            Chord(f"B{FLAT_SYMBOL}m")      # Unicode flat minor
        ]

        # All chords should parse correctly
        for chord in progression:
            assert len(chord.notes) > 0
            assert chord.quality in ["Major", "minor", "diminished"]

        # Test enharmonic equivalence
        assert Chord("C#").notes == Chord(f"D{FLAT_SYMBOL}").notes
        assert Chord("Bb").notes == Chord(f"B{FLAT_SYMBOL}").notes
