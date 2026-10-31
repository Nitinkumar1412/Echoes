# -*- coding: utf-8 -*-
"""User model — identity and authentication anchor."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import Field, field_validator

from .base import EchoesBaseModel, utcnow


class UserSettings(EchoesBaseModel):
    default_workspace_id: Optional[str] = None
    result_limit: int = Field(default=10, ge=1, le=100)
    preferred_language: str = "en"


class User(EchoesBaseModel):
    """
    MongoDB collection: users
    Primary key: user_id (UUID string, stable)
    """
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    hashed_password: Optional[str] = None
    is_active: bool = True
    settings: UserSettings = Field(default_factory=UserSettings)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    def to_safe_dict(self) -> dict:
        """Returns public user representation omitting hashed_password."""
        d = self.model_dump()
        d.pop("hashed_password", None)
        return d

    @field_validator("email")
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
            raise ValueError("Invalid email format")
        return cleaned

    @field_validator("display_name")
    @classmethod
    def display_name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("display_name cannot be empty")
        return v.strip()

    @classmethod
    def create(cls, email: str, display_name: str, **kwargs) -> "User":
        """Factory method — creates a new user with defaults."""
        return cls(email=email, display_name=display_name, **kwargs)
