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
        Checks if a chord sequence is a valid tonal progression in
        any of the provided tonalities.
        """
        if not input_chord_sequence:
            failure_explanation = Explanation()
            failure_explanation.add_step(formal_rule_applied="Failure", observation="Input chord sequence is empty.")
            return False, failure_explanation

        reversed_chord_sequence = list(reversed(input_chord_sequence))

        # The first chord of the reversed sequence is the last of the original.
        last_chord_of_original_progression = reversed_chord_sequence[0]

        initial_state = self.kripke_config.get_state_by_tonal_function(TonalFunction.TONIC)
        if not initial_state:
            failure_explanation = Explanation()
            failure_explanation.add_step(
                formal_rule_applied="Configuration Error",
                observation="Kripke structure configuration is missing a TONIC state."
            )
            return False, failure_explanation

        # Iterate over each candidate tonality to find one that satisfies the progression.
        for candidate_tonality in tonalities_to_test:

            # The analysis of a progression in a given tonality cannot even begin if its last chord is not a tonic of that tonality.
            if not candidate_tonality.chord_fulfills_function(last_chord_of_original_progression, TonalFunction.TONIC):
                continue

            # For each attempt in a new tonality, we create a new evaluator.
            evaluator = SatisfactionEvaluator(self.kripke_config, self.all_available_tonalities, candidate_tonality)
            initial_explanation = Explanation()
            initial_explanation.add_step(
                formal_rule_applied="Analysis Start",
                observation=f"Testing progression in tonality: '{candidate_tonality.tonality_name}'.",
                tonality_used_in_step=candidate_tonality
            )

            # The recursive call now also receives the ranked list of tonalities for optimization
            success, final_explanation = evaluator.evaluate_satisfaction_recursive(
                current_tonality=candidate_tonality,
                current_state=initial_state,
                remaining_chords=reversed_chord_sequence,
                recursion_depth=0,
                parent_explanation=initial_explanation,
                ranked_tonalities=tonalities_to_test
            )
            
            # If a solution is found, return immediately with success and explanation.
            if success:
                final_explanation.add_step(
                    formal_rule_applied="Overall Success",
                    observation=f"Progression identified as tonal in '{candidate_tonality.tonality_name}'.",
                    tonality_used_in_step=candidate_tonality
                )
                return True, final_explanation

        # If the loop ends without finding a solution in any of the tested tonalities.
        failure_explanation = Explanation()
        failure_explanation.add_step(formal_rule_applied="Overall Failure", observation="No tested tonality satisfied the progression.")
        return False, failure_explanation