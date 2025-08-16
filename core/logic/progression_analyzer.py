from typing import List, Tuple
from core.domain.models import (
    Chord, Tonality, KripkeStructureConfig, Explanation, TonalFunction
)
from core.logic.kripke_evaluator import SatisfactionEvaluator

class ProgressionAnalyzer:
    """
    Orchestrates the process of analyzing a tonal progression.
    This class is the main entry point for the business logic.
    """
    def __init__(self, kripke_config: KripkeStructureConfig, all_available_tonalities: List[Tonality]):
        """
        Initializes the ProgressionAnalyzer.
        """
        self.kripke_config = kripke_config
        self.all_available_tonalities = all_available_tonalities


    def check_tonal_progression(
        self,
        input_chord_sequence: List[Chord],
        tonalities_to_test: List[Tonality]
    ) -> Tuple[bool, Explanation]:
        """
        Checks if a chord sequence is a valid tonal progression.
        The analysis starts from the most likely tonality and explores
        other possibilities recursively.
        """
        failure_explanation = Explanation()
        if not input_chord_sequence:
            failure_explanation.add_step(formal_rule_applied="Failure", observation="Input chord sequence is empty.")
            return False, failure_explanation
        if not tonalities_to_test:
            failure_explanation.add_step(formal_rule_applied="Failure", observation="List of tonalities to test is empty.")
            return False, failure_explanation

        # The primary candidate is the first in the ranked list. This is our "home base" and starting point.
        primary_tonality = tonalities_to_test[0]

        # Create the evaluator ONCE with the fixed primary (original) tonality.
        evaluator = SatisfactionEvaluator(self.kripke_config, self.all_available_tonalities, primary_tonality)

        reversed_chord_sequence = list(reversed(input_chord_sequence))
        initial_state = self.kripke_config.get_state_by_tonal_function(TonalFunction.TONIC)

        if not initial_state:
            failure_explanation.add_step(
                formal_rule_applied="Configuration Error",
                observation="Kripke structure configuration is missing a TONIC state."
            )
            return False, failure_explanation

        # The analysis MUST begin with the last chord being a tonic in the primary tonality.
        if not primary_tonality.chord_fulfills_function(reversed_chord_sequence[0], TonalFunction.TONIC):
            failure_explanation.add_step(
                formal_rule_applied="Overall Failure",
                observation=f"The progression's final chord '{reversed_chord_sequence[0].name}' is not a tonic in the most likely tonality '{primary_tonality.tonality_name}'. Analysis cannot proceed."
            )
            return False, failure_explanation

        # We initiate the analysis only once from the primary tonality.
        # The evaluator's internal logic (pivots, re-anchoring) is responsible for exploring other tonalities.
        initial_explanation = Explanation()
        initial_explanation.add_step(
            formal_rule_applied="Analysis Start",
            observation=f"Testing progression with primary tonality: '{primary_tonality.tonality_name}'.",
            tonality_used_in_step=primary_tonality
        )

        success, final_explanation = evaluator.evaluate_satisfaction_recursive(
            current_tonality=primary_tonality,
            current_state=initial_state,
            remaining_chords=reversed_chord_sequence,
            recursion_depth=0,
            parent_explanation=initial_explanation,
            ranked_tonalities=tonalities_to_test
        )
        
        if success:
            final_explanation.add_step(
                formal_rule_applied="Overall Success",
                observation=f"Progression identified as tonal, anchored in '{primary_tonality.tonality_name}'.",
                tonality_used_in_step=primary_tonality
            )
            return True, final_explanation

        # If the single, comprehensive analysis fails, then no solution was found.
        failure_explanation.add_step(formal_rule_applied="Overall Failure", observation="No valid analytical path found for the progression.")
        return False, failure_explanation
