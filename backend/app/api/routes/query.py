# -*- coding: utf-8 -*-
"""Query and grounded answer generation API routes."""
from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.api.dependencies import verify_workspace_access
from backend.app.models.user import User
from backend.app.models.workspace import Workspace
from backend.app.schemas.query import (
    AskQueryRequest,
    AskQueryResponse,
    CitationItem,
    PerformanceSummary,
    QueryHistoryResponse,
    TimelineSummaryItem,
)
from backend.app.services.database import get_async_db
from backend.app.services.generation.service import QueryService

logger = logging.getLogger("echoes.api.query")

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/query",
    tags=["RAG & Question Answering"],
)


@router.post("", response_model=AskQueryResponse, status_code=status.HTTP_200_OK)
async def ask_question(
    workspace_id: str,
    payload: AskQueryRequest,
    db: AsyncIOMotorDatabase = Depends(get_async_db),
    access: tuple[Workspace, User] = Depends(verify_workspace_access),
) -> AskQueryResponse:
    """
    Ask a question over the authenticated user's workspace documents ONLY.
    Executes Hybrid Retrieval -> Knowledge Graph Expansion -> Grounded Generation
    -> Citation Verification -> Audit Logging in MongoDB.
    Cross-user data access is impossible — workspace membership is enforced.
    """
    _, current_user = access
    service = QueryService(db)
    try:
        res = await service.answer_query(
            workspace_id=workspace_id,
            query_text=payload.query,
            user_id=current_user.user_id,  # Always use authenticated user's ID
            document_ids=payload.document_ids,
            top_k=payload.top_k,
        )

        return AskQueryResponse(
            query_id=res["query_id"],
            workspace_id=res["workspace_id"],
            query=res["query"],
            answer=res["answer"],
            confidence=res["confidence"],
            has_uncertainty=res["has_uncertainty"],
            citations=[CitationItem(**c) for c in res["citations"]],
            timeline=[TimelineSummaryItem(**t) for t in res["timeline"]],
            performance=PerformanceSummary(**res["performance"]),
            created_at=res["created_at"],
        )
    except Exception as exc:
        logger.error("[QUERY ROUTE ERROR] Failed to answer query: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {exc}",
        )


@router.get("/history", response_model=QueryHistoryResponse, status_code=status.HTTP_200_OK)
async def get_query_history(
    workspace_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_async_db),
    access: tuple[Workspace, User] = Depends(verify_workspace_access),
) -> QueryHistoryResponse:
    """Retrieve query audit log history for this workspace (authenticated members only)."""
    cursor = db["queries"].find(
        {"workspace_id": workspace_id},
    ).sort("created_at", -1).limit(limit)

    query_docs = await cursor.to_list(length=limit)

    items = []
    for q in query_docs:
        ans = q.get("answer", {})
        inp = q.get("input", {})
        perf = q.get("performance", {})
        items.append(
            AskQueryResponse(
                query_id=q["query_id"],
                workspace_id=q["workspace_id"],
                query=inp.get("query_text", ""),
                answer=ans.get("text", "") or "",
                confidence=ans.get("confidence", "medium"),
                has_uncertainty=ans.get("has_uncertainty", False),
                citations=[CitationItem(**c) for c in q.get("citations", [])],
                timeline=[TimelineSummaryItem(**t) for t in q.get("timeline", [])],
                performance=PerformanceSummary(**perf) if perf else PerformanceSummary(),
                created_at=q.get("created_at"),
            )
        )

    return QueryHistoryResponse(
        workspace_id=workspace_id,
        total_queries=len(items),
        queries=items,
    )
