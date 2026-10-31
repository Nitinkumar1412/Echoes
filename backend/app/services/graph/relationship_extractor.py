# -*- coding: utf-8 -*-
"""
Relationship extraction service for Echoes Search.
Extracts evidence-backed edges connecting entities with relationship types.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.models.base import utcnow
from backend.app.models.chunk import Chunk
from backend.app.models.entity import Entity, EntityType
from backend.app.models.relationship import (
    Relationship,
    RelationshipEvidence,
    RelationshipType,
    TargetEntityType,
)

logger = logging.getLogger("echoes.graph.relationship")

_RELATION_PATTERNS = [
    (r"\b(?:worked on|leads|leading|developed|developing|built|building|working on)\b", RelationshipType.WORKED_ON),
    (r"\b(?:manages|managed|supervises|director of|head of)\b", RelationshipType.MANAGES),
    (r"\b(?:created|founded|designed|authored|invented)\b", RelationshipType.CREATED),
    (r"\b(?:attended|joined|participated in|present at)\b", RelationshipType.ATTENDED),
    (r"\b(?:decided|authorized|approved|signed|resolved)\b", RelationshipType.DECIDED),
    (r"\b(?:part of|subsidiary of|division of|belongs to|member of)\b", RelationshipType.PART_OF),
    (r"\b(?:contributed to|assisted with|collaborated with)\b", RelationshipType.CONTRIBUTED_TO),
]


def classify_relation_type(sentence: str) -> RelationshipType:
    """Classify the edge type based on action verbs in the sentence."""
    lower = sentence.lower()
    for pattern, rel_type in _RELATION_PATTERNS:
        if re.search(pattern, lower):
            return rel_type
    return RelationshipType.WORKED_ON


class RelationshipExtractorService:
    """Extracts relationships between co-occurring entities in a chunk."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def extract_and_upsert_chunk_relationships(
        self,
        workspace_id: str,
        chunk: Chunk,
        entities_in_chunk: List[Entity],
    ) -> List[Relationship]:
        """
        Extract relationships between pairs of entities mentioned in the chunk.
        """
        if len(entities_in_chunk) < 2:
            return []

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", chunk.content.text) if s.strip()]
        created_or_updated: List[Relationship] = []

        # Find co-occurrences
        for i in range(len(entities_in_chunk)):
            for j in range(i + 1, len(entities_in_chunk)):
                ent1 = entities_in_chunk[i]
                ent2 = entities_in_chunk[j]

                name1 = ent1.identity.canonical_name.lower().strip()
                name2 = ent2.identity.canonical_name.lower().strip()

                # Skip identical entities or self-loops
                if ent1.entity_id == ent2.entity_id or name1 == name2:
                    continue

                # Find the sentence containing both
                supporting_sentence = None
                for s in sentences:
                    s_lower = s.lower()
                    if name1 in s_lower and name2 in s_lower:
                        supporting_sentence = s
                        break

                # If not in same sentence, only connect if there are few entities in the chunk
                if not supporting_sentence:
                    if len(entities_in_chunk) > 4:
                        continue
                    supporting_sentence = chunk.content.text[:180]

                rel_type = classify_relation_type(supporting_sentence)

                # Direct edge from Person/Org -> Project/Org
                from_id = ent1.entity_id
                to_id = ent2.entity_id
                if ent1.identity.entity_type == EntityType.PROJECT and ent2.identity.entity_type == EntityType.PERSON:
                    from_id, to_id = ent2.entity_id, ent1.entity_id

                if from_id == to_id:
                    continue

                evidence_obj = RelationshipEvidence(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    excerpt=supporting_sentence,
                    confidence=0.85,
                )

                # Check if relationship already exists
                existing = await self.db["relationships"].find_one(
                    {
                        "workspace_id": workspace_id,
                        "from_entity_id": from_id,
                        "to_entity_id": to_id,
                        "relationship_type": rel_type.value,
                    }
                )

                if existing:
                    # Append evidence
                    await self.db["relationships"].update_one(
                        {"relationship_id": existing["relationship_id"]},
                        {
                            "$push": {"evidence": evidence_obj.model_dump()},
                            "$set": {"updated_at": utcnow()},
                        },
                    )
                else:
                    new_rel = Relationship(
                        workspace_id=workspace_id,
                        from_entity_id=from_id,
                        to_entity_id=to_id,
                        to_entity_type=TargetEntityType.ENTITY,
                        relationship_type=rel_type,
                        evidence=[evidence_obj],
                        confidence=0.85,
                    )
                    await self.db["relationships"].insert_one(new_rel.model_dump())
                    created_or_updated.append(new_rel)

        return created_or_updated
