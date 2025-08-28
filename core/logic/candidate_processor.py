import logging
from typing import List, Optional, Tuple

from core.domain.models import Chord, TonalFunction, Tonality

logger = logging.getLogger(__name__)


class CandidateProcessor:
    """
    Encapsulates the heuristics for filtering and ranking candidate tonalities
    from a chord progression.
    """

    def _is_chord_in_tonality(self, tonality: Tonality, chord: Chord) -> bool:
        """Checks if a chord belongs to the harmonic field of a tonality."""
        for function in TonalFunction:
            if tonality.chord_fulfills_function(chord, function):
                return True
        return False

    def _filter_by_final_tonic(
        self, last_chord: Chord, tonalities: List[Tonality]
    ) -> List[Tonality]:
        """
        Prioritization filter (hard rule): Returns only the tonalities
        where the last chord of the progression can function as a Tonic.
        """
        return [
            tonality
            for tonality in tonalities
            if tonality.chord_fulfills_function(last_chord, TonalFunction.TONIC)
        ]

    def _rank_by_fit(
        self,
        progression_chords: List[Chord],
        candidate_tonalities: List[Tonality],
        last_chord: Chord,
    ) -> List[Tonality]:
        """
        Ranks candidate tonalities based on how well the progression fits them.
        Criteria:
        1. Score (number of chords that belong to the tonality).
        2. Tie-breaker: Prefers tonality quality (Major/minor) that matches the last chord's quality.
        """
        scored_tonalities = []
        for tonality in candidate_tonalities:
            score = sum(
                1 for chord in progression_chords if self._is_chord_in_tonality(tonality, chord)
            )
            scored_tonalities.append((tonality, score))

        # Determine the preferred quality based on the last chord's quality.
        preferred_quality = last_chord.quality

        # Custom sort key: first by score (desc), then by quality match
        def sort_key(item: Tuple[Tonality, int]) -> Tuple[int, int]:
            tonality, score = item
            # Preference: 0 if tonality quality matches the preferred one, 1 otherwise.
            quality_preference = 0 if tonality.quality == preferred_quality else 1
            return (-score, quality_preference)

        scored_tonalities.sort(key=sort_key)

        logger.info(
            f"Tonality Ranking (preference: {preferred_quality}): {[ (t.tonality_name, s) for t, s in scored_tonalities ]}"
        )

        return [tonality for tonality, score in scored_tonalities]

    def process(
        self, progression_chords: List[Chord], all_tonalities: List[Tonality]
    ) -> Tuple[List[Tonality], Optional[str]]:
        """
        Orchestrates the candidate selection and ranking process.
        """
        if not progression_chords:
            return [], "The chord progression list is empty."

        last_chord = progression_chords[-1]
        valid_candidates = self._filter_by_final_tonic(last_chord, all_tonalities)

        if not valid_candidates:
            # For debugging, we can rank all tonalities to understand why it failed
            all_ranked = self._rank_by_fit(progression_chords, all_tonalities, last_chord)
            logger.warning(
                f"No valid candidates found. Overall ranking: {[t.tonality_name for t in all_ranked]}"
            )
            error_msg = f"No candidate tonality found where the final chord '{last_chord.name}' functions as a Tonic."
            return [], error_msg

        # Pass the last chord to the ranking method for the dynamic tie-breaker
        ranked_candidates = self._rank_by_fit(progression_chords, valid_candidates, last_chord)
        return ranked_candidates, None
