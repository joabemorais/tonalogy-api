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
