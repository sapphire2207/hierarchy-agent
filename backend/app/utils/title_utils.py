"""Deterministic title parsing, normalization, attribute extraction, and hierarchy graph utilities."""

import re

# Common title abbreviation expansions
ABBREVIATION_MAP = {
    r"\bvp\b": "Vice President",
    r"\bv\.p\.\b": "Vice President",
    r"\bsvp\b": "Senior Vice President",
    r"\bs\.v\.p\.\b": "Senior Vice President",
    r"\bevp\b": "Executive Vice President",
    r"\be\.v\.p\.\b": "Executive Vice President",
    r"\bsr\b\.?": "Senior",
    r"\bjr\b\.?": "Junior",
    r"\bdir\b\.?": "Director",
    r"\bmgr\b\.?": "Manager",
    r"\beng\b\.?": "Engineering",
    r"\bengr\b\.?": "Engineer",
    r"\bswe\b": "Software Engineer",
    r"\bsde\b": "Software Development Engineer",
    r"\bpm\b": "Product Manager",
    r"\btpm\b": "Technical Product Manager",
    r"\bassoc\b\.?": "Associate",
    r"\bexec\b\.?": "Executive",
    r"\btech\b\.?": "Technical",
    r"\bdev\b\.?": "Developer",
    r"\bhr\b": "Human Resources",
    r"\bqa\b": "Quality Assurance",
    r"\bqc\b": "Quality Control",
    r"\bsre\b": "Site Reliability Engineer",
    r"\bsec\b\.?": "Security",
    r"\bops\b": "Operations",
    r"\bfin\b\.?": "Finance",
    r"\bacct\b\.?": "Accountant",
    r"\badmin\b\.?": "Administrator",
    r"\bcoo\b": "Chief Operating Officer",
    r"\bceo\b": "Chief Executive Officer",
    r"\bcto\b": "Chief Technology Officer",
    r"\bcfo\b": "Chief Financial Officer",
    r"\bcmo\b": "Chief Marketing Officer",
    r"\bcro\b": "Chief Revenue Officer",
    r"\bciso\b": "Chief Information Security Officer",
    r"\bcio\b": "Chief Information Officer",
}

# Standardized full titles for exact matches
CANONICAL_TITLES = {
    "ceo": "Chief Executive Officer",
    "cto": "Chief Technology Officer",
    "cfo": "Chief Financial Officer",
    "coo": "Chief Operating Officer",
    "cmo": "Chief Marketing Officer",
    "cro": "Chief Revenue Officer",
    "ciso": "Chief Information Security Officer",
    "cio": "Chief Information Officer",
    "president": "President",
}

# Seniority Taxonomy and Scoring
SENIORITY_SCORES: dict[str, int] = {
    "C-Level": 10,
    "President": 10,
    "EVP": 9,
    "SVP": 9,
    "VP": 8,
    "Senior Director": 8,
    "Director": 7,
    "Head": 7,
    "Manager": 5,
    "Lead": 4,
    "Senior": 3,
    "Mid-level": 2,
    "Junior": 1,
    "Unknown": 0,
}


def clean_whitespace(text: str) -> str:
    """Collapses duplicate whitespace characters."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def normalize_title_deterministic(title: str) -> str:
    """
    Applies rule-based deterministic normalization to job titles.
    Expands common abbreviations, standardizes connectors, and formats casing.
    """
    if not title:
        return ""

    raw = clean_whitespace(title)
    lower_raw = raw.lower().replace(".", "").strip()

    # Check exact canonical titles first
    if lower_raw in CANONICAL_TITLES:
        return CANONICAL_TITLES[lower_raw]

    # Pre-process common hyphenated variations like Vice-President
    processed = re.sub(r"\bvice[\s-]+president\b", "Vice President", raw, flags=re.IGNORECASE)

    # Replace known abbreviations
    for pattern, replacement in ABBREVIATION_MAP.items():
        processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)

    # Standardize phrasing like "Vice President Engineering" -> "Vice President of Engineering"
    processed = re.sub(
        r"\bVice President\s+(?!of\b)(.+)",
        r"Vice President of \1",
        processed,
        flags=re.IGNORECASE,
    )

    # Standardize phrasing like "Director Engineering" -> "Director of Engineering"
    processed = re.sub(
        r"\bDirector\s+(?!of\b)(.+)",
        r"Director of \1",
        processed,
        flags=re.IGNORECASE,
    )

    # Standardize phrasing like "Head Engineering" -> "Head of Engineering"
    processed = re.sub(
        r"\bHead\s+(?!of\b)(.+)",
        r"Head of \1",
        processed,
        flags=re.IGNORECASE,
    )

    # Clean up duplicate 'of of' or spacing
    processed = re.sub(r"\bof\s+of\b", "of", processed, flags=re.IGNORECASE)
    processed = clean_whitespace(processed)

    # Title-case capitalizing words except minor prepositions
    words = processed.split(" ")
    title_cased_words = []
    minor_words = {"of", "and", "the", "for", "in", "to", "at", "with"}

    for i, word in enumerate(words):
        w_lower = word.lower()
        if i > 0 and w_lower in minor_words:
            title_cased_words.append(w_lower)
        else:
            title_cased_words.append(word.capitalize())

    return " ".join(title_cased_words)


def extract_seniority_info(title: str) -> tuple[str, int, str]:
    """
    Extracts (seniority_label, seniority_score, management_level) based on title patterns.
    """
    norm = normalize_title_deterministic(title).lower()

    # C-Level & President
    if (
        re.search(r"\bchief\s+\w+\s+officer\b", norm)
        or re.search(r"\b(ceo|cto|cfo|coo|cmo|cro|ciso|cio)\b", norm)
        or re.search(r"\bc-level\b", norm)
    ):
        return "C-Level", 10, "Executive"

    if re.search(r"\bpresident\b", norm) and not re.search(r"\bvice\s+president\b", norm):
        return "President", 10, "Executive"

    # Executive VP / Senior VP
    if re.search(r"\bexecutive\s+vice\s+president\b", norm) or re.search(r"\bevp\b", norm):
        return "EVP", 9, "Executive"

    if re.search(r"\bsenior\s+vice\s+president\b", norm) or re.search(r"\bsvp\b", norm):
        return "SVP", 9, "Executive"

    # Senior Director
    if re.search(r"\bsenior\s+director\b", norm) or re.search(r"\bsr\.?\s+director\b", norm):
        return "Senior Director", 8, "Senior Management"

    # VP
    if re.search(r"\bvice\s+president\b", norm) or re.search(r"\bvp\b", norm):
        return "VP", 8, "Executive"

    # Director / Head
    if re.search(r"\bdirector\b", norm):
        return "Director", 7, "Senior Management"

    if re.search(r"\bhead\s+of\b", norm) or re.search(r"\bhead\b", norm):
        return "Head", 7, "Senior Management"

    # Manager
    if re.search(r"\bmanager\b", norm) or re.search(r"\bmanagement\b", norm):
        return "Manager", 5, "Middle Management"

    # Lead / Principal
    if (
        re.search(r"\blead\b", norm)
        or re.search(r"\bprincipal\b", norm)
        or re.search(r"\barchitect\b", norm)
    ):
        return "Lead", 4, "Team Lead"

    # Senior / Staff
    if re.search(r"\bsenior\b", norm) or re.search(r"\bstaff\b", norm):
        return "Senior", 3, "Individual Contributor"

    # Junior / Entry / Associate / Intern
    if (
        re.search(r"\bjunior\b", norm)
        or re.search(r"\bassociate\b", norm)
        or re.search(r"\bintern\b", norm)
        or re.search(r"\bentry\b", norm)
        or re.search(r"\bgraduate\b", norm)
    ):
        return "Junior", 1, "Individual Contributor"

    # Mid-level default if specific role noun found
    if any(
        kw in norm
        for kw in [
            "engineer",
            "developer",
            "specialist",
            "analyst",
            "designer",
            "consultant",
            "administrator",
            "officer",
            "coordinator",
            "representative",
            "executive",
            "scientist",
        ]
    ):
        return "Mid-level", 2, "Individual Contributor"

    return "Unknown", 0, "Individual Contributor"


def infer_department_and_function(
    title: str, department_hint: str | None = None
) -> tuple[str, str]:
    """
    Infers department and functional domain from job title and optional department hint.
    """
    t_lower = title.lower()
    dept_lower = (department_hint or "").lower()

    # If department is explicitly provided, prioritize it
    if department_hint and department_hint.strip():
        inferred_dept = department_hint.strip()
    else:
        # Infer department from title
        if any(
            w in t_lower
            for w in [
                "software",
                "swe",
                "developer",
                "engineering",
                "architect",
                "devops",
                "sre",
                "frontend",
                "backend",
                "cloud",
            ]
        ):
            inferred_dept = "Engineering"
        elif any(w in t_lower for w in ["product", "ux", "ui", "design"]):
            inferred_dept = "Product"
        elif any(
            w in t_lower
            for w in ["finance", "financial", "accounting", "cfo", "controller", "treasury"]
        ):
            inferred_dept = "Finance"
        elif any(
            w in t_lower for w in ["sales", "account executive", "sdr", "bdr", "cro", "revenue"]
        ):
            inferred_dept = "Sales"
        elif any(w in t_lower for w in ["marketing", "cmo", "content", "growth", "seo", "brand"]):
            inferred_dept = "Marketing"
        elif any(
            w in t_lower for w in ["procurement", "purchasing", "sourcing", "buyer", "supply"]
        ):
            inferred_dept = "Procurement"
        elif any(w in t_lower for w in ["human resources", "hr", "people", "talent", "recruiting"]):
            inferred_dept = "Human Resources"
        elif any(w in t_lower for w in ["legal", "counsel", "compliance"]):
            inferred_dept = "Legal"
        elif any(w in t_lower for w in ["operations", "coo", "admin", "logistics"]):
            inferred_dept = "Operations"
        elif any(w in t_lower for w in ["ceo", "president", "chief executive"]):
            inferred_dept = "Executive"
        elif any(w in t_lower for w in ["technology", "cto", "it", "information"]):
            inferred_dept = "Technology"
        else:
            inferred_dept = "General"

    # Infer function
    f_check = f"{t_lower} {dept_lower}"
    if any(
        w in f_check
        for w in ["software", "swe", "developer", "frontend", "backend", "fullstack", "architect"]
    ):
        inferred_func = "Software Development"
    elif any(w in f_check for w in ["devops", "sre", "infrastructure", "cloud", "systems"]):
        inferred_func = "Infrastructure & DevOps"
    elif any(w in f_check for w in ["engineering", "tech"]):
        inferred_func = (
            "Engineering Management"
            if "manager" in f_check or "director" in f_check or "vp" in f_check
            else "Engineering"
        )
    elif any(w in f_check for w in ["product manager", "product management", "product"]):
        inferred_func = "Product Management"
    elif any(w in f_check for w in ["procurement", "purchasing", "sourcing", "buyer"]):
        inferred_func = "Procurement & Purchasing"
    elif any(w in f_check for w in ["finance", "accounting", "treasury"]):
        inferred_func = "Finance & Accounting"
    elif any(w in f_check for w in ["sales", "revenue", "account executive"]):
        inferred_func = "Sales & Business Development"
    elif any(w in f_check for w in ["marketing", "growth"]):
        inferred_func = "Marketing"
    elif any(w in f_check for w in ["talent", "recruiting", "hr", "people"]):
        inferred_func = "Human Resources"
    elif any(w in f_check for w in ["executive", "ceo", "cfo", "coo", "president"]):
        inferred_func = "Executive Leadership"
    else:
        inferred_func = inferred_dept

    return inferred_dept, inferred_func


def detect_cycles_in_relationships(
    relationships: list[dict[str, str | None]],
) -> list[list[str]]:
    """
    Detects directed cycles in reporting relationships.
    Returns a list of cycles (each cycle is a list of employee IDs in loop order).
    """
    parent_map: dict[str, str | None] = {}
    for rel in relationships:
        emp_id = rel.get("employee_id")
        parent_id = rel.get("parent_id")
        if emp_id:
            parent_map[emp_id] = parent_id

    cycles: list[list[str]] = []
    visited: set[str] = set()

    for start_id in parent_map:
        if start_id in visited:
            continue

        path: list[str] = []
        path_set: set[str] = set()
        curr: str | None = start_id

        while curr is not None:
            if curr in path_set:
                cycle_start_idx = path.index(curr)
                cycle = path[cycle_start_idx:] + [curr]
                cycles.append(cycle)
                break
            if curr in visited or curr not in parent_map:
                break

            path.append(curr)
            path_set.add(curr)
            curr = parent_map.get(curr)

        visited.update(path)

    return cycles


def validate_hierarchy_structure(
    employee_ids: set[str],
    relationships: list[dict[str, str | None]],
) -> tuple[bool, list[str], list[str]]:
    """
    Validates structural integrity of hierarchy relationships:
    - Checks completeness (every employee present)
    - Checks for self-reporting
    - Checks for references to non-existent parent IDs
    - Checks for circular reporting loops
    - Identifies root employee IDs (parent_id is None)

    Returns:
        (is_valid, error_messages, root_employee_ids)
    """
    errors: list[str] = []
    rel_emp_ids = set()
    root_ids: list[str] = []

    for rel in relationships:
        emp_id = rel.get("employee_id")
        parent_id = rel.get("parent_id")

        if not emp_id:
            errors.append("Encountered relationship with empty employee_id.")
            continue

        if emp_id not in employee_ids:
            errors.append(f"Relationship contains unknown employee_id: '{emp_id}'.")

        rel_emp_ids.add(emp_id)

        # Check self-reporting
        if parent_id is not None and parent_id == emp_id:
            errors.append(
                f"Self-reporting detected: employee '{emp_id}' cannot report to themselves."
            )

        # Check non-existent parent ID
        if parent_id is not None and parent_id not in employee_ids:
            errors.append(
                f"Invalid parent_id '{parent_id}' for employee '{emp_id}'; parent ID does not exist in employee list."
            )

        if parent_id is None and emp_id in employee_ids:
            root_ids.append(emp_id)

    # Check for missing employees
    missing_ids = employee_ids - rel_emp_ids
    if missing_ids:
        errors.append(f"Missing hierarchy relationships for employees: {sorted(missing_ids)}")

    # Check for duplicate relationships
    if len(relationships) != len(rel_emp_ids):
        errors.append("Duplicate relationships found for one or more employees.")

    # Check for cycles
    cycles = detect_cycles_in_relationships(relationships)
    if cycles:
        for cycle in cycles:
            cycle_str = " -> ".join(cycle)
            errors.append(f"Circular reporting relationship detected: {cycle_str}")

    # If no root IDs found and we have employees, there is a cycle or disconnect
    if not root_ids and employee_ids:
        errors.append("No root employee (parent_id=null) found in hierarchy structure.")

    is_valid = len(errors) == 0
    return is_valid, errors, root_ids
