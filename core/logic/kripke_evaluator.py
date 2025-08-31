from typing import Dict, List, Optional, Tuple

# Import the domain models we created previously
from core.domain.models import (
    Chord,
    Explanation,
    KripkePath,
    KripkeState,
    KripkeStructureConfig,
    TonalFunction,
    Tonality,
)
from core.i18n import T, translate_function, translate_tonality
from core.i18n.locale_manager import locale_manager

# A constant to prevent infinite recursion in edge cases or complex progressions.
MAX_RECURSION_DEPTH = 25


class SatisfactionEvaluator:
    """
    Implements the recursive satisfaction logic from Aragão's 5th Definition.

    This class uses a backtracking algorithm to search for a valid analytical path
    through the state space of possible harmonic interpretations. It explores hypotheses
    incrementally and backtracks when a path leads to a dead end.
    """

    def __init__(
        self,
        kripke_config: KripkeStructureConfig,
        all_available_tonalities: List[Tonality],
        original_tonality: Tonality,
    ) -> None:
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
        # Cache for memoization to store results of subproblems and avoid re-computation.
        self.cache: Dict[Tuple, Tuple[bool, Explanation, Optional[KripkePath]]] = {}

    def _get_possible_continuations(
        self, p_chord: Chord, current_path: KripkePath, parent_explanation: Explanation
    ) -> List[Tuple[KripkePath, Explanation]]:
        """
        Generates a list of all possible valid paths and explanations for a direct continuation.
        This corresponds to the first part of the disjunction in Aragão's Equation 4.
        """
        continuations = []
        current_state = current_path.get_current_state()
        current_tonality = current_path.get_current_tonality()

        if not current_tonality or not current_state:
            return []

        # Check if the current chord (P) fulfills the function of the current state.
        if current_tonality.chord_fulfills_function(
            p_chord, current_state.associated_tonal_function
        ):
            explanation_for_P = parent_explanation.clone()
            explanation_for_P.add_step(
                formal_rule_applied=T("analysis.rules.p_in_l"),
                observation=T(
                    "analysis.messages.chord_fulfills_function",
                    chord_name=p_chord.name,
                    function_name=translate_function(
                        current_state.associated_tonal_function.name, locale_manager.current_locale
                    ),
                    tonality_name=translate_tonality(
                        current_tonality.tonality_name, locale_manager.current_locale
                    ),
                ),
                evaluated_functional_state=current_state,
                processed_chord=p_chord,
                tonality_used_in_step=current_tonality,
            )
            # If it fits, generate a new potential path for each successor state.
            for next_state in self.kripke_config.get_successors_of_state(current_state):
                path_copy = current_path.clone()
                path_copy.add_step(
                    next_state,
                    current_tonality,
                    T(
                        "analysis.rules.direct_transition",
                        function=translate_function(
                            next_state.associated_tonal_function.name, locale_manager.current_locale
                        ),
                    ),
                )
                continuations.append((path_copy, explanation_for_P.clone()))

        # ADDITIONAL: Also check if the chord can fulfill any function in directly accessible states
        # This handles cases like s_d -> s_sd where the chord is SUBDOMINANT (not DOMINANT)
        successor_states = self.kripke_config.get_successors_of_state(current_state)
        for next_state in successor_states:
            # Skip if we already handled this through the current state logic above
            if current_tonality.chord_fulfills_function(
                p_chord, current_state.associated_tonal_function
            ):
                continue

            # Check if the chord fulfills the function required by this successor state
            if current_tonality.chord_fulfills_function(
                p_chord, next_state.associated_tonal_function
            ):
                explanation_for_P = parent_explanation.clone()
                explanation_for_P.add_step(
                    formal_rule_applied=T("analysis.rules.p_in_l"),
                    observation=T(
                        "analysis.messages.chord_fulfills_function",
                        chord_name=p_chord.name,
                        function_name=translate_function(
                            next_state.associated_tonal_function.name, locale_manager.current_locale
                        ),
                        tonality_name=translate_tonality(
                            current_tonality.tonality_name, locale_manager.current_locale
                        ),
                    ),
                    evaluated_functional_state=next_state,
                    processed_chord=p_chord,
                    tonality_used_in_step=current_tonality,
                )
                # Create path with transition to this state
                path_copy = current_path.clone()
                path_copy.add_step(
                    next_state,
                    current_tonality,
                    T(
                        "analysis.rules.direct_transition",
                        function=translate_function(
                            next_state.associated_tonal_function.name, locale_manager.current_locale
                        ),
                    ),
                )
                continuations.append((path_copy, explanation_for_P.clone()))

        return continuations

    def _get_possible_pivots(
        self,
        p_chord: Chord,
        phi_sub_sequence: List[Chord],
        current_path: KripkePath,
        parent_explanation: Explanation,
    ) -> List[Tuple[KripkePath, Explanation]]:
        """
        Generates a list of all possible valid paths and explanations for pivot modulations.
        This corresponds to Aragão's Equation 5.
        """
        pivots = []
        current_state = current_path.get_current_state()
        current_tonality = current_path.get_current_tonality()
        new_tonic_state = self.kripke_config.get_state_by_tonal_function(TonalFunction.TONIC)

        if not current_tonality or not current_state or not new_tonic_state:
            return []

        # --- FIX START ---
        # The list of tonalities to check for pivots must be comprehensive, but prioritized.
        # We start with the ranked tonalities (if provided) and then add all others to ensure completeness.
        tonalities_to_check: List[Tonality] = []
        seen_tonalities = set()

        # First, add the prioritized tonalities from the heuristic
        if hasattr(self, "ranked_tonalities"):
            for tonality in self.ranked_tonalities:
                if tonality.tonality_name not in seen_tonalities:
                    tonalities_to_check.append(tonality)
                    seen_tonalities.add(tonality.tonality_name)

        # Then, add any remaining tonalities to ensure the search is exhaustive
        for tonality in self.all_available_tonalities:
            if tonality.tonality_name not in seen_tonalities:
                tonalities_to_check.append(tonality)
                seen_tonalities.add(tonality.tonality_name)
        # --- FIX END ---

        for l_prime_tonality in tonalities_to_check:
            if l_prime_tonality.tonality_name == current_tonality.tonality_name:
                continue

            # Check if the current chord can function as a tonic in the new tonality (L').
            p_is_tonic_in_L_prime = l_prime_tonality.chord_fulfills_function(
                p_chord, TonalFunction.TONIC
            )
            if not p_is_tonic_in_L_prime:
                continue

            # A pivot is stronger if it also has a function in the original tonality...
            p_functions_in_L = [
                func
                for func in TonalFunction
                if current_tonality.chord_fulfills_function(p_chord, func)
            ]

            # ...or if the modulation is reinforced by the next chord (which should be the dominant of L').
            tonicization_reinforced = False
            if phi_sub_sequence:
                next_chord = phi_sub_sequence[0]
                if l_prime_tonality.chord_fulfills_function(next_chord, TonalFunction.DOMINANT):
                    tonicization_reinforced = True

            pivot_valid = p_is_tonic_in_L_prime and (
                bool(p_functions_in_L) or tonicization_reinforced
            )

            if pivot_valid:
                explanation_for_pivot = parent_explanation.clone()
                functions_str = (
                    ", ".join([f.name for f in p_functions_in_L])
                    if p_functions_in_L
                    else "a transitional role"
                )
                explanation_for_pivot.add_step(
                    formal_rule_applied=T("analysis.rules.pivot_modulation"),
                    observation=(
                        f"Chord '{p_chord.name}' acts as pivot. It has function '{functions_str}' in '{current_tonality.tonality_name}' "
                        f"and becomes the new TONIC in '{l_prime_tonality.tonality_name}'. "
                        f"(Reinforced by next chord: {tonicization_reinforced})"
                    ),
                    evaluated_functional_state=current_state,
                    processed_chord=p_chord,
                    tonality_used_in_step=current_tonality,
                )
                # Generate a new potential path for each successor of the new tonic state.
                for next_state in self.kripke_config.get_successors_of_state(new_tonic_state):
                    path_copy = current_path.clone()
                    path_copy.add_step(
                        next_state,
                        l_prime_tonality,
                        T(
                            "analysis.rules.transition_to",
                            function=translate_function(
                                next_state.associated_tonal_function.name,
                                locale_manager.current_locale,
                            ),
                            tonality=translate_tonality(
                                l_prime_tonality.tonality_name, locale_manager.current_locale
                            ),
                        ),
                    )
                    pivots.append((path_copy, explanation_for_pivot.clone()))

        return pivots

    def _try_reanchor(
        self, remaining_chords: List[Chord], parent_explanation: Explanation, recursion_depth: int
    ) -> Tuple[bool, Explanation, Optional[KripkePath]]:
        """
        Attempts to satisfy the remaining sequence as a completely new problem.
        This is the "safety net" of the algorithm, corresponding to the second part
        of the disjunction in Aragão's Equation 4 (K,L ⊧π' φ).
        """
        explanation_before_reanchor = parent_explanation.clone()
        explanation_before_reanchor.add_step(
            formal_rule_applied=T("analysis.rules.reanchor_attempt"),
            observation=T(
                "analysis.messages.reanchor_attempt_observation",
                remaining_chords=[c.name for c in remaining_chords],
            ),
        )

        tonalities_to_try = [self.original_tonality] + [
            k
            for k in self.all_available_tonalities
            if k.tonality_name != self.original_tonality.tonality_name
        ]
        tonic_start_state = self.kripke_config.get_state_by_tonal_function(TonalFunction.TONIC)

        if not tonic_start_state:
            return False, parent_explanation, None

        for l_star_tonality in tonalities_to_try:
            reanchor_path = KripkePath()
            reanchor_path.add_step(
                tonic_start_state,
                l_star_tonality,
                T(
                    "analysis.rules.reanchoring_in",
                    tonality=translate_tonality(
                        l_star_tonality.tonality_name, locale_manager.current_locale
                    ),
                ),
            )

            # Recursive call to solve the subproblem.
            success, final_explanation, final_path = self.evaluate_satisfaction_with_path(
                reanchor_path, remaining_chords, recursion_depth + 1, explanation_before_reanchor
            )
            if success:
                return True, final_explanation, final_path

        return False, parent_explanation, None

    def evaluate_satisfaction_with_path(
        self,
        current_path: KripkePath,
        remaining_chords: List[Chord],
        recursion_depth: int,
        parent_explanation: Explanation,
    ) -> Tuple[bool, Explanation, Optional[KripkePath]]:
        """
        The main backtracking engine. It orchestrates the search for a valid solution.
        """
        # --- Memoization ---
        current_tonality_obj = current_path.get_current_tonality()
        cache_key = (
            current_path.get_current_state(),
            current_tonality_obj.tonality_name if current_tonality_obj else None,
            tuple(c.name for c in remaining_chords),
        )
        if cache_key in self.cache:
            success, cached_exp, cached_path = self.cache[cache_key]
            return success, cached_exp.clone(), cached_path.clone() if cached_path else None

        # --- Base Cases ---
        if recursion_depth > MAX_RECURSION_DEPTH:
            return False, parent_explanation, None

        if not remaining_chords:
            final_explanation = parent_explanation.clone()
            final_explanation.add_step(
                formal_rule_applied=T("analysis.rules.end_of_sequence"),
                observation=T("analysis.messages.end_of_sequence_observation"),
            )
            return True, final_explanation, current_path

        # --- Recursive Step ---
        p_chord = remaining_chords[0]
        phi_sub_sequence = remaining_chords[1:]

        # STRATEGY 1: Try to extend the current path.
        # First, try direct continuations (higher priority)
        direct_continuations = self._get_possible_continuations(
            p_chord, current_path, parent_explanation
        )

        # Test direct continuations first
        for path_after_p, explanation_for_p in direct_continuations:
            success, final_explanation, final_path = self.evaluate_satisfaction_with_path(
                path_after_p, phi_sub_sequence, recursion_depth + 1, explanation_for_p
            )
            if success:
                self.cache[cache_key] = (True, final_explanation, final_path)
                return True, final_explanation, final_path

        # If no direct continuation worked, try pivots (lower priority)
        pivots = self._get_possible_pivots(
            p_chord, phi_sub_sequence, current_path, parent_explanation
        )

        for path_after_p, explanation_for_p in pivots:
            success, final_explanation, final_path = self.evaluate_satisfaction_with_path(
                path_after_p, phi_sub_sequence, recursion_depth + 1, explanation_for_p
            )
            if success:
                self.cache[cache_key] = (True, final_explanation, final_path)
                return True, final_explanation, final_path

        # STRATEGY 2: If ALL attempts to extend the path failed, try to re-anchor.
        success_reanchor, explanation_reanchor, path_reanchor = self._try_reanchor(
            remaining_chords, parent_explanation, recursion_depth
        )
        if success_reanchor:
            self.cache[cache_key] = (True, explanation_reanchor, path_reanchor)
            return True, explanation_reanchor, path_reanchor

        # If both strategies have failed, this subproblem is unsolvable.
        self.cache[cache_key] = (False, parent_explanation, None)
        return False, parent_explanation, None

    def evaluate_satisfaction_recursive(
        self,
        current_tonality: Tonality,
        current_state: KripkeState,
        remaining_chords: List[Chord],
        recursion_depth: int,
        parent_explanation: Explanation,
        ranked_tonalities: Optional[List[Tonality]] = None,
    ) -> Tuple[bool, Explanation]:
        """
        Wrapper method for backward compatibility. Creates the initial path and calls the main backtracking engine.
        """
        initial_path = KripkePath()
        initial_path.add_step(
            current_state,
            current_tonality,
            f"Starting analysis in {current_tonality.tonality_name}",
        )

        # Pass the ranked tonalities to the evaluator instance for optimization.
        if ranked_tonalities:
            self.ranked_tonalities = ranked_tonalities

        success, explanation, _ = self.evaluate_satisfaction_with_path(
            initial_path, remaining_chords, recursion_depth, parent_explanation
        )

        return success, explanation
