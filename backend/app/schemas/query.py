# -*- coding: utf-8 -*-
"""Pydantic schemas for the Query and RAG Answer Generation API."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AskQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="User question or information request")
    user_id: Optional[str] = Field(default="user_default")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional document filters")
    top_k: Optional[int] = Field(default=10, ge=1, le=50)


class CitationItem(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    excerpt: str
    relevance_score: float = 1.0


class TimelineSummaryItem(BaseModel):
    event_id: str
    title: str
    normalized_date: Optional[datetime] = None


class PerformanceSummary(BaseModel):
    total_ms: int = 0
    retrieval_ms: int = 0
    reranking_ms: int = 0
    generation_ms: int = 0


class AskQueryResponse(BaseModel):
    query_id: str
    workspace_id: str
    query: str
    answer: str
    confidence: str                     # "high" | "medium" | "low" | "insufficient_evidence"
    has_uncertainty: bool = False
    citations: List[CitationItem] = []
    timeline: List[TimelineSummaryItem] = []
    performance: PerformanceSummary
    created_at: datetime


class QueryHistoryResponse(BaseModel):
    workspace_id: str
    total_queries: int
    queries: List[AskQueryResponse]
