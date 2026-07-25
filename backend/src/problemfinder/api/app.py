"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from problemfinder.api.routers import signals, sources, summaries
from problemfinder.settings import get_settings


def create_app() -> FastAPI:
    app = FastAPI(title="problemfinder", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[get_settings().cors_origin],
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(signals.router)
    app.include_router(summaries.router)
    app.include_router(sources.router)
    return app
