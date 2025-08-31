from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from core.i18n import T, translate_function, translate_tonality


class ProgressionAnalysisRequest(BaseModel):
    """
    Defines the structure of the request body for progression analysis.
    """

    chords: List[str] = Field(
        ...,
        min_length=1,
        description=T("schemas.progression_analysis_request.chords.description"),
        json_schema_extra={"example": ["Em", "A", "Dm", "G", "C"]},
    )
    tonalities_to_test: Optional[List[str]] = Field(
        None,
        description=T("schemas.progression_analysis_request.tonalities_to_test.description"),
        json_schema_extra={"example": []},
    )
    theme: Optional[Literal["light", "dark"]] = Field(
        "light",
        description=T("schemas.progression_analysis_request.theme.description"),
        json_schema_extra={"example": "light"},
    )


class ExplanationStepAPI(BaseModel):
    """
    Represents a single step in the explanation derivation process.
    """

    formal_rule_applied: Optional[str] = Field(
        None, description=T("schemas.explanation_step.formal_rule_applied.description")
    )
    observation: str = Field(..., description=T("schemas.explanation_step.observation.description"))
    processed_chord: Optional[str] = Field(
        None, description=T("schemas.explanation_step.processed_chord.description")
    )
    tonality_used_in_step: Optional[str] = Field(
        None, description=T("schemas.explanation_step.tonality_used_in_step.description")
    )
    evaluated_functional_state: Optional[str] = Field(
        None, description=T("schemas.explanation_step.evaluated_functional_state.description")
    )

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain_step(cls, orm_obj: Any) -> "ExplanationStepAPI":
        """Convert from domain ExplanationStep to response DTO."""
        # Get the current locale for translations
        from core.i18n.locale_manager import locale_manager

        current_locale = locale_manager.current_locale

        return cls(
            formal_rule_applied=orm_obj.formal_rule_applied,
            observation=orm_obj.observation,
            processed_chord=orm_obj.processed_chord.name if orm_obj.processed_chord else None,
            tonality_used_in_step=(
                translate_tonality(orm_obj.tonality_used_in_step.tonality_name, current_locale)
                if orm_obj.tonality_used_in_step
                else None
            ),
            evaluated_functional_state=(
                f"{translate_function(orm_obj.evaluated_functional_state.associated_tonal_function.name, current_locale)} ({orm_obj.evaluated_functional_state.state_id})"
                if orm_obj.evaluated_functional_state
                else None
            ),
        )


class ProgressionAnalysisResponse(BaseModel):
    """
    Defines the structure of the API response.
    """

    is_tonal_progression: bool = Field(
        ..., description=T("schemas.progression_analysis_response.is_tonal_progression.description")
    )
    identified_tonality: Optional[str] = Field(
        None, description=T("schemas.progression_analysis_response.identified_tonality.description")
    )
    explanation_details: List[ExplanationStepAPI] = Field(
        [], description=T("schemas.progression_analysis_response.explanation_details.description")
    )
    error: Optional[str] = Field(
        None, description=T("schemas.progression_analysis_response.error.description")
    )
