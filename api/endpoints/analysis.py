from fastapi import APIRouter, Depends, HTTPException
from typing import Dict

from api.schemas.analysis_schemas import ProgressionAnalysisRequest, ProgressionAnalysisResponse
from api.services.analysis_service import TonalAnalysisService

# A função get_analysis_service será fornecida pelo main.py através de injeção de dependência.
# Esta abordagem permite que a configuração e a inicialização do serviço sejam centralizadas.
def get_analysis_service() -> TonalAnalysisService:
    raise NotImplementedError("Dependency not implemented. This will be overridden by the main app.")

router = APIRouter()

@router.post(
    "/analyze",
    response_model=ProgressionAnalysisResponse,
    summary="Analisa uma Progressão Harmónica Tonal",
    tags=["Analysis"]
)
async def analyze_progression(
    request: ProgressionAnalysisRequest,
    service: TonalAnalysisService = Depends(get_analysis_service)
):
    """
    Recebe uma lista de acordes e opcionalmente uma lista de tonalidades para testar.
    
    - **chords**: Uma lista de strings, onde cada string é um acorde (e.g., "C", "G7", "Am").
    - **keys_to_test**: (Opcional) Uma lista de nomes de tonalidades (e.g., "C Major") para limitar a análise.
    
    Retorna uma análise detalhada indicando se a progressão é tonal, em qual
    tonalidade foi identificada, e os passos formais da análise.
    """
    try:
        result = service.analyze_progression(request)
        if result.error:
            raise HTTPException(status_code=400, detail=result.error)
        return result
    except Exception as e:
        # Tratamento de erros inesperados no servidor
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")

