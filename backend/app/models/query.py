# -*- coding: utf-8 -*-
"""Query model — immutable audit log of queries, retrieval results, and grounded answers."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import Field

from .base import EchoesBaseModel, utcnow


class QueryStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnswerConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class DateRangeFilter(EchoesBaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class QueryFilters(EchoesBaseModel):
    document_ids: list[str] = Field(default_factory=list)
    date_range: Optional[DateRangeFilter] = None
    entity_types: list[str] = Field(default_factory=list)


class QueryInput(EchoesBaseModel):
    query_text: str
    filters: QueryFilters = Field(default_factory=QueryFilters)


class RetrievedChunkRef(EchoesBaseModel):
    chunk_id: str
    score: float
    rank: int


class QueryRetrieval(EchoesBaseModel):
    semantic_chunks: list[RetrievedChunkRef] = Field(default_factory=list)
    bm25_chunks: list[RetrievedChunkRef] = Field(default_factory=list)
    reranked_chunks: list[RetrievedChunkRef] = Field(default_factory=list)
    expanded_entity_ids: list[str] = Field(default_factory=list)
    expanded_chunk_ids: list[str] = Field(default_factory=list)


class QueryAnswer(EchoesBaseModel):
    text: Optional[str] = None
    model: str = "gemini-2.5-flash"
    confidence: AnswerConfidence = AnswerConfidence.MEDIUM
    has_uncertainty: bool = False


class QueryCitation(EchoesBaseModel):
    chunk_id: str
    document_id: str
    document_name: str                  # Denormalized for durability if doc is deleted
    excerpt: str
    relevance_score: float = Field(default=1.0)


class QueryTimelineItem(EchoesBaseModel):
    event_id: str
    title: str
    normalized_date: Optional[datetime] = None


class QueryPerformance(EchoesBaseModel):
    total_ms: int = 0
    retrieval_ms: int = 0
    reranking_ms: int = 0
    generation_ms: int = 0


class Query(EchoesBaseModel):
    """
    MongoDB collection: queries
    Primary key: query_id (UUID string)

    Design: Append-only audit log. Queries are never modified after completion.
    """
    query_id: str = Field(default_factory=lambda: str(uuid4()))
    workspace_id: str                   # ref: workspaces.workspace_id
    user_id: str                        # ref: users.user_id
    input: QueryInput
    retrieval: QueryRetrieval = Field(default_factory=QueryRetrieval)
    answer: Optional[QueryAnswer] = None
    citations: list[QueryCitation] = Field(default_factory=list)
    timeline: list[QueryTimelineItem] = Field(default_factory=list)
    performance: QueryPerformance = Field(default_factory=QueryPerformance)
    status: QueryStatus = QueryStatus.PROCESSING
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
