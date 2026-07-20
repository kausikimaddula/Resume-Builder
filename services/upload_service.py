"""Reusable helpers for validating and storing uploaded resume templates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


ALLOWED_TEMPLATE_EXTENSIONS = {"docx", "pdf"}


@dataclass(frozen=True)
class UploadedTemplate:
    """Details about a stored upload."""

    original_filename: str
    stored_filename: str
    extension: str
    file_type: str
    path: Path


def is_allowed_template(filename: str) -> bool:
    """Return True when the filename has a supported extension."""
    return get_extension(filename) in ALLOWED_TEMPLATE_EXTENSIONS


def get_extension(filename: str) -> str:
    """Get the lowercase file extension without the dot."""
    return Path(filename).suffix.lower().lstrip(".")


def save_template_upload(file: FileStorage, upload_folder: Path) -> UploadedTemplate:
    """Save an uploaded DOCX or PDF template inside the uploads folder."""
    original_filename = file.filename or ""

    if not is_allowed_template(original_filename):
        raise ValueError("Only DOCX and PDF files are allowed.")

    extension = get_extension(original_filename)
    safe_name = secure_filename(original_filename)
    stored_filename = f"{Path(safe_name).stem}-{uuid4().hex[:8]}.{extension}"

    upload_folder.mkdir(parents=True, exist_ok=True)
    destination = upload_folder / stored_filename
    file.save(destination)

    return UploadedTemplate(
        original_filename=original_filename,
        stored_filename=stored_filename,
        extension=extension,
        file_type="DOCX template for editing" if extension == "docx" else "PDF for display only",
        path=destination,
    )


def save_resume_upload(file: FileStorage, upload_folder: Path) -> UploadedTemplate:
    """Save an uploaded DOCX or PDF resume inside the uploads folder."""
    original_filename = file.filename or ""

    if not is_allowed_template(original_filename):
        raise ValueError("Only DOCX and PDF files are allowed.")

    extension = get_extension(original_filename)
    safe_name = secure_filename(original_filename)
    stored_filename = f"{Path(safe_name).stem}-{uuid4().hex[:8]}.{extension}"

    upload_folder.mkdir(parents=True, exist_ok=True)
    destination = upload_folder / stored_filename
    file.save(destination)

    return UploadedTemplate(
        original_filename=original_filename,
        stored_filename=stored_filename,
        extension=extension,
        file_type="DOCX Resume" if extension == "docx" else "PDF Resume",
        path=destination,
    )


def list_uploaded_templates(upload_folder: Path) -> list[UploadedTemplate]:
    """List uploaded DOCX and PDF files currently stored on disk."""
    if not upload_folder.exists():
        return []

    templates: list[UploadedTemplate] = []
    for path in sorted(upload_folder.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_file() or not is_allowed_template(path.name):
            continue

        extension = get_extension(path.name)
        templates.append(
            UploadedTemplate(
                original_filename=path.name,
                stored_filename=path.name,
                extension=extension,
                file_type="DOCX template for editing"
                if extension == "docx"
                else "PDF for display only",
                path=path,
            )
        )
    return templates


def list_docx_templates(upload_folder: Path) -> list[UploadedTemplate]:
    """List only DOCX templates because PDFs are display-only."""
    return [
        template
        for template in list_uploaded_templates(upload_folder)
        if template.extension == "docx"
    ]


def resolve_uploaded_template(upload_folder: Path, stored_filename: str) -> Path:
    """Resolve an uploaded template path while keeping access inside uploads."""
    safe_name = secure_filename(stored_filename)
    template_path = (upload_folder / safe_name).resolve()
    upload_root = upload_folder.resolve()

    if upload_root not in template_path.parents or not template_path.is_file():
        raise FileNotFoundError("Template file was not found.")

    if get_extension(template_path.name) != "docx":
        raise ValueError("Only DOCX templates can be used for generation.")

    return template_path
