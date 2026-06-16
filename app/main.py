from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.analyze import router as analyze_router
from app.routers.health import router as health_router

settings = get_settings()

app = FastAPI(
    title="Imalytix API",
    version="0.1.0",
    description="AI image generation detection and evidence analysis API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"chrome-extension://.*|moz-extension://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(analyze_router, prefix="/api/v1")
