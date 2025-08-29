from typing import Any, List, Optional, Literal

from pydantic import BaseModel, ConfigDict, Field


class ProgressionAnalysisRequest(BaseModel):
    """
    Defines the structure of the request body for progression analysis.
    """

    chords: List[str] = Field(
        ...,
        min_length=1,
        description="A list of chords to be analyzed.",
        json_schema_extra={"example": ["Em", "A", "Dm", "G", "C"]},
    )
    tonalities_to_test: Optional[List[str]] = Field(
        None,
        description="Optional. A list of tonalities to be tested.",
        json_schema_extra={"example": []},
    )
    theme: Optional[Literal["light", "dark"]] = Field(
        "light",
        description="Theme mode for visualization - 'light' or 'dark'.",
        json_schema_extra={"example": "light"},
    )


class ExplanationStepAPI(BaseModel):
    """
    Represents a single step in the explanation derivation process.
    """

    formal_rule_applied: Optional[str] = Field(
        None, description="The formal model rule that was applied."
    )
    observation: str = Field(
        ..., description="A readable description of what happened in this step."
    )
    processed_chord: Optional[str] = Field(
        None, description="The chord that was processed in this step."
    )
    tonality_used_in_step: Optional[str] = Field(
        None, description="The tonality in use during this step."
    )
    evaluated_functional_state: Optional[str] = Field(
        None, description="The evaluated functional state (e.g., 'TONIC (s_t)')."
    )

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, orm_obj: Any) -> "ExplanationStepAPI":
        """Converts an ORM-like object to the Pydantic schema."""
        return cls(
            formal_rule_applied=orm_obj.formal_rule_applied,
            observation=orm_obj.observation,
            processed_chord=orm_obj.processed_chord.name if orm_obj.processed_chord else None,
            tonality_used_in_step=(
                orm_obj.tonality_used_in_step.tonality_name
                if orm_obj.tonality_used_in_step
                else None
            ),
            evaluated_functional_state=(
                f"{orm_obj.evaluated_functional_state.associated_tonal_function.name} ({orm_obj.evaluated_functional_state.state_id})"
                if orm_obj.evaluated_functional_state
                else None
            ),
        )


class ProgressionAnalysisResponse(BaseModel):
    """
    Defines the structure of the API response.
    """

    is_tonal_progression: bool = Field(
        ..., description="True if the progression is tonal, false otherwise."
    )
    identified_tonality: Optional[str] = Field(
        None, description="The tonality in which the progression was identified as tonal."
    )
    explanation_details: List[ExplanationStepAPI] = Field(
        [], description="A detailed list of analysis steps."
    )
    error: Optional[str] = Field(None, description="An error message, if any.")
