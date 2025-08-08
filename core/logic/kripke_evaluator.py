from typing import List, Tuple, Optional

# Import the domain models we created previously
from core.domain.models import (
    Chord, KripkeState, Tonality, KripkeStructureConfig,
    Explanation, TonalFunction, KripkePath
)

# Constant to avoid infinite recursion in complex cases
MAX_RECURSION_DEPTH = 20

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
        current_path: KripkePath,
        parent_explanation: Explanation,
        recursion_depth: int
    ) -> Tuple[bool, Optional[Explanation], Optional[KripkePath]]:
        """
        ATTEMPT 1: Implements direct continuation (Aragão's Eq. 4A).
        Checks if P fits and, if so, tries to satisfy the tail (phi) in successor states.
        """
        # Check that current_path is not empty to avoid IndexError
        if not current_path or len(current_path) == 0:
            return False, None, None
        current_state = current_path.get_current_state()
        # Ensure the path is not empty before accessing the current tonality
        if current_state is None or current_path.is_empty():
            return False, None, None
        current_tonality = current_path.get_current_tonality()

        if not current_tonality.chord_fulfills_function(p_chord, current_state.associated_tonal_function):
            return False, None, None # P doesn't fit the current function in this tonality.

        updated_path = current_path.clone()
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
                formal_rule_applied="End of Sequence",
                observation=f"End of sequence. All chords have been successfully processed.",
                evaluated_functional_state=None,
                processed_chord=None,
                tonality_used_in_step=None
            )
            return True, explanation_after_P, updated_path

        # Recursive case: Try to satisfy the tail from successors.
        for next_state in self.kripke_config.get_successors_of_state(current_state):
            next_path = updated_path.clone()
            next_path.add_step(
                next_state,
                current_tonality,
                f"Direct transition to {next_state.associated_tonal_function.name}"
            )
            success, final_explanation, final_path = self.evaluate_satisfaction_with_path(
                next_path, phi_sub_sequence, recursion_depth + 1, explanation_after_P
            )
            if success:
                return True, final_explanation, final_path

        return False, None, None

    def _try_tonicization_pivot(
        self,
        p_chord: Chord,
        phi_sub_sequence: List[Chord],
        current_path: KripkePath,
        parent_explanation: Explanation,
        recursion_depth: int
    ) -> Tuple[bool, Optional[Explanation], Optional[KripkePath]]:
        """
        ATTEMPT 2: Implements tonicization with enhanced pivot detection logic.
        """
        current_state = current_path.get_current_state()
        current_tonality = current_path.get_current_tonality()

        new_tonic_state: Optional[KripkeState] = self.kripke_config.get_state_by_tonal_function(TonalFunction.TONIC)
        if not new_tonic_state:
            return False, None, None

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

            pivot_path = current_path.clone()
            pivot_path.add_step(
                new_tonic_state,
                l_prime_tonality,
                f"Pivot: {p_chord.name} from {current_tonality.tonality_name} to {l_prime_tonality.tonality_name}"
            )

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
                return True, explanation_for_pivot, pivot_path

            # Recursive Case: Try to satisfy the tail (phi) from SUCCESSORS of the new tonic.
            # This is the correct continuation logic.
            for next_state in self.kripke_config.get_successors_of_state(new_tonic_state):
                next_path = pivot_path.clone()
                next_path.add_step(
                    next_state,
                    l_prime_tonality,
                    f"Transition to {next_state.associated_tonal_function.name} in {l_prime_tonality.tonality_name}"
                )
                success, final_explanation, final_path = self.evaluate_satisfaction_with_path(
                    next_path,
                    phi_sub_sequence,
                    recursion_depth + 1,
                    explanation_for_pivot
                )
                if success:
                    return True, final_explanation, final_path
        
        return False, None, None # No pivot opportunity was found or successful.

    def _try_reanchor_tail(
        self,
        phi_sub_sequence: List[Chord],
        parent_explanation: Explanation,
        recursion_depth: int
    ) -> Tuple[bool, Optional[Explanation], Optional[KripkePath]]:
        """
        ATTEMPT 3: General tail re-anchoring (Aragão's Eq. 4B).
        Tries to satisfy the tail as a new problem, prioritizing the original tonality.
        """
        if not phi_sub_sequence:
            return False, None, None # There's no tail to re-anchor.

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
            return False, None, None

        for l_star_tonality in tonalities_to_try:
            reanchor_path = KripkePath()
            reanchor_path.add_step(
                tonic_start_state,
                l_star_tonality,
                f"Re-anchor in {l_star_tonality.tonality_name}"
            )

            success, final_explanation, final_path = self.evaluate_satisfaction_with_path(
                reanchor_path,
                phi_sub_sequence,
                recursion_depth + 1,
                explanation_before_reanchor
            )
            if success:
                return True, final_explanation, final_path

        return False, None, None # Re-anchoring failed in all tonalities.

    def evaluate_satisfaction_with_path(
        self,
        current_path: KripkePath,
        remaining_chords: List[Chord],
        recursion_depth: int,
        parent_explanation: Explanation
    ) -> Tuple[bool, Explanation, Optional[KripkePath]]:
        """
        Main method that orchestrates the search for a solution using path-aware strategies.
        Implements Aragão's Definition 5 with path tracking from Definition 4.
        """
        # Initial Checks
        if recursion_depth > MAX_RECURSION_DEPTH:
            explanation_failure = parent_explanation.clone()
            explanation_failure.add_step(formal_rule_applied="Recursion Limit", observation="Exceeded maximum recursion depth.")
            return False, explanation_failure, None

        if not remaining_chords:
            return True, parent_explanation, current_path

        p_chord: Chord = remaining_chords[0]
        phi_sub_sequence: List[Chord] = remaining_chords[1:]

        # ATTEMPT 1: Direct Continuation
        success, explanation, path = self._try_direct_continuation(
            p_chord, phi_sub_sequence, current_path, parent_explanation, recursion_depth
        )
        if success:
            return True, explanation, path

        # ATTEMPT 2: Tonicization/Pivot
        success, explanation, path = self._try_tonicization_pivot(
            p_chord, phi_sub_sequence, current_path, parent_explanation, recursion_depth
        )
        if success:
            return True, explanation, path

        # ATTEMPT 3: Re-anchoring (with path tracking)
        current_state = current_path.get_current_state()
        current_tonality = current_path.get_current_tonality()
        
        p_is_valid_in_current_context: bool = current_tonality.chord_fulfills_function(p_chord, current_state.associated_tonal_function)

        if p_is_valid_in_current_context:
            explanation_before_reanchor = parent_explanation.clone()
            explanation_before_reanchor.add_step(
                formal_rule_applied="P in L (prior to re-anchor)",
                observation=f"Chord '{p_chord.name}' is valid in '{current_tonality.tonality_name}', but direct continuation failed. Attempting to re-anchor tail. Current path: {current_path.to_readable_format()}",
                evaluated_functional_state=current_state,
                processed_chord=p_chord,
                tonality_used_in_step=current_tonality
            )

            success, explanation, path = self._try_reanchor_tail(
                phi_sub_sequence, explanation_before_reanchor, recursion_depth
            )
            if success:
                return True, explanation, path

        return False, parent_explanation, None

    # Keep the original method for compatibility
    def evaluate_satisfaction_recursive(
        self,
        current_tonality: Tonality,
        current_state: KripkeState,
        remaining_chords: List[Chord],
        recursion_depth: int,
        parent_explanation: Explanation
    ) -> Tuple[bool, Explanation]:
        """
        Wrapper method for backward compatibility. Creates initial path and calls path-aware version.
        """
        initial_path = KripkePath()
        initial_path.add_step(current_state, current_tonality, f"Starting analysis in {current_tonality.tonality_name}")
        
        success, explanation, final_path = self.evaluate_satisfaction_with_path(
            initial_path, remaining_chords, recursion_depth, parent_explanation
        )
        
        return success, explanation
