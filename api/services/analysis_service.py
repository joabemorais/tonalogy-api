import logging
from typing import Dict, List, Optional

from api.schemas.analysis_schemas import (
    ExplanationStepAPI,
    ProgressionAnalysisRequest,
    ProgressionAnalysisResponse,
)
from api.services.explanation_formatter import ExplanationFormatter
from core.config.knowledge_base import TonalKnowledgeBase
from core.domain.models import Chord, Explanation, Tonality
from core.i18n import T, translate_function, translate_tonality
from core.i18n.locale_manager import locale_manager
from core.logic.candidate_processor import CandidateProcessor
from core.logic.progression_analyzer import ProgressionAnalyzer

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
            all_available_tonalities=self.knowledge_base.all_tonalities,
        )
        self.candidate_processor = CandidateProcessor()
        self.explanation_formatter = ExplanationFormatter()
        self.tonalities_map: Dict[str, Tonality] = {
            t.tonality_name: t for t in self.knowledge_base.all_tonalities
        }

    def analyze_progression(
        self, request: ProgressionAnalysisRequest
    ) -> ProgressionAnalysisResponse:
        """
        Executes the analysis of a chord progression.
        """
        try:
            if not request.chords:
                return ProgressionAnalysisResponse(
                    is_tonal_progression=False,
                    identified_tonality=None,
                    explanation_details=[],
                    human_readable_explanation=None,
                    error=T("errors.chord_list_empty"),
                )

            input_chords: List[Chord] = [Chord(c) for c in request.chords]

            initial_tonalities_to_test: List[Tonality]
            if request.tonalities_to_test:
                initial_tonalities_to_test = [
                    self.tonalities_map[name]
                    for name in request.tonalities_to_test
                    if name in self.tonalities_map
                ]
                if not initial_tonalities_to_test:
                    return ProgressionAnalysisResponse(
                        is_tonal_progression=False,
                        identified_tonality=None,
                        explanation_details=[],
                        human_readable_explanation=None,
                        error="None of the specified tonalities are known by the system.",
                    )
            else:
                initial_tonalities_to_test = self.knowledge_base.all_tonalities

            tonalities_to_test, error = self.candidate_processor.process(
                input_chords, initial_tonalities_to_test
            )

            if error:
                return ProgressionAnalysisResponse(
                    is_tonal_progression=False,
                    identified_tonality=None,
                    explanation_details=[],
                    human_readable_explanation=None,
                    error=error,
                )

            success: bool
            explanation: Explanation
            success, explanation = self.analyzer.check_tonal_progression(
                input_chords, tonalities_to_test
            )

            identified_tonality: Optional[str] = None
            if success and tonalities_to_test:
                # Translate the identified tonality name
                original_tonality = tonalities_to_test[0].tonality_name
                identified_tonality = translate_tonality(
                    original_tonality, locale_manager.current_locale
                )

            explanation_steps_api: List[ExplanationStepAPI] = []
            for step in explanation.steps:
                evaluated_state_str = None
                raw_tonal_function = None
                if step.evaluated_functional_state:
                    state = step.evaluated_functional_state
                    raw_tonal_function = state.associated_tonal_function.name
                    # Translate the function name
                    translated_function = translate_function(
                        raw_tonal_function, locale_manager.current_locale
                    )
                    evaluated_state_str = f"{translated_function} ({state.state_id})"

                # Determine rule type and get pivot target from structured data
                rule_type = None
                pivot_target_tonality = None
                if step.formal_rule_applied and (
                    "Pivot" in step.formal_rule_applied or "Pivô" in step.formal_rule_applied
                ):
                    rule_type = "pivot_modulation"
                    # Use structured data instead of regex parsing
                    if step.pivot_target_tonality:
                        pivot_target_tonality = step.pivot_target_tonality.tonality_name

                api_step = ExplanationStepAPI(
                    formal_rule_applied=step.formal_rule_applied,
                    observation=step.observation,
                    processed_chord=step.processed_chord.name if step.processed_chord else None,
                    tonality_used_in_step=(
                        translate_tonality(
                            step.tonality_used_in_step.tonality_name, locale_manager.current_locale
                        )
                        if step.tonality_used_in_step
                        else None
                    ),
                    evaluated_functional_state=evaluated_state_str,
                    # Structured metadata fields
                    rule_type=rule_type,
                    tonal_function=raw_tonal_function,
                    pivot_target_tonality=pivot_target_tonality,
                    raw_tonality_used_in_step=(
                        step.tonality_used_in_step.tonality_name
                        if step.tonality_used_in_step
                        else None
                    ),
                )
                explanation_steps_api.append(api_step)

            # Create the basic response
            response = ProgressionAnalysisResponse(
                is_tonal_progression=success,
                identified_tonality=identified_tonality,
                explanation_details=explanation_steps_api,
                error=None,
            )

            # Generate human-readable explanation
            try:
                human_readable = self.explanation_formatter.format_explanation(response)
                response.human_readable_explanation = human_readable
            except Exception as e:
                logger.warning(f"Failed to generate human-readable explanation: {e}")
                response.human_readable_explanation = None

            return response
        except Exception as e:
            logging.error("Unexpected error during progression analysis", exc_info=True)
            return ProgressionAnalysisResponse(
                is_tonal_progression=False,
                identified_tonality=None,
                explanation_details=[],
                human_readable_explanation=None,
                error="An unexpected error occurred during analysis.",
            )
