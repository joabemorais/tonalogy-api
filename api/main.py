from fastapi import FastAPI
from pathlib import Path
from typing import Dict
import uvicorn

from api.endpoints import analysis, visualizer 

from api.services.analysis_service import TonalAnalysisService
from core.config.knowledge_base import TonalKnowledgeBase

app = FastAPI(
    title="Tonalogy API",
    description="An API for analysis and visualization of tonal harmonic progressions using Kripke Semantics.",
    version="2.0.0"
)

BASE_DIR = Path(__file__).resolve().parent.parent
KRIPKE_CONFIG_PATH = BASE_DIR / "core" / "config" / "data" / "kripke_structure.json"
TONALITIES_CONFIG_PATH = BASE_DIR / "core" / "config" / "data" / "tonalities.json"

try:
    knowledge_base: TonalKnowledgeBase = TonalKnowledgeBase(KRIPKE_CONFIG_PATH, TONALITIES_CONFIG_PATH)
except IOError as e:
    print(f"FATAL ERROR: Could not load configuration files. {e}")
    raise e

tonal_analysis_service: TonalAnalysisService = TonalAnalysisService(knowledge_base)

def get_analysis_service_override() -> TonalAnalysisService:
    return tonal_analysis_service

# Replaces the placeholder function in our routers with the real implementation
app.dependency_overrides[analysis.get_analysis_service] = get_analysis_service_override
app.dependency_overrides[visualizer.get_analysis_service] = get_analysis_service_override

# Includes the routers in the main application
app.include_router(analysis.router)
app.include_router(visualizer.router)

# --- Root Route ---
@app.get("/", tags=["Root"])
async def read_root() -> Dict[str, str]:
    return {
        "message": "Welcome to Tonalogy API. Visit /docs to see the API documentation."
    }


def main():
    """Entry point for the tonalogy-api script."""
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
