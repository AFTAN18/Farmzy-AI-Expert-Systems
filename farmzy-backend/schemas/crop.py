from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CropRecommendationOut(BaseModel):
    id: str
    field_id: str
    sensor_reading_id: str
    recommended_at: datetime
    top_crop_1: str | None = None
    top_crop_2: str | None = None
    top_crop_3: str | None = None
    probabilities: dict[str, float] = Field(default_factory=dict)
    naive_bayes_confidence: float | None = None
    model_version: str | None = None
    reasoning_summary: str | None = None


class CropPredictionResponse(BaseModel):
    top_3: list[tuple[str, float]]
    confidence: float
    raw_probabilities: dict[str, Any]
