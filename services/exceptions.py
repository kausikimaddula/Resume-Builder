"""Custom domain exception hierarchy for production-ready error handling."""

from __future__ import annotations

from typing import Any


class AppBaseException(Exception):
    """Base exception for application errors.

    Attributes:
        message: Internal technical details intended for developer logs.
        user_message: Clear, friendly text safe for user display in UI/flash messages.
        status_code: HTTP status code representing the error (default 400 or 500).
        details: Additional contextual dictionary for diagnostics.
    """

    def __init__(
        self,
        message: str,
        user_message: str | None = None,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.user_message = user_message or "An unexpected error occurred. Please try again."
        self.status_code = status_code
        self.details = details or {}


class MissingApiKeyError(AppBaseException):
    """Raised when an API key (e.g. OpenAI) is missing or empty."""

    def __init__(
        self,
        message: str = "API key is missing.",
        user_message: str = "OpenAI API key is missing. Please configure your API key to use AI features.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            user_message=user_message,
            status_code=401,
            details=details,
        )


class InvalidFileError(AppBaseException):
    """Raised when an uploaded file format is invalid, empty, or unparseable."""

    def __init__(
        self,
        message: str = "Invalid file format or corrupted file.",
        user_message: str = "The uploaded file is invalid or corrupted. Please upload a valid DOCX or PDF file.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            user_message=user_message,
            status_code=400,
            details=details,
        )


class UploadError(AppBaseException):
    """Raised when file storage or upload processing fails."""

    def __init__(
        self,
        message: str = "File upload failed.",
        user_message: str = "Failed to upload file. Please check file permissions and try again.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            user_message=user_message,
            status_code=500,
            details=details,
        )


class OpenAiApiError(AppBaseException):
    """Base exception for general OpenAI service failures."""

    def __init__(
        self,
        message: str = "OpenAI API request failed.",
        user_message: str = "AI service is currently unavailable. Please try again later.",
        status_code: int = 502,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            user_message=user_message,
            status_code=status_code,
            details=details,
        )


class OpenAiTimeoutError(OpenAiApiError):
    """Raised when OpenAI API request times out."""

    def __init__(
        self,
        message: str = "OpenAI API request timed out.",
        user_message: str = "The request to the AI service timed out. Please try again.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            user_message=user_message,
            status_code=504,
            details=details,
        )


class OpenAiRateLimitError(OpenAiApiError):
    """Raised when OpenAI API rate limit or quota is exceeded."""

    def __init__(
        self,
        message: str = "OpenAI API rate limit or quota exceeded.",
        user_message: str = "AI service rate limit exceeded. Please wait a moment and try again.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            user_message=user_message,
            status_code=429,
            details=details,
        )


class DatabaseError(AppBaseException):
    """Raised when a database query or connection failure occurs."""

    def __init__(
        self,
        message: str = "Database operation failed.",
        user_message: str = "A database error occurred. Your changes could not be saved. Please try again.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            user_message=user_message,
            status_code=500,
            details=details,
        )
