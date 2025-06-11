from fastapi import APIRouter, Depends, HTTPException

from api.schemas.analysis_schemas import ProgressionAnalysisRequest, ProgressionAnalysisResponse
from api.services.analysis_service import TonalAnalysisService

# The get_analysis_service function will be provided by main.py through dependency injection.
# This approach allows service configuration and initialization to be centralized.
def get_analysis_service() -> TonalAnalysisService:
    raise NotImplementedError("Dependency not implemented. This will be overridden by the main app.")

router = APIRouter()

@router.post(
    "/analyze",
    response_model=ProgressionAnalysisResponse,
    summary="Analyzes a Tonal Harmonic Progression",
    tags=["Analysis"]
)
async def analyze_progression(
    request: ProgressionAnalysisRequest,
    service: TonalAnalysisService = Depends(get_analysis_service)
) -> ProgressionAnalysisResponse:
    """
    Receives a list of chords and optionally a list of tonalities to test.
    
    - **chords**: A list of strings, where each string is a chord (e.g., "C", "G7", "Am").
    - **tonalities_to_test**: (Optional) A list of tonality names (e.g., "C Major") to limit the analysis.
    
    Returns a detailed analysis indicating whether the progression is tonal, in which
    tonality it was identified, and the formal steps of the analysis.
    """
    try:
        # Only catch service-level exceptions, not HTTPExceptions
        result: ProgressionAnalysisResponse = service.analyze_progression(request)
    except Exception as e:
        # Handle unexpected server errors
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")
    
    # Check for error outside the try block so HTTPException isn't caught
    if result.error:
        raise HTTPException(status_code=400, detail=result.error)
        
    return result

