"""Unit tests for services/jd_matcher.py with the improved schema."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from services.jd_matcher import match_resume_to_jd, JdMatcherError


class TestJdMatcher(unittest.TestCase):
    """Tests verify resume-to-JD checking logic and fallbacks with the updated metrics schema."""

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
                        '"missing_technical_skills": ["Docker", "Kubernetes"], '
                        '"missing_soft_skills": ["Leadership"], '
                        '"recommended_keywords": ["Containers", "Agile"], '
                        '"recommended_certifications": ["AWS Solutions Architect"], '
                        '"recommended_projects": ["Create a cluster deployment."], '
                        '"learning_roadmap": ["Step 1: Containerize.", "Step 2: Orchestrate."]}'
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
        self.assertIn("Docker", result["missing_technical_skills"])
        self.assertIn("Leadership", result["missing_soft_skills"])
        self.assertIn("AWS Solutions Architect", result["recommended_certifications"])
        self.assertIn("Create a cluster deployment.", result["recommended_projects"])
        self.assertIn("Step 1: Containerize.", result["learning_roadmap"])

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
        jd_text = "Require Python, React, Docker, and AWS certified expertise. Need communication skills."

        result = match_resume_to_jd(
            resume_text=resume_text,
            jd_text=jd_text,
            api_key="",
            model="gpt-4o-mini",
        )

        self.assertEqual(result["analysis_type"], "Local Diagnostics")
        self.assertGreater(result["match_percentage"], 10)
        self.assertIn("Python", result["matching_skills"])
        # Docker is in JD, not resume
        self.assertIn("Docker", result["missing_technical_skills"])
        # Communication is a soft skill in JD, not resume
        self.assertIn("Communication", result["missing_soft_skills"])
        # Cert checks
        self.assertTrue(len(result["recommended_certifications"]) > 0)
        self.assertTrue(len(result["recommended_projects"]) > 0)
        self.assertTrue(len(result["learning_roadmap"]) > 0)


if __name__ == "__main__":
    unittest.main()
