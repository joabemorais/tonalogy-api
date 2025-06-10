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