"""Structured LLM contracts for FlowDesk."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ComplaintValidationResult(BaseModel):
    is_valid: bool
    is_complete: bool
    missing_fields: list[str] = Field(default_factory=list)
    reason: str = ""


class ClarificationResult(BaseModel):
    normalized_complaint: str
    missing_fields: list[str] = Field(default_factory=list)
    next_questions: list[str] = Field(default_factory=list, max_length=2)


class IntakeResult(BaseModel):
    title: str
    description: str
    location: str = "Unknown"


class RoutingResult(BaseModel):
    department_id: int
    department_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class TargetResolutionResult(BaseModel):
    urgency: Literal["Low", "Medium", "High", "Critical"]
    target_hours: int = Field(ge=1, le=168)
    explanation: str


COMPLAINT_VALIDATION_SCHEMA = ComplaintValidationResult.model_json_schema()
CLARIFICATION_SCHEMA = ClarificationResult.model_json_schema()
INTAKE_SCHEMA = IntakeResult.model_json_schema()
ROUTING_SCHEMA = RoutingResult.model_json_schema()
TARGET_RESOLUTION_SCHEMA = TargetResolutionResult.model_json_schema()
