"""Tests for Google OAuth 2.0 authentication endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from flask import session
from app import create_app
from config import Config, BASE_DIR


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"
    DATABASE_PATH = BASE_DIR / "test_google_auth.db"
    GOOGLE_CLIENT_ID = "fake-test-client-id"
    GOOGLE_CLIENT_SECRET = "fake-test-client-secret"


def test_google_login_missing_credentials():
    """Test google_login behavior when GOOGLE_CLIENT_ID is missing."""
    app = create_app(TestConfig)

    # 1. In production (DEBUG=False, TESTING=False) with no keys
    app.config["DEBUG"] = False
    app.config["TESTING"] = False

    with patch("routes.main.sync_google_credentials", return_value=("", "")):
        with app.test_client() as client:
            response = client.get("/login/google", follow_redirects=True)
            assert response.status_code == 200
            assert b"Google Authentication is not configured" in response.data

    # 2. In dev/testing mode (DEBUG=True) with no keys
    app.config["DEBUG"] = True
    with patch("routes.main.sync_google_credentials", return_value=("", "")):
        with app.test_client() as client:
            response = client.get("/login/google", follow_redirects=True)
            assert response.status_code == 200
            assert session.get("user_name") == "Google User (Demo)"
            assert b"Logged in via Demo Google Account" in response.data


def test_google_login_redirect():
    """Test that google_login calls authorize_redirect when credentials exist."""
    app = create_app(TestConfig)

    with app.test_client() as client:
        with patch("routes.main.oauth.google.authorize_redirect") as mock_authorize:
            mock_authorize.return_value = "Redirecting to Google"
            res = client.get("/login/google")
            assert mock_authorize.called
            assert res.data == b"Redirecting to Google"


def test_google_callback_success():
    """Test successful Google OAuth callback processing."""
    app = create_app(TestConfig)

    mock_token = {
        "access_token": "fake_access_token",
        "userinfo": {
            "email": "testuser@gmail.com",
            "name": "Test User",
            "picture": "https://example.com/photo.jpg",
        },
    }

    with app.test_client() as client:
        with patch("routes.main.oauth.google.authorize_access_token", return_value=mock_token):
            response = client.get("/login/google/callback", follow_redirects=True)
            assert response.status_code == 200
            assert session.get("user_name") == "Test User"
            assert session.get("user_email") == "testuser@gmail.com"
            assert session.get("user_picture") == "https://example.com/photo.jpg"
            assert b"Successfully logged in with Google" in response.data


def test_google_callback_error_handling():
    """Test Google callback handling when token exchange raises an exception."""
    app = create_app(TestConfig)

    with app.test_client() as client:
        with patch("routes.main.oauth.google.authorize_access_token", side_effect=Exception("OAuth Error")):
            response = client.get("/login/google/callback", follow_redirects=True)
            assert response.status_code == 200
            assert b"Google authentication failed" in response.data
