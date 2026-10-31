# -*- coding: utf-8 -*-
"""Entity model — named things extracted across documents in a workspace."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import Field, field_validator

from .base import EchoesBaseModel, utcnow


class EntityType(str, Enum):
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    PROJECT = "PROJECT"
    CONCEPT = "CONCEPT"
    LOCATION = "LOCATION"
    TECHNOLOGY = "TECHNOLOGY"
    DECISION = "DECISION"
    OTHER = "OTHER"


class EntityIdentity(EchoesBaseModel):
    canonical_name: str                 # primary, normalized name
    aliases: list[str] = Field(default_factory=list)   # alternative names for fuzzy matching
    entity_type: EntityType


class EntityAttributes(EchoesBaseModel):
    """Type-specific attributes — not all fields apply to all entity types."""
    role: Optional[str] = None          # e.g. "Team Lead", "Investor"
    organization: Optional[str] = None
    domain: Optional[str] = None        # e.g. "Healthcare", "Engineering"


class EntityProvenance(EchoesBaseModel):
    """A single mention of this entity, with its source location."""
    document_id: str
    chunk_id: str
    excerpt: str                        # the sentence where the entity was found
    confidence: float = Field(ge=0.0, le=1.0)


class EntityStats(EchoesBaseModel):
    """Denormalized counters updated during entity extraction."""
    mention_count: int = 0
    document_count: int = 0


class Entity(EchoesBaseModel):
    """
    MongoDB collection: entities
    Primary key: entity_id (UUID string)

    Design: One entity per canonical name per workspace.
    "Nitin" appearing in 3 documents → 1 entity with 3 provenance entries.
    Entity resolution (deduplication) uses RapidFuzz at extraction time.
    """
    entity_id: str = Field(default_factory=lambda: str(uuid4()))
    workspace_id: str                   # ref: workspaces.workspace_id
    identity: EntityIdentity
    description: Optional[str] = None  # AI-generated one-line summary
    attributes: EntityAttributes = Field(default_factory=EntityAttributes)
    provenance: list[EntityProvenance] = Field(default_factory=list)
    stats: EntityStats = Field(default_factory=EntityStats)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @classmethod
    def create(
        cls,
        workspace_id: str,
        canonical_name: str,
        entity_type: EntityType,
        aliases: Optional[list[str]] = None,
    ) -> "Entity":
        return cls(
            workspace_id=workspace_id,
            identity=EntityIdentity(
                canonical_name=canonical_name,
                entity_type=entity_type,
                aliases=aliases or [],
            ),
        )
