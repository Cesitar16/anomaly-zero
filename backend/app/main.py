"""Minimal API entry point for Anomaly Zero."""

import os
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.analyses import router as analyses_router
from backend.app.api.catalog import router as catalog_router
from backend.app.api.series import router as series_router

app = FastAPI(
    title="Anomaly Zero API",
    description="API inicial para explorar tendencias de sistemas terrestres.",
    version="0.1.0",
)

frontend_origin = os.environ.get("ANOMALY_ZERO_FRONTEND_ORIGIN", "").rstrip("/")
if frontend_origin:
    origin = urlsplit(frontend_origin)
    if (
        origin.scheme not in {"http", "https"}
        or not origin.hostname
        or origin.username is not None
        or origin.password is not None
        or origin.path
        or origin.query
        or origin.fragment
    ):
        raise ValueError("ANOMALY_ZERO_FRONTEND_ORIGIN must be an HTTP(S) origin")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[frontend_origin],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

app.include_router(catalog_router)
app.include_router(series_router)
app.include_router(analyses_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Report whether the API process is responding."""
    return {"status": "ok", "service": "anomaly-zero-api"}
