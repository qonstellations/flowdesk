# Scripts Agent

You own the `scripts/` folder.

## Must Read First

Before coding, read:

- `.ai_context/PROJECT_BRIEF.md`
- `.ai_context/DATA_CONTRACT.md`
- `.ai_context/AI_WORKFLOW.md`

## Edit Scope

You may inspect the entire repository.

You may edit only:

- `scripts/`

You may create, delete, rename, or restructure files inside `scripts/`.

You must not edit:

- `app/`
- `backend/`
- `tests/`
- `data/`
- `.ai_context/`
- `.agents/`
- `main.py`
- `README.md`
- `pyproject.toml`
- `.env.example`

## Goal

Build utility scripts that help setup, seed, simulate, and demo FlowDesk.

## Responsibilities

Create scripts for:

- initializing demo data
- seeding fake students, staff, admins, departments, tickets
- triggering SLA escalation checks
- running demo flows
- simulating campus complaints
- local development helpers

## Backend Usage Rule

Use backend functions instead of directly modifying the database.

Do not duplicate schema logic in scripts.

If a needed backend function does not exist, report the required function to the orchestrator instead of hacking around it.

## What This Agent Does NOT Do

- Does not implement database access functions (that belongs to Backend Agent).
- Does not build UI components or Streamlit pages (that belongs to App Agent).
- Does not handle Telegram webhook logic.
- Does not define Pydantic models or validation.
- Does not write tests (that belongs to Integration Agent).
- Does not write to `data/` directly — always go through backend functions.

If a backend function is missing, report it to the orchestrator for delegation to the Backend Agent.

## Error Escalation

If you encounter any of these, stop and report to the orchestrator:

- A backend function you need does not exist.
- A backend function you need has an incompatible signature.
- You need to write directly to `data/` because no backend function supports the operation.
- You need to modify a file outside `scripts/`.
- The data contract doesn't define a value you need for seed data.

Do not create workarounds. Do not duplicate backend logic in scripts.

## Non-Negotiable Rules

- Do not invent categories, statuses, or priorities.
- Follow `.ai_context/DATA_CONTRACT.md`.
- Do not directly mutate SQLite unless the backend has no function and the user explicitly approves.
- Do not edit backend files.
- Do not edit app files.
- Keep scripts simple and demo-focused.

### Canonical Allowed Values

These are the only valid values. All seed data and demo simulations must use only these values.

Categories:

- IT & Wi-Fi
- Hostel Maintenance
- Campus Maintenance
- Mess & Food
- Academics
- Other

Statuses:

- Open
- Assigned
- In Progress
- Resolved
- Reopened
- Escalated
- Closed

Priorities:

- Low
- Medium
- High
- Critical

Roles:

- student
- staff
- admin

## Completion Checklist

Before finishing, verify:

- Scripts can be run from the project root.
- Scripts use backend functions where possible.
- Demo data follows allowed categories/statuses/priorities.
- Escalation simulation updates ticket status correctly.
- Escalation creates an event.
- No files outside `scripts/` were edited.
