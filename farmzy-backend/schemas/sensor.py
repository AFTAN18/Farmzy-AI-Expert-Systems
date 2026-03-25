from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SensorReadingBase(BaseModel):
    nitrogen: float | None = None
    phosphorus: float | None = None
    potassium: float | None = None
    temperature: float | None = None
    humidity: float | None = None
    ph: float | None = None
    gas_ppm: float | None = None
    soil_moisture: float | None = None


class SensorReadingCreate(SensorReadingBase):
    field_id: str
    farm_id: str
    thingspeak_entry_id: int
    recorded_at: datetime


class SensorReadingOut(SensorReadingBase):
    id: str
    field_id: str
    farm_id: str
    thingspeak_entry_id: int
    recorded_at: datetime
    ingested_at: datetime


class ThingSpeakFeed(BaseModel):
    entry_id: int
    created_at: datetime
    field1: str | None = None
    field2: str | None = None
    field3: str | None = None
    field4: str | None = None
    field5: str | None = None
    field6: str | None = None
    field7: str | None = None
    field8: str | None = None


class ReadingEventPayload(BaseModel):
    reading: dict[str, Any]
    prediction: dict[str, Any] | None = None
    alerts: list[dict[str, Any]] = Field(default_factory=list)
