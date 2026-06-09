# PROJECT BRIEF: FlowDesk

## 1. Product Name

FlowDesk

## 2. One-Line Description

FlowDesk is an Autonomous Multi-Agent Campus Issue Resolution Platform.

## 3. Core Problem

Campus complaints are usually scattered across WhatsApp groups, verbal reports, registers, Google Forms, and disconnected dashboards. Students lack transparency, staff receive poorly structured complaints, and admins lack SLA visibility and audit-ready records.

## 4. Core Solution

FlowDesk converts student complaints into structured, trackable tickets. It uses an agentic workflow to classify the complaint, assign the correct department, set an SLA deadline, create a work order, escalate overdue tickets, and maintain an auditable event timeline.

## 5. MVP Tech Stack

* Python 3.13+
* Telegram Bot for student complaint intake
* FastAPI for Telegram webhook handling
* LangGraph for the agent workflow
* LLM Provider API for complaint understanding
* SQLite for local database
* Streamlit for staff/admin/student dashboard
* Plotly or Streamlit-native charts for analytics

## 6. Architecture Rule

The project must stay Python-first. Do not add React, MongoDB, Supabase, Docker or RAG.

## 7. Application Flow

Student starts a complaint with `/ticket`
→ Bot accepts a natural-language complaint after the command
→ If required details are missing, bot asks short follow-up questions
→ FastAPI receives message
→ LangGraph runs the agent workflow
→ LLM classifies and structures the issue
→ SQLite stores ticket and event timeline
→ Telegram replies with ticket ID and SLA
→ Streamlit dashboard shows ticket status, staff actions, escalations, and analytics

## 8. MVP Scope

Build the proper MVP before optimizing for any presentation. The MVP should support the complete core ticket lifecycle:

* Student complaint intake through Telegram
* Optional conversational clarification after `/ticket` when the issue is incomplete
* Ticket classification, priority assignment, department routing, and SLA creation
* Staff/admin status updates
* SLA escalation
* Student status tracking and verification/reopen flow
* Audit-ready event timeline

Only support these categories in the MVP:

* IT & Wi-Fi
* Hostel Maintenance
* Campus Maintenance
* Mess & Food
* Academics
* Other

## 9. Product Goal

FlowDesk must become a coherent end-to-end issue-resolution product, not a collection of disconnected screens. Testing should be added after the core layers and contracts are stable; tests should validate behavior from outside the app rather than adding test-only branches or fake behavior into production code.
