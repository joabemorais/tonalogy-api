import pytest
from unittest.mock import MagicMock

# Importar as classes que vamos testar e usar
from core.logic.progression_analyzer import ProgressionAnalyzer
from core.domain.models import Chord, Tonality, Explanation

# Usaremos fixtures para os mocks. No seu projeto real, as fixtures de
# mock_kripke_config, c_major_tonality_mock, etc., poderiam ser movidas
# para um arquivo central de testes (conftest.py).

@pytest.fixture
def mock_kripke_config():
    """Cria um mock da configuração Kripke."""
    config = MagicMock()
    mock_tonic_state = MagicMock()
    config.get_state_by_tonal_function.return_value = mock_tonic_state
    return config

@pytest.fixture
def c_major_tonality_mock():
    """Cria um mock para a tonalidade de Dó Maior."""
    key = MagicMock(spec=Tonality)
    key.key_name = "C Major"
    return key

@pytest.fixture
def g_major_tonality_mock():
    """Cria um mock para a tonalidade de Sol Maior."""
    key = MagicMock(spec=Tonality)
    key.key_name = "G Major"
    return key


# --- Testes ---

def test_check_progression_returns_true_on_first_key(mocker, mock_kripke_config, c_major_tonality_mock):
    """
    Verifica se o analisador retorna True quando a primeira tonalidade testada é bem-sucedida.
    """
    # GIVEN: um mock do SatisfactionEvaluator que sempre retorna sucesso
    mock_evaluator_instance = MagicMock()
    mock_evaluator_instance.evaluate_satisfaction_recursive.return_value = (True, Explanation())

    # Substituímos a classe SatisfactionEvaluator pelo nosso mock.
    # Sempre que a classe for instanciada, ela retornará nosso 'mock_evaluator_instance'.
    mocker.patch(
        'core.logic.progression_analyzer.SatisfactionEvaluator',
        return_value=mock_evaluator_instance
    )

    # WHEN: criamos o ProgressionAnalyzer e rodamos a análise
    analyzer = ProgressionAnalyzer(mock_kripke_config, [c_major_tonality_mock])
    progression = [Chord("C"), Chord("G7")]
    
    success, _ = analyzer.check_tonal_progression(progression, [c_major_tonality_mock])

    # THEN: o resultado deve ser sucesso
    assert success is True
    # Verificamos se o avaliador foi chamado corretamente
    mock_evaluator_instance.evaluate_satisfaction_recursive.assert_called_once()


def test_check_progression_returns_true_on_second_key(mocker, mock_kripke_config, c_major_tonality_mock, g_major_tonality_mock):
    """
    Verifica se o analisador continua para a segunda tonalidade se a primeira falhar.
    """
    # GIVEN: um mock do evaluator que falha na primeira chamada e tem sucesso na segunda
    mock_evaluator_instance = MagicMock()
    mock_evaluator_instance.evaluate_satisfaction_recursive.side_effect = [
        (False, Explanation()), # Resultado para a primeira chamada (C Major)
        (True, Explanation())   # Resultado para a segunda chamada (G Major)
    ]
    mocker.patch(
        'core.logic.progression_analyzer.SatisfactionEvaluator',
        return_value=mock_evaluator_instance
    )

    # WHEN: rodamos a análise com duas tonalidades
    tonalities_to_test = [c_major_tonality_mock, g_major_tonality_mock]
    analyzer = ProgressionAnalyzer(mock_kripke_config, tonalities_to_test)
    progression = [Chord("G"), Chord("D7")]
    
    success, _ = analyzer.check_tonal_progression(progression, tonalities_to_test)

    # THEN: o resultado final é sucesso e o avaliador foi chamado duas vezes
    assert success is True
    assert mock_evaluator_instance.evaluate_satisfaction_recursive.call_count == 2


def test_check_progression_returns_false_if_all_keys_fail(mocker, mock_kripke_config, c_major_tonality_mock):
    """
    Verifica se o analisador retorna False se nenhuma tonalidade satisfizer a progressão.
    """
    # GIVEN: um mock do evaluator que sempre retorna falha
    mock_evaluator_instance = MagicMock()
    mock_evaluator_instance.evaluate_satisfaction_recursive.return_value = (False, Explanation())
    mocker.patch(
        'core.logic.progression_analyzer.SatisfactionEvaluator',
        return_value=mock_evaluator_instance
    )

    # WHEN: rodamos a análise
    analyzer = ProgressionAnalyzer(mock_kripke_config, [c_major_tonality_mock])
    progression = [Chord("C"), Chord("F#")]
    
    success, _ = analyzer.check_tonal_progression(progression, [c_major_tonality_mock])

    # THEN: o resultado é falha
    assert success is False


def test_check_progression_handles_empty_sequence(mock_kripke_config, c_major_tonality_mock):
    """
    Verifica o caso de borda de uma progressão de acordes vazia.
    """
    # WHEN: rodamos a análise com uma lista vazia
    analyzer = ProgressionAnalyzer(mock_kripke_config, [c_major_tonality_mock])
    success, explanation = analyzer.check_tonal_progression([], [c_major_tonality_mock])

    # THEN: o resultado é falha e a explicação reflete o erro
    assert success is False
    assert "empty" in explanation.steps[0].observation.lower()
