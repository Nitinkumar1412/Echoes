# -*- coding: utf-8 -*-
"""Document model — provenance root for all uploaded files."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import Field

from .base import EchoesBaseModel, utcnow


class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    IMAGE = "image"
    TRANSCRIPT = "transcript"
    OTHER = "other"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class DocumentFile(EchoesBaseModel):
    """Immutable file metadata — set at upload time, never changed."""
    original_name: str          # as uploaded by the user
    stored_name: str            # UUID-based filename on disk (collision-safe)
    storage_path: str           # relative path from UPLOAD_DIR
    mime_type: str
    file_type: FileType
    size_bytes: int
    sha256_hash: str            # 64-char hex; used for duplicate detection
    storage_url: Optional[str] = None       # Public or direct access URL (e.g. Supabase Storage URL)
    storage_provider: str = "local"         # "supabase" or "local"


class ContentMeta(EchoesBaseModel):
    """Extracted during parsing — populated after processing completes."""
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    language: Optional[str] = None
    encoding: Optional[str] = None
    extracted_title: Optional[str] = None


class ProcessingInfo(EchoesBaseModel):
    """
    Tracks the processing pipeline state.
    State machine: pending → processing → completed | failed
    Failed documents with retry_count < 3 are retried automatically.
    """
    status: ProcessingStatus = ProcessingStatus.PENDING
    chunk_count: int = 0
    indexed_chunk_count: int = 0       # chunks with embeddings in ChromaDB
    error_message: Optional[str] = None
    retry_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class Document(EchoesBaseModel):
    """
    MongoDB collection: documents
    Primary key: document_id (UUID string, globally unique, stable)
    Unique constraint: (workspace_id, file.sha256_hash)
    """
    document_id: str = Field(default_factory=lambda: str(uuid4()))
    workspace_id: str                   # ref: workspaces.workspace_id
    uploaded_by: str                    # ref: users.user_id
    file: DocumentFile
    content_meta: ContentMeta = Field(default_factory=ContentMeta)
    processing: ProcessingInfo = Field(default_factory=ProcessingInfo)
    duplicate_of: Optional[str] = None  # document_id of original if this is a duplicate
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @classmethod
    def create(
        cls,
        workspace_id: str,
        uploaded_by: str,
        file: DocumentFile,
    ) -> "Document":
        """Create a new document in PENDING state."""
        return cls(
            workspace_id=workspace_id,
            uploaded_by=uploaded_by,
            file=file,
        )
