# -*- coding: utf-8 -*-
"""Event model — time-bound occurrences with normalized temporal metadata."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import Field

from .base import EchoesBaseModel, utcnow


class EventType(str, Enum):
    MEETING = "MEETING"
    DECISION = "DECISION"
    MILESTONE = "MILESTONE"
    DISCUSSION = "DISCUSSION"
    TASK = "TASK"
    ASSIGNMENT = "ASSIGNMENT"
    OTHER = "OTHER"


class DatePrecision(str, Enum):
    EXACT = "exact"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    APPROXIMATE = "approximate"


class EventTemporal(EchoesBaseModel):
    """
    Dual temporal representation:
    - original_expression: preserved exactly as found in the text ("last Thursday")
    - normalized_date:     best-effort ISO datetime for sorting and filtering
    - date_precision:      how much to trust normalized_date
    - is_inferred:         true when date was inferred from context, not stated explicitly

    UI must show inferred dates with a caveat.
    """
    original_expression: str
    normalized_date: Optional[datetime] = None
    date_precision: DatePrecision = DatePrecision.APPROXIMATE
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    is_inferred: bool = False


class EventProvenance(EchoesBaseModel):
    chunk_id: str
    document_id: str
    excerpt: str
    confidence: float = Field(ge=0.0, le=1.0)


class Event(EchoesBaseModel):
    """
    MongoDB collection: events
    Primary key: event_id (UUID string)

    Supports temporal reconstruction queries:
    "What happened first?", "When was this discussed?", "What changed between meetings?"
    """
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    workspace_id: str                       # ref: workspaces.workspace_id
    title: str                              # short description
    description: Optional[str] = None
    event_type: EventType
    temporal: EventTemporal
    participants: list[str] = Field(default_factory=list)       # entity_ids (people/orgs)
    related_entities: list[str] = Field(default_factory=list)   # entity_ids (projects, concepts)
    related_documents: list[str] = Field(default_factory=list)  # document_ids
    provenance: list[EventProvenance] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @classmethod
    def create(
        cls,
        workspace_id: str,
        title: str,
        event_type: EventType,
        original_expression: str,
        normalized_date: Optional[datetime] = None,
        date_precision: DatePrecision = DatePrecision.APPROXIMATE,
        is_inferred: bool = False,
    ) -> "Event":
        return cls(
            workspace_id=workspace_id,
            title=title,
            event_type=event_type,
            temporal=EventTemporal(
                original_expression=original_expression,
                normalized_date=normalized_date,
                date_precision=date_precision,
                is_inferred=is_inferred,
            ),
        )
