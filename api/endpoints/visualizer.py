from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
import os

from api.schemas.analysis_schemas import ProgressionAnalysisRequest
from api.services.analysis_service import TonalAnalysisService
from api.services.visualizer_service import VisualizerService
from api.endpoints.analysis import get_analysis_service

router = APIRouter()

def get_visualizer_service() -> VisualizerService:
    """Dependency for the VisualizerService."""
    return VisualizerService()

@router.post(
    "/visualize",
    summary="Analyzes and Visualizes a Tonal Harmonic Progression",
    tags=["Visualization"],
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Returns the generated PNG image of the analysis.",
        },
        400: {"description": "Invalid request, e.g.: non-tonal progression."},
    },
)
async def visualize_progression(
    request: ProgressionAnalysisRequest,
    analysis_service: TonalAnalysisService = Depends(get_analysis_service),
    visualizer_service: VisualizerService = Depends(get_visualizer_service)
):
    """
    Receives a list of chords, analyzes the progression and returns a
    visual diagram of the analysis.
    """
    analysis_result = analysis_service.analyze_progression(request)

    if not analysis_result.is_tonal_progression:
        raise HTTPException(
            status_code=400, 
            detail=f"The progression is not tonal. {analysis_result.error or ''}"
        )

    try:
        image_path = visualizer_service.create_graph_from_analysis(analysis_result)
        
        if not os.path.exists(image_path):
             raise HTTPException(status_code=500, detail="Image file not found after generation.")

        return FileResponse(image_path, media_type="image/png")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred during visualization: {e}")
