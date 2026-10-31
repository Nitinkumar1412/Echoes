# -*- coding: utf-8 -*-
"""Workspace model — logical container for user document collections."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import Field

from .base import EchoesBaseModel, utcnow


class MemberRole(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class WorkspaceMember(EchoesBaseModel):
    user_id: str
    role: MemberRole
    joined_at: datetime = Field(default_factory=utcnow)


class WorkspaceStats(EchoesBaseModel):
    """Denormalized counters — updated on document operations, eventually consistent."""
    document_count: int = 0
    chunk_count: int = 0
    entity_count: int = 0
    total_size_bytes: int = 0


class Workspace(EchoesBaseModel):
    """
    MongoDB collection: workspaces
    Primary key: workspace_id (UUID string)
    """
    workspace_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    owner_id: str                                   # ref: users.user_id
    members: list[WorkspaceMember] = Field(default_factory=list)
    stats: WorkspaceStats = Field(default_factory=WorkspaceStats)
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @classmethod
    def create(cls, name: str, owner_id: str, description: Optional[str] = None) -> "Workspace":
        """Create a new workspace; owner is automatically added as a member."""
        ws = cls(name=name, owner_id=owner_id, description=description)
        ws.members.append(WorkspaceMember(user_id=owner_id, role=MemberRole.OWNER))
        return ws
