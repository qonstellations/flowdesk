# Agent Specification: Admin Validation & Department-Student Email Agent

## Overview
This agent is responsible for implementing the ticket verification workflow and transactional email system for FlowDesk, based on the requirements and architectural details specified in [.ai_context/FUTURE_PLAN.md](file:///D:/flowdesk/.ai_context/FUTURE_PLAN.md).

It enables admin validation of tickets from the dashboard, emails the appropriate department with ticket details and a secure, time-limited completion link, and sends a confirmation email to the student once the ticket is marked resolved by the department.

## Workspace Access Permissions
* **Read-Write Access**: `backend/` (Allowed to modify database models, query functions, FastAPI webhook/route endpoints, and write new Python scripts).
* **Read-Only Access**: `app/` (Allowed to read Streamlit code to understand how components render, but **must not** modify or write to files in this directory).

---

## Detailed Tasks & Requirements

### 1. Database Schema Updates (`backend/db.py`)
* **Status Enum**: Keep the existing ticket statuses or introduce a validation tracking status/flag.
* **Tracking Table / Columns**:
  * Implement support for tracking admin validation and completion tokens.
  * You can create a new table `completion_tokens` or extend the `tickets` table to store:
    * `token` (TEXT, Primary Key): A secure, random token.
    * `ticket_id` (INTEGER): References `tickets.ticket_id`.
    * `recipient_email` (TEXT): The department email the link was sent to.
    * `expires_at` (TEXT): ISO timestamp representing expiration (e.g., 24 or 48 hours).
    * `used_at` (TEXT, Nullable): ISO timestamp when the link was clicked.
* **Helper Functions**:
  * Add database functions to generate/save a token, check token validity (not expired, not used), mark the token as used, and retrieve ticket/student details.

### 2. Email Service Implementation (`backend/email_service.py`)
* Create a dedicated, clean module `backend/email_service.py` to keep mail utilities separate.
* Use Python's standard `smtplib` and `email.mime` package for email construction and delivery.
* Read SMTP server parameters from environment variables (e.g., `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`).
* Load a `BASE_URL` representing the hosted server address (e.g., `http://localhost:8000`) to construct the secure completion link.
* Implement two primary email dispatch functions:
  1. `send_department_completion_link(ticket, department_email, token)`:
     * Dispatched when the admin approves the ticket.
     * Contains ticket ID, Title, Description, Location, Priority, and a completion link (e.g., `{BASE_URL}/api/tickets/complete?token={token}`).
  2. `send_student_resolution_notification(ticket, student_email)`:
     * Dispatched immediately when the completion link is clicked and processed.
     * Informs the student that their complaint has been resolved.

### 3. FastAPI Completion Webhook (`backend/webhook.py` or new routes file)
* Expose a new public GET route in FastAPI (e.g., `/api/tickets/complete`).
* **Handler Logic**:
  * Accept `token` as a query parameter.
  * Verify token validity in the database (matches, not expired, not already used).
  * If valid, update the token as used (`used_at = utc_now()`).
  * Transition the ticket status to `"Resolved"` (and update `resolved_at` timestamp).
  * Record a system audit event in the database (`EventCreate(action="RESOLVED_VIA_LINK", actor_type="system", actor_name="department")`).
  * Identify the registering student's email and trigger `send_student_resolution_notification()`.
  * Return a beautifully styled HTML success page stating "Ticket resolved successfully!" so that department representatives get instant, premium-looking visual feedback in their browser.
  * **Security**: Ensure this completion endpoint does not expose any admin credentials, access keys, or administrative dashboard views.

### 4. Code Quality & Integration
* All new logic (email templates, token generation) must be written in a new clean backend file or modules to avoid cluttering existing files.
* Add comprehensive error handling, connection retries, and clean logging messages.
