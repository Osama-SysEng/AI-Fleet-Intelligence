from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Driver(BaseModel):
    model_config = ConfigDict(extra="forbid")
    driver_id: str = Field(min_length=1, max_length=64)
    display_name: str = Field(min_length=1, max_length=120)
    license_class: str = Field(min_length=1, max_length=20)
    active: bool = True


class Vehicle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vehicle_id: str = Field(min_length=1, max_length=64)
    plate_number: str = Field(min_length=1, max_length=32)
    vehicle_type: str = Field(min_length=1, max_length=64)
    driver_id: str | None = Field(default=None, max_length=64)
    fleet_id: str = Field(min_length=1, max_length=64)
    active: bool = True

    @field_validator("vehicle_id", "plate_number", "vehicle_type", "fleet_id", "driver_id")
    @classmethod
    def no_control_chars(cls, value):
        if value is not None and any(ord(char) < 32 for char in value):
            raise ValueError("control characters are not allowed")
        return value


class TelemetryIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vehicle_id: str = Field(min_length=1, max_length=64)
    sequence: int = Field(ge=0)
    occurred_at: datetime
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    speed_kph: float = Field(ge=0, le=260)
    fuel_percent: float = Field(ge=0, le=100)
    engine_temp_c: float = Field(ge=-40, le=180)
