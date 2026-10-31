# -*- coding: utf-8 -*-
"""Relationship model — directed or undirected edges connecting entities and events with evidence."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import Field

from .base import EchoesBaseModel, utcnow


class RelationshipType(str, Enum):
    WORKED_ON = "WORKED_ON"
    SUGGESTED = "SUGGESTED"
    MANAGES = "MANAGES"
    ATTENDED = "ATTENDED"
    DECIDED = "DECIDED"
    PART_OF = "PART_OF"
    KNOWS = "KNOWS"
    REPORTED_TO = "REPORTED_TO"
    CREATED = "CREATED"
    CONTRIBUTED_TO = "CONTRIBUTED_TO"
    OTHER = "OTHER"


class TargetEntityType(str, Enum):
    ENTITY = "entity"
    EVENT = "event"


class RelationshipDirection(str, Enum):
    DIRECTED = "directed"
    UNDIRECTED = "undirected"


class RelationshipEvidence(EchoesBaseModel):
    """Specific chunk excerpt providing evidence for this relationship."""
    chunk_id: str
    document_id: str
    excerpt: str                        # the sentence supporting this relationship
    confidence: float = Field(ge=0.0, le=1.0)


class RelationshipTemporal(EchoesBaseModel):
    """Optional time bounds for time-sensitive relationships (e.g. employment)."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class Relationship(EchoesBaseModel):
    """
    MongoDB collection: relationships
    Primary key: relationship_id (UUID string)

    Design: from_entity_id + to_entity_id + relationship_type is unique per workspace.
    Evidence is appended to evidence[] rather than creating duplicate relationships.
    """
    relationship_id: str = Field(default_factory=lambda: str(uuid4()))
    workspace_id: str                   # ref: workspaces.workspace_id
    from_entity_id: str                 # ref: entities.entity_id
    to_entity_id: str                   # ref: entities.entity_id OR events.event_id
    to_entity_type: TargetEntityType = TargetEntityType.ENTITY
    relationship_type: RelationshipType = RelationshipType.OTHER
    direction: RelationshipDirection = RelationshipDirection.DIRECTED
    evidence: list[RelationshipEvidence] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    temporal: Optional[RelationshipTemporal] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
