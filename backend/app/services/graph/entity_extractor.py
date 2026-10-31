# -*- coding: utf-8 -*-
"""
Entity extraction and fuzzy deduplication service.
Identifies People, Organizations, Projects, and Concepts from text chunks and resolves
duplicates against existing workspace entities using RapidFuzz.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase
from rapidfuzz import fuzz

from backend.app.models.base import utcnow
from backend.app.models.chunk import Chunk
from backend.app.models.entity import (
    Entity,
    EntityIdentity,
    EntityProvenance,
    EntityType,
)

logger = logging.getLogger("echoes.graph.entity")

# Regex patterns for named entity detection
_TITLE_NAME_REGEX = re.compile(
    r"\b(?:Dr\.|Mr\.|Mrs\.|Ms\.|Prof\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
)
_CAPITALIZED_PHRASE_REGEX = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b"
)
_PROJECT_REGEX = re.compile(
    r"\b(?:[Pp]roject|[Oo]peration|[Ii]nitiative|[Tt]ask [Ff]orce)\s+([A-Z][A-Za-z0-9_-]+(?:\s+[A-Z][A-Za-z0-9_-]+)*)\b"
)
_ORG_SUFFIXES = ("Inc", "LLC", "Ltd", "Corp", "Corporation", "Technologies", "Tech", "Labs", "Group", "AI", "Hospital", "University")

_STOP_PHRASES = {
    "the", "this is", "in late", "for the", "on the", "at the", "with the", "from the",
    "by the", "to the", "according to", "based on", "as well", "in addition", "in order",
    "due to", "because of", "one of", "each of", "part of", "first of", "last of",
    "all of", "some of", "many of", "such as", "as an", "as a", "for example",
}


def detect_entity_type_and_canonical_name(candidate: str) -> Tuple[str, EntityType]:
    """Classify entity type and normalize candidate text."""
    cand = candidate.strip()

    # Project patterns
    if re.search(r"\b(?:Project|Initiative|Task Force|App)\b", cand, re.IGNORECASE):
        clean_name = re.sub(r"^(?:Project|Initiative|Task Force)\s+", "", cand, flags=re.IGNORECASE).strip()
        return clean_name or cand, EntityType.PROJECT

    # Organization suffixes
    for suffix in _ORG_SUFFIXES:
        if re.search(rf"\b{suffix}\b", cand, re.IGNORECASE):
            return cand, EntityType.ORGANIZATION

    # Check for person honorific
    honorific_match = _TITLE_NAME_REGEX.search(cand)
    if honorific_match:
        return honorific_match.group(1).strip(), EntityType.PERSON

    # Fallback: multi-word capitalized phrase usually a Person or Concept
    words = cand.split()
    if len(words) == 2:
        return cand, EntityType.PERSON

    return cand, EntityType.CONCEPT


class EntityExtractorService:
    """Extracts entities from chunks and deduplicates within workspace."""

    def __init__(self, db: AsyncIOMotorDatabase, fuzzy_threshold: float = 85.0):
        self.db = db
        self.fuzzy_threshold = fuzzy_threshold

    def extract_from_text(self, text: str) -> List[Tuple[str, EntityType, str]]:
        """
        Extract candidate entities from a string.
        Returns list of (canonical_name, entity_type, sentence_excerpt).
        """
        results: List[Tuple[str, EntityType, str]] = []
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

        for sent in sentences:
            # 1. Projects
            for m in _PROJECT_REGEX.finditer(sent):
                full_match = m.group(0)
                name, etype = detect_entity_type_and_canonical_name(full_match)
                results.append((name, etype, sent))

            # 2. Persons with titles
            for m in _TITLE_NAME_REGEX.finditer(sent):
                full_match = m.group(0)
                name, etype = detect_entity_type_and_canonical_name(full_match)
                results.append((name, etype, sent))

            # 3. Organizations and Multi-word proper nouns
            for m in _CAPITALIZED_PHRASE_REGEX.finditer(sent):
                phrase = m.group(1).strip()
                if phrase.lower() in _STOP_PHRASES or len(phrase) < 3:
                    continue
                name, etype = detect_entity_type_and_canonical_name(phrase)
                if len(name) > 3:
                    results.append((name, etype, sent))

        # Deduplicate candidates within the single chunk
        unique_results = {}
        for name, etype, sent in results:
            key = (name.lower(), etype)
            if key not in unique_results:
                unique_results[key] = (name, etype, sent)

        return list(unique_results.values())

    async def extract_and_upsert_chunk_entities(
        self,
        workspace_id: str,
        chunk: Chunk,
    ) -> List[Entity]:
        """
        Extract entities from a single chunk, resolve against workspace entities,
        and update provenance in MongoDB.
        """
        candidates = self.extract_from_text(chunk.content.text)
        if not candidates:
            return []

        # Load existing workspace entities for fuzzy matching
        cursor = self.db["entities"].find(
            {"workspace_id": workspace_id},
            {"entity_id": 1, "identity": 1, "provenance": 1, "stats": 1},
        )
        existing_entities = await cursor.to_list(length=1000)

        resolved_entities: List[Entity] = []

        for name, etype, excerpt in candidates:
            matched_entity = None

            # Fuzzy match against existing entities
            for ent_doc in existing_entities:
                ident = ent_doc.get("identity", {})
                canonical = ident.get("canonical_name", "")
                aliases = ident.get("aliases", [])

                # Compare with canonical name
                sim = fuzz.token_set_ratio(name.lower(), canonical.lower())
                if sim >= self.fuzzy_threshold and ident.get("entity_type") == etype.value:
                    matched_entity = ent_doc
                    break

                # Compare with aliases
                for alias in aliases:
                    alias_sim = fuzz.token_set_ratio(name.lower(), alias.lower())
                    if alias_sim >= self.fuzzy_threshold and ident.get("entity_type") == etype.value:
                        matched_entity = ent_doc
                        break

                if matched_entity:
                    break

            provenance_entry = {
                "document_id": chunk.document_id,
                "chunk_id": chunk.chunk_id,
                "excerpt": excerpt,
                "confidence": 0.9,
            }

            if matched_entity:
                # Update existing entity
                update_fields: Dict[str, Any] = {
                    "$inc": {"stats.mention_count": 1},
                    "$set": {"updated_at": utcnow()},
                }
                # Add to aliases if new string
                canonical = matched_entity["identity"]["canonical_name"]
                if name.lower() != canonical.lower():
                    update_fields["$addToSet"] = {"identity.aliases": name}

                # Push provenance
                update_fields["$push"] = {"provenance": provenance_entry}

                await self.db["entities"].update_one(
                    {"entity_id": matched_entity["entity_id"]},
                    update_fields,
                )
                updated_doc = await self.db["entities"].find_one({"entity_id": matched_entity["entity_id"]})
                if updated_doc:
                    resolved_entities.append(Entity.model_validate(updated_doc))
            else:
                # Create brand new entity
                new_entity = Entity.create(
                    workspace_id=workspace_id,
                    canonical_name=name,
                    entity_type=etype,
                )
                new_entity.provenance.append(EntityProvenance(**provenance_entry))
                new_entity.stats.mention_count = 1
                new_entity.stats.document_count = 1

                await self.db["entities"].insert_one(new_entity.model_dump())
                existing_entities.append(new_entity.model_dump())
                resolved_entities.append(new_entity)

        return resolved_entities
