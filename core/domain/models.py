from enum import Enum, auto
from typing import Set, Dict, Tuple
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Chord:
    """
    Representa um símbolo de acorde individual (e.g., "Am", "G").
    'dataclass' gera automaticamente métodos como __init__, __repr__, etc.
    'frozen=True' torna os objetos desta classe imutáveis. Uma vez criado, um
    acorde não pode ser alterado. Isso é bom para a consistência dos dados.
    Como é 'frozen', o Python gera automaticamente os métodos __eq__ e __hash__,
    o que nos permite usar objetos Chord em conjuntos (sets) e como chaves de dicionários.
    """

    name: str


class TonalFunction(Enum):
    """
    Representa as categorias funcionais abstratas (Tônica, Dominante, Subdominante).
    Usar uma Enum garante que só possamos usar esses valores definidos, evitando erros.
    """

    TONIC = auto()
    DOMINANT = auto()
    SUBDOMINANT = auto()


@dataclass(frozen=True)
class KripkeState:
    """
    Representa um estado 's' na estrutura de Kripke (e.g., s_t, s_d, s_sd).
    Associa um ID de estado a uma função tonal.
    'frozen=True' também gera __eq__ e __hash__ para nós, permitindo que
    KripkeState seja usado em conjuntos e como chaves de dicionário, o que é
    essencial para representar a relação de acessibilidade R.
    """

    state_id: str
    associated_tonal_function: TonalFunction
