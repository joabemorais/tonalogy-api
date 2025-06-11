from typing import List, Dict, Optional

# Import API and domain models
from api.schemas.analysis_schemas import ProgressionAnalysisRequest, ExplanationStepAPI, ProgressionAnalysisResponse
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
            # 1. Convert chord strings to Chord objects
            input_chords: List[Chord] = [Chord(c) for c in request.chords]

            # 2. Determine which tonalities to test
            tonalities_to_test: List[Tonality]
            if request.tonalities_to_test:
                # If the user specified tonalities, use them
                tonalities_to_test = [self.tonalities_map[name] for name in request.tonalities_to_test if name in self.tonalities_map]
                if not tonalities_to_test:
                    return ProgressionAnalysisResponse(
                        is_tonal_progression=False,
                        error="None of the specified tonalities are known by the system."
                    )
            else:
                # Otherwise, test against all known tonalities
                tonalities_to_test = self.knowledge_base.all_tonalities

            # 3. Call the core analysis engine
            success: bool
            explanation: Explanation
            success, explanation = self.analyzer.check_tonal_progression(input_chords, tonalities_to_test)
            
            # 4. Format the response
            identified_key: Optional[str] = None
            if success and explanation.steps:
                 # Get the tonality from the last significant step, which usually contains the final result
                 final_step_with_key = next((step for step in reversed(explanation.steps) if step.tonality_used_in_step), None)
                 if final_step_with_key:
                     identified_key = final_step_with_key.tonality_used_in_step.tonality_name

            # Convert explanation steps to API format
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