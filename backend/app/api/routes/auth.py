# -*- coding: utf-8 -*-
"""
Authentication API routes — user registration, login, and profile inspection.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from backend.app.models.user import User
from backend.app.services.auth import (
    authenticate_user,
    get_current_user,
    google_authenticate_or_register,
    register_user,
)
from backend.app.services.database import get_async_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str = Field(..., json_schema_extra={"example": "researcher@echoes.ai"})
    password: str = Field(..., min_length=6, json_schema_extra={"example": "SecurePassword123!"})
    display_name: str = Field(..., min_length=1, json_schema_extra={"example": "Dr. Jane Doe"})


class LoginRequest(BaseModel):
    email: str = Field(..., json_schema_extra={"example": "researcher@echoes.ai"})
    password: str = Field(..., min_length=1, json_schema_extra={"example": "SecurePassword123!"})


class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = Field(None, description="Google ID Token from Google Identity Services")
    email: Optional[str] = Field(None, description="Direct email for OAuth callback/fallback")
    display_name: Optional[str] = Field(None, description="Display name for the user")
    avatar_url: Optional[str] = Field(None, description="User avatar image URL")


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    workspace_id: str
    user: dict


class UserProfileResponse(BaseModel):
    user: dict
    workspace_id: Optional[str] = None
    workspaces: list[dict] = Field(default_factory=list)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Registers a new user, hashes their password, and creates their initial personal workspace.",
)
async def register_endpoint(
    req: RegisterRequest,
    db: AsyncIOMotorDatabase = Depends(get_async_db),
):
    try:
        user, workspace, token = await register_user(
            db=db,
            email=req.email,
            password=req.password,
            display_name=req.display_name,
        )
        return AuthResponse(
            access_token=token,
            token_type="bearer",
            workspace_id=workspace.workspace_id,
            user=user.to_safe_dict(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[AUTH] Registration failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(exc)}",
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Authenticate user and obtain JWT token",
    description="Validates email and password, returning a signed JWT access token.",
)
async def login_endpoint(
    req: LoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_async_db),
):
    user, token = await authenticate_user(
        db=db,
        email=req.email,
        password=req.password,
    )
    workspace_id = user.settings.default_workspace_id or "default-workspace"
    
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        workspace_id=workspace_id,
        user=user.to_safe_dict(),
    )


@router.post(
    "/google",
    response_model=AuthResponse,
    summary="Authenticate or register via Google OAuth",
    description="Validates Google credential/ID token, signs in or auto-registers the user and creates their personal workspace in MongoDB.",
)
async def google_auth_endpoint(
    req: GoogleAuthRequest,
    db: AsyncIOMotorDatabase = Depends(get_async_db),
):
    try:
        user, workspace_id, token = await google_authenticate_or_register(
            db=db,
            credential=req.credential,
            email=req.email,
            display_name=req.display_name,
            avatar_url=req.avatar_url,
        )
        return AuthResponse(
            access_token=token,
            token_type="bearer",
            workspace_id=workspace_id,
            user=user.to_safe_dict(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[AUTH] Google authentication failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google authentication failed: {str(exc)}",
        )


@router.post(
    "/demo",
    response_model=AuthResponse,
    summary="One-click demo login",
    description="Logs in with or auto-registers the default demo account for instant testing.",
)
async def demo_login_endpoint(
    db: AsyncIOMotorDatabase = Depends(get_async_db),
):
    demo_email = "demo@echoes.ai"
    demo_password = "demo_echoes_pass_2026"
    demo_name = "Alex Mercer"
    
    # Try logging in first
    try:
        user, token = await authenticate_user(db=db, email=demo_email, password=demo_password)
        workspace_id = user.settings.default_workspace_id or "default-workspace"
        return AuthResponse(
            access_token=token,
            token_type="bearer",
            workspace_id=workspace_id,
            user=user.to_safe_dict(),
        )
    except HTTPException:
        # If demo user doesn't exist, register them
        user, workspace, token = await register_user(
            db=db,
            email=demo_email,
            password=demo_password,
            display_name=demo_name,
        )
        return AuthResponse(
            access_token=token,
            token_type="bearer",
            workspace_id=workspace.workspace_id,
            user=user.to_safe_dict(),
        )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
    description="Inspects the authenticated user's session and retrieves their active workspaces.",
)
async def me_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_async_db),
):
    # Fetch user's workspaces
    cursor = db["workspaces"].find({"members.user_id": current_user.user_id, "is_deleted": False})
    workspaces = []
    async for ws in cursor:
        ws_copy = dict(ws)
        ws_copy.pop("_id", None)
        workspaces.append(ws_copy)
    
    workspace_id = current_user.settings.default_workspace_id
    if not workspace_id and workspaces:
        workspace_id = workspaces[0].get("workspace_id")
    
    return UserProfileResponse(
        user=current_user.to_safe_dict(),
        workspace_id=workspace_id,
        workspaces=workspaces,
    )


@router.post(
    "/logout",
    summary="Log out user",
    description="Stateless token invalidation confirmation.",
)
async def logout_endpoint(
    current_user: User = Depends(get_current_user),
):
    return {"message": "Logged out successfully", "user_id": current_user.user_id}
