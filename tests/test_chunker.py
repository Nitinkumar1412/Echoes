# -*- coding: utf-8 -*-
"""Unit tests for boundary-aware chunking engine."""
from backend.app.services.chunker import (
    chunk_document,
    estimate_token_count,
    split_into_sentence_units,
)
from backend.app.services.parsers.base import PageContent, ParsedDocument


def test_token_estimation():
    assert estimate_token_count("") == 0
    assert estimate_token_count("Hello world") >= 2


def test_sentence_splitting():
    text = "First sentence here. Second sentence follows! Third question?"
    units = split_into_sentence_units(text)
    assert len(units) == 3
    assert units[0][0] == "First sentence here."
    assert units[1][0] == "Second sentence follows!"
    assert units[2][0] == "Third question?"


def test_chunk_document_deterministic_ids():
    # Long text to generate multiple chunks
    paragraphs = [
        f"Paragraph {i}: Echoes Search is a personal knowledge retrieval and reconstruction system that allows users to upload documents, PDFs, conversations, screenshots, and transcripts. Grounded answers with full citations are generated."
        for i in range(15)
    ]
    full_text = "\n\n".join(paragraphs)

    pages = [
        PageContent(page_number=1, text=full_text[:500], char_start=0, char_end=500),
        PageContent(page_number=2, text=full_text[500:], char_start=500, char_end=len(full_text)),
    ]
    parsed_doc = ParsedDocument(text=full_text, pages=pages, page_count=2)

    chunks = chunk_document(
        parsed_doc=parsed_doc,
        document_id="doc_test123",
        workspace_id="ws_abc",
        chunk_size=100,
        overlap=20,
    )

    assert len(chunks) > 1
    # Verify deterministic chunk IDs format
    for idx, c in enumerate(chunks):
        assert c.chunk_id == f"doc_test123__chunk_{idx:04d}"
        assert c.document_id == "doc_test123"
        assert c.workspace_id == "ws_abc"
        assert c.location.chunk_index == idx
        assert c.content.token_count > 0
        assert c.location.page_number in (1, 2)
