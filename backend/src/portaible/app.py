"""FastAPI application entrypoint — wires routers and lifespan."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import decisions as decisions_router
from .api import jobs as jobs_router
from .api import pipeline as pipeline_router
from .api import profiles as profiles_router
from .api import prompt as prompt_router
from .api import prompt_bank as prompt_bank_router
from .api import sessions as sessions_router
from .api import source as source_router
from .config import settings
from .infrastructure.db import create_all, dispose_engine, init_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.workspace_dir).mkdir(parents=True, exist_ok=True)
    (Path(settings.workspace_dir) / "sessions").mkdir(parents=True, exist_ok=True)

    init_engine(settings.database_url)
    await create_all()

    logger.info("portAIble starting — workspace=%s, ai_pipeline=%s, db=%s",
                settings.workspace_dir, settings.ai_pipeline_url, settings.database_url)
    yield
    await dispose_engine()
    logger.info("portAIble shutting down")


def create_app() -> FastAPI:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = FastAPI(
        title="portAIble",
        version="0.1.0",
        description="Interactive prompt-building experience for AI-driven code porting",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.frontend_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(sessions_router.router)
    app.include_router(source_router.router)
    app.include_router(profiles_router.router)
    app.include_router(decisions_router.router)
    app.include_router(jobs_router.router)
    app.include_router(prompt_router.router)
    app.include_router(pipeline_router.router)
    app.include_router(prompt_bank_router.router)

    @app.get("/api/health")
    async def health() -> dict:
        return {"ok": True, "workspace_dir": settings.workspace_dir}

    return app


app = create_app()
