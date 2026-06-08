"""Contract compliance tests for FlowDesk.

Verifies that the canonical values defined in backend.constants
match the specifications in DATA_CONTRACT.md, ensuring code and
documentation stay in sync.
"""

import pytest

# Import from backend.constants


from backend import constants


def test_categories_match_contract() -> None:
    """Verify categories match DATA_CONTRACT.md."""
    expected_categories = {
        "IT & Wi-Fi",
        "Hostel Maintenance",
        "Campus Maintenance",
        "Mess & Food",
        "Academics",
        "Other",
    }
    assert set(constants.CATEGORIES) == expected_categories


def test_statuses_match_contract() -> None:
    """Verify statuses match DATA_CONTRACT.md."""
    expected_statuses = {
        "Open",
        "Assigned",
        "In Progress",
        "Resolved",
        "Reopened",
        "Escalated",
        "Closed",
    }
    assert set(constants.STATUSES) == expected_statuses


def test_priorities_match_contract() -> None:
    """Verify priorities match DATA_CONTRACT.md."""
    expected_priorities = {
        "Low",
        "Medium",
        "High",
        "Critical",
    }
    assert set(constants.PRIORITIES) == expected_priorities


def test_department_routing_matches_contract() -> None:
    """Verify routing map matches DATA_CONTRACT.md."""
    expected_routing = {
        "IT & Wi-Fi": "IT Department",
        "Hostel Maintenance": "Hostel Maintenance Team",
        "Campus Maintenance": "Campus Facilities Team",
        "Mess & Food": "Mess Committee",
        "Academics": "Academic Office",
        "Other": "General Admin",
    }
    assert constants.DEPARTMENT_ROUTING == expected_routing

