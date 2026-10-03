"""Pytest test suite for grammar checking and proofreading service."""

from __future__ import annotations

from unittest.mock import patch
import pytest

from services.proofreader import (
    ProofreaderError,
    _proofread_heuristics,
    _validate_proofreader_schema,
    proofread_resume,
)


def test_proofread_resume_heuristic_fallback(sample_resume_text: str) -> None:
    """Test local heuristic proofreader fallback when API key is empty."""
    result = proofread_resume(
        resume_text=sample_resume_text,
        api_key="",
        model="gpt-4o-mini",
    )

    assert isinstance(result, dict)
    assert result["analysis_type"] == "Local Diagnostics"
    assert "mistakes" in result
    assert isinstance(result["mistakes"], list)


@patch("services.proofreader.execute_json_chat_completion")
def test_proofread_resume_ai(mock_execute: patch, sample_resume_text: str) -> None:
    """Test AI-driven proofreading analysis."""
    mock_execute.return_value = {
        "mistakes": [
            {
                "original": "I worked on teh project.",
                "correction": "I worked on the project.",
                "reason": "Spelling typo.",
                "mistake_word": "teh",
            }
        ]
    }

    result = proofread_resume(
        resume_text=sample_resume_text,
        api_key="sk-fake-key",
        model="gpt-4o-mini",
    )

    assert result["analysis_type"] == "AI Assessment"
    assert "mistakes" in result
    assert len(result["mistakes"]) == 1
    assert result["mistakes"][0]["mistake_word"] == "teh"


def test_validate_proofreader_schema() -> None:
    """Test schema validation and list coercion."""
    raw = {
        "mistakes": [
            {
                "original": "Original sentence",
                "correction": "Corrected sentence",
                "reason": "Grammar rule",
                "mistake_word": "mistake",
            }
        ]
    }

    validated = _validate_proofreader_schema(raw)
    assert isinstance(validated["mistakes"], list)
    assert len(validated["mistakes"]) == 1


def test_proofread_resume_empty_text() -> None:
    """Test error handling when text is empty."""
    with pytest.raises(ProofreaderError) as exc_info:
        proofread_resume(
            resume_text="   ",
            api_key="sk-fake-key",
            model="gpt-4o-mini",
        )

    assert "empty" in str(exc_info.value).lower()
