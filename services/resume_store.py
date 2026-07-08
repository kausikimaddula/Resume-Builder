"""Temporary in-memory storage for submitted resume details."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


# This list is intentionally temporary. Data will reset when the Flask process
# restarts, which is fine until a database is introduced later.
_resume_submissions: list[dict[str, Any]] = []


def save_resume(data: dict[str, Any]) -> dict[str, Any]:
    """Save one resume submission and return the stored record."""
    record = deepcopy(data)
    record["id"] = len(_resume_submissions) + 1
    _resume_submissions.append(record)
    return deepcopy(record)


def get_all_resumes() -> list[dict[str, Any]]:
    """Return a copy of all submitted resume details."""
    return deepcopy(_resume_submissions)


def get_resume(resume_id: int) -> dict[str, Any] | None:
    """Find one submitted resume by its temporary in-memory ID."""
    for resume in _resume_submissions:
        if resume["id"] == resume_id:
            return deepcopy(resume)
    return None
