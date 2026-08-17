"""Unit tests for title normalization and seniority extraction."""

from backend.app.utils.title_utils import (
    extract_seniority_info,
    infer_department_and_function,
    normalize_title_deterministic,
)


def test_abbreviation_normalization():
    """Tests standard abbreviation expansions."""
    assert normalize_title_deterministic("VP Eng.") == "Vice President of Engineering"
    assert normalize_title_deterministic("VP Engineering") == "Vice President of Engineering"
    assert (
        normalize_title_deterministic("Vice President Engineering")
        == "Vice President of Engineering"
    )
    assert (
        normalize_title_deterministic("Vice-President of Engineering")
        == "Vice President of Engineering"
    )

    assert normalize_title_deterministic("Sr. SWE") == "Senior Software Engineer"
    assert normalize_title_deterministic("Senior SWE") == "Senior Software Engineer"
    assert normalize_title_deterministic("Sr Software Engineer") == "Senior Software Engineer"

    assert normalize_title_deterministic("Dir. Engineering") == "Director of Engineering"
    assert normalize_title_deterministic("Eng Manager") == "Engineering Manager"


def test_seniority_extraction():
    """Tests seniority level and score extraction across titles."""
    label, score, mgmt = extract_seniority_info("CEO")
    assert label == "C-Level"
    assert score == 10
    assert mgmt == "Executive"

    label, score, mgmt = extract_seniority_info("Chief Technology Officer")
    assert label == "C-Level"
    assert score == 10
    assert mgmt == "Executive"

    label, score, mgmt = extract_seniority_info("President")
    assert label == "President"
    assert score == 10
    assert mgmt == "Executive"

    label, score, mgmt = extract_seniority_info("Vice President of Engineering")
    assert label == "VP"
    assert score == 8
    assert mgmt == "Executive"

    label, score, mgmt = extract_seniority_info("Director of Engineering")
    assert label == "Director"
    assert score == 7
    assert mgmt == "Senior Management"

    label, score, mgmt = extract_seniority_info("Engineering Manager")
    assert label == "Manager"
    assert score == 5
    assert mgmt == "Middle Management"

    label, score, mgmt = extract_seniority_info("Tech Lead")
    assert label == "Lead"
    assert score == 4
    assert mgmt == "Team Lead"

    label, score, mgmt = extract_seniority_info("Senior Software Engineer")
    assert label == "Senior"
    assert score == 3
    assert mgmt == "Individual Contributor"

    label, score, mgmt = extract_seniority_info("Software Engineer")
    assert label == "Mid-level"
    assert score == 2
    assert mgmt == "Individual Contributor"

    label, score, mgmt = extract_seniority_info("Junior Software Engineer")
    assert label == "Junior"
    assert score == 1
    assert mgmt == "Individual Contributor"


def test_department_and_function_inference():
    """Tests department and function derivation."""
    dept, func = infer_department_and_function("Senior Software Engineer", None)
    assert dept == "Engineering"
    assert func == "Software Development"

    dept, func = infer_department_and_function("Procurement Manager", "Procurement")
    assert dept == "Procurement"
    assert "Procurement" in func

    dept, func = infer_department_and_function("Chief Financial Officer", None)
    assert dept == "Finance"
    assert "Executive" in func or "Finance" in func
