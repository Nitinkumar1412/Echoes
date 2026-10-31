# -*- coding: utf-8 -*-
"""
Document ingestion pipeline service for Echoes Search.
Handles SHA-256 deduplication, file storage, parsing, chunking, and MongoDB persistence.
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.core.config import settings
from backend.app.models.base import utcnow
from backend.app.models.chunk import Chunk
from backend.app.models.document import (
    ContentMeta,
    Document,
    DocumentFile,
    FileType,
    ProcessingStatus,
)
from backend.app.services.chunker import chunk_document
from backend.app.services.parsers.factory import detect_file_type, parse_document
from backend.app.services.supabase_storage import supabase_storage
from backend.app.services.vector_store import VectorStoreService

logger = logging.getLogger("echoes.ingestion")


def compute_sha256(content_bytes: bytes) -> str:
    """Compute hex SHA-256 checksum of raw file bytes."""
    return hashlib.sha256(content_bytes).hexdigest()


class IngestionService:
    """Orchestrates document ingestion from upload to parsed and chunked database records."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def ingest_file(
        self,
        workspace_id: str,
        uploaded_by: str,
        filename: str,
        content_bytes: bytes,
        mime_type: Optional[str] = None,
    ) -> Tuple[Document, bool]:
        """
        Ingest a file into a workspace.

        Returns:
            Tuple of (Document, is_duplicate: bool)
        """
        sha256_hash = compute_sha256(content_bytes)
        file_size_bytes = len(content_bytes)
        file_type = detect_file_type(filename)

        # 1. Deduplication check within workspace
        existing = await self.db["documents"].find_one(
            {
                "workspace_id": workspace_id,
                "file.sha256_hash": sha256_hash,
                "is_deleted": False,
            }
        )
        if existing:
            logger.info(
                "[INGEST] Duplicate file detected for workspace %s (sha256: %s)",
                workspace_id,
                sha256_hash[:10],
            )
            return Document.model_validate(existing), True

        # 2. Persist file to local cache (for parsers) and Supabase Cloud Storage
        stored_ext = Path(filename).suffix.lower() or ".bin"
        stored_filename = f"{uuid4().hex}{stored_ext}"
        workspace_storage_dir = settings.upload_dir_path / workspace_id
        workspace_storage_dir.mkdir(parents=True, exist_ok=True)
        target_path = workspace_storage_dir / stored_filename
        target_path.write_bytes(content_bytes)

        # 2b. Upload to Supabase Storage if configured
        storage_url: Optional[str] = None
        storage_provider: str = "local"
        supabase_path = f"{workspace_id}/{stored_filename}"

        if supabase_storage.is_configured:
            try:
                upload_res = supabase_storage.upload_file(
                    file_bytes=content_bytes,
                    destination_path=supabase_path,
                    mime_type=mime_type or "application/octet-stream",
                )
                if upload_res.get("provider") == "supabase":
                    storage_url = upload_res.get("storage_url")
                    storage_provider = "supabase"
                    logger.info("[INGEST] Successfully saved to Supabase: %s", storage_url)
            except Exception as sb_err:
                logger.warning("[INGEST WARN] Supabase upload failed, falling back to local: %s", sb_err)

        # 3. Create initial Document model (PENDING)
        doc_file = DocumentFile(
            original_name=filename,
            stored_name=stored_filename,
            storage_path=supabase_path if storage_provider == "supabase" else str(target_path.relative_to(settings.upload_dir_path)),
            mime_type=mime_type or "application/octet-stream",
            file_type=file_type,
            size_bytes=file_size_bytes,
            sha256_hash=sha256_hash,
            storage_url=storage_url,
            storage_provider=storage_provider,
        )
        document = Document.create(
            workspace_id=workspace_id,
            uploaded_by=uploaded_by,
            file=doc_file,
        )
        document.processing.status = ProcessingStatus.PROCESSING
        document.processing.started_at = utcnow()

        # Insert document record in processing state
        await self.db["documents"].insert_one(document.model_dump())

        # 4. Parse document
        try:
            parsed_doc, _ = parse_document(target_path)
            document.content_meta = ContentMeta(
                page_count=parsed_doc.page_count,
                word_count=parsed_doc.word_count,
                extracted_title=parsed_doc.extracted_title,
                encoding=parsed_doc.encoding,
                language=parsed_doc.language,
            )

            # 5. Chunk document
            chunks = chunk_document(
                parsed_doc=parsed_doc,
                document_id=document.document_id,
                workspace_id=workspace_id,
            )

            # 6. Bulk insert chunks if text extracted
            indexed_count = 0
            if chunks:
                # 6a. Index into ChromaDB vector store
                try:
                    vs = VectorStoreService()
                    indexed_count = vs.upsert_chunks(chunks)
                    for c in chunks:
                        c.vector.is_indexed = True
                        c.vector.indexed_at = utcnow()
                        c.vector.embedding_model = settings.EMBEDDING_MODEL
                except Exception as vector_err:
                    logger.error("[INGEST WARN] Vector indexing failed for doc %s: %s", document.document_id, vector_err)

                # 6b. Insert chunks into MongoDB
                chunk_docs = [c.model_dump() for c in chunks]
                await self.db["chunks"].insert_many(chunk_docs)

                # 6c. Extract and index knowledge graph (entities, events, relationships)
                try:
                    from backend.app.services.graph.pipeline import extract_and_index_graph_for_chunks
                    await extract_and_index_graph_for_chunks(self.db, workspace_id, chunks)
                except Exception as graph_err:
                    logger.error("[INGEST WARN] Graph extraction failed for doc %s: %s", document.document_id, graph_err)

            # 7. Update document status to COMPLETED
            document.processing.status = ProcessingStatus.COMPLETED
            document.processing.chunk_count = len(chunks)
            document.processing.indexed_chunk_count = indexed_count
            document.processing.completed_at = utcnow()
            document.updated_at = utcnow()

            await self.db["documents"].update_one(
                {"document_id": document.document_id},
                {"$set": document.model_dump()},
            )

            # 8. Update workspace stats
            await self.db["workspaces"].update_one(
                {"workspace_id": workspace_id},
                {
                    "$inc": {
                        "stats.document_count": 1,
                        "stats.chunk_count": len(chunks),
                        "stats.total_size_bytes": file_size_bytes,
                    },
                    "$set": {"updated_at": utcnow()},
                },
            )

            logger.info(
                "[INGEST] Successfully ingested doc %s ('%s'): %d chunks created",
                document.document_id,
                filename,
                len(chunks),
            )
            return document, False

        except Exception as exc:
            logger.error("[INGEST ERROR] Ingestion failed for doc %s: %s", document.document_id, exc)
            document.processing.status = ProcessingStatus.FAILED
            document.processing.error_message = str(exc)
            document.processing.retry_count += 1
            document.updated_at = utcnow()

            await self.db["documents"].update_one(
                {"document_id": document.document_id},
                {"$set": document.model_dump()},
            )
            raise exc
