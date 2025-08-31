from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.schemas.analysis_schemas import ProgressionAnalysisRequest, ProgressionAnalysisResponse
from api.services.analysis_service import TonalAnalysisService
from core.i18n import T


# The get_analysis_service function will be provided by main.py through dependency injection.
# This approach allows service configuration and initialization to be centralized.
def get_analysis_service() -> TonalAnalysisService:
    raise NotImplementedError(T("errors.dependency_not_implemented"))


router = APIRouter()


@router.post(
    "/analyze",
    response_model=ProgressionAnalysisResponse,
    summary=T("endpoints.analyze.summary"),
    tags=["Analysis"],
)
async def analyze_progression(
    request: ProgressionAnalysisRequest,
    service: TonalAnalysisService = Depends(get_analysis_service),
    lang: Optional[str] = Query(None, description="Language for the response (en, pt_br)"),
) -> ProgressionAnalysisResponse:
    """
    Receives a list of chords and optionally a list of tonalities to test.

    - **chords**: A list of strings, where each string is a chord (e.g., "C", "G7", "Am").
    - **tonalities_to_test**: (Optional) A list of tonality names (e.g., "C Major") to limit the analysis.

    Returns a detailed analysis indicating whether the progression is tonal, in which
    tonality it was identified, and the formal steps of the analysis.
    """
    # Set locale based on query parameter
    from core.i18n.locale_manager import locale_manager

    if lang:
        locale_manager.set_locale(lang)

    try:
        result: ProgressionAnalysisResponse = service.analyze_progression(request)
        if result.error:
            raise HTTPException(status_code=400, detail=result.error)
        return result
    except Exception as e:
        # Handle unexpected server errors
        raise HTTPException(status_code=500, detail=T("errors.internal_server_error", error=str(e)))
