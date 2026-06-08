"""Demo seed for FlowDesk.

Clears existing tickets/events/users/notifications and inserts 12
realistic campus grievances across all categories with full audit trails.
Run directly:  python scripts/seed_data.py
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import backend.db as db
from backend import constants


# ── Time helpers ───────────────────────────────────────────────────────────

def _ago(days: float = 0, hours: float = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days, hours=hours)).isoformat()


def _sla(created: str, priority: str) -> str:
    dt = datetime.fromisoformat(created)
    return (dt + timedelta(hours=constants.SLA_HOURS[priority])).isoformat()


# ── Low-level inserts (bypass model layer to control timestamps) ────────────

def _ins_user(c: sqlite3.Cursor, name, role, tg_id, dept=None):
    c.execute(
        "INSERT OR IGNORE INTO users (name,role,telegram_id,department,created_at) VALUES(?,?,?,?,?)",
        (name, role, tg_id, dept, _ago(8)),
    )


def _ins_ticket(c: sqlite3.Cursor, tg_id, title, desc, category, location,
                priority, status, dept, days_ago,
                resolved_days=None, closed_days=None) -> int:
    created   = _ago(days_ago)
    sla       = _sla(created, priority)
    resolved  = _ago(resolved_days) if resolved_days is not None else None
    closed    = _ago(closed_days)   if closed_days   is not None else None
    c.execute(
        """INSERT INTO tickets
           (telegram_id,title,description,raw_message,category,location,
            priority,status,assigned_dept,sla_deadline,
            created_at,updated_at,resolved_at,closed_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (tg_id, title, desc, desc, category, location,
         priority, status, dept, sla,
         created, _ago(days_ago - 0.05), resolved, closed),
    )
    return c.lastrowid


def _ins_ev(c: sqlite3.Cursor, ticket_id, actor_type, actor_name,
            action, details, days_ago, hours_offset=0):
    c.execute(
        """INSERT INTO events
           (ticket_id,actor_type,actor_name,action,details,created_at)
           VALUES(?,?,?,?,?,?)""",
        (ticket_id, actor_type, actor_name, action, details,
         _ago(days_ago, hours_offset)),
    )


# ── Main seed ──────────────────────────────────────────────────────────────

def seed() -> None:
    db.init_db()
    conn = db.get_connection()
    c    = conn.cursor()

    # Wipe existing demo data (order respects FK constraints)
    for tbl in ("notifications", "events", "tickets", "users"):
        c.execute(f"DELETE FROM {tbl}")

    # ── Users ────────────────────────────────────────────────────────────
    _ins_user(c, "Rahul Sharma",    "student", "@rahul_s")
    _ins_user(c, "Priya Verma",     "student", "@priya_v")
    _ins_user(c, "Arjun Patel",     "student", "@arjun_p")
    _ins_user(c, "Sneha Gupta",     "student", "@sneha_g")
    _ins_user(c, "Karan Mehta",     "student", "@karan_m")
    _ins_user(c, "Deepak Singh",    "staff",   "@deepak_it",     "IT Department")
    _ins_user(c, "Meena Joshi",     "staff",   "@meena_hostel",  "Hostel Maintenance Team")
    _ins_user(c, "Rohan Tiwari",    "staff",   "@rohan_mess",    "Mess Committee")
    _ins_user(c, "Anita Kapoor",    "staff",   "@anita_campus",  "Campus Facilities Team")
    _ins_user(c, "Dr. S. Mathur",   "admin",   "@admin_flowdesk")

    # ── T1: Wi-Fi down in Library (Critical → Escalated, 4 days ago) ──────
    t1 = _ins_ticket(c, "@rahul_s",
        "Wi-Fi completely down across Central Library",
        "All Wi-Fi access points on both floors of the central library have been unreachable "
        "since 7 AM. Over 300 students are unable to access online resources, submit "
        "assignments, or attend virtual classes. Router logs show repeated DHCP failures.",
        "IT & Wi-Fi", "Central Library — Both Floors",
        "Critical", "Escalated", "IT Department", days_ago=4)
    _ins_ev(c, t1, "student", "Rahul Sharma",  "TICKET_CREATED", "Complaint submitted via portal", 4)
    _ins_ev(c, t1, "agent",   "FlowDesk AI",   "CLASSIFIED",     "IT & Wi-Fi · Critical — affects 300+ students, zero workaround", 4, 0.1)
    _ins_ev(c, t1, "agent",   "FlowDesk AI",   "ROUTED",         "→ IT Department", 4, 0.12)
    _ins_ev(c, t1, "agent",   "FlowDesk AI",   "SLA_ASSIGNED",   "Deadline: 4 h from creation", 4, 0.12)
    _ins_ev(c, t1, "staff",   "Deepak Singh",  "STATUS_UPDATED", "In Progress — checking core switch in server room", 3.8)
    _ins_ev(c, t1, "system",  "System",        "ESCALATED",      "SLA window breached — auto-escalated", 3.5)

    # ── T2: No hot water Block C (High → Escalated, 3 days ago) ──────────
    t2 = _ins_ticket(c, "@priya_v",
        "No hot water in Hostel Block C for 3 consecutive days",
        "Geysers on all three floors of Hostel Block C stopped working on Monday morning. "
        "With temperatures dropping to 14 °C at night, students are unable to bathe. "
        "The warden's office was informed verbally twice but no action was taken.",
        "Hostel Maintenance", "Hostel Block C — Floors 1, 2 & 3",
        "High", "Escalated", "Hostel Maintenance Team", days_ago=3)
    _ins_ev(c, t2, "student", "Priya Verma",  "TICKET_CREATED", "Complaint submitted via portal", 3)
    _ins_ev(c, t2, "agent",   "FlowDesk AI",  "CLASSIFIED",     "Hostel Maintenance · High — recurring, affects entire block", 3, 0.1)
    _ins_ev(c, t2, "agent",   "FlowDesk AI",  "ROUTED",         "→ Hostel Maintenance Team", 3, 0.12)
    _ins_ev(c, t2, "agent",   "FlowDesk AI",  "SLA_ASSIGNED",   "Deadline: 12 h from creation", 3, 0.12)
    _ins_ev(c, t2, "system",  "System",       "ESCALATED",      "SLA window breached — auto-escalated", 2.5)

    # ── T3: Cockroaches in Mess kitchen (Critical → In Progress, 2 days) ─
    t3 = _ins_ticket(c, "@arjun_p",
        "Cockroaches spotted near food counter in Main Mess",
        "Multiple cockroaches were found crawling near the food serving station and inside "
        "the kitchen rack area during dinner service. This is a serious food hygiene "
        "violation. At least 6 students reported nausea after eating there on Tuesday. "
        "Photographic evidence available.",
        "Mess & Food", "Main Mess — Kitchen & Serving Counter",
        "Critical", "In Progress", "Mess Committee", days_ago=2)
    _ins_ev(c, t3, "student", "Arjun Patel",  "TICKET_CREATED", "Complaint submitted with photo evidence", 2)
    _ins_ev(c, t3, "agent",   "FlowDesk AI",  "CLASSIFIED",     "Mess & Food · Critical — hygiene violation, illness reported", 2, 0.1)
    _ins_ev(c, t3, "agent",   "FlowDesk AI",  "ROUTED",         "→ Mess Committee", 2, 0.12)
    _ins_ev(c, t3, "agent",   "FlowDesk AI",  "SLA_ASSIGNED",   "Deadline: 4 h from creation", 2, 0.12)
    _ins_ev(c, t3, "staff",   "Rohan Tiwari", "STATUS_UPDATED", "In Progress — pest control team booked for tomorrow 6 AM", 1.8)

    # ── T4: Water leakage Room 204 (High → Resolved, 5 days ago) ─────────
    t4 = _ins_ticket(c, "@sneha_g",
        "Ceiling water leakage in Hostel Block A, Room 204",
        "Continuous dripping from the bathroom ceiling in Room 204, Block A since last "
        "night's rain. The floor is waterlogged, the electrical switchboard is damp, "
        "and there is risk of short-circuit. Three students sharing the room have moved "
        "out temporarily.",
        "Hostel Maintenance", "Hostel Block A — Room 204",
        "High", "Resolved", "Hostel Maintenance Team",
        days_ago=5, resolved_days=4.2)
    _ins_ev(c, t4, "student", "Sneha Gupta",   "TICKET_CREATED", "Complaint submitted via portal", 5)
    _ins_ev(c, t4, "agent",   "FlowDesk AI",   "CLASSIFIED",     "Hostel Maintenance · High — safety risk, electrical hazard", 5, 0.1)
    _ins_ev(c, t4, "agent",   "FlowDesk AI",   "ROUTED",         "→ Hostel Maintenance Team", 5, 0.12)
    _ins_ev(c, t4, "agent",   "FlowDesk AI",   "SLA_ASSIGNED",   "Deadline: 12 h from creation", 5, 0.12)
    _ins_ev(c, t4, "staff",   "Meena Joshi",   "STATUS_UPDATED", "In Progress — plumber and electrician dispatched", 4.8)
    _ins_ev(c, t4, "staff",   "Meena Joshi",   "RESOLVED",       "Pipe sealed, ceiling patched, electricals inspected and cleared", 4.2)

    # ── T5: AC failure in Exam Hall (Critical → Escalated, 2 days ago) ───
    t5 = _ins_ticket(c, "@rahul_s",
        "All 4 ACs non-functional in Exam Hall during semester exams",
        "All four AC units in the main exam hall (capacity 220 students) have failed "
        "during the ongoing end-semester examinations. Indoor temperature is 39 °C. "
        "Students are sweating through papers. Invigilators have also raised concerns. "
        "Two students have already reported dizziness.",
        "Campus Maintenance", "Main Exam Hall — Ground Floor, Admin Block",
        "Critical", "Escalated", "Campus Facilities Team", days_ago=2)
    _ins_ev(c, t5, "student", "Rahul Sharma",  "TICKET_CREATED", "Complaint submitted during exam break", 2)
    _ins_ev(c, t5, "agent",   "FlowDesk AI",   "CLASSIFIED",     "Campus Maintenance · Critical — ongoing exam, health risk", 2, 0.1)
    _ins_ev(c, t5, "agent",   "FlowDesk AI",   "ROUTED",         "→ Campus Facilities Team", 2, 0.12)
    _ins_ev(c, t5, "agent",   "FlowDesk AI",   "SLA_ASSIGNED",   "Deadline: 4 h from creation", 2, 0.12)
    _ins_ev(c, t5, "staff",   "Anita Kapoor",  "STATUS_UPDATED", "In Progress — HVAC vendor contacted, ETA 2 hours", 1.9)
    _ins_ev(c, t5, "system",  "System",        "ESCALATED",      "SLA window breached — auto-escalated", 1.5)

    # ── T6: Elevator stuck Block D (High → In Progress, 2 days ago) ──────
    t6 = _ins_ticket(c, "@karan_m",
        "Elevator out of service in Hostel Block D for 2 days",
        "The only elevator in Hostel Block D has been stuck between floors 2 and 3 "
        "since Sunday afternoon. Three students with mobility impairments on upper "
        "floors are severely affected. Stairs are the only option, which is not "
        "accessible for them.",
        "Hostel Maintenance", "Hostel Block D — Main Elevator",
        "High", "In Progress", "Hostel Maintenance Team", days_ago=2)
    _ins_ev(c, t6, "student", "Karan Mehta",  "TICKET_CREATED", "Complaint submitted via portal", 2)
    _ins_ev(c, t6, "agent",   "FlowDesk AI",  "CLASSIFIED",     "Hostel Maintenance · High — mobility access affected", 2, 0.1)
    _ins_ev(c, t6, "agent",   "FlowDesk AI",  "ROUTED",         "→ Hostel Maintenance Team", 2, 0.12)
    _ins_ev(c, t6, "agent",   "FlowDesk AI",  "SLA_ASSIGNED",   "Deadline: 12 h from creation", 2, 0.12)
    _ins_ev(c, t6, "staff",   "Meena Joshi",  "STATUS_UPDATED", "In Progress — AMC vendor (Otis) on-site, parts being sourced", 1.7)

    # ── T7: Projector broken Seminar Hall (Medium → Open, 1 day ago) ─────
    t7 = _ins_ticket(c, "@priya_v",
        "Projector not working in Seminar Hall 101",
        "The ceiling-mounted projector in Seminar Hall 101 stopped mid-lecture today. "
        "The control panel shows a lamp error. A guest lecture and a student "
        "presentation are both scheduled in this hall tomorrow morning.",
        "Academics", "Academic Block — Seminar Hall 101",
        "Medium", "Open", "Academic Office", days_ago=1)
    _ins_ev(c, t7, "student", "Priya Verma",  "TICKET_CREATED", "Complaint submitted via portal", 1)
    _ins_ev(c, t7, "agent",   "FlowDesk AI",  "CLASSIFIED",     "Academics · Medium — session disrupted, workaround possible", 1, 0.1)
    _ins_ev(c, t7, "agent",   "FlowDesk AI",  "ROUTED",         "→ Academic Office", 1, 0.12)
    _ins_ev(c, t7, "agent",   "FlowDesk AI",  "SLA_ASSIGNED",   "Deadline: 24 h from creation", 1, 0.12)

    # ── T8: Poor food quality Main Mess (Medium → Open, 1 day ago) ───────
    t8 = _ins_ticket(c, "@sneha_g",
        "Consistently poor food quality in Main Mess this week",
        "For the past 5 days the food quality in the main mess has been unacceptable: "
        "undercooked rice, watered-down dal, and vegetables with a sour smell. "
        "A student petition with 87 signatures was submitted to the mess supervisor "
        "yesterday but no response has been received.",
        "Mess & Food", "Main Mess — Dining Hall",
        "Medium", "Open", "Mess Committee", days_ago=1)
    _ins_ev(c, t8, "student", "Sneha Gupta",  "TICKET_CREATED", "Complaint submitted with attached petition", 1)
    _ins_ev(c, t8, "agent",   "FlowDesk AI",  "CLASSIFIED",     "Mess & Food · Medium — recurring pattern, petition submitted", 1, 0.1)
    _ins_ev(c, t8, "agent",   "FlowDesk AI",  "ROUTED",         "→ Mess Committee", 1, 0.12)
    _ins_ev(c, t8, "agent",   "FlowDesk AI",  "SLA_ASSIGNED",   "Deadline: 24 h from creation", 1, 0.12)

    # ── T9: Network down Computer Lab 3 (High → Assigned, 1 day ago) ─────
    t9 = _ins_ticket(c, "@arjun_p",
        "Full network outage in Computer Lab 3 — practical tomorrow",
        "All 32 workstations in Computer Lab 3 lost network connectivity at 3 PM today. "
        "The managed switch in the lab cabinet shows all port LEDs off. A networking "
        "practical for CS3 batch is scheduled 9 AM tomorrow — 64 students affected.",
        "IT & Wi-Fi", "Academic Block — Computer Lab 3, 2nd Floor",
        "High", "Assigned", "IT Department", days_ago=1)
    _ins_ev(c, t9, "student", "Arjun Patel",  "TICKET_CREATED", "Complaint submitted via portal", 1)
    _ins_ev(c, t9, "agent",   "FlowDesk AI",  "CLASSIFIED",     "IT & Wi-Fi · High — lab session at risk, deadline tomorrow", 1, 0.1)
    _ins_ev(c, t9, "agent",   "FlowDesk AI",  "ROUTED",         "→ IT Department", 1, 0.12)
    _ins_ev(c, t9, "agent",   "FlowDesk AI",  "SLA_ASSIGNED",   "Deadline: 12 h from creation", 1, 0.12)
    _ins_ev(c, t9, "staff",   "Deepak Singh", "STATUS_UPDATED", "Assigned — will inspect switch cabinet first thing tomorrow", 0.9)

    # ── T10: Street lights out (Medium → Closed, 6 days ago) ─────────────
    t10 = _ins_ticket(c, "@karan_m",
        "Street lights out on road between Hostel Block B and Mess",
        "The 200 m stretch between Hostel Block B and the main mess has had no working "
        "street lighting for a week. Students returning from late study sessions are at "
        "risk. Two near-miss incidents with cyclists were reported last Wednesday.",
        "Campus Maintenance", "Campus Road — Block B to Main Mess",
        "Medium", "Closed", "Campus Facilities Team",
        days_ago=6, resolved_days=5.1, closed_days=4.8)
    _ins_ev(c, t10, "student", "Karan Mehta",   "TICKET_CREATED", "Complaint submitted via portal", 6)
    _ins_ev(c, t10, "agent",   "FlowDesk AI",   "CLASSIFIED",     "Campus Maintenance · Medium — safety risk, recurring", 6, 0.1)
    _ins_ev(c, t10, "agent",   "FlowDesk AI",   "ROUTED",         "→ Campus Facilities Team", 6, 0.12)
    _ins_ev(c, t10, "agent",   "FlowDesk AI",   "SLA_ASSIGNED",   "Deadline: 24 h from creation", 6, 0.12)
    _ins_ev(c, t10, "staff",   "Anita Kapoor",  "STATUS_UPDATED", "In Progress — electrician team dispatched", 5.5)
    _ins_ev(c, t10, "staff",   "Anita Kapoor",  "RESOLVED",       "All 9 lights replaced with LED units. Tested and functional.", 5.1)
    _ins_ev(c, t10, "admin",   "Dr. S. Mathur", "CLOSED",         "Student confirmed resolution via portal. Ticket closed.", 4.8)

    # ── T11: Attendance portal 500 error (High → Assigned, 2 days ago) ───
    t11 = _ins_ticket(c, "@rahul_s",
        "Attendance portal throwing 500 error for entire Batch 2023",
        "Since yesterday morning, all ~180 students of Batch 2023 (CSE & ECE) get a "
        "'500 Internal Server Error' when logging into the attendance management portal. "
        "End-semester attendance shortage warnings cannot be checked. Final exams begin "
        "in 5 days.",
        "Academics", "Online Portal — Attendance Management System",
        "High", "Assigned", "Academic Office", days_ago=2)
    _ins_ev(c, t11, "student", "Rahul Sharma",    "TICKET_CREATED", "Complaint submitted via portal", 2)
    _ins_ev(c, t11, "agent",   "FlowDesk AI",     "CLASSIFIED",     "Academics · High — exam imminent, 180 students blocked", 2, 0.1)
    _ins_ev(c, t11, "agent",   "FlowDesk AI",     "ROUTED",         "→ Academic Office", 2, 0.12)
    _ins_ev(c, t11, "agent",   "FlowDesk AI",     "SLA_ASSIGNED",   "Deadline: 12 h from creation", 2, 0.12)
    _ins_ev(c, t11, "staff",   "Academic Office", "STATUS_UPDATED", "Assigned — IT cell looped in, investigating DB migration issue", 1.8)

    # ── T12: Damp walls Common Room Block B (Low → Open, 6 hours ago) ────
    t12 = _ins_ticket(c, "@priya_v",
        "Seepage and damp walls in Common Room, Hostel Block B",
        "After last night's rain, the common room walls in Hostel Block B have severe "
        "seepage. Paint is peeling, the carpet is damp, and there is a musty smell. "
        "The wooden furniture is starting to warp. The warden has been informed.",
        "Hostel Maintenance", "Hostel Block B — Common Room, Ground Floor",
        "Low", "Open", "Hostel Maintenance Team", days_ago=0.25)
    _ins_ev(c, t12, "student", "Priya Verma",  "TICKET_CREATED", "Complaint submitted via portal", 0.25)
    _ins_ev(c, t12, "agent",   "FlowDesk AI",  "CLASSIFIED",     "Hostel Maintenance · Low — no immediate safety risk, monitor", 0.25, 0.1)
    _ins_ev(c, t12, "agent",   "FlowDesk AI",  "ROUTED",         "→ Hostel Maintenance Team", 0.25, 0.12)
    _ins_ev(c, t12, "agent",   "FlowDesk AI",  "SLA_ASSIGNED",   "Deadline: 72 h from creation", 0.25, 0.12)

    conn.commit()
    conn.close()

    # Summary
    all_t = db.get_all_tickets()
    print(f"Seeded {len(all_t)} tickets:")
    for t in all_t:
        evs = db.get_events_by_ticket(t["ticket_id"])
        print(f"  #{t['ticket_id']:>2} [{t['status']:<11}] [{t['priority']:<8}] "
              f"{t['title'][:45]:<45}  ({len(evs)} events)")


if __name__ == "__main__":
    seed()
