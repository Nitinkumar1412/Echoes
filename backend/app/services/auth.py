# -*- coding: utf-8 -*-
"""
Authentication & JWT Security Service for Echoes.
Provides secure password hashing via bcrypt, JWT token issuing and verification,
and FastAPI security dependencies for user authentication and authorization.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.app.core.config import get_settings
from backend.app.models.base import utcnow
from backend.app.models.user import User
from backend.app.models.workspace import Workspace
from backend.app.services.database import get_async_db

logger = logging.getLogger(__name__)
settings = get_settings()

security_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt with standard salt rounds."""
    # Bcrypt enforces a 72-byte max length on input
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored bcrypt hash."""
    if not hashed_password:
        return False
    try:
        pw_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception as exc:
        logger.warning("[AUTH] Password verification error: %s", exc)
        return False


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token with expiration time and issued-at timestamp."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": now,
    })
    token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodes and validates a JWT access token. Raises HTTPException on invalid/expired tokens."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def register_user(
    db: AsyncIOMotorDatabase,
    email: str,
    password: str,
    display_name: str,
) -> tuple[User, Workspace, str]:
    """
    Registers a new user, hashes password, provisions a default personal workspace,
    and returns (user, workspace, access_token).
    """
    email_clean = email.strip().lower()
    name_clean = display_name.strip()
    
    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long.",
        )
    
    # Check uniqueness
    existing = await db["users"].find_one({"email": email_clean})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )
    
    # Hash password & construct user
    hashed = hash_password(password)
    user = User(
        email=email_clean,
        display_name=name_clean or email_clean.split("@")[0],
        hashed_password=hashed,
    )
    
    # Provision personal workspace
    ws_name = f"{user.display_name}'s Workspace"
    workspace = Workspace.create(
        name=ws_name,
        owner_id=user.user_id,
        description="Personal memory space for documents, notes, and research.",
    )
    user.settings.default_workspace_id = workspace.workspace_id
    
    # Persist in MongoDB
    await db["workspaces"].insert_one(workspace.model_dump())
    await db["users"].insert_one(user.model_dump())
    
    logger.info("[AUTH] Registered user %s with workspace %s", user.user_id, workspace.workspace_id)
    
    # Generate token
    token = create_access_token({
        "sub": user.user_id,
        "email": user.email,
        "workspace_id": workspace.workspace_id,
    })
    
    return user, workspace, token


async def authenticate_user(
    db: AsyncIOMotorDatabase,
    email: str,
    password: str,
) -> tuple[User, str]:
    """
    Validates user credentials against MongoDB users collection.
    Returns (user, access_token).
    """
    email_clean = email.strip().lower()
    doc = await db["users"].find_one({"email": email_clean})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    doc_data = dict(doc)
    doc_data.pop("_id", None)
    user = User.model_validate(doc_data)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )
    
    if not user.hashed_password or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Issue token
    token = create_access_token({
        "sub": user.user_id,
        "email": user.email,
        "workspace_id": user.settings.default_workspace_id,
    })
    
    return user, token


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncIOMotorDatabase = Depends(get_async_db),
) -> User:
    """
    FastAPI dependency that enforces authentication.
    Extracts Bearer token from Authorization header and returns the active User object.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    doc = await db["users"].find_one({"user_id": user_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    doc_data = dict(doc)
    doc_data.pop("_id", None)
    user = User.model_validate(doc_data)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )
    return user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncIOMotorDatabase = Depends(get_async_db),
) -> Optional[User]:
    """Optional authentication dependency — returns User if valid token is provided, else None."""
    if not credentials or not credentials.credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        doc = await db["users"].find_one({"user_id": user_id})
        if not doc:
            return None
        doc_data = dict(doc)
        doc_data.pop("_id", None)
        return User.model_validate(doc_data)
    except Exception:
        return None


async def google_authenticate_or_register(
    db: AsyncIOMotorDatabase,
    credential: Optional[str] = None,
    email: Optional[str] = None,
    display_name: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> tuple[User, str, str]:
    """
    Authenticate or register a user via Google OAuth (GIS / OneTap / ID Token).
    Returns (user, workspace_id, access_token).
    """
    verified_email: Optional[str] = None
    verified_name: Optional[str] = None
    verified_picture: Optional[str] = None

    if credential:
        # 1. Try verifying Google ID token with google-auth library
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests

            client_id = settings.GOOGLE_CLIENT_ID or None
            idinfo = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                client_id,
            )
            verified_email = idinfo.get("email")
            verified_name = idinfo.get("name")
            verified_picture = idinfo.get("picture")
        except Exception as exc:
            logger.warning("[GOOGLE AUTH] Local token verification returned: %s. Trying tokeninfo check...", exc)
            # 2. Fallback to Google tokeninfo endpoint
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10.0) as http_client:
                    resp = await http_client.get(
                        f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
                    )
                    if resp.status_code == 200:
                        info = resp.json()
                        verified_email = info.get("email")
                        verified_name = info.get("name")
                        verified_picture = info.get("picture")
            except Exception as http_exc:
                logger.error("[GOOGLE AUTH] Google tokeninfo request failed: %s", http_exc)

    final_email = (verified_email or email or "").strip().lower()
    final_name = (verified_name or display_name or "").strip()
    final_avatar = verified_picture or avatar_url

    if not final_email or "@" not in final_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or missing Google authentication credentials.",
        )

    if not final_name:
        final_name = final_email.split("@")[0].capitalize()

    # Look up user in MongoDB
    user_doc = await db["users"].find_one({"email": final_email})
    if user_doc:
        doc_data = dict(user_doc)
        doc_data.pop("_id", None)
        user = User.model_validate(doc_data)

        # Update avatar if new one available
        if final_avatar and not user.avatar_url:
            user.avatar_url = final_avatar
            await db["users"].update_one(
                {"user_id": user.user_id},
                {"$set": {"avatar_url": final_avatar, "updated_at": utcnow()}},
            )

        # Ensure user has a valid workspace
        workspace_id = user.settings.default_workspace_id
        if not workspace_id:
            ws_doc = await db["workspaces"].find_one(
                {"members.user_id": user.user_id, "is_deleted": False}
            )
            if ws_doc:
                workspace_id = ws_doc["workspace_id"]
            else:
                ws = Workspace.create(
                    name=f"{user.display_name}'s Vault",
                    owner_id=user.user_id,
                    description="Personal memory space for documents, notes, and research.",
                )
                await db["workspaces"].insert_one(ws.model_dump())
                workspace_id = ws.workspace_id
                await db["users"].update_one(
                    {"user_id": user.user_id},
                    {"$set": {"settings.default_workspace_id": workspace_id}},
                )

        token = create_access_token(
            {"sub": user.user_id, "email": user.email, "display_name": user.display_name}
        )
        return user, workspace_id, token

    # New user: Provision account and personal workspace
    user = User(
        email=final_email,
        display_name=final_name,
        avatar_url=final_avatar,
        hashed_password=None,  # OAuth users don't require plaintext password
    )
    workspace = Workspace.create(
        name=f"{user.display_name}'s Vault",
        owner_id=user.user_id,
        description="Personal memory space for documents, notes, and research.",
    )
    user.settings.default_workspace_id = workspace.workspace_id

    # Persist in MongoDB
    await db["workspaces"].insert_one(workspace.model_dump())
    await db["users"].insert_one(user.model_dump())

    logger.info(
        "[GOOGLE AUTH] Registered new Google user %s (%s) with workspace %s",
        user.user_id,
        user.email,
        workspace.workspace_id,
    )

    token = create_access_token(
        {"sub": user.user_id, "email": user.email, "display_name": user.display_name}
    )
    return user, workspace.workspace_id, token

