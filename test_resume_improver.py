"""Unit and integration tests for the Resume Improvement feature."""

from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from app import app
from services.resume_improver import (
    improve_resume,
    ResumeImproverError,
    IMPROVER_SYSTEM_PROMPT,
)


class TestResumeImprover(unittest.TestCase):
    """Tests for the resume improver service and integration routes."""

    def setUp(self):
        self.app = app
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    @patch("services.resume_improver.OpenAI")
    def test_improve_resume_ai_success(self, mock_openai_class):
        """Test improve_resume with a successful mock OpenAI JSON response."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        json_response = """{
            "project_descriptions": [{"original": "Built app", "improved": "Architected scalable app", "reason": "Quantifies scale"}],
            "experience_wording": [{"original": "Handled tasks", "improved": "Orchestrated multi-team tasks", "impact": "Demonstrates leadership"}],
            "summaries": [{"title": "Impact Summary", "text": "Results-driven engineer..."}],
            "skills_ordering": [{"category": "Languages", "ordered_skills": "Python, JS", "rationale": "High demand"}],
            "action_verbs": [{"weak_verb": "made", "power_verb": "engineered", "example": "engineered backend"}],
            "ats_optimization": [{"area": "Headers", "suggestion": "Use Work Experience", "importance": "High"}]
        }"""

        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content=json_response))
        ]
        mock_client.chat.completions.create.return_value = mock_completion

        result = improve_resume(
            resume_text="John Doe Python Developer Experience Projects Skills",
            target_role="Full Stack Engineer",
            api_key="mock-key",
            model="gpt-4o-mini",
        )

        self.assertEqual(result["analysis_type"], "AI Powered Assessment")
        self.assertEqual(len(result["project_descriptions"]), 1)
        self.assertEqual(result["project_descriptions"][0]["improved"], "Architected scalable app")
        self.assertEqual(len(result["experience_wording"]), 1)
        self.assertEqual(len(result["summaries"]), 1)
        self.assertEqual(len(result["skills_ordering"]), 1)
        self.assertEqual(len(result["action_verbs"]), 1)
        self.assertEqual(len(result["ats_optimization"]), 1)

    @patch("services.resume_improver.OpenAI")
    def test_improve_resume_ai_invalid_json(self, mock_openai_class):
        """Test error handling when OpenAI returns non-JSON text."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Invalid non-JSON response"))]
        mock_client.chat.completions.create.return_value = mock_completion

        with self.assertRaises(ResumeImproverError):
            improve_resume(
                resume_text="Sample text",
                api_key="mock-key",
                model="gpt-4o-mini",
            )

    @patch("services.resume_improver.OpenAI")
    def test_improve_resume_ai_missing_keys(self, mock_openai_class):
        """Test error handling when OpenAI response misses required section keys."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content='{"project_descriptions": []}'))
        ]
        mock_client.chat.completions.create.return_value = mock_completion

        with self.assertRaises(ResumeImproverError):
            improve_resume(
                resume_text="Sample text",
                api_key="mock-key",
                model="gpt-4o-mini",
            )

    def test_improve_resume_empty_text(self):
        """Test exception when empty resume text is passed."""
        with self.assertRaises(ResumeImproverError):
            improve_resume(resume_text="   ", api_key="", model="")

    def test_improve_resume_heuristic_fallback(self):
        """Test local heuristic improver fallback when api_key is empty."""
        result = improve_resume(
            resume_text="John Doe. Built web application. Responsible for project management.",
            target_role="Software Engineer",
            api_key="",
            model="",
        )

        self.assertEqual(result["analysis_type"], "Local Diagnostics (Offline)")
        self.assertTrue(len(result["project_descriptions"]) >= 1)
        self.assertTrue(len(result["experience_wording"]) >= 1)
        self.assertTrue(len(result["summaries"]) >= 1)
        self.assertTrue(len(result["skills_ordering"]) >= 1)
        self.assertTrue(len(result["action_verbs"]) >= 1)
        self.assertTrue(len(result["ats_optimization"]) >= 1)

    def test_improve_resume_route_get(self):
        """Test GET request to /resume/improve renders the page."""
        response = self.client.get("/resume/improve")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Resume Improvement & AI Recommendations", html)
        self.assertIn("Upload or Paste Resume", html)

    def test_improve_resume_route_post_text(self):
        """Test POST request with pasted resume text renders suggestions."""
        response = self.client.post(
            "/resume/improve",
            data={
                "resume_text": "Experienced developer with Python, Flask, and PostgreSQL background.",
                "target_role": "Backend Developer",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("AI Improvement Suggestions", html)
        self.assertIn("Better Summaries", html)
        self.assertIn("Better Experience Wording", html)
        self.assertIn("Better Project Descriptions", html)

    def test_improve_resume_route_post_file(self):
        """Test POST request with resume DOCX file upload renders suggestions."""
        docx_path = Path("test_resume.docx")
        if not docx_path.exists():
            from docx import Document
            doc = Document()
            doc.add_paragraph("Jane Doe Resume")
            doc.save(docx_path)

        with open(docx_path, "rb") as docx_file:
            response = self.client.post(
                "/resume/improve",
                data={
                    "resume_file": (docx_file, "test_resume.docx"),
                    "target_role": "Frontend Developer",
                },
                follow_redirects=True,
            )

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("AI Improvement Suggestions", html)
        self.assertIn("Better Summaries", html)


if __name__ == "__main__":
    unittest.main()
