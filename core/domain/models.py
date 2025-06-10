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


@dataclass
class Key:
    """
    Representa uma Tonalidade, que é uma função de rótulo L_i no formalismo.
    Mapeia funções tonais a conjuntos de acordes que podem realizá-las.
    Não usamos 'frozen=True' aqui, pois poderíamos querer adicionar ou
    modificar os mapeamentos de acordes no futuro, embora seja improvável.
    """

    key_name: str
    function_to_chords_map: Dict[TonalFunction, Set[Chord]]

    def get_chords_for_function(self, func: TonalFunction) -> Set[Chord]:
        """Retorna o conjunto de acordes para uma dada função tonal."""
        return self.function_to_chords_map.get(func, set())

    def chord_fulfills_function(
        self, test_chord: Chord, target_function: TonalFunction
    ) -> bool:
        """Verifica se um acorde cumpre uma determinada função nesta tonalidade."""
        return test_chord in self.get_chords_for_function(target_function)


@dataclass
class KripkeStructureConfig:
    """
    Define a parte estática da estrutura de Kripke: <S, S0, SF, R>.
    Esta configuração é a base sobre a qual as diferentes Tonalidades (L_i) operam.
    'field(default_factory=set)' é usado para garantir que um novo conjunto vazio
    seja criado para cada instância se nenhum valor for fornecido, evitando
    problemas com objetos mutáveis como padrões em classes.
    """

    states: Set[KripkeState] = field(default_factory=set)
    initial_states_S0: Set[KripkeState] = field(default_factory=set)
    final_states_SF: Set[KripkeState] = field(default_factory=set)
    # A Relação de Acessibilidade R é um conjunto de tuplas, onde cada tupla
    # representa uma transição permitida de um estado para outro.
    accessibility_relation_R: Set[Tuple[KripkeState, KripkeState]] = field(
        default_factory=set
    )
