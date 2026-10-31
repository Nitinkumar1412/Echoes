# -*- coding: utf-8 -*-
"""Integration tests for ChromaDB vector store service."""
import uuid
import pytest

from backend.app.models.chunk import Chunk
from backend.app.services.vector_store import VectorStoreService


def test_chroma_upsert_and_similarity_search():
    """Verify upserting chunks and executing workspace-isolated similarity search."""
    test_collection = f"test_col_{uuid.uuid4().hex[:8]}"
    vs = VectorStoreService(collection_name=test_collection)

    workspace_a = f"ws_a_{uuid.uuid4().hex[:6]}"
    workspace_b = f"ws_b_{uuid.uuid4().hex[:6]}"

    chunk1 = Chunk.create(
        document_id="doc_1",
        workspace_id=workspace_a,
        index=0,
        text="The healthcare project kickoff meeting was scheduled for October 15th.",
        token_count=12,
        char_start=0,
        char_end=70,
        chunk_size=512,
        overlap=64,
    )
    chunk2 = Chunk.create(
        document_id="doc_2",
        workspace_id=workspace_a,
        index=0,
        text="Budget allocation for the mobile app development is two hundred thousand dollars.",
        token_count=13,
        char_start=0,
        char_end=80,
        chunk_size=512,
        overlap=64,
    )
    chunk3 = Chunk.create(
        document_id="doc_3",
        workspace_id=workspace_b,
        index=0,
        text="Healthcare meeting details and timeline for team B.",
        token_count=8,
        char_start=0,
        char_end=50,
        chunk_size=512,
        overlap=64,
    )

    # Upsert all 3
    upserted = vs.upsert_chunks([chunk1, chunk2, chunk3])
    assert upserted == 3

    # Query for "When was the healthcare kickoff meeting?" in workspace_a
    results_a = vs.search_similar_chunks(
        workspace_id=workspace_a,
        query_text="healthcare kickoff meeting date",
        top_k=5,
    )

    assert len(results_a) == 2  # Only chunks from workspace_a!
    assert results_a[0]["chunk_id"] == chunk1.chunk_id  # chunk1 should rank first
    assert results_a[0]["score"] > 0.5

    # Verify workspace isolation: chunk3 (workspace_b) must NOT appear in workspace_a results
    returned_ids = [r["chunk_id"] for r in results_a]
    assert chunk3.chunk_id not in returned_ids

    # Test delete document vectors
    vs.delete_document_vectors("doc_1")
    post_delete_results = vs.search_similar_chunks(
        workspace_id=workspace_a,
        query_text="healthcare kickoff meeting date",
        top_k=5,
    )
    assert chunk1.chunk_id not in [r["chunk_id"] for r in post_delete_results]

    # Cleanup collection
    try:
        vs.client.delete_collection(test_collection)
    except Exception:
        pass
