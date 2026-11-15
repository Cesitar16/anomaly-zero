"""Minimal API entry point for Anomaly Zero."""

from fastapi import FastAPI

from backend.app.api.analyses import router as analyses_router
from backend.app.api.catalog import router as catalog_router
from backend.app.api.series import router as series_router

app = FastAPI(
    title="Anomaly Zero API",
    description="API inicial para explorar tendencias de sistemas terrestres.",
    version="0.1.0",
)
app.include_router(catalog_router)
app.include_router(series_router)
app.include_router(analyses_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Report whether the API process is responding."""
    return {"status": "ok", "service": "anomaly-zero-api"}
