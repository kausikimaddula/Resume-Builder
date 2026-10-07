"""MongoDB Database Service for User Authentication, Resumes, and Version Tracking."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash

from services.exceptions import DatabaseError

load_dotenv()

logger = logging.getLogger(__name__)

# Global client cache
_mongo_client: Any = None
_mongo_db: Any = None
_use_mock: bool = False


def get_mongo_db(mongo_uri: str | None = None, db_name: str | None = None) -> Any:
    """Return an active MongoDB database instance, using mongomock if server is unreachable."""
    global _mongo_client, _mongo_db, _use_mock

    uri = mongo_uri or os.getenv("MONGO_URI") or os.getenv("MONGODB_URI") or "mongodb://localhost:27017/"
    database_name = db_name or os.getenv("MONGO_DB_NAME", "ResumeDB")

    if _mongo_db is not None:
        return _mongo_db

    try:
        import pymongo

        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Verify connection
        client.admin.command("ping")
        _mongo_client = client
        _mongo_db = client[database_name]
        _use_mock = False
        logger.info("Connected to MongoDB at '%s' (Database: %s)", uri, database_name)
    except Exception as exc:
        logger.warning(
            "Could not connect to live MongoDB server (%s). Initializing in-memory MongoMock engine.",
            exc,
        )
        try:
            import mongomock

            _mongo_client = mongomock.MongoClient()
            _mongo_db = _mongo_client[database_name]
            _use_mock = True
            logger.info("In-memory MongoMock database initialized for database: %s", database_name)
        except Exception as mock_exc:
            logger.error("Failed to initialize database: %s", mock_exc, exc_info=True)
            raise DatabaseError(
                message=f"MongoDB Error: {mock_exc}",
                user_message="Database connection error. Please ensure MongoDB is running or pymongo/mongomock is installed.",
            ) from mock_exc

    return _mongo_db


def get_next_sequence_value(sequence_name: str, db: Any = None) -> int:
    """Generate sequential auto-incrementing integer IDs using counters collection."""
    database = db if db is not None else get_mongo_db()
    counters = database["counters"]
    try:
        from pymongo import ReturnDocument
        doc = counters.find_one_and_update(
            {"_id": sequence_name},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if doc and "seq" in doc:
            return int(doc["seq"])
    except Exception:
        pass

    # Fallback for mock engines or alternative drivers
    existing = counters.find_one({"_id": sequence_name})
    if existing and "seq" in existing:
        return int(existing["seq"])
    return 1


def init_all_tables(db_target: Any = None) -> None:
    """Initialize MongoDB indexes for users, resumes, and resume_versions."""
    db = get_mongo_db()
    try:
        # Users indexes
        db.users.create_index("email", unique=True)
        # Resumes indexes
        db.resumes.create_index("id", unique=True)
        db.resumes.create_index("user_email")
        # Resume versions indexes
        db.resume_versions.create_index("id", unique=True)
        db.resume_versions.create_index("resume_id")
        logger.info("Successfully initialized MongoDB collections and indexes.")
    except Exception as exc:
        logger.warning("Index creation notice: %s", exc)


def clear_test_database() -> None:
    """Clear MongoDB collections for clean testing."""
    db = get_mongo_db()
    for col in ["users", "resumes", "resume_versions", "counters"]:
        try:
            db[col].delete_many({})
        except Exception:
            pass


# ---------------------------------------------------------------------------
# User Authentication Helpers
# ---------------------------------------------------------------------------

def create_user(
    full_name: str,
    email: str,
    password: str | None = None,
    oauth_provider: str | None = None,
    db_target: Any = None,
) -> dict[str, Any]:
    """Register and save a new user in MongoDB."""
    db = get_mongo_db()
    email_clean = email.strip().lower()
    pw_hash = generate_password_hash(password) if password else None

    existing = db.users.find_one({"email": email_clean})
    if existing:
        user_doc = dict(existing)
        user_doc.pop("_id", None)
        return user_doc

    user_id = get_next_sequence_value("users", db)
    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    user_record = {
        "id": user_id,
        "full_name": full_name.strip(),
        "email": email_clean,
        "password_hash": pw_hash,
        "oauth_provider": oauth_provider,
        "created_at": created_at,
    }

    db.users.insert_one(user_record)
    result = dict(user_record)
    result.pop("_id", None)
    return result


def get_user_by_email(email: str, db_target: Any = None) -> dict[str, Any] | None:
    """Retrieve user record from MongoDB by email."""
    db = get_mongo_db()
    user = db.users.find_one({"email": email.strip().lower()})
    if not user:
        return None
    user_doc = dict(user)
    user_doc.pop("_id", None)
    return user_doc


def verify_user(email: str, password: str, db_target: Any = None) -> dict[str, Any] | None:
    """Verify email and password hash from MongoDB."""
    user = get_user_by_email(email, db_target)
    if not user or not user.get("password_hash"):
        return None
    if check_password_hash(user["password_hash"], password):
        return user
    return None


def update_user_password(email: str, new_password: str, db_target: Any = None) -> bool:
    """Update user password directly in MongoDB."""
    db = get_mongo_db()
    email_clean = email.strip().lower()
    pw_hash = generate_password_hash(new_password)
    result = db.users.update_one(
        {"email": email_clean},
        {"$set": {"password_hash": pw_hash, "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}}
    )
    return bool(result.matched_count > 0)


# ---------------------------------------------------------------------------
# Resume Persistence Helpers
# ---------------------------------------------------------------------------

def save_resume_db(
    data: dict[str, Any],
    user_email: str | None = None,
    db_target: Any = None,
) -> dict[str, Any]:
    """Save structured resume into MongoDB."""
    db = get_mongo_db()
    resume_id = get_next_sequence_value("resumes", db)

    personal = data.get("personal", {})
    full_name = personal.get("full_name", "") if isinstance(personal, dict) else ""
    email = (personal.get("email") if isinstance(personal, dict) else "") or user_email or ""
    role_title = personal.get("role_title", "") if isinstance(personal, dict) else ""
    phone = personal.get("phone", "") if isinstance(personal, dict) else ""
    location = personal.get("location", "") or personal.get("address", "") if isinstance(personal, dict) else ""
    summary = personal.get("summary", "") if isinstance(personal, dict) else ""

    experience = data.get("experience", [])
    education = data.get("education", [])
    skills = data.get("skills", "")
    projects = data.get("projects", {})
    certifications = data.get("certifications", "")
    achievements = data.get("achievements", "")
    languages = data.get("languages", "")

    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    doc = {
        "id": resume_id,
        "user_email": (user_email or email or "").lower(),
        "personal": {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "location": location,
            "address": location,
            "role_title": role_title,
            "summary": summary,
            "linkedin": personal.get("linkedin", "") if isinstance(personal, dict) else "",
            "github": personal.get("github", "") if isinstance(personal, dict) else "",
            "portfolio": personal.get("portfolio", "") if isinstance(personal, dict) else "",
        },
        "experience": experience,
        "education": education,
        "skills": skills,
        "projects": projects,
        "certifications": certifications,
        "achievements": achievements,
        "languages": languages,
        "created_at": created_at,
        "updated_at": created_at,
    }

    db.resumes.insert_one(doc)
    saved_record = dict(doc)
    saved_record.pop("_id", None)
    return saved_record


def get_all_resumes_db(
    user_email: str | None = None,
    db_target: Any = None,
) -> list[dict[str, Any]]:
    """Retrieve all resumes from MongoDB, optionally filtered by user_email."""
    db = get_mongo_db()
    query = {"user_email": user_email.lower()} if user_email else {}
    cursor = db.resumes.find(query).sort("id", -1)

    results = []
    for r in cursor:
        doc = dict(r)
        doc.pop("_id", None)
        results.append(doc)
    return results


def get_resume_db(resume_id: int, db_target: Any = None) -> dict[str, Any] | None:
    """Retrieve a single resume by its ID from MongoDB."""
    db = get_mongo_db()
    doc = db.resumes.find_one({"id": int(resume_id)})
    if not doc:
        return None
    record = dict(doc)
    record.pop("_id", None)
    return record


# ---------------------------------------------------------------------------
# Resume Version History Helpers
# ---------------------------------------------------------------------------

def create_resume_version_db(
    *,
    resume_id: int,
    version_number: int,
    version_name: str,
    created_at: str,
    filename: str,
    file_path: str,
    ats_score: int | None,
    match_score: int | None,
    changes: str,
    resume_details_json: str,
    resume_text: str,
    template_filename: str,
    db_target: Any = None,
) -> int:
    """Insert a new resume version into MongoDB."""
    db = get_mongo_db()
    version_id = get_next_sequence_value("resume_versions", db)

    doc = {
        "id": version_id,
        "resume_id": int(resume_id),
        "version_number": int(version_number),
        "version_name": version_name,
        "created_at": created_at,
        "filename": filename,
        "file_path": str(file_path),
        "ats_score": ats_score,
        "match_score": match_score,
        "changes": changes,
        "resume_details_json": resume_details_json,
        "resume_text": resume_text,
        "template_filename": template_filename,
    }

    db.resume_versions.insert_one(doc)
    return version_id


def get_next_version_number_db(resume_id: int, db_target: Any = None) -> int:
    """Get the next version number for a given resume_id from MongoDB."""
    db = get_mongo_db()
    cursor = db.resume_versions.find({"resume_id": int(resume_id)}).sort("version_number", -1).limit(1)
    for doc in cursor:
        return int(doc.get("version_number", 0)) + 1
    return 1


def get_latest_version_for_resume_db(resume_id: int, db_target: Any = None) -> dict[str, Any] | None:
    """Retrieve the latest version for a given resume_id from MongoDB."""
    db = get_mongo_db()
    cursor = db.resume_versions.find({"resume_id": int(resume_id)}).sort("version_number", -1).limit(1)
    for doc in cursor:
        record = dict(doc)
        record.pop("_id", None)
        return record
    return None


def get_version_db(version_id: int, db_target: Any = None) -> dict[str, Any] | None:
    """Retrieve one version by its database ID from MongoDB."""
    db = get_mongo_db()
    doc = db.resume_versions.find_one({"id": int(version_id)})
    if not doc:
        return None
    record = dict(doc)
    record.pop("_id", None)
    return record


def get_versions_for_resume_db(resume_id: int, db_target: Any = None) -> list[dict[str, Any]]:
    """Retrieve all versions for a specific resume_id from MongoDB."""
    db = get_mongo_db()
    cursor = db.resume_versions.find({"resume_id": int(resume_id)}).sort("version_number", 1)
    results = []
    for doc in cursor:
        record = dict(doc)
        record.pop("_id", None)
        results.append(record)
    return results


def get_all_versions_db(db_target: Any = None) -> list[dict[str, Any]]:
    """Retrieve all resume versions across all resumes from MongoDB."""
    db = get_mongo_db()
    cursor = db.resume_versions.find().sort([("resume_id", 1), ("version_number", 1)])
    results = []
    for doc in cursor:
        record = dict(doc)
        record.pop("_id", None)
        results.append(record)
    return results
