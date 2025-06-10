# tonalogy-api/tests/core/logic/test_kripke_evaluator.py

import pytest
from typing import List, Set, Dict, Tuple

# Importar as classes que vamos testar e usar como dependências
from core.domain.models import (
    Chord, TonalFunction, KripkeState, Tonality,
    KripkeStructureConfig, Explanation, DetailedExplanationStep
)
from core.logic.kripke_evaluator import SatisfactionEvaluator

# --- Fixtures para criar um ambiente de teste consistente ---
# Essas fixtures fornecem objetos reutilizáveis para os nossos testes.

@pytest.fixture
def tonic_state() -> KripkeState:
    return KripkeState(state_id="s_t", associated_tonal_function=TonalFunction.TONIC)

@pytest.fixture
def dominant_state() -> KripkeState:
    return KripkeState(state_id="s_d", associated_tonal_function=TonalFunction.DOMINANT)

@pytest.fixture
def subdominant_state() -> KripkeState:
    return KripkeState(state_id="s_sd", associated_tonal_function=TonalFunction.SUBDOMINANT)

@pytest.fixture
def c_major_tonality() -> Tonality:
    return Tonality(
        tonality_name="C Major",
        function_to_chords_map={
            TonalFunction.TONIC: {Chord("C"), Chord("Am"), Chord("Em")},
            TonalFunction.DOMINANT: {Chord("G"), Chord("G7"), Chord("Bdim")},
            TonalFunction.SUBDOMINANT: {Chord("F"), Chord("Dm")}
        }
    )

@pytest.fixture
def d_minor_tonality() -> Tonality:
    return Tonality(
        tonality_name="D minor",
        function_to_chords_map={
            TonalFunction.TONIC: {Chord("Dm"), Chord("F")},
            TonalFunction.DOMINANT: {Chord("A"), Chord("A7")},
            TonalFunction.SUBDOMINANT: {Chord("Gm"), Chord("Bb")}
        }
    )

@pytest.fixture
def aragao_kripke_config(
    tonic_state: KripkeState,
    dominant_state: KripkeState,
    subdominant_state: KripkeState
    ) -> KripkeStructureConfig:
    """
    Cria a configuração da estrutura Kripke com as relações de acessibilidade
    INVERTIDAS, conforme a sugestão direta do autor Aragão.
    """
    return KripkeStructureConfig(
        states={tonic_state, dominant_state, subdominant_state},
        initial_states={tonic_state}, # Análise sempre começa na tônica
        final_states={tonic_state},
        accessibility_relation={
            (tonic_state, dominant_state),      # s_t -> s_d
            (tonic_state, subdominant_state),   # s_t -> s_sd
            (dominant_state, subdominant_state) # s_d -> s_sd
        }
    )

# --- Testes para a Classe SatisfactionEvaluator ---

def test_base_case_empty_sequence(aragao_kripke_config, c_major_tonality, tonic_state):
    """
    Testa o caso base mais simples: uma sequência de acordes vazia deve ser satisfeita.
    """
    # GIVEN: um avaliador e uma progressão vazia
    evaluator = SatisfactionEvaluator(aragao_kripke_config, [c_major_tonality], c_major_tonality)
    empty_progression: List[Chord] = []
    
    # WHEN: a avaliação é executada
    success, _ = evaluator.evaluate_satisfaction_recursive(
        current_tonality=c_major_tonality,
        current_state=tonic_state,
        remaining_chords=empty_progression,
        recursion_depth=0,
        parent_explanation=Explanation()
    )
    
    # THEN: o resultado deve ser sucesso
    assert success is True

def test_single_valid_chord_in_tonic(aragao_kripke_config, c_major_tonality, tonic_state):
    """
    Testa a Eq. 3 de Aragão: uma progressão com um único acorde que é válido na tônica.
    """
    # GIVEN: um avaliador e uma progressão com um acorde válido
    evaluator = SatisfactionEvaluator(aragao_kripke_config, [c_major_tonality], c_major_tonality)
    progression = [Chord("C")]
    
    # WHEN: a avaliação é executada
    success, explanation = evaluator.evaluate_satisfaction_recursive(
        current_tonality=c_major_tonality,
        current_state=tonic_state,
        remaining_chords=progression,
        recursion_depth=0,
        parent_explanation=Explanation()
    )
    
    # THEN: o resultado deve ser sucesso
    assert success is True
    assert "P in L" in explanation.steps[-1].formal_rule_applied
    assert "End of sequence" in explanation.steps[-1].observation

def test_direct_continuation_success_V_I(aragao_kripke_config, c_major_tonality, tonic_state):
    """
    Testa a TENTATIVA 1 (Eq. 4A): uma cadência V-I (invertida para C G).
    Isso deve seguir o caminho s_t -> s_d.
    """
    # GIVEN: um avaliador e a progressão invertida [C, G]
    evaluator = SatisfactionEvaluator(aragao_kripke_config, [c_major_tonality], c_major_tonality)
    progression = [Chord("C"), Chord("G")]
    
    # WHEN: a avaliação é executada
    success, explanation = evaluator.evaluate_satisfaction_recursive(
        current_tonality=c_major_tonality,
        current_state=tonic_state,
        remaining_chords=progression,
        recursion_depth=0,
        parent_explanation=Explanation()
    )
    
    # THEN: o resultado deve ser sucesso
    assert success is True
    # O rastro da explicação deve mostrar P='C' em L='Lc' e depois P='G' em L='Lc'
    assert explanation.steps[0].processed_chord == Chord("C")
    assert explanation.steps[1].processed_chord == Chord("G")
    assert "P in L" in explanation.steps[1].formal_rule_applied

def test_direct_continuation_failure_no_path(aragao_kripke_config, c_major_tonality, tonic_state):
    """
    Testa uma progressão que é harmonicamente plausível (G Dm) mas para a qual
    não há um caminho na nossa Relação de Acessibilidade R (não há s_d -> s_sd invertido, mas s_d->s_sd sim).
    No nosso R atual: s_d -> s_sd. A progressão G Dm (invertida) é Dm G.
    Dm é s_sd. G é s_d. Começando em s_t -> Dm(s_sd). s_sd não tem sucessor, então falha.
    """
    # GIVEN: um avaliador e a progressão invertida [Dm, G]
    evaluator = SatisfactionEvaluator(aragao_kripke_config, [c_major_tonality], c_major_tonality)
    progression = [Chord("Dm"), Chord("G")]
    
    # WHEN: a avaliação é executada na tônica
    success, _ = evaluator.evaluate_satisfaction_recursive(
        current_tonality=c_major_tonality,
        current_state=tonic_state,
        remaining_chords=progression,
        recursion_depth=0,
        parent_explanation=Explanation()
    )
    
    # THEN: o resultado deve ser falha, pois a continuação direta não funciona e o pivô/reancoragem
    # não encontrará uma solução simples.
    assert success is False


def test_tonicization_pivot_success_complex_progression(
    aragao_kripke_config, c_major_tonality, d_minor_tonality, tonic_state
):
    """
    Testa a progressão complexa do usuário: C G Dm A7 Em.
    Isso deve validar a TENTATIVA 2 (Tonicização/Pivô).
    """
    # GIVEN: um avaliador com múltiplas tonalidades e a progressão completa
    all_tonalities = [c_major_tonality, d_minor_tonality]
    # A análise começa em C Maior
    evaluator = SatisfactionEvaluator(aragao_kripke_config, all_tonalities, c_major_tonality)
    
    # A progressão original é Em A7 Dm G C. A invertida é C G Dm A7 Em.
    progression = [Chord("C"), Chord("G"), Chord("Dm"), Chord("A7"), Chord("Em")]
    
    # WHEN: a avaliação é executada
    success, explanation = evaluator.evaluate_satisfaction_recursive(
        current_tonality=c_major_tonality,
        current_state=tonic_state,
        remaining_chords=progression,
        recursion_depth=0,
        parent_explanation=Explanation()
    )

    # THEN: o resultado deve ser sucesso
    assert success is True

    # Vamos verificar alguns pontos chave na explicação para confirmar a lógica
    # Esperamos ver uma tonicização para Dm.
    pivot_step = next((step for step in explanation.steps if "Tonicization Pivot" in step.formal_rule_applied), None)
    assert pivot_step is not None
    assert pivot_step.processed_chord == Chord("Dm")
    assert "becomes the new TONIC in 'D minor'" in pivot_step.observation
    
    # O acorde seguinte (A7) deve ser processado em D minor.
    a7_step = next((step for step in explanation.steps if step.processed_chord == Chord("A7")), None)
    assert a7_step is not None
    assert a7_step.tonality_used_in_step.tonality_name == "D minor"

    # O acorde final (Em) deve ser reancorado de volta para C Major.
    em_step = next((step for step in explanation.steps if step.processed_chord == Chord("Em")), None)
    assert em_step is not None
    assert em_step.tonality_used_in_step.tonality_name == "C Major"
    assert "Re-anchor" in explanation.steps[explanation.steps.index(em_step) - 1].formal_rule_applied
