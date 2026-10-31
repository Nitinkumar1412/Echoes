# -*- coding: utf-8 -*-
"""Hybrid Search and Retrieval API routes."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.api.dependencies import verify_workspace_access
from backend.app.models.user import User
from backend.app.models.workspace import Workspace
from backend.app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from backend.app.services.database import get_async_db
from backend.app.services.retrieval import HybridRetrievalEngine

logger = logging.getLogger("echoes.api.search")

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/search",
    tags=["Search & Retrieval"],
)


@router.post("", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def hybrid_search(
    workspace_id: str,
    payload: SearchRequest,
    db: AsyncIOMotorDatabase = Depends(get_async_db),
    access: tuple[Workspace, User] = Depends(verify_workspace_access),
) -> SearchResponse:
    """
    Execute hybrid search (Semantic Vector Search + BM25 Lexical Search + RRF Reranking).
    Returns ranked evidence chunks with similarity scores, provenance, and timing breakdown.
    Strictly scoped to the authenticated user's workspace — no cross-user data leakage.
    """
    engine = HybridRetrievalEngine(db)
    try:
        search_output = await engine.search(
            workspace_id=workspace_id,
            query_text=payload.query,
            top_k=payload.top_k,
            document_ids=payload.document_ids,
        )

        results = [
            SearchResultItem(
                chunk_id=r["chunk_id"],
                document_id=r["document_id"],
                document_name=r.get("document_name", "Unknown"),
                text=r["text"],
                score=r["score"],
                rank=r["rank"],
                page_number=r.get("page_number", 1),
                retrieval_method=r.get("retrieval_method", "hybrid"),
            )
            for r in search_output["results"]
        ]

        return SearchResponse(
            workspace_id=workspace_id,
            query=payload.query,
            total_results=len(results),
            results=results,
            timing_ms=search_output["timing_ms"],
        )

    except Exception as exc:
        logger.error("[SEARCH ERROR] Hybrid search failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {exc}",
        )
