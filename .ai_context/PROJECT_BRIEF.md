# PROJECT BRIEF: FlowDesk

## 1. Product Name

FlowDesk

## 2. One-Line Description

FlowDesk is an Autonomous Multi-Agent Campus Issue Resolution Platform.

## 3. Core Problem

Campus complaints are usually scattered across WhatsApp groups, verbal reports, registers, Google Forms, and disconnected dashboards. Students lack transparency, staff receive poorly structured complaints, and admins lack SLA visibility and audit-ready records.

## 4. Core Solution

FlowDesk converts student complaints into structured, trackable tickets. It uses an agentic workflow to classify the complaint, assign the correct department, set an SLA deadline, create a work order, escalate overdue tickets, and maintain an auditable event timeline.

## 5. Final Beginner-Friendly Tech Stack

* Python 3.13+
* Telegram Bot for student complaint intake
* FastAPI for Telegram webhook handling
* LangGraph for the agent workflow
* LLM Provider API for complaint understanding
* SQLite for local database
* Streamlit for staff/admin/student dashboard
* Plotly for analytics charts

## 6. Architecture Rule

The project must stay Python-first. Do not add React, MongoDB, Supabase, Docker or RAG.

## 7. Application Flow

Student sends complaint on Telegram
→ FastAPI receives message
→ LangGraph runs the agent workflow
→ LLM classifies and structures the issue
→ SQLite stores ticket and event timeline
→ Telegram replies with ticket ID and SLA
→ Streamlit dashboard shows ticket status, staff actions, escalations, and analytics

## 8. MVP Scope

Only support these categories for the hackathon MVP:

* IT & Wi-Fi
* Hostel Maintenance
* Campus Maintenance
* Mess & Food
* Academics
* Other

Focus deeply on Hostel Maintenance and IT & Wi-Fi for the live demo.

## 9. Demo Goal

The demo must prove that FlowDesk is not just a complaint dashboard. It must show an issue moving autonomously from student complaint to classification, routing, SLA assignment, escalation, staff resolution, and student verification.
