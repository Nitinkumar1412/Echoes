# -*- coding: utf-8 -*-
"""
Echoes — Database Service
Provides both async (Motor) client for FastAPI and sync (PyMongo) client for scripts/tests.

Windows SSL Note: tlsAllowInvalidCertificates=True is required due to Python 3.13 +
OpenSSL 3.0 TLS handshake incompatibility with MongoDB Atlas on Windows.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import certifi
from dotenv import load_dotenv

# Load .env from project root, always — works regardless of CWD
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=_ROOT / ".env", override=True)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Shared TLS kwargs (Windows Python 3.13 fix)
# ─────────────────────────────────────────────
_TLS_KWARGS = {
    "tls": True,
    "tlsCAFile": certifi.where(),
    "tlsAllowInvalidCertificates": True,   # Required on Windows + OpenSSL 3.0
}


# ─────────────────────────────────────────────
# Async client (Motor) — used by FastAPI
# ─────────────────────────────────────────────
try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

    _async_client: Optional[AsyncIOMotorClient] = None
    _async_db: Optional[AsyncIOMotorDatabase] = None

    async def connect_async(uri: str, db_name: str) -> AsyncIOMotorDatabase:
        """Call once at FastAPI startup (lifespan)."""
        global _async_client, _async_db
        import asyncio

        try:
            running_loop = asyncio.get_running_loop()
            client_loop = getattr(_async_client, "io_loop", None) or getattr(_async_client, "_loop", None)
            if _async_client is not None and client_loop and (client_loop.is_closed() or client_loop is not running_loop):
                _async_client = None
                _async_db = None
        except Exception:
            _async_client = None
            _async_db = None

        if _async_client is None:
            _async_client = AsyncIOMotorClient(
                uri,
                serverSelectionTimeoutMS=15000,
                connectTimeoutMS=15000,
                **_TLS_KWARGS,
            )
            # Verify connection
            await _async_client.admin.command("ping")
            _async_db = _async_client[db_name]
            logger.info("[DB] Async MongoDB connected — db: %s", db_name)
        return _async_db

    async def disconnect_async() -> None:
        """Call at FastAPI shutdown."""
        global _async_client, _async_db
        if _async_client:
            _async_client.close()
            _async_client = None
            _async_db = None
            logger.info("[DB] Async MongoDB disconnected")

    def get_async_db() -> AsyncIOMotorDatabase:
        """FastAPI dependency — returns the active async database."""
        if _async_db is None:
            raise RuntimeError("Async DB not initialised. Call connect_async() first.")
        return _async_db

except ImportError:
    logger.warning("[DB] motor not installed — async DB unavailable")
    AsyncIOMotorClient = None  # type: ignore
    AsyncIOMotorDatabase = None  # type: ignore


# ─────────────────────────────────────────────
# Sync client (PyMongo) — used by CLI / tests
# ─────────────────────────────────────────────
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

_sync_client: Optional[MongoClient] = None
_sync_db: Optional[Database] = None


def connect_sync(uri: str, db_name: str) -> Database:
    """Connect and return a synchronous database handle."""
    global _sync_client, _sync_db
    if _sync_client is None:
        _sync_client = MongoClient(
            uri,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=10000,
            **_TLS_KWARGS,
        )
        _sync_client.admin.command("ping")   # raises on failure
        _sync_db = _sync_client[db_name]
        logger.info("[DB] Sync MongoDB connected — db: %s", db_name)
    return _sync_db


def disconnect_sync() -> None:
    global _sync_client, _sync_db
    if _sync_client:
        _sync_client.close()
        _sync_client = None
        _sync_db = None
        logger.info("[DB] Sync MongoDB disconnected")


def get_sync_db() -> Database:
    if _sync_db is None:
        raise RuntimeError("Sync DB not initialised. Call connect_sync() first.")
    return _sync_db


# ─────────────────────────────────────────────
# Quick-test (python database.py)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    uri = os.getenv("MONGODB_URI", "")
    db_name = os.getenv("MONGODB_DATABASE", "echoes_db")

    if not uri or "YOUR_USERNAME" in uri:
        print("[ERROR] Set MONGODB_URI in .env first.")
        sys.exit(1)

    print(f"Connecting to: {uri[:40]}...")
    try:
        db = connect_sync(uri, db_name)
        col = db["_connection_test"]

        # Insert → Read → Delete
        ins = col.insert_one({"source": "Echoes connection test"})
        doc = col.find_one({"_id": ins.inserted_id})
        col.delete_one({"_id": ins.inserted_id})

        print(f"[OK] Insert/Read/Delete successful. Doc: {doc}")
        disconnect_sync()
        print("\n[SUCCESS] MongoDB Atlas is fully operational!")
    except (ServerSelectionTimeoutError, ConnectionFailure) as exc:
        print(f"[FAIL] {exc}")
        sys.exit(1)
