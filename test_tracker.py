"""Unit and integration tests for the Resume Tracker feature."""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


from app import app
from models import db, TrackedResume
from services.resume_store import save_resume


class TestResumeTracker(unittest.TestCase):
    """Tests for the Resume Tracker model, routes, search, sort, and deletion."""

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            TrackedResume.query.delete()
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            TrackedResume.query.delete()
            db.session.commit()


    def test_tracked_resume_model_crud(self):
        """Test creating, reading, updating, and deleting TrackedResume records."""
        with self.app.app_context():
            record = TrackedResume(
                resume_name="Software Engineer Resume",
                job_role="Senior Python Engineer",
                company_name="Google",
                ats_score=92,
                match_score=88,
                notes="Referred by team lead.",
            )
            db.session.add(record)
            db.session.commit()

            fetched = TrackedResume.query.filter_by(company_name="Google").first()
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.resume_name, "Software Engineer Resume")
            self.assertEqual(fetched.ats_score, 92)
            self.assertEqual(fetched.match_score, 88)

            d = fetched.to_dict()
            self.assertEqual(d["job_role"], "Senior Python Engineer")

            # Delete
            db.session.delete(fetched)
            db.session.commit()
            self.assertIsNone(TrackedResume.query.filter_by(company_name="Google").first())

    def test_tracker_route_get_empty(self):
        """Test GET request to /tracker when no entries exist."""
        response = self.client.get("/tracker")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Resume Tracker Dashboard", html)
        self.assertIn("No Tracked Resumes Found", html)

    def test_tracker_route_post_manual_entry(self):
        """Test POST request to /tracker adds a new record."""
        response = self.client.post(
            "/tracker",
            data={
                "resume_name": "Full Stack Dev Resume",
                "job_role": "Full Stack Engineer",
                "company_name": "Acme Corp",
                "ats_score": 85,
                "match_score": 90,
                "notes": "Direct application",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Acme Corp", html)
        self.assertIn("Full Stack Engineer", html)

        with self.app.app_context():
            count = TrackedResume.query.count()
            self.assertEqual(count, 1)

    def test_tracker_route_search_filter(self):
        """Test search filter query parameter on /tracker."""
        with self.app.app_context():
            rec1 = TrackedResume(
                resume_name="DevOps Resume",
                job_role="DevOps Specialist",
                company_name="Amazon",
                ats_score=90,
                match_score=85,
            )
            rec2 = TrackedResume(
                resume_name="Frontend Resume",
                job_role="React Developer",
                company_name="Netflix",
                ats_score=75,
                match_score=80,
            )
            db.session.add_all([rec1, rec2])
            db.session.commit()

        # Search for Amazon
        response = self.client.get("/tracker?search=Amazon")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("DevOps Resume", html)
        self.assertNotIn("Frontend Resume", html)

    def test_tracker_route_sort_by_ats(self):
        """Test sorting entries by ATS score descending."""
        with self.app.app_context():
            rec1 = TrackedResume(
                resume_name="Low ATS Resume",
                job_role="Role A",
                company_name="Company A",
                ats_score=50,
            )
            rec2 = TrackedResume(
                resume_name="High ATS Resume",
                job_role="Role B",
                company_name="Company B",
                ats_score=95,
            )
            db.session.add_all([rec1, rec2])
            db.session.commit()

        response = self.client.get("/tracker?sort_by=ats_desc")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        high_idx = html.find("High ATS Resume")
        low_idx = html.find("Low ATS Resume")
        self.assertTrue(high_idx < low_idx, "High ATS Resume should appear before Low ATS Resume.")

    def test_tracker_route_delete(self):
        """Test deleting a record via POST /tracker/delete/<id>."""
        with self.app.app_context():
            rec = TrackedResume(
                resume_name="Temp Resume",
                job_role="Tester",
                company_name="Test Co",
            )
            db.session.add(rec)
            db.session.commit()
            rec_id = rec.id

        response = self.client.post(f"/tracker/delete/{rec_id}", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("has been deleted", html)

        with self.app.app_context():
            self.assertIsNone(TrackedResume.query.get(rec_id))

    def test_auto_track_on_generate(self):
        """Test that generating a resume auto-saves an entry to TrackedResume."""
        saved_resume = save_resume(
            {
                "personal": {
                    "full_name": "Alice Smith",
                    "email": "alice@example.com",
                    "phone": "555-0199",
                },
                "education": {
                    "degree": "B.S. CS",
                    "college": "MIT",
                    "graduation_year": "2024",
                },
                "skills": "Python, Flask",
                "experience": {
                    "company": "OpenAI",
                    "role": "AI Research Intern",
                    "duration": "2023 - 2024",
                    "responsibilities": "Built model evaluation pipelines.",
                },
                "projects": {
                    "project_name": "Resume Builder",
                    "description": "Flask app",
                    "technologies": "Python, Flask",
                },
            }
        )

        upload_folder = Path(self.app.config["UPLOAD_FOLDER"])
        upload_folder.mkdir(parents=True, exist_ok=True)
        docx_path = upload_folder / "test_resume.docx"
        if not docx_path.exists():
            from docx import Document
            doc = Document()
            doc.add_paragraph("Alice Smith Resume")
            doc.save(docx_path)

        with patch("routes.main.build_resume_from_template") as mock_build:
            mock_build.return_value = MagicMock(filename="generated_test.docx")
            response = self.client.post(
                f"/resume/{saved_resume['id']}/generate",
                data={"template_filename": docx_path.name},
                follow_redirects=False,
            )
            self.assertEqual(response.status_code, 302)


        with self.app.app_context():
            tracked = TrackedResume.query.filter_by(company_name="OpenAI").first()
            self.assertIsNotNone(tracked)
            self.assertIn("Alice Smith", tracked.resume_name)
            self.assertEqual(tracked.job_role, "AI Research Intern")



if __name__ == "__main__":
    unittest.main()
