"""Domain models for employee representation."""

from dataclasses import dataclass, field


@dataclass
class EmployeeDomain:
    """Internal domain model for employee entity."""

    id: str
    name: str | None = None
    original_title: str = ""
    normalized_title: str = ""
    department: str | None = None
    function: str | None = None
    seniority: str = "Unknown"
    seniority_score: int = 0
    management_level: str = "Individual Contributor"
    reports_to: str | None = None
    buying_role: str = "Unknown"
    confidence: float = 0.0
    reason: str = ""
    supporting_factors: list[str] = field(default_factory=list)
