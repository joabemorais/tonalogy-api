from typing import List, Tuple, Optional, Dict
from core.domain.models import (
    Chord, KripkeState, Tonality, KripkeStructureConfig,
    Explanation, TonalFunction, KripkePath
)

MAX_RECURSION_DEPTH = 25

class SatisfactionEvaluator:
    def __init__(self, kripke_config: KripkeStructureConfig, all_available_tonalities: List[Tonality], original_tonality: Tonality) -> None:
        self.kripke_config: KripkeStructureConfig = kripke_config
        self.all_available_tonalities: List[Tonality] = all_available_tonalities
        self.original_tonality: Tonality = original_tonality
        self.cache: Dict[Tuple, Tuple[bool, Explanation, Optional[KripkePath]]] = {}

    def _get_possible_continuations(
        self,
        p_chord: Chord,
        current_path: KripkePath,
        parent_explanation: Explanation
    ) -> List[Tuple[KripkePath, Explanation]]:
        """
        Gera uma lista de todos os caminhos e explicações possíveis para a continuação direta.
        """
        continuations = []
        current_state = current_path.get_current_state()
        current_tonality = current_path.get_current_tonality()

        if not current_tonality or not current_state:
            return []

        if current_tonality.chord_fulfills_function(p_chord, current_state.associated_tonal_function):
            explanation_for_P = parent_explanation.clone()
            explanation_for_P.add_step(
                formal_rule_applied="P in L",
                observation=f"Acorde '{p_chord.name}' cumpre a função '{current_state.associated_tonal_function.name}' em '{current_tonality.tonality_name}'.",
                evaluated_functional_state=current_state,
                processed_chord=p_chord,
                tonality_used_in_step=current_tonality
            )
            for next_state in self.kripke_config.get_successors_of_state(current_state):
                path_copy = current_path.clone()
                path_copy.add_step(
                    next_state,
                    current_tonality,
                    f"Transição direta para {next_state.associated_tonal_function.name}"
                )
                continuations.append((path_copy, explanation_for_P.clone()))
        
        return continuations

    def _get_possible_pivots(
        self,
        p_chord: Chord,
        phi_sub_sequence: List[Chord],
        current_path: KripkePath,
        parent_explanation: Explanation
    ) -> List[Tuple[KripkePath, Explanation]]:
        """
        Gera uma lista de todos os caminhos e explicações possíveis para modulações por pivô.
        """
        pivots = []
        current_state = current_path.get_current_state()
        current_tonality = current_path.get_current_tonality()
        new_tonic_state = self.kripke_config.get_state_by_tonal_function(TonalFunction.TONIC)

        if not current_tonality or not current_state or not new_tonic_state:
            return []

        tonalities_to_check = self.all_available_tonalities
        if hasattr(self, 'ranked_tonalities'):
             tonalities_to_check = self.ranked_tonalities

        for l_prime_tonality in tonalities_to_check:
            if l_prime_tonality.tonality_name == current_tonality.tonality_name:
                continue

            p_is_tonic_in_L_prime = l_prime_tonality.chord_fulfills_function(p_chord, TonalFunction.TONIC)
            if not p_is_tonic_in_L_prime:
                continue

            p_functions_in_L = [func for func in TonalFunction if current_tonality.chord_fulfills_function(p_chord, func)]
            tonicization_reinforced = False
            if phi_sub_sequence:
                next_chord = phi_sub_sequence[0]
                if l_prime_tonality.chord_fulfills_function(next_chord, TonalFunction.DOMINANT):
                    tonicization_reinforced = True
            
            pivot_valid = p_is_tonic_in_L_prime and (bool(p_functions_in_L) or tonicization_reinforced)
            
            if pivot_valid:
                explanation_for_pivot = parent_explanation.clone()
                functions_str = ", ".join([f.name for f in p_functions_in_L]) if p_functions_in_L else "um papel de transição"
                explanation_for_pivot.add_step(
                    formal_rule_applied="Modulação por Pivô (Eq.5)",
                    observation=(
                        f"Acorde '{p_chord.name}' atua como pivô. Ele tem a função '{functions_str}' em '{current_tonality.tonality_name}' "
                        f"e se torna a nova TÔNICA em '{l_prime_tonality.tonality_name}'. "
                        f"(Reforçado pelo próximo acorde: {tonicization_reinforced})"
                    ),
                    evaluated_functional_state=current_state,
                    processed_chord=p_chord,
                    tonality_used_in_step=current_tonality
                )
                for next_state in self.kripke_config.get_successors_of_state(new_tonic_state):
                    path_copy = current_path.clone()
                    path_copy.add_step(
                        next_state,
                        l_prime_tonality,
                        f"Transição para {next_state.associated_tonal_function.name} em {l_prime_tonality.tonality_name}"
                    )
                    pivots.append((path_copy, explanation_for_pivot.clone()))
        
        return pivots

    def _try_reanchor(
        self,
        remaining_chords: List[Chord],
        parent_explanation: Explanation,
        recursion_depth: int
    ) -> Tuple[bool, Explanation, Optional[KripkePath]]:
        """
        Tenta satisfazer a sequência restante como um novo problema.
        """
        explanation_before_reanchor = parent_explanation.clone()
        explanation_before_reanchor.add_step(
            formal_rule_applied="Tentativa de Reancoragem (Eq.4B)",
            observation=f"Extensão de caminho falhou. Tentando reavaliar a sequência restante '{[c.name for c in remaining_chords]}' a partir de um novo contexto."
        )
        
        tonalities_to_try = [self.original_tonality] + [k for k in self.all_available_tonalities if k.tonality_name != self.original_tonality.tonality_name]
        tonic_start_state = self.kripke_config.get_state_by_tonal_function(TonalFunction.TONIC)

        if not tonic_start_state:
            return False, parent_explanation, None

        for l_star_tonality in tonalities_to_try:
            reanchor_path = KripkePath()
            reanchor_path.add_step(
                tonic_start_state,
                l_star_tonality,
                f"Reancoragem em {l_star_tonality.tonality_name}"
            )
            
            success, final_explanation, final_path = self.evaluate_satisfaction_with_path(
                reanchor_path,
                remaining_chords,
                recursion_depth + 1,
                explanation_before_reanchor
            )
            if success:
                return True, final_explanation, final_path

        return False, parent_explanation, None


    def evaluate_satisfaction_with_path(
        self,
        current_path: KripkePath,
        remaining_chords: List[Chord],
        recursion_depth: int,
        parent_explanation: Explanation
    ) -> Tuple[bool, Explanation, Optional[KripkePath]]:
        """
        Método principal que orquestra a busca por uma solução.
        """
        current_tonality_obj = current_path.get_current_tonality()
        cache_key = (
            current_path.get_current_state(), 
            current_tonality_obj.tonality_name if current_tonality_obj else None, 
            tuple(c.name for c in remaining_chords)
        )
        if cache_key in self.cache:
            return self.cache[cache_key]

        if recursion_depth > MAX_RECURSION_DEPTH:
            return False, parent_explanation, None

        if not remaining_chords:
            final_explanation = parent_explanation.clone()
            final_explanation.add_step(
                formal_rule_applied="Fim da Sequência",
                observation="Fim da sequência. Todos os acordes foram processados com sucesso."
            )
            return True, final_explanation, current_path

        p_chord = remaining_chords[0]
        phi_sub_sequence = remaining_chords[1:]

        # Passo 1: Gerar e testar todas as hipóteses de extensão de caminho (continuações e pivôs)
        possible_continuations = self._get_possible_continuations(p_chord, current_path, parent_explanation)
        possible_pivots = self._get_possible_pivots(p_chord, phi_sub_sequence, current_path, parent_explanation)

        for path, explanation in possible_continuations + possible_pivots:
            success, final_explanation, final_path = self.evaluate_satisfaction_with_path(
                path,
                phi_sub_sequence,
                recursion_depth + 1,
                explanation
            )
            if success:
                self.cache[cache_key] = (True, final_explanation, final_path)
                return True, final_explanation, final_path

        # Passo 2: Se todas as extensões falharam, usar a "rede de segurança" da reancoragem
        success, final_explanation, final_path = self._try_reanchor(
            remaining_chords, # Reancora a sequência inteira restante
            parent_explanation,
            recursion_depth
        )
        if success:
            self.cache[cache_key] = (True, final_explanation, final_path)
            return True, final_explanation, final_path

        # Se tudo falhou, armazena o resultado da falha no cache e retorna
        self.cache[cache_key] = (False, parent_explanation, None)
        return False, parent_explanation, None

    def evaluate_satisfaction_recursive(
        self,
        current_tonality: Tonality,
        current_state: KripkeState,
        remaining_chords: List[Chord],
        recursion_depth: int,
        parent_explanation: Explanation,
        ranked_tonalities: Optional[List[Tonality]] = None
    ) -> Tuple[bool, Explanation]:
        initial_path = KripkePath()
        initial_path.add_step(current_state, current_tonality, f"Iniciando análise em {current_tonality.tonality_name}")

        if ranked_tonalities:
            self.ranked_tonalities = ranked_tonalities
        
        success, explanation, _ = self.evaluate_satisfaction_with_path(
            initial_path, remaining_chords, recursion_depth, parent_explanation
        )
        
        return success, explanation
