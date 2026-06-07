# AI WORKFLOW: FlowDesk LangGraph System

## 1. Purpose

This file defines the agentic workflow for FlowDesk. Keep the workflow deterministic and demo-safe. The system should feel autonomous, but it must not become unpredictable.

## 2. LangGraph Rule

Use LangGraph as a state machine, not as a free-form multi-agent chat system.

The MVP graph must be mostly linear:

START
→ Intake Agent
→ Classification Agent
→ Routing Agent
→ SLA Agent
→ Work Order Agent
→ Save Ticket State
→ END

Escalation and verification can run separately from the initial complaint flow.

## 3. Shared State Object

The graph state should contain:

* raw_message: str
* telegram_id: str optional
* student_id: str optional
* ticket_id: int optional
* title: str optional
* description: str
* category: str optional
* location: str optional
* priority: str optional
* assigned_dept: str optional
* sla_deadline: str optional
* status: str (default: Open)
* created_at: str optional
* agent_notes: list[str]

## 4. Agent Responsibilities

### Intake Agent

Input:

* Raw student complaint

Output:

* Clean title
* Clean description
* Extracted location if available

Rules:

* Do not reject unclear complaints.
* If location is missing, still create the ticket but mark location as `Unknown`.

### Classification Agent

Input:

* Ticket description

Output:

* Category
* Priority

Allowed categories:

* IT & Wi-Fi
* Hostel Maintenance
* Campus Maintenance
* Mess & Food
* Academics
* Other

Allowed priorities:

* Low
* Medium
* High
* Critical

Use LLM for classification.

### Routing Agent

Input:

* Category
* Location
* Priority

Output:

* assigned_dept

Routing rules:

* IT & Wi-Fi → IT Department
* Hostel Maintenance → Hostel Maintenance Team
* Campus Maintenance → Campus Facilities Team
* Mess & Food → Mess Committee
* Academics → Academic Office
* Other → General Admin

### SLA Agent

Input:

* Category
* Priority
* created_at

Output:

* sla_deadline

SLA rules:

* Critical → 4 hours
* High → 12 hours
* Medium → 24 hours
* Low → 72 hours

### Work Order Agent

Input:

* Fully processed ticket state

Output:

* Ticket saved or updated in SQLite
* Event timeline updated

Rules:

* Create an event for classification.
* Create an event for routing.
* Create an event for SLA assignment.
* Create an event for ticket assignment.

## 5. Escalation Engine

The escalation engine can be a separate script:

`scripts/run_escalations.py`

It should:

* Find tickets where current time > sla_deadline
* Ignore tickets with status Closed or Resolved
* Change status to Escalated
* Add an event with action ESCALATED
* Add a notification record

## 6. Streamlit Demo Requirement

The admin dashboard must include a button:

`Trigger SLA Engine`

When clicked, it should run the escalation check so judges can see overdue tickets escalate during the live demo.

## 7. Strict Limits

Do not add RAG in the MVP.

Do not add autonomous agent debate.

Do not add loops unless needed for missing information.

Do not let the LLM invent departments, statuses, categories, or priority values.
