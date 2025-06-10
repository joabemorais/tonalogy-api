from typing import List, Tuple

# Import domain models and evaluator class
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

        Args:
            kripke_config: The base configuration of the Kripke structure (S, S0, SF, R).
            all_available_tonalities: A list of all tonalities known by the system.
        """
        self.kripke_config = kripke_config
        self.all_available_tonalities = all_available_tonalities


    def check_tonal_progression(
        self,
        input_chord_sequence: List[Chord],
        keys_to_test: List[Tonality]
    ) -> Tuple[bool, Explanation]:
        """
        Checks if a chord sequence is a valid tonal progression in
        any of the provided tonalities.

        Args:
            input_chord_sequence: The list of Chord objects to be analyzed.
            keys_to_test: A list of Tonality objects to use as starting points.

        Returns:
            A tuple containing a success boolean and the Explanation object with the
            trace of the successful analysis (or the last failure).
        """
        # According to Aragão's methodology, analysis starts from end to beginning.
        reversed_chord_sequence = list(reversed(input_chord_sequence))

        if not reversed_chord_sequence:
            failure_explanation = Explanation()
            failure_explanation.add_step(formal_rule_applied="Failure", observation="Input chord sequence is empty.")
            return False, failure_explanation

        # The analysis of a tonal progression typically resolves in the tonic.
        # Therefore, the initial state for evaluating the reversed sequence is the Tonic.
        initial_state = self.kripke_config.get_state_by_tonal_function(TonalFunction.TONIC)
        if not initial_state:
            failure_explanation = Explanation()
            failure_explanation.add_step(
                formal_rule_applied="Configuration Error",
                observation="Kripke structure configuration is missing a TONIC state."
            )
            return False, failure_explanation

        # Iterate over each candidate tonality to find one that satisfies the progression.
        for candidate_tonality in keys_to_test:
            # For each attempt in a new tonality, we create a new evaluator.
            # It's crucial to pass the 'candidate_tonality' as the 'original_tonality',
            # as this informs the evaluator which is the "main" tonality
            # to be prioritized in ATTEMPT 3 (Re-anchoring).
            evaluator = SatisfactionEvaluator(self.kripke_config, self.all_available_tonalities, candidate_tonality)

            initial_explanation = Explanation()
            initial_explanation.add_step(
                formal_rule_applied="Analysis Start",
                observation=f"Testing progression in tonality: '{candidate_tonality.key_name}'.",
                key_used_in_step=candidate_tonality
            )

            success, final_explanation = evaluator.evaluate_satisfaction_recursive(
                current_tonality=candidate_tonality,
                current_state=initial_state,
                remaining_chords=reversed_chord_sequence,
                recursion_depth=0,
                parent_explanation=initial_explanation
            )

            # If a solution is found, return immediately with success and explanation.
            if success:
                final_explanation.add_step(
                    formal_rule_applied="Overall Success",
                    observation=f"Progression identified as tonal in '{candidate_tonality.key_name}'.",
                    key_used_in_step=candidate_tonality
                )
                return True, final_explanation

        # If the loop ends without finding a solution in any of the tested tonalities.
        failure_explanation = Explanation()
        failure_explanation.add_step(formal_rule_applied="Overall Failure", observation="No tested key satisfied the progression.")
        return False, failure_explanation