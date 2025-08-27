from typing import List, Tuple, Optional
from core.domain.models import Chord, Tonality, TonalFunction
import logging

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
        self,
        last_chord: Chord,
        tonalities: List[Tonality]
    ) -> List[Tonality]:
        """
        Prioritization filter (hard rule): Returns only the tonalities
        where the last chord of the progression can function as a Tonic.
        """
        return [
            tonality for tonality in tonalities
            if tonality.chord_fulfills_function(last_chord, TonalFunction.TONIC)
        ]

    def _rank_by_fit(
        self,
        progression_chords: List[Chord],
        candidate_tonalities: List[Tonality]
    ) -> List[Tonality]:
        """
        Ranks candidate tonalities based on how well the progression fits them.
        """
        scored_tonalities = []
        for tonality in candidate_tonalities:
            score = sum(1 for chord in progression_chords if self._is_chord_in_tonality(tonality, chord))
            scored_tonalities.append((tonality, score))

        # Simple sort by score
        scored_tonalities.sort(key=lambda item: item[1], reverse=True)

        logger.info(f"Tonality Ranking: {[ (t.tonality_name, s) for t, s in scored_tonalities ]}")

        return [tonality for tonality, score in scored_tonalities]

    def process(
        self,
        progression_chords: List[Chord],
        all_tonalities: List[Tonality]
    ) -> Tuple[List[Tonality], Optional[str]]:
        """
        Orchestrates the candidate selection and ranking process.
        """
        if not progression_chords:
            return [], "The chord progression list is empty."

        last_chord = progression_chords[-1]
        valid_candidates = self._filter_by_final_tonic(last_chord, all_tonalities)

        if not valid_candidates:
            error_msg = f"No candidate tonality found where the final chord '{last_chord.name}' functions as a Tonic."
            return [], error_msg

        ranked_candidates = self._rank_by_fit(progression_chords, valid_candidates)
        return ranked_candidates, None
