"""
Defines the visual themes (colors) for different tonalities.
"""
import pandas as pd
from pathlib import Path
from typing import Dict

# Path to the color configuration file
CONFIG_PATH = Path(__file__).parent / "config" / "tonality_colors.csv"

# Default Theme (will be used if a tonality does not have a specific theme)
DEFAULT_THEME = {
    'primary_fill': '#f0f0f080',      # Light gray with transparency
    'primary_stroke': '#444444',      # Dark gray
    'primary_text_color': '#000000',
    'secondary_fill': '#e3e3e380',    # Gray with transparency
    'secondary_stroke': '#666666',
    'secondary_text_color': '#000000',
    'annotation_gray': '#555555'
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

def _load_themes_from_csv(file_path: Path) -> Dict[str, Dict[str, str]]:
    """Loads themes from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        themes = {}
        for _, row in df.iterrows():
            key_name = row['Key']
            themes[key_name] = {
                'primary_fill': row['Fill'] + '80', # Adds alpha
                'primary_stroke': row['Stroke'],
                'primary_text_color': row['Label'],
                'secondary_fill': '#ffd8a880', # Example of secondary color
                'secondary_stroke': '#ffa94d',
                'secondary_text_color': '#e8590c',
                'annotation_gray': '#555555'
            }
        return themes
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return {}

TONALITY_THEMES = _load_themes_from_csv(CONFIG_PATH)

def get_theme_for_tonality(tonality_name: str) -> dict:
    """
    Fetches the theme for a tonality. If the tonality is minor,
    it uses the theme of its relative major.
    """
    key_to_lookup = tonality_name
    
    # If the provided name is a minor key, find its relative major
    if tonality_name in RELATIVE_MAJOR_MAP:
        key_to_lookup = RELATIVE_MAJOR_MAP[tonality_name]

    # Return the theme for the determined key (major or relative major)
    return TONALITY_THEMES.get(key_to_lookup, DEFAULT_THEME)
