from typing import List, Tuple

from core.domain.models import (
    KripkeStructureConfig,
    Tonality,
    KripkeState,
    Chord,
    Explanation,
)

MAX_RECURSION_DEPTH = 50

class SatisfactionEvaluator:
    """
    Implements the complex recursive logic of Definition 5 from Aragão's paper [1]
    to determine if a sequence of chords is satisfied by a Kripke structure
    under a given key (label function L).
    """
    def __init__(self, kripke_config: KripkeStructureConfig, all_available_tonalities: List[Tonality]):
        """
        Initializes the SatisfactionEvaluator.

        Args:
            kripke_config: The base Kripke structure configuration (S, S0, SF, R).
            all_available_keys: A list of all Key objects known to the system,
                                used for trying the L' rule (modulation) from Eq. 5.
        """
        self.kripke_config: KripkeStructureConfig = kripke_config
        self.all_available_tonalities: List[Tonality] = all_available_tonalities
        # The ProgressionAnalyzer might be needed for complete phi re-evaluation
        # If we don't want a circular dependency, we can pass a reference to a method
        # or simplify phi re-evaluation to always start from the Tonic state.
        # For now, let's keep the re-evaluation logic within this class.

    def evaluate_satisfaction_recursive(
        self,
        current_tonality: Tonality,
        current_state_in_path: KripkeState,
        remaining_chord_sequence: List[Chord],
        recursion_depth: int,
        parent_explanation: Explanation # Renamed for clarity
    ) -> Tuple[bool, Explanation]:
        """
        Recursively evaluates if the remaining_chord_sequence is satisfied starting
        from current_state_in_path under current_key.

        Implements the logic from Definition 5 of Aragão, considering
        Equations 3, 4, and 5.

        Args:
            current_key: The current musical key (L) being used for evaluation.
            current_state_in_path: The current Kripke state (π_k) where the
                                   first chord of remaining_chord_sequence is being evaluated.
            remaining_chord_sequence: The list of chords (Pφ) yet to be satisfied.
                                      The first chord is P, the rest is φ.
            recursion_depth: Current depth of recursion, to prevent infinite loops.
            partial_explanation: The Explanation object being built up.

        Returns:
            A tuple (success: bool, resulting_explanation: Explanation).
            'success' is True if the sequence is satisfied, False otherwise.
            'resulting_explanation' contains the trace of the evaluation.
        """

        if recursion_depth > MAX_RECURSION_DEPTH:
            explanation_failure = parent_explanation.clone()
            explanation_failure.add_step(
                formal_rule_applied="Recursion Limit",
                observation=f"Exceeded maximum recursion depth ({MAX_RECURSION_DEPTH}).",
                evaluated_functional_state=current_state_in_path,
                tonality_used_in_step=current_tonality
            )
            return False, explanation_failure

        if not remaining_chord_sequence:
            current_explanation = parent_explanation.clone()
            current_explanation.add_step(
                formal_rule_applied="Base (Empty Seq)",
                observation="Chord sequence fully consumed successfully.",
                evaluated_functional_state=current_state_in_path,
                tonality_used_in_step=current_tonality
            )
            return True, current_explanation

        current_chord: Chord = remaining_chord_sequence[0]
        phi_sub_sequence: List[Chord] = remaining_chord_sequence[1:]

        # --- ATTEMPT 1: P in L, then φ in L via successors of current_state_in_path ---
        # (Corresponds to K,L|=π_k P and K,L|=π_{k+1,n} φ from Eq. 4A)
        p_satisfied_in_L: bool = current_tonality.chord_fulfills_function(
            current_chord,
            current_state_in_path.associated_tonal_function
        )

        if p_satisfied_in_L:
            # P is satisfied in L at the current state.
            # Clone the explanation here, as this is a valid branching point.
            explanation_after_P_in_L = parent_explanation.clone()
            explanation_after_P_in_L.add_step(
                formal_rule_applied="P in L", # A generic step for P
                observation=(
                    f"Chord '{current_chord.name}' fulfills function "
                    f"'{current_state_in_path.associated_tonal_function.to_string()}' "
                    f"in tonality '{current_tonality.tonality_name}' (at state '{current_state_in_path.state_id}')."
                ),
                evaluated_functional_state=current_state_in_path,
                processed_chord=current_chord,
                tonality_used_in_step=current_tonality
            )

            if not phi_sub_sequence: # BASE CASE 2: P is the last chord, P in L (Eq. 3)
                explanation_eq3_L = explanation_after_P_in_L # Already cloned and with added P
                explanation_eq3_L.add_step( # Add the Eq.3's conclusion
                    formal_rule_applied="Eq.3 (L)",
                    observation="End of sequence. Progression satisfied.",
                    evaluated_functional_state=current_state_in_path, # State where P was satisfied
                    processed_chord=current_chord, # The P that was satisfied
                    tonality_used_in_step=current_tonality
                )
                return True, explanation_eq3_L

            # RECURSIVE: Try φ in L via successors (Eq. 4A for φ)
            successors = self.kripke_config.get_successors_of_state(current_state_in_path)
            if successors:
                for next_state_L in successors:
                    explanation_for_L_branch = explanation_after_P_in_L.clone() # Clone from the point where P was satisfied in L
                    explanation_for_L_branch.add_step(
                        formal_rule_applied="Try φ in L (Eq.4A)",
                        observation=(
                            f"Attempting to satisfy tail '{[c.name for c in phi_sub_sequence]}' in tonality '{current_tonality.tonality_name}' "
                            f"from next state '{next_state_L.state_id}'."
                        )
                        # There's no specific current_chord/state for *this* branch attempt step
                    )
                    success_phi_L, expl_phi_L = self.evaluate_satisfaction_recursive(
                        current_tonality, next_state_L, phi_sub_sequence, recursion_depth + 1, explanation_for_L_branch
                    )
                    if success_phi_L:
                        return True, expl_phi_L
            # If we reach here, P was in L, but φ couldn't be satisfied continuing in L via successors.
            # Now, the "Refined Flow" suggests we should try generalized Option 4B for φ.
            # And also Eq. 5 (P as pivot) is an alternative for Pφ.

            # --- ATTEMPT 3: Independent re-evaluation of φ (Generalized Option 4B: K,L* |=_{\overline{\π}} φ) ---
            # This is attempted IF P was satisfied in L, BUT the direct continuation of φ in L (above) failed.
            # This corresponds to the "or K,L|=π′ϕ" from Eq.4, where π' is a new path for φ,
            # potentially in a new tonality L*.
            if phi_sub_sequence: # Only makes sense if there's a tail φ
                explanation_before_phi_re_eval = explanation_after_P_in_L.clone() # Explanation up to P being satisfied in L
                explanation_before_phi_re_eval.add_step(
                    formal_rule_applied="Attempt Eq.4B (Re-eval φ)",
                    observation=(
                        f"Continuation of tail '{[c.name for c in phi_sub_sequence]}' in tonality '{current_tonality.tonality_name}' failed. "
                        f"Now attempting to satisfy tail independently via alternative paths/tonalitys."
                    )
                )
                
                first_chord_of_phi = phi_sub_sequence[0]
                for l_star_tonality in self.all_available_tonalities:
                    # For each L*, try to start phi_sub_sequence from any state s'
                    # where the first chord of phi (P_phi) is satisfied in L*(s').
                    for potential_start_state_for_phi in self.kripke_config.states:
                        if l_star_tonality.chord_fulfills_function(first_chord_of_phi, potential_start_state_for_phi.associated_tonal_function):
                            explanation_for_phi_re_eval_branch = explanation_before_phi_re_eval.clone()
                            explanation_for_phi_re_eval_branch.add_step(
                                formal_rule_applied="Try φ in L* (Eq.4B)",
                                observation=(
                                    f"Attempting independent satisfaction of tail '{[c.name for c in phi_sub_sequence]}' "
                                    f"in tonality '{l_star_tonality.tonality_name}' starting from state '{potential_start_state_for_phi.state_id}' "
                                    f"for its first chord '{first_chord_of_phi.name}'."
                                )
                            )
                            success_phi_re_eval, expl_phi_re_eval = self.evaluate_satisfaction_recursive(
                                l_star_tonality, potential_start_state_for_phi, phi_sub_sequence,
                                recursion_depth + 1,
                                explanation_for_phi_re_eval_branch
                            )
                            if success_phi_re_eval:
                                return True, expl_phi_re_eval
            # If P was in L, but neither the continuation of φ in L (ATTEMPT 1) nor the re-evaluation of φ (ATTEMPT 3) worked,
            # we still need to consider Eq. 5 (ATTEMPT 2) as an alternative way to satisfy Pφ as a whole.

        # --- ATTEMPT 2: P as pivot to L' (Eq. 5: K,L|=π0P and K,L'|=π′0P and K,L'|=π′1,nφ) ---
        # This is an alternative to satisfy Pφ in the original tonality L.
        # Requires that P be satisfied in L at the current state (checked by p_satisfied_in_L).
        # And P is also satisfied in L' at the current state.
        # And φ is satisfied in L' from the successors of the current state.
        if p_satisfied_in_L: # Condition 1 of Eq. 5: K,L|=π_k P
            for alternative_tonality_for_pivot in self.all_available_tonalities:
                if alternative_tonality_for_pivot.tonality_name == current_tonality.tonality_name:
                    continue # Not really an alternative L'

                # Condition 2 of Eq. 5: K,L'|=π_k P (using current_state_in_path as π_k for L')
                p_satisfied_in_L_prime_for_pivot: bool = alternative_tonality_for_pivot.chord_fulfills_function(
                    current_chord,
                    current_state_in_path.associated_tonal_function
                )

                if p_satisfied_in_L_prime_for_pivot:
                    # P is satisfied in L (p_satisfied_in_L) AND P is satisfied in L' (p_satisfied_in_L_prime_for_pivot)
                    # at the same current_state_in_path.
                    explanation_after_P_in_L_and_Lprime = parent_explanation.clone() # Start from parent, as this is an alternative for Pφ
                    explanation_after_P_in_L_and_Lprime.add_step(
                        formal_rule_applied="Eq.5 (P in L & L')",
                        observation=(
                            f"Chord '{current_chord.name}' acts as pivot: fulfills function "
                            f"'{current_state_in_path.associated_tonal_function.to_string()}' "
                            f"in original tonality '{current_tonality.tonality_name}' AND in alternative tonality '{alternative_tonality_for_pivot.tonality_name}' "
                            f"at state '{current_state_in_path.state_id}'."
                        ),
                        evaluated_functional_state=current_state_in_path,
                        processed_chord=current_chord,
                        tonality_used_in_step=current_tonality # Or maybe both? For clarity, the original.
                    )

                    if not phi_sub_sequence: # BASE CASE: P is the last, satisfied via Eq. 5
                        explanation_eq5_L_prime_p_last = explanation_after_P_in_L_and_Lprime
                        explanation_eq5_L_prime_p_last.add_step(
                            formal_rule_applied="Eq.5 (L', φ empty)",
                            observation="End of sequence. Progression satisfied via pivot chord.",
                            # evaluated_functional_state, processed_chord already in previous step
                            tonality_used_in_step=alternative_tonality_for_pivot # The "new" tonality for the (empty) tail
                        )
                        return True, explanation_eq5_L_prime_p_last

                    # RECURSIVE: Try φ in L' via successors (Condition 3 of Eq. 5)
                    successors_for_L_prime_pivot = self.kripke_config.get_successors_of_state(current_state_in_path)
                    if successors_for_L_prime_pivot:
                        for next_state_L_prime in successors_for_L_prime_pivot:
                            explanation_for_L_prime_pivot_branch = explanation_after_P_in_L_and_Lprime.clone()
                            explanation_for_L_prime_pivot_branch.add_step(
                                formal_rule_applied="Try φ in L' (Eq.5 cont.)",
                                observation=(
                                    f"Attempting to satisfy tail '{[c.name for c in phi_sub_sequence]}' in pivoted tonality '{alternative_tonality_for_pivot.tonality_name}' "
                                    f"from next state '{next_state_L_prime.state_id}'."
                                )
                            )
                            success_phi_L_prime, expl_phi_L_prime = self.evaluate_satisfaction_recursive(
                                alternative_tonality_for_pivot, next_state_L_prime, phi_sub_sequence,
                                recursion_depth + 1, explanation_for_L_prime_pivot_branch
                            )
                            if success_phi_L_prime:
                                return True, expl_phi_L_prime
                    # If φ couldn't be satisfied in L' after the pivot, this branch of Eq.5 fails.
        
        # If P was not satisfied in L (p_satisfied_in_L is False), AND
        # the attempt to use P as pivot to L' (ATTEMPT 2) also didn't work (or wasn't applicable),
        # OR if P was satisfied in L but none of the continuations for φ (ATTEMPT 1 or ATTEMPT 3) worked.
        # Then, this branch of the evaluation fails for current_chord.
        final_branch_explanation = parent_explanation.clone()
        final_branch_explanation.add_step(
            formal_rule_applied="Branch Failure",
            observation=(
                f"Chord '{current_chord.name}' could not be satisfied from state "
                f"'{current_state_in_path.state_id}' ({current_state_in_path.associated_tonal_function.to_string()}) "
                f"under tonality '{current_tonality.tonality_name}' through any applicable rule (Eq.3, Eq.4A, Eq.4B general, or Eq.5)."
            ),
            evaluated_functional_state=current_state_in_path,
            processed_chord=current_chord,
            tonality_used_in_step=current_tonality
        )
        return False, final_branch_explanation