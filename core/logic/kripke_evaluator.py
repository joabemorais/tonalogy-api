from typing import List, Tuple, Optional

# Assuming your domain models are in core.domain.models
# Adjust the import path if your structure is different or if you've
# exposed these via __init__.py files in parent packages.
from core.domain.models import (
    KripkeStructureConfig,
    Tonality,
    KripkeState,
    Chord,
    Explanation,
    # DetailedExplanationStep is implicitly used by Explanation.add_step
)

# A practical limit to prevent infinite recursion in case of unexpected cyclic paths
# or very long non-terminating sequences. Aragão's specific examples are finite.
MAX_RECURSION_DEPTH = 50 # Adjust as needed

class SatisfactionEvaluator:
    """
    Implements the complex recursive logic of Definition 5 from Aragão's paper]
    to determine if a sequence of chords is satisfied by a Kripke structure
    under a given tonality (label function L).
    """

    def __init__(self, kripke_config: KripkeStructureConfig, all_available_tonalitys: List[Tonality]):
        """
        Initializes the SatisfactionEvaluator.

        Args:
            kripke_config: The base Kripke structure configuration (S, S0, SF, R).
            all_available_tonalitys: A list of all Tonality objects known to the system,
                                used for trying the L' rule (modulation) from Eq. 5.
        """
        self.kripke_config: KripkeStructureConfig = kripke_config
        self.all_available_tonalitys: List[Tonality] = all_available_tonalitys
        
    def evaluate_satisfaction_recursive(
        self,
        current_tonality: Tonality,                     # L
        current_state_in_path: KripkeState,        # π_k (current functional state for P)
        remaining_chord_sequence: List[Chord],     # Pφ (current chord P and tail φ)
        recursion_depth: int,
        partial_explanation: Explanation
    ) -> Tuple[bool, Explanation]:
        """
        Recursively evaluates if the remaining_chord_sequence is satisfied starting
        from current_state_in_path under current_tonality.

        Implements the logic from Definition 5 of Aragão, considering
        Equations 3, 4, and 5.

        Args:
            current_tonality: The current tonality (L) being used for evaluation.
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

        # Protection against excessive recursion
        if recursion_depth > MAX_RECURSION_DEPTH:
            explanation_failure = partial_explanation.clone()
            explanation_failure.add_step(
                formal_rule_applied="Recursion Limit",
                observation=f"Exceeded maximum recursion depth ({MAX_RECURSION_DEPTH}).",
                evaluated_functional_state=current_state_in_path,
                tonality_used_in_step=current_tonality
            )
            return False, explanation_failure

        # BASE CASE 1: Empty chord sequence (Aragão's Def. 5 implies satisfaction if sequence is fully read)
        # If there are no more chords to verify, the sequence up to this point was satisfied.
        if not remaining_chord_sequence:
            # This base case is typically hit when a previous call successfully processed its chord
            # and called recursively with an empty phi_sub_sequence.
            # The explanation step for the *last actual chord* would have been added by the caller.
            # However, adding a "fully consumed" step can be useful for clarity.
            current_explanation = partial_explanation.clone() # Clone to avoid modifying parent's branch if this is part of a larger success
            current_explanation.add_step(
                formal_rule_applied="Base (Empty Seq)",
                observation="Chord sequence fully consumed successfully.",
                evaluated_functional_state=current_state_in_path, # State where the consumption finished
                tonality_used_in_step=current_tonality
            )
            return True, current_explanation

        current_chord: Chord = remaining_chord_sequence        # P
        phi_sub_sequence: List[Chord] = remaining_chord_sequence[1:] # φ (can be empty)

        # Check if P ∈ L(π_k)
        p_satisfied_in_L: bool = current_tonality.chord_fulfills_function(
            current_chord,
            current_state_in_path.associated_tonal_function
        )

        # --- ATTEMPT 1: Try to satisfy P in current_tonality (L) and then φ in current_tonality (L) ---
        # This corresponds to K,L |=π_k P and then K,L |=π_k+1,n φ (part of Eq. 4/5)
        if p_satisfied_in_L:
            # BASE CASE 2: P ∈ L(π_k) and φ is empty (P is the last chord).
            # This corresponds to Aragão's Eq. 3: K,L |=π P <=> P ∈ L(π_0)
            # (where current_state_in_path is π_0 for this P)
            if not phi_sub_sequence:
                explanation_eq3_L = partial_explanation.clone()
                explanation_eq3_L.add_step(
                    formal_rule_applied="Eq.3 (L)",
                    observation=(
                        f"Chord '{current_chord.name}' fulfills function "
                        f"'{current_state_in_path.associated_tonal_function.to_string()}' "
                        f"in tonality '{current_tonality.tonality_name}'. End of sequence."
                    ),
                    evaluated_functional_state=current_state_in_path,
                    processed_chord=current_chord,
                    tonality_used_in_step=current_tonality
                )
                return True, explanation_eq3_L

            # RECURSIVE CASE: P ∈ L(π_k) and φ is not empty.
            # Try to satisfy φ by continuing with the same tonality L, moving to successor states.
            # K,L |=π_k+1,n φ (from Eq. 4 or Eq. 5)
            successors = self.kripke_config.get_successors_of_state(current_state_in_path)
            if not successors: # No way to continue the path for φ
                 explanation_no_succ_L = partial_explanation.clone()
                 explanation_no_succ_L.add_step(
                    formal_rule_applied="Attempt L (No Succ)",
                    observation=(
                        f"Chord '{current_chord.name}' fulfills function in tonality '{current_tonality.tonality_name}', "
                        f"but no successor states from '{current_state_in_path.state_id}' to satisfy remaining sequence."
                    ),
                    evaluated_functional_state=current_state_in_path,
                    processed_chord=current_chord,
                    tonality_used_in_step=current_tonality
                )
                # Do not return False yet, ATTEMPT 2 (L') might still work.
            else:
                for next_possible_state in successors:
                    explanation_for_L_branch = partial_explanation.clone()
                    explanation_for_L_branch.add_step(
                        formal_rule_applied="Eq.4/5 (P in L, try φ in L)",
                        observation=(
                            f"Chord '{current_chord.name}' fulfills function "
                            f"'{current_state_in_path.associated_tonal_function.to_string()}' "
                            f"in tonality '{current_tonality.tonality_name}'. Trying next state '{next_possible_state.state_id}' "
                            f"for remaining sequence."
                        ),
                        evaluated_functional_state=current_state_in_path,
                        processed_chord=current_chord,
                        tonality_used_in_step=current_tonality
                    )

                    success_recursive_L, explanation_recursive_L = self.evaluate_satisfaction_recursive(
                        current_tonality=current_tonality,             # Continue with L
                        current_state_in_path=next_possible_state,  # π_k+1
                        remaining_chord_sequence=phi_sub_sequence, # φ
                        recursion_depth=recursion_depth + 1,
                        partial_explanation=explanation_for_L_branch
                    )
                    if success_recursive_L:
                        return True, explanation_recursive_L # Found a satisfaction path with L

        # --- ATTEMPT 2: Try to satisfy P in an alternative_tonality (L') and then φ in L' ---
        # This corresponds to Aragão's Eq. 5: K,L'|=π_0' P AND K,L'|=π_1,n' φ
        # This attempt is made if ATTEMPT 1 failed for φ, or if P was not satisfied in L initially.
        for alternative_tonality in self.all_available_tonalitys:
            if alternative_tonality.tonality_name == current_tonality.tonality_name:
                # If p_satisfied_in_L was true, we've already tried this tonality for P and its φ continuation.
                # If p_satisfied_in_L was false, then trying current_tonality again here is redundant.
                continue

            # Check if P ∈ L'(π_k)
            p_satisfied_in_L_prime: bool = alternative_tonality.chord_fulfills_function(
                current_chord,
                current_state_in_path.associated_tonal_function
            )

            if p_satisfied_in_L_prime:
                # BASE CASE (with L'): P ∈ L'(π_k) and φ is empty. (Eq. 3 for L')
                if not phi_sub_sequence:
                    explanation_eq3_L_prime = partial_explanation.clone()
                    explanation_eq3_L_prime.add_step(
                        formal_rule_applied="Eq.3 (L')",
                        observation=(
                            f"Chord '{current_chord.name}' fulfills function "
                            f"'{current_state_in_path.associated_tonal_function.to_string()}' "
                            f"in tonality '{alternative_tonality.tonality_name}' (tonality change from '{current_tonality.tonality_name}'). End of sequence."
                        ),
                        evaluated_functional_state=current_state_in_path,
                        processed_chord=current_chord,
                        tonality_used_in_step=alternative_tonality
                    )
                    return True, explanation_eq3_L_prime

                # RECURSIVE CASE (with L'): P ∈ L'(π_k) and φ is not empty.
                # Try to satisfy K,L' |=π_k+1,n' φ
                successors_L_prime = self.kripke_config.get_successors_of_state(current_state_in_path)
                if not successors_L_prime:
                    explanation_no_succ_L_prime = partial_explanation.clone()
                    explanation_no_succ_L_prime.add_step(
                        formal_rule_applied="Attempt L' (No Succ)",
                        observation=(
                            f"Chord '{current_chord.name}' fulfills function in tonality '{alternative_tonality.tonality_name}', "
                            f"but no successor states from '{current_state_in_path.state_id}' to satisfy remaining sequence in L'."
                        ),
                        evaluated_functional_state=current_state_in_path,
                        processed_chord=current_chord,
                        tonality_used_in_step=alternative_tonality
                    )
                    # Continue to the next alternative_tonality if this one has no successors for phi
                else:
                    for next_possible_state_L_prime in successors_L_prime:
                        explanation_for_L_prime_branch = partial_explanation.clone()
                        explanation_for_L_prime_branch.add_step(
                            formal_rule_applied="Eq.5 (P in L', try φ in L')",
                            observation=(
                                f"Chord '{current_chord.name}' fulfills function "
                                f"'{current_state_in_path.associated_tonal_function.to_string()}' "
                                f"in tonality '{alternative_tonality.tonality_name}' (tonality change from '{current_tonality.tonality_name}'). "
                                f"Trying next state '{next_possible_state_L_prime.state_id}' for remaining sequence."
                            ),
                            evaluated_functional_state=current_state_in_path,
                            processed_chord=current_chord,
                            tonality_used_in_step=alternative_tonality
                        )

                        success_recursive_L_prime, explanation_recursive_L_prime = self.evaluate_satisfaction_recursive(
                            current_tonality=alternative_tonality,         # Continue with L'
                            current_state_in_path=next_possible_state_L_prime,  # π_k+1
                            remaining_chord_sequence=phi_sub_sequence,        # φ
                            recursion_depth=recursion_depth + 1,
                            partial_explanation=explanation_for_L_prime_branch
                        )
                        if success_recursive_L_prime:
                            return True, explanation_recursive_L_prime # Found a satisfaction path with L'
        
        # If none of the attempts (with L or any L') led to a solution for current_chord and phi_sub_sequence
        # from current_state_in_path.
        # Add a failure step for the current_chord at this specific state and tonality combination.
        # This helps trace why a particular branch failed.
        final_branch_explanation = partial_explanation.clone()
        final_branch_explanation.add_step(
            formal_rule_applied="Branch Failure",
            observation=(
                f"Chord '{current_chord.name}' could not be satisfied from state "
                f"'{current_state_in_path.state_id}' ({current_state_in_path.associated_tonal_function.to_string()}) "
                f"with current tonality '{current_tonality.tonality_name}' or via any alternative tonality L' for this branch."
            ),
            evaluated_functional_state=current_state_in_path,
            processed_chord=current_chord,
            tonality_used_in_step=current_tonality # The tonality under which this branch ultimately failed for P
        )
        return False, final_branch_explanation