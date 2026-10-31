# -*- coding: utf-8 -*-
"""Pydantic schemas for search and retrieval API."""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Input payload for hybrid search."""
    query: str = Field(..., min_length=1, description="Search query string")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to return")
    document_ids: Optional[List[str]] = Field(default=None, description="Filter search to specific documents")


class SearchResultItem(BaseModel):
    """An individual ranked retrieved chunk."""
    chunk_id: str
    document_id: str
    document_name: str
    text: str
    score: float
    rank: int
    page_number: Optional[int] = 1
    retrieval_method: str               # "semantic" | "bm25" | "hybrid"


class SearchResponse(BaseModel):
    """Response returned by the hybrid search endpoint."""
    workspace_id: str
    query: str
    total_results: int
    results: List[SearchResultItem]
    timing_ms: Dict[str, int]
