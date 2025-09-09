"""
Service for formatting technical explanations into human-readable narratives.
This service transforms the formal analytical steps into more accessible language.
"""

from typing import List, Optional, Dict, Tuple
from api.schemas.analysis_schemas import ExplanationStepAPI, ProgressionAnalysisResponse
from core.i18n import T, translate_tonality
from core.i18n.locale_manager import locale_manager


class ExplanationFormatter:
    """
    Formats technical harmonic analysis explanations into human-readable narratives.
    """

    def __init__(self):
        self._chord_sequence_cache: Optional[List[str]] = None
        self._main_tonality_cache: Optional[str] = None

    def format_explanation(self, analysis: ProgressionAnalysisResponse, original_chords: Optional[List[str]] = None) -> str:
        """
        Convert a technical explanation into a human-readable narrative.
        
        Args:
            analysis: The progression analysis response containing technical steps
            original_chords: The original chord sequence as provided by the user
            
        Returns:
            A formatted, human-readable explanation string
        """
        if not analysis.explanation_details:
            return T("explanation.formatter.no_steps_available")

        # Cache the chord sequence and main tonality for reference
        # Extract basic progression information
        self._extract_progression_info(analysis, original_chords)
        
        # Build the narrative sections
        sections = []
        
        # Introduction
        intro = self._build_introduction(analysis)
        if intro:
            sections.append(intro)
        
        # Main analysis narrative
        main_narrative = self._build_main_narrative(analysis.explanation_details)
        if main_narrative:
            sections.append(main_narrative)
        
        # Conclusion
        conclusion = self._build_conclusion(analysis)
        if conclusion:
            sections.append(conclusion)
        
        return "\n\n".join(sections)

    def _extract_progression_info(self, analysis: ProgressionAnalysisResponse, original_chords: Optional[List[str]] = None) -> None:
        """Extract and cache basic information about the progression."""
        # Use original chord order if provided, otherwise extract from steps
        if original_chords:
            self._chord_sequence_cache = original_chords
        else:
            # Extract chord sequence maintaining original order (including duplicates)
            chord_sequence = []
            for step in analysis.explanation_details:
                if step.processed_chord:
                    chord_sequence.append(step.processed_chord)
            self._chord_sequence_cache = chord_sequence
        
        self._main_tonality_cache = analysis.identified_tonality

    def _build_introduction(self, analysis: ProgressionAnalysisResponse) -> str:
        """Build an introductory paragraph explaining what will be analyzed."""
        if not self._chord_sequence_cache:
            return ""
        
        chord_list = " → ".join(self._chord_sequence_cache)
        
        if analysis.is_tonal_progression and self._main_tonality_cache:
            return T(
                "explanation.formatter.intro_tonal",
                chord_sequence=chord_list,
                tonality=self._main_tonality_cache
            )
        else:
            return T(
                "explanation.formatter.intro_non_tonal",
                chord_sequence=chord_list
            )

    def _build_main_narrative(self, steps: List[ExplanationStepAPI]) -> str:
        """Build the main narrative describing the harmonic progression."""
        narrative_parts = []
        
        # Group steps by logical sections
        functional_steps = [s for s in steps if s.processed_chord and s.evaluated_functional_state]
        pivot_steps = [s for s in steps if s.rule_type == "pivot_modulation"]
        
        if functional_steps:
            # Describe functional progression
            functional_narrative = self._describe_functional_progression(functional_steps)
            if functional_narrative:
                narrative_parts.append(functional_narrative)
        
        if pivot_steps:
            # Describe modulations
            modulation_narrative = self._describe_modulations(pivot_steps)
            if modulation_narrative:
                narrative_parts.append(modulation_narrative)
        
        return " ".join(narrative_parts)

    def _describe_functional_progression(self, steps: List[ExplanationStepAPI]) -> str:
        """Describe the functional harmonic progression in narrative form."""
        if not steps or not self._chord_sequence_cache:
            return ""
        
        # Create mappings of chord -> function and chord -> tonality
        chord_to_function = {}
        chord_to_tonality = {}
        current_tonality = None
        
        for step in steps:
            if step.processed_chord and step.evaluated_functional_state:
                function = step.evaluated_functional_state.split(" ")[0]  # Extract function name
                chord_to_function[step.processed_chord] = function
                chord_to_tonality[step.processed_chord] = step.tonality_used_in_step or current_tonality
                if step.tonality_used_in_step:
                    current_tonality = step.tonality_used_in_step
        
        # Build the functional sequence using the original chord order
        chord_functions = []
        for chord in self._chord_sequence_cache:
            if chord in chord_to_function:
                tonality = chord_to_tonality[chord]
                chord_functions.append((chord, chord_to_function[chord], tonality))
        
        if not chord_functions:
            return ""
        
        # Check for tonicizations and secondary dominants
        tonicization_info = self._analyze_tonicizations(chord_functions)
        
        # Build the main functional description
        main_description = self._build_functional_description(chord_functions, current_tonality or "unknown")
        
        # Add tonicization explanations
        if tonicization_info:
            return f"{main_description} {tonicization_info}"
        else:
            return main_description

    def _analyze_tonicizations(self, chord_functions: List[Tuple[str, str, str]]) -> str:
        """Analyze and describe tonicizations and secondary dominants."""
        tonicizations = []
        main_tonality = self._main_tonality_cache
        
        # Create a map for easier lookup
        chord_info = {chord: (function, tonality) for chord, function, tonality in chord_functions}
        
        # Go through the original chord order to check for secondary dominants
        for i, chord in enumerate(self._chord_sequence_cache):
            if chord not in chord_info:
                continue
                
            function, tonality = chord_info[chord]
            
            # Check if this chord is functioning as a dominant in a different tonality
            if tonality != main_tonality and function == "DOMINANT":
                # Look for the target chord (what this dominant resolves to)
                target_chord = None
                target_tonality = tonality
                
                # Check the next chord in the original order
                if i + 1 < len(self._chord_sequence_cache):
                    next_chord = self._chord_sequence_cache[i + 1]
                    if next_chord in chord_info:
                        next_function, next_tonality = chord_info[next_chord]
                        
                        # Check for V/V pattern specifically (dominant of dominant)
                        if next_function == "DOMINANT" and next_tonality == main_tonality:
                            tonicizations.append(T(
                                "explanation.formatter.dominant_of_dominant",
                                secondary_dominant=chord,
                                primary_dominant=next_chord,
                                main_tonality=main_tonality
                            ))
                        # Check if the next chord can be the target of this tonicization
                        elif (next_tonality == tonality and next_function in ["TONIC", "SUBDOMINANT"]) or \
                           (next_tonality == main_tonality and next_function == "SUBDOMINANT"):
                            target_chord = next_chord
                            tonicizations.append(T(
                                "explanation.formatter.secondary_dominant",
                                dominant_chord=chord,
                                target_chord=target_chord,
                                target_tonality=target_tonality,
                                main_tonality=main_tonality
                            ))
        
        if tonicizations:
            return " ".join(tonicizations)
        return ""

    def _build_functional_description(self, chord_functions: List[Tuple[str, str, str]], main_tonality: str) -> str:
        """Build the main functional description, grouping by primary tonality."""
        # Filter chords that belong to the main tonality for the main description
        main_tonality_chords = [(chord, func) for chord, func, tonality in chord_functions 
                               if tonality == main_tonality or tonality is None]
        
        if len(main_tonality_chords) == 1:
            chord, function = main_tonality_chords[0]
            return T(
                "explanation.formatter.single_function",
                chord=chord,
                function=function.lower(),
                tonality=main_tonality
            )
        else:
            # Use the existing pattern identification system
            return self._identify_progression_patterns(main_tonality_chords, main_tonality)

    def _connect_descriptions_with_transitions(self, descriptions: List[str]) -> str:
        """Connect multiple tonality descriptions with smooth transitions."""
        if len(descriptions) <= 1:
            return " ".join(descriptions)
        
        # Use different connectors for a more natural flow
        connectors = [
            T("explanation.formatter.transition_then"),
            T("explanation.formatter.transition_afterwards"), 
            T("explanation.formatter.transition_subsequently")
        ]
        
        result = descriptions[0]
        for i, desc in enumerate(descriptions[1:]):
            connector_idx = min(i, len(connectors) - 1)
            result += f" {connectors[connector_idx]} {desc}"
        
        return result

    def _group_by_tonality(self, steps: List[ExplanationStepAPI]) -> List[Tuple[str, List[Tuple[str, str]]]]:
        """Group steps by their tonality, maintaining order."""
        groups = []
        current_tonality = None
        current_group = []
        
        for step in steps:
            tonality = step.tonality_used_in_step
            if tonality != current_tonality:
                if current_group:
                    groups.append((current_tonality, current_group))
                current_tonality = tonality
                current_group = []
            
            if step.processed_chord and step.evaluated_functional_state:
                function = step.evaluated_functional_state.split(" ")[0]  # Extract function name
                current_group.append((step.processed_chord, function))
        
        if current_group:
            groups.append((current_tonality, current_group))
        
        return groups

    def _describe_function_sequence(self, chord_functions: List[Tuple[str, str]], tonality: str) -> str:
        """Describe a sequence of functional chords in a given tonality."""
        if len(chord_functions) <= 2:
            # Simple progression
            chord_list = [f"{chord} ({func.lower()})" for chord, func in chord_functions]
            return T(
                "explanation.formatter.simple_progression",
                chord_sequence=" → ".join(chord_list),
                tonality=tonality
            )
        else:
            # Complex progression - map functions to original chord order
            return self._describe_with_original_order(chord_functions, tonality)

    def _describe_with_original_order(self, chord_functions: List[Tuple[str, str]], tonality: str) -> str:
        """Describe progression using the original chord order."""
        if not self._chord_sequence_cache:
            return self._identify_progression_patterns(chord_functions, tonality)
        
        # Create a mapping of chord to function
        chord_to_function = {chord: func for chord, func in chord_functions}
        
        # Build the sequence using original order
        ordered_sequence = []
        
        for chord in self._chord_sequence_cache:
            if chord in chord_to_function:
                func = chord_to_function[chord]
                ordered_sequence.append((chord, func))
        
        # Use the new pattern identification system
        return self._identify_progression_patterns(ordered_sequence, tonality)

    def _identify_progression_patterns(self, chord_functions: List[Tuple[str, str]], tonality: str) -> str:
        """Identify and describe common harmonic patterns including all types of cadences."""
        if len(chord_functions) < 2:
            chord_sequence = " → ".join([f"{c} ({f.lower()})" for c, f in chord_functions])
            return T(
                "explanation.formatter.functional_progression",
                tonality=tonality,
                chord_sequence=chord_sequence
            )
        
        # Identify all cadences in the progression
        cadences_description = self._identify_all_cadences(chord_functions)
        chord_sequence = " → ".join([f"{c} ({f.lower()})" for c, f in chord_functions])
        
        if cadences_description:
            return T(
                "explanation.formatter.progression_with_cadences",
                tonality=tonality,
                chord_sequence=chord_sequence,
                cadences_description=cadences_description
            )
        else:
            # Generic functional progression without specific cadences
            return T(
                "explanation.formatter.functional_progression",
                tonality=tonality,
                chord_sequence=chord_sequence
            )

    def _identify_all_cadences(self, chord_functions: List[Tuple[str, str]]) -> str:
        """Identify all types of cadences throughout the progression."""
        if len(chord_functions) < 2:
            return ""
        
        functions = [func for _, func in chord_functions]
        chords = [chord for chord, _ in chord_functions]
        cadences = []
        
        # Check each pair of consecutive chords for cadential motion
        for i in range(len(functions) - 1):
            first_func = functions[i]
            second_func = functions[i + 1]
            first_chord = chords[i]
            second_chord = chords[i + 1]
            
            # Perfect cadence: Dominant → Tonic
            if first_func == "DOMINANT" and second_func == "TONIC":
                cadences.append(T(
                    "explanation.formatter.perfect_cadence_location",
                    first_chord=first_chord,
                    second_chord=second_chord
                ))
            
            # Plagal cadence: Subdominant → Tonic
            elif first_func == "SUBDOMINANT" and second_func == "TONIC":
                cadences.append(T(
                    "explanation.formatter.plagal_cadence_location",
                    first_chord=first_chord,
                    second_chord=second_chord
                ))
            
            # Half cadence: Subdominant → Dominant (or any chord → Dominant at phrase end)
            elif second_func == "DOMINANT" and i == len(functions) - 2:
                # Half cadence at the end of progression
                cadences.append(T(
                    "explanation.formatter.half_cadence_location",
                    first_chord=first_chord,
                    second_chord=second_chord
                ))
            elif first_func == "SUBDOMINANT" and second_func == "DOMINANT":
                # Half cadence in middle of progression
                cadences.append(T(
                    "explanation.formatter.half_cadence_location",
                    first_chord=first_chord,
                    second_chord=second_chord
                ))
        
        if cadences:
            # Connect multiple cadences with proper grammar
            if len(cadences) == 1:
                return cadences[0]
            elif len(cadences) == 2:
                return T("explanation.formatter.two_cadences", first=cadences[0], second=cadences[1])
            else:
                # Multiple cadences: use commas and "and" for the last one
                return T("explanation.formatter.multiple_cadences", cadences_list=", ".join(cadences[:-1]), last_cadence=cadences[-1])
        
        return ""

    def _describe_modulations(self, pivot_steps: List[ExplanationStepAPI]) -> str:
        """Describe pivot modulations in narrative form."""
        if not pivot_steps:
            return ""
        
        descriptions = []
        for step in pivot_steps:
            if step.pivot_target_tonality and step.processed_chord:
                # Translate the target tonality to the current locale
                translated_target = translate_tonality(step.pivot_target_tonality, locale_manager.current_locale)
                translated_current = translate_tonality(step.tonality_used_in_step, locale_manager.current_locale) if step.tonality_used_in_step else "unknown"
                
                descriptions.append(T(
                    "explanation.formatter.pivot_modulation",
                    pivot_chord=step.processed_chord,
                    current_tonality=translated_current,
                    target_tonality=translated_target
                ))
        
        return " ".join(descriptions)

    def _build_conclusion(self, analysis: ProgressionAnalysisResponse) -> str:
        """Build a concluding statement about the analysis."""
        if analysis.is_tonal_progression and self._main_tonality_cache:
            # Check if there are tonicizations to mention in conclusion
            has_tonicizations = self._has_secondary_functions(analysis.explanation_details)
            
            if has_tonicizations:
                return T(
                    "explanation.formatter.conclusion_tonal_with_tonicizations",
                    tonality=self._main_tonality_cache
                )
            else:
                return T(
                    "explanation.formatter.conclusion_tonal",
                    tonality=self._main_tonality_cache
                )
        else:
            return T("explanation.formatter.conclusion_non_tonal")

    def _has_secondary_functions(self, steps: List[ExplanationStepAPI]) -> bool:
        """Check if the progression contains secondary functions (tonicizations)."""
        main_tonality = self._main_tonality_cache
        
        for step in steps:
            if (step.processed_chord and step.tonality_used_in_step and 
                step.tonality_used_in_step != main_tonality):
                return True
        return False
