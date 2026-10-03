"""Pytest test suite for upload service and template handling."""

from __future__ import annotations

import io
from pathlib import Path
import pytest
from werkzeug.datastructures import FileStorage

from services.exceptions import InvalidFileError
from services.upload_service import (
    get_extension,
    is_allowed_template,
    list_docx_templates,
    list_uploaded_templates,
    resolve_uploaded_template,
    save_resume_upload,
    save_template_upload,
)


def test_get_extension() -> None:
    """Test get_extension helper function."""
    assert get_extension("resume.DOCX") == "docx"
    assert get_extension("document.pdf") == "pdf"
    assert get_extension("file.txt") == "txt"


def test_is_allowed_template() -> None:
    """Test extension validation for allowed template types."""
    assert is_allowed_template("my_template.docx") is True
    assert is_allowed_template("my_template.pdf") is True
    assert is_allowed_template("my_template.txt") is False
    assert is_allowed_template("executable.exe") is False


def test_save_template_upload_valid_docx(tmp_test_dir: Path) -> None:
    """Test saving a valid template upload."""
    upload_folder = tmp_test_dir / "templates"
    file_storage = FileStorage(
        stream=io.BytesIO(b"dummy docx content"),
        filename="custom_template.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    result = save_template_upload(file_storage, upload_folder)

    assert result.original_filename == "custom_template.docx"
    assert result.extension == "docx"
    assert result.path.exists()
    assert "DOCX template" in result.file_type


def test_save_resume_upload_valid_pdf(tmp_test_dir: Path) -> None:
    """Test saving a valid resume PDF upload."""
    upload_folder = tmp_test_dir / "resumes"
    file_storage = FileStorage(
        stream=io.BytesIO(b"dummy pdf content"),
        filename="my_resume.pdf",
        content_type="application/pdf",
    )

    result = save_resume_upload(file_storage, upload_folder)

    assert result.original_filename == "my_resume.pdf"
    assert result.extension == "pdf"
    assert result.path.exists()
    assert result.file_type == "PDF Resume"


def test_save_upload_disallowed_extension(tmp_test_dir: Path) -> None:
    """Test that uploading a file with disallowed extension raises InvalidFileError."""
    upload_folder = tmp_test_dir / "uploads"
    file_storage = FileStorage(
        stream=io.BytesIO(b"plain text"),
        filename="notes.txt",
        content_type="text/plain",
    )

    with pytest.raises(InvalidFileError) as exc_info:
        save_template_upload(file_storage, upload_folder)

    assert "Only DOCX and PDF files are allowed." in exc_info.value.user_message


def test_list_and_resolve_templates(tmp_test_dir: Path) -> None:
    """Test listing uploaded DOCX templates and resolving safe path."""
    upload_folder = tmp_test_dir / "templates"
    
    file_docx = FileStorage(
        stream=io.BytesIO(b"content"),
        filename="template_a.docx",
    )
    saved_docx = save_template_upload(file_docx, upload_folder)

    file_pdf = FileStorage(
        stream=io.BytesIO(b"content"),
        filename="template_b.pdf",
    )
    save_template_upload(file_pdf, upload_folder)

    all_templates = list_uploaded_templates(upload_folder)
    assert len(all_templates) == 2

    docx_templates = list_docx_templates(upload_folder)
    assert len(docx_templates) == 1
    assert docx_templates[0].extension == "docx"

    resolved = resolve_uploaded_template(upload_folder, saved_docx.stored_filename)
    assert resolved.exists()
    assert resolved.name == saved_docx.stored_filename
