"""Configuration settings loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# Load values from a local .env file when one exists.
load_dotenv()


BASE_DIR = Path(__file__).resolve().parent


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

    # Uploaded resumes will live here in a future feature.
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    LOG_FOLDER = BASE_DIR / "logs"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
