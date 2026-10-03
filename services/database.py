"""Unified Database Service supporting PostgreSQL and SQLite."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator
from urllib.parse import urlparse

from werkzeug.security import check_password_hash, generate_password_hash

from services.exceptions import DatabaseError

logger = logging.getLogger(__name__)

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


def is_postgres(db_target: str | Path | None = None) -> bool:
    """Check if the target database is PostgreSQL."""
    url = str(db_target or os.getenv("DATABASE_URL", ""))
    return url.startswith("postgresql://") or url.startswith("postgres://")


@contextmanager
def get_db_cursor(db_target: str | Path | None = None) -> Generator[Any, None, None]:
    """Provide a database connection and cursor supporting both PostgreSQL and SQLite."""
    target = str(db_target or os.getenv("DATABASE_URL", "resume_builder.db"))
    
    if is_postgres(target):
        if not PSYCOPG2_AVAILABLE:
            raise DatabaseError(
                message="psycopg2 is not installed but a PostgreSQL DATABASE_URL was provided.",
                user_message="PostgreSQL driver is missing. Please run pip install psycopg2-binary.",
            )
        try:
            conn = psycopg2.connect(target)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
                conn.close()
        except Exception as error:
            logger.error("PostgreSQL connection/query error: %s", error, exc_info=True)
            raise DatabaseError(
                message=f"PostgreSQL Error: {error}",
                user_message="Database connection error. Please verify PostgreSQL credentials.",
            ) from error
    else:
        # SQLite Connection
        db_path = target.replace("sqlite:///", "") if target.startswith("sqlite:///") else target
        try:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
                conn.close()
        except Exception as error:
            logger.error("SQLite connection/query error on '%s': %s", db_path, error, exc_info=True)
            raise DatabaseError(
                message=f"SQLite Error: {error}",
                user_message="Database error occurred.",
            ) from error


def init_all_tables(db_target: str | Path | None = None) -> None:
    """Initialize all tables (users, resumes, resume_versions) in PostgreSQL or SQLite."""
    with get_db_cursor(db_target) as cursor:
        if is_postgres(db_target):
            # PostgreSQL Schema
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    full_name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash TEXT,
                    oauth_provider VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS resumes (
                    id SERIAL PRIMARY KEY,
                    user_email VARCHAR(255),
                    full_name VARCHAR(255),
                    role_title VARCHAR(255),
                    email VARCHAR(255),
                    phone VARCHAR(50),
                    location VARCHAR(255),
                    summary TEXT,
                    experience_json TEXT,
                    education_json TEXT,
                    skills_json TEXT,
                    projects_json TEXT,
                    certifications_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS resume_versions (
                    id SERIAL PRIMARY KEY,
                    resume_id INTEGER NOT NULL,
                    version_number INTEGER NOT NULL,
                    version_name VARCHAR(255) NOT NULL,
                    created_at VARCHAR(100) NOT NULL,
                    filename VARCHAR(255),
                    file_path TEXT,
                    ats_score INTEGER,
                    match_score INTEGER,
                    changes TEXT,
                    resume_details_json TEXT,
                    resume_text TEXT,
                    template_filename VARCHAR(255)
                );
                """
            )
        else:
            # SQLite Schema
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    oauth_provider TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS resumes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT,
                    full_name TEXT,
                    role_title TEXT,
                    email TEXT,
                    phone TEXT,
                    location TEXT,
                    summary TEXT,
                    experience_json TEXT,
                    education_json TEXT,
                    skills_json TEXT,
                    projects_json TEXT,
                    certifications_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS resume_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resume_id INTEGER NOT NULL,
                    version_number INTEGER NOT NULL,
                    version_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    filename TEXT,
                    file_path TEXT,
                    ats_score INTEGER,
                    match_score INTEGER,
                    changes TEXT,
                    resume_details_json TEXT,
                    resume_text TEXT,
                    template_filename TEXT
                );
                """
            )

    logger.info("Successfully initialized all database tables in %s", "PostgreSQL" if is_postgres(db_target) else "SQLite")


# ---------------------------------------------------------------------------
# User Authentication Helpers
# ---------------------------------------------------------------------------

def create_user(full_name: str, email: str, password: str | None = None, oauth_provider: str | None = None, db_target: str | Path | None = None) -> dict[str, Any]:
    """Register and save a new user with hashed password."""
    email_clean = email.strip().lower()
    pw_hash = generate_password_hash(password) if password else None
    
    with get_db_cursor(db_target) as cursor:
        placeholder = "%s" if is_postgres(db_target) else "?"
        
        # Check existing
        cursor.execute(f"SELECT * FROM users WHERE LOWER(email) = {placeholder}", (email_clean,))
        existing = cursor.fetchone()
        if existing:
            return dict(existing)

        if is_postgres(db_target):
            cursor.execute(
                """
                INSERT INTO users (full_name, email, password_hash, oauth_provider)
                VALUES (%s, %s, %s, %s)
                RETURNING id, full_name, email, oauth_provider, created_at;
                """,
                (full_name.strip(), email_clean, pw_hash, oauth_provider),
            )
            row = cursor.fetchone()
            return dict(row)
        else:
            cursor.execute(
                """
                INSERT INTO users (full_name, email, password_hash, oauth_provider)
                VALUES (?, ?, ?, ?);
                """,
                (full_name.strip(), email_clean, pw_hash, oauth_provider),
            )
            user_id = cursor.lastrowid
            return {
                "id": user_id,
                "full_name": full_name.strip(),
                "email": email_clean,
                "oauth_provider": oauth_provider,
            }


def get_user_by_email(email: str, db_target: str | Path | None = None) -> dict[str, Any] | None:
    """Retrieve user record by email."""
    with get_db_cursor(db_target) as cursor:
        placeholder = "%s" if is_postgres(db_target) else "?"
        cursor.execute(f"SELECT * FROM users WHERE LOWER(email) = {placeholder}", (email.strip().lower(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def verify_user(email: str, password: str, db_target: str | Path | None = None) -> dict[str, Any] | None:
    """Verify email and password hash."""
    user = get_user_by_email(email, db_target)
    if not user or not user.get("password_hash"):
        return None
    if check_password_hash(user["password_hash"], password):
        return user
    return None


# ---------------------------------------------------------------------------
# Resume Persistence Helpers
# ---------------------------------------------------------------------------

def save_resume_db(data: dict[str, Any], user_email: str | None = None, db_target: str | Path | None = None) -> dict[str, Any]:
    """Save structured resume into the database."""
    personal = data.get("personal", {})
    full_name = personal.get("full_name", "")
    email = personal.get("email", "") or user_email or ""
    role_title = personal.get("role_title", "")
    phone = personal.get("phone", "")
    location = personal.get("location", "")
    summary = personal.get("summary", "")

    exp_json = json.dumps(data.get("experience", []))
    edu_json = json.dumps(data.get("education", []))
    skills_json = json.dumps(data.get("skills", []))
    proj_json = json.dumps(data.get("projects", []))
    cert_json = json.dumps(data.get("certifications", []))

    with get_db_cursor(db_target) as cursor:
        if is_postgres(db_target):
            cursor.execute(
                """
                INSERT INTO resumes (
                    user_email, full_name, role_title, email, phone, location, summary,
                    experience_json, education_json, skills_json, projects_json, certifications_json
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (user_email, full_name, role_title, email, phone, location, summary,
                 exp_json, edu_json, skills_json, proj_json, cert_json),
            )
            resume_id = cursor.fetchone()["id"]
        else:
            cursor.execute(
                """
                INSERT INTO resumes (
                    user_email, full_name, role_title, email, phone, location, summary,
                    experience_json, education_json, skills_json, projects_json, certifications_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (user_email, full_name, role_title, email, phone, location, summary,
                 exp_json, edu_json, skills_json, proj_json, cert_json),
            )
            resume_id = cursor.lastrowid

    record = dict(data)
    record["id"] = resume_id
    return record


def get_all_resumes_db(user_email: str | None = None, db_target: str | Path | None = None) -> list[dict[str, Any]]:
    """Retrieve all resumes, optionally filtered by user_email."""
    with get_db_cursor(db_target) as cursor:
        placeholder = "%s" if is_postgres(db_target) else "?"
        if user_email:
            cursor.execute(f"SELECT * FROM resumes WHERE LOWER(user_email) = {placeholder} ORDER BY id DESC", (user_email.lower(),))
        else:
            cursor.execute("SELECT * FROM resumes ORDER BY id DESC")
        
        rows = cursor.fetchall()
        results = []
        for r in rows:
            row_dict = dict(r)
            results.append({
                "id": row_dict["id"],
                "personal": {
                    "full_name": row_dict.get("full_name", ""),
                    "email": row_dict.get("email", ""),
                    "phone": row_dict.get("phone", ""),
                    "location": row_dict.get("location", ""),
                    "role_title": row_dict.get("role_title", ""),
                    "summary": row_dict.get("summary", ""),
                },
                "experience": json.loads(row_dict.get("experience_json") or "[]"),
                "education": json.loads(row_dict.get("education_json") or "[]"),
                "skills": json.loads(row_dict.get("skills_json") or "[]"),
                "projects": json.loads(row_dict.get("projects_json") or "[]"),
                "certifications": json.loads(row_dict.get("certifications_json") or "[]"),
                "created_at": str(row_dict.get("created_at", "")),
            })
        return results


def get_resume_db(resume_id: int, db_target: str | Path | None = None) -> dict[str, Any] | None:
    """Retrieve a single resume by its ID."""
    with get_db_cursor(db_target) as cursor:
        placeholder = "%s" if is_postgres(db_target) else "?"
        cursor.execute(f"SELECT * FROM resumes WHERE id = {placeholder}", (resume_id,))
        row = cursor.fetchone()
        if not row:
            return None
        row_dict = dict(row)
        return {
            "id": row_dict["id"],
            "personal": {
                "full_name": row_dict.get("full_name", ""),
                "email": row_dict.get("email", ""),
                "phone": row_dict.get("phone", ""),
                "location": row_dict.get("location", ""),
                "role_title": row_dict.get("role_title", ""),
                "summary": row_dict.get("summary", ""),
            },
            "experience": json.loads(row_dict.get("experience_json") or "[]"),
            "education": json.loads(row_dict.get("education_json") or "[]"),
            "skills": json.loads(row_dict.get("skills_json") or "[]"),
            "projects": json.loads(row_dict.get("projects_json") or "[]"),
            "certifications": json.loads(row_dict.get("certifications_json") or "[]"),
            "created_at": str(row_dict.get("created_at", "")),
        }
