"""Pydantic models and LangGraph state definition for FlowDesk.

Includes request schemas for users, tickets, events, and notifications,
plus the ``GraphState`` TypedDict consumed by the LangGraph workflow.
"""

from __future__ import annotations

from typing import Optional, TypedDict

from pydantic import BaseModel, field_validator

from backend import constants


# ── Request / input models ─────────────────────────────────────────────


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    name: str
    role: str
    telegram_id: str
    department: Optional[str] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        """Ensure *role* is one of the allowed values."""
        if value not in constants.ROLES:
            raise ValueError(
                f"Invalid role '{value}'. Must be one of {constants.ROLES}"
            )
        return value


class TicketCreate(BaseModel):
    """Schema for creating a new support ticket."""

    telegram_id: str
    title: str
    description: str
    raw_message: str
    category: str
    location: str = "Unknown"
    priority: str

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        """Ensure *category* is one of the allowed values."""
        if value not in constants.CATEGORIES:
            raise ValueError(
                f"Invalid category '{value}'. Must be one of {constants.CATEGORIES}"
            )
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        """Ensure *priority* is one of the allowed values."""
        if value not in constants.PRIORITIES:
            raise ValueError(
                f"Invalid priority '{value}'. Must be one of {constants.PRIORITIES}"
            )
        return value


class TicketUpdate(BaseModel):
    """Schema for partially updating an existing ticket."""

    status: Optional[str] = None
    assigned_dept: Optional[str] = None
    sla_deadline: Optional[str] = None
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        """Ensure *status*, when provided, is one of the allowed values."""
        if value is not None and value not in constants.STATUSES:
            raise ValueError(
                f"Invalid status '{value}'. Must be one of {constants.STATUSES}"
            )
        return value


class EventCreate(BaseModel):
    """Schema for creating an audit-trail event on a ticket."""

    ticket_id: int
    actor_type: str
    actor_name: str
    action: str
    details: Optional[str] = None

    @field_validator("actor_type")
    @classmethod
    def validate_actor_type(cls, value: str) -> str:
        """Ensure *actor_type* is one of the allowed values."""
        if value not in constants.ACTOR_TYPES:
            raise ValueError(
                f"Invalid actor_type '{value}'. Must be one of {constants.ACTOR_TYPES}"
            )
        return value


class NotificationCreate(BaseModel):
    """Schema for queuing a notification to a user."""

    ticket_id: int
    recipient: str
    channel: str
    message: str
    status: str = "pending"

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, value: str) -> str:
        """Ensure *channel* is one of the allowed values."""
        if value not in constants.NOTIFICATION_CHANNELS:
            raise ValueError(
                f"Invalid channel '{value}'. Must be one of {constants.NOTIFICATION_CHANNELS}"
            )
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        """Ensure *status* is one of the allowed values."""
        if value not in constants.NOTIFICATION_STATUSES:
            raise ValueError(
                f"Invalid status '{value}'. Must be one of {constants.NOTIFICATION_STATUSES}"
            )
        return value


# ── LangGraph workflow state ───────────────────────────────────────────


class GraphState(TypedDict):
    """Shared state dictionary passed between LangGraph nodes.

    Every node reads from and writes to this dict; keys are additive —
    a node should only overwrite keys it owns.
    """

    raw_message: str
    telegram_id: str | None
    student_id: str | None
    ticket_id: int | None
    title: str | None
    description: str
    category: str | None
    location: str | None
    priority: str | None
    assigned_dept: str | None
    sla_deadline: str | None
    status: str
    created_at: str | None
    agent_notes: list[str]
