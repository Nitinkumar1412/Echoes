# -*- coding: utf-8 -*-
"""Unit tests for all 8 Echoes Pydantic domain models."""
import pytest
from pydantic import ValidationError

from backend.app.models import (
    AnswerConfidence,
    Chunk,
    Document,
    DocumentFile,
    Entity,
    EntityType,
    Event,
    EventType,
    FileType,
    MemberRole,
    ProcessingStatus,
    Query,
    QueryInput,
    QueryStatus,
    Relationship,
    RelationshipType,
    User,
    Workspace,
)


def test_user_creation_and_validation():
    user = User(email="test@echoes.ai", display_name="Test User")
    assert user.user_id is not None
    assert user.email == "test@echoes.ai"
    assert user.display_name == "Test User"
    assert user.is_active is True

    # Invalid email test (should raise ValidationError)
    with pytest.raises(ValidationError):
        User(email="not-an-email", display_name="Bad User")


def test_workspace_creation():
    user = User(email="owner@echoes.ai", display_name="Owner")
    ws = Workspace.create(
        name="Personal Project",
        owner_id=user.user_id,
        description="A test workspace",
    )
    assert ws.workspace_id is not None
    assert ws.owner_id == user.user_id
    assert len(ws.members) == 1
    assert ws.members[0].role == MemberRole.OWNER
    assert ws.is_deleted is False


def test_document_creation():
    file_info = DocumentFile(
        original_name="notes.pdf",
        stored_name="abc-123.pdf",
        storage_path="documents/abc-123.pdf",
        mime_type="application/pdf",
        file_type=FileType.PDF,
        size_bytes=1024,
        sha256_hash="abc123hash",
    )
    doc = Document.create(
        workspace_id="ws_123",
        uploaded_by="usr_123",
        file=file_info,
    )
    assert doc.document_id is not None
    assert doc.workspace_id == "ws_123"
    assert doc.file.original_name == "notes.pdf"
    assert doc.processing.status == ProcessingStatus.PENDING


def test_chunk_deterministic_id():
    chunk = Chunk.create(
        document_id="doc_abc",
        workspace_id="ws_123",
        index=0,
        text="This is a test chunk content.",
        token_count=6,
        char_start=0,
        char_end=28,
        chunk_size=512,
        overlap=64,
    )
    assert chunk.chunk_id == "doc_abc__chunk_0000"
    assert chunk.vector.chroma_id == "doc_abc__chunk_0000"
    assert chunk.location.chunk_index == 0
    assert chunk.content.token_count == 6


def test_entity_creation():
    entity = Entity.create(
        workspace_id="ws_123",
        canonical_name="Echoes AI",
        entity_type=EntityType.PROJECT,
        aliases=["Echoes", "Project Echoes"],
    )
    assert entity.entity_id is not None
    assert entity.identity.canonical_name == "Echoes AI"
    assert entity.identity.entity_type == EntityType.PROJECT
    assert "Echoes" in entity.identity.aliases


def test_event_creation():
    event = Event.create(
        workspace_id="ws_123",
        title="Project Kickoff",
        original_expression="October 2026",
        event_type=EventType.MILESTONE,
    )
    assert event.event_id is not None
    assert event.title == "Project Kickoff"
    assert event.temporal.original_expression == "October 2026"
    assert event.event_type == EventType.MILESTONE


def test_relationship_creation():
    rel = Relationship(
        workspace_id="ws_123",
        from_entity_id="ent_1",
        to_entity_id="ent_2",
        relationship_type=RelationshipType.WORKED_ON,
        confidence=0.95,
    )
    assert rel.relationship_id is not None
    assert rel.from_entity_id == "ent_1"
    assert rel.to_entity_id == "ent_2"
    assert rel.relationship_type == RelationshipType.WORKED_ON
    assert rel.confidence == 0.95


def test_query_creation():
    q = Query(
        workspace_id="ws_123",
        user_id="usr_123",
        input=QueryInput(query_text="What was discussed in October?"),
    )
    assert q.query_id is not None
    assert q.input.query_text == "What was discussed in October?"
    assert q.status == QueryStatus.PROCESSING
    assert q.answer is None
