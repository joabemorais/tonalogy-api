"""
Service for formatting technical explanations into human-readable narratives.
This service transforms the formal analytical steps into more accessible language.
"""

from typing import List, Optional, Dict, Tuple
from api.schemas.analysis_schemas import ExplanationStepAPI, ProgressionAnalysisResponse
from core.i18n import T
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
        
        # Create a mapping of chord -> function from the analysis steps
        chord_to_function = {}
        current_tonality = None
        
        for step in steps:
            if step.processed_chord and step.evaluated_functional_state:
                function = step.evaluated_functional_state.split(" ")[0]  # Extract function name
                chord_to_function[step.processed_chord] = function
                if step.tonality_used_in_step:
                    current_tonality = step.tonality_used_in_step
        
        # Build the functional sequence using the original chord order
        chord_functions = []
        for chord in self._chord_sequence_cache:
            if chord in chord_to_function:
                chord_functions.append((chord, chord_to_function[chord]))
        
        if not chord_functions:
            return ""
        
        # Describe the sequence maintaining original order
        if len(chord_functions) == 1:
            chord, function = chord_functions[0]
            return T(
                "explanation.formatter.single_function",
                chord=chord,
                function=function.lower(),
                tonality=current_tonality or "unknown"
            )
        else:
            # Describe the functional sequence
            return self._describe_function_sequence(chord_functions, current_tonality or "unknown")

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
                descriptions.append(T(
                    "explanation.formatter.pivot_modulation",
                    pivot_chord=step.processed_chord,
                    current_tonality=step.tonality_used_in_step or "unknown",
                    target_tonality=step.pivot_target_tonality
                ))
        
        return " ".join(descriptions)

    def _build_conclusion(self, analysis: ProgressionAnalysisResponse) -> str:
        """Build a concluding statement about the analysis."""
        if analysis.is_tonal_progression and self._main_tonality_cache:
            return T(
                "explanation.formatter.conclusion_tonal",
                tonality=self._main_tonality_cache
            )
        else:
            return T("explanation.formatter.conclusion_non_tonal")
