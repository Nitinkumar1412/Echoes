# -*- coding: utf-8 -*-
"""Integration and unit tests for Hybrid Retrieval (BM25, RRF, Hybrid Search API)."""
import io
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.main import app
from backend.app.services.database import connect_async, disconnect_async
from backend.app.services.retrieval.bm25 import BM25Service
from backend.app.services.retrieval.reranker import reciprocal_rank_fusion


def test_reciprocal_rank_fusion_logic():
    """Verify RRF merges multi-source results and boosts items present in both streams."""
    semantic = [
        {"chunk_id": "c1", "rank": 1, "text": "Semantic top"},
        {"chunk_id": "c2", "rank": 2, "text": "Semantic second"},
    ]
    bm25 = [
        {"chunk_id": "c3", "rank": 1, "text": "BM25 top"},
        {"chunk_id": "c1", "rank": 2, "text": "Semantic top also in BM25"},
    ]

    fused = reciprocal_rank_fusion(semantic, bm25, rrf_k=60)
    assert len(fused) == 3

    # c1 is rank 1 in semantic and rank 2 in BM25 -> MUST receive highest fused score
    assert fused[0]["chunk_id"] == "c1"
    assert fused[0]["retrieval_method"] == "hybrid"
    assert fused[0]["score"] > fused[1]["score"]


@pytest.mark.anyio
async def test_bm25_service_direct():
    """Verify BM25 lexical keyword search over MongoDB chunk collection."""
    db = await connect_async(settings.MONGODB_URI, settings.MONGODB_DATABASE)
    workspace_id = f"ws_bm25_{uuid.uuid4().hex[:6]}"

    # Insert test chunks into MongoDB
    test_chunks = [
        {
            "chunk_id": "bm25_chk_1",
            "document_id": "doc_bm25_1",
            "workspace_id": workspace_id,
            "content": {"text": "Project Apollo budget was approved for five million dollars."},
            "location": {"chunk_index": 0, "page_number": 1},
        },
        {
            "chunk_id": "bm25_chk_2",
            "document_id": "doc_bm25_2",
            "workspace_id": workspace_id,
            "content": {"text": "Apollo spacecraft telemetry data and flight coordinates."},
            "location": {"chunk_index": 0, "page_number": 2},
        },
        {
            "chunk_id": "bm25_chk_3",
            "document_id": "doc_bm25_3",
            "workspace_id": workspace_id,
            "content": {"text": "Unrelated garden flowers and vegetable planting notes."},
            "location": {"chunk_index": 0, "page_number": 1},
        },
    ]

    await db["chunks"].insert_many(test_chunks)

    bm25_svc = BM25Service(db)
    results = await bm25_svc.search_chunks(workspace_id, "spacecraft telemetry", top_k=5)

    assert len(results) >= 1
    assert results[0]["chunk_id"] == "bm25_chk_2"

    # Cleanup
    await db["chunks"].delete_many({"workspace_id": workspace_id})
    await disconnect_async()


def test_hybrid_search_api_endpoint():
    """Verify end-to-end POST /search API after uploading a document."""
    workspace_id = f"ws_search_{uuid.uuid4().hex[:8]}"
    doc_content = (
        b"# Healthcare AI Architecture\n\n"
        b"The clinical trial project was authorized by Dr. Nitin Sharma on October 14th.\n\n"
        b"Budget allocation for clinical machine learning algorithms is 500,000 USD."
    )
    filename = "clinical_trial.md"

    with TestClient(app) as client:
        # 1. Upload document (triggers ingestion + chunking + ChromaDB vectorization)
        upload_files = {"file": (filename, io.BytesIO(doc_content), "text/markdown")}
        upload_resp = client.post(
            f"/api/v1/workspaces/{workspace_id}/documents/upload",
            files=upload_files,
            data={"uploaded_by": "lead_researcher"},
        )
        assert upload_resp.status_code == 201

        # 2. Execute hybrid search
        search_payload = {
            "query": "clinical trial authorization Dr. Nitin Sharma",
            "top_k": 5,
        }
        search_resp = client.post(
            f"/api/v1/workspaces/{workspace_id}/search",
            json=search_payload,
        )
        assert search_resp.status_code == 200
        data = search_resp.json()

        assert data["workspace_id"] == workspace_id
        assert data["query"] == "clinical trial authorization Dr. Nitin Sharma"
        assert data["total_results"] >= 1

        top_chunk = data["results"][0]
        assert "Nitin Sharma" in top_chunk["text"]
        assert top_chunk["document_name"] == filename
        assert top_chunk["score"] > 0
        assert top_chunk["rank"] == 1
        assert "timing_ms" in data
        assert "total_ms" in data["timing_ms"]

    # Cleanup test data
    try:
        from backend.app.services.database import connect_sync, disconnect_sync
        from backend.app.services.vector_store import VectorStoreService

        vs = VectorStoreService()
        vs.collection.delete(where={"workspace_id": workspace_id})

        db = connect_sync(settings.MONGODB_URI, settings.MONGODB_DATABASE)
        db["documents"].delete_many({"workspace_id": workspace_id})
        db["chunks"].delete_many({"workspace_id": workspace_id})
        disconnect_sync()
    except Exception:
        pass
