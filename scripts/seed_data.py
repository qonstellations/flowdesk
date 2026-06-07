"""Demo data seeding script for FlowDesk.

Populates the database with sample users, departments, and tickets
so the system can be demonstrated without manual data entry.
"""

# Import from backend.db for data access
# Uses canonical values from backend.constants


def seed_users() -> None:
    """Create demo students, staff, and admins."""
    pass


def seed_departments() -> None:
    """Ensure departments exist (may be handled by db init)."""
    pass


def seed_tickets() -> None:
    """Create sample tickets across categories."""
    pass


def main() -> None:
    """Run all seed functions."""
    pass


if __name__ == "__main__":
    main()
