"""Pytest test suite for ATS score analysis service."""

from __future__ import annotations

from unittest.mock import patch
import pytest

from services.ats_checker import (
    AtsAnalysisError,
    _analyze_resume_heuristics,
    _validate_ats_schema,
    analyze_resume_ats,
)


def test_analyze_resume_ats_heuristic_fallback(sample_resume_text: str) -> None:
    """Test local heuristic ATS analysis when API key is empty."""
    result = analyze_resume_ats(
        resume_text=sample_resume_text,
        api_key="",
        model="gpt-4o-mini",
    )

    assert isinstance(result, dict)
    assert result["analysis_type"] == "Local Diagnostics"
    assert "score" in result
    assert 0 <= result["score"] <= 100
    assert isinstance(result["strengths"], list)
    assert isinstance(result["weaknesses"], list)
    assert isinstance(result["suggestions"], list)


@patch("services.ats_checker.execute_json_chat_completion")
def test_analyze_resume_ats_ai(mock_execute: patch, sample_resume_text: str) -> None:
    """Test OpenAI AI-driven ATS analysis."""
    mock_execute.return_value = {
        "score": 88,
        "strengths": ["Clear work history", "Strong tech stack"],
        "weaknesses": ["Lack of quantifiable metrics"],
        "suggestions": ["Add metrics like % improvement"],
    }

    result = analyze_resume_ats(
        resume_text=sample_resume_text,
        api_key="sk-fake-test-key",
        model="gpt-4o-mini",
    )

    assert result["analysis_type"] == "AI Assessment"
    assert result["score"] == 88
    assert len(result["strengths"]) == 2
    assert len(result["suggestions"]) == 1


def test_validate_ats_schema_coercion_and_clamping() -> None:
    """Test schema validation and score clamping between 0 and 100."""
    raw_data = {
        "score": "120",  # Should be clamped to 100
        "strengths": "Single string strength",  # Should be converted to list
        "weaknesses": ["Weakness 1"],
        "suggestions": [],
    }

    validated = _validate_ats_schema(raw_data)
    assert validated["score"] == 100
    assert isinstance(validated["strengths"], list)
    assert validated["strengths"] == ["Single string strength"]


def test_analyze_resume_ats_empty_text() -> None:
    """Test error handling when resume text is empty."""
    with pytest.raises(AtsAnalysisError) as exc_info:
        analyze_resume_ats(
            resume_text="",
            api_key="sk-fake-key",
            model="gpt-4o-mini",
        )

    assert "Resume text is empty" in str(exc_info.value)
