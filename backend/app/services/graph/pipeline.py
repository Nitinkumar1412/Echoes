# -*- coding: utf-8 -*-
"""
Knowledge graph extraction pipeline coordinator.
Processes newly ingested chunks to extract and index entities, events, and relationships.
"""
from __future__ import annotations

import logging
from typing import List

from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.models.chunk import Chunk
from .entity_extractor import EntityExtractorService
from .event_extractor import EventExtractorService
from .relationship_extractor import RelationshipExtractorService

logger = logging.getLogger("echoes.graph.pipeline")


async def extract_and_index_graph_for_chunks(
    db: AsyncIOMotorDatabase,
    workspace_id: str,
    chunks: List[Chunk],
) -> dict:
    """
    Run entity, event, and relationship extraction over chunks in a workspace.
    """
    if not chunks:
        return {"entities": 0, "events": 0, "relationships": 0}

    entity_extractor = EntityExtractorService(db)
    event_extractor = EventExtractorService(db)
    rel_extractor = RelationshipExtractorService(db)

    total_entities = 0
    total_events = 0
    total_relationships = 0

    for chunk in chunks:
        try:
            # 1. Extract and resolve entities
            entities = await entity_extractor.extract_and_upsert_chunk_entities(workspace_id, chunk)
            total_entities += len(entities)

            # 2. Extract events
            participant_ids = [e.entity_id for e in entities if e.identity.entity_type == "PERSON"]
            events = await event_extractor.extract_and_upsert_chunk_events(
                workspace_id, chunk, participant_entity_ids=participant_ids
            )
            total_events += len(events)

            # 3. Extract relationships between co-occurring entities
            relationships = await rel_extractor.extract_and_upsert_chunk_relationships(
                workspace_id, chunk, entities
            )
            total_relationships += len(relationships)

        except Exception as exc:
            logger.warning("[GRAPH PIPELINE] Error extracting graph for chunk %s: %s", chunk.chunk_id, exc)

    logger.info(
        "[GRAPH PIPELINE] Workspace '%s' indexed: %d entities, %d events, %d relationships from %d chunks",
        workspace_id,
        total_entities,
        total_events,
        total_relationships,
        len(chunks),
    )

    return {
        "entities": total_entities,
        "events": total_events,
        "relationships": total_relationships,
    }
