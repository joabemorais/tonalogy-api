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
    formal_rule_applied: Optional[str] = Field(None, description="The formal rule from Aragão's model that was applied.")
    observation: str = Field(..., description="A human-readable description of what happened in this step.")
    processed_chord: Optional[str] = Field(None, description="The chord that was processed in this step.")
    tonality_used_in_step: Optional[str] = Field(None, description="The tonality that was in use during this step.")
    evaluated_functional_state: Optional[str] = Field(None, description="The functional state (e.g., 'TONIC (s_t)') that was evaluated.")
    
    model_config = ConfigDict(from_attributes=True)

class InterpretationResult(BaseModel):
    """Represents a single valid interpretation of the progression."""
    identified_key: str = Field(..., description="The initial key for this interpretation.")
    explanation_details: List[ExplanationStepAPI] = Field([], description="The detailed analysis steps for this interpretation.")

class ProgressionAnalysisResponse(BaseModel):
    """Defines the API response, which can contain multiple interpretations."""
    is_tonal_progression: bool = Field(..., description="True if at least one tonal interpretation was found.")
    possible_interpretations: List[InterpretationResult] = Field([], description="A list of all valid tonal interpretations found.")
    error: Optional[str] = Field(None, description="An error message, if any.")
