import json
import tempfile
import unittest
from pathlib import Path
from docx import Document

from app import create_app
from config import Config
from services.version_service import (
    init_db,
    create_resume_version,
    get_versions_for_resume,
    get_all_versions,
    get_version,
    compare_versions,
)
from services.resume_store import save_resume


class TestVersioning(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_versions.db"
        self.upload_folder = Path(self.temp_dir.name) / "uploads"
        self.generated_folder = self.upload_folder / "generated"
        self.upload_folder.mkdir(parents=True, exist_ok=True)
        self.generated_folder.mkdir(parents=True, exist_ok=True)

        class TestConfig(Config):
            TESTING = True
            SECRET_KEY = "test-secret"
            DATABASE_PATH = Path(self.temp_dir.name) / "test_versions.db"
            UPLOAD_FOLDER = Path(self.temp_dir.name) / "uploads"
            GENERATED_FOLDER = Path(self.temp_dir.name) / "uploads" / "generated"
            WTF_CSRF_ENABLED = False

        self.app = create_app(TestConfig)
        self.client = self.app.test_client()

        self.sample_details_v1 = {
            "personal": {"full_name": "Alice Smith", "email": "alice@example.com", "phone": "1234567890"},
            "education": {"degree": "B.S. CS", "college": "Tech Uni", "graduation_year": "2024"},
            "skills": "Python, SQL",
            "experience": {"role": "Junior Dev", "company": "Acme", "duration": "1 year", "responsibilities": "Wrote code."},
            "projects": {"project_name": "App", "description": "Web app", "technologies": "Flask"},
        }

        self.sample_details_v2 = {
            "personal": {"full_name": "Alice Smith", "email": "alice@example.com", "phone": "1234567890"},
            "education": {"degree": "B.S. CS", "college": "Tech Uni", "graduation_year": "2024"},
            "skills": "Python, SQL, Docker, Kubernetes",
            "experience": {"role": "Senior Dev", "company": "Acme", "duration": "2 years", "responsibilities": "Led team and refactored backend."},
            "projects": {"project_name": "App V2", "description": "Microservices app", "technologies": "Flask, Docker"},
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_db(self):
        init_db(self.db_path)
        self.assertTrue(self.db_path.exists())

    def test_version_creation_and_auto_increment(self):
        v1 = create_resume_version(
            db_path=self.db_path,
            resume_id=1,
            resume_details=self.sample_details_v1,
            filename="resume_v1.docx",
            file_path=self.generated_folder / "resume_v1.docx",
            template_filename="classic.docx",
        )

        self.assertIsNotNone(v1)
        self.assertEqual(v1["version_number"], 1)
        self.assertEqual(v1["version_name"], "Version 1")
        self.assertIsNotNone(v1["created_at"])
        self.assertIn("Initial generation", v1["changes"])

        v2 = create_resume_version(
            db_path=self.db_path,
            resume_id=1,
            resume_details=self.sample_details_v2,
            filename="resume_v2.docx",
            file_path=self.generated_folder / "resume_v2.docx",
            template_filename="modern.docx",
        )

        self.assertEqual(v2["version_number"], 2)
        self.assertEqual(v2["version_name"], "Version 2")
        self.assertIn("Changed template from 'classic.docx' to 'modern.docx'.", v2["changes"])
        self.assertIn("Updated Skills.", v2["changes"])

        v3 = create_resume_version(
            db_path=self.db_path,
            resume_id=1,
            resume_details=self.sample_details_v2,
            filename="resume_v3.docx",
            file_path=self.generated_folder / "resume_v3.docx",
            template_filename="modern.docx",
        )

        self.assertEqual(v3["version_number"], 3)
        self.assertEqual(v3["version_name"], "Version 3")

    def test_get_versions_for_resume(self):
        create_resume_version(
            db_path=self.db_path,
            resume_id=10,
            resume_details=self.sample_details_v1,
            filename="resume1.docx",
            file_path=self.generated_folder / "resume1.docx",
            template_filename="tpl.docx",
        )
        create_resume_version(
            db_path=self.db_path,
            resume_id=10,
            resume_details=self.sample_details_v2,
            filename="resume2.docx",
            file_path=self.generated_folder / "resume2.docx",
            template_filename="tpl.docx",
        )

        versions = get_versions_for_resume(self.db_path, 10)
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0]["version_name"], "Version 1")
        self.assertEqual(versions[1]["version_name"], "Version 2")

    def test_compare_versions(self):
        v1 = create_resume_version(
            db_path=self.db_path,
            resume_id=5,
            resume_details=self.sample_details_v1,
            filename="r1.docx",
            file_path=self.generated_folder / "r1.docx",
            template_filename="template1.docx",
        )
        v2 = create_resume_version(
            db_path=self.db_path,
            resume_id=5,
            resume_details=self.sample_details_v2,
            filename="r2.docx",
            file_path=self.generated_folder / "r2.docx",
            template_filename="template2.docx",
        )

        cmp_res = compare_versions(self.db_path, v1["id"], v2["id"])
        self.assertIsNotNone(cmp_res)
        self.assertEqual(cmp_res["version_a"]["id"], v1["id"])
        self.assertEqual(cmp_res["version_b"]["id"], v2["id"])
        self.assertIsNotNone(cmp_res["diff_lines"])

    def test_flask_version_routes(self):
        # Test GET /versions
        res = self.client.get("/versions")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Resume Versions", res.data)

        # Create a version and test GET /versions/compare
        v1 = create_resume_version(
            db_path=self.app.config["DATABASE_PATH"],
            resume_id=99,
            resume_details=self.sample_details_v1,
            filename="test99_v1.docx",
            file_path=self.generated_folder / "test99_v1.docx",
            template_filename="t.docx",
        )
        v2 = create_resume_version(
            db_path=self.app.config["DATABASE_PATH"],
            resume_id=99,
            resume_details=self.sample_details_v2,
            filename="test99_v2.docx",
            file_path=self.generated_folder / "test99_v2.docx",
            template_filename="t.docx",
        )

        res_cmp = self.client.get(f"/versions/compare?a={v1['id']}&b={v2['id']}")
        self.assertEqual(res_cmp.status_code, 200)
        self.assertIn(b"Version 1", res_cmp.data)
        self.assertIn(b"Version 2", res_cmp.data)


if __name__ == "__main__":
    unittest.main()
