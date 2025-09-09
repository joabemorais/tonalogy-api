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
    description="Performs comprehensive harmonic analysis of a chord progression using Kripke semantics and modal logic. Returns both technical analysis steps and a human-readable explanation.",
    response_description="Detailed analysis results including technical steps and narrative explanation",
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
    Performs comprehensive harmonic analysis of a chord progression.

    **New Feature**: Now includes human-readable explanations that make harmonic 
    analysis accessible to musicians and students without technical background.

    **Input Parameters:**
    - **chords**: A list of chord symbols (e.g., ["C", "Am", "F", "G"])
    - **tonalities_to_test**: (Optional) Limit analysis to specific keys
    - **lang**: Response language (en for English, pt_br for Portuguese)

    **Returns:**
    - Technical analysis steps for formal verification
    - **Human-readable explanation** in natural language
    - Identified tonality and tonal classification

    **Example Usage:**
    Try these chord progressions:
    - Classic I-vi-IV-V: ["C", "Am", "F", "G"]  
    - ii-V-I Jazz: ["Dm", "G7", "C"]
    - Plagal cadence: ["C", "F", "C"]
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
    summary="Get Human-Readable Harmonic Analysis Explanation",
    description="🆕 **NEW FEATURE**: Analyzes chord progressions and returns only a natural language explanation, perfect for educational use and non-technical audiences.",
    response_description="Simple, narrative explanation of the harmonic analysis",
    tags=["Analysis", "Human-Readable"],
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
    🎵 **Human-Readable Harmonic Analysis** 🎵
    
    This endpoint transforms complex music theory into accessible explanations!
    Perfect for:
    - **Music students** learning harmonic analysis
    - **Teachers** explaining chord progressions
    - **Applications** that need natural language descriptions
    - **Musicians** who want to understand their progressions

    **What you get:**
    - Clear, narrative explanation in everyday language
    - Identification of common patterns (cadences, modulations)
    - Key/tonality information
    - Bilingual support (English/Portuguese)

    **Try these examples:**
    - **Pop progression**: ["C", "G", "Am", "F"] 
    - **Jazz ii-V-I**: ["Dm7", "G7", "Cmaj7"]
    - **Classical cadence**: ["C", "F", "G", "C"]
    - **Modal progression**: ["Am", "F", "C", "G"]

    **Languages:**
    - `lang=en` for English explanations
    - `lang=pt_br` for Portuguese explanations (explicações em português)
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
