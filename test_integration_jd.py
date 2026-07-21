"""Integration test for the /job-description/upload route and parser service."""

from __future__ import annotations

import sys
from pathlib import Path
from io import BytesIO
from app import app

def test_jd_upload_flow() -> bool:
    app.config["WTF_CSRF_ENABLED"] = False
    
    with app.test_client() as client:
        # 1. Test TXT file upload
        print("Testing Job Description TXT upload...")
        response = client.post(
            "/job-description/upload",
            data={
                "jd_file": (BytesIO(b"Backend engineer with fast writing skills."), "backend_role.txt"),
                "jd_text": ""
            },
            follow_redirects=True
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        html = response.get_data(as_text=True)
        assert "Backend engineer with fast writing skills." in html, "Could not find text in response html"
        assert "backend_role.txt" in html, "Could not find file info in html"
        print("TXT upload integration test passed!")

        # 2. Test Copy-paste text
        print("Testing Job Description Copy-paste text...")
        response = client.post(
            "/job-description/upload",
            data={
                "jd_file": (BytesIO(), ""),
                "jd_text": "Marketing manager role requiring SEO and SEM skills."
            },
            follow_redirects=True
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        html = response.get_data(as_text=True)
        assert "Marketing manager role requiring SEO and SEM skills." in html, "Could not find copy-pasted text in html"
        assert "Pasted Text" in html, "Expected 'Pasted Text' descriptor in HTML output"
        print("Copy-paste integration test passed!")

        # 3. Test Empty inputs (should show validation message/alert)
        print("Testing empty inputs behavior...")
        response = client.post(
            "/job-description/upload",
            data={
                "jd_file": (BytesIO(), ""),
                "jd_text": "   "
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Please upload a file or paste a job description." in html, "Expected flash message alert in empty post"
        print("Empty inputs test passed!")

    print("All Job Description integration tests passed successfully!")
    return True

if __name__ == "__main__":
    try:
        success = test_jd_upload_flow()
        if not success:
            sys.exit(1)
    except AssertionError as e:
        print(f"Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Test failed with error: {e}")
        sys.exit(1)
