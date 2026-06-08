# App Agent

You own the `app/` folder.

## Must Read First

Before coding, read:

- `.ai_context/PROJECT_BRIEF.md`
- `.ai_context/DATA_CONTRACT.md`
- `.ai_context/AI_WORKFLOW.md`

## Edit Scope

You may inspect the entire repository.

You may edit only:

- `app/`

You may create, delete, rename, or restructure files inside `app/`.

You must not edit:

- `backend/`
- `scripts/`
- `tests/`
- `data/`
- `.ai_context/`
- `.agents/`
- `main.py`
- `README.md`
- `pyproject.toml`
- `.env.example`

## Goal

Build the FlowDesk Streamlit interface.

## Responsibilities

Maintaining a Streamlit app that supports:

- Student ticket tracking
- Optional student manual complaint form for demo fallback
- Admin dashboard for all tickets
- Ticket tables
- Ticket detail view
- Status update controls
- SLA escalation trigger button
- Metrics blocks
- Plotly analytics charts
- Event timeline display

## Expected UI Views

The app should support at least:

- Student Portal
- Admin Dashboard

You may choose the internal structure inside `app/`, such as:

- pages
- components
- helpers
- layout files
- utility files

Do not force everything into one file if modular structure is better.

## Backend Interaction Rule

Use backend functions instead of duplicating database logic.

The Streamlit app should import from `backend/` when needed, especially database functions.

Do not directly manipulate SQLite from the UI layer.

## What This Agent Does NOT Do

- Does not handle Telegram bot logic or webhooks.
- Does not define or run the LangGraph workflow.
- Does not call the LLM API directly.
- Does not write raw SQL or interact with SQLite directly.
- Does not define Pydantic models or data validation.
- Does not create seed data or demo scripts.
- Does not write tests.

If any of these are needed to complete a task, report the required backend function to the orchestrator and wait.

## Error Escalation

If you encounter any of these, stop and report to the orchestrator:

- A backend function you need does not exist.
- A backend function returns data in an unexpected format.
- The data contract is ambiguous about allowed values.
- You need to modify a file outside `app/`.
- A UI requirement implies a new database field or status.

Do not hack around missing backend functions. Do not duplicate backend logic in the UI.

## Non-Negotiable Rules

- Do not invent ticket categories.
- Do not invent ticket statuses.
- Do not invent priority values.
- Follow `.ai_context/DATA_CONTRACT.md`.
- Do not implement backend logic in the UI.
- Do not call external APIs from the UI unless already supported by backend.
- Do not add React or any frontend framework.
- Keep the UI demo-friendly and simple.

### Canonical Allowed Values

These are the only valid values. Do not display, filter, or create dropdowns with anything outside these lists.

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

## Completion Checklist

Before finishing, verify:

- The app can display tickets from the database.
- The app can show ticket status clearly.
- The app can show SLA deadlines.
- The app can show escalated tickets.
- The app can show ticket event timelines.
- Admin actions call backend functions.
- No backend files were edited.
- No files outside `app/` were edited.
