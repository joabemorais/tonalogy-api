from typing import List, Dict

# Importar os modelos da API e do domínio
from api.schemas.analysis_schemas import ProgressionAnalysisRequest, ExplanationStepAPI, ProgressionAnalysisResponse
from core.domain.models import Chord, Tonality, Explanation
from core.logic.progression_analyzer import ProgressionAnalyzer
from core.config.knowledge_base import TonalKnowledgeBase
import logging

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

class TonalAnalysisService:
    """
    A camada de serviço que lida com a lógica de negócio de alto nível,
    conectando a API ao core de análise.
    """
    def __init__(self, knowledge_base: TonalKnowledgeBase):
        # O serviço é inicializado com acesso à nossa base de conhecimento tonal.
        self.knowledge_base = knowledge_base
        self.analyzer = ProgressionAnalyzer(
            kripke_config=self.knowledge_base.kripke_config,
            all_available_tonalities=self.knowledge_base.all_tonalities
        )
        self.tonalities_map: Dict[str, Tonality] = {
            t.key_name: t for t in self.knowledge_base.all_tonalities
        }

    def analyze_progression(self, request: ProgressionAnalysisRequest) -> ProgressionAnalysisResponse:
        """
        Executa a análise de uma progressão de acordes.

        Args:
            request: O objeto de requisição da API validado pelo Pydantic.

        Returns:
            Um objeto de resposta da API pronto para ser serializado como JSON.
        """
        try:
            # 1. Converter strings de acordes para objetos Chord
            input_chords = [Chord(c) for c in request.chords]

            # 2. Determinar quais tonalidades testar
            if request.keys_to_test:
                # Se o utilizador especificou tonalidades, use-as
                keys_to_test = [self.tonalities_map[name] for name in request.keys_to_test if name in self.tonalities_map]
                if not keys_to_test:
                    return ProgressionAnalysisResponse(
                        is_tonal_progression=False,
                        error="Nenhuma das tonalidades especificadas é conhecida pelo sistema."
                    )
            else:
                # Caso contrário, teste contra todas as tonalidades conhecidas
                keys_to_test = self.knowledge_base.all_tonalities

            # 3. Chamar o motor de análise do core
            success, explanation = self.analyzer.check_tonal_progression(input_chords, keys_to_test)
            
            # 4. Formatar a resposta
            identified_key = None
            if success and explanation.steps:
                 # Pega a tonalidade do último passo significativo, que geralmente contém o resultado final
                 final_step_with_key = next((step for step in reversed(explanation.steps) if step.key_used_in_step), None)
                 if final_step_with_key:
                     identified_key = final_step_with_key.key_used_in_step.key_name

            # Converter os passos da explicação para o formato da API
            explanation_steps_api = [
                ExplanationStepAPI(
                    formal_rule_applied=step.formal_rule_applied,
                    observation=step.observation,
                    processed_chord=step.processed_chord.name if step.processed_chord else None,
                    key_used_in_step=step.key_used_in_step.key_name if step.key_used_in_step else None,
                    evaluated_functional_state=f"{step.evaluated_functional_state.associated_tonal_function.name} ({step.evaluated_functional_state.state_id})" if step.evaluated_functional_state else None
                )
                for step in explanation.steps
            ]

            return ProgressionAnalysisResponse(
                is_tonal_progression=success,
                identified_key=identified_key,
                explanation_details=explanation_steps_api
            )

        except KeyError as e:
            # Handle specific KeyError (e.g., missing tonalities in the map)
            return ProgressionAnalysisResponse(
                is_tonal_progression=False,
                error=f"Key error occurred: {e}"
            )
        except ValueError as e:
            # Handle specific ValueError (e.g., invalid chord format)
            return ProgressionAnalysisResponse(
                is_tonal_progression=False,
                error=f"Value error occurred: {e}"
            )
        except Exception as e:
            # Log the full traceback for unexpected errors
            logging.error("Unexpected error during progression analysis", exc_info=True)
            return ProgressionAnalysisResponse(
                is_tonal_progression=False,
                error="An unexpected error occurred during analysis."
            )