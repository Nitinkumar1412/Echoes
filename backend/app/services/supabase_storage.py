# -*- coding: utf-8 -*-
"""
Supabase Cloud Storage Service for Echoes Platform.
Handles secure upload, retrieval, signed URLs, and deletion of documents (PDFs, DOCX, TXT, Images, etc.).
Falls back gracefully to local disk storage if Supabase credentials are not configured.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from backend.app.core.config import settings

logger = logging.getLogger("echoes.supabase_storage")


class SupabaseStorageService:
    """Service to interact with Supabase Cloud Storage."""

    def __init__(self) -> None:
        self.url = settings.SUPABASE_URL.strip()
        self.key = settings.SUPABASE_KEY.strip()
        self.default_bucket = settings.SUPABASE_BUCKET.strip() or "documents"
        self._client: Any = None
        self._bucket_checked: bool = False

    @property
    def is_configured(self) -> bool:
        """Return True if Supabase URL and Key are provided."""
        return bool(self.url and self.key and not self.url.startswith("your_"))

    def get_client(self) -> Any:
        """Get or initialize the Supabase client."""
        if not self.is_configured:
            return None

        if self._client is None:
            try:
                from supabase import create_client
                self._client = create_client(self.url, self.key)
                logger.info("[SUPABASE] Connected to Supabase at %s", self.url)
            except Exception as exc:
                logger.error("[SUPABASE ERROR] Failed to initialize Supabase client: %s", exc)
                return None
        return self._client

    def ensure_bucket_exists(self, bucket_name: Optional[str] = None) -> bool:
        """Ensure the specified bucket exists in Supabase. Creates it if missing."""
        client = self.get_client()
        if not client:
            return False

        target_bucket = bucket_name or self.default_bucket
        try:
            # Check if bucket exists
            buckets = client.storage.list_buckets()
            bucket_names = [b.name for b in buckets if hasattr(b, "name")] or [
                b.get("name") for b in buckets if isinstance(b, dict)
            ]

            if target_bucket not in bucket_names:
                logger.info("[SUPABASE] Bucket '%s' not found. Creating public bucket...", target_bucket)
                client.storage.create_bucket(
                    target_bucket,
                    options={"public": True, "file_size_limit": settings.MAX_FILE_SIZE_MB * 1024 * 1024},
                )
                logger.info("[SUPABASE] Successfully created bucket '%s'", target_bucket)
            self._bucket_checked = True
            return True
        except Exception as exc:
            # Some service keys or permissions might disallow bucket creation or listing, but still allow uploads
            logger.warning("[SUPABASE WARN] Could not verify/create bucket '%s': %s", target_bucket, exc)
            return True

    def upload_file(
        self,
        file_bytes: bytes,
        destination_path: str,
        mime_type: str = "application/octet-stream",
        bucket_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload raw file bytes (PDF, Image, DOCX, TXT) to Supabase Storage.

        Returns:
            Dict containing storage_path, storage_url, and provider ("supabase" or "local").
        """
        client = self.get_client()
        target_bucket = bucket_name or self.default_bucket

        if not client:
            logger.debug("[SUPABASE] Supabase credentials not set. Skipping cloud upload.")
            return {
                "storage_path": destination_path,
                "storage_url": None,
                "provider": "local",
            }

        # Check bucket on first upload
        if not self._bucket_checked:
            self.ensure_bucket_exists(target_bucket)

        # Standardize path (no leading slash)
        clean_path = destination_path.lstrip("/")

        try:
            logger.info("[SUPABASE] Uploading '%s' (%d bytes) to bucket '%s'", clean_path, len(file_bytes), target_bucket)
            # Upload with upsert enabled so re-uploading identical paths succeeds
            client.storage.from_(target_bucket).upload(
                path=clean_path,
                file=file_bytes,
                file_options={"content-type": mime_type, "upsert": "true"},
            )

            # Retrieve URL
            public_url = self.get_public_url(clean_path, target_bucket)
            logger.info("[SUPABASE] Successfully uploaded '%s'. URL: %s", clean_path, public_url)

            return {
                "storage_path": clean_path,
                "storage_url": public_url,
                "provider": "supabase",
            }
        except Exception as exc:
            logger.error("[SUPABASE ERROR] Failed to upload '%s': %s", clean_path, exc)
            # Return path without url so caller can fallback to local path
            return {
                "storage_path": clean_path,
                "storage_url": None,
                "provider": "local",
                "error": str(exc),
            }

    def get_public_url(self, storage_path: str, bucket_name: Optional[str] = None) -> str:
        """Get the public URL for a file stored in Supabase."""
        client = self.get_client()
        target_bucket = bucket_name or self.default_bucket
        if not client:
            return ""

        clean_path = storage_path.lstrip("/")
        try:
            res = client.storage.from_(target_bucket).get_public_url(clean_path)
            return str(res) if res else ""
        except Exception as exc:
            logger.warning("[SUPABASE WARN] Failed to get public url for '%s': %s", clean_path, exc)
            return ""

    def create_signed_url(
        self,
        storage_path: str,
        expires_in: int = 3600,
        bucket_name: Optional[str] = None,
    ) -> Optional[str]:
        """Create a temporary signed URL for private bucket access."""
        client = self.get_client()
        target_bucket = bucket_name or self.default_bucket
        if not client:
            return None

        clean_path = storage_path.lstrip("/")
        try:
            res = client.storage.from_(target_bucket).create_signed_url(clean_path, expires_in)
            if isinstance(res, dict) and "signedURL" in res:
                return res["signedURL"]
            if hasattr(res, "signed_url"):
                return res.signed_url
            return str(res)
        except Exception as exc:
            logger.error("[SUPABASE ERROR] Failed to create signed url for '%s': %s", clean_path, exc)
            return None

    def download_file(self, storage_path: str, bucket_name: Optional[str] = None) -> Optional[bytes]:
        """Download file bytes directly from Supabase Storage."""
        client = self.get_client()
        target_bucket = bucket_name or self.default_bucket
        if not client:
            return None

        clean_path = storage_path.lstrip("/")
        try:
            data = client.storage.from_(target_bucket).download(clean_path)
            return data if isinstance(data, bytes) else bytes(data)
        except Exception as exc:
            logger.error("[SUPABASE ERROR] Failed to download '%s': %s", clean_path, exc)
            return None

    def delete_file(self, storage_path: str, bucket_name: Optional[str] = None) -> bool:
        """Delete a file from Supabase Storage."""
        client = self.get_client()
        target_bucket = bucket_name or self.default_bucket
        if not client:
            return False

        clean_path = storage_path.lstrip("/")
        try:
            client.storage.from_(target_bucket).remove([clean_path])
            logger.info("[SUPABASE] Deleted '%s' from bucket '%s'", clean_path, target_bucket)
            return True
        except Exception as exc:
            logger.error("[SUPABASE ERROR] Failed to delete '%s': %s", clean_path, exc)
            return False


# Singleton instance
supabase_storage = SupabaseStorageService()
