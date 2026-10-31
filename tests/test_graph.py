# -*- coding: utf-8 -*-
"""Integration and unit tests for Knowledge Graph and Temporal Engine (Milestone 5)."""
import io
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.main import app
from backend.app.models.chunk import Chunk
from backend.app.services.database import connect_async, disconnect_async
from backend.app.services.graph.entity_extractor import EntityExtractorService
from backend.app.services.graph.event_extractor import EventExtractorService
from backend.app.services.graph.networkx_service import NetworkXGraphService


@pytest.mark.anyio
async def test_entity_extraction_and_fuzzy_dedup():
    """Verify entity extraction and RapidFuzz deduplication across mentions."""
    db = await connect_async(settings.MONGODB_URI, settings.MONGODB_DATABASE)
    workspace_id = f"ws_ent_{uuid.uuid4().hex[:6]}"

    extractor = EntityExtractorService(db, fuzzy_threshold=80.0)

    # Chunk 1 with full title
    chunk1 = Chunk.create(
        document_id="doc_1",
        workspace_id=workspace_id,
        index=0,
        text="Dr. Nitin Sharma organized the engineering review for Project Apollo.",
        token_count=10,
        char_start=0,
        char_end=65,
        chunk_size=512,
        overlap=64,
    )
    # Chunk 2 with informal name
    chunk2 = Chunk.create(
        document_id="doc_2",
        workspace_id=workspace_id,
        index=0,
        text="During the review, Nitin Sharma presented the architecture slides.",
        token_count=10,
        char_start=0,
        char_end=65,
        chunk_size=512,
        overlap=64,
    )

    ents1 = await extractor.extract_and_upsert_chunk_entities(workspace_id, chunk1)
    ents2 = await extractor.extract_and_upsert_chunk_entities(workspace_id, chunk2)

    # Count how many Person entities exist for Nitin Sharma in the workspace
    person_docs = await db["entities"].find(
        {"workspace_id": workspace_id, "identity.entity_type": "PERSON"}
    ).to_list(length=10)

    # Should have deduplicated to exactly 1 Person entity with multiple provenance records
    assert len(person_docs) == 1
    assert "Nitin Sharma" in person_docs[0]["identity"]["canonical_name"]
    assert len(person_docs[0]["provenance"]) >= 2
    assert person_docs[0]["stats"]["mention_count"] >= 2

    # Cleanup
    await db["entities"].delete_many({"workspace_id": workspace_id})
    await disconnect_async()


@pytest.mark.anyio
async def test_event_extraction_and_normalization():
    """Verify temporal event extraction and ISO date normalization."""
    db = await connect_async(settings.MONGODB_URI, settings.MONGODB_DATABASE)
    workspace_id = f"ws_ev_{uuid.uuid4().hex[:6]}"

    extractor = EventExtractorService(db)
    chunk = Chunk.create(
        document_id="doc_ev",
        workspace_id=workspace_id,
        index=0,
        text="The clinical kickoff meeting was scheduled for October 14, 2026.",
        token_count=10,
        char_start=0,
        char_end=60,
        chunk_size=512,
        overlap=64,
    )

    events = await extractor.extract_and_upsert_chunk_events(workspace_id, chunk)
    assert len(events) >= 1
    ev = events[0]
    assert ev.temporal.normalized_date is not None
    assert ev.temporal.normalized_date.year == 2026
    assert ev.temporal.normalized_date.month == 10
    assert ev.temporal.normalized_date.day == 14
    assert ev.temporal.date_precision == "day"

    # Cleanup
    await db["events"].delete_many({"workspace_id": workspace_id})
    await disconnect_async()


def test_graph_and_timeline_api_endpoints():
    """Verify live document upload triggers graph extraction and populates /graph, /timeline, /entities."""
    workspace_id = f"ws_graph_api_{uuid.uuid4().hex[:8]}"
    doc_content = (
        b"# Space Missions\n\n"
        b"Director Sarah Connor authorized Project Artemis on September 15, 2025.\n\n"
        b"Lead engineer John Connor developed the navigation subsystem for Project Artemis."
    )
    filename = "artemis_mission.md"

    with TestClient(app) as client:
        # 1. Upload document (triggers ingestion + chunking + vectors + graph extraction)
        upload_resp = client.post(
            f"/api/v1/workspaces/{workspace_id}/documents/upload",
            files={"file": (filename, io.BytesIO(doc_content), "text/markdown")},
        )
        assert upload_resp.status_code == 201

        # 2. Test GET /entities
        ent_resp = client.get(f"/api/v1/workspaces/{workspace_id}/entities")
        assert ent_resp.status_code == 200
        ent_data = ent_resp.json()
        assert ent_data["total_entities"] >= 2
        entity_names = [e["canonical_name"] for e in ent_data["entities"]]
        assert any("Connor" in name for name in entity_names)

        # 3. Test GET /timeline
        time_resp = client.get(f"/api/v1/workspaces/{workspace_id}/timeline")
        assert time_resp.status_code == 200
        time_data = time_resp.json()
        assert time_data["total_events"] >= 1
        assert "September" in time_data["events"][0]["original_expression"]

        # 4. Test GET /graph
        graph_resp = client.get(f"/api/v1/workspaces/{workspace_id}/graph")
        assert graph_resp.status_code == 200
        graph_data = graph_resp.json()
        assert len(graph_data["nodes"]) >= 2
        assert len(graph_data["edges"]) >= 1

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
        disconnect_sync()
    except Exception:
        pass
