# -*- coding: utf-8 -*-
"""
Embedding service for Echoes Search using sentence-transformers.
Generates 384-dimensional dense embeddings for chunks and search queries.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from typing import Any, List, Optional

from backend.app.core.config import settings

logger = logging.getLogger("echoes.embedding")

_model_instance: Optional[Any] = None


def get_embedding_model() -> Any:
    """
    Get or initialize the shared SentenceTransformer singleton.
    Loaded lazily on first call to optimize startup time and reduce memory footprint.
    """
    global _model_instance
    if _model_instance is None:
        logger.info("[EMBEDDING] Lazy-loading model '%s' on first use...", settings.EMBEDDING_MODEL)
        from sentence_transformers import SentenceTransformer
        _model_instance = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("[EMBEDDING] Model '%s' loaded successfully.", settings.EMBEDDING_MODEL)
    return _model_instance


class EmbeddingService:
    """Service for generating dense embeddings in batches."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        # Do NOT eagerly instantiate model in __init__ to keep memory low

    @property
    def model(self) -> Any:
        return get_embedding_model()

    def embed_texts(self, texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
        """
        Embed a list of text strings into normalized vector embeddings.

        Args:
            texts: List of strings to encode
            batch_size: Batch size for encoding (defaults to settings.EMBEDDING_BATCH_SIZE)

        Returns:
            List of float vectors, each of length 384 (for all-MiniLM-L6-v2)
        """
        if not texts:
            return []

        bs = batch_size or settings.EMBEDDING_BATCH_SIZE
        embeddings = self.model.encode(
            texts,
            batch_size=bs,
            show_progress_bar=False,
            normalize_embeddings=True,  # Normalized embeddings enable cosine similarity via dot product
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """Generate a single embedding vector for a search query."""
        if not query.strip():
            return [0.0] * 384
        return self.embed_texts([query.strip()])[0]
