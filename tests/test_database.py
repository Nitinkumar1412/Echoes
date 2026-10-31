# -*- coding: utf-8 -*-
"""Database integration tests with MongoDB Atlas."""
import pytest
from backend.app.core.config import settings
from backend.app.services.database import (
    connect_async,
    connect_sync,
    disconnect_async,
    disconnect_sync,
    get_async_db,
    get_sync_db,
)


def test_sync_db_connection_and_crud():
    """Verify synchronous PyMongo connectivity, ping, and basic CRUD."""
    db = connect_sync(settings.MONGODB_URI, settings.MONGODB_DATABASE)
    assert db is not None

    test_col = db["_pytest_sync_test"]
    res = test_col.insert_one({"item": "echoes_test", "value": 42})
    assert res.inserted_id is not None

    doc = test_col.find_one({"_id": res.inserted_id})
    assert doc is not None
    assert doc["item"] == "echoes_test"
    assert doc["value"] == 42

    del_res = test_col.delete_one({"_id": res.inserted_id})
    assert del_res.deleted_count == 1

    disconnect_sync()


@pytest.mark.anyio
async def test_async_db_connection_and_ping():
    """Verify asynchronous Motor connectivity and ping command."""
    db = await connect_async(settings.MONGODB_URI, settings.MONGODB_DATABASE)
    assert db is not None

    # Ping database
    pong = await db.command("ping")
    assert pong.get("ok") == 1.0

    # Quick insert and cleanup
    test_col = db["_pytest_async_test"]
    ins = await test_col.insert_one({"async": True, "ping": "pong"})
    assert ins.inserted_id is not None

    doc = await test_col.find_one({"_id": ins.inserted_id})
    assert doc["ping"] == "pong"

    await test_col.delete_one({"_id": ins.inserted_id})
    await disconnect_async()
