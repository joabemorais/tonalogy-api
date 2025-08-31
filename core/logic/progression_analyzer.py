from typing import List, Tuple

from core.domain.models import Chord, Explanation, KripkeStructureConfig, TonalFunction, Tonality
from core.logic.kripke_evaluator import SatisfactionEvaluator
from core.i18n import T


class ProgressionAnalyzer:
    """
    Orchestrates the process of analyzing a tonal progression.
    This class is the main entry point for the business logic.
    """

    def __init__(
        self, kripke_config: KripkeStructureConfig, all_available_tonalities: List[Tonality]
    ):
        """
        Initializes the ProgressionAnalyzer.
        """
        self.kripke_config = kripke_config
        self.all_available_tonalities = all_available_tonalities

    def check_tonal_progression(
        self, input_chord_sequence: List[Chord], tonalities_to_test: List[Tonality]
    ) -> Tuple[bool, Explanation]:
        """
        Checks if a chord sequence is a valid tonal progression.
        The analysis starts from the most likely tonality and explores
        other possibilities recursively.
        """
        failure_explanation = Explanation()
        if not input_chord_sequence:
            failure_explanation.add_step(
                formal_rule_applied=T("analysis.rules.failure"), 
                observation=T("analysis.messages.input_empty")
            )
            return False, failure_explanation
        if not tonalities_to_test:
            failure_explanation.add_step(
                formal_rule_applied=T("analysis.rules.failure"), 
                observation=T("analysis.messages.tonalities_empty")
            )
            return False, failure_explanation

        # The primary candidate is the first in the ranked list. This is our "home base" and starting point.
        primary_tonality = tonalities_to_test[0]

        # Create the evaluator ONCE with the fixed primary (original) tonality.
        evaluator = SatisfactionEvaluator(
            self.kripke_config, self.all_available_tonalities, primary_tonality
        )

        reversed_chord_sequence = list(reversed(input_chord_sequence))
        initial_state = self.kripke_config.get_state_by_tonal_function(TonalFunction.TONIC)

        if not initial_state:
            failure_explanation.add_step(
                formal_rule_applied=T("analysis.rules.configuration_error"),
                observation=T("analysis.messages.missing_tonic_state"),
            )
            return False, failure_explanation

        # The analysis MUST begin with the last chord being a tonic in the primary tonality.
        if not primary_tonality.chord_fulfills_function(
            reversed_chord_sequence[0], TonalFunction.TONIC
        ):
            failure_explanation.add_step(
                formal_rule_applied=T("analysis.rules.overall_failure"),
                observation=T("analysis.messages.final_chord_not_tonic", 
                             chord_name=reversed_chord_sequence[0].name,
                             tonality_name=primary_tonality.tonality_name),
            )
            return False, failure_explanation

        # We initiate the analysis only once from the primary tonality.
        # The evaluator's internal logic (pivots, re-anchoring) is responsible for exploring other tonalities.
        initial_explanation = Explanation()
        initial_explanation.add_step(
            formal_rule_applied=T("analysis.rules.analysis_start"),
            observation=T("analysis.messages.testing_progression", 
                         tonality_name=primary_tonality.tonality_name),
            tonality_used_in_step=primary_tonality,
        )

        success, final_explanation = evaluator.evaluate_satisfaction_recursive(
            current_tonality=primary_tonality,
            current_state=initial_state,
            remaining_chords=reversed_chord_sequence,
            recursion_depth=0,
            parent_explanation=initial_explanation,
            ranked_tonalities=tonalities_to_test,
        )

        if success:
            final_explanation.add_step(
                formal_rule_applied=T("analysis.rules.overall_success"),
                observation=T("analysis.messages.progression_identified", 
                             tonality_name=primary_tonality.tonality_name),
                tonality_used_in_step=primary_tonality,
            )
            return True, final_explanation

        # If the single, comprehensive analysis fails, then no solution was found.
        failure_explanation.add_step(
            formal_rule_applied=T("analysis.rules.overall_failure"),
            observation=T("analysis.messages.no_valid_path"),
        )
        return False, failure_explanation
