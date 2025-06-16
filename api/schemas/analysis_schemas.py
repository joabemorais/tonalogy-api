from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class ProgressionAnalysisRequest(BaseModel):
    """
    Defines the structure of the request body for progression analysis.
    """
    chords: List[str] = Field(
        ...,
        min_length=1,
        description="A list of chords to be analyzed.",
        json_schema_extra={"example": ["Em", "A", "Dm", "G", "C"]}
    )
    tonalities_to_test: Optional[List[str]] = Field(
        None,
        description="Optional. A list of tonalities to be tested. If omitted, the system may test against a default set.",
        json_schema_extra={"example": []}
    )

class ExplanationStepAPI(BaseModel):
    """
    Represents a single step in the explanation derivation process.
    """
    formal_rule_applied: Optional[str] = Field(..., description="The formal rule from Aragão's model that was applied.")
    observation: str = Field(..., description="A human-readable description of what happened in this step.")
    processed_chord: Optional[str] = Field(None, description="The chord that was processed in this step.")
    tonality_used_in_step: Optional[str] = Field(None, description="The tonality that was in use during this step.")
    evaluated_functional_state: Optional[str] = Field(None, description="The functional state (e.g., 'TONIC (s_t)') that was evaluated.")
    
    model_config = ConfigDict(from_attributes=True)

class ProgressionAnalysisResponse(BaseModel):
    """
    Defines the structure of the API response.
    """
    is_tonal_progression: bool = Field(..., description="True if the progression is tonal, False otherwise.")
    identified_tonality: Optional[str] = Field(None, description="The tonality in which the progression was identified as tonal.")
    explanation_details: List[ExplanationStepAPI] = Field([], description="A detailed list of analysis steps.")
    error: Optional[str] = Field(None, description="An error message, if any.")
