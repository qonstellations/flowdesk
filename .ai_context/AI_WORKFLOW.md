# AI WORKFLOW: FlowDesk LangGraph System

## 1. Purpose

This file defines the agentic workflow for FlowDesk. Keep the workflow deterministic, reliable, and product-safe. The system should feel autonomous, but it must not become unpredictable or hide failures behind fake success states.

## 2. LangGraph Rule

Use LangGraph as a state machine, not as a free-form multi-agent chat system.

The initial ticket creation graph should be mostly linear:

START
→ Intake Agent
→ Clarification Agent, only if required details are missing
→ Classification Agent
→ Routing Agent
→ SLA Agent
→ Work Order Agent
→ Save Ticket State
→ END

Escalation, staff resolution, and student verification can run separately from the initial complaint creation flow.

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
* needs_clarification: bool optional
* clarification_questions: list[str] optional
* clarification_answers: dict optional

## 4. Agent Responsibilities

### Intake Agent

Input:

* Raw student complaint after `/ticket`
* Any answers collected through follow-up questions

Output:

* Clean title
* Clean description
* Extracted location if available
* `needs_clarification` if the complaint is too incomplete to route responsibly
* Short follow-up questions when required

Rules:

* `/ticket` is the entry point for complaint creation.
* The text after `/ticket` can be natural language.
* Ask follow-up questions only when the complaint lacks information needed to create a useful ticket.
* Do not force a form-like conversation when the initial complaint is already clear enough.
* If location is missing but the category and issue are still actionable, create the ticket and mark location as `Unknown`.
* Reject obvious spam, random text, and casual chat before creating a ticket.

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

The escalation engine should be callable from application code and reusable by the admin dashboard or a scheduled job. It should:

* Find tickets where current time > sla_deadline
* Ignore tickets with status Closed or Resolved
* Change status to Escalated
* Add an event with action ESCALATED
* Add a notification record

## 6. Strict Limits

Do not add autonomous agent debate.

Do not add loops unless needed for missing information.

Do not let the LLM invent departments, statuses, categories, or priority values.

Do not add test-only branches, random IDs, or fake success fallbacks to production workflow code.
