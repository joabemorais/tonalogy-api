"""
Define os temas visuais (cores) para diferentes tonalidades.
"""
import pandas as pd
from pathlib import Path
from typing import Dict

# Caminho para o arquivo de configuração de cores
CONFIG_PATH = Path(__file__).parent / "config" / "tonality_colors.csv"

# Tema Padrão (será usado se uma tonalidade não tiver um tema específico)
DEFAULT_THEME = {
    'primary_fill': '#f0f0f080',      # Cinza claro com transparência
    'primary_stroke': '#444444',      # Cinza escuro
    'primary_text_color': '#000000',
    'secondary_fill': '#e3e3e380',    # Cinza com transparência
    'secondary_stroke': '#666666',
    'secondary_text_color': '#000000',
    'cinza_anotacao': '#555555'
}

def _load_themes_from_csv(file_path: Path) -> Dict[str, Dict[str, str]]:
    """Carrega os temas de um arquivo CSV."""
    try:
        df = pd.read_csv(file_path)
        themes = {}
        for _, row in df.iterrows():
            key_name = row['Key']
            themes[key_name] = {
                'primary_fill': row['Fill'] + '80', # Adiciona alfa
                'primary_stroke': row['Stroke'],
                'primary_text_color': row['Label'],
                'secondary_fill': '#ffd8a880', # Exemplo de cor secundária
                'secondary_stroke': '#ffa94d',
                'secondary_text_color': '#e8590c',
                'cinza_anotacao': '#555555'
            }
        return themes
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return {}

TONALITY_THEMES = _load_themes_from_csv(CONFIG_PATH)

def get_theme_for_tonality(tonality_name: str) -> dict:
    """Busca o tema para uma tonalidade, retornando o padrão se não for encontrado."""
    return TONALITY_THEMES.get(tonality_name, DEFAULT_THEME)
