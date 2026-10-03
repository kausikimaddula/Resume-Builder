"""Pytest test suite for SQLite database versioning models and operations."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
from unittest.mock import patch

pytest = __import__("pytest")

from services.exceptions import DatabaseError
from services.version_service import (
    calculate_changes_summary,
    compare_versions,
    create_resume_version,
    format_details_to_text,
    get_all_versions,
    get_db_connection,
    get_latest_version_for_resume,
    get_next_version_number,
    get_version,
    get_versions_for_resume,
    init_db,
)


def test_init_db(tmp_test_dir: Path) -> None:
    """Test SQLite database initialization and schema creation."""
    db_path = tmp_test_dir / "test_init.db"
    init_db(db_path)

    assert db_path.exists()

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='resume_versions';")
        row = cursor.fetchone()
        assert row is not None
        assert row["name"] == "resume_versions"


def test_create_and_get_resume_version(tmp_test_dir: Path, sample_resume_data: dict[str, Any]) -> None:
    """Test creating a resume version in database and retrieving it."""
    db_path = tmp_test_dir / "test_versioning.db"

    v1 = create_resume_version(
        db_path=db_path,
        resume_id=1,
        resume_details=sample_resume_data,
        filename="resume_v1.docx",
        file_path=tmp_test_dir / "resume_v1.docx",
        template_filename="modern.docx",
        extracted_text="Jane Smith Software Engineer",
    )

    assert v1 is not None
    assert v1["resume_id"] == 1
    assert v1["version_number"] == 1
    assert v1["version_name"] == "Version 1"
    assert v1["filename"] == "resume_v1.docx"

    fetched = get_version(db_path, v1["id"])
    assert fetched is not None
    assert fetched["id"] == v1["id"]

    latest = get_latest_version_for_resume(db_path, 1)
    assert latest is not None
    assert latest["id"] == v1["id"]


def test_multiple_versions_and_diffing(tmp_test_dir: Path, sample_resume_data: dict[str, Any]) -> None:
    """Test creating multiple versions and comparing diffs side-by-side."""
    db_path = tmp_test_dir / "test_diffing.db"

    v1 = create_resume_version(
        db_path=db_path,
        resume_id=10,
        resume_details=sample_resume_data,
        filename="v1.docx",
        file_path="v1.docx",
        template_filename="template1.docx",
        extracted_text="Name: Jane Smith\nSkills: Python, Flask",
    )

    # Modify data for v2
    data_v2 = dict(sample_resume_data)
    data_v2["skills"] = "Python, Flask, Docker, Kubernetes, AWS"

    v2 = create_resume_version(
        db_path=db_path,
        resume_id=10,
        resume_details=data_v2,
        filename="v2.docx",
        file_path="v2.docx",
        template_filename="template2.docx",
        extracted_text="Name: Jane Smith\nSkills: Python, Flask, Docker, Kubernetes, AWS",
    )

    assert v2["version_number"] == 2
    assert "Changed template" in v2["changes"]

    all_user_versions = get_versions_for_resume(db_path, 10)
    assert len(all_user_versions) == 2

    all_versions = get_all_versions(db_path)
    assert len(all_versions) >= 2

    diff_result = compare_versions(db_path, v1["id"], v2["id"])
    assert diff_result is not None
    assert "diff_lines" in diff_result
    assert len(diff_result["diff_lines"]) > 0


def test_format_details_to_text(sample_resume_data: dict[str, Any]) -> None:
    """Test converting structured resume data dictionary to text string."""
    text = format_details_to_text(sample_resume_data)
    assert "Name: Jane Smith" in text
    assert "EDUCATION:" in text
    assert "EXPERIENCE:" in text
    assert "SKILLS:" in text


@patch("services.version_service.get_db_connection")
def test_database_error_handling(mock_get_db: patch, tmp_test_dir: Path) -> None:
    """Test that SQLite database exceptions raise DatabaseError cleanly."""
    mock_get_db.side_effect = sqlite3.Error("Database locked or read-only")

    with pytest.raises(DatabaseError) as exc_info:
        get_all_versions(tmp_test_dir / "db.sqlite")

    assert "database" in exc_info.value.user_message.lower() or "failed" in exc_info.value.user_message.lower()
