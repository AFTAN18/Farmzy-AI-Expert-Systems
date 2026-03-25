from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IrrigationPredictionOut(BaseModel):
    id: str
    field_id: str
    sensor_reading_id: str
    predicted_at: datetime
    water_requirement_liters: float
    irrigation_decision: str
    confidence_score: float
    model_version: str | None = None
    expert_rule_fired: str | None = None
    fuzzy_membership_score: float | None = None
    reasoning_trace: dict[str, Any] = Field(default_factory=dict)


class ExpertSystemResponse(BaseModel):
    decision: str
    water_liters: float
    rules_fired: list[str]
    reasoning_trace: dict[str, Any]
    confidence: float
    alerts: list[dict[str, Any]] = Field(default_factory=list)


class RulePayload(BaseModel):
    rule_id: str
    rule_name: str
    condition_description: str
    action_description: str
    priority: int = 50
    is_active: bool = True
