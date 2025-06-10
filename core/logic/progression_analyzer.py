from typing import List, Tuple

# Importar os modelos de domínio e a classe do avaliador
from core.domain.models import (
    Chord, Tonality, KripkeStructureConfig, Explanation, TonalFunction
)
from core.logic.kripke_evaluator import SatisfactionEvaluator

class ProgressionAnalyzer:
    """
    Orquestra o processo de análise de uma progressão tonal.
    Esta classe é o ponto de entrada principal para a lógica de negócio.
    """
    def __init__(self, kripke_config: KripkeStructureConfig, all_available_tonalities: List[Tonality]):
        """
        Inicializa o ProgressionAnalyzer.

        Args:
            kripke_config: A configuração base da estrutura Kripke (S, S0, SF, R).
            all_available_tonalities: Uma lista de todas as tonalidades conhecidas pelo sistema.
        """
        self.kripke_config = kripke_config
        self.all_available_tonalities = all_available_tonalities

