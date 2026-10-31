# -*- coding: utf-8 -*-
"""
Tests for Multi-Tenant Workspace & Graph Isolation.
Verifies:
1. Unauthenticated requests to workspace endpoints are rejected with 401 Unauthorized.
2. User A cannot access or see User B's workspace (rejected with 403 Forbidden).
3. User A can successfully access their own workspace.
"""
from __future__ import annotations

import io
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.main import app
from backend.app.services.database import connect_sync, disconnect_sync


def test_cross_user_workspace_isolation():
    """Verify that User A and User B cannot read each other's documents or graph."""
    with TestClient(app) as client:
        # 1. Register User A
        email_a = f"alice_{uuid.uuid4().hex[:6]}@echoes.ai"
        resp_a = client.post(
            "/api/v1/auth/register",
            json={"email": email_a, "password": "Password123!", "display_name": "Alice"},
        )
        assert resp_a.status_code == 201
        data_a = resp_a.json()
        token_a = data_a["access_token"]
        ws_a = data_a["workspace_id"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # 2. Register User B
        email_b = f"bob_{uuid.uuid4().hex[:6]}@echoes.ai"
        resp_b = client.post(
            "/api/v1/auth/register",
            json={"email": email_b, "password": "Password123!", "display_name": "Bob"},
        )
        assert resp_b.status_code == 201
        data_b = resp_b.json()
        token_b = data_b["access_token"]
        ws_b = data_b["workspace_id"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 3. Unauthenticated request to Alice's workspace -> 401 Unauthorized
        unauth_resp = client.get(f"/api/v1/workspaces/{ws_a}/documents")
        assert unauth_resp.status_code == 401

        # 4. User B attempts to access Alice's workspace documents -> 403 Forbidden
        b_access_a_docs = client.get(
            f"/api/v1/workspaces/{ws_a}/documents",
            headers=headers_b,
        )
        assert b_access_a_docs.status_code == 403
        assert "access" in b_access_a_docs.json()["detail"].lower()

        # 5. User B attempts to view Alice's Knowledge Graph -> 403 Forbidden
        b_access_a_graph = client.get(
            f"/api/v1/workspaces/{ws_a}/graph",
            headers=headers_b,
        )
        assert b_access_a_graph.status_code == 403

        # 6. User B attempts to view Alice's Timeline -> 403 Forbidden
        b_access_a_timeline = client.get(
            f"/api/v1/workspaces/{ws_a}/timeline",
            headers=headers_b,
        )
        assert b_access_a_timeline.status_code == 403

        # 7. User B attempts to query Alice's workspace -> 403 Forbidden
        b_query_a = client.post(
            f"/api/v1/workspaces/{ws_a}/query",
            json={"query": "What secrets does Alice have?"},
            headers=headers_b,
        )
        assert b_query_a.status_code == 403

        # 8. User A successfully accesses her own workspace -> 200 OK
        a_access_own_docs = client.get(
            f"/api/v1/workspaces/{ws_a}/documents",
            headers=headers_a,
        )
        assert a_access_own_docs.status_code == 200

        # 9. User A successfully accesses her own graph -> 200 OK
        a_access_own_graph = client.get(
            f"/api/v1/workspaces/{ws_a}/graph",
            headers=headers_a,
        )
        assert a_access_own_graph.status_code == 200

    # Cleanup test data
    try:
        db = connect_sync(settings.MONGODB_URI, settings.MONGODB_DATABASE)
        db["users"].delete_many({"email": {"$in": [email_a, email_b]}})
        db["workspaces"].delete_many({"workspace_id": {"$in": [ws_a, ws_b]}})
        disconnect_sync()
    except Exception:
        pass
