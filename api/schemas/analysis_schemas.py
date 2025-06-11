from typing import List, Optional
from pydantic import BaseModel, Field

class ProgressionAnalysisRequest(BaseModel):
    """
    Defines the structure of the request body for progression analysis.
    """
    chords: List[str] = Field(
        ...,
        min_items=1,
        example=["C", "G", "Dm", "A7", "Em"],
        description="A list of chords to be analyzed."
    )
    keys_to_test: Optional[List[str]] = Field(
        None,
        example=["C Major", "G Major", "A minor"],
        description="Optional. A list of keys to be tested. If omitted, the system may test against a default set."
    )

class ExplanationStepAPI(BaseModel):
    """
    Represents a single step in the explanation derivation process.
    """
    formal_rule_applied: str = Field(..., description="The formal rule from Aragão's model that was applied.")
    observation: str = Field(..., description="A human-readable description of what happened in this step.")
    processed_chord: Optional[str] = Field(None, description="The chord that was processed in this step.")
    key_used_in_step: Optional[str] = Field(None, description="The key that was in use during this step.")
    evaluated_functional_state: Optional[str] = Field(None, description="The functional state (e.g., 'TONIC (s_t)') that was evaluated.")
    
    class Config:
        # Pydantic V2 uses `from_attributes` instead of `orm_mode`
        from_attributes = True

class ProgressionAnalysisResponse(BaseModel):
    """
    Defines the structure of the API response.
    """
    is_tonal_progression: bool = Field(..., description="True if the progression is tonal, False otherwise.")
    identified_key: Optional[str] = Field(None, description="The key in which the progression was identified as tonal.")
    explanation_details: List[ExplanationStepAPI] = Field([], description="A detailed list of analysis steps.")
    error: Optional[str] = Field(None, description="An error message, if any.")
