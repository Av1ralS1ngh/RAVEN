"""FastAPI application entry point.

Defines:
  - Lifespan context manager: TigerGraph startup/shutdown.
  - CORS middleware wired to settings.
  - Route registration for both modules.
  - /health endpoint.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import blast, path
from app.config import get_settings
from app.services.person_seed import seed_famous_nodes
from app.services.tigergraph_client import TigerGraphClient, TigerGraphError

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown.

    Startup:
      1. Build ``TigerGraphClient`` from settings.
      2. Install schemas (idempotent DDL).
      3. Install GSQL queries (idempotent compile+install).
      4. Store client on ``app.state.tg_client`` for dependency injection.

    Shutdown:
      - Log closure notice (pyTigerGraph connections are stateless HTTP calls;
        no explicit teardown is needed, but this hook is the right place to
        add cleanup if we later move to a persistent socket).
    """
    settings = get_settings()

    logger.info("RecruitGraph starting up.")
    client = TigerGraphClient(settings)

    try:
        logger.info("Installing TigerGraph schemas…")
        client.install_schemas()
    except TigerGraphError as exc:
        # Non-fatal on startup — the app can run in degraded mode if TG is
        # down; routes will fail individually rather than blocking the whole
        # process.
        logger.warning("Schema installation skipped: %s", exc)

    try:
        logger.info("Installing TigerGraph queries…")
        client.install_queries()
    except TigerGraphError as exc:
        logger.warning("Query installation skipped: %s", exc)

    try:
        person_count, edge_count = seed_famous_nodes(client)
        logger.info(
            "PersonGraph startup seed complete: %d nodes, %d edges.",
            person_count,
            edge_count,
        )
    except TigerGraphError as exc:
        logger.warning("PersonGraph startup seed skipped: %s", exc)
    except Exception as exc:
        logger.warning("PersonGraph startup seed failed: %s", exc)

    app.state.tg_client = client
    logger.info("TigerGraph client ready.")

    yield  # ← application runs here

    logger.info("TigerGraph connections closed.")


# ─────────────────────────────────────────────────────────────────────────────
# Application factory
# ─────────────────────────────────────────────────────────────────────────────

_settings = get_settings()

app = FastAPI(
    title="RecruitGraph API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(path.router, prefix="/api/path", tags=["path"])
app.include_router(blast.router, prefix="/api/blast", tags=["blast"])


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────


@app.get("/health", tags=["meta"])
async def health_check() -> dict[str, str]:
    """Liveness probe — always returns 200 if the process is alive."""
    return {"status": "ok"}
