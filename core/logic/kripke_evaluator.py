from typing import List, Tuple, Optional

# Importar os modelos de domínio que criamos anteriormente
from core.domain.models import (
    Chord, KripkeState, Key as Tonality, KripkeStructureConfig,
    Explanation, DetailedExplanationStep, TonalFunction
)

# Constante para evitar recursão infinita em casos complexos
MAX_RECURSION_DEPTH = 20

class SatisfactionEvaluator:
    """
    Implementa a lógica recursiva da Definição 5 de Aragão, refatorada para
    priorizar estratégias de análise musicalmente intuitivas.
    """
    def __init__(self, kripke_config: KripkeStructureConfig, all_available_tonalities: List[Tonality], original_tonality: Tonality):
        """
        Inicializa o SatisfactionEvaluator.

        Args:
            kripke_config: A configuração base da estrutura Kripke (S, S0, SF, R).
            all_available_tonalities: Uma lista de todas as tonalidades conhecidas pelo sistema.
            original_tonality: A tonalidade principal da análise, usada para priorizar a reancoragem.
        """
        self.kripke_config: KripkeStructureConfig = kripke_config
        self.all_available_tonalities: List[Tonality] = all_available_tonalities
        self.original_tonality: Tonality = original_tonality # Armazena a tonalidade inicial da análise

    def _try_direct_continuation(
        self,
        p_chord: Chord,
        phi_sub_sequence: List[Chord],
        current_tonality: Tonality,
        current_state: KripkeState,
        parent_explanation: Explanation,
        recursion_depth: int
    ) -> Tuple[bool, Optional[Explanation]]:
        """
        TENTATIVA 1: Implementa a continuação direta (Eq. 4A de Aragão).
        Verifica se P se encaixa e, em caso afirmativo, tenta satisfazer a cauda (phi) nos estados sucessores.
        """
        if not current_tonality.chord_fulfills_function(p_chord, current_state.associated_tonal_function):
            return False, None # P não se encaixa na função atual nesta tonalidade.

        # P é satisfeito. Logar este fato.
        explanation_after_P = parent_explanation.clone()
        explanation_after_P.add_step(
            formal_rule_applied="P in L",
            observation=f"Chord '{p_chord.name}' fulfills function '{current_state.associated_tonal_function.name}' in '{current_tonality.key_name}'.",
            evaluated_functional_state=current_state,
            processed_chord=p_chord,
            key_used_in_step=current_tonality
        )

        # Caso base: Se P era o último acorde, a continuação é um sucesso.
        if not phi_sub_sequence:
            return True, explanation_after_P

        # Caso recursivo: Tentar satisfazer a cauda a partir dos sucessores.
        for next_state in self.kripke_config.get_successors_of_state(current_state):
            success, final_explanation = self.evaluate_satisfaction_recursive(
                current_tonality, next_state, phi_sub_sequence, recursion_depth + 1, explanation_after_P
            )
            if success:
                return True, final_explanation

        return False, None # A continuação direta a partir deste estado não levou a uma solução.

    def _try_tonicization_pivot(
        self,
        p_chord: Chord,
        phi_sub_sequence: List[Chord],
        current_tonality: Tonality,
        current_state: KripkeState,
        parent_explanation: Explanation,
        recursion_depth: int
    ) -> Tuple[bool, Optional[Explanation]]:
        """
        TENTATIVA 2: Implementa a tonicização (variação da Eq. 5 de Aragão).
        Verifica se P pode atuar como uma nova tônica em uma tonalidade L'.
        """
        for l_prime_tonality in self.all_available_tonalities:
            # Não é um pivô se a tonalidade for a mesma.
            if l_prime_tonality.key_name == current_tonality.key_name:
                continue

            # O acorde P precisa cumprir a função atual em L E a função de TÔNICA em L'.
            p_is_valid_in_L = current_tonality.chord_fulfills_function(p_chord, current_state.associated_tonal_function)
            p_is_tonic_in_L_prime = l_prime_tonality.chord_fulfills_function(p_chord, TonalFunction.TONIC)

            if p_is_valid_in_L and p_is_tonic_in_L_prime:
                explanation_for_pivot = parent_explanation.clone()
                explanation_for_pivot.add_step(
                    formal_rule_applied="Eq.5 (Tonicization Pivot)",
                    observation=f"Chord '{p_chord.name}' acts as pivot. It is '{current_state.associated_tonal_function.name}' in '{current_tonality.key_name}' and becomes the new TONIC in '{l_prime_tonality.key_name}'.",
                    evaluated_functional_state=current_state,
                    processed_chord=p_chord,
                    key_used_in_step=current_tonality
                )
                
                new_tonic_state = self.kripke_config.get_state_by_tonal_function(TonalFunction.TONIC)
                if not new_tonic_state: return False, None # Configuração inválida

                # Tentar satisfazer a cauda a partir dos sucessores da NOVA tônica na NOVA tonalidade.
                for next_state in self.kripke_config.get_successors_of_state(new_tonic_state):
                    success, final_explanation = self.evaluate_satisfaction_recursive(
                        l_prime_tonality, next_state, phi_sub_sequence, recursion_depth + 1, explanation_for_pivot
                    )
                    if success:
                        return True, final_explanation

        return False, None # Nenhuma oportunidade de pivô para tônica foi encontrada/bem-sucedida.

    def _try_reanchor_tail(
        self,
        phi_sub_sequence: List[Chord],
        parent_explanation: Explanation,
        recursion_depth: int
    ) -> Tuple[bool, Optional[Explanation]]:
        """
        TENTATIVA 3: Reancoragem geral da cauda (Eq. 4B de Aragão).
        Tenta satisfazer a cauda como um novo problema, priorizando a tonalidade original.
        """
        if not phi_sub_sequence:
            return False, None # Não há cauda para reancorar.

        explanation_before_reanchor = parent_explanation.clone()
        explanation_before_reanchor.add_step(
            formal_rule_applied="Attempt Eq.4B (Re-anchor Tail)",
            observation=f"Direct continuation/pivot failed. Attempting to re-evaluate tail '{[c.name for c in phi_sub_sequence]}' from a new context."
        )

        # Lista de tonalidades para tentar, com a original primeiro.
        tonalities_to_try = [self.original_tonality] + [k for k in self.all_available_tonalities if k.key_name != self.original_tonality.key_name]
        
        # O estado inicial para uma reancoragem é sempre a tônica.
        tonic_start_state = self.kripke_config.get_state_by_tonal_function(TonalFunction.TONIC)
        if not tonic_start_state: return False, None

        for l_star_tonality in tonalities_to_try:
            success, final_explanation = self.evaluate_satisfaction_recursive(
                l_star_tonality, tonic_start_state, phi_sub_sequence, recursion_depth + 1, explanation_before_reanchor
            )
            if success:
                return True, final_explanation

        return False, None # A reancoragem falhou em todas as tonalidades.

    def evaluate_satisfaction_recursive(
        self,
        current_tonality: Tonality,
        current_state: KripkeState,
        remaining_chords: List[Chord],
        recursion_depth: int,
        parent_explanation: Explanation
    ) -> Tuple[bool, Explanation]:
        """
        Método principal que orquestra a busca por uma solução usando as estratégias
        em ordem de prioridade.
        """
        # --- Verificações Iniciais ---
        if recursion_depth > MAX_RECURSION_DEPTH:
            explanation_failure = parent_explanation.clone()
            explanation_failure.add_step(formal_rule_applied="Recursion Limit", observation="Exceeded maximum recursion depth.")
            return False, explanation_failure

        if not remaining_chords:
            return True, parent_explanation # Sucesso, sequência vazia.

        p_chord = remaining_chords[0]
        phi_sub_sequence = remaining_chords[1:]

        # --- ESTRATÉGIA DE BUSCA ---

        # TENTATIVA 1: Continuação Direta
        success, explanation = self._try_direct_continuation(
            p_chord, phi_sub_sequence, current_tonality, current_state, parent_explanation, recursion_depth
        )
        if success:
            return True, explanation

        # TENTATIVA 2: Tonicização/Pivô
        success, explanation = self._try_tonicization_pivot(
            p_chord, phi_sub_sequence, current_tonality, current_state, parent_explanation, recursion_depth
        )
        if success:
            return True, explanation

        # TENTATIVA 3: Reancoragem Geral da Cauda
        success, explanation = self._try_reanchor_tail(
            phi_sub_sequence, parent_explanation, recursion_depth
        )
        if success:
            # Se a reancoragem da cauda funcionou, precisamos adicionar a validação do acorde P atual
            # à explicação retornada, pois a reancoragem só lidou com a cauda.
            # No entanto, a lógica de reancoragem como está agora no _try_reanchor_tail já
            # chama o evaluate_satisfaction_recursive principal para a cauda, então a explicação
            # já estará sendo construída corretamente dentro dessa chamada.
            # O que precisamos é garantir que o P atual foi logado.
            final_explanation = parent_explanation.clone()
            final_explanation.add_step(
                formal_rule_applied="P in L (prior to successful re-anchor)",
                observation=f"Chord '{p_chord.name}' was valid in '{current_tonality.key_name}', leading to a successful re-anchor of its tail.",
                evaluated_functional_state=current_state,
                processed_chord=p_chord,
                key_used_in_step=current_tonality
            )
            final_explanation.steps.extend(explanation.steps) # Adicionar os passos da reancoragem bem-sucedida
            return True, final_explanation

        # Se nenhuma estratégia funcionou.
        return False, parent_explanation
