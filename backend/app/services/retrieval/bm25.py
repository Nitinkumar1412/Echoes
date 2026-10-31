# -*- coding: utf-8 -*-
"""
BM25 Lexical search service using rank-bm25.
Provides exact keyword matching for codes, numbers, specific names, and terms.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from rank_bm25 import BM25Okapi

from backend.app.core.config import settings

logger = logging.getLogger("echoes.retrieval.bm25")

_TOKEN_SPLIT_REGEX = re.compile(r"\w+")


def tokenize_text(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    return _TOKEN_SPLIT_REGEX.findall(text.lower())


class BM25Service:
    """In-memory BM25 index built over chunks in a workspace."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def search_chunks(
        self,
        workspace_id: str,
        query_text: str,
        top_k: Optional[int] = None,
        document_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute BM25 lexical search over chunks in a workspace.

        Args:
            workspace_id: Target workspace
            query_text: User search query
            top_k: Number of candidates to return (defaults to settings.TOP_K_BM25)
            document_ids: Optional document filters

        Returns:
            List of candidates: [{"chunk_id", "score", "rank", "text", "document_id"}]
        """
        k = top_k or settings.TOP_K_BM25
        query_tokens = tokenize_text(query_text)
        if not query_tokens:
            return []

        # Build mongo query for chunks
        chunk_filter: Dict[str, Any] = {"workspace_id": workspace_id}
        if document_ids:
            chunk_filter["document_id"] = {"$in": document_ids}

        cursor = self.db["chunks"].find(
            chunk_filter,
            {"chunk_id": 1, "document_id": 1, "content.text": 1, "location.page_number": 1},
        )
        chunks = await cursor.to_list(length=2000)

        if not chunks:
            return []

        # Tokenize corpus for BM25
        corpus_chunks = []
        tokenized_corpus = []

        for ch in chunks:
            text = ch.get("content", {}).get("text", "")
            tokens = tokenize_text(text)
            if tokens:
                corpus_chunks.append(ch)
                tokenized_corpus.append(tokens)

        if not tokenized_corpus:
            return []

        # Run BM25
        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(query_tokens)

        # Pair scores with chunk metadata
        scored_pairs = []
        for idx, score in enumerate(scores):
            if score > 0.0:  # Only chunks with at least 1 matching term
                scored_pairs.append((score, corpus_chunks[idx]))

        # Sort descending by BM25 score
        scored_pairs.sort(key=lambda x: x[0], reverse=True)
        top_pairs = scored_pairs[:k]

        candidates: List[Dict[str, Any]] = []
        for rank, (score, ch) in enumerate(top_pairs, start=1):
            candidates.append(
                {
                    "chunk_id": ch["chunk_id"],
                    "document_id": ch["document_id"],
                    "score": round(float(score), 4),
                    "rank": rank,
                    "text": ch.get("content", {}).get("text", ""),
                    "page_number": ch.get("location", {}).get("page_number", 1),
                }
            )

        return candidates
