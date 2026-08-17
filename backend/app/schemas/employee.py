"""Pydantic schemas for employee data and normalization."""

from pydantic import BaseModel, Field, field_validator

from backend.app.schemas.classification import BuyingRole


class EmployeeInput(BaseModel):
    """Input payload for a single employee."""

    id: str = Field(..., description="Unique employee identifier")
    name: str | None = Field(
        default=None,
        description="Employee name (optional)",
    )
    title: str = Field(
        ...,
        description="Job title (required, cannot be blank)",
    )
    department: str | None = Field(
        default=None,
        description="Department name (optional)",
    )

    @field_validator("title")
    @classmethod
    def validate_title_non_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Employee title cannot be empty or whitespace only")
        return cleaned

    @field_validator("id")
    @classmethod
    def validate_id_non_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Employee id cannot be empty or whitespace only")
        return cleaned


class NormalizedEmployee(BaseModel):
    """Employee representation with normalized title and extracted attributes."""

    id: str = Field(..., description="Employee identifier")
    name: str | None = Field(default=None, description="Employee name")
    original_title: str = Field(..., description="Original raw job title")
    normalized_title: str = Field(..., description="Standardized job title")
    department: str | None = Field(
        default=None,
        description="Assigned or inferred department",
    )
    function: str | None = Field(
        default=None,
        description="Inferred organizational function (e.g. Software Development, Finance)",
    )
    seniority: str = Field(
        ...,
        description="Seniority level label (e.g. C-Level, VP, Manager, Senior, Mid-level)",
    )
    seniority_score: int = Field(
        ...,
        ge=0,
        le=10,
        description="Numeric seniority score from 0 (Unknown) to 10 (C-Level/President)",
    )
    management_level: str = Field(
        ...,
        description="Management status (e.g. Executive, Senior Management, Middle Management, Team Lead, Individual Contributor)",
    )


class BatchTitleNormalization(BaseModel):
    """Structured LLM output for normalizing titles."""

    normalized_employees: list[NormalizedEmployee] = Field(
        ...,
        description="List of employees with normalized titles and attributes",
    )


class FinalEmployeeAnalysis(BaseModel):
    """Comprehensive analysis result for an employee."""

    id: str = Field(..., description="Employee identifier")
    name: str | None = Field(default=None, description="Employee name")
    original_title: str = Field(..., description="Original job title")
    normalized_title: str = Field(..., description="Normalized job title")
    department: str | None = Field(default=None, description="Department")
    function: str | None = Field(default=None, description="Functional area")
    seniority: str = Field(..., description="Seniority level")
    seniority_score: int = Field(..., description="Seniority score (0-10)")
    management_level: str = Field(..., description="Management level")
    reports_to: str | None = Field(
        default=None,
        description="Employee ID of direct manager, or null if root / unknown",
    )
    buying_role: BuyingRole = Field(..., description="Classified buying role")
    confidence: float = Field(..., description="Confidence score (0.0 - 1.0)")
    reason: str = Field(..., description="Concise observable reasoning")
    supporting_factors: list[str] = Field(
        default_factory=list,
        description="Observable factors supporting classification",
    )
