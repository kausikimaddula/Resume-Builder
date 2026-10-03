"""Pytest test suite for resume text parsing services."""

from __future__ import annotations

from pathlib import Path
import pytest

from services.exceptions import InvalidFileError
from services.resume_parser import (
    extract_resume_text,
    extract_text_from_docx,
    extract_text_from_pdf,
)


def test_extract_text_from_docx(sample_docx_file: Path) -> None:
    """Test text extraction from a valid DOCX file."""
    text = extract_text_from_docx(sample_docx_file)

    assert "Jane Smith" in text
    assert "Software Engineer" in text
    assert "Computer Engineering" in text


def test_extract_text_from_pdf(sample_pdf_file: Path) -> None:
    """Test text extraction from a valid PDF file."""
    text = extract_text_from_pdf(sample_pdf_file)

    assert "Jane Smith" in text
    assert "Python, Flask, SQL" in text


def test_extract_resume_text_docx(sample_docx_file: Path) -> None:
    """Test text extraction router for DOCX file format."""
    text = extract_resume_text(sample_docx_file)
    assert len(text) > 0
    assert "Jane Smith" in text


def test_extract_resume_text_pdf(sample_pdf_file: Path) -> None:
    """Test text extraction router for PDF file format."""
    text = extract_resume_text(sample_pdf_file)
    assert len(text) > 0
    assert "Jane Smith" in text


def test_extract_resume_text_nonexistent_file(tmp_test_dir: Path) -> None:
    """Test error handling when the file path does not exist."""
    missing_file = tmp_test_dir / "does_not_exist.docx"

    with pytest.raises(InvalidFileError) as exc_info:
        extract_resume_text(missing_file)

    assert "could not be found" in exc_info.value.user_message.lower()


def test_extract_resume_text_unsupported_format(tmp_test_dir: Path) -> None:
    """Test error handling for unsupported file extensions like .txt or .png."""
    txt_file = tmp_test_dir / "resume.txt"
    txt_file.write_text("Hello World", encoding="utf-8")

    with pytest.raises(InvalidFileError) as exc_info:
        extract_resume_text(txt_file)

    assert "unsupported file format" in exc_info.value.user_message.lower()


def test_extract_resume_text_corrupted_docx(tmp_test_dir: Path) -> None:
    """Test error handling when trying to parse corrupted DOCX binary data."""
    corrupted_file = tmp_test_dir / "bad_resume.docx"
    corrupted_file.write_bytes(b"Corrupted binary string data")

    with pytest.raises(InvalidFileError) as exc_info:
        extract_resume_text(corrupted_file)

    assert "corrupted" in exc_info.value.user_message.lower()
