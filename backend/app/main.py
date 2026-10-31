# -*- coding: utf-8 -*-
"""
Echoes Search — FastAPI Application Entrypoint
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import auth, documents, graph, health, query, search
from .core.config import settings
from .services.database import connect_async, disconnect_async

# Setup logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("echoes")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager:
    Initializes storage dirs & database connection on startup,
    cleans up connection on shutdown.
    """
    logger.info("[STARTUP] Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    
    # 1. Ensure required storage directories exist
    settings.upload_dir_path.mkdir(parents=True, exist_ok=True)
    settings.chroma_path_path.mkdir(parents=True, exist_ok=True)
    logger.info("[STARTUP] Storage directories verified: %s, %s", settings.upload_dir_path, settings.chroma_path_path)

    # 2. Connect to MongoDB Atlas (Motor async)
    try:
        await connect_async(settings.MONGODB_URI, settings.MONGODB_DATABASE)
        logger.info("[STARTUP] MongoDB Atlas connection established successfully.")
    except Exception as exc:
        logger.error("[STARTUP ERROR] Failed to connect to MongoDB Atlas: %s", exc)
        # We don't crash here so health check can report the 503 error gracefully
    
    yield
    
    # 3. Disconnect on shutdown
    logger.info("[SHUTDOWN] Closing database connections...")
    await disconnect_async()
    logger.info("[SHUTDOWN] Application shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Personal knowledge retrieval and reconstruction RAG engine.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(graph.router)
app.include_router(query.router)
