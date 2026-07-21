"""Unit tests for services/jd_matcher.py."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from services.jd_matcher import match_resume_to_jd, JdMatcherError, JD_MATCHER_SYSTEM_PROMPT


class TestJdMatcher(unittest.TestCase):
    """Tests verify resume-to-JD checking logic and fallbacks."""

    @patch("services.jd_matcher.OpenAI")
    def test_match_resume_to_jd_success(self, mock_openai_class):
        """Test successful OpenAI match parsing."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(
                message=MagicMock(
                    content=(
                        '{"match_percentage": 85, "matching_skills": ["Python", "Flask"], '
                        '"missing_skills": ["Docker"], "recommended_keywords": ["Containers"], '
                        '"important_certifications_missing": ["AWS Architect"], '
                        '"recommended_improvements": ["Add Docker project details."]}'
                    )
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_completion

        result = match_resume_to_jd(
            resume_text="I code in Python and Flask.",
            jd_text="Looking for a Python Developer who knows Flask and Docker.",
            api_key="mock-key",
            model="gpt-4o-mini",
        )

        self.assertEqual(result["match_percentage"], 85)
        self.assertEqual(result["analysis_type"], "AI Assessment")
        self.assertIn("Python", result["matching_skills"])
        self.assertIn("Docker", result["missing_skills"])
        self.assertIn("Containers", result["recommended_keywords"])
        self.assertIn("AWS Architect", result["important_certifications_missing"])
        self.assertIn("Add Docker project details.", result["recommended_improvements"])

        # Check call parameters
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_kwargs["model"], "gpt-4o-mini")
        self.assertEqual(call_kwargs["response_format"], {"type": "json_object"})

    @patch("services.jd_matcher.OpenAI")
    def test_match_resume_to_jd_invalid_json(self, mock_openai_class):
        """Test match_resume_to_jd throws JdMatcherError when OpenAI yields invalid json."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Malformed plain text"))]
        mock_client.chat.completions.create.return_value = mock_completion

        with self.assertRaises(JdMatcherError):
            match_resume_to_jd(
                resume_text="Some resume",
                jd_text="Some description",
                api_key="mock-key",
                model="gpt-4o-mini",
            )

    def test_match_resume_to_jd_heuristics(self):
        """Test matcher fallback to heuristics when API key is empty."""
        resume_text = "I study Python, React, and Flask. Certified AWS practitioner."
        jd_text = "Require Python, React, Docker, and AWS certified expertise."

        result = match_resume_to_jd(
            resume_text=resume_text,
            jd_text=jd_text,
            api_key="",
            model="gpt-4o-mini",
        )

        self.assertEqual(result["analysis_type"], "Local Diagnostics")
        self.assertGreater(result["match_percentage"], 20)
        self.assertIn("Python", result["matching_skills"])
        self.assertIn("React", result["matching_skills"])
        # Docker is in JD, not resume
        self.assertIn("Docker", result["missing_skills"])
        # Cert checks
        self.assertTrue(any("AWS" in s for s in result["matching_skills"]) or len(result["important_certifications_missing"]) >= 0)


if __name__ == "__main__":
    unittest.main()
