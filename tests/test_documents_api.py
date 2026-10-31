# -*- coding: utf-8 -*-
"""Integration tests for Document Ingestion API endpoints."""
import io
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.main import app
from backend.app.services.database import get_sync_db


def test_document_upload_dedup_and_chunk_inspection():
    """Verify document upload, SHA-256 deduplication, listing, and chunk inspection."""
    workspace_id = f"ws_test_{uuid.uuid4().hex[:8]}"
    doc_content = (
        b"# Milestone 2 Architecture\n\n"
        b"Echoes Search ingest pipeline processes files into boundary-aware chunks.\n\n"
        b"Each chunk retains provenance back to the source document with page numbers."
    )
    filename = "milestone2_spec.md"

    with TestClient(app) as client:
        # 1. First upload -> should be created and chunked
        upload_files = {"file": (filename, io.BytesIO(doc_content), "text/markdown")}
        resp1 = client.post(
            f"/api/v1/workspaces/{workspace_id}/documents/upload",
            files=upload_files,
            data={"uploaded_by": "test_user"},
        )
        assert resp1.status_code == 201
        data1 = resp1.json()
        assert data1["is_duplicate"] is False
        assert data1["chunks_created"] >= 1
        doc_id = data1["document"]["document_id"]
        assert doc_id is not None
        assert data1["document"]["workspace_id"] == workspace_id
        assert data1["document"]["file"]["original_name"] == filename

        # 2. Second upload with SAME bytes -> should detect duplicate
        upload_files_duplicate = {"file": (filename, io.BytesIO(doc_content), "text/markdown")}
        resp2 = client.post(
            f"/api/v1/workspaces/{workspace_id}/documents/upload",
            files=upload_files_duplicate,
            data={"uploaded_by": "test_user"},
        )
        assert resp2.status_code == 201
        data2 = resp2.json()
        assert data2["is_duplicate"] is True
        assert data2["document"]["document_id"] == doc_id  # same document returned!

        # 3. List documents in workspace
        list_resp = client.get(f"/api/v1/workspaces/{workspace_id}/documents")
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert list_data["total_count"] == 1
        assert list_data["documents"][0]["document_id"] == doc_id

        # 4. Get single document details
        detail_resp = client.get(f"/api/v1/workspaces/{workspace_id}/documents/{doc_id}")
        assert detail_resp.status_code == 200
        detail_data = detail_resp.json()
        assert detail_data["document_id"] == doc_id
        assert detail_data["processing"]["status"] == "completed"

        # 5. Inspect generated chunks
        chunks_resp = client.get(f"/api/v1/workspaces/{workspace_id}/documents/{doc_id}/chunks")
        assert chunks_resp.status_code == 200
        chunks = chunks_resp.json()
        assert len(chunks) >= 1
        assert chunks[0]["chunk_id"] == f"{doc_id}__chunk_0000"
        assert "Milestone 2" in chunks[0]["text"]
        assert chunks[0]["token_count"] > 0

    # Cleanup test data from MongoDB
    try:
        from backend.app.services.database import connect_sync, disconnect_sync
        db = connect_sync(settings.MONGODB_URI, settings.MONGODB_DATABASE)
        db["documents"].delete_many({"workspace_id": workspace_id})
        db["chunks"].delete_many({"workspace_id": workspace_id})
        db["workspaces"].delete_one({"workspace_id": workspace_id})
        disconnect_sync()
    except Exception:
        pass
