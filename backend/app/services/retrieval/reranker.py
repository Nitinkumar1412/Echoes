# -*- coding: utf-8 -*-
"""
Reranking service combining Reciprocal Rank Fusion (RRF) and optional Cross-Encoder.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings

logger = logging.getLogger("echoes.retrieval.reranker")

_cross_encoder_instance = None
_DEFAULT_RRF_K = 60


def get_cross_encoder():
    """Lazily load cross-encoder model if needed."""
    global _cross_encoder_instance
    if _cross_encoder_instance is None:
        try:
            from sentence_transformers import CrossEncoder

            # Lightweight, standard MS MARCO reranker
            _cross_encoder_instance = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            logger.info("[RERANKER] Cross-encoder loaded successfully.")
        except Exception as exc:
            logger.warning("[RERANKER] CrossEncoder could not be loaded: %s", exc)
            _cross_encoder_instance = False
    return _cross_encoder_instance if _cross_encoder_instance is not False else None


def reciprocal_rank_fusion(
    semantic_candidates: List[Dict[str, Any]],
    bm25_candidates: List[Dict[str, Any]],
    rrf_k: int = _DEFAULT_RRF_K,
    weight_semantic: float = 1.0,
    weight_bm25: float = 1.0,
) -> List[Dict[str, Any]]:
    """
    Merge and score candidates using Reciprocal Rank Fusion (RRF).

    Formula:
        RRF_score(d) = (w_sem / (k + rank_sem)) + (w_bm25 / (k + rank_bm25))
    """
    fused_scores: Dict[str, float] = {}
    chunk_meta_map: Dict[str, Dict[str, Any]] = {}
    sources_map: Dict[str, List[str]] = {}

    # 1. Process Semantic candidates
    for item in semantic_candidates:
        cid = item["chunk_id"]
        rank = item["rank"]
        rrf_contrib = weight_semantic / (rrf_k + rank)
        fused_scores[cid] = fused_scores.get(cid, 0.0) + rrf_contrib
        chunk_meta_map[cid] = item
        sources_map.setdefault(cid, []).append("semantic")

    # 2. Process BM25 candidates
    for item in bm25_candidates:
        cid = item["chunk_id"]
        rank = item["rank"]
        rrf_contrib = weight_bm25 / (rrf_k + rank)
        fused_scores[cid] = fused_scores.get(cid, 0.0) + rrf_contrib
        if cid not in chunk_meta_map:
            chunk_meta_map[cid] = item
        sources_map.setdefault(cid, []).append("bm25")

    # 3. Sort by aggregated RRF score descending
    sorted_items = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

    fused_results: List[Dict[str, Any]] = []
    for rank, (cid, score) in enumerate(sorted_items, start=1):
        item = chunk_meta_map[cid]
        sources = sources_map[cid]
        method = "hybrid" if len(sources) > 1 else sources[0]

        fused_results.append(
            {
                "chunk_id": cid,
                "document_id": item.get("document_id") or item.get("metadata", {}).get("document_id", ""),
                "score": round(score, 6),
                "rank": rank,
                "text": item.get("text", ""),
                "page_number": item.get("page_number") or item.get("metadata", {}).get("page_number", 1),
                "retrieval_method": method,
            }
        )

    return fused_results


class RerankerService:
    """Combines RRF fusion with cross-encoder precision reranking."""

    def __init__(self, use_neural_reranker: bool = False):
        self.use_neural = use_neural_reranker

    def rerank(
        self,
        query: str,
        semantic_candidates: List[Dict[str, Any]],
        bm25_candidates: List[Dict[str, Any]],
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Merge candidates using RRF and optionally refine via neural cross-encoder.
        """
        k = top_k or settings.TOP_K_RERANKED
        # 1. RRF Fusion
        fused = reciprocal_rank_fusion(semantic_candidates, bm25_candidates)

        if not fused:
            return []

        # 2. Optional Neural Cross-Encoder
        if self.use_neural:
            encoder = get_cross_encoder()
            if encoder:
                # Score top 20 candidates with cross encoder
                candidates_to_score = fused[:20]
                pairs = [[query, c["text"]] for c in candidates_to_score]
                try:
                    ce_scores = encoder.predict(pairs)
                    for idx, c in enumerate(candidates_to_score):
                        c["ce_score"] = float(ce_scores[idx])
                    candidates_to_score.sort(key=lambda x: x["ce_score"], reverse=True)
                    # Update ranks
                    for rank, c in enumerate(candidates_to_score, start=1):
                        c["rank"] = rank
                    return candidates_to_score[:k]
                except Exception as exc:
                    logger.warning("[RERANKER] Neural scoring failed, falling back to RRF: %s", exc)

        return fused[:k]
