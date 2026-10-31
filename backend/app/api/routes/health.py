# -*- coding: utf-8 -*-
"""Health check and status API routes."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ...core.config import settings
from ...services.database import get_async_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, Any]:
    """
    Check the health of the application and its connection to MongoDB Atlas.
    Returns HTTP 200 if healthy, or 503 if the database ping fails.
    """
    try:
        db = get_async_db()
        # Ping the MongoDB database
        await db.command("ping")
        return {
            "status": "ok",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "database": "connected",
            "db_name": settings.MONGODB_DATABASE,
        }
    except Exception as exc:
        logger.error("[HEALTH] Database health check failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "app": settings.APP_NAME,
                "database": "disconnected",
                "error": str(exc),
            },
        )


@router.get("/", status_code=status.HTTP_200_OK)
async def root() -> dict[str, str]:
    """Basic root service info."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }
