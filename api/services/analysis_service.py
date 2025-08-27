from typing import List, Dict, Optional
from api.schemas.analysis_schemas import ProgressionAnalysisRequest, ExplanationStepAPI, ProgressionAnalysisResponse
from core.domain.models import Chord, Tonality, Explanation
from core.logic.progression_analyzer import ProgressionAnalyzer
from core.logic.candidate_processor import CandidateProcessor
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
        self.knowledge_base = knowledge_base
        self.analyzer = ProgressionAnalyzer(
            kripke_config=self.knowledge_base.kripke_config,
            all_available_tonalities=self.knowledge_base.all_tonalities
        )
        self.candidate_processor = CandidateProcessor()
        self.tonalities_map: Dict[str, Tonality] = {
            t.tonality_name: t for t in self.knowledge_base.all_tonalities
        }

    def analyze_progression(self, request: ProgressionAnalysisRequest) -> ProgressionAnalysisResponse:
        """
        Executes the analysis of a chord progression.
        """
        try:
            if not request.chords:
                return ProgressionAnalysisResponse(is_tonal_progression=False, error="Chord list cannot be empty.")

            input_chords: List[Chord] = [Chord(c) for c in request.chords]

            initial_tonalities_to_test: List[Tonality]
            if request.tonalities_to_test:
                initial_tonalities_to_test = [self.tonalities_map[name] for name in request.tonalities_to_test if name in self.tonalities_map]
                if not initial_tonalities_to_test:
                    return ProgressionAnalysisResponse(is_tonal_progression=False, error="None of the specified tonalities are known by the system.")
            else:
                initial_tonalities_to_test = self.knowledge_base.all_tonalities

            tonalities_to_test, error = self.candidate_processor.process(input_chords, initial_tonalities_to_test)

            if error:
                return ProgressionAnalysisResponse(is_tonal_progression=False, error=error)

            success: bool
            explanation: Explanation
            success, explanation = self.analyzer.check_tonal_progression(input_chords, tonalities_to_test)

            identified_tonality: Optional[str] = None
            if success and tonalities_to_test:
                identified_tonality = tonalities_to_test[0].tonality_name

            explanation_steps_api: List[ExplanationStepAPI] = []
            for step in explanation.steps:
                evaluated_state_str = None
                if step.evaluated_functional_state:
                    state = step.evaluated_functional_state
                    evaluated_state_str = f"{state.associated_tonal_function.name} ({state.state_id})"

                api_step = ExplanationStepAPI(
                    formal_rule_applied=step.formal_rule_applied,
                    observation=step.observation,
                    processed_chord=step.processed_chord.name if step.processed_chord else None,
                    tonality_used_in_step=step.tonality_used_in_step.tonality_name if step.tonality_used_in_step else None,
                    evaluated_functional_state=evaluated_state_str
                )
                explanation_steps_api.append(api_step)

            return ProgressionAnalysisResponse(
                is_tonal_progression=success,
                identified_tonality=identified_tonality,
                explanation_details=explanation_steps_api
            )
        except Exception as e:
            logging.error("Unexpected error during progression analysis", exc_info=True)
            return ProgressionAnalysisResponse(
                is_tonal_progression=False,
                error="An unexpected error occurred during analysis."
            )
