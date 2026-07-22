"""SQLAlchemy database models for the AI Resume Builder & Tracker."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class TrackedResume(db.Model):
    """Model representing a tracked resume with ATS and job match scores."""

    __tablename__ = "tracked_resumes"

    id = db.Column(db.Integer, primary_key=True)
    resume_name = db.Column(db.String(150), nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ats_score = db.Column(db.Integer, default=0, nullable=False)
    job_role = db.Column(db.String(120), nullable=False)
    company_name = db.Column(db.String(120), nullable=False)
    match_score = db.Column(db.Integer, default=0, nullable=False)
    notes = db.Column(db.Text, nullable=True, default="")

    def to_dict(self) -> dict[str, Any]:
        """Convert tracked resume record to a dictionary representation."""
        return {
            "id": self.id,
            "resume_name": self.resume_name,
            "creation_date": self.creation_date.strftime("%Y-%m-%d %H:%M"),
            "ats_score": self.ats_score,
            "job_role": self.job_role,
            "company_name": self.company_name,
            "match_score": self.match_score,
            "notes": self.notes or "",
        }

    def __repr__(self) -> str:
        return (
            f"<TrackedResume id={self.id} name='{self.resume_name}' "
            f"role='{self.job_role}' company='{self.company_name}'>"
        )
