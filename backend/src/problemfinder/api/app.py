"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from problemfinder.api.routers import (
    runs,
    signals,
    sources,
    summaries,
    theme_suggestions,
    themes,
    trends,
)
from problemfinder.settings import get_settings


def create_app() -> FastAPI:
    app = FastAPI(title="problemfinder", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[get_settings().cors_origin],
        # Single-user local tool: the dev server may sit on any localhost port
        # (Vite falls back when 5173 is taken), so any localhost origin is fine.
        allow_origin_regex=r"http://localhost:\d+",
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(signals.router)
    app.include_router(summaries.router)
    app.include_router(themes.router)
    app.include_router(theme_suggestions.router)
    app.include_router(trends.router)
    app.include_router(sources.router)
    app.include_router(runs.router)
    return app
