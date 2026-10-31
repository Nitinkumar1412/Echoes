# -*- coding: utf-8 -*-
"""Document management and upload API routes."""
from __future__ import annotations

import logging
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, RedirectResponse, Response
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.api.dependencies import verify_workspace_access
from backend.app.core.config import settings
from backend.app.models.base import utcnow
from backend.app.models.user import User
from backend.app.models.workspace import Workspace
from backend.app.schemas.document import (
    ChunkResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from backend.app.services.database import get_async_db
from backend.app.services.ingestion import IngestionService
from backend.app.services.supabase_storage import supabase_storage
from backend.app.services.vector_store import VectorStoreService

logger = logging.getLogger("echoes.api.documents")

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    workspace_id: str,
    file: UploadFile = File(...),
    uploaded_by: str = Form("user_default"),
    db: AsyncIOMotorDatabase = Depends(get_async_db),
    access: tuple[Workspace, User] = Depends(verify_workspace_access),
) -> DocumentUploadResponse:
    """
    Upload a document (PDF, DOCX, TXT, MD, Image) to a workspace.
    Performs SHA-256 deduplication, boundary-aware chunking, and stores in MongoDB.
    Requires authenticated user who is a member of the workspace.
    """
    _, current_user = access

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    # Read content and enforce file size limit
    content = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB.",
        )

    ingestion = IngestionService(db)
    try:
        doc, is_duplicate = await ingestion.ingest_file(
            workspace_id=workspace_id,
            uploaded_by=current_user.user_id,  # Use authenticated user ID
            filename=file.filename,
            content_bytes=content,
            mime_type=file.content_type,
        )
        msg = "File already exists in workspace (deduplicated)." if is_duplicate else "Document uploaded and processed successfully."
        return DocumentUploadResponse(
            message=msg,
            document=DocumentResponse.model_validate(doc.model_dump()),
            is_duplicate=is_duplicate,
            chunks_created=doc.processing.chunk_count,
        )
    except Exception as exc:
        logger.error("[API UPLOAD ERROR] Error processing file %s: %s", file.filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {exc}",
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    workspace_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_async_db),
    access: tuple[Workspace, User] = Depends(verify_workspace_access),
) -> DocumentListResponse:
    """List all active documents in this workspace (members only)."""
    query = {"workspace_id": workspace_id, "is_deleted": False}
    total = await db["documents"].count_documents(query)
    cursor = db["documents"].find(query).sort("created_at", -1).skip(skip).limit(limit)

    docs = []
    async for d in cursor:
        docs.append(DocumentResponse.model_validate(d))

    return DocumentListResponse(
        workspace_id=workspace_id,
        total_count=total,
        documents=docs,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    workspace_id: str,
    document_id: str,
    db: AsyncIOMotorDatabase = Depends(get_async_db),
    access: tuple[Workspace, User] = Depends(verify_workspace_access),
) -> DocumentResponse:
    """Retrieve details and processing status of a single document (workspace members only)."""
    doc_data = await db["documents"].find_one(
        {"workspace_id": workspace_id, "document_id": document_id, "is_deleted": False}
    )
    if not doc_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found in workspace '{workspace_id}'.",
        )
    return DocumentResponse.model_validate(doc_data)


@router.get("/{document_id}/chunks", response_model=List[ChunkResponse])
async def get_document_chunks(
    workspace_id: str,
    document_id: str,
    db: AsyncIOMotorDatabase = Depends(get_async_db),
    access: tuple[Workspace, User] = Depends(verify_workspace_access),
) -> List[ChunkResponse]:
    """Retrieve all chunks for a document (workspace members only)."""
    # Verify document exists and belongs to this workspace
    doc = await db["documents"].find_one(
        {"workspace_id": workspace_id, "document_id": document_id, "is_deleted": False}
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    cursor = db["chunks"].find({"document_id": document_id, "workspace_id": workspace_id}).sort("location.chunk_index", 1)
    chunk_list = []
    async for c in cursor:
        chunk_list.append(
            ChunkResponse(
                chunk_id=c["chunk_id"],
                document_id=c["document_id"],
                workspace_id=c["workspace_id"],
                text=c["content"]["text"],
                token_count=c["content"]["token_count"],
                chunk_index=c["location"]["chunk_index"],
                page_number=c["location"].get("page_number"),
                section_heading=c["location"].get("section_heading"),
                char_start=c["content"]["char_start"],
                char_end=c["content"]["char_end"],
                is_indexed=c["vector"]["is_indexed"],
            )
        )
    return chunk_list


@router.get("/{document_id}/download")
async def download_document(
    workspace_id: str,
    document_id: str,
    db: AsyncIOMotorDatabase = Depends(get_async_db),
    access: tuple[Workspace, User] = Depends(verify_workspace_access),
):
    """Download document file from Supabase Cloud Storage or local disk."""
    doc_data = await db["documents"].find_one(
        {"workspace_id": workspace_id, "document_id": document_id, "is_deleted": False}
    )
    if not doc_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    file_info = doc_data.get("file", {})
    storage_provider = file_info.get("storage_provider", "local")
    storage_path = file_info.get("storage_path", "")
    storage_url = file_info.get("storage_url")
    original_name = file_info.get("original_name", "document.bin")
    mime_type = file_info.get("mime_type", "application/octet-stream")

    # 1. Supabase Storage download / redirect
    if storage_provider == "supabase" and supabase_storage.is_configured:
        # If public storage_url exists, redirect to it
        if storage_url:
            return RedirectResponse(url=storage_url)

        # Or download bytes directly from Supabase
        file_bytes = supabase_storage.download_file(storage_path)
        if file_bytes:
            return Response(
                content=file_bytes,
                media_type=mime_type,
                headers={"Content-Disposition": f'attachment; filename="{original_name}"'},
            )

    # 2. Local disk fallback
    local_path = settings.upload_dir_path / storage_path
    if not local_path.is_file():
        # Check workspace directory
        stored_name = file_info.get("stored_name", "")
        fallback_path = settings.upload_dir_path / workspace_id / stored_name
        if fallback_path.is_file():
            local_path = fallback_path

    if local_path.is_file():
        return FileResponse(
            path=local_path,
            filename=original_name,
            media_type=mime_type,
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Document file not found on storage server.",
    )


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    workspace_id: str,
    document_id: str,
    db: AsyncIOMotorDatabase = Depends(get_async_db),
    access: tuple[Workspace, User] = Depends(verify_workspace_access),
):
    """Delete a document, its chunks, vector embeddings, and stored cloud file."""
    doc_data = await db["documents"].find_one(
        {"workspace_id": workspace_id, "document_id": document_id, "is_deleted": False}
    )
    if not doc_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )

    file_info = doc_data.get("file", {})
    storage_provider = file_info.get("storage_provider", "local")
    storage_path = file_info.get("storage_path", "")
    size_bytes = file_info.get("size_bytes", 0)
    chunk_count = doc_data.get("processing", {}).get("chunk_count", 0)

    # 1. Remove from Supabase Storage if uploaded there
    if storage_provider == "supabase" and supabase_storage.is_configured and storage_path:
        try:
            supabase_storage.delete_file(storage_path)
        except Exception as sb_err:
            logger.warning("[DELETE WARN] Failed to delete file from Supabase: %s", sb_err)

    # 2. Remove local file if present
    try:
        local_path = settings.upload_dir_path / storage_path
        if local_path.is_file():
            local_path.unlink()
    except Exception as loc_err:
        logger.debug("[DELETE WARN] Failed to delete local file: %s", loc_err)

    # 3. Delete chunks from ChromaDB
    try:
        vs = VectorStoreService()
        vs.delete_document_vectors(document_id)
    except Exception as vec_err:
        logger.warning("[DELETE WARN] Failed to delete Chroma vectors for doc %s: %s", document_id, vec_err)

    # 4. Delete chunks from MongoDB
    await db["chunks"].delete_many({"workspace_id": workspace_id, "document_id": document_id})

    # 5. Soft delete document in MongoDB
    await db["documents"].update_one(
        {"document_id": document_id},
        {"$set": {"is_deleted": True, "deleted_at": utcnow()}},
    )

    # 6. Decrement workspace statistics
    await db["workspaces"].update_one(
        {"workspace_id": workspace_id},
        {
            "$inc": {
                "stats.document_count": -1,
                "stats.chunk_count": -chunk_count,
                "stats.total_size_bytes": -size_bytes,
            },
            "$set": {"updated_at": utcnow()},
        },
    )

    logger.info("[DELETE] Successfully deleted document %s from workspace %s", document_id, workspace_id)
    return {"message": f"Document '{document_id}' successfully deleted.", "document_id": document_id}
