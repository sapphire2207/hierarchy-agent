"""Pydantic schemas for buying-role classification."""

from enum import Enum

from pydantic import BaseModel, Field


class BuyingRole(str, Enum):
    """B2B Buying roles as defined in standard sales qualification frameworks."""

    ECONOMIC_BUYER = "Economic Buyer"
    CHAMPION = "Champion"
    INFLUENCER = "Influencer"
    USER = "User"
    UNKNOWN = "Unknown"


class RoleClassification(BaseModel):
    """Classification of a single employee into a buying role."""

    employee_id: str = Field(..., description="Unique employee identifier")
    buying_role: BuyingRole = Field(..., description="Inferred buying role")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated confidence score between 0.0 and 1.0",
    )
    reason: str = Field(
        ...,
        description="Concise observable justification for role classification",
    )
    supporting_factors: list[str] = Field(
        default_factory=list,
        description="Key factors influencing this classification",
    )


class BatchRoleClassification(BaseModel):
    """Structured LLM output for batch role classification."""

    roles: list[RoleClassification] = Field(
        ...,
        description="Role classifications for all provided employees",
    )
