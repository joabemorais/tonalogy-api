from typing import List, Tuple, Optional

# Import the domain models we created previously
from core.domain.models import (
    Chord, KripkeState, Tonality, KripkeStructureConfig,
    Explanation, TonalFunction
)

# Constant to avoid infinite recursion in complex cases
MAX_RECURSION_DEPTH = 20

# TODO: add "path" logic, as is described by Aragão in Definition 4. In the structure of Example 3 (modified for our purposes), we have the following paths: π_a = [s_t, s_d, s_sd], π_b = [s_t, s_sd] and π_c = [s_t, s_d]. Note that the paths are already inverted due to the same reasons the accessibility relations are. 

class SatisfactionEvaluator:
    """
    Implements the recursive logic of Aragão's Definition 5, refactored to
    find ALL possible valid interpretations of a progression.
    """
    def __init__(self, kripke_config: KripkeStructureConfig, all_available_tonalities: List[Tonality], original_tonality: Tonality) -> None:
        """
        Initializes the SatisfactionEvaluator.

        Args:
            kripke_config: The base Kripke structure configuration (S, S0, SF, R).
            all_available_tonalities: A list of all tonalities known to the system.
            original_tonality: The main tonality of the analysis, used to prioritize re-anchoring.
        """
        self.kripke_config: KripkeStructureConfig = kripke_config
        self.all_available_tonalities: List[Tonality] = all_available_tonalities
        self.original_tonality: Tonality = original_tonality

    def _get_observation_string(self, chord: Chord, tonality: Tonality, state: KripkeState) -> str:
        """Helper to create detailed observation strings, including scale origin."""
        func_name = state.associated_tonal_function.name
        tonality_name = tonality.tonality_name
        origin = tonality.get_chord_origin_for_function(chord, state.associated_tonal_function)

        # Add scale origin info only if it's not the default 'natural' for clarity
        if origin and origin != "natural":
            return f"Chord '{chord.name}' fulfills function '{func_name}' in '{tonality_name}' (from {origin} scale)."
        else:
            return f"Chord '{chord.name}' fulfills function '{func_name}' in '{tonality_name}'."

    def evaluate_satisfaction_recursive(
        self,
        current_tonality: Tonality,
        current_state: KripkeState,
        remaining_chords: List[Chord],
        recursion_depth: int,
        parent_explanation: Explanation
    ) -> List[Explanation]:
        """
        Main recursive method. Returns a list of all successful explanation paths.
        An empty list signifies failure from this branch.
        """
        # --- Initial Checks ---
        if recursion_depth > MAX_RECURSION_DEPTH:
            # This path is too deep, return failure (empty list)
            return []

        # Base case: an empty chord sequence is satisfied.
        if not remaining_chords:
            final_explanation = parent_explanation.clone()
            final_explanation.add_step(
                formal_rule_applied="End of Sequence",
                observation="End of sequence. All chords have been successfully processed."
            )
            return [final_explanation]

        p_chord: Chord = remaining_chords[0]
        phi_sub_sequence: List[Chord] = remaining_chords[1:]
        
        all_found_solutions: List[Explanation] = []

        # --- SEARCH STRATEGIES ---
        # The logic now explores all possibilities and accumulates solutions.

        # STRATEGY 1: Direct Continuation in Current Tonality (L)
        if current_tonality.chord_fulfills_function(p_chord, current_state.associated_tonal_function):
            observation = self._get_observation_string(p_chord, current_tonality, current_state)

            for next_state in self.kripke_config.get_successors_of_state(current_state):
                explanation_branch = parent_explanation.clone()
                explanation_branch.add_step(
                    formal_rule_applied="P in L",
                    observation=observation,
                    processed_chord=p_chord,
                    tonality_used_in_step=current_tonality,
                    evaluated_functional_state=current_state
                )
                
                solutions = self.evaluate_satisfaction_recursive(
                    current_tonality, next_state, phi_sub_sequence, recursion_depth + 1, explanation_branch
                )
                all_found_solutions.extend(solutions)

        # STRATEGY 2: Tonicization Pivot (Change to L')
        new_tonic_state = self.kripke_config.get_state_by_tonal_function(TonalFunction.TONIC)
        if new_tonic_state:
            for l_prime_tonality in self.all_available_tonalities:
                if l_prime_tonality.tonality_name == current_tonality.tonality_name:
                    continue

                if l_prime_tonality.chord_fulfills_function(p_chord, TonalFunction.TONIC):
                    explanation_for_pivot = parent_explanation.clone()
                    explanation_for_pivot.add_step(
                        formal_rule_applied="Tonicization Pivot",
                        observation=f"Chord '{p_chord.name}' acts as pivot, becoming the new TONIC in '{l_prime_tonality.tonality_name}'.",
                        processed_chord=p_chord,
                        tonality_used_in_step=current_tonality,
                        evaluated_functional_state=current_state
                    )

                    for next_state in self.kripke_config.get_successors_of_state(new_tonic_state):
                        solutions = self.evaluate_satisfaction_recursive(
                            l_prime_tonality, next_state, phi_sub_sequence, recursion_depth + 1, explanation_for_pivot
                        )
                        all_found_solutions.extend(solutions)

        # STRATEGY 3: General Re-anchoring of the Tail
        # This allows interpretations like the one you suggested for "Em".
        tonic_start_state = self.kripke_config.get_state_by_tonal_function(TonalFunction.TONIC)
        if not phi_sub_sequence or not tonic_start_state: # Re-anchoring needs a tail and a tonic state
             return all_found_solutions

        # We can re-anchor if P is valid in the current context, but continuation failed OR
        # even if it succeeded, to find alternative readings.
        if current_tonality.chord_fulfills_function(p_chord, current_state.associated_tonal_function):
            explanation_before_reanchor = parent_explanation.clone()
            observation = self._get_observation_string(p_chord, current_tonality, current_state)
            explanation_before_reanchor.add_step(
                formal_rule_applied="P in L (prior to re-anchor)",
                observation=f"{observation} Attempting to re-anchor remaining sequence.",
                processed_chord=p_chord,
                tonality_used_in_step=current_tonality,
                evaluated_functional_state=current_state
            )

            tonalities_to_try = [self.original_tonality] + [
                k for k in self.all_available_tonalities if k.tonality_name != self.original_tonality.tonality_name
            ]

            for l_star_tonality in tonalities_to_try:
                reanchor_explanation = explanation_before_reanchor.clone()
                reanchor_explanation.add_step(
                    formal_rule_applied="Re-anchor Tail",
                    observation=f"Re-anchoring tail to '{l_star_tonality.tonality_name}'."
                )
                solutions = self.evaluate_satisfaction_recursive(
                    l_star_tonality, tonic_start_state, phi_sub_sequence, recursion_depth + 1, reanchor_explanation
                )
                all_found_solutions.extend(solutions)

        return all_found_solutions
