# -*- coding: utf-8 -*-
"""
Hybrid Retrieval Engine for Echoes Search.
Coordinates Vector Semantic Search, BM25 Lexical Search, and RRF Reranking with timing breakdown.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.core.config import settings
from backend.app.services.vector_store import VectorStoreService
from .bm25 import BM25Service
from .reranker import RerankerService

logger = logging.getLogger("echoes.retrieval.engine")


class HybridRetrievalEngine:
    """End-to-end hybrid retrieval coordinator."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        vector_store: Optional[VectorStoreService] = None,
        bm25_service: Optional[BM25Service] = None,
        reranker: Optional[RerankerService] = None,
    ):
        self.db = db
        self.vector_store = vector_store or VectorStoreService()
        self.bm25_service = bm25_service or BM25Service(db)
        self.reranker = reranker or RerankerService()

    async def search(
        self,
        workspace_id: str,
        query_text: str,
        top_k: Optional[int] = None,
        document_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute full hybrid retrieval pipeline.

        Returns:
            Dict containing:
                "results": List of ranked chunks with scores and document names
                "timing_ms": {"semantic_ms", "bm25_ms", "reranking_ms", "total_ms"}
                "counts": {"semantic_count", "bm25_count", "final_count"}
        """
        start_total = time.perf_counter()
        target_k = top_k or settings.TOP_K_RERANKED

        # 1. Semantic Search (ChromaDB)
        t0 = time.perf_counter()
        semantic_candidates = self.vector_store.search_similar_chunks(
            workspace_id=workspace_id,
            query_text=query_text,
            top_k=settings.TOP_K_SEMANTIC,
        )
        # Apply document_ids filter if specified
        if document_ids:
            doc_set = set(document_ids)
            semantic_candidates = [
                c for c in semantic_candidates
                if c.get("metadata", {}).get("document_id") in doc_set
            ]
        semantic_ms = int((time.perf_counter() - t0) * 1000)

        # 2. Lexical Search (BM25)
        t1 = time.perf_counter()
        bm25_candidates = await self.bm25_service.search_chunks(
            workspace_id=workspace_id,
            query_text=query_text,
            top_k=settings.TOP_K_BM25,
            document_ids=document_ids,
        )
        bm25_ms = int((time.perf_counter() - t1) * 1000)

        # 3. Rerank & Merge (RRF)
        t2 = time.perf_counter()
        ranked_chunks = self.reranker.rerank(
            query=query_text,
            semantic_candidates=semantic_candidates,
            bm25_candidates=bm25_candidates,
            top_k=target_k,
        )
        reranking_ms = int((time.perf_counter() - t2) * 1000)

        # 4. Enrich with document names from MongoDB
        doc_ids_to_fetch = list({c["document_id"] for c in ranked_chunks if c.get("document_id")})
        doc_name_map: Dict[str, str] = {}
        if doc_ids_to_fetch:
            cursor = self.db["documents"].find(
                {"document_id": {"$in": doc_ids_to_fetch}},
                {"document_id": 1, "file.original_name": 1},
            )
            async for d in cursor:
                doc_name_map[d["document_id"]] = d.get("file", {}).get("original_name", "Unknown Document")

        for c in ranked_chunks:
            c["document_name"] = doc_name_map.get(c["document_id"], "Unknown Document")

        total_ms = int((time.perf_counter() - start_total) * 1000)

        logger.info(
            "[HYBRID RETRIEVAL] Query: '%s' | Sem: %d (%dms) | BM25: %d (%dms) | Final: %d (%dms)",
            query_text[:30],
            len(semantic_candidates),
            semantic_ms,
            len(bm25_candidates),
            bm25_ms,
            len(ranked_chunks),
            total_ms,
        )

        return {
            "results": ranked_chunks,
            "timing_ms": {
                "semantic_ms": semantic_ms,
                "bm25_ms": bm25_ms,
                "reranking_ms": reranking_ms,
                "total_ms": total_ms,
            },
            "counts": {
                "semantic_count": len(semantic_candidates),
                "bm25_count": len(bm25_candidates),
                "final_count": len(ranked_chunks),
            },
        }
