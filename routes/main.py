"""Main public routes for the application."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, url_for

from forms import ResumeDetailsForm, ResumeTemplateUploadForm
from services.resume_store import get_all_resumes, get_resume, save_resume
from services.upload_service import save_template_upload


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    """Show the landing page."""
    current_app.logger.info("Home page requested")
    return render_template("index.html", resume_count=len(get_all_resumes()))


@main_bp.route("/resume/new", methods=["GET", "POST"])
def resume_form():
    """Show and process the resume details form."""
    form = ResumeDetailsForm()

    if form.validate_on_submit():
        # Store only the fields we care about, not Flask-WTF internals.
        resume = save_resume(
            {
                "personal": {
                    "full_name": form.full_name.data,
                    "email": form.email.data,
                    "phone": form.phone.data,
                    "linkedin": form.linkedin.data,
                    "github": form.github.data,
                    "portfolio": form.portfolio.data,
                    "address": form.address.data,
                },
                "education": {
                    "degree": form.degree.data,
                    "college": form.college.data,
                    "graduation_year": form.graduation_year.data,
                    "gpa": form.gpa.data,
                },
                "skills": form.skills.data,
                "experience": {
                    "company": form.company.data,
                    "role": form.role.data,
                    "duration": form.duration.data,
                    "responsibilities": form.responsibilities.data,
                },
                "projects": {
                    "project_name": form.project_name.data,
                    "description": form.project_description.data,
                    "technologies": form.technologies.data,
                },
                "certifications": form.certifications.data,
                "achievements": form.achievements.data,
                "languages": form.languages.data,
            }
        )
        current_app.logger.info("Resume details saved in memory: %s", resume["id"])
        flash("Resume details saved temporarily in memory.", "success")
        return redirect(url_for("main.resume_detail", resume_id=resume["id"]))

    return render_template("resume_form.html", form=form)


@main_bp.get("/resume/<int:resume_id>")
def resume_detail(resume_id: int):
    """Show a saved in-memory resume submission."""
    resume = get_resume(resume_id)
    if resume is None:
        flash("That resume submission is no longer available.", "warning")
        return redirect(url_for("main.resume_form"))

    return render_template("resume_detail.html", resume=resume)


@main_bp.route("/templates/upload", methods=["GET", "POST"])
def upload_template():
    """Upload a DOCX or PDF resume template to the uploads folder."""
    form = ResumeTemplateUploadForm()
    uploaded_template = None

    if form.validate_on_submit():
        try:
            upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
            uploaded_template = save_template_upload(form.template_file.data, upload_folder)
            current_app.logger.info(
                "Resume template uploaded: %s",
                uploaded_template.stored_filename,
            )
            flash("Resume template uploaded successfully.", "success")
        except ValueError as error:
            current_app.logger.warning("Template upload rejected: %s", error)
            flash(str(error), "danger")

    return render_template(
        "template_upload.html",
        form=form,
        uploaded_template=uploaded_template,
    )
