"""LLM service providing unified access to structured LLM outputs across providers."""

import json
from typing import Any

from pydantic import BaseModel

from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import logger
from backend.app.schemas.classification import (
    BatchRoleClassification,
    BuyingRole,
    RoleClassification,
)
from backend.app.schemas.employee import (
    BatchTitleNormalization,
    NormalizedEmployee,
)
from backend.app.schemas.hierarchy import (
    BatchHierarchyInference,
    HierarchyRelationship,
)
from backend.app.utils.title_utils import (
    extract_seniority_info,
    infer_department_and_function,
    normalize_title_deterministic,
)


class MockStructuredLLM:
    """
    Mock LLM implementation for offline testing, local development, and deterministic evaluation.
    Produces structured Pydantic outputs using sophisticated heuristic reasoning.
    """

    def __init__(self, schema: type[BaseModel]):
        self.schema = schema

    def invoke(self, messages: list[Any]) -> BaseModel:
        # Extract prompt content from the latest user message first, then all messages
        user_content = ""
        for msg in reversed(messages):
            if hasattr(msg, "content"):
                user_content += f"\n{msg.content}"
            elif isinstance(msg, dict):
                user_content += f"\n{msg.get('content', '')}"
            elif isinstance(msg, tuple) and len(msg) >= 2:
                user_content += f"\n{msg[1]}"
            elif isinstance(msg, str):
                user_content += f"\n{msg}"

        if self.schema == BatchTitleNormalization:
            return self._mock_normalization(user_content)
        elif self.schema == BatchHierarchyInference:
            return self._mock_hierarchy(user_content)
        elif self.schema == BatchRoleClassification:
            return self._mock_roles(user_content)
        else:
            raise ValueError(f"Unsupported mock schema: {self.schema}")

    def _extract_json_from_prompt(self, prompt: str) -> Any | None:
        # Search all valid JSON array structures in the prompt
        start_indices = [i for i, ch in enumerate(prompt) if ch == "["]
        end_indices = [i for i, ch in enumerate(prompt) if ch == "]"]

        for s in reversed(start_indices):
            for e in reversed(end_indices):
                if e > s:
                    candidate = prompt[s : e + 1]
                    try:
                        parsed = json.loads(candidate)
                        if (
                            isinstance(parsed, list)
                            and len(parsed) > 0
                            and isinstance(parsed[0], dict)
                        ):
                            return parsed
                    except Exception:
                        pass
        return None

    def _mock_normalization(self, prompt: str) -> BatchTitleNormalization:
        data = self._extract_json_from_prompt(prompt) or []
        normalized_list = []

        for item in data:
            emp_id = str(item.get("id", ""))
            name = item.get("name")
            raw_title = item.get("title", "")
            raw_dept = item.get("department")

            norm_title = normalize_title_deterministic(raw_title)
            seniority, score, mgmt_level = extract_seniority_info(raw_title)
            dept, func = infer_department_and_function(raw_title, raw_dept)

            normalized_list.append(
                NormalizedEmployee(
                    id=emp_id,
                    name=name,
                    original_title=raw_title,
                    normalized_title=norm_title,
                    department=dept,
                    function=func,
                    seniority=seniority,
                    seniority_score=score,
                    management_level=mgmt_level,
                )
            )

        return BatchTitleNormalization(normalized_employees=normalized_list)

    def _mock_hierarchy(self, prompt: str) -> BatchHierarchyInference:
        data = self._extract_json_from_prompt(prompt) or []
        if not data:
            return BatchHierarchyInference(relationships=[])

        # Sort employees by seniority score descending
        employees = sorted(data, key=lambda x: x.get("seniority_score", 0), reverse=True)

        # Identify executive root (e.g. CEO or highest seniority)
        ceo_candidates = [
            e
            for e in employees
            if "chief executive officer" in (e.get("normalized_title", "") or "").lower()
            or "ceo" in (e.get("original_title", "") or "").lower()
        ]
        top_root = ceo_candidates[0] if ceo_candidates else employees[0]
        top_root_id = str(top_root.get("id"))

        relationships: list[HierarchyRelationship] = []

        for emp in employees:
            emp_id = str(emp.get("id"))
            dept = (emp.get("department") or "").lower()
            score = emp.get("seniority_score", 0)

            if emp_id == top_root_id:
                relationships.append(
                    HierarchyRelationship(
                        employee_id=emp_id,
                        parent_id=None,
                        relationship_confidence=0.98,
                        reason=f"Identified as top-level executive / root ({emp.get('normalized_title')}).",
                    )
                )
                continue

            # Look for supervisor in same department with higher seniority score
            dept_superiors = [
                e
                for e in employees
                if str(e.get("id")) != emp_id
                and e.get("seniority_score", 0) > score
                and (
                    (e.get("department") or "").lower() == dept
                    or "executive" in (e.get("department") or "").lower()
                    or e.get("seniority_score", 0) >= 9
                )
            ]

            # Sort dept superiors by score ascending (closest direct superior above this employee)
            dept_superiors = sorted(dept_superiors, key=lambda x: x.get("seniority_score", 0))

            if dept_superiors:
                parent = dept_superiors[0]
                parent_id = str(parent.get("id"))
                parent_title = parent.get("normalized_title")
                relationships.append(
                    HierarchyRelationship(
                        employee_id=emp_id,
                        parent_id=parent_id,
                        relationship_confidence=0.88,
                        reason=f"{emp.get('normalized_title')} reports to immediate departmental leader {parent_title}.",
                    )
                )
            else:
                # If no direct departmental supervisor found, report to top root
                relationships.append(
                    HierarchyRelationship(
                        employee_id=emp_id,
                        parent_id=top_root_id,
                        relationship_confidence=0.75,
                        reason=f"Reports directly to executive leadership ({top_root.get('normalized_title')}).",
                    )
                )

        return BatchHierarchyInference(relationships=relationships)

    def _mock_roles(self, prompt: str) -> BatchRoleClassification:
        data = self._extract_json_from_prompt(prompt) or []
        roles: list[RoleClassification] = []

        for item in data:
            emp_id = str(item.get("id"))
            norm_title = (item.get("normalized_title") or item.get("title") or "").lower()
            dept = (item.get("department") or "").lower()
            mgmt = (item.get("management_level") or "").lower()
            score = item.get("seniority_score", 0)

            # Classify Buying Role
            if any(
                k in norm_title
                for k in ["cfo", "chief financial officer", "finance director", "vp finance"]
            ) or ("finance" in dept and score >= 8):
                roles.append(
                    RoleClassification(
                        employee_id=emp_id,
                        buying_role=BuyingRole.ECONOMIC_BUYER,
                        confidence=0.92,
                        reason="Controls organizational budget, financial authorizations, and final purchasing commitments.",
                        supporting_factors=[
                            "Financial Oversight",
                            "Executive Budget Authority",
                            "Sign-off Responsibility",
                        ],
                    )
                )
            elif any(
                k in norm_title
                for k in [
                    "vp engineering",
                    "head of engineering",
                    "vp technology",
                    "director of engineering",
                    "director engineering",
                ]
            ) or (
                score in [7, 8] and any(d in dept for d in ["engineering", "technology", "product"])
            ):
                roles.append(
                    RoleClassification(
                        employee_id=emp_id,
                        buying_role=BuyingRole.CHAMPION,
                        confidence=0.89,
                        reason="Senior domain leader who actively champions tools that improve departmental productivity and efficiency.",
                        supporting_factors=[
                            "Departmental Leadership",
                            "Operational Alignment",
                            "Internal Influence",
                        ],
                    )
                )
            elif any(
                k in norm_title
                for k in [
                    "cto",
                    "chief technology officer",
                    "procurement",
                    "architect",
                    "ciso",
                    "security",
                    "engineering manager",
                ]
            ) or ("procurement" in dept or "management" in mgmt or score in [4, 5, 10]):
                roles.append(
                    RoleClassification(
                        employee_id=emp_id,
                        buying_role=BuyingRole.INFLUENCER,
                        confidence=0.85,
                        reason="Provides technical validation, procurement criteria, or strategic architectural requirements.",
                        supporting_factors=[
                            "Technical Evaluation",
                            "Governance & Compliance",
                            "Key Stakeholder",
                        ],
                    )
                )
            elif any(
                k in norm_title
                for k in [
                    "software engineer",
                    "developer",
                    "analyst",
                    "specialist",
                    "designer",
                    "associate",
                ]
            ):
                roles.append(
                    RoleClassification(
                        employee_id=emp_id,
                        buying_role=BuyingRole.USER,
                        confidence=0.82,
                        reason="Hands-on technical contributor who will directly interact with and utilize the tooling daily.",
                        supporting_factors=[
                            "Hands-on Practitioner",
                            "Daily Workflow Consumer",
                            "Direct End User",
                        ],
                    )
                )
            elif any(k in norm_title for k in ["ceo", "chief executive officer", "president"]):
                roles.append(
                    RoleClassification(
                        employee_id=emp_id,
                        buying_role=BuyingRole.ECONOMIC_BUYER,
                        confidence=0.80,
                        reason="Executive leadership with overarching commercial sign-off and strategic decision ownership.",
                        supporting_factors=["Executive Leadership", "Final Decision Authority"],
                    )
                )
            else:
                roles.append(
                    RoleClassification(
                        employee_id=emp_id,
                        buying_role=BuyingRole.UNKNOWN,
                        confidence=0.45,
                        reason="Insufficient contextual evidence to definitively classify buying role with high confidence.",
                        supporting_factors=["Ambiguous Title", "Limited Context"],
                    )
                )

        return BatchRoleClassification(roles=roles)


class LLMService:
    """Service for managing LLM provider lifecycle and structured outputs."""

    def __init__(self, custom_settings: Settings | None = None):
        self.settings = custom_settings or get_settings()

    def get_structured_llm(self, schema: type[BaseModel]) -> Any:
        """
        Returns a runnable LLM configured with structured output for the provided Pydantic schema.
        Falls back to MockStructuredLLM if provider is 'mock' or API key is not supplied.
        """
        provider = self.settings.llm_provider.lower().strip()

        # If mock provider or no API key provided in dev/test, use deterministic MockStructuredLLM
        if provider == "mock" or not self.settings.llm_api_key:
            logger.info(f"Using MockStructuredLLM for schema '{schema.__name__}'")
            return MockStructuredLLM(schema=schema)

        try:
            if provider == "openai":
                from langchain_openai import ChatOpenAI

                base_llm = ChatOpenAI(
                    model=self.settings.llm_model,
                    api_key=self.settings.llm_api_key,
                    base_url=self.settings.llm_base_url,
                    temperature=self.settings.llm_temperature,
                )
                return base_llm.with_structured_output(schema)

            elif provider in ["google", "google_genai", "gemini"]:
                from langchain_google_genai import ChatGoogleGenerativeAI

                base_llm = ChatGoogleGenerativeAI(
                    model=self.settings.llm_model,
                    google_api_key=self.settings.llm_api_key,
                    temperature=self.settings.llm_temperature,
                )
                return base_llm.with_structured_output(schema)

            else:
                logger.warning(
                    f"Unsupported or unconfigured LLM provider '{provider}'. Falling back to MockStructuredLLM."
                )
                return MockStructuredLLM(schema=schema)

        except Exception as exc:
            logger.error(
                f"Failed to initialize LLM provider '{provider}': {exc}. Falling back to MockStructuredLLM."
            )
            return MockStructuredLLM(schema=schema)


def get_llm_service() -> LLMService:
    """Factory function for LLMService."""
    return LLMService()
