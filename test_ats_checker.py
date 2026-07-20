"""Unit and integration tests for the ATS Score Analyzer feature."""

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from app import app
from services.ats_checker import analyze_resume_ats, AtsAnalysisError, ATS_SYSTEM_PROMPT


class TestAtsChecker(unittest.TestCase):
    """Tests for the ATS checker service and integration."""

    def setUp(self):
        self.app = app
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    @patch("services.ats_checker.OpenAI")
    def test_analyze_resume_ats_success(self, mock_openai_class):
        """Test analyze_resume_ats with a successful mock OpenAI response."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"score": 85, "strengths": ["Good formatting"], "weaknesses": ["Lack of verbs"], "suggestions": ["Add action words"]}'
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_completion

        result = analyze_resume_ats(
            resume_text="This is my test resume text.",
            api_key="mock-key",
            model="gpt-4o-mini",
        )

        self.assertEqual(result["score"], 85)
        self.assertEqual(result["analysis_type"], "AI Assessment")
        self.assertIn("Good formatting", result["strengths"])
        self.assertIn("Lack of verbs", result["weaknesses"])
        self.assertIn("Add action words", result["suggestions"])

        # Check call parameters
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_kwargs["model"], "gpt-4o-mini")
        self.assertEqual(call_kwargs["response_format"], {"type": "json_object"})

    @patch("services.ats_checker.OpenAI")
    def test_analyze_resume_ats_invalid_json(self, mock_openai_class):
        """Test analyze_resume_ats when OpenAI returns invalid JSON."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Not JSON"))]
        mock_client.chat.completions.create.return_value = mock_completion

        with self.assertRaises(AtsAnalysisError):
            analyze_resume_ats(
                resume_text="Resume content",
                api_key="mock-key",
                model="gpt-4o-mini",
            )

    @patch("services.ats_checker.OpenAI")
    def test_analyze_resume_ats_missing_keys(self, mock_openai_class):
        """Test analyze_resume_ats when OpenAI response is missing required keys."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_completion = MagicMock()
        mock_completion.choices = [mock_completion.choices[0] if hasattr(mock_completion, "choices") else MagicMock()]
        mock_completion.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"score": 85, "strengths": ["formatting"]}'
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_completion

        with self.assertRaises(AtsAnalysisError):
            analyze_resume_ats(
                resume_text="Resume content",
                api_key="mock-key",
                model="gpt-4o-mini",
            )

    def test_analyze_resume_ats_fallback(self):
        """Test analyze_resume_ats when api_key is missing (should use local heuristics)."""
        result = analyze_resume_ats(
            resume_text="John Doe. Email: john@example.com, Phone: 1234567890. Experience. Education. Skills. Projects. Developed python code.",
            api_key="",
            model="gpt-4o-mini",
        )
        self.assertEqual(result["analysis_type"], "Local Diagnostics")
        self.assertGreater(result["score"], 40)
        self.assertIn("Contains complete contact info (email and phone number parsed).", result["strengths"])

    @patch("routes.main.analyze_resume_ats")
    def test_upload_route_with_mock_ats(self, mock_analyze):
        """Test the upload route and html render containing ATS score layout."""
        mock_analyze.return_value = {
            "score": 92,
            "strengths": ["Excellent formatting", "Clear headings"],
            "weaknesses": ["Missed contact metrics"],
            "suggestions": ["Include list of portfolio urls"],
            "analysis_type": "AI Assessment",
        }

        # Enable mock key on Flask config for route path execution
        self.app.config["OPENAI_API_KEY"] = "mock-key"
        self.app.config["OPENAI_MODEL"] = "gpt-4o-mini"

        docx_path = Path("test_resume.docx")
        
        # Resolve test file
        if not docx_path.exists():
            # Create a mock file if not present
            with open(docx_path, "wb") as f:
                f.write(b"mock docx file content")

        with open(docx_path, "rb") as docx_file:
            response = self.client.post(
                "/resume/upload",
                data={"resume_file": (docx_file, "test_resume.docx")},
                follow_redirects=True,
            )

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # Assert ATS UI blocks are rendered
        self.assertIn("ATS Score Analysis", html)
        self.assertIn("AI Assessment", html)  # Analysis type badge content
        self.assertIn("92", html)  # Score number
        self.assertIn("Excellent formatting", html)
        self.assertIn("Missed contact metrics", html)
        self.assertIn("Include list of portfolio urls", html)
        self.assertIn("progress-bar bg-success", html)  # Green progress bar for score >= 80

        # Clean config
        self.app.config["OPENAI_API_KEY"] = None


if __name__ == "__main__":
    unittest.main()
