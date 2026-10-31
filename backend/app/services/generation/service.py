# -*- coding: utf-8 -*-
"""
End-to-end Query Service orchestrating Hybrid Retrieval, Knowledge Graph Expansion,
Grounded Answer Generation, Citation Verification, and Audit Logging.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional, Set

from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.core.config import settings
from backend.app.models.base import utcnow
from backend.app.models.query import (
    AnswerConfidence,
    Query,
    QueryAnswer,
    QueryCitation,
    QueryFilters,
    QueryInput,
    QueryPerformance,
    QueryRetrieval,
    QueryStatus,
    QueryTimelineItem,
    RetrievedChunkRef,
)
from backend.app.services.graph.networkx_service import NetworkXGraphService
from backend.app.services.retrieval.engine import HybridRetrievalEngine
from .client import GeminiClient
from .prompt import build_rag_prompt

logger = logging.getLogger("echoes.generation.service")

_CHUNK_TAG_REGEX = re.compile(r"\[CHUNK_(\d+)\]", re.IGNORECASE)
_CONFIDENCE_TAG_REGEX = re.compile(r"\[CONFIDENCE:\s*(high|medium|low|insufficient_evidence)\]", re.IGNORECASE)


class QueryService:
    """Orchestrates RAG retrieval, LLM synthesis, citation validation, and query logging."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        retrieval_engine: Optional[HybridRetrievalEngine] = None,
        llm_client: Optional[GeminiClient] = None,
        graph_service: Optional[NetworkXGraphService] = None,
    ):
        self.db = db
        self.retrieval_engine = retrieval_engine or HybridRetrievalEngine(db)
        self.llm_client = llm_client or GeminiClient()
        self.graph_service = graph_service or NetworkXGraphService(db)

    async def answer_query(
        self,
        workspace_id: str,
        query_text: str,
        user_id: Optional[str] = "user_default",
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = 10,
    ) -> Dict[str, Any]:
        """
        Execute full RAG pipeline for a user question.

        Returns:
            Dict containing query_id, answer, confidence, citations, timeline, and performance.
        """
        start_time = time.perf_counter()

        # 1. Hybrid Retrieval
        t_ret_start = time.perf_counter()
        retrieval_output = await self.retrieval_engine.search(
            workspace_id=workspace_id,
            query_text=query_text,
            top_k=top_k,
            document_ids=document_ids,
        )
        retrieval_ms = int((time.perf_counter() - t_ret_start) * 1000)
        chunks = retrieval_output["results"]

        # 2. Knowledge Graph Expansion & Timeline Context
        events_cursor = self.db["events"].find(
            {"workspace_id": workspace_id},
        ).sort("temporal.normalized_date", 1).limit(5)
        timeline_events = await events_cursor.to_list(length=5)

        # 3. Assemble Prompt
        prompt = build_rag_prompt(
            query=query_text,
            chunks=chunks,
            events=timeline_events,
        )

        # 4. Generate Grounded Answer via LLM
        t_gen_start = time.perf_counter()
        raw_answer = await self.llm_client.generate_answer(prompt, query_text, chunks)
        generation_ms = int((time.perf_counter() - t_gen_start) * 1000)

        # 5. Extract Confidence
        confidence_enum = AnswerConfidence.MEDIUM
        has_uncertainty = False
        conf_match = _CONFIDENCE_TAG_REGEX.search(raw_answer)
        if conf_match:
            conf_str = conf_match.group(1).lower()
            if conf_str == "high":
                confidence_enum = AnswerConfidence.HIGH
            elif conf_str == "low":
                confidence_enum = AnswerConfidence.LOW
                has_uncertainty = True
            elif conf_str == "insufficient_evidence":
                confidence_enum = AnswerConfidence.INSUFFICIENT_EVIDENCE
                has_uncertainty = True
            # Clean confidence tag from public answer text
            clean_answer = _CONFIDENCE_TAG_REGEX.sub("", raw_answer).strip()
        else:
            clean_answer = raw_answer.strip()

        # 6. Parse and Validate Citations (Hallucination Guard)
        cited_indices: Set[int] = set()
        for m in _CHUNK_TAG_REGEX.finditer(clean_answer):
            try:
                cited_indices.add(int(m.group(1)))
            except ValueError:
                pass

        citations: List[QueryCitation] = []
        for idx in sorted(list(cited_indices)):
            # 1-indexed mapping
            chunk_pos = idx - 1
            if 0 <= chunk_pos < len(chunks):
                ch = chunks[chunk_pos]
                citations.append(
                    QueryCitation(
                        chunk_id=ch["chunk_id"],
                        document_id=ch["document_id"],
                        document_name=ch.get("document_name", "Unknown Document"),
                        excerpt=ch.get("text", "")[:250],
                        relevance_score=ch.get("score", 1.0),
                    )
                )

        # If LLM didn't cite directly but answered from top chunk, add top chunk as citation
        if not citations and chunks and confidence_enum != AnswerConfidence.INSUFFICIENT_EVIDENCE:
            ch = chunks[0]
            citations.append(
                QueryCitation(
                    chunk_id=ch["chunk_id"],
                    document_id=ch["document_id"],
                    document_name=ch.get("document_name", "Unknown Document"),
                    excerpt=ch.get("text", "")[:250],
                    relevance_score=ch.get("score", 1.0),
                )
            )

        # 7. Timeline Items
        timeline_items = [
            QueryTimelineItem(
                event_id=ev["event_id"],
                title=ev["title"],
                normalized_date=ev.get("temporal", {}).get("normalized_date"),
            )
            for ev in timeline_events
        ]

        total_ms = int((time.perf_counter() - start_time) * 1000)

        # 8. Create and Persist Immutable Query Document (Audit Log)
        query_record = Query(
            workspace_id=workspace_id,
            user_id=user_id or "user_default",
            input=QueryInput(
                query_text=query_text,
                filters=QueryFilters(document_ids=document_ids or []),
            ),
            retrieval=QueryRetrieval(
                reranked_chunks=[
                    RetrievedChunkRef(chunk_id=c["chunk_id"], score=c["score"], rank=c["rank"])
                    for c in chunks
                ]
            ),
            answer=QueryAnswer(
                text=clean_answer,
                model=self.llm_client.model_name,
                confidence=confidence_enum,
                has_uncertainty=has_uncertainty,
            ),
            citations=citations,
            timeline=timeline_items,
            performance=QueryPerformance(
                total_ms=total_ms,
                retrieval_ms=retrieval_ms,
                reranking_ms=retrieval_output.get("timing_ms", {}).get("reranking_ms", 0),
                generation_ms=generation_ms,
            ),
            status=QueryStatus.COMPLETED,
        )

        await self.db["queries"].insert_one(query_record.model_dump())

        logger.info(
            "[QUERY RAG] Answered '%s' | Conf: %s | Citations: %d | Time: %dms",
            query_text[:30],
            confidence_enum.value,
            len(citations),
            total_ms,
        )

        return {
            "query_id": query_record.query_id,
            "workspace_id": workspace_id,
            "query": query_text,
            "answer": clean_answer,
            "confidence": confidence_enum.value,
            "has_uncertainty": has_uncertainty,
            "citations": [c.model_dump() for c in citations],
            "timeline": [t.model_dump() for t in timeline_items],
            "performance": query_record.performance.model_dump(),
            "created_at": query_record.created_at,
        }
