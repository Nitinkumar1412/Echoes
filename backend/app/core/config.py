# -*- coding: utf-8 -*-
"""
Echoes Search — Application Configuration
All settings are loaded from environment variables / .env file.
Never hardcode secrets here.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

# Resolve project root so the .env is always found regardless of CWD
_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # backend/app/core → project root


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "Echoes Search"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ── MongoDB Atlas ─────────────────────────────────────────────────────────
    MONGODB_URI: str = "mongodb+srv://user_nitin:c6zfo31m5JCaiXaW@echoescluster.bmdvsoz.mongodb.net/echoes_db?retryWrites=true&w=majority"
    MONGODB_DATABASE: str = "echoes_db"

    # ── Google Gemini ─────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = "AQ.Ab8RN6LV6KyKXxstMN9YmPvAWmBYLfeoxIr8A0sQOEcKZfo7eQ"
    MODEL_NAME: str = "gemini-2.5-flash"

    # ── Storage Paths & Supabase Cloud Storage ───────────────────────────────
    UPLOAD_DIR: str = "./storage/documents"
    CHROMA_PATH: str = "./storage/vectors"
    SUPABASE_URL: str = "https://ypstgmatzzsljykhaklw.supabase.co"
    SUPABASE_KEY: str = "sb_secret_cB4xxqiI5WUvMcLJty5Rpw_zHifzhB-"
    SUPABASE_BUCKET: str = "Echoes_documents"
    SUPABASE_PUBLIC_URL_EXPIRY: int = 3600

    # ── Document Processing ───────────────────────────────────────────────────
    CHUNK_SIZE: int = 512          # tokens per chunk
    CHUNK_OVERLAP: int = 64        # token overlap between adjacent chunks
    MAX_FILE_SIZE_MB: int = 50     # maximum upload file size in megabytes

    # ── Embedding ─────────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_BATCH_SIZE: int = 32

    # ── Retrieval ─────────────────────────────────────────────────────────────
    TOP_K_SEMANTIC: int = 20       # candidates from ChromaDB
    TOP_K_BM25: int = 20           # candidates from BM25
    TOP_K_RERANKED: int = 10       # final chunks after reranking

    # ── JWT & OAuth Authentication ────────────────────────────────────────────
    JWT_SECRET_KEY: str = "echoes-super-secret-jwt-token-key-2026-secure-random-seed-32bytes"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    GOOGLE_CLIENT_ID: str = ""

    # ── CORS (comma-separated origins) ───────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def upload_dir_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        return p if p.is_absolute() else _ROOT / p

    @property
    def chroma_path_path(self) -> Path:
        p = Path(self.CHROMA_PATH)
        return p if p.is_absolute() else _ROOT / p

    model_config = {
        "env_file": (str(_ROOT / ".env"), str(_ROOT / "backend" / ".env")),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Module-level singleton — import this everywhere
settings: Settings = get_settings()
