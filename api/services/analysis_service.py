from typing import List, Dict, Optional

# Import API and domain models
from api.schemas.analysis_schemas import ProgressionAnalysisRequest, ExplanationStepAPI, ProgressionAnalysisResponse, InterpretationResult
from core.domain.models import Chord, Tonality, Explanation
from core.logic.progression_analyzer import ProgressionAnalyzer
from core.config.knowledge_base import TonalKnowledgeBase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TonalAnalysisService:
    """
    The service layer that handles high-level business logic,
    connecting the API to the analysis core.
    """
    def __init__(self, knowledge_base: TonalKnowledgeBase) -> None:
        # The service is initialized with access to our tonal knowledge base.
        self.knowledge_base = knowledge_base
        self.analyzer = ProgressionAnalyzer(
            kripke_config=self.knowledge_base.kripke_config,
            all_available_tonalities=self.knowledge_base.all_tonalities
        )
        self.tonalities_map: Dict[str, Tonality] = {
            t.tonality_name: t for t in self.knowledge_base.all_tonalities
        }

    def analyze_progression(self, request: ProgressionAnalysisRequest) -> ProgressionAnalysisResponse:
        """
        Executes the analysis of a chord progression.

        Args:
            request: The API request object validated by Pydantic.

        Returns:
            An API response object ready to be serialized as JSON.
        """
        try:
            input_chords: List[Chord] = [Chord(c) for c in request.chords]

            tonalities_to_test: List[Tonality]
            if request.tonalities_to_test:
                tonalities_to_test = [self.tonalities_map[name] for name in request.tonalities_to_test if name in self.tonalities_map]
                if not tonalities_to_test:
                    return ProgressionAnalysisResponse(
                        is_tonal_progression=False,
                        error="None of the specified tonalities are known by the system."
                    )
            else:
                tonalities_to_test = self.knowledge_base.all_tonalities

            analyzer = ProgressionAnalyzer(
                kripke_config=self.knowledge_base.kripke_config,
                all_available_tonalities=self.knowledge_base.all_tonalities
            )

            # The analyzer now returns a list of all valid Explanation objects
            all_explanations: List[Explanation] = analyzer.check_tonal_progression(input_chords, tonalities_to_test)

            if not all_explanations:
                return ProgressionAnalysisResponse(is_tonal_progression=False, possible_interpretations=[])

            # Process each found explanation into an InterpretationResult
            possible_interpretations: List[InterpretationResult] = []
            for explanation in all_explanations:
                # The identified key is the one used in the "Analysis Start" step
                start_step = explanation.steps[0]
                identified_key = start_step.tonality_used_in_step.tonality_name if start_step.tonality_used_in_step else "Unknown"

                explanation_steps_api: List[ExplanationStepAPI] = [
                    ExplanationStepAPI(
                        formal_rule_applied=step.formal_rule_applied,
                        observation=step.observation,
                        processed_chord=step.processed_chord.name if step.processed_chord else None,
                        key_used_in_step=step.tonality_used_in_step.tonality_name if step.tonality_used_in_step else None,
                        evaluated_functional_state=f"{step.evaluated_functional_state.associated_tonal_function.name} ({step.evaluated_functional_state.state_id})" if step.evaluated_functional_state else None
                    )
                    for step in explanation.steps
                ]

                possible_interpretations.append(
                    InterpretationResult(
                        identified_key=identified_key,
                        explanation_details=explanation_steps_api
                    )
                )

            return ProgressionAnalysisResponse(
                is_tonal_progression=True,
                possible_interpretations=possible_interpretations
            )

        except Exception as e:
            logging.error("Unexpected error during progression analysis", exc_info=True)
            return ProgressionAnalysisResponse(
                is_tonal_progression=False,
                error=f"An unexpected error occurred during analysis: {e}"
            )
