# -*- coding: utf-8 -*-
"""
Shared base class and utilities for all Echoes Pydantic models.
"""
from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware). Use instead of deprecated utcnow()."""
    return datetime.now(timezone.utc)


from pydantic import BaseModel, ConfigDict


class EchoesBaseModel(BaseModel):
    """
    Base model for all Echoes domain models.
    - populate_by_name: allows both field name and alias
    - arbitrary_types_allowed: needed for ObjectId if ever used
    """
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        use_enum_values=True,       # store enum as string value in dicts
    )
