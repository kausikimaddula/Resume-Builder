"""Resume storage backed by PostgreSQL / SQLite database with fallback."""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any

from services.database import get_all_resumes_db, get_resume_db, save_resume_db

logger = logging.getLogger(__name__)

# In-memory fallback
_resume_submissions: list[dict[str, Any]] = []


def save_resume(data: dict[str, Any], user_email: str | None = None) -> dict[str, Any]:
    """Save resume into database or fallback in-memory."""
    try:
        saved = save_resume_db(data, user_email=user_email)
        _resume_submissions.append(deepcopy(saved))
        return saved
    except Exception as exc:
        logger.warning("Database save failed, using memory fallback: %s", exc)
        record = deepcopy(data)
        record["id"] = len(_resume_submissions) + 1
        _resume_submissions.append(record)
        return deepcopy(record)


def get_all_resumes(user_email: str | None = None) -> list[dict[str, Any]]:
    """Return all resumes from database or fallback in-memory."""
    try:
        return get_all_resumes_db(user_email=user_email)
    except Exception as exc:
        logger.warning("Database fetch failed, using memory fallback: %s", exc)
        return deepcopy(_resume_submissions)


def get_resume(resume_id: int) -> dict[str, Any] | None:
    """Retrieve resume by ID from database or fallback in-memory."""
    try:
        res = get_resume_db(resume_id)
        if res:
            return res
    except Exception as exc:
        logger.warning("Database fetch resume %s failed: %s", resume_id, exc)

    for resume in _resume_submissions:
        if resume.get("id") == resume_id:
            return deepcopy(resume)
    return None
