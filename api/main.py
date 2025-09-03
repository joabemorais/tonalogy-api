from pathlib import Path
from typing import Dict

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.endpoints import analysis, visualizer
from api.services.analysis_service import TonalAnalysisService
from core.config.knowledge_base import TonalKnowledgeBase
from core.i18n import T

try:
    from core.i18n.middleware import I18nMiddleware

    MIDDLEWARE_AVAILABLE = True
except ImportError:
    MIDDLEWARE_AVAILABLE = False

app = FastAPI(
    title=T("api.title"),
    description=T("api.description"),
    version="2.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tonalogy-interface.onrender.com",  # Production frontend
        "http://localhost:3000",  # Local development
        "http://127.0.0.1:3000",  # Alternative local address
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Add i18n middleware (temporarily disabled for testing)
# if MIDDLEWARE_AVAILABLE:
#     try:
#         app.add_middleware(I18nMiddleware)
#     except Exception as e:
#         print(f"Warning: Could not add I18nMiddleware: {e}")

BASE_DIR = Path(__file__).resolve().parent.parent
KRIPKE_CONFIG_PATH = BASE_DIR / "core" / "config" / "data" / "kripke_structure.json"
TONALITIES_CONFIG_PATH = BASE_DIR / "core" / "config" / "data" / "tonalities.json"

try:
    knowledge_base: TonalKnowledgeBase = TonalKnowledgeBase(
        KRIPKE_CONFIG_PATH, TONALITIES_CONFIG_PATH
    )
except IOError as e:
    print(T("errors.fatal_config_error", error=str(e)))
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
    return {"message": T("api.welcome_message")}


# --- Health Check Route ---
@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """Health check endpoint for deployment verification."""
    return {"status": "healthy", "message": "API is running"}


def main() -> None:
    """Entry point for the tonalogy-api script."""
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")


if __name__ == "__main__":
    main()
