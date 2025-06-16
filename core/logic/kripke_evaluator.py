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
    prioritize musically intuitive analysis strategies.
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
        self.original_tonality: Tonality = original_tonality # Stores the initial tonality of the analysis

    def _try_direct_continuation(
        self,
        p_chord: Chord,
        phi_sub_sequence: List[Chord],
        current_tonality: Tonality,
        current_state: KripkeState,
        parent_explanation: Explanation,
        recursion_depth: int
    ) -> Tuple[bool, Optional[Explanation]]:
        """
        ATTEMPT 1: Implements direct continuation (Aragão's Eq. 4A).
        Checks if P fits and, if so, tries to satisfy the tail (phi) in successor states.
        """
        if not current_tonality.chord_fulfills_function(p_chord, current_state.associated_tonal_function):
            return False, None # P doesn't fit the current function in this tonality.

        # P is satisfied. Log this fact.
        explanation_after_P = parent_explanation.clone()
        explanation_after_P.add_step(
            formal_rule_applied="P in L",
            observation=f"Chord '{p_chord.name}' fulfills function '{current_state.associated_tonal_function.name}' in '{current_tonality.tonality_name}'.",
            evaluated_functional_state=current_state,
            processed_chord=p_chord,
            tonality_used_in_step=current_tonality
        )

        # Base case: If P was the last chord, continuation is a success.
        if not phi_sub_sequence:
            explanation_after_P.add_step(
                formal_rule_applied=None,
                observation=f"End of sequence. All chords have been successfully processed.",
                evaluated_functional_state=None,
                processed_chord=None,
                tonality_used_in_step=None
            )
            return True, explanation_after_P

        # Recursive case: Try to satisfy the tail from successors.
        for next_state in self.kripke_config.get_successors_of_state(current_state):
            success, final_explanation = self.evaluate_satisfaction_recursive(
                current_tonality, next_state, phi_sub_sequence, recursion_depth + 1, explanation_after_P
            )
            if success:
                return True, final_explanation

        return False, None # Direct continuation from this state didn't lead to a solution.

    def _try_tonicization_pivot(
        self,
        p_chord: Chord,
        phi_sub_sequence: List[Chord],
        current_tonality: Tonality,
        current_state: KripkeState,
        parent_explanation: Explanation,
        recursion_depth: int
    ) -> Tuple[bool, Optional[Explanation]]:
        """
        ATTEMPT 2: Implements tonicization with enhanced pivot detection logic.
        """
        new_tonic_state: Optional[KripkeState] = self.kripke_config.get_state_by_tonal_function(TonalFunction.TONIC)
        if not new_tonic_state:
            return False, None

        for l_prime_tonality in self.all_available_tonalities:
            if l_prime_tonality.tonality_name == current_tonality.tonality_name:
                continue

            # --- Enhanced Pivot Detection Logic (Your Logic) ---
            p_is_tonic_in_L_prime: bool = l_prime_tonality.chord_fulfills_function(p_chord, TonalFunction.TONIC)
            if not p_is_tonic_in_L_prime:
                continue

            p_functions_in_L: List[TonalFunction] = [func for func in TonalFunction if current_tonality.chord_fulfills_function(p_chord, func)]
            
            tonicization_reinforced: bool = False
            if phi_sub_sequence:
                next_chord: Chord = phi_sub_sequence[0]
                if l_prime_tonality.chord_fulfills_function(next_chord, TonalFunction.DOMINANT):
                    tonicization_reinforced = True
            
            pivot_valid: bool = p_is_tonic_in_L_prime and (bool(p_functions_in_L) or tonicization_reinforced)
            
            if not pivot_valid:
                continue

            # --- Continuation of Analysis After Finding a Valid Pivot ---
            
            explanation_for_pivot = parent_explanation.clone()
            functions_str: str = ", ".join([f.name for f in p_functions_in_L]) if p_functions_in_L else "a transitional role"
            
            explanation_for_pivot.add_step(
                formal_rule_applied="Tonicization Pivot (Eq.5)",
                observation=(
                    f"Chord '{p_chord.name}' acts as pivot. It has '{functions_str}' in '{current_tonality.tonality_name}' "
                    f"and becomes the new TONIC in '{l_prime_tonality.tonality_name}'. "
                    f"(Reinforced by next chord: {tonicization_reinforced})"
                ),
                evaluated_functional_state=current_state,
                processed_chord=p_chord,
                tonality_used_in_step=current_tonality
            )

            # Base Case: If the pivot was the last chord, success.
            if not phi_sub_sequence:
                return True, explanation_for_pivot

            # Recursive Case: Try to satisfy the tail (phi) from SUCCESSORS of the new tonic.
            # This is the correct continuation logic.
            for next_state in self.kripke_config.get_successors_of_state(new_tonic_state):
                success, final_explanation = self.evaluate_satisfaction_recursive(
                    current_tonality=l_prime_tonality,  # The tonality is now L'
                    current_state=next_state,           # The state is the successor of the new tonic
                    remaining_chords=phi_sub_sequence,  # The tail of the progression
                    recursion_depth=recursion_depth + 1,
                    parent_explanation=explanation_for_pivot
                )
                if success:
                    return True, final_explanation
        
        return False, None # No pivot opportunity was found or successful.

    def _try_reanchor_tail(
        self,
        phi_sub_sequence: List[Chord],
        parent_explanation: Explanation,
        recursion_depth: int
    ) -> Tuple[bool, Optional[Explanation]]:
        """
        ATTEMPT 3: General tail re-anchoring (Aragão's Eq. 4B).
        Tries to satisfy the tail as a new problem, prioritizing the original tonality.
        """
        if not phi_sub_sequence:
            return False, None # There's no tail to re-anchor.

        explanation_before_reanchor = parent_explanation.clone()
        explanation_before_reanchor.add_step(
            formal_rule_applied="Attempt Eq.4B (Re-anchor Tail)",
            observation=f"Direct continuation/pivot failed. Attempting to re-evaluate tail '{[c.name for c in phi_sub_sequence]}' from a new context."
        )

        # List of tonalities to try, with the original first.
        tonalities_to_try: List[Tonality] = [self.original_tonality] + [k for k in self.all_available_tonalities if k.tonality_name != self.original_tonality.tonality_name]
        
        # The initial state for a re-anchoring is always the tonic.
        tonic_start_state: Optional[KripkeState] = self.kripke_config.get_state_by_tonal_function(TonalFunction.TONIC)
        if not tonic_start_state: 
            return False, None

        for l_star_tonality in tonalities_to_try:
            success, final_explanation = self.evaluate_satisfaction_recursive(
                l_star_tonality, tonic_start_state, phi_sub_sequence, recursion_depth + 1, explanation_before_reanchor
            )
            if success:
                return True, final_explanation

        return False, None # Re-anchoring failed in all tonalities.

    def evaluate_satisfaction_recursive(
        self,
        current_tonality: Tonality,
        current_state: KripkeState,
        remaining_chords: List[Chord],
        recursion_depth: int,
        parent_explanation: Explanation
    ) -> Tuple[bool, Explanation]:
        """
        Main method that orchestrates the search for a solution using strategies
        in order of priority.
        """
        # --- Initial Checks ---
        if recursion_depth > MAX_RECURSION_DEPTH:
            explanation_failure = parent_explanation.clone()
            explanation_failure.add_step(formal_rule_applied="Recursion Limit", observation="Exceeded maximum recursion depth.")
            return False, explanation_failure

        if not remaining_chords:
            return True, parent_explanation # Success, empty sequence.

        p_chord: Chord = remaining_chords[0]
        phi_sub_sequence: List[Chord] = remaining_chords[1:]

        # --- SEARCH STRATEGY ---

        # ATTEMPT 1: Direct Continuation
        success, explanation = self._try_direct_continuation(
            p_chord, phi_sub_sequence, current_tonality, current_state, parent_explanation, recursion_depth
        )
        if success:
            return True, explanation

        # ATTEMPT 2: Tonicization/Pivot
        success, explanation = self._try_tonicization_pivot(
            p_chord, phi_sub_sequence, current_tonality, current_state, parent_explanation, recursion_depth
        )
        if success:
            return True, explanation

        # ATTEMPT 3: General Tail Re-anchoring

        p_is_valid_in_current_context: bool = current_tonality.chord_fulfills_function(p_chord, current_state.associated_tonal_function)

        if p_is_valid_in_current_context:
            # P is valid, but direct continuation failed. Now it's time to log P
            # and try re-anchoring for its tail.
            explanation_before_reanchor = parent_explanation.clone()
            explanation_before_reanchor.add_step(
                formal_rule_applied="P in L (prior to re-anchor)",
                observation=f"Chord '{p_chord.name}' is valid in '{current_tonality.tonality_name}', but direct continuation failed. Attempting to re-anchor tail.",
                evaluated_functional_state=current_state,
                processed_chord=p_chord,
                tonality_used_in_step=current_tonality
            )

            # Try to re-anchor the tail (phi) from the current state.
            success, explanation = self._try_reanchor_tail(
                phi_sub_sequence, explanation_before_reanchor, recursion_depth
            )
            if success:
                return True, explanation

        # If no strategy worked.
        return False, parent_explanation
