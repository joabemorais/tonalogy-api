import json
from typing import Dict, List, Set, Any

class TonalityGenerator:
    """
    Classe base abstrata para gerar dados de tonalidades.
    """
    NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    def __init__(self, root_note: str):
        if root_note not in self.NOTE_NAMES:
            raise ValueError(f"Tonalidade inválida: {root_note}")
        self.root_note = root_note
        self.tonality_name: str = ""
        # Dicionário para armazenar as diferentes escalas (natural, harmônica, etc.)
        self.scales: Dict[str, List[str]] = {}
        self.harmonic_field: Dict[str, Set[str]] = {}

    def _build_scale(self, steps: List[int]) -> List[str]:
        """Constrói uma escala com base nos passos fornecidos."""
        start_index = self.NOTE_NAMES.index(self.root_note)
        scale = [self.NOTE_NAMES[start_index]]
        current_index = start_index
        for step in steps[:-1]:
            current_index = (current_index + step) % len(self.NOTE_NAMES)
            scale.append(self.NOTE_NAMES[current_index])
        return scale
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte os dados da tonalidade para um dicionário serializável em JSON."""
        serializable_map = {
            func_name: sorted(list(chords))
            for func_name, chords in self.harmonic_field.items()
        }
        return {
            "key_name": self.tonality_name,
            "function_to_chords_map": serializable_map
        }

class MajorTonality(TonalityGenerator):
    """Gera o campo harmônico e as funções para uma tonalidade maior."""
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
        self.scales['natural'] = self._build_scale(self.MAJOR_SCALE_STEPS) # A escala maior é a "natural" para este modo
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
    Gera o campo harmônico e as funções para uma tonalidade menor, utilizando
    acordes das escalas natural, harmônica e melódica.
    """
    NATURAL_MINOR_STEPS = [2, 1, 2, 2, 1, 2, 2]
    
    # Mapeamento completo dos graus comuns e suas origens
    DEGREE_INFO = {
        # Grau: (Qualidade, Função, Fonte da Escala, Índice na Escala Fonte)
        "i":      {"quality": "m",   "function": "TONIC",       "source": "natural",  "index": 0},
        "iidim":  {"quality": "dim", "function": "SUBDOMINANT", "source": "natural",  "index": 1},
        "ii":     {"quality": "m",   "function": "SUBDOMINANT", "source": "melodic",  "index": 1},
        "bIII":   {"quality": "",    "function": "TONIC",       "source": "natural",  "index": 2},
        "bIII+":  {"quality": "aug", "function": "TONIC",       "source": "melodic",  "index": 2}, # Novo: 3º grau aumentado da melódica
        "iv":     {"quality": "m",   "function": "SUBDOMINANT", "source": "natural",  "index": 3},
        "IV":     {"quality": "",    "function": "SUBDOMINANT", "source": "melodic",  "index": 3},
        "v":      {"quality": "m",   "function": "DOMINANT",    "source": "natural",  "index": 4},
        "V":      {"quality": "",    "function": "DOMINANT",    "source": "harmonic", "index": 4},
        "bVI":    {"quality": "",    "function": "TONIC",       "source": "natural",  "index": 5},
        "vidim":  {"quality": "dim", "function": "SUBDOMINANT", "source": "melodic",  "index": 5}, # Novo: 6º grau diminuto da melódica
        "bVII":   {"quality": "",    "function": "DOMINANT",    "source": "natural",  "index": 6},
        "viidim": {"quality": "dim", "function": "DOMINANT",    "source": "harmonic", "index": 6},
    }
    DEGREE_LABELS = list(DEGREE_INFO.keys())

    def __init__(self, root_note: str):
        super().__init__(root_note)
        self.tonality_name = f"{self.root_note} minor"
        
        # 1. Construir a escala menor natural como base
        self.scales['natural'] = self._build_scale(self.NATURAL_MINOR_STEPS)
        
        # 2. Construir a escala menor harmônica (7ª elevada) a partir da natural
        harmonic_scale = self.scales['natural'][:]
        h_7th_idx = (self.NOTE_NAMES.index(harmonic_scale[6]) + 1) % len(self.NOTE_NAMES)
        harmonic_scale[6] = self.NOTE_NAMES[h_7th_idx]
        self.scales['harmonic'] = harmonic_scale

        # 3. Construir a escala menor melódica (6ª e 7ª elevadas) a partir da natural
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
            # Seleciona a escala correta (natural, harmônica ou melódica)
            source_scale = self.scales[info["source"]]
            # Pega a nota fundamental do acorde a partir do grau correto naquela escala
            note = source_scale[info["index"]]
            
            quality = info["quality"]
            function_name = info["function"]
            
            chord_name = f"{note}{quality}"
            field[function_name].add(chord_name)
        
        return field

def generate_tonal_data_json(filepath: str):
    """
    Gera o arquivo tonalities.json com todas as 24 tonalidades maiores e menores.
    """
    all_tonalities = []
    root_notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    
    for note in root_notes:
        try:
            major_tonality = MajorTonality(note)
            all_tonalities.append(major_tonality.to_dict())
            
            minor_tonality = MinorTonality(note)
            all_tonalities.append(minor_tonality.to_dict())
        except ValueError as e:
            print(f"Erro ao gerar tonalidade para {note}: {e}")
            
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(all_tonalities, f, indent=2, ensure_ascii=False)
        
    print(f"Arquivo '{filepath}' gerado com sucesso com {len(all_tonalities)} tonalidades.")

if __name__ == "__main__":
    output_path = "core/config/data/tonalities.json"
    generate_tonal_data_json(output_path)

    print("\nExemplo para C Major (Tríades):")
    c_major = MajorTonality("C")
    print(json.dumps(c_major.to_dict(), indent=2))
    
    print("\nExemplo para A minor (com acordes de todas as escalas):")
    a_minor = MinorTonality("A")
    print(json.dumps(a_minor.to_dict(), indent=2))
