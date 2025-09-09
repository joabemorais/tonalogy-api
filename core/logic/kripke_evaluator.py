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

# Constants to control backtracking behavior and prevent exponential explosion
MAX_RECURSION_DEPTH = 25  # Prevents infinite recursion in complex progressions
MAX_PIVOT_CANDIDATES = 8  # Limits pivot exploration to most promising tonalities
MAX_CONTINUATION_BRANCHES = 6  # Limits direct continuation paths to explore


class SatisfactionEvaluator:
    """
    Implements the recursive satisfaction logic from Aragão's 5th Definition.

    This class uses a sophisticated backtracking algorithm to search for a valid analytical path
    through the state space of possible harmonic interpretations. The algorithm addresses the
    NP-complete nature of Kripke structure navigation through multiple pruning strategies:

    1. **Memoization (Dynamic Programming)**: Caches subproblem results to avoid recomputation
    2. **Depth Limiting**: Prevents infinite recursion with MAX_RECURSION_DEPTH
    3. **Priority Ordering**: Tests direct continuations before pivots before re-anchoring
    4. **Early Termination**: Returns immediately upon finding first valid solution
    5. **Constraint Propagation**: Uses functional and harmonic constraints to prune branches

    The backtracking explores hypotheses incrementally and backtracks when a path leads to
    a dead end, making it suitable for the exponential search space while maintaining efficiency.
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
            ranked = list(self.ranked_tonalities)
            
            # TONICIZATION PRIORITY: Ensure tonalities where the pivot chord is tonic are tested first
            if p_chord:
                # Find tonalities where P is tonic that aren't in ranked
                tonic_tonalities = []
                for tonality in self.all_available_tonalities:
                    if (tonality.chord_fulfills_function(p_chord, TonalFunction.TONIC) and 
                        tonality.tonality_name not in [r.tonality_name for r in ranked]):
                        tonic_tonalities.append(tonality)
                
                # Sort tonic tonalities (major first in major context)
                if current_tonality and current_tonality.quality == "Major":
                    tonic_tonalities.sort(key=lambda t: (t.quality != "Major", t.tonality_name))
                
                # Insert tonic tonalities at the beginning
                ranked = tonic_tonalities + ranked
            
            for tonality in ranked:
                if tonality.tonality_name not in seen_tonalities:
                    tonalities_to_check.append(tonality)
                    seen_tonalities.add(tonality.tonality_name)

        # Then, add any remaining tonalities to ensure the search is exhaustive
        # TONICIZATION PRIORITY: Prioritize tonalities where the pivot chord is actually the tonic
        remaining_tonalities = [t for t in self.all_available_tonalities if t.tonality_name not in seen_tonalities]
        
        # Sort remaining tonalities: put those where P is tonic first
        if p_chord:
            remaining_tonalities.sort(key=lambda t: (
                not t.chord_fulfills_function(p_chord, TonalFunction.TONIC),  # Tonic first
                t.quality != "Major" if current_tonality and current_tonality.quality == "Major" else False,  # Major tonalities first in major context
                t.tonality_name
            ))
        
        for tonality in remaining_tonalities:
            tonalities_to_check.append(tonality)
            seen_tonalities.add(tonality.tonality_name)

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
                    ", ".join(
                        [
                            translate_function(f.name, locale_manager.current_locale)
                            for f in p_functions_in_L
                        ]
                    )
                    if p_functions_in_L
                    else "a transitional role"
                )
                
                # Find the correct state for the pivot chord's function in the current tonality
                pivot_state = None
                if p_functions_in_L:
                    # Use the first (primary) function of the pivot chord in the current tonality
                    primary_function = p_functions_in_L[0]
                    # Find the state that corresponds to this function
                    pivot_state = self.kripke_config.get_state_by_tonal_function(primary_function)
                
                # Fallback to current_state if no specific function state found
                if pivot_state is None:
                    pivot_state = current_state
                
                explanation_for_pivot.add_step(
                    formal_rule_applied=T("analysis.rules.pivot_modulation"),
                    observation=T(
                        "analysis.messages.pivot_chord_observation",
                        chord_name=p_chord.name,
                        functions_str=functions_str,
                        current_tonality=translate_tonality(
                            current_tonality.tonality_name, locale_manager.current_locale
                        ),
                        target_tonality=translate_tonality(
                            l_prime_tonality.tonality_name, locale_manager.current_locale
                        ),
                        reinforcement_status=tonicization_reinforced,
                    ),
                    evaluated_functional_state=pivot_state,
                    processed_chord=p_chord,
                    tonality_used_in_step=current_tonality,
                    pivot_target_tonality=l_prime_tonality,  # Add structured pivot target
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

        BACKTRACKING ALGORITHM STRUCTURE:
        1. **Memoization Check**: Return cached result if subproblem already solved
        2. **Pruning**: Check depth limit and base cases for early termination
        3. **Branch Generation**: Create possible continuations in priority order:
           - Direct continuations (highest priority - most likely to succeed)
           - Pivot modulations (medium priority - handle key changes)
           - Re-anchoring (lowest priority - last resort for complex cases)
        4. **Recursive Exploration**: For each branch, recursively solve remaining subproblem
        5. **Early Success**: Return immediately when first valid path is found
        6. **Backtrack**: If all branches fail, mark this subproblem as unsolvable

        This approach transforms the exponential search space into a manageable exploration
        by systematically pruning unsuccessful branches and caching solved subproblems.
        """
        # --- PRUNING STRATEGY 1: Memoization (Dynamic Programming) ---
        # Check if this exact subproblem (state + tonality + remaining chords) has been solved before
        # This provides exponential speedup for progressions with repeated patterns
        current_tonality_obj = current_path.get_current_tonality()
        cache_key = (
            current_path.get_current_state(),
            current_tonality_obj.tonality_name if current_tonality_obj else None,
            tuple(c.name for c in remaining_chords),
        )
        if cache_key in self.cache:
            success, cached_exp, cached_path = self.cache[cache_key]
            return success, cached_exp.clone(), cached_path.clone() if cached_path else None

        # --- PRUNING STRATEGY 2: Depth Limiting ---
        # Prevent infinite recursion and limit computational complexity
        # 25 levels should be sufficient for even very complex real-world progressions
        if recursion_depth > MAX_RECURSION_DEPTH:
            return False, parent_explanation, None

        # --- PRUNING STRATEGY 3: Base Case (Successful Termination) ---
        # If no more chords to process, we've found a complete valid path
        if not remaining_chords:
            final_explanation = parent_explanation.clone()
            final_explanation.add_step(
                formal_rule_applied=T("analysis.rules.end_of_sequence"),
                observation=T("analysis.messages.end_of_sequence_observation"),
            )
            return True, final_explanation, current_path

        # --- BACKTRACKING: Generate and test branches in priority order ---
        p_chord = remaining_chords[0]
        phi_sub_sequence = remaining_chords[1:]

        # PRIORITY 1: Direct continuations (most likely to succeed)
        # These represent normal functional progressions within the current tonality
        direct_continuations = self._get_possible_continuations(
            p_chord, current_path, parent_explanation
        )

        # Test direct continuations first - early success terminates search
        for path_after_p, explanation_for_p in direct_continuations:
            success, final_explanation, final_path = self.evaluate_satisfaction_with_path(
                path_after_p, phi_sub_sequence, recursion_depth + 1, explanation_for_p
            )
            if success:
                # Cache successful result and return immediately
                self.cache[cache_key] = (True, final_explanation, final_path)
                return True, final_explanation, final_path

        # PRIORITY 2: Pivot modulations (handle key changes)
        # Only try if direct continuations failed - this reduces branching factor
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

        # PRIORITY 3: Re-anchoring (last resort for complex cases)
        # This is the most expensive option, only used when all else fails
        success_reanchor, explanation_reanchor, path_reanchor = self._try_reanchor(
            remaining_chords, parent_explanation, recursion_depth
        )
        if success_reanchor:
            self.cache[cache_key] = (True, explanation_reanchor, path_reanchor)
            return True, explanation_reanchor, path_reanchor

        # BACKTRACK: All strategies failed - cache failure and return
        # This prevents re-exploring this failed subproblem
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
