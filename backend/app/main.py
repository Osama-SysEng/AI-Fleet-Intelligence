from __future__ import annotations

import os
import time
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import router


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8080")
    return [o.strip() for o in raw.split(",") if o.strip()]


def _rate_limit_per_minute() -> int:
    try:
        value = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
    except ValueError:
        value = 120
    return max(1, min(value, 6000))


RATE_LIMIT = _rate_limit_per_minute()
_hits: dict[str, list[float]] = defaultdict(list)

app = FastAPI(title="AI Fleet Intelligence — Simulation", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Operator-Token"],
    max_age=600,
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path != "/health":
        now = time.monotonic()
        window_start = now - 60.0
        client = request.client.host if request.client else "unknown"
        key = f"{client}:{request.url.path}"
        recent = [t for t in _hits[key] if t > window_start]
        _hits[key] = recent
        if len(recent) >= RATE_LIMIT:
            return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
        recent.append(now)
    return await call_next(request)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "mode": "simulation-only", "external_dispatch": False, "vehicle_control": False}
