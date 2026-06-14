# FlowDesk

Campus complaints usually do not fail because nobody cares.

They fail because the system around them is messy.

A student reports that the Wi-Fi is down, a fan is broken, water is leaking, or a classroom projector is dead. The message lands in the wrong chat, gets forwarded twice, loses context, and eventually becomes someone else's problem. By the time the right department sees it, nobody knows who raised it, how urgent it is, or whether it was already handled.

FlowDesk is a campus complaint workflow built to make that chain less chaotic.

It takes student complaints from Telegram, verifies the student through Google OAuth, turns the message into a structured ticket, routes it to the right department, gives admins a dashboard to validate and track it, and sends departments secure resolution links when work is ready to be closed.


## The Problem

Most campus complaint systems are either too informal or too heavy.

Informal systems are fast, but hard to track:

- WhatsApp messages disappear under newer messages.
- Email threads split across departments.
- Students do not know whether anyone saw the complaint.
- Admins cannot easily tell what is overdue.
- Departments get incomplete reports with missing location or context.

Heavy systems solve tracking, but students avoid them:

- Too many forms.
- Too many portals.
- Too much friction for a broken fan or bad Wi-Fi.

FlowDesk sits between those two extremes: students use a lightweight channel they already understand, while the institution gets a real ticket lifecycle behind it.

## The Solution

FlowDesk turns a plain-language complaint into an operational workflow.

```text
Student message
    -> validation and clarification
    -> AI-assisted classification
    -> department routing
    -> admin review
    -> escalation email
    -> secure resolution link
    -> student-visible ticket history
```

The product is intentionally simple at the surface. A student can type:

```text
/ticket Wi-Fi is not working in the library second floor
```

Behind that message, FlowDesk handles identity, validation, routing, priority, department assignment, SLA tracking, and event history.

## What It Actually Does

### For Students

- Creates tickets directly from Telegram.
- Links Telegram users to verified Google accounts.
- Asks follow-up questions when the complaint is too vague.
- Shows ticket status through `/status` and the Student Portal.
- Keeps complaint history tied to the verified student identity.

### For Admins

- Provides a Streamlit dashboard for ticket review and operations.
- Supports approval, rejection, reassignment, and status updates.
- Tracks department, priority, SLA, overdue tickets, and event history.
- Lets admins manage departments and escalation email IDs.
- Moves approved open tickets into `Escalated` for department action.

### For Departments

- Receives structured escalation emails.
- Gets ticket details without needing dashboard access.
- Marks work resolved through a secure one-time link.
- Feeds resolution state back into FlowDesk.

## Why Telegram?

Because complaint intake should not start with a login wall.

Telegram gives students a low-friction entry point, while Google OAuth gives the backend a verified identity. That combination keeps the reporting experience lightweight without making the system anonymous or untrackable.

## Technical Shape

| Area | Implementation |
| --- | --- |
| Student intake | Telegram Bot API |
| Frontend | Streamlit |
| Backend | FastAPI |
| Auth | Google OAuth |
| Data store | SQLite |
| Routing intelligence | Gemini, OpenAI, or Ollama |
| Email flow | SMTP with local mock-email fallback |
| Public local callbacks | ngrok |

## Core Flow

1. Student links Telegram with Google using `/link`.
2. Student submits a complaint using `/ticket`.
3. FlowDesk validates the complaint and asks for missing details if needed.
4. The LLM classifies the issue and suggests routing metadata.
5. A ticket is created with department, priority, SLA, and event history.
6. Admin reviews the ticket and approves or rejects it.
7. Approved tickets move to `Escalated`.
8. Department receives a resolution email.
9. Department clicks a secure link after completing the work.
10. Ticket is marked resolved and remains visible in history.

## Local Development

For the full setup, including Telegram, Google OAuth, ngrok, SMTP, and LLM configuration:

[LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md)

Quick start:

```bash
git clone https://github.com/qonstellations/flowdesk.git
cd flowdesk
uv sync
cp .env.example .env
```

Run the backend:

```bash
uv run uvicorn backend.webhook:app --host 0.0.0.0 --port 8000 --reload
```

Run the frontend:

```bash
uv run streamlit run app/main.py
```

Open:

```text
http://localhost:8501
```

## Email Behavior

FlowDesk can send real emails through SMTP, but local development does not require SMTP.

If `SMTP_HOST` or `SMTP_USER` is empty, generated emails are written to:

```text
data/mock_emails/
```

That makes the department escalation flow testable without sending real mail. For real recipients, configure SMTP and set `BASE_URL` to a public backend URL such as an ngrok HTTPS URL.

## Repository Map

```text
app/                  Streamlit frontend
app/pages/            Admin dashboard and student portal
app/components/       Shared ticket UI components
backend/              FastAPI, Telegram, auth, workflow, DB, email
LOCAL_SETUP_GUIDE.md  Full local setup instructions
.env.example          Environment variable template
```

## Current Status

FlowDesk is an active MVP. The main loop is in place: verified student intake, complaint validation, AI-assisted routing, admin triage, department escalation, and resolution tracking.
