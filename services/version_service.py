"""Service for managing resume versions in MongoDB database."""

from __future__ import annotations

import difflib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from services.ats_checker import analyze_resume_ats
from services.database import (
    create_resume_version_db,
    get_all_versions_db,
    get_latest_version_for_resume_db,
    get_next_version_number_db,
    get_version_db,
    get_versions_for_resume_db,
    init_all_tables,
)
from services.exceptions import DatabaseError
from services.jd_matcher import match_resume_to_jd

logger = logging.getLogger(__name__)


def init_db(db_path: Path | str | None = None) -> None:
    """Initialize database tables and indexes."""
    init_all_tables(db_path)


def get_next_version_number(db_path: Path | str | None, resume_id: int) -> int:
    """Get the next version number for a given resume_id."""
    return get_next_version_number_db(resume_id, db_path)


def get_latest_version_for_resume(db_path: Path | str | None, resume_id: int) -> dict[str, Any] | None:
    """Retrieve the latest version for a given resume_id."""
    return get_latest_version_for_resume_db(resume_id, db_path)


def format_details_to_text(resume_details: dict[str, Any]) -> str:
    """Convert structured resume details dictionary into readable text for ATS, diffing, and matching."""
    lines = []
    personal = resume_details.get("personal", {})
    if isinstance(personal, dict):
        if personal.get("full_name"):
            lines.append(f"Name: {personal['full_name']}")
        if personal.get("email"):
            lines.append(f"Email: {personal['email']}")
        if personal.get("phone"):
            lines.append(f"Phone: {personal['phone']}")
        if personal.get("linkedin"):
            lines.append(f"LinkedIn: {personal['linkedin']}")
        if personal.get("github"):
            lines.append(f"GitHub: {personal['github']}")
        if personal.get("portfolio"):
            lines.append(f"Portfolio: {personal['portfolio']}")
        if personal.get("address"):
            lines.append(f"Address: {personal['address']}")

    edu = resume_details.get("education", {})
    if isinstance(edu, dict) and any(edu.values()):
        lines.append("\nEDUCATION:")
        if edu.get("degree"):
            lines.append(f"Degree: {edu['degree']}")
        if edu.get("college"):
            lines.append(f"College: {edu['college']}")
        if edu.get("graduation_year"):
            lines.append(f"Graduation Year: {edu['graduation_year']}")
        if edu.get("gpa"):
            lines.append(f"GPA: {edu['gpa']}")

    exp = resume_details.get("experience", {})
    if isinstance(exp, dict) and any(exp.values()):
        lines.append("\nEXPERIENCE:")
        if exp.get("role"):
            lines.append(f"Role: {exp['role']}")
        if exp.get("company"):
            lines.append(f"Company: {exp['company']}")
        if exp.get("duration"):
            lines.append(f"Duration: {exp['duration']}")
        if exp.get("responsibilities"):
            lines.append(f"Responsibilities:\n{exp['responsibilities']}")

    proj = resume_details.get("projects", {})
    if isinstance(proj, dict) and any(proj.values()):
        lines.append("\nPROJECTS:")
        if proj.get("project_name"):
            lines.append(f"Project: {proj['project_name']}")
        if proj.get("description"):
            lines.append(f"Description: {proj['description']}")
        if proj.get("technologies"):
            lines.append(f"Technologies: {proj['technologies']}")

    if resume_details.get("skills"):
        lines.append(f"\nSKILLS:\n{resume_details['skills']}")
    if resume_details.get("certifications"):
        lines.append(f"\nCERTIFICATIONS:\n{resume_details['certifications']}")
    if resume_details.get("achievements"):
        lines.append(f"\nACHIEVEMENTS:\n{resume_details['achievements']}")
    if resume_details.get("languages"):
        lines.append(f"\nLANGUAGES:\n{resume_details['languages']}")

    return "\n".join(lines)


def calculate_changes_summary(
    previous_version: dict[str, Any] | None,
    new_details: dict[str, Any],
    new_template: str,
) -> str:
    """Calculate human-readable summary of changes compared to previous version."""
    if not previous_version:
        return f"Initial generation (Version 1) created using template '{new_template}'."

    changes_list = []
    prev_template = previous_version.get("template_filename") or ""
    if prev_template != new_template:
        changes_list.append(f"Changed template from '{prev_template}' to '{new_template}'.")

    prev_details = {}
    if previous_version.get("resume_details_json"):
        try:
            prev_details = json.loads(previous_version["resume_details_json"])
        except json.JSONDecodeError:
            pass

    for section in ["personal", "education", "experience", "projects"]:
        prev_sec = prev_details.get(section, {})
        new_sec = new_details.get(section, {})
        if isinstance(prev_sec, dict) and isinstance(new_sec, dict):
            all_keys = set(prev_sec.keys()) | set(new_sec.keys())
            for key in sorted(all_keys):
                if prev_sec.get(key) != new_sec.get(key):
                    changes_list.append(f"Updated {section.capitalize()} ({key}).")

    for field in ["skills", "certifications", "achievements", "languages"]:
        if prev_details.get(field) != new_details.get(field):
            changes_list.append(f"Updated {field.capitalize()}.")

    if not changes_list:
        return f"Regenerated version with template '{new_template}'."

    return " ".join(changes_list)


def create_resume_version(
    *,
    db_path: Path | str | None,
    resume_id: int,
    resume_details: dict[str, Any],
    filename: str,
    file_path: Path | str,
    template_filename: str,
    jd_text: str | None = None,
    api_key: str = "",
    model: str = "",
    extracted_text: str | None = None,
) -> dict[str, Any]:
    """Create and persist a new resume version in MongoDB."""
    init_db(db_path)
    version_number = get_next_version_number(db_path, resume_id)
    version_name = f"Version {version_number}"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    resume_text = extracted_text if extracted_text else format_details_to_text(resume_details)

    # 1. Compute ATS Score
    ats_score = None
    try:
        ats_res = analyze_resume_ats(
            resume_text=resume_text,
            api_key=api_key,
            model=model,
        )
        if isinstance(ats_res, dict) and "score" in ats_res:
            ats_score = int(ats_res["score"])
    except Exception as exc:
        logger.warning("ATS Analysis skipped or failed during version creation: %s", exc)
        ats_score = None

    # 2. Compute Match Score if JD text provided
    match_score = None
    if jd_text and jd_text.strip():
        try:
            match_res = match_resume_to_jd(
                resume_text=resume_text,
                jd_text=jd_text,
                api_key=api_key,
                model=model,
            )
            if isinstance(match_res, dict) and "match_percentage" in match_res:
                match_score = int(match_res["match_percentage"])
        except Exception as exc:
            logger.warning("JD Matcher skipped or failed during version creation: %s", exc)
            match_score = None

    # 3. Calculate Changes
    latest_ver = get_latest_version_for_resume(db_path, resume_id)
    changes = calculate_changes_summary(latest_ver, resume_details, template_filename)
    details_json = json.dumps(resume_details)

    version_id = create_resume_version_db(
        resume_id=resume_id,
        version_number=version_number,
        version_name=version_name,
        created_at=created_at,
        filename=filename,
        file_path=str(file_path),
        ats_score=ats_score,
        match_score=match_score,
        changes=changes,
        resume_details_json=details_json,
        resume_text=resume_text,
        template_filename=template_filename,
        db_target=db_path,
    )

    return get_version(db_path, version_id)  # type: ignore


def get_version(db_path: Path | str | None, version_id: int) -> dict[str, Any] | None:
    """Retrieve one version by its database ID."""
    return get_version_db(version_id, db_path)


def get_versions_for_resume(db_path: Path | str | None, resume_id: int) -> list[dict[str, Any]]:
    """Retrieve all versions associated with a specific resume_id."""
    return get_versions_for_resume_db(resume_id, db_path)


def get_all_versions(db_path: Path | str | None) -> list[dict[str, Any]]:
    """Retrieve all versions across all resumes."""
    return get_all_versions_db(db_path)


def compare_versions(
    db_path: Path | str | None,
    version_a_id: int,
    version_b_id: int,
) -> dict[str, Any] | None:
    """Compare two versions and return side-by-side metadata and diff results."""
    version_a = get_version(db_path, version_a_id)
    version_b = get_version(db_path, version_b_id)

    if not version_a or not version_b:
        return None

    text_a = (version_a.get("resume_text") or "").splitlines()
    text_b = (version_b.get("resume_text") or "").splitlines()

    diff_lines = list(
        difflib.unified_diff(
            text_a,
            text_b,
            fromfile=f"{version_a['version_name']} ({version_a['created_at']})",
            tofile=f"{version_b['version_name']} ({version_b['created_at']})",
            lineterm="",
        )
    )

    ats_delta = None
    if version_a.get("ats_score") is not None and version_b.get("ats_score") is not None:
        ats_delta = version_b["ats_score"] - version_a["ats_score"]

    match_delta = None
    if version_a.get("match_score") is not None and version_b.get("match_score") is not None:
        match_delta = version_b["match_score"] - version_a["match_score"]

    return {
        "version_a": version_a,
        "version_b": version_b,
        "ats_delta": ats_delta,
        "match_delta": match_delta,
        "diff_lines": diff_lines,
    }
