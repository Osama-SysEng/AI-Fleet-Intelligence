from __future__ import annotations

import os
from fastapi import APIRouter, Depends, Header, HTTPException

from backend.app.fleet.store import SimulationFleetStore
from backend.app.models.vehicle import TelemetryIn
from backend.app.services.violation_engine import evaluate_telemetry, explain

router = APIRouter(prefix="/api/v1", tags=["fleet-simulation"])
store = SimulationFleetStore()


def operator_guard(x_operator_token: str | None = Header(default=None)) -> None:
    tokens = [x.strip() for x in os.getenv("OPERATOR_TOKENS", "").split(",") if x.strip()]
    environment = os.getenv("ENVIRONMENT", "development").casefold()
    if environment == "production" and not tokens:
        raise HTTPException(503, "operator access is not configured")
    if tokens and x_operator_token not in tokens:
        raise HTTPException(403, "operator authorization required")


@router.post("/telemetry", status_code=202)
def telemetry(payload: TelemetryIn):
    try:
        result = store.ingest(payload.model_dump())
        if result.get("event"):
            violations = evaluate_telemetry(
                speed_kph=payload.speed_kph,
                fuel_percent=payload.fuel_percent,
                engine_temp_c=payload.engine_temp_c,
            )
            result["event"]["violations"] = explain(violations)
        return result
    except (TypeError, ValueError, OverflowError):
        raise HTTPException(400, "invalid simulation telemetry")


@router.get("/events", dependencies=[Depends(operator_guard)])
def events():
    return store.events()


@router.get("/audit", dependencies=[Depends(operator_guard)])
def audit():
    return store.audit()


@router.post("/commands")
def commands():
    raise HTTPException(409, "vehicle commands are prohibited in this simulation release")
