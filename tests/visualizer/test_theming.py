from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from visualizer.theming import (
    DEFAULT_LIGHT_THEME as DEFAULT_THEME,
    RELATIVE_MAJOR_MAP,
    _load_themes_from_csv,
    get_theme_for_tonality,
)


class TestTheming:
    """Test cases for theming functionality."""

    def test_default_theme_structure(self) -> None:
        """Test that DEFAULT_THEME has all required keys."""
        required_keys = [
            "primary_fill",
            "primary_stroke",
            "primary_text_color",
            "secondary_fill",
            "secondary_stroke",
            "secondary_text_color",
            "annotation_gray",
        ]

        for key in required_keys:
            assert key in DEFAULT_THEME
            assert isinstance(DEFAULT_THEME[key], str)

    def test_relative_major_map_completeness(self) -> None:
        """Test that RELATIVE_MAJOR_MAP contains expected minor keys."""
        expected_minor_keys = [
            "A minor",
            "E minor",
            "B minor",
            "F# minor",
            "C# minor",
            "G# minor",
            "D# minor",
            "A# minor",
            "D minor",
            "G minor",
            "C minor",
            "F minor",
        ]

        for minor_key in expected_minor_keys:
            assert minor_key in RELATIVE_MAJOR_MAP
            # Verify the mapped value ends with "Major"
            assert RELATIVE_MAJOR_MAP[minor_key].endswith("Major")

    def test_relative_major_map_values(self) -> None:
        """Test specific mappings in RELATIVE_MAJOR_MAP."""
        assert RELATIVE_MAJOR_MAP["A minor"] == "C Major"
        assert RELATIVE_MAJOR_MAP["E minor"] == "G Major"
        assert RELATIVE_MAJOR_MAP["D minor"] == "F Major"
        assert RELATIVE_MAJOR_MAP["F# minor"] == "A Major"
        assert RELATIVE_MAJOR_MAP["C# minor"] == "E Major"

    @patch("visualizer.theming.pd.read_csv")
    def test_load_themes_from_csv_success(self, mock_read_csv: MagicMock) -> None:
        """Test successful loading of themes from CSV."""
        # GIVEN
        mock_df = pd.DataFrame(
            {
                "Key": ["C Major", "G Major", "D Major"],
                "Stroke": ["#4dabf7", "#ff8787", "#69db7c"],
                "Fill": ["#a5d8ff", "#ffc9c9", "#b2f2bb"],
                "Label": ["#1971c2", "#e03131", "#2f9e44"],
            }
        )
        mock_read_csv.return_value = mock_df

        # WHEN
        result = _load_themes_from_csv(Path("/fake/path.csv"))

        # THEN
        assert len(result) == 3
        assert "C Major" in result
        assert "G Major" in result
        assert "D Major" in result

        # Check theme structure for C Major
        c_major_theme = result["C Major"]
        assert c_major_theme["primary_fill"] == "#a5d8ff80"  # Alpha added
        assert c_major_theme["primary_stroke"] == "#4dabf7"
        assert c_major_theme["primary_text_color"] == "#1971c2"
        assert c_major_theme["secondary_fill"] == "#ffd8a880"
        assert c_major_theme["secondary_stroke"] == "#ffa94d"

    @patch("visualizer.theming.pd.read_csv")
    def test_load_themes_from_csv_file_not_found(self, mock_read_csv: MagicMock) -> None:
        """Test loading themes when CSV file is not found."""
        # GIVEN
        mock_read_csv.side_effect = FileNotFoundError("File not found")

        # WHEN
        result = _load_themes_from_csv(Path("/nonexistent/path.csv"))

        # THEN
        assert result == {}

    @patch("visualizer.theming.pd.read_csv")
    def test_load_themes_from_csv_empty_data_error(self, mock_read_csv: MagicMock) -> None:
        """Test loading themes when CSV is empty."""
        # GIVEN
        mock_read_csv.side_effect = pd.errors.EmptyDataError("No data")

        # WHEN
        result = _load_themes_from_csv(Path("/empty/path.csv"))

        # THEN
        assert result == {}

    @patch(
        "visualizer.theming.TONALITY_THEMES",
        {
            "C Major": {
                "primary_fill": "#a5d8ff80",
                "primary_stroke": "#4dabf7",
                "primary_text_color": "#1971c2",
                "secondary_fill": "#ffd8a880",
                "secondary_stroke": "#ffa94d",
                "secondary_text_color": "#e8590c",
                "annotation_gray": "#555555",
            },
            "G Major": {
                "primary_fill": "#ffc9c980",
                "primary_stroke": "#ff8787",
                "primary_text_color": "#e03131",
                "secondary_fill": "#ffd8a880",
                "secondary_stroke": "#ffa94d",
                "secondary_text_color": "#e8590c",
                "annotation_gray": "#555555",
            },
        },
    )
    def test_get_theme_for_tonality_major_key(self) -> None:
        """Test getting theme for a major key."""
        # WHEN
        theme = get_theme_for_tonality("C Major")

        # THEN
        assert theme["primary_stroke"] == "#4dabf7"
        assert theme["primary_fill"] == "#a5d8ff80"
        assert theme["primary_text_color"] == "#1971c2"

    @patch(
        "visualizer.theming.TONALITY_THEMES",
        {
            "F Major": {
                "primary_fill": "#ffd8a880",
                "primary_stroke": "#ffa94d",
                "primary_text_color": "#e8590c",
                "secondary_fill": "#d0ebff80",
                "secondary_stroke": "#74c0fc",
                "secondary_text_color": "#339af0",
                "annotation_gray": "#555555",
            }
        },
    )
    def test_get_theme_for_tonality_minor_key_mapped_to_relative_major(self) -> None:
        """Test getting theme for a minor key (should use relative major)."""
        # WHEN
        theme = get_theme_for_tonality("D minor")  # Should map to F Major

        # THEN
        assert theme["primary_stroke"] == "#ffa94d"
        assert theme["primary_fill"] == "#ffd8a880"
        assert theme["primary_text_color"] == "#e8590c"

    def test_get_theme_for_tonality_unknown_key_returns_default(self) -> None:
        """Test getting theme for unknown key returns default theme."""
        # WHEN
        theme = get_theme_for_tonality("Unknown Key")

        # THEN
        assert theme == DEFAULT_THEME

    @patch("visualizer.theming.TONALITY_THEMES", {})
    def test_get_theme_for_tonality_empty_themes_returns_default(self) -> None:
        """Test getting theme when TONALITY_THEMES is empty."""
        # WHEN
        theme = get_theme_for_tonality("C Major")

        # THEN
        assert theme == DEFAULT_THEME

    def test_get_theme_for_tonality_minor_key_not_in_map(self) -> None:
        """Test getting theme for a minor key not in the relative map."""
        # WHEN
        theme = get_theme_for_tonality("X minor")  # Not in RELATIVE_MAJOR_MAP

        # THEN
        assert theme == DEFAULT_THEME

    @patch(
        "visualizer.theming.TONALITY_THEMES",
        {
            "C Major": {
                "primary_fill": "#a5d8ff80",
                "primary_stroke": "#4dabf7",
                "primary_text_color": "#1971c2",
                "secondary_fill": "#ffd8a880",
                "secondary_stroke": "#ffa94d",
                "secondary_text_color": "#e8590c",
                "annotation_gray": "#555555",
            }
        },
    )
    def test_get_theme_for_tonality_case_sensitivity(self) -> None:
        """Test that theme lookup is case-sensitive."""
        # WHEN
        theme_correct_case = get_theme_for_tonality("C Major")
        theme_wrong_case = get_theme_for_tonality("c major")

        # THEN
        assert theme_correct_case["primary_stroke"] == "#4dabf7"
        assert theme_wrong_case == DEFAULT_THEME

    def test_all_minor_keys_have_valid_major_mappings(self) -> None:
        """Test that all minor keys in the map point to valid major key names."""
        for minor_key, major_key in RELATIVE_MAJOR_MAP.items():
            # Each minor key should be formatted correctly
            assert minor_key.endswith(" minor")
            # Each major key should be formatted correctly
            assert major_key.endswith(" Major")
            # The root note should be valid (basic check)
            root_note = major_key.replace(" Major", "")
            assert len(root_note) in [1, 2]  # Single note or note with sharp/flat

    def test_default_theme_colors_are_valid_hex(self) -> None:
        """Test that all colors in DEFAULT_THEME are valid hex colors."""
        for key, color in DEFAULT_THEME.items():
            assert isinstance(color, str)
            assert color.startswith("#")
            # Remove alpha channel if present
            hex_part = color[:7] if len(color) == 7 else color[:9]
            # Should be valid hex
            int(hex_part[1:], 16)  # This will raise ValueError if not valid hex

    @patch("visualizer.theming.pd.read_csv")
    def test_load_themes_alpha_channel_addition(self, mock_read_csv: MagicMock) -> None:
        """Test that alpha channels are correctly added to fill colors."""
        # GIVEN
        mock_df = pd.DataFrame(
            {"Key": ["Test Key"], "Stroke": ["#ff0000"], "Fill": ["#00ff00"], "Label": ["#0000ff"]}
        )
        mock_read_csv.return_value = mock_df

        # WHEN
        result = _load_themes_from_csv(Path("/fake/path.csv"))

        # THEN
        theme = result["Test Key"]
        assert theme["primary_fill"] == "#00ff0080"  # Alpha 80 added

    def test_comprehensive_minor_to_major_circle_of_fifths(self) -> None:
        """Test that the minor to major mapping follows circle of fifths logic."""
        # Test some key relationships from music theory
        assert RELATIVE_MAJOR_MAP["A minor"] == "C Major"  # No accidentals
        assert RELATIVE_MAJOR_MAP["E minor"] == "G Major"  # 1 sharp
        assert RELATIVE_MAJOR_MAP["B minor"] == "D Major"  # 2 sharps
        assert RELATIVE_MAJOR_MAP["F# minor"] == "A Major"  # 3 sharps
        assert RELATIVE_MAJOR_MAP["D minor"] == "F Major"  # 1 flat
        assert RELATIVE_MAJOR_MAP["G minor"] == "A# Major"  # 2 flats
        assert RELATIVE_MAJOR_MAP["C minor"] == "D# Major"  # 3 flats
