"""Pytest test suite for Job Description matching service."""

from __future__ import annotations

from unittest.mock import patch
import pytest

from services.jd_matcher import (
    JdMatcherError,
    _match_resume_to_jd_heuristics,
    _validate_matcher_schema,
    match_resume_to_jd,
)


def test_match_resume_to_jd_heuristic_fallback(sample_resume_text: str, sample_jd_text: str) -> None:
    """Test local heuristic job description matching when API key is empty."""
    result = match_resume_to_jd(
        resume_text=sample_resume_text,
        jd_text=sample_jd_text,
        api_key="",
        model="gpt-4o-mini",
    )

    assert isinstance(result, dict)
    assert result["analysis_type"] == "Local Diagnostics"
    assert "match_percentage" in result
    assert 0 <= result["match_percentage"] <= 100
    assert isinstance(result["matching_skills"], list)
    assert isinstance(result["missing_technical_skills"], list)


@patch("services.jd_matcher.execute_json_chat_completion")
def test_match_resume_to_jd_ai(mock_execute: patch, sample_resume_text: str, sample_jd_text: str) -> None:
    """Test AI-driven job description matching."""
    mock_execute.return_value = {
        "match_percentage": 92,
        "matching_skills": ["Python", "Flask", "Docker", "AWS"],
        "missing_technical_skills": ["Kubernetes"],
        "missing_soft_skills": ["Agile"],
        "recommended_keywords": ["CI/CD"],
        "recommended_certifications": ["AWS Developer"],
        "recommended_projects": ["Microservice architecture"],
        "learning_roadmap": ["Learn Kubernetes fundamentals"],
    }

    result = match_resume_to_jd(
        resume_text=sample_resume_text,
        jd_text=sample_jd_text,
        api_key="sk-fake-key",
        model="gpt-4o-mini",
    )

    assert result["analysis_type"] == "AI Assessment"
    assert result["match_percentage"] == 92
    assert "Kubernetes" in result["missing_technical_skills"]


def test_validate_matcher_schema() -> None:
    """Test schema validation and score clamping for JD match data."""
    raw = {
        "match_percentage": 105,  # Clamped to 100
        "matching_skills": ["Python"],
        "missing_technical_skills": ["Go"],
        "missing_soft_skills": [],
        "recommended_keywords": ["Backend"],
        "recommended_certifications": [],
        "recommended_projects": [],
        "learning_roadmap": "Study Go concurrency",  # Converted to list
    }

    validated = _validate_matcher_schema(raw)
    assert validated["match_percentage"] == 100
    assert isinstance(validated["learning_roadmap"], list)


def test_match_resume_to_jd_empty_resume(sample_jd_text: str) -> None:
    """Test error handling when resume text is empty."""
    with pytest.raises(JdMatcherError) as exc_info:
        match_resume_to_jd(
            resume_text="",
            jd_text=sample_jd_text,
            api_key="sk-fake-key",
            model="gpt-4o-mini",
        )

    assert "empty" in str(exc_info.value).lower()


def test_match_resume_to_jd_empty_jd(sample_resume_text: str) -> None:
    """Test error handling when job description text is empty."""
    with pytest.raises(JdMatcherError) as exc_info:
        match_resume_to_jd(
            resume_text=sample_resume_text,
            jd_text="   ",
            api_key="sk-fake-key",
            model="gpt-4o-mini",
        )

    assert "empty" in str(exc_info.value).lower()
