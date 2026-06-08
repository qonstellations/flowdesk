"""Tests that verify constants match the DATA_CONTRACT.md specification."""
from __future__ import annotations

from backend import constants


def test_categories_match_contract():
    assert constants.CATEGORIES == (
        "IT & Wi-Fi",
        "Hostel Maintenance",
        "Campus Maintenance",
        "Mess & Food",
        "Academics",
        "Other",
    )


def test_statuses_match_contract():
    assert constants.STATUSES == (
        "Open",
        "Assigned",
        "In Progress",
        "Resolved",
        "Reopened",
        "Escalated",
        "Closed",
    )


def test_priorities_match_contract():
    assert constants.PRIORITIES == ("Low", "Medium", "High", "Critical")


def test_department_routing_matches_contract():
    assert isinstance(constants.DEPARTMENT_ROUTING, dict)
    assert constants.DEPARTMENT_ROUTING == {
        "IT & Wi-Fi": "IT Department",
        "Hostel Maintenance": "Hostel Maintenance Team",
        "Campus Maintenance": "Campus Facilities Team",
        "Mess & Food": "Mess Committee",
        "Academics": "Academic Office",
        "Other": "General Admin",
    }


def test_sla_hours_match_contract():
    assert constants.SLA_HOURS == {
        "Critical": 4,
        "High": 12,
        "Medium": 24,
        "Low": 72,
    }


def test_roles_match_contract():
    assert constants.ROLES == ("student", "staff", "admin")


def test_actor_types_match_contract():
    assert constants.ACTOR_TYPES == ("student", "staff", "admin", "agent", "system")
