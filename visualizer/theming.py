"""
Defines the visual themes (colors) for different tonalities.
"""

from pathlib import Path
from typing import Dict, Literal

import pandas as pd

# Path to the color configuration files
CONFIG_DIR = Path(__file__).parent / "config"
LIGHT_THEME_PATH = CONFIG_DIR / "tonality_colors.csv"
DARK_THEME_PATH = CONFIG_DIR / "tonality_colors_dark.csv"

ThemeMode = Literal["light", "dark"]

# Default Themes (will be used if a tonality does not have a specific theme)
DEFAULT_LIGHT_THEME = {
    "primary_fill": "#f0f0f080",  # Light gray with transparency
    "primary_stroke": "#444444",  # Dark gray
    "primary_text_color": "#000000",
    "secondary_fill": "#e3e3e380",  # Gray with transparency
    "secondary_stroke": "#666666",
    "secondary_text_color": "#000000",
    "annotation_gray": "#555555",
}

DEFAULT_DARK_THEME = {
    "primary_fill": "#2d3748",  # Dark gray with transparency
    "primary_stroke": "#e2e8f0",  # Light gray
    "primary_text_color": "#ffffff",
    "secondary_fill": "#4a5568",  # Gray with transparency
    "secondary_stroke": "#cbd5e0",
    "secondary_text_color": "#ffffff",
    "annotation_gray": "#a0aec0",
}

# Mapping of minor keys to their relative major keys
RELATIVE_MAJOR_MAP = {
    "A minor": "C Major",
    "E minor": "G Major",
    "B minor": "D Major",
    "F# minor": "A Major",
    "C# minor": "E Major",
    "G# minor": "B Major",
    "D# minor": "F# Major",
    "A# minor": "C# Major",
    "D minor": "F Major",
    "G minor": "A# Major",
    "C minor": "D# Major",
    "F minor": "G# Major",
}


def _load_themes_from_csv(file_path: Path, mode: ThemeMode = "light") -> Dict[str, Dict[str, str]]:
    """Loads themes from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        themes = {}

        # Choose secondary colors based on theme mode
        if mode == "dark":
            secondary_fill = "#4a556880"  # Dark secondary with alpha
            secondary_stroke = "#718096"  # Darker stroke for dark theme
            secondary_text_color = "#ffffff"
            annotation_gray = "#718096"
        else:
            secondary_fill = "#ffd8a880"  # Light secondary with alpha
            secondary_stroke = "#ffa94d"
            secondary_text_color = "#e8590c"
            annotation_gray = "#555555"

        for _, row in df.iterrows():
            key_name = row["Key"]
            themes[key_name] = {
                "primary_fill": row["Fill"] + "80",  # Adds alpha
                "primary_stroke": row["Stroke"],
                "primary_text_color": row["Label"],
                "secondary_fill": secondary_fill,
                "secondary_stroke": secondary_stroke,
                "secondary_text_color": secondary_text_color,
                "annotation_gray": annotation_gray,
            }
        return themes
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return {}


# Load both light and dark themes
LIGHT_TONALITY_THEMES = _load_themes_from_csv(LIGHT_THEME_PATH, "light")
DARK_TONALITY_THEMES = _load_themes_from_csv(DARK_THEME_PATH, "dark")

# Backward compatibility - default to light theme
TONALITY_THEMES = LIGHT_TONALITY_THEMES


def get_theme_for_tonality(tonality_name: str, mode: ThemeMode = "light") -> dict:
    """
    Fetches the theme for a tonality. If the tonality is minor,
    it uses the theme of its relative major.

    Args:
        tonality_name: The name of the tonality (e.g., "C Major", "A minor")
        mode: Theme mode - "light" or "dark"

    Returns:
        Theme dictionary with color configuration
    """
    key_to_lookup = tonality_name

    # If the provided name is a minor key, find its relative major
    if tonality_name in RELATIVE_MAJOR_MAP:
        key_to_lookup = RELATIVE_MAJOR_MAP[tonality_name]

    # Choose the appropriate theme collection and default
    if mode == "dark":
        theme_collection = DARK_TONALITY_THEMES
        default_theme = DEFAULT_DARK_THEME
    else:
        theme_collection = LIGHT_TONALITY_THEMES
        default_theme = DEFAULT_LIGHT_THEME

    # Return the theme for the determined key (major or relative major)
    return theme_collection.get(key_to_lookup, default_theme)
