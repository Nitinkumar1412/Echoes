# -*- coding: utf-8 -*-
"""Pydantic schemas for Knowledge Graph and Timeline API responses."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    mentions: int = 1


class GraphEdge(BaseModel):
    id: str
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    label: str
    confidence: float = 1.0
    evidence_count: int = 1

    model_config = {"populate_by_name": True}


class GraphDataResponse(BaseModel):
    workspace_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class TimelineItemResponse(BaseModel):
    event_id: str
    title: str
    event_type: str
    original_expression: str
    normalized_date: Optional[datetime] = None
    date_precision: str
    participants: List[str] = []


class TimelineResponse(BaseModel):
    workspace_id: str
    total_events: int
    events: List[TimelineItemResponse]


class EntityItemResponse(BaseModel):
    entity_id: str
    canonical_name: str
    entity_type: str
    aliases: List[str] = []
    mention_count: int = 1
    document_count: int = 1


class EntityListResponse(BaseModel):
    workspace_id: str
    total_entities: int
    entities: List[EntityItemResponse]
