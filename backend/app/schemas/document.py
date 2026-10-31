# -*- coding: utf-8 -*-
"""API request and response schemas for document operations."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from backend.app.models.document import ContentMeta, DocumentFile, ProcessingInfo


class DocumentResponse(BaseModel):
    """Public representation of a Document."""
    document_id: str
    workspace_id: str
    uploaded_by: str
    file: DocumentFile
    content_meta: ContentMeta
    processing: ProcessingInfo
    duplicate_of: Optional[str] = None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(BaseModel):
    """Response returned upon uploading a document."""
    message: str
    document: DocumentResponse
    is_duplicate: bool
    chunks_created: int


class ChunkResponse(BaseModel):
    """Public representation of an individual chunk."""
    chunk_id: str
    document_id: str
    workspace_id: str
    text: str
    token_count: int
    chunk_index: int
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    char_start: int
    char_end: int
    is_indexed: bool


class DocumentListResponse(BaseModel):
    """Paginated list of documents in a workspace."""
    workspace_id: str
    total_count: int
    documents: List[DocumentResponse]
