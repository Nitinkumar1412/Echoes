# -*- coding: utf-8 -*-
"""FastAPI endpoint tests for /health and /."""
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.main import app


def test_root_endpoint():
    """Verify GET / returns service info."""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["app"] == settings.APP_NAME
        assert data["version"] == settings.APP_VERSION
        assert "health" in data


def test_health_endpoint():
    """Verify GET /health executes DB ping and returns 200 with connected status."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"
        assert data["db_name"] == settings.MONGODB_DATABASE
