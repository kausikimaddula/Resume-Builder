"""Unit and integration tests for application error handling and domain exceptions."""

from __future__ import annotations

import io
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from openai import APITimeoutError, AuthenticationError, RateLimitError

from app import create_app
from config import Config
from services.exceptions import (
    AppBaseException,
    DatabaseError,
    InvalidFileError,
    MissingApiKeyError,
    OpenAiApiError,
    OpenAiRateLimitError,
    OpenAiTimeoutError,
    UploadError,
)
from services.openai_service import create_client, execute_json_chat_completion
from services.resume_parser import extract_resume_text
from services.upload_service import save_resume_upload, save_template_upload
from services.version_service import get_versions_for_resume


class TestConfig(Config):
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False


class TestErrorHandling(unittest.TestCase):
    """Test suite for error handling across OpenAI API, uploads, database, and unexpected exceptions."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        class CustomTestConfig(TestConfig):
            UPLOAD_FOLDER = Path(self.temp_dir.name) / "uploads"
            GENERATED_FOLDER = Path(self.temp_dir.name) / "generated"
            DATABASE_PATH = Path(self.temp_dir.name) / "test.db"
            LOG_FOLDER = Path(self.temp_dir.name) / "logs"

        self.app = create_app(CustomTestConfig)
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        # Close all logging handlers to release file handles on Windows
        for h in list(self.app.logger.handlers):
            h.close()
            self.app.logger.removeHandler(h)
        root_logger = logging.getLogger()
        for h in list(root_logger.handlers):
            h.close()
            root_logger.removeHandler(h)
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    # 1. Missing API Keys
    def test_missing_api_key_raises_exception(self) -> None:
        """Verify MissingApiKeyError is raised when key is empty."""
        with self.assertRaises(MissingApiKeyError) as ctx:
            create_client("")
        self.assertIn("missing", ctx.exception.user_message.lower())

    def test_authentication_error_mapped_to_missing_api_key(self) -> None:
        """Verify openai.AuthenticationError maps to MissingApiKeyError."""
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.side_effect = AuthenticationError(
            message="Invalid API Key", response=MagicMock(status_code=401), body=None
        )

        with self.assertRaises(MissingApiKeyError) as ctx:
            execute_json_chat_completion(
                system_prompt="sys",
                user_prompt="user",
                api_key="invalid-key",
                model="gpt-4o-mini",
                client=mock_openai_client,
            )
        self.assertIn("invalid or unauthorized", ctx.exception.user_message.lower())

    # 2. Upload Failures & Invalid Files
    def test_upload_invalid_file_extension(self) -> None:
        """Verify uploading an invalid file format raises InvalidFileError."""
        data = {"template_file": (io.BytesIO(b"dummy data"), "resume.txt")}
        response = self.client.post(
            "/templates/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Only DOCX and PDF files are allowed.", response.data)

    def test_extract_text_from_nonexistent_file(self) -> None:
        """Verify extract_resume_text raises InvalidFileError when file does not exist."""
        non_existent = self.temp_path / "missing.docx"
        with self.assertRaises(InvalidFileError) as ctx:
            extract_resume_text(non_existent)
        self.assertIn("could not be found", ctx.exception.user_message.lower())

    def test_extract_text_from_corrupted_docx(self) -> None:
        """Verify extract_resume_text raises InvalidFileError for corrupted DOCX."""
        corrupted_path = self.temp_path / "corrupted.docx"
        corrupted_path.write_bytes(b"Not a valid zip docx file")

        with self.assertRaises(InvalidFileError) as ctx:
            extract_resume_text(corrupted_path)
        self.assertIn("corrupted", ctx.exception.user_message.lower())

    # 3. OpenAI Timeouts & Rate Limits
    def test_openai_timeout_handling(self) -> None:
        """Verify APITimeoutError maps to OpenAiTimeoutError."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = APITimeoutError(request=MagicMock())

        with self.assertRaises(OpenAiTimeoutError) as ctx:
            execute_json_chat_completion(
                system_prompt="sys",
                user_prompt="user",
                api_key="valid-key",
                model="gpt-4o-mini",
                client=mock_client,
            )
        self.assertIn("timed out", ctx.exception.user_message.lower())

    def test_openai_rate_limit_handling(self) -> None:
        """Verify RateLimitError maps to OpenAiRateLimitError."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RateLimitError(
            message="Rate limit reached", response=MagicMock(status_code=429), body=None
        )

        with self.assertRaises(OpenAiRateLimitError) as ctx:
            execute_json_chat_completion(
                system_prompt="sys",
                user_prompt="user",
                api_key="valid-key",
                model="gpt-4o-mini",
                client=mock_client,
            )
        self.assertIn("rate limit exceeded", ctx.exception.user_message.lower())

    # 4. Database Errors
    @patch("services.version_service.get_db_connection")
    def test_database_error_handling(self, mock_get_db) -> None:
        """Verify DatabaseError is raised and caught cleanly on SQLite failures."""
        import sqlite3
        mock_get_db.side_effect = sqlite3.Error("Disk I/O failure")

        with self.assertRaises(DatabaseError) as ctx:
            get_versions_for_resume(self.app.config["DATABASE_PATH"], resume_id=1)
        self.assertTrue(
            "database" in ctx.exception.user_message.lower()
            or "failed" in ctx.exception.user_message.lower()
        )

    # 5. Unexpected Exceptions User-Friendly Handling
    def test_unexpected_exception_returns_friendly_error_page(self) -> None:
        """Verify unhandled exception renders 500 error page with user-friendly text."""
        @self.app.route("/test-crash")
        def crash_route():
            raise RuntimeError("Catastrophic unexpected failure!")

        response = self.client.get("/test-crash")
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Something went wrong on our end", response.data)
        self.assertNotIn(b"Catastrophic unexpected failure!", response.data)


if __name__ == "__main__":
    unittest.main()
