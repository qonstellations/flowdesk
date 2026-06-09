# Future Plan

## Staff Completion Links

When a ticket is routed to a department with an escalation email, FlowDesk can email the responsible staff a temporary secure link.

Potential flow:

1. A ticket is created and routed to a department.
2. The system sends an email to the department email ID with ticket details and a time-limited completion link.
3. Staff opens the link after fixing the issue and submits a short completion confirmation.
4. FlowDesk marks the ticket as awaiting student confirmation.
5. The student receives a Telegram message asking whether the issue is fixed.
6. If the student confirms, FlowDesk closes the ticket automatically.
7. If the student rejects or does not confirm within a configured window, FlowDesk reopens or escalates the ticket.

Implementation notes:

- Store link tokens with ticket ID, recipient email, expiry, and one-time-use status.
- Add a FastAPI route for staff completion submissions.
- Add an intermediate ticket status such as `Pending Confirmation`.
- Keep an audit event for staff completion and student confirmation.
- Avoid exposing admin controls through the temporary staff link.
