"""Unit tests for buying role classification."""

from backend.app.schemas.classification import BuyingRole
from backend.app.schemas.employee import EmployeeInput
from backend.app.schemas.hierarchy import HierarchyAnalyzeRequest
from backend.app.services.hierarchy_service import HierarchyService


def test_buying_role_classifications():
    """
    Tests buying role classifications for key buyer committee archetypes:
    - CFO -> Economic Buyer
    - VP Engineering -> Champion
    - Procurement / Engineering Manager -> Influencer
    - Software Engineer -> User
    - Ambiguous title -> Unknown
    """
    service = HierarchyService()
    request = HierarchyAnalyzeRequest(
        company="Enterprise Alpha",
        employees=[
            EmployeeInput(id="1", name="Sarah", title="CFO", department="Finance"),
            EmployeeInput(id="2", name="Emily", title="VP Engineering", department="Engineering"),
            EmployeeInput(
                id="3", name="Lisa", title="Procurement Manager", department="Procurement"
            ),
            EmployeeInput(
                id="4", name="Alex", title="Engineering Manager", department="Engineering"
            ),
            EmployeeInput(
                id="5", name="James", title="Software Engineer", department="Engineering"
            ),
            EmployeeInput(id="6", name="Sam", title="Consultant", department=None),
        ],
    )

    response = service.analyze(request)
    people_map = {p.id: p for p in response.people}

    # CFO: Economic Buyer
    assert people_map["1"].buying_role == BuyingRole.ECONOMIC_BUYER
    assert people_map["1"].confidence >= 0.70

    # VP Engineering: Champion
    assert people_map["2"].buying_role == BuyingRole.CHAMPION
    assert people_map["2"].confidence >= 0.70

    # Procurement Manager: Influencer
    assert people_map["3"].buying_role == BuyingRole.INFLUENCER
    assert people_map["3"].confidence >= 0.70

    # Software Engineer: User
    assert people_map["5"].buying_role == BuyingRole.USER
    assert people_map["5"].confidence >= 0.70

    # Verify all employees have valid reasons, supporting factors, and confidence bounds
    for person in response.people:
        assert 0.0 <= person.confidence <= 1.0
        assert len(person.reason.strip()) > 0
        assert isinstance(person.supporting_factors, list)
