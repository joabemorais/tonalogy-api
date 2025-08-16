"""
Defines visual themes (colors) for different tonalities.
"""
import pandas as pd
from pathlib import Path
from typing import Dict

# Path to the color configuration file
CONFIG_PATH = Path(__file__).parent / "config" / "tonality_colors.csv"

# Default Theme (will be used if a tonality doesn't have a specific theme)
DEFAULT_THEME = {
    'primary_fill': '#f0f0f080',      # Light gray with transparency
    'primary_stroke': '#444444',      # Dark gray
    'primary_text_color': '#000000',
    'secondary_fill': '#e3e3e380',    # Gray with transparency
    'secondary_stroke': '#666666',
    'secondary_text_color': '#000000',
    'annotation_gray': '#555555'
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
                'secondary_fill': '#ffd8a880', # Example secondary color
                'secondary_stroke': '#ffa94d',
                'secondary_text_color': '#e8590c',
                'annotation_gray': '#555555'
            }
        return themes
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return {}

TONALITY_THEMES = _load_themes_from_csv(CONFIG_PATH)

def get_theme_for_tonality(tonality_name: str) -> dict:
    """Searches for a theme for a tonality, returning the default if not found."""
    return
