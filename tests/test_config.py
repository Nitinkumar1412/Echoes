# -*- coding: utf-8 -*-
"""Tests for Echoes configuration loading."""
from pathlib import Path
from backend.app.core.config import Settings, get_settings, settings


def test_config_loads_from_env():
    """Verify settings instance is instantiated with expected defaults."""
    assert settings.APP_NAME == "Echoes Search"
    assert settings.MONGODB_DATABASE == "echoes_db"
    assert settings.CHUNK_SIZE > 0
    assert settings.CHUNK_OVERLAP > 0
    assert settings.TOP_K_SEMANTIC > 0


def test_cors_origins_list():
    """Verify CORS origins parsing splits comma-separated strings."""
    s = Settings(CORS_ORIGINS="http://localhost:3000, http://localhost:5173")
    origins = s.cors_origins_list
    assert "http://localhost:3000" in origins
    assert "http://localhost:5173" in origins


def test_storage_paths():
    """Verify upload and chroma paths are Path objects."""
    assert isinstance(settings.upload_dir_path, Path)
    assert isinstance(settings.chroma_path_path, Path)
