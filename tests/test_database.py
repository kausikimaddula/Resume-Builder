"""Pytest test suite for MongoDB database operations, resumes, and versioning."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.database import (
    create_user,
    get_all_resumes_db,
    get_resume_db,
    get_user_by_email,
    init_all_tables,
    save_resume_db,
    update_user_password,
    verify_user,
)
from services.version_service import (
    calculate_changes_summary,
    compare_versions,
    create_resume_version,
    format_details_to_text,
    get_all_versions,
    get_latest_version_for_resume,
    get_next_version_number,
    get_version,
    get_versions_for_resume,
    init_db,
)


def test_init_db(tmp_test_dir: Path) -> None:
    """Test MongoDB initialization."""
    init_db()
    init_all_tables()


def test_user_authentication_mongo() -> None:
    """Test user registration and verification in MongoDB."""
    user = create_user("Test User", "mongo_user@example.com", "SecurePass123!")
    assert user is not None
    assert user["email"] == "mongo_user@example.com"
    assert user["full_name"] == "Test User"

    fetched = get_user_by_email("mongo_user@example.com")
    assert fetched is not None
    assert fetched["email"] == "mongo_user@example.com"

    verified = verify_user("mongo_user@example.com", "SecurePass123!")
    assert verified is not None
    assert verified["email"] == "mongo_user@example.com"

    bad_verified = verify_user("mongo_user@example.com", "WrongPassword")
    assert bad_verified is None

    # Test update_user_password
    reset_ok = update_user_password("mongo_user@example.com", "NewBrandPass456!")
    assert reset_ok is True

    new_verified = verify_user("mongo_user@example.com", "NewBrandPass456!")
    assert new_verified is not None
    assert new_verified["email"] == "mongo_user@example.com"

    old_verified = verify_user("mongo_user@example.com", "SecurePass123!")
    assert old_verified is None


def test_save_and_get_resume_mongo(sample_resume_data: dict[str, Any]) -> None:
    """Test saving and retrieving structured resumes in MongoDB."""
    saved = save_resume_db(sample_resume_data, user_email="mongo_user@example.com")
    assert saved is not None
    assert "id" in saved
    assert saved["personal"]["full_name"] == "Jane Smith"

    resume_id = saved["id"]
    fetched = get_resume_db(resume_id)
    assert fetched is not None
    assert fetched["id"] == resume_id
    assert fetched["personal"]["email"] == "jane.smith@example.com"

    all_resumes = get_all_resumes_db(user_email="mongo_user@example.com")
    assert len(all_resumes) >= 1
    assert any(r["id"] == resume_id for r in all_resumes)


def test_create_and_get_resume_version(tmp_test_dir: Path, sample_resume_data: dict[str, Any]) -> None:
    """Test creating a resume version in MongoDB and retrieving it."""
    v1 = create_resume_version(
        db_path=None,
        resume_id=101,
        resume_details=sample_resume_data,
        filename="resume_v1.docx",
        file_path=tmp_test_dir / "resume_v1.docx",
        template_filename="modern.docx",
        extracted_text="Jane Smith Software Engineer",
    )

    assert v1 is not None
    assert v1["resume_id"] == 101
    assert v1["version_number"] == 1
    assert v1["version_name"] == "Version 1"
    assert v1["filename"] == "resume_v1.docx"

    fetched = get_version(None, v1["id"])
    assert fetched is not None
    assert fetched["id"] == v1["id"]

    latest = get_latest_version_for_resume(None, 101)
    assert latest is not None
    assert latest["id"] == v1["id"]


def test_multiple_versions_and_diffing(tmp_test_dir: Path, sample_resume_data: dict[str, Any]) -> None:
    """Test creating multiple versions and comparing diffs side-by-side in MongoDB."""
    v1 = create_resume_version(
        db_path=None,
        resume_id=202,
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
        db_path=None,
        resume_id=202,
        resume_details=data_v2,
        filename="v2.docx",
        file_path="v2.docx",
        template_filename="template2.docx",
        extracted_text="Name: Jane Smith\nSkills: Python, Flask, Docker, Kubernetes, AWS",
    )

    assert v2["version_number"] == 2
    assert "Changed template" in v2["changes"]

    all_user_versions = get_versions_for_resume(None, 202)
    assert len(all_user_versions) == 2

    all_versions = get_all_versions(None)
    assert len(all_versions) >= 2

    diff_result = compare_versions(None, v1["id"], v2["id"])
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
