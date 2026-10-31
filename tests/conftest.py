# -*- coding: utf-8 -*-
"""Pytest configuration and global fixtures for Echoes test suite."""
from __future__ import annotations

import pytest
from backend.app.api.dependencies import verify_workspace_access
from backend.app.main import app
from backend.app.models.user import User
from backend.app.models.workspace import Workspace


@pytest.fixture(autouse=True)
def auto_mock_workspace_access(request):
    """
    For integration tests outside test_auth.py and test_workspace_isolation.py,
    auto-mock verify_workspace_access so individual pipeline tests don't fail
    due to missing JWT bearer tokens or workspace registration.
    """
    if "test_auth" in request.node.nodeid or "test_workspace_isolation" in request.node.nodeid:
        yield
        return

    mock_user = User(
        user_id="usr_test_pipeline",
        email="test_pipeline@echoes.ai",
        display_name="Pipeline Tester",
        hashed_password="mock_hashed_password",
    )

    async def _mock_verify_workspace_access(workspace_id: str):
        ws = Workspace.create(
            name=f"Workspace {workspace_id}",
            owner_id=mock_user.user_id,
        )
        ws.workspace_id = workspace_id
        return ws, mock_user

    app.dependency_overrides[verify_workspace_access] = _mock_verify_workspace_access
    try:
        yield
    finally:
        app.dependency_overrides.pop(verify_workspace_access, None)
