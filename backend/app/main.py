from fastapi import FastAPI
from backend.app.api.router import router

app = FastAPI(title="AI Fleet Intelligence — Simulation", version="2.0.0")
app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok", "mode": "simulation-only", "external_dispatch": False, "vehicle_control": False}

