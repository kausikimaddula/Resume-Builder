"""Integration test for the /compare route and matcher service with the improved schema."""

from __future__ import annotations

import sys
from io import BytesIO
from unittest.mock import patch
from app import app


@patch("routes.main.extract_resume_text")
@patch("routes.main.extract_jd_text")
@patch("routes.main.match_resume_to_jd")
def test_matcher_integration_flow(
    mock_match, mock_extract_jd, mock_extract_resume
) -> bool:
    app.config["WTF_CSRF_ENABLED"] = False
    
    # Configure mock returns matching the improved schema
    mock_extract_resume.return_value = "Mocked Resume Text"
    mock_extract_jd.return_value = "Mocked Job Description Text"
    mock_match.return_value = {
        "match_percentage": 75,
        "matching_skills": ["Python", "Flask"],
        "missing_technical_skills": ["Docker", "Kubernetes"],
        "missing_soft_skills": ["Leadership"],
        "recommended_keywords": ["Containers", "Pod"],
        "recommended_certifications": ["AWS Architect"],
        "recommended_projects": ["Build Docker container deployment project."],
        "learning_roadmap": ["Step 1: Containerize application.", "Step 2: Learn orchestration."],
        "analysis_type": "AI Assessment",
    }
    
    with app.test_client() as client:
        # 1. Test Copy-Pasted Text Comparison (Local Diagnostics Fallback)
        print("Testing Compare Route with pasted inputs...")
        response = client.post(
            "/compare",
            data={
                "resume_file": (BytesIO(), ""),
                "resume_text": "Experienced Python developer with React and Postgres expertise.",
                "jd_file": (BytesIO(), ""),
                "jd_text": "We need a Python developer who knows React, Docker and AWS.",
            },
            follow_redirects=True,
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        html = response.get_data(as_text=True)
        assert "Match Analysis Dashboard" in html or "Match Analysis Results" in html, "Couldn't find Match Analysis headers in page output"
        assert "Python" in html, "Skills output should list matching keywords like Python"
        assert "Docker" in html, "Missing tech skills should include Docker"
        print("Copy-paste compare integration test passed!")

        # 2. Test File Upload + Pasted Text Mix
        print("Testing Compare Route with file upload + pasted text mix...")
        response = client.post(
            "/compare",
            data={
                "resume_file": (BytesIO(b"Data analyst specializing in SQL and PowerBI."), "my_resume.pdf"),
                "resume_text": "",
                "jd_file": (BytesIO(), ""),
                "jd_text": "Looking for SQL Analyst with PowerBI skills.",
            },
            follow_redirects=True,
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        html = response.get_data(as_text=True)
        assert "my_resume.pdf" in html, "Did not record resume file source"
        assert "Pasted Job Description Text" in html, "Did not record JD text source"
        print("File mix comparison integration test passed!")

        # 3. Test Form Validation (missing resume input)
        print("Testing missing input validation error handling...")
        response = client.post(
            "/compare",
            data={
                "resume_file": (BytesIO(), ""),
                "resume_text": "   ",  # whitespace only
                "jd_file": (BytesIO(), ""),
                "jd_text": "Some position requirements",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Please upload a resume file or paste resume text." in html, "Missing resume flash check failed"
        print("Integration validation checks passed!")

    print("All comparison integration tests passed successfully!")
    return True


if __name__ == "__main__":
    try:
        success = test_matcher_integration_flow()
        if not success:
            sys.exit(1)
    except AssertionError as e:
        print(f"Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Test failed with error: {e}")
        sys.exit(1)
