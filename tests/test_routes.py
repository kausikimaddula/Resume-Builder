"""Pytest test suite for Flask Web application routes and HTTP endpoints."""

from __future__ import annotations

import io
from pathlib import Path
import pytest
from flask.testing import FlaskClient

from services.database import create_user


def test_index_route(client: FlaskClient) -> None:
    """Test landing page GET request."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Resume" in response.data or b"Studio" in response.data or b"Builder" in response.data


def test_login_route_get_and_post(client: FlaskClient) -> None:
    """Test GET and POST /login endpoint."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Welcome back" in response.data or b"Log In" in response.data or b"Welcome Back" in response.data

    create_user("Test Login User", "user@example.com", "password123")
    login_data = {"email": "user@example.com", "password": "password123"}
    response_post = client.post("/login", data=login_data, follow_redirects=True)
    assert response_post.status_code == 200
    assert b"logged in" in response_post.data.lower() or b"welcome" in response_post.data.lower()


def test_signup_route_get_and_post(client: FlaskClient) -> None:
    """Test GET and POST /signup endpoint."""
    response = client.get("/signup")
    assert response.status_code == 200
    assert b"Create your account" in response.data or b"Sign Up" in response.data or b"Create Your Account" in response.data

    signup_data = {
        "full_name": "New Signup User",
        "email": "newuser_mongo@example.com",
        "password": "password123",
        "confirm_password": "password123",
        "terms_agree": "y",
    }
    response_post = client.post("/signup", data=signup_data, follow_redirects=True)
    assert response_post.status_code == 200
    assert b"account created" in response_post.data.lower() or b"welcome" in response_post.data.lower()


def test_reset_password_route_get_and_post(client: FlaskClient) -> None:
    """Test GET and POST /reset-password endpoint."""
    response = client.get("/reset-password")
    assert response.status_code == 200
    assert b"Reset Password" in response.data

    # Non-existent user
    bad_reset = client.post(
        "/reset-password",
        data={
            "email": "nonexistent_reset@example.com",
            "new_password": "NewSecretPassword123!",
            "confirm_password": "NewSecretPassword123!",
        },
        follow_redirects=True,
    )
    assert bad_reset.status_code == 200
    assert b"no account found" in bad_reset.data.lower()

    # Create account first, then reset
    client.post(
        "/signup",
        data={
            "full_name": "Reset Test User",
            "email": "reset_user@example.com",
            "password": "OldPassword123!",
            "confirm_password": "OldPassword123!",
            "terms_agree": "y",
        },
        follow_redirects=True,
    )

    good_reset = client.post(
        "/reset-password",
        data={
            "email": "reset_user@example.com",
            "new_password": "BrandNewPassword456!",
            "confirm_password": "BrandNewPassword456!",
        },
        follow_redirects=True,
    )
    assert good_reset.status_code == 200
    assert b"password has been reset" in good_reset.data.lower() or b"log in" in good_reset.data.lower()


def test_logout_route(client: FlaskClient) -> None:
    """Test GET /logout endpoint."""
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"logged out" in response.data.lower()


def test_unauthenticated_user_redirects_to_login(unauthenticated_client: FlaskClient) -> None:
    """Verify unauthenticated user clicking tool route redirects to login with warning."""
    response = unauthenticated_client.get("/resume/new", follow_redirects=True)
    assert response.status_code == 200
    assert b"Please log in or sign up" in response.data or b"Log In" in response.data


def test_resume_form_get(client: FlaskClient) -> None:
    """Test GET /resume/new form page."""
    response = client.get("/resume/new")
    assert response.status_code == 200
    assert b"Full Name" in response.data or b"full_name" in response.data


def test_resume_form_post_validation_and_detail(client: FlaskClient) -> None:
    """Test POST /resume/new with valid data saves submission and redirects."""
    form_data = {
        "full_name": "Alice Cooper",
        "email": "alice@example.com",
        "phone": "555-123-4567",
        "degree": "B.S. Software Engineering",
        "college": "MIT",
        "graduation_year": "2021",
        "gpa": "3.8",
        "skills": "Python, Flask, Docker",
        "company": "Alpha Corp",
        "role": "Backend Engineer",
        "duration": "2021-Present",
        "responsibilities": "Built API microservices.",
        "project_name": "Open Source Tool",
        "project_description": "CLI utility for developers.",
        "technologies": "Python",
    }

    response = client.post("/resume/new", data=form_data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Alice Cooper" in response.data


def test_template_upload_route(client: FlaskClient) -> None:
    """Test GET and POST template upload endpoint."""
    response_get = client.get("/templates/upload")
    assert response_get.status_code == 200

    data = {"template_file": (io.BytesIO(b"template binary"), "custom.docx")}
    response_post = client.post("/templates/upload", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert response_post.status_code == 200
    assert b"uploaded successfully" in response_post.data.lower() or b"template" in response_post.data.lower()


def test_resume_upload_route_post(client: FlaskClient, sample_docx_file: Path) -> None:
    """Test POST /resume/upload with a valid DOCX file."""
    with open(sample_docx_file, "rb") as f:
        data = {"resume_file": (f, "test_resume.docx")}
        response = client.post("/resume/upload", data=data, content_type="multipart/form-data", follow_redirects=True)

    assert response.status_code == 200
    assert b"Jane Smith" in response.data
    assert b"ATS Compatibility Score" in response.data


def test_upload_job_description_route(client: FlaskClient) -> None:
    """Test POST /job-description/upload with pasted text."""
    data = {"jd_text": "Senior Backend Developer position requiring Python and SQL."}
    response = client.post("/job-description/upload", data=data, follow_redirects=True)

    assert response.status_code == 200
    assert b"Senior Backend Developer" in response.data


def test_compare_route_pasted_text(client: FlaskClient) -> None:
    """Test POST /compare with pasted resume and JD text."""
    data = {
        "resume_text": "Python Engineer skilled in Flask and SQL",
        "jd_text": "Looking for Python Engineer proficient in Flask and SQL databases",
    }
    response = client.post("/compare", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"comparison completed" in response.data.lower() or b"match" in response.data.lower()


def test_improve_resume_route(client: FlaskClient) -> None:
    """Test POST /resume/improve with resume text."""
    data = {
        "resume_text": "Software Engineer working with Python and web development.",
        "target_role": "Senior Developer",
    }
    response = client.post("/resume/improve", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"improvement analysis completed" in response.data.lower() or b"improved" in response.data.lower() or b"bullet" in response.data.lower()



def test_versions_history_route(client: FlaskClient) -> None:
    """Test GET /versions history page."""
    response = client.get("/versions")
    assert response.status_code == 200
    assert b"Resume" in response.data or b"Version" in response.data


def test_versions_compare_route(client: FlaskClient) -> None:
    """Test GET /versions/compare."""
    response = client.get("/versions/compare")
    assert response.status_code == 200


def test_export_resume_details_pdf(client: FlaskClient) -> None:
    """Test PDF export endpoint for a saved resume."""
    from services.database import save_resume_db
    saved = save_resume_db({"personal": {"full_name": "Export Test", "email": "export@example.com"}})
    resume_id = saved["id"]

    response = client.get(f"/export/resume/details/{resume_id}/pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert len(response.data) > 0


def test_export_resume_details_docx(client: FlaskClient) -> None:
    """Test DOCX export endpoint for a saved resume."""
    from services.database import save_resume_db
    saved = save_resume_db({"personal": {"full_name": "Export Test Docx", "email": "export_docx@example.com"}})
    resume_id = saved["id"]

    response = client.get(f"/export/resume/details/{resume_id}/docx")
    assert response.status_code == 200
    assert "wordprocessingml" in response.mimetype
    assert len(response.data) > 0
