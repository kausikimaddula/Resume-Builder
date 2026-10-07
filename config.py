"""Configuration settings loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# Load values from a local .env file when one exists.
load_dotenv()


BASE_DIR = Path(__file__).resolve().parent


IS_SERVERLESS = os.getenv("VERCEL") == "1" or "AWS_LAMBDA_FUNCTION_NAME" in os.environ
WRITABLE_DIR = Path("/tmp") if IS_SERVERLESS else BASE_DIR


class Config:
    """Base Flask configuration.

    Environment variables keep secrets and machine-specific settings out of code.
    """

    # SECRET_KEY protects browser sessions and form security features.
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-development")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    PORT = int(os.getenv("FLASK_PORT", "5000"))

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Google OAuth 2.0 Credentials
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

    # Uploaded resumes & templates
    UPLOAD_FOLDER = WRITABLE_DIR / "uploads"
    GENERATED_FOLDER = UPLOAD_FOLDER / "generated"
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # MongoDB Database Settings
    MONGO_URI = (os.getenv("MONGO_URI") or os.getenv("MONGODB_URI") or "mongodb://localhost:27017/").strip()
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ResumeDB").strip()
    DATABASE_PATH = WRITABLE_DIR / "resume_builder.db"
    DATABASE_URL = MONGO_URI

    LOG_FOLDER = WRITABLE_DIR / "logs"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
