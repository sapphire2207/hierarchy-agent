"""Pydantic schemas for hierarchy inference and final API response."""

from pydantic import BaseModel, Field, field_validator

from backend.app.schemas.employee import EmployeeInput, FinalEmployeeAnalysis


class HierarchyRelationship(BaseModel):
    """Parent-child reporting relationship between employees."""

    employee_id: str = Field(..., description="Employee identifier")
    parent_id: str | None = Field(
        default=None,
        description="Employee ID of the supervisor/manager, or null if root",
    )
    relationship_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for this reporting relationship (0.0 to 1.0)",
    )
    reason: str = Field(
        ...,
        description="Concise rationale for this reporting relationship",
    )


class BatchHierarchyInference(BaseModel):
    """Structured LLM output for holistic hierarchy inference."""

    relationships: list[HierarchyRelationship] = Field(
        ...,
        description="Inferred reporting relationships for all employees",
    )


class HierarchyAnalyzeRequest(BaseModel):
    """Request schema for hierarchy and buying-role analysis."""

    company: str | None = Field(
        default="Unknown Company",
        description="Name of the company or organization",
    )
    employees: list[EmployeeInput] = Field(
        ...,
        description="List of employees to analyze (must not be empty)",
    )

    @field_validator("employees")
    @classmethod
    def validate_employees(cls, v: list[EmployeeInput]) -> list[EmployeeInput]:
        if not v:
            raise ValueError("Employee list cannot be empty")

        ids = [emp.id for emp in v]
        if len(ids) != len(set(ids)):
            seen = set()
            duplicates = []
            for emp_id in ids:
                if emp_id in seen:
                    duplicates.append(emp_id)
                seen.add(emp_id)
            raise ValueError(f"Duplicate employee IDs found: {list(set(duplicates))}")

        return v


class AnalysisMetadata(BaseModel):
    """Operational and validation metadata for the hierarchy analysis."""

    total_employees: int = Field(..., description="Total number of analyzed employees")
    root_count: int = Field(..., description="Number of root-level individuals identified")
    execution_time_ms: float | None = Field(
        default=None,
        description="Total execution time in milliseconds",
    )
    retry_count: int = Field(
        default=0,
        description="Number of validation retries during analysis",
    )
    is_valid: bool = Field(
        default=True,
        description="Whether the output satisfies all structural validation rules",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Semantic or structural warnings generated during validation",
    )


class FinalHierarchyResponse(BaseModel):
    """Complete structured response for organizational hierarchy and buying roles."""

    company: str | None = Field(
        default=None,
        description="Company or organization name",
    )
    people: list[FinalEmployeeAnalysis] = Field(
        ...,
        description="List of analyzed employees with roles and hierarchy",
    )
    root_employee_ids: list[str] = Field(
        ...,
        description="IDs of employees at the top of the hierarchy tree/forest",
    )
    analysis_metadata: AnalysisMetadata = Field(
        ...,
        description="Metadata and validation information",
    )
