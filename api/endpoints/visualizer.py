import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from api.endpoints.analysis import get_analysis_service
from api.schemas.analysis_schemas import ProgressionAnalysisRequest
from api.services.analysis_service import TonalAnalysisService
from api.services.visualizer_service import VisualizerService
from core.i18n import T

router = APIRouter()


def get_visualizer_service() -> VisualizerService:
    """Dependency for the VisualizerService."""
    return VisualizerService()


@router.post(
    "/visualize",
    summary=T("endpoints.visualize.summary"),
    tags=["Visualization"],
    responses={
        200: {
            "content": {"image/png": {}},
            "description": T("endpoints.visualize.responses.200"),
        },
        400: {"description": T("endpoints.visualize.responses.400")},
    },
)
async def visualize_progression(
    request: ProgressionAnalysisRequest,
    analysis_service: TonalAnalysisService = Depends(get_analysis_service),
    visualizer_service: VisualizerService = Depends(get_visualizer_service),
) -> FileResponse:
    """
    Receives a list of chords, analyzes the progression and returns a
    visual diagram of the analysis.
    """
    analysis_result = analysis_service.analyze_progression(request)

    if not analysis_result.is_tonal_progression:
        error_detail = T("errors.progression_not_tonal")
        if analysis_result.error:
            error_detail += f" {analysis_result.error}"
        raise HTTPException(status_code=400, detail=error_detail)

    try:
        image_path = visualizer_service.create_graph_from_analysis(
            analysis_result, theme_mode=request.theme or "light"
        )

        if not os.path.exists(image_path):
            raise HTTPException(status_code=500, detail=T("errors.image_not_found"))

        return FileResponse(image_path, media_type="image/png")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=T("errors.internal_visualization_error", error=str(e))
        )
