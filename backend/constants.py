"""Canonical constants and allowed values for the FlowDesk data contract.

All enumerations are defined as tuples (immutable) so they can be used
for validation throughout the codebase without risk of mutation.
"""

# ── Complaint / Ticket categories ──────────────────────────────────────
CATEGORIES: tuple[str, ...] = (
    "IT & Wi-Fi",
    "Hostel Maintenance",
    "Campus Maintenance",
    "Mess & Food",
    "Academics",
    "Other",
)

# ── Ticket lifecycle statuses ──────────────────────────────────────────
STATUSES: tuple[str, ...] = (
    "Open",
    "Assigned",
    "In Progress",
    "Resolved",
    "Reopened",
    "Escalated",
    "Closed",
)

# ── Priority levels (ascending severity) ───────────────────────────────
PRIORITIES: tuple[str, ...] = (
    "Low",
    "Medium",
    "High",
    "Critical",
)

# ── User roles ─────────────────────────────────────────────────────────
ROLES: tuple[str, ...] = (
    "student",
    "admin",
)

# ── Actor types for audit-trail events ─────────────────────────────────
ACTOR_TYPES: tuple[str, ...] = (
    "student",
    "admin",
    "agent",
    "system",
)

# ── Notification channels ─────────────────────────────────────────────
NOTIFICATION_CHANNELS: tuple[str, ...] = (
    "telegram",
    "dashboard",
)

# ── Notification delivery statuses ─────────────────────────────────────
NOTIFICATION_STATUSES: tuple[str, ...] = (
    "pending",
    "sent",
    "failed",
)

# ── Department routing: category → responsible department ──────────────
DEPARTMENT_ROUTING: dict[str, str] = {
    "IT & Wi-Fi": "IT Department",
    "Hostel Maintenance": "Hostel Maintenance Team",
    "Campus Maintenance": "Campus Facilities Team",
    "Mess & Food": "Mess Committee",
    "Academics": "Academic Office",
    "Other": "General Admin",
}

# ── SLA windows: priority → maximum resolution hours ───────────────────
SLA_HOURS: dict[str, int] = {
    "Critical": 4,
    "High": 12,
    "Medium": 24,
    "Low": 72,
}

# ── Default database path (relative to project root) ──────────────────
DB_PATH: str = "data/flowdesk.db"
