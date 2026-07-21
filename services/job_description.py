"""Service for parsing and extracting text from PDF, DOCX, and TXT job descriptions."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from services.resume_parser import extract_text_from_pdf, extract_text_from_docx

logger = logging.getLogger(__name__)

ALLOWED_JD_EXTENSIONS = {"docx", "pdf", "txt"}


@dataclass(frozen=True)
class UploadedJobDescription:
    """Details about a stored job description upload."""

    original_filename: str
    stored_filename: str
    extension: str
    file_type: str
    path: Path


def is_allowed_jd(filename: str) -> bool:
    """Return True when the filename has a supported job description extension."""
    return get_extension(filename) in ALLOWED_JD_EXTENSIONS


def get_extension(filename: str) -> str:
    """Get the lowercase file extension without the dot."""
    return Path(filename).suffix.lower().lstrip(".")


def extract_text_from_txt(file_path: Path) -> str:
    """Extract text from a plain TXT file."""
    logger.info("Extracting text from TXT: %s", file_path)
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except Exception as e:
        logger.exception("Failed to extract text from TXT file: %s", file_path)
        raise ValueError(f"Error reading TXT file: {str(e)}") from e


def extract_jd_text(file_path: Path) -> str:
    """Detect file type and extract text from the job description.

    Supported formats: PDF, DOCX, TXT.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Job Description file not found at: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix == ".docx":
        return extract_text_from_docx(file_path)
    elif suffix == ".txt":
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(
            f"Unsupported file type: {suffix}. Only PDF, DOCX, and TXT are allowed."
        )


def save_jd_upload(file: FileStorage, upload_folder: Path) -> UploadedJobDescription:
    """Save an uploaded Job Description inside the uploads folder."""
    original_filename = file.filename or ""

    if not is_allowed_jd(original_filename):
        raise ValueError("Only PDF, DOCX, and TXT files are allowed.")

    extension = get_extension(original_filename)
    safe_name = secure_filename(original_filename)
    # Handle files with non-ASCII or empty secured names
    if not safe_name or safe_name.startswith('.'):
        safe_name = "job_description"

    stored_filename = f"{Path(safe_name).stem}-{uuid4().hex[:8]}.{extension}"

    upload_folder.mkdir(parents=True, exist_ok=True)
    destination = upload_folder / stored_filename
    file.save(destination)

    # Determine file type string
    if extension == "docx":
        file_type = "DOCX Job Description"
    elif extension == "pdf":
        file_type = "PDF Job Description"
    else:
        file_type = "TXT Job Description"

    return UploadedJobDescription(
        original_filename=original_filename,
        stored_filename=stored_filename,
        extension=extension,
        file_type=file_type,
        path=destination,
    )
