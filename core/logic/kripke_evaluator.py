from typing import List, Tuple

from core.domain.models import (
    KripkeStructureConfig,
    Tonality,
    KripkeState,
    Chord,
    Explanation,
)

MAX_RECURSION_DEPTH = 50

class SatisfactionEvaluator:
    def __init__(self, kripke_config: KripkeStructureConfig, all_available_tonalities: List[Tonality]):
        self.kripke_config: KripkeStructureConfig = kripke_config
        self.all_available_tonalities: List[Tonality] = all_available_tonalities
        # O ProgressionAnalyzer pode ser necessário para a reavaliação completa de phi
        # Se não quisermos uma dependência circular, podemos passar uma referência a um método
        # ou simplificar a reavaliação de phi para começar sempre do estado Tônica.
        # Por agora, vamos manter a lógica de reavaliação dentro desta classe.

    def evaluate_satisfaction_recursive(
        self,
        current_tonality: Tonality,
        current_state_in_path: KripkeState,
        remaining_chord_sequence: List[Chord],
        recursion_depth: int,
        parent_explanation: Explanation # Renomeado para clareza
    ) -> Tuple[bool, Explanation]:

        if recursion_depth > MAX_RECURSION_DEPTH:
            explanation_failure = parent_explanation.clone()
            explanation_failure.add_step(
                formal_rule_applied="Recursion Limit",
                observation=f"Exceeded maximum recursion depth ({MAX_RECURSION_DEPTH}).",
                evaluated_functional_state=current_state_in_path,
                tonality_used_in_step=current_tonality
            )
            return False, explanation_failure

        if not remaining_chord_sequence:
            current_explanation = parent_explanation.clone()
            current_explanation.add_step(
                formal_rule_applied="Base (Empty Seq)",
                observation="Chord sequence fully consumed successfully.",
                evaluated_functional_state=current_state_in_path,
                tonality_used_in_step=current_tonality
            )
            return True, current_explanation

        current_chord: Chord = remaining_chord_sequence
        phi_sub_sequence: List[Chord] = remaining_chord_sequence[1:]

        # --- ATTEMPT 1: P em L, e então φ em L via sucessores de current_state_in_path ---
        # (Corresponde a K,L|=π_k P e K,L|=π_{k+1,n} φ da Eq. 4A)
        p_satisfied_in_L: bool = current_tonality.chord_fulfills_function(
            current_chord,
            current_state_in_path.associated_tonal_function
        )

        if p_satisfied_in_L:
            # P está satisfeito em L no estado atual.
            # Clonar a explicação aqui, pois este é um ponto de ramificação válido.
            explanation_after_P_in_L = parent_explanation.clone()
            explanation_after_P_in_L.add_step(
                formal_rule_applied="P in L", # Um passo genérico para P
                observation=(
                    f"Chord '{current_chord.name}' fulfills function "
                    f"'{current_state_in_path.associated_tonal_function.to_string()}' "
                    f"in tonality '{current_tonality.tonality_name}' (at state '{current_state_in_path.state_id}')."
                ),
                evaluated_functional_state=current_state_in_path,
                processed_chord=current_chord,
                tonality_used_in_step=current_tonality
            )

            if not phi_sub_sequence: # BASE CASE 2: P é o último acorde, P em L (Eq. 3)
                explanation_eq3_L = explanation_after_P_in_L # Já clonado e com P adicionado
                explanation_eq3_L.add_step( # Adiciona a conclusão da Eq.3
                    formal_rule_applied="Eq.3 (L)",
                    observation="End of sequence. Progression satisfied.",
                    evaluated_functional_state=current_state_in_path, # Estado onde P foi satisfeito
                    processed_chord=current_chord, # O P que foi satisfeito
                    tonality_used_in_step=current_tonality
                )
                return True, explanation_eq3_L

            # RECURSIVO: Tentar φ em L via sucessores (Eq. 4A para φ)
            successors = self.kripke_config.get_successors_of_state(current_state_in_path)
            if successors:
                for next_state_L in successors:
                    explanation_for_L_branch = explanation_after_P_in_L.clone() # Clonar a partir do ponto onde P foi satisfeito em L
                    explanation_for_L_branch.add_step(
                        formal_rule_applied="Try φ in L (Eq.4A)",
                        observation=(
                            f"Attempting to satisfy tail '{[c.name for c in phi_sub_sequence]}' in tonality '{current_tonality.tonality_name}' "
                            f"from next state '{next_state_L.state_id}'."
                        )
                        # Não há current_chord/state específico para *este* passo de tentativa de ramo
                    )
                    success_phi_L, expl_phi_L = self.evaluate_satisfaction_recursive(
                        current_tonality, next_state_L, phi_sub_sequence, recursion_depth + 1, explanation_for_L_branch
                    )
                    if success_phi_L:
                        return True, expl_phi_L
            # Se chegamos aqui, P estava em L, mas φ não pôde ser satisfeito continuando em L via sucessores.
            # Agora, o "Fluxo Refinado" sugere que devemos tentar a Opção 4B generalizada para φ.
            # E também a Eq. 5 (P como pivô) é uma alternativa para Pφ.

            # --- ATTEMPT 3 (NOVO): Reavaliação independente de φ (Opção 4B generalizada: K,L* |=_{\overline{\pi}} φ) ---
            # Isto é tentado SE P foi satisfeito em L, MAS a continuação direta de φ em L (acima) falhou.
            # Isto corresponde ao "ou K,L|=π′ϕ" da Eq.4, onde π' é um novo caminho para φ,
            # potencialmente em uma nova tonalidade L*.
            if phi_sub_sequence: # Só faz sentido se houver uma cauda φ
                explanation_before_phi_re_eval = explanation_after_P_in_L.clone() # Explicação até P ter sido satisfeito em L
                explanation_before_phi_re_eval.add_step(
                    formal_rule_applied="Attempt Eq.4B (Re-eval φ)",
                    observation=(
                        f"Continuation of tail '{[c.name for c in phi_sub_sequence]}' in tonality '{current_tonality.tonality_name}' failed. "
                        f"Now attempting to satisfy tail independently via alternative paths/tonalitys."
                    )
                )
                
                first_chord_of_phi = phi_sub_sequence
                for l_star_tonality in self.all_available_tonalities:
                    # Para cada L*, tentar iniciar phi_sub_sequence a partir de qualquer estado s'
                    # onde o primeiro acorde de phi (P_phi) é satisfeito em L*(s').
                    for potential_start_state_for_phi in self.kripke_config.states:
                        if l_star_tonality.chord_fulfills_function(first_chord_of_phi, potential_start_state_for_phi.associated_tonal_function):
                            explanation_for_phi_re_eval_branch = explanation_before_phi_re_eval.clone()
                            explanation_for_phi_re_eval_branch.add_step(
                                formal_rule_applied="Try φ in L* (Eq.4B)",
                                observation=(
                                    f"Attempting independent satisfaction of tail '{[c.name for c in phi_sub_sequence]}' "
                                    f"in tonality '{l_star_tonality.tonality_name}' starting from state '{potential_start_state_for_phi.state_id}' "
                                    f"for its first chord '{first_chord_of_phi.name}'."
                                )
                            )
                            success_phi_re_eval, expl_phi_re_eval = self.evaluate_satisfaction_recursive(
                                l_star_tonality, potential_start_state_for_phi, phi_sub_sequence,
                                recursion_depth + 1, # A profundidade da recursão continua
                                explanation_for_phi_re_eval_branch
                            )
                            if success_phi_re_eval:
                                return True, expl_phi_re_eval
            # Se P estava em L, mas nem a continuação de φ em L (ATTEMPT 1) nem a reavaliação de φ (ATTEMPT 3) funcionaram,
            # ainda precisamos considerar a Eq. 5 (ATTEMPT 2) como uma forma alternativa de satisfazer Pφ como um todo.

        # --- ATTEMPT 2: P como pivô para L' (Eq. 5: K,L|=π0P e K,L'|=π′0P e K,L'|=π′1,nφ) ---
        # Esta é uma alternativa para satisfazer Pφ na tonalidade original L.
        # Requer que P seja satisfeito em L no estado atual (verificado por p_satisfied_in_L).
        # E P também seja satisfeito em L' no estado atual.
        # E φ seja satisfeita em L' a partir dos sucessores do estado atual.
        if p_satisfied_in_L: # Condição 1 da Eq. 5: K,L|=π_k P
            for alternative_tonality_for_pivot in self.all_available_tonalities:
                if alternative_tonality_for_pivot.tonality_name == current_tonality.tonality_name:
                    continue # Não é realmente uma alternativa L'

                # Condição 2 da Eq. 5: K,L'|=π_k P (usando current_state_in_path como π_k para L')
                p_satisfied_in_L_prime_for_pivot: bool = alternative_tonality_for_pivot.chord_fulfills_function(
                    current_chord,
                    current_state_in_path.associated_tonal_function
                )

                if p_satisfied_in_L_prime_for_pivot:
                    # P está satisfeito em L (p_satisfied_in_L) E P está satisfeito em L' (p_satisfied_in_L_prime_for_pivot)
                    # no mesmo current_state_in_path.
                    explanation_after_P_in_L_and_Lprime = parent_explanation.clone() # Começa do pai, pois esta é uma alternativa para Pφ
                    explanation_after_P_in_L_and_Lprime.add_step(
                        formal_rule_applied="Eq.5 (P in L & L')",
                        observation=(
                            f"Chord '{current_chord.name}' acts as pivot: fulfills function "
                            f"'{current_state_in_path.associated_tonal_function.to_string()}' "
                            f"in original tonality '{current_tonality.tonality_name}' AND in alternative tonality '{alternative_tonality_for_pivot.tonality_name}' "
                            f"at state '{current_state_in_path.state_id}'."
                        ),
                        evaluated_functional_state=current_state_in_path,
                        processed_chord=current_chord,
                        tonality_used_in_step=current_tonality # Ou talvez ambos? Para clareza, o original.
                    )

                    if not phi_sub_sequence: # BASE CASE: P é o último, satisfeito via Eq. 5
                        explanation_eq5_L_prime_p_last = explanation_after_P_in_L_and_Lprime
                        explanation_eq5_L_prime_p_last.add_step(
                            formal_rule_applied="Eq.5 (L', φ empty)",
                            observation="End of sequence. Progression satisfied via pivot chord.",
                            # evaluated_functional_state, processed_chord já no passo anterior
                            tonality_used_in_step=alternative_tonality_for_pivot # A "nova" tonalidade para a (vazia) cauda
                        )
                        return True, explanation_eq5_L_prime_p_last

                    # RECURSIVO: Tentar φ em L' via sucessores (Condição 3 da Eq. 5)
                    successors_for_L_prime_pivot = self.kripke_config.get_successors_of_state(current_state_in_path)
                    if successors_for_L_prime_pivot:
                        for next_state_L_prime in successors_for_L_prime_pivot:
                            explanation_for_L_prime_pivot_branch = explanation_after_P_in_L_and_Lprime.clone()
                            explanation_for_L_prime_pivot_branch.add_step(
                                formal_rule_applied="Try φ in L' (Eq.5 cont.)",
                                observation=(
                                    f"Attempting to satisfy tail '{[c.name for c in phi_sub_sequence]}' in pivoted tonality '{alternative_tonality_for_pivot.tonality_name}' "
                                    f"from next state '{next_state_L_prime.state_id}'."
                                )
                            )
                            success_phi_L_prime, expl_phi_L_prime = self.evaluate_satisfaction_recursive(
                                alternative_tonality_for_pivot, next_state_L_prime, phi_sub_sequence,
                                recursion_depth + 1, explanation_for_L_prime_pivot_branch
                            )
                            if success_phi_L_prime:
                                return True, expl_phi_L_prime
                    # Se φ não pôde ser satisfeito em L' após o pivô, este ramo da Eq.5 falha.
        
        # Se P não foi satisfeito em L (p_satisfied_in_L é False), E
        # a tentativa de usar P como pivô para L' (ATTEMPT 2) também não funcionou (ou não foi aplicável),
        # OU se P foi satisfeito em L mas nenhuma das continuações para φ (ATTEMPT 1 ou ATTEMPT 3) funcionou.
        # Então, este ramo da avaliação falha para current_chord.
        final_branch_explanation = parent_explanation.clone()
        final_branch_explanation.add_step(
            formal_rule_applied="Branch Failure",
            observation=(
                f"Chord '{current_chord.name}' could not be satisfied from state "
                f"'{current_state_in_path.state_id}' ({current_state_in_path.associated_tonal_function.to_string()}) "
                f"under tonality '{current_tonality.tonality_name}' through any applicable rule (Eq.3, Eq.4A, Eq.4B general, or Eq.5)."
            ),
            evaluated_functional_state=current_state_in_path,
            processed_chord=current_chord,
            tonality_used_in_step=current_tonality
        )
        return False, final_branch_explanation