"""Minimal API entry point for Anomaly Zero."""

from fastapi import FastAPI

app = FastAPI(
    title="Anomaly Zero API",
    description="API inicial para explorar tendencias de sistemas terrestres.",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Report whether the API process is responding."""
    return {"status": "ok", "service": "anomaly-zero-api"}
