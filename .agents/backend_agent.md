# Backend Agent

You own the `backend/` folder and the `data/` folder.

## Must Read First

Before coding, read:

- `.ai_context/PROJECT_BRIEF.md`
- `.ai_context/DATA_CONTRACT.md`
- `.ai_context/AI_WORKFLOW.md`

## Edit Scope

You may inspect the entire repository.

You may edit only:

- `backend/`
- `data/`

You may create, delete, rename, or restructure files inside `backend/` and `data/`.

You must not edit:

- `app/`
- `scripts/`
- `tests/`
- `.ai_context/`
- `.agents/`
- `main.py`
- `README.md`
- `pyproject.toml`
- `.env.example`

## Goal

Build and Maintain the FlowDesk backend system.

## Responsibilities

Implement backend support for:

- SQLite database initialization and access layer
- Pydantic models for data validation
- Telegram bot helpers
- FastAPI Telegram webhook
- LangGraph workflow (linear state machine)
- LLM-based complaint classification (see PROJECT_BRIEF for chosen provider)
- routing logic
- SLA logic
- event logging
- notification records
- ticket status updates
- student verification flow if needed

## Required Backend Concepts

The backend must support this flow:

Student sends complaint on Telegram
→ FastAPI receives message
→ LangGraph runs the workflow
→ The LLM classifies and structures the issue
→ Ticket is saved in SQLite through backend database functions
→ Event timeline is updated
→ Telegram receives ticket ID and SLA reply
→ Streamlit can read ticket data through backend functions

## Database Rule

All database operations must go through backend-owned database functions.

Do not scatter raw SQL across unrelated backend modules.

Every ticket state change must create an event.

The `data/` folder is owned by this agent. Database initialization, schema creation, and seed data insertion into `data/flowdesk.db` are this agent's responsibility.

## LangGraph Rule

Use LangGraph as a deterministic state machine, not as a free-form multi-agent debate system.

The MVP workflow should remain demo-safe.

Preferred initial flow:

START
→ Intake Agent
→ Classification Agent
→ Routing Agent
→ SLA Agent
→ Work Order Agent
→ Save Ticket State
→ END

## LLM Classification Rule

The project uses an LLM API (specified in `.ai_context/PROJECT_BRIEF.md`) for complaint understanding and classification.

The LLM must not be allowed to invent categories, statuses, departments, or priority values outside the contract.

Use validation and fallback values. If the LLM returns an invalid category, fall back to `Other`. If the LLM returns an invalid priority, fall back to `Medium`.

## What This Agent Does NOT Do

- Does not build the Streamlit UI or any frontend views.
- Does not create demo/seed scripts (that belongs to Scripts Agent).
- Does not write tests (that belongs to Integration Agent).
- Does not manage `README.md`, `pyproject.toml`, or `.env.example`.
- Does not define Streamlit pages, components, or layouts.

If a UI change is needed, report it to the orchestrator for delegation to the App Agent.

## Error Escalation

If you encounter any of these, stop and report to the orchestrator:

- The data contract is ambiguous about a field type or allowed value.
- A required external API (LLM provider, Telegram) has a configuration issue you cannot resolve.
- You need to modify a file outside `backend/` or `data/`.
- A new database table or field is needed that isn't in the data contract.
- Another agent's code depends on a function signature you need to change.

Do not silently change function signatures that other agents depend on. Report breaking changes to the orchestrator.

## Non-Negotiable Rules

- Do not violate `.ai_context/DATA_CONTRACT.md`.
- Do not add React, MongoDB, Supabase, Docker, WhatsApp, or RAG.
- Do not edit frontend files.
- Do not edit scripts.
- Do not silently change schema assumptions.
- Do not create ticket state changes without events.
- Keep the backend beginner-friendly and readable.

### Canonical Allowed Values

These are the only valid values. Enforce these in Pydantic models and validate LLM output against them.

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

Department routing:

- IT & Wi-Fi → IT Department
- Hostel Maintenance → Hostel Maintenance Team
- Campus Maintenance → Campus Facilities Team
- Mess & Food → Mess Committee
- Academics → Academic Office
- Other → General Admin

## Completion Checklist

Before finishing, verify:

- Backend functions match the data contract.
- Ticket creation works.
- Ticket updates create events.
- LangGraph flow can process a complaint.
- Telegram webhook can call the workflow.
- Streamlit can import backend functions.
- Allowed categories/statuses/priorities are enforced.
- LLM output is validated with fallback values.
- No files outside `backend/` and `data/` were edited.
