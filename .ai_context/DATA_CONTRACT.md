# DATA CONTRACT: FlowDesk

## 1. Rule

This file is the source of truth for database tables, allowed values, and shared data models. Any code touching tickets, events, users, or departments must follow this contract.

## 2. Allowed Ticket Categories

Use only these exact strings:

* IT & Wi-Fi
* Hostel Maintenance
* Campus Maintenance
* Mess & Food
* Academics
* Other

## 3. Allowed Ticket Statuses

Use only these exact strings:

* Open
* Assigned
* In Progress
* Resolved
* Reopened
* Escalated
* Closed

## 4. Allowed Priority Levels

Use only these exact strings:

* Low
* Medium
* High
* Critical

## 5. Main Tables

### users

Fields:

* user_id: INTEGER PRIMARY KEY AUTOINCREMENT
* name: TEXT
* role: TEXT
* telegram_id: TEXT
* department: TEXT OPTIONAL
* created_at: TEXT

Allowed roles:

* student
* staff
* admin

### tickets

Fields:

* ticket_id: INTEGER PRIMARY KEY AUTOINCREMENT
* telegram_id: TEXT (references users.telegram_id — this is the ticket owner)
* title: TEXT
* description: TEXT
* raw_message: TEXT (original unprocessed complaint for audit)
* category: TEXT
* location: TEXT OPTIONAL (default: Unknown)
* priority: TEXT
* status: TEXT (default: Open)
* assigned_dept: TEXT OPTIONAL
* sla_deadline: TEXT OPTIONAL
* created_at: TEXT
* updated_at: TEXT
* resolved_at: TEXT OPTIONAL
* closed_at: TEXT OPTIONAL

### events

Fields:

* event_id: INTEGER PRIMARY KEY AUTOINCREMENT
* ticket_id: INTEGER (references tickets.ticket_id)
* actor_type: TEXT
* actor_name: TEXT
* action: TEXT
* details: TEXT OPTIONAL
* created_at: TEXT

Allowed actor_type values:

* student
* staff
* admin
* agent
* system

Example event actions:

* TICKET_CREATED
* CLASSIFIED
* ROUTED
* SLA_ASSIGNED
* STATUS_UPDATED
* ESCALATED
* RESOLVED
* REOPENED
* CLOSED

### departments

Fields:

* department_id: INTEGER PRIMARY KEY AUTOINCREMENT
* name: TEXT UNIQUE
* category: TEXT
* escalation_contact: TEXT OPTIONAL

Seed data (must be inserted on DB init):

* IT Department → IT & Wi-Fi
* Hostel Maintenance Team → Hostel Maintenance
* Campus Facilities Team → Campus Maintenance
* Mess Committee → Mess & Food
* Academic Office → Academics
* General Admin → Other

### notifications

Fields:

* notification_id: INTEGER PRIMARY KEY AUTOINCREMENT
* ticket_id: INTEGER (references tickets.ticket_id)
* recipient: TEXT
* channel: TEXT
* message: TEXT
* status: TEXT
* created_at: TEXT

Allowed channel values:

* telegram
* dashboard

Allowed notification status values:

* pending
* sent
* failed

## 6. Non-Negotiable Backend Rules

* Every ticket state change must create an event.
* Agents must not directly write random fields to the database.
* All database writes must go through functions in `backend/db.py`.
* The Streamlit UI must read and write using `backend/db.py`.
* The Telegram webhook must create tickets using `backend/db.py`.
* The LangGraph workflow must update tickets using `backend/db.py`.

## 7. MVP Database Choice

Use SQLite at:

`data/flowdesk.db`

Do not migrate to PostgreSQL during the hackathon unless SQLite becomes a real blocker.
