from fastapi import FastAPI
from pathlib import Path
from typing import Dict

# Import the router from our endpoint
from api.endpoints import analysis
# Import the service layer and knowledge base
from api.services.analysis_service import TonalAnalysisService
from core.config.knowledge_base import TonalKnowledgeBase

# --- Application Configuration ---
app = FastAPI(
    title="Tonalogy API",
    description="An API for analyzing tonal harmonic progressions using Kripke Semantics.",
    version="1.0.0"
)

# --- Loading and Dependency Injection ---

# Load the knowledge base ONCE when the application starts.
# This ensures we're not reading JSON files on every request.
BASE_DIR = Path(__file__).resolve().parent.parent 
KRIPKE_CONFIG_PATH = BASE_DIR / "core" / "config" / "data" / "kripke_structure.json"
TONALITIES_CONFIG_PATH = BASE_DIR / "core" / "config" / "data" / "tonalities.json"

# Instantiate our knowledge base
# Error handling if configuration files are not found
try:
    knowledge_base: TonalKnowledgeBase = TonalKnowledgeBase(KRIPKE_CONFIG_PATH, TONALITIES_CONFIG_PATH)
except IOError as e:
    print(f"FATAL ERROR: Could not load configuration files. {e}")
    raise e

# Instantiate our service with the loaded knowledge base
tonal_analysis_service: TonalAnalysisService = TonalAnalysisService(knowledge_base)

# Dependency function that FastAPI will use
# Simply returns the service instance we already created.
def get_analysis_service_override() -> TonalAnalysisService:
    return tonal_analysis_service

# Replace the placeholder function in our router with our real implementation
app.dependency_overrides[analysis.get_analysis_service] = get_analysis_service_override

# Include the router in our main application
app.include_router(analysis.router)


# --- Root Route (Optional, for health check) ---
@app.get("/", tags=["Root"])
async def read_root() -> Dict[str, str]:
    return {
        "message": "Welcome to Tonalogy API. Visit /docs to see the API documentation."
    }
