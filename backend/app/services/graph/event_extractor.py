# -*- coding: utf-8 -*-
"""
Event and temporal extraction service using dateparser.
Normalizes date expressions into sortable timestamps with precision tags for timeline queries.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import dateparser
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.models.base import utcnow
from backend.app.models.chunk import Chunk
from backend.app.models.event import (
    DatePrecision,
    Event,
    EventProvenance,
    EventTemporal,
    EventType,
)

logger = logging.getLogger("echoes.graph.event")

# Date pattern regexes
_DATE_PATTERNS = [
    # Full Month Day, Year e.g., October 14, 2024 or 14 October 2024
    re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b", re.IGNORECASE),
    re.compile(r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4}\b", re.IGNORECASE),
    # Month Day without year e.g., October 14th
    re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?\b", re.IGNORECASE),
    # Month Year e.g., October 2024
    re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b", re.IGNORECASE),
    # ISO dates YYYY-MM-DD
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    # Quarters e.g., Q1 2024, Q2 2025
    re.compile(r"\bQ[1-4]\s+\d{4}\b", re.IGNORECASE),
]

_EVENT_KEYWORD_TYPES = {
    "kickoff": EventType.MILESTONE,
    "launch": EventType.MILESTONE,
    "deadline": EventType.MILESTONE,
    "approved": EventType.DECISION,
    "authorized": EventType.DECISION,
    "decided": EventType.DECISION,
    "meeting": EventType.MEETING,
    "call": EventType.MEETING,
    "discussion": EventType.DISCUSSION,
    "contract": EventType.DECISION,
    "signed": EventType.DECISION,
    "task": EventType.TASK,
    "completed": EventType.MILESTONE,
}


def classify_event_type(text: str) -> EventType:
    """Classify the event type based on action verbs in the sentence."""
    lower = text.lower()
    for kw, etype in _EVENT_KEYWORD_TYPES.items():
        if kw in lower:
            return etype
    return EventType.OTHER


def infer_date_precision(date_str: str) -> DatePrecision:
    """Infer precision from the raw date string."""
    lower = date_str.lower()
    if re.search(r"q[1-4]", lower):
        return DatePrecision.QUARTER
    if re.search(r"^\d{4}$", date_str.strip()):
        return DatePrecision.YEAR
    if re.search(r"^[a-zA-Z]+\s+\d{4}$", date_str.strip()):
        return DatePrecision.MONTH
    return DatePrecision.DAY


class EventExtractorService:
    """Extracts date-anchored events from text chunks."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    def extract_events_from_text(self, text: str) -> List[Tuple[str, str, EventType, DatePrecision, Optional[datetime]]]:
        """
        Extract events from text.
        Returns list of (title, raw_date_expr, event_type, precision, normalized_date).
        """
        events = []
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

        for sent in sentences:
            found_date_str = None
            for pattern in _DATE_PATTERNS:
                m = pattern.search(sent)
                if m:
                    found_date_str = m.group(0).strip()
                    break

            if found_date_str:
                # Parse date
                parsed_dt = dateparser.parse(
                    found_date_str,
                    settings={"PREFER_DATES_FROM": "past", "RELATIVE_BASE": datetime(2026, 1, 1)},
                )
                if parsed_dt and parsed_dt.tzinfo is None:
                    parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)

                etype = classify_event_type(sent)
                precision = infer_date_precision(found_date_str)
                title = sent[:120].strip()

                events.append((title, found_date_str, etype, precision, parsed_dt))

        return events

    async def extract_and_upsert_chunk_events(
        self,
        workspace_id: str,
        chunk: Chunk,
        participant_entity_ids: Optional[List[str]] = None,
    ) -> List[Event]:
        """Extract and persist events from a chunk."""
        raw_events = self.extract_events_from_text(chunk.content.text)
        created_events: List[Event] = []

        for title, raw_expr, etype, precision, norm_date in raw_events:
            event = Event.create(
                workspace_id=workspace_id,
                title=title,
                original_expression=raw_expr,
                event_type=etype,
                normalized_date=norm_date,
                date_precision=precision,
            )
            event.provenance.append(
                EventProvenance(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    excerpt=title,
                    confidence=0.85,
                )
            )
            if participant_entity_ids:
                event.participants = participant_entity_ids
            event.related_documents = [chunk.document_id]

            await self.db["events"].insert_one(event.model_dump())
            created_events.append(event)

        return created_events
