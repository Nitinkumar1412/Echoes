# -*- coding: utf-8 -*-
"""Integration and unit tests for Generation, Citations, and RAG Query API (Milestone 6)."""
import io
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.main import app
from backend.app.services.generation.client import GeminiClient
from backend.app.services.generation.prompt import build_rag_prompt


def test_prompt_construction():
    """Verify evidence chunks and timeline items are formatted into prompt."""
    chunks = [
        {"chunk_id": "c_1", "document_name": "memo.txt", "page_number": 1, "text": "Project Apollo budget: $5M."},
        {"chunk_id": "c_2", "document_name": "memo.txt", "page_number": 2, "text": "Launch date: Nov 2026."},
    ]
    events = [{"original_expression": "Nov 2026", "title": "Apollo Launch"}]

    prompt = build_rag_prompt("When is Apollo launching?", chunks, events)

    assert "[CHUNK_1]" in prompt
    assert "[CHUNK_2]" in prompt
    assert "memo.txt" in prompt
    assert "Apollo Launch" in prompt
    assert "When is Apollo launching?" in prompt


@pytest.mark.anyio
async def test_insufficient_evidence_response():
    """Verify system explicitly returns insufficient_evidence when chunks are empty."""
    client = GeminiClient()
    answer = await client.generate_answer(
        prompt="Tell me about Mars base.",
        query="Mars base details",
        chunks=[],
    )
    assert "insufficient_evidence" in answer.lower()
    assert "[CONFIDENCE: insufficient_evidence]" in answer


def test_full_rag_query_api_workflow():
    """Verify complete end-to-end RAG answer generation, citations, and history logging."""
    workspace_id = f"ws_query_api_{uuid.uuid4().hex[:8]}"
    doc_content = (
        b"# Clinical Research Memo\n\n"
        b"Lead researcher Dr. Nitin Sharma secured a 250,000 USD grant for the AI diagnostics system.\n\n"
        b"The clinical trials are scheduled to commence in November 2026."
    )
    filename = "clinical_memo.md"

    with TestClient(app) as client:
        # 1. Upload document (ingestion + chunking + vectors + graph)
        upload_resp = client.post(
            f"/api/v1/workspaces/{workspace_id}/documents/upload",
            files={"file": (filename, io.BytesIO(doc_content), "text/markdown")},
        )
        assert upload_resp.status_code == 201

        # 2. Ask question
        query_payload = {
            "query": "How much grant was secured by Dr. Nitin Sharma?",
            "top_k": 5,
        }
        query_resp = client.post(
            f"/api/v1/workspaces/{workspace_id}/query",
            json=query_payload,
        )
        assert query_resp.status_code == 200
        data = query_resp.json()

        assert data["workspace_id"] == workspace_id
        assert data["query"] == "How much grant was secured by Dr. Nitin Sharma?"
        assert data["answer"] is not None
        assert len(data["answer"]) > 10
        assert data["confidence"] in ("high", "medium", "low", "insufficient_evidence")

        # Verify Citations (Provable grounding)
        assert len(data["citations"]) >= 1
        top_citation = data["citations"][0]
        assert top_citation["document_name"] == filename
        assert "chunk_id" in top_citation
        assert "excerpt" in top_citation

        # Verify Performance timing
        assert "total_ms" in data["performance"]
        assert "retrieval_ms" in data["performance"]
        assert "generation_ms" in data["performance"]

        # 3. Verify Query History
        history_resp = client.get(f"/api/v1/workspaces/{workspace_id}/query/history")
        assert history_resp.status_code == 200
        hist_data = history_resp.json()
        assert hist_data["total_queries"] >= 1
        assert hist_data["queries"][0]["query"] == "How much grant was secured by Dr. Nitin Sharma?"

    # Cleanup test data
    try:
        from backend.app.services.database import connect_sync, disconnect_sync
        from backend.app.services.vector_store import VectorStoreService

        vs = VectorStoreService()
        vs.collection.delete(where={"workspace_id": workspace_id})

        db = connect_sync(settings.MONGODB_URI, settings.MONGODB_DATABASE)
        db["documents"].delete_many({"workspace_id": workspace_id})
        db["chunks"].delete_many({"workspace_id": workspace_id})
        db["entities"].delete_many({"workspace_id": workspace_id})
        db["events"].delete_many({"workspace_id": workspace_id})
        db["relationships"].delete_many({"workspace_id": workspace_id})
        db["queries"].delete_many({"workspace_id": workspace_id})
        disconnect_sync()
    except Exception:
        pass
