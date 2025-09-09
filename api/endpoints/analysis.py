from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.schemas.analysis_schemas import ProgressionAnalysisRequest, ProgressionAnalysisResponse
from api.services.analysis_service import TonalAnalysisService
from core.i18n import T


class HumanReadableExplanationResponse(BaseModel):
    """Response model for human-readable explanation endpoint."""
    explanation: str = Field(
        ..., 
        description="A narrative explanation of the harmonic analysis in plain language",
        json_schema_extra={
            "example": "We're analyzing the chord progression C → F → G → C. This progression appears to be tonal and is anchored in the key of C Major. In C Major, this progression features a plagal cadence pattern (subdominant to tonic resolution): C (tonic) → F (subdominant) → G (dominant) → C (tonic). Overall, this progression establishes a clear tonal center in C Major, following traditional harmonic conventions."
        }
    )
    is_tonal: bool = Field(
        ..., 
        description="Whether the progression follows traditional tonal patterns",
        json_schema_extra={"example": True}
    )
    identified_tonality: Optional[str] = Field(
        None, 
        description="The key/tonality identified for the progression",
        json_schema_extra={"example": "C Major"}
    )


# The get_analysis_service function will be provided by main.py through dependency injection.
# This approach allows service configuration and initialization to be centralized.
def get_analysis_service() -> TonalAnalysisService:
    raise NotImplementedError(T("errors.dependency_not_implemented"))


router = APIRouter()


@router.post(
    "/analyze",
    response_model=ProgressionAnalysisResponse,
    summary=T("endpoints.analyze.summary"),
    description="**Comprehensive Harmonic Analysis** - Analyzes chord progressions using Kripke semantics and modal logic. Includes human-readable explanations perfect for education and non-technical users!",
    response_description="Complete analysis with technical steps and natural language explanation",
    tags=["Analysis"],
)
async def analyze_progression(
    request: ProgressionAnalysisRequest,
    service: TonalAnalysisService = Depends(get_analysis_service),
    lang: Optional[str] = Query(
        None, 
        description="Language for the response (en, pt_br)",
        example="en"
    ),
) -> ProgressionAnalysisResponse:
    """
    **Complete Harmonic Analysis with Human-Readable Explanations**

    Includes natural language explanations alongside technical analysis!

    **Input Parameters:**
    - **chords**: List of chord symbols (e.g., ["C", "Am", "F", "G"])
    - **tonalities_to_test**: (Optional) Limit analysis to specific keys
    - **lang**: Response language (en for English, pt_br for Portuguese)
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


@router.post(
    "/explain",
    response_model=HumanReadableExplanationResponse,
    summary="Get Human-Readable Explanation Only",
    description="Returns only the natural language explanation from harmonic analysis (subset of /analyze endpoint).",
    response_description="Simplified response with just the narrative explanation",
    tags=["Analysis"],
)
async def get_human_readable_explanation(
    request: ProgressionAnalysisRequest,
    service: TonalAnalysisService = Depends(get_analysis_service),
    lang: Optional[str] = Query(
        None, 
        description="Language for the response (en, pt_br)",
        example="en"
    ),
) -> HumanReadableExplanationResponse:
    """
    Returns only the human-readable explanation portion of the harmonic analysis.
    
    This is a simplified endpoint that extracts just the narrative explanation 
    from the full analysis performed by the /analyze endpoint.
    
    **Parameters:**
    - **chords**: List of chord symbols to analyze
    - **lang**: Language for explanation (en, pt_br)
    
    **For full analysis with technical details, use the /analyze endpoint.**
    """
    # Set locale based on query parameter
    from core.i18n.locale_manager import locale_manager

    if lang:
        locale_manager.set_locale(lang)

    try:
        result: ProgressionAnalysisResponse = service.analyze_progression(request)
        if result.error:
            raise HTTPException(status_code=400, detail=result.error)
        
        explanation = result.human_readable_explanation or "No explanation available."
        
        return HumanReadableExplanationResponse(
            explanation=explanation,
            is_tonal=result.is_tonal_progression,
            identified_tonality=result.identified_tonality
        )
    except Exception as e:
        # Handle unexpected server errors
        raise HTTPException(status_code=500, detail=T("errors.internal_server_error", error=str(e)))
