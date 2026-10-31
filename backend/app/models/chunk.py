# -*- coding: utf-8 -*-
"""Chunk model — atomic retrieval unit linking MongoDB to ChromaDB."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import EchoesBaseModel, utcnow


class ChunkContent(EchoesBaseModel):
    text: str                   # the actual chunk text — main retrieval content
    token_count: int
    char_start: int             # character offset in full extracted document text
    char_end: int


class ChunkLocation(EchoesBaseModel):
    chunk_index: int            # 0-based position within the document
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    paragraph_index: Optional[int] = None


class ChunkingMeta(EchoesBaseModel):
    strategy: str               # e.g. "fixed_512_overlap_64"
    chunk_size: int
    overlap: int


class ChunkVector(EchoesBaseModel):
    """
    Links this chunk to its ChromaDB embedding.
    chroma_id == chunk_id — same identifier used in both stores.
    NO embedding array is stored here; embeddings live entirely in ChromaDB.
    """
    chroma_id: str
    is_indexed: bool = False
    indexed_at: Optional[datetime] = None
    embedding_model: Optional[str] = None


class Chunk(EchoesBaseModel):
    """
    MongoDB collection: chunks
    Primary key: chunk_id (deterministic string, unique)
    Format: "{document_id}__chunk_{index:04d}"

    workspace_id is denormalized from the parent document to avoid a join
    on every BM25 and embedding pipeline query.
    """
    chunk_id: str               # set explicitly via make_id()
    document_id: str            # ref: documents.document_id
    workspace_id: str           # ref: workspaces.workspace_id (denormalized)
    content: ChunkContent
    location: ChunkLocation
    chunking_meta: ChunkingMeta
    vector: ChunkVector
    created_at: datetime = Field(default_factory=utcnow)

    @staticmethod
    def make_id(document_id: str, index: int) -> str:
        """Generate the deterministic chunk ID."""
        return f"{document_id}__chunk_{index:04d}"

    @classmethod
    def create(
        cls,
        document_id: str,
        workspace_id: str,
        index: int,
        text: str,
        token_count: int,
        char_start: int,
        char_end: int,
        chunk_size: int,
        overlap: int,
        page_number: Optional[int] = None,
        section_heading: Optional[str] = None,
    ) -> "Chunk":
        chunk_id = cls.make_id(document_id, index)
        return cls(
            chunk_id=chunk_id,
            document_id=document_id,
            workspace_id=workspace_id,
            content=ChunkContent(
                text=text,
                token_count=token_count,
                char_start=char_start,
                char_end=char_end,
            ),
            location=ChunkLocation(
                chunk_index=index,
                page_number=page_number,
                section_heading=section_heading,
            ),
            chunking_meta=ChunkingMeta(
                strategy=f"fixed_{chunk_size}_overlap_{overlap}",
                chunk_size=chunk_size,
                overlap=overlap,
            ),
            vector=ChunkVector(chroma_id=chunk_id),
        )
