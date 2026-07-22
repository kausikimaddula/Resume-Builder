"""Unit and integration tests for the Resume Proofreader feature."""

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from app import app
from services.proofreader import proofread_resume, ProofreaderError


class TestProofreader(unittest.TestCase):
    """Tests for the resume proofreading service and integration."""

    def setUp(self):
        self.app = app
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    @patch("services.proofreader.OpenAI")
    def test_proofread_resume_ai_success(self, mock_openai_class):
        """Test proofread_resume with a successful mock OpenAI response."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"mistakes": [{"original": "I has a cat.", "correction": "I have a cat.", "reason": "Subject-verb agreement error.", "mistake_word": "has"}]}'
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_completion

        result = proofread_resume(
            resume_text="I has a cat.",
            api_key="mock-key",
            model="gpt-4o-mini",
        )

        self.assertEqual(result["analysis_type"], "AI Assessment")
        self.assertEqual(len(result["mistakes"]), 1)
        mistake = result["mistakes"][0]
        self.assertEqual(mistake["original"], "I has a cat.")
        self.assertEqual(mistake["correction"], "I have a cat.")
        self.assertEqual(mistake["mistake_word"], "has")

    @patch("services.proofreader.OpenAI")
    def test_proofread_resume_invalid_json(self, mock_openai_class):
        """Test proofread_resume raising error on invalid JSON."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Invalid JSON body"))]
        mock_client.chat.completions.create.return_value = mock_completion

        with self.assertRaises(ProofreaderError):
            proofread_resume(
                resume_text="Text content",
                api_key="mock-key",
                model="gpt-4o-mini",
            )

    def test_proofread_resume_heuristics_fallback(self):
        """Test local proofread heuristics for spelling typos, double words, and weak words."""
        # Test double word, typo "teh", weak word "helped", and passive voice
        test_text = "I went to teh store. The client was developed by teh team. We had database database issues. I helped design UI."
        result = proofread_resume(
            resume_text=test_text,
            api_key="",
            model="gpt-4o-mini",
        )

        self.assertEqual(result["analysis_type"], "Local Diagnostics")
        mistakes = result["mistakes"]
        self.assertGreater(len(mistakes), 2)

        # Match typos
        originals = [m["original"] for m in mistakes]
        self.assertTrue(any("teh" in orig for orig in originals), "Heuristic failed to identify 'teh' typo.")
        
        # Match double words
        self.assertTrue(any("database database" in orig for orig in originals), "Heuristic failed to catch duplicate word sequence.")

        # Match weak words
        self.assertTrue(any("helped" in orig for orig in originals), "Heuristic failed to catch weak verb 'helped'.")

    @patch("routes.main.proofread_resume")
    def test_upload_route_with_mock_proofread(self, mock_proofread):
        """Test the upload route HTML rendering for spelling & grammar reviews."""
        mock_proofread.return_value = {
            "mistakes": [
                {
                    "original": "I has developed the site.",
                    "correction": "I have developed the site.",
                    "reason": "Subject-verb agreement error with singular possessive verb.",
                    "mistake_word": "has",
                }
            ],
            "analysis_type": "AI Assessment",
        }

        # Enable key in Flask config for route execution logic
        self.app.config["OPENAI_API_KEY"] = "mock-key"
        self.app.config["OPENAI_MODEL"] = "gpt-4o-mini"

        # Resolve test file
        docx_path = Path("test_resume.docx")
        if not docx_path.exists():
            from docx import Document
            doc = Document()
            doc.add_paragraph("Jane Doe Resume")
            doc.save(docx_path)


        with open(docx_path, "rb") as docx_file:
            response = self.client.post(
                "/resume/upload",
                data={"resume_file": (docx_file, "test_resume.docx")},
                follow_redirects=True,
            )

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # Assert ATS UI blocks are rendered
        self.assertIn("Grammar & Spelling Review", html)
        self.assertIn("AI Assessment", html)
        self.assertIn("I <mark", html)  # Mark for highlighted mistake
        self.assertIn("has", html)
        self.assertIn("I have developed the site.", html)

        # Clean config
        self.app.config["OPENAI_API_KEY"] = None


if __name__ == "__main__":
    unittest.main()
