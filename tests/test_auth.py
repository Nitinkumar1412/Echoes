# -*- coding: utf-8 -*-
"""
Tests for Authentication:
- Bcrypt password hashing & verification
- JWT creation and claims decoding
- Registration, Login, Demo login, and /me routes
"""
from __future__ import annotations

from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing_and_verification():
    raw = "MySuperSecret123!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(raw, "") is False


def test_jwt_token_flow():
    payload = {"sub": "usr_test_123", "email": "test@echoes.ai"}
    token = create_access_token(payload, expires_delta=timedelta(minutes=5))
    assert isinstance(token, str)
    assert len(token) > 20

    decoded = decode_access_token(token)
    assert decoded["sub"] == "usr_test_123"
    assert decoded["email"] == "test@echoes.ai"
    assert "exp" in decoded


def test_jwt_expired_token():
    payload = {"sub": "usr_expired_123"}
    # Token expired 1 second ago
    token = create_access_token(payload, expires_delta=timedelta(seconds=-1))
    
    with pytest.raises(Exception) as excinfo:
        decode_access_token(token)
    assert "expired" in str(excinfo.value.detail).lower()


def test_auth_api_routes():
    """Integration test for register, login, me, and demo endpoints."""
    with TestClient(app) as client:
        # 1. Register with short password -> 400
        bad_reg = client.post(
            "/api/v1/auth/register",
            json={"email": "short@echoes.ai", "password": "123", "display_name": "Short"},
        )
        assert bad_reg.status_code in (400, 422)

        # 2. Register valid user
        import uuid
        test_email = f"user_{uuid.uuid4().hex[:8]}@echoes.ai"
        test_pass = "ComplexPass2026!"
        test_name = "Echoes Explorer"

        reg_res = client.post(
            "/api/v1/auth/register",
            json={"email": test_email, "password": test_pass, "display_name": test_name},
        )
        assert reg_res.status_code == 201
        data = reg_res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "workspace_id" in data
        assert data["user"]["email"] == test_email
        assert "hashed_password" not in data["user"]
        token = data["access_token"]

        # 3. Duplicate register -> 400
        dup_res = client.post(
            "/api/v1/auth/register",
            json={"email": test_email, "password": test_pass, "display_name": test_name},
        )
        assert dup_res.status_code == 400

        # 4. Login with wrong password -> 401
        wrong_login = client.post(
            "/api/v1/auth/login",
            json={"email": test_email, "password": "wrongpassword"},
        )
        assert wrong_login.status_code == 401

        # 5. Login with correct password -> 200
        good_login = client.post(
            "/api/v1/auth/login",
            json={"email": test_email, "password": test_pass},
        )
        assert good_login.status_code == 200
        login_data = good_login.json()
        assert "access_token" in login_data
        assert login_data["user"]["email"] == test_email

        # 6. /me without auth -> 401
        unauth_me = client.get("/api/v1/auth/me")
        assert unauth_me.status_code == 401

        # 7. /me with valid Bearer token -> 200
        auth_me = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert auth_me.status_code == 200
        me_data = auth_me.json()
        assert me_data["user"]["email"] == test_email
        assert len(me_data["workspaces"]) >= 1

        # 8. Demo login -> 200
        demo_res = client.post("/api/v1/auth/demo")
        assert demo_res.status_code == 200
        assert "access_token" in demo_res.json()


def test_google_auth_flow():
    """Verify Google OAuth register, login, and workspace creation."""
    import uuid
    google_email = f"google_user_{uuid.uuid4().hex[:6]}@gmail.com"
    google_name = "Dr. Google Researcher"
    avatar = "https://example.com/avatar.png"

    with TestClient(app) as client:
        # 1. Invalid empty request -> 400
        bad_resp = client.post("/api/v1/auth/google", json={})
        assert bad_resp.status_code == 400

        # 2. Register / login via Google OAuth
        resp = client.post(
            "/api/v1/auth/google",
            json={
                "email": google_email,
                "display_name": google_name,
                "avatar_url": avatar,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == google_email
        assert data["user"]["display_name"] == google_name
        assert data["user"]["avatar_url"] == avatar
        assert data["workspace_id"] is not None
        ws_id = data["workspace_id"]

        # 3. Repeat login with same Google account -> returns existing account
        repeat_resp = client.post(
            "/api/v1/auth/google",
            json={
                "email": google_email,
                "display_name": google_name,
            },
        )
        assert repeat_resp.status_code == 200
        repeat_data = repeat_resp.json()
        assert repeat_data["workspace_id"] == ws_id
        assert repeat_data["user"]["user_id"] == data["user"]["user_id"]

