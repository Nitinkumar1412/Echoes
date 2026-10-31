# -*- coding: utf-8 -*-
"""Domain models for Echoes Search."""
from .base import EchoesBaseModel, utcnow
from .chunk import (
    Chunk,
    ChunkContent,
    ChunkingMeta,
    ChunkLocation,
    ChunkVector,
)
from .document import (
    ContentMeta,
    Document,
    DocumentFile,
    FileType,
    ProcessingInfo,
    ProcessingStatus,
)
from .entity import (
    Entity,
    EntityAttributes,
    EntityIdentity,
    EntityProvenance,
    EntityStats,
    EntityType,
)
from .event import (
    DatePrecision,
    Event,
    EventProvenance,
    EventTemporal,
    EventType,
)
from .query import (
    AnswerConfidence,
    DateRangeFilter,
    Query,
    QueryAnswer,
    QueryCitation,
    QueryFilters,
    QueryInput,
    QueryPerformance,
    QueryRetrieval,
    QueryStatus,
    QueryTimelineItem,
    RetrievedChunkRef,
)
from .relationship import (
    Relationship,
    RelationshipDirection,
    RelationshipEvidence,
    RelationshipTemporal,
    RelationshipType,
    TargetEntityType,
)
from .user import User, UserSettings
from .workspace import MemberRole, Workspace, WorkspaceMember, WorkspaceStats

__all__ = [
    # Base
    "EchoesBaseModel",
    "utcnow",
    # User
    "User",
    "UserSettings",
    # Workspace
    "Workspace",
    "WorkspaceMember",
    "WorkspaceStats",
    "MemberRole",
    # Document
    "Document",
    "DocumentFile",
    "ContentMeta",
    "ProcessingInfo",
    "FileType",
    "ProcessingStatus",
    # Chunk
    "Chunk",
    "ChunkContent",
    "ChunkLocation",
    "ChunkingMeta",
    "ChunkVector",
    # Entity
    "Entity",
    "EntityIdentity",
    "EntityAttributes",
    "EntityProvenance",
    "EntityStats",
    "EntityType",
    # Event
    "Event",
    "EventType",
    "EventTemporal",
    "DatePrecision",
    "EventProvenance",
    # Relationship
    "Relationship",
    "RelationshipType",
    "TargetEntityType",
    "RelationshipDirection",
    "RelationshipEvidence",
    "RelationshipTemporal",
    # Query
    "Query",
    "QueryStatus",
    "AnswerConfidence",
    "DateRangeFilter",
    "QueryFilters",
    "QueryInput",
    "RetrievedChunkRef",
    "QueryRetrieval",
    "QueryAnswer",
    "QueryCitation",
    "QueryTimelineItem",
    "QueryPerformance",
]
