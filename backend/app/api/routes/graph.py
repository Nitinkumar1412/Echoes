# -*- coding: utf-8 -*-
"""Knowledge Graph and Timeline API routes."""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.api.dependencies import verify_workspace_access
from backend.app.models.user import User
from backend.app.models.workspace import Workspace
from backend.app.schemas.graph import (
    EntityItemResponse,
    EntityListResponse,
    GraphDataResponse,
    GraphEdge,
    GraphNode,
    TimelineItemResponse,
    TimelineResponse,
)
from backend.app.services.database import get_async_db
from backend.app.services.graph.networkx_service import NetworkXGraphService

logger = logging.getLogger("echoes.api.graph")

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}",
    tags=["Knowledge Graph & Timeline"],
)


@router.get("/graph", response_model=GraphDataResponse, status_code=status.HTTP_200_OK)
async def get_workspace_graph(
    workspace_id: str,
    db: AsyncIOMotorDatabase = Depends(get_async_db),
    access: tuple[Workspace, User] = Depends(verify_workspace_access),
) -> GraphDataResponse:
    """
    Retrieve the knowledge graph (entities as nodes, relationships as edges)
    for the authenticated user's workspace ONLY. Other users' graphs are never exposed.
    """
    svc = NetworkXGraphService(db)
    data = await svc.get_graph_visualization_data(workspace_id)
    return GraphDataResponse(
        workspace_id=workspace_id,
        nodes=[GraphNode(**n) for n in data["nodes"]],
        edges=[
            GraphEdge(
                id=e["id"],
                from_node=e["from"],
                to_node=e["to"],
                label=e["label"],
                confidence=e.get("confidence", 1.0),
                evidence_count=e.get("evidence_count", 1),
            )
            for e in data["edges"]
        ],
    )


@router.get("/timeline", response_model=TimelineResponse, status_code=status.HTTP_200_OK)
async def get_workspace_timeline(
    workspace_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncIOMotorDatabase = Depends(get_async_db),
    access: tuple[Workspace, User] = Depends(verify_workspace_access),
) -> TimelineResponse:
    """
    Retrieve chronological timeline of events extracted from this workspace's documents.
    Strictly scoped to the authenticated user's workspace — other users' events never appear.
    """
    cursor = db["events"].find(
        {"workspace_id": workspace_id},
    ).sort("temporal.normalized_date", 1).limit(limit)

    event_docs = await cursor.to_list(length=limit)

    events: List[TimelineItemResponse] = []
    for ed in event_docs:
        temp = ed.get("temporal", {})
        events.append(
            TimelineItemResponse(
                event_id=ed["event_id"],
                title=ed["title"],
                event_type=ed.get("event_type", "OTHER"),
                original_expression=temp.get("original_expression", ""),
                normalized_date=temp.get("normalized_date"),
                date_precision=temp.get("date_precision", "approximate"),
                participants=ed.get("participants", []),
            )
        )

    return TimelineResponse(
        workspace_id=workspace_id,
        total_events=len(events),
        events=events,
    )


@router.get("/entities", response_model=EntityListResponse, status_code=status.HTTP_200_OK)
async def list_workspace_entities(
    workspace_id: str,
    entity_type: Optional[str] = Query(None, description="Filter by type (PERSON, ORGANIZATION, PROJECT, CONCEPT)"),
    limit: int = Query(100, ge=1, le=300),
    db: AsyncIOMotorDatabase = Depends(get_async_db),
    access: tuple[Workspace, User] = Depends(verify_workspace_access),
) -> EntityListResponse:
    """List entities extracted from this workspace's documents (authenticated members only)."""
    query = {"workspace_id": workspace_id}
    if entity_type:
        query["identity.entity_type"] = entity_type.upper()

    cursor = db["entities"].find(query).sort("stats.mention_count", -1).limit(limit)
    entity_docs = await cursor.to_list(length=limit)

    entities: List[EntityItemResponse] = []
    for ed in entity_docs:
        ident = ed.get("identity", {})
        stats = ed.get("stats", {})
        entities.append(
            EntityItemResponse(
                entity_id=ed["entity_id"],
                canonical_name=ident.get("canonical_name", "Unknown"),
                entity_type=ident.get("entity_type", "OTHER"),
                aliases=ident.get("aliases", []),
                mention_count=stats.get("mention_count", 1),
                document_count=stats.get("document_count", 1),
            )
        )

    return EntityListResponse(
        workspace_id=workspace_id,
        total_entities=len(entities),
        entities=entities,
    )


@router.get("/entities/{entity_id}/ego", response_model=GraphDataResponse, status_code=status.HTTP_200_OK)
async def get_entity_ego_graph(
    workspace_id: str,
    entity_id: str,
    radius: int = Query(1, ge=1, le=3),
    db: AsyncIOMotorDatabase = Depends(get_async_db),
    access: tuple[Workspace, User] = Depends(verify_workspace_access),
) -> GraphDataResponse:
    """Retrieve ego subgraph for a specific entity (workspace members only)."""
    svc = NetworkXGraphService(db)
    data = await svc.get_ego_subgraph(workspace_id, entity_id, radius=radius)
    return GraphDataResponse(
        workspace_id=workspace_id,
        nodes=[GraphNode(**n) for n in data["nodes"]],
        edges=[
            GraphEdge(
                id=f"{e['from']}_{e['to']}",
                from_node=e["from"],
                to_node=e["to"],
                label=e.get("label", "CONNECTED_TO"),
            )
            for e in data["edges"]
        ],
    )
