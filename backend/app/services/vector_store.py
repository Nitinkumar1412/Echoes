# -*- coding: utf-8 -*-
"""
ChromaDB vector store service for Echoes Search.
Manages persistent vector indexing, semantic search, and document vector lifecycle.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

from backend.app.core.config import settings
from backend.app.models.chunk import Chunk
from backend.app.services.embedding import EmbeddingService

logger = logging.getLogger("echoes.vector_store")

_chroma_client: Optional[ClientAPI] = None
_DEFAULT_COLLECTION = "echoes_chunks"


def get_chroma_client() -> ClientAPI:
    """Get or initialize the persistent ChromaDB client."""
    global _chroma_client
    if _chroma_client is None:
        chroma_dir = settings.chroma_path_path
        chroma_dir.mkdir(parents=True, exist_ok=True)
        logger.info("[CHROMA] Initializing ChromaDB at: %s", chroma_dir)
        _chroma_client = chromadb.PersistentClient(path=str(chroma_dir))
    return _chroma_client


class VectorStoreService:
    """Service wrapping ChromaDB operations with cosine similarity and metadata filtering."""

    def __init__(
        self,
        collection_name: str = _DEFAULT_COLLECTION,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        self.client = get_chroma_client()
        self.collection_name = collection_name
        self.embedding_service = embedding_service or EmbeddingService()
        self.collection: Collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},  # Cosine distance for normalized embeddings
        )

    def upsert_chunks(self, chunks: List[Chunk]) -> int:
        """
        Embed and upsert a list of chunks into ChromaDB.
        Uses deterministic chunk IDs: chroma_id == chunk_id.
        """
        if not chunks:
            return 0

        ids: List[str] = []
        texts: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for c in chunks:
            ids.append(c.chunk_id)
            texts.append(c.content.text)
            metadatas.append(
                {
                    "workspace_id": c.workspace_id,
                    "document_id": c.document_id,
                    "chunk_id": c.chunk_id,
                    "chunk_index": c.location.chunk_index,
                    "page_number": c.location.page_number or 1,
                    "token_count": c.content.token_count,
                }
            )

        # Generate embeddings
        embeddings = self.embedding_service.embed_texts(texts)

        # Upsert in ChromaDB
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        logger.info(
            "[CHROMA] Upserted %d chunk vectors into '%s'",
            len(chunks),
            self.collection_name,
        )
        return len(chunks)

    def search_similar_chunks(
        self,
        workspace_id: str,
        query_text: str,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search scoped to a specific workspace.

        Args:
            workspace_id: Target workspace for isolation
            query_text: Search query
            top_k: Maximum candidate chunks (defaults to settings.TOP_K_SEMANTIC = 20)

        Returns:
            List of result dicts: [{"chunk_id", "score", "rank", "text", "metadata"}]
        """
        k = top_k or settings.TOP_K_SEMANTIC
        query_vec = self.embedding_service.embed_query(query_text)

        # Query ChromaDB with workspace filtering
        results = self.collection.query(
            query_embeddings=[query_vec],
            n_results=k,
            where={"workspace_id": workspace_id},
            include=["documents", "metadatas", "distances"],
        )

        candidates: List[Dict[str, Any]] = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return candidates

        ids = results["ids"][0]
        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for rank, (chunk_id, doc, meta, dist) in enumerate(zip(ids, docs, metadatas, distances), start=1):
            # For cosine distance: distance is in [0, 2], similarity is 1.0 - (dist / 2) or 1.0 - dist
            score = max(0.0, min(1.0, 1.0 - dist))
            candidates.append(
                {
                    "chunk_id": chunk_id,
                    "score": round(score, 4),
                    "distance": round(dist, 4),
                    "rank": rank,
                    "text": doc,
                    "metadata": meta,
                }
            )

        return candidates

    def delete_document_vectors(self, document_id: str) -> None:
        """Remove all chunk vectors belonging to a specific document."""
        try:
            self.collection.delete(where={"document_id": document_id})
            logger.info("[CHROMA] Deleted vectors for doc '%s'", document_id)
        except Exception as exc:
            logger.warning("[CHROMA] Error deleting vectors for doc '%s': %s", document_id, exc)

    def count(self) -> int:
        """Return total vector count in the collection."""
        return self.collection.count()
