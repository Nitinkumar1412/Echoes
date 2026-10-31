# -*- coding: utf-8 -*-
"""
Workspace access control dependency.
Verifies that the currently authenticated user is a member of the requested workspace.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.models.user import User
from backend.app.models.workspace import Workspace
from backend.app.services.auth import get_current_user, get_optional_current_user
from backend.app.services.database import get_async_db

logger = logging.getLogger("echoes.deps")


async def verify_workspace_access(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_async_db),
) -> tuple[Workspace, User]:
    """
    FastAPI dependency that:
    1. Enforces the user is authenticated (Bearer token required).
    2. Verifies the requested workspace_id exists.
    3. Verifies the current user is a member of that workspace.

    Returns (workspace, current_user) if all checks pass.
    Raises 403 Forbidden if the user does not have access.
    """
    doc = await db["workspaces"].find_one({"workspace_id": workspace_id, "is_deleted": False})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace '{workspace_id}' not found.",
        )

    # Check membership
    members = doc.get("members", [])
    member_ids = [m["user_id"] for m in members]
    if current_user.user_id not in member_ids:
        logger.warning(
            "[ACCESS DENIED] User %s attempted to access workspace %s without membership.",
            current_user.user_id,
            workspace_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this workspace.",
        )

    doc_data = dict(doc)
    doc_data.pop("_id", None)
    workspace = Workspace.model_validate(doc_data)
    return workspace, current_user


async def verify_workspace_access_optional(
    workspace_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncIOMotorDatabase = Depends(get_async_db),
) -> tuple[Optional[Workspace], Optional[User]]:
    """
    Optional variant: returns (workspace, user) if authenticated and member,
    else (None, None). Useful for public-facing or demo endpoints.
    """
    if not current_user:
        return None, None
    try:
        workspace, user = await verify_workspace_access(workspace_id, current_user, db)
        return workspace, user
    except HTTPException:
        return None, None
