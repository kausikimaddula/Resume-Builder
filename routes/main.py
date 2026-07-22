"""Main public routes for the application."""

from __future__ import annotations

from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    send_from_directory,
    url_for,
)

from forms import (
    GenerateResumeForm,
    ResumeDetailsForm,
    ResumeTemplateUploadForm,
    ResumeUploadForm,
    JobDescriptionUploadForm,
    ResumeJdCompareForm,
    ResumeImprovementForm,
)
from services.resume_store import get_all_resumes, get_resume, save_resume
from services.resume_builder import ResumeBuilderError, build_resume_from_template
from services.upload_service import (
    list_docx_templates,
    resolve_uploaded_template,
    save_template_upload,
    save_resume_upload,
)
from services.resume_parser import extract_resume_text
from services.proofreader import ProofreaderError, proofread_resume
from services.ats_checker import AtsAnalysisError, analyze_resume_ats
from services.job_description import save_jd_upload, extract_jd_text
from services.jd_matcher import match_resume_to_jd, JdMatcherError
from services.resume_improver import improve_resume, ResumeImproverError



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

    generate_form = build_generate_form()
    return render_template(
        "resume_detail.html",
        resume=resume,
        generate_form=generate_form,
    )


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


@main_bp.route("/resume/upload", methods=["GET", "POST"])
def upload_resume():
    """Upload an existing resume to parse and display its content."""
    form = ResumeUploadForm()
    extracted_text = None
    file_info = None
    ats_analysis = None
    proofread_results = None

    if form.validate_on_submit():
        try:
            upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
            uploaded_file = save_resume_upload(form.resume_file.data, upload_folder)
            
            # Extract text
            extracted_text = extract_resume_text(uploaded_file.path)
            
            file_info = {
                "original_filename": uploaded_file.original_filename,
                "file_type": uploaded_file.file_type,
            }
            
            # General OpenAI API details
            api_key = current_app.config.get("OPENAI_API_KEY")
            model = current_app.config.get("OPENAI_MODEL")
            
            # Perform ATS analysis
            try:
                ats_analysis = analyze_resume_ats(
                    resume_text=extracted_text,
                    api_key=api_key,
                    model=model,
                )
            except AtsAnalysisError as ats_err:
                current_app.logger.warning("ATS Score Analysis failed: %s", ats_err)
                flash(f"ATS Score Analysis could not be completed: {ats_err}", "warning")
                
            # Perform proofreading analysis
            try:
                proofread_results = proofread_resume(
                    resume_text=extracted_text,
                    api_key=api_key,
                    model=model,
                )
            except ProofreaderError as pr_err:
                current_app.logger.warning("Proofreading Analysis failed: %s", pr_err)
                flash(f"Proofreading Analysis could not be completed: {pr_err}", "warning")
                
            current_app.logger.info(
                "Resume uploaded and text extracted: %s",
                uploaded_file.stored_filename,
            )
            flash("Resume uploaded and parsed successfully.", "success")
        except Exception as error:
            current_app.logger.exception("Failed to upload/parse resume: %s", error)
            flash(str(error), "danger")

    return render_template(
        "resume_upload.html",
        form=form,
        extracted_text=extracted_text,
        file_info=file_info,
        ats_analysis=ats_analysis,
        proofread_results=proofread_results,
    )


@main_bp.route("/job-description/upload", methods=["GET", "POST"])
def upload_job_description():
    """Upload an existing job description or paste text to extract and display."""
    form = JobDescriptionUploadForm()
    extracted_text = None
    file_info = None

    if form.validate_on_submit():
        jd_file = form.jd_file.data
        jd_text = form.jd_text.data

        if not jd_file and not jd_text.strip():
            flash("Please upload a file or paste a job description.", "danger")
        else:
            try:
                if jd_file:
                    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
                    uploaded_file = save_jd_upload(jd_file, upload_folder)
                    extracted_text = extract_jd_text(uploaded_file.path)
                    file_info = {
                        "original_filename": uploaded_file.original_filename,
                        "file_type": uploaded_file.file_type,
                    }
                else:
                    extracted_text = jd_text.strip()
                    file_info = {
                        "original_filename": "Pasted Text",
                        "file_type": "Plain Text",
                    }
                flash("Job description processed successfully.", "success")
                current_app.logger.info("Job description processed successfully")
            except Exception as error:
                current_app.logger.exception("Failed to process job description: %s", error)
                flash(str(error), "danger")

    return render_template(
        "job_description_upload.html",
        form=form,
        extracted_text=extracted_text,
        file_info=file_info,
    )


@main_bp.route("/compare", methods=["GET", "POST"])
def compare_resume_vs_jd():
    """Compare a resume (PDF/DOCX) against a job description (PDF/DOCX/TXT) or paste text."""
    form = ResumeJdCompareForm()
    match_results = None
    inputs_info = None

    if form.validate_on_submit():
        resume_file = form.resume_file.data
        resume_text_input = form.resume_text.data
        jd_file = form.jd_file.data
        jd_text_input = form.jd_text.data

        has_resume = bool(resume_file or resume_text_input.strip())
        has_jd = bool(jd_file or jd_text_input.strip())

        if not has_resume or not has_jd:
            if not has_resume:
                flash("Please upload a resume file or paste resume text.", "danger")
            if not has_jd:
                flash("Please upload a job description file or paste job description text.", "danger")
        else:
            try:
                # 1. Process Resume
                if resume_file:
                    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
                    uploaded_resume = save_resume_upload(resume_file, upload_folder)
                    resume_text = extract_resume_text(uploaded_resume.path)
                    resume_source = uploaded_resume.original_filename
                else:
                    resume_text = resume_text_input.strip()
                    resume_source = "Pasted Resume Text"

                # 2. Process Job Description
                if jd_file:
                    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
                    uploaded_jd = save_jd_upload(jd_file, upload_folder)
                    jd_text = extract_jd_text(uploaded_jd.path)
                    jd_source = uploaded_jd.original_filename
                else:
                    jd_text = jd_text_input.strip()
                    jd_source = "Pasted Job Description Text"

                # 3. Perform Comparison
                api_key = current_app.config.get("OPENAI_API_KEY")
                model = current_app.config.get("OPENAI_MODEL")
                
                match_results = match_resume_to_jd(
                    resume_text=resume_text,
                    jd_text=jd_text,
                    api_key=api_key,
                    model=model,
                )
                
                inputs_info = {
                    "resume_source": resume_source,
                    "jd_source": jd_source,
                }
                
                flash("Resume vs Job Description comparison completed successfully.", "success")
                current_app.logger.info("Resume vs JD comparison successful")
            except Exception as error:
                current_app.logger.exception("Comparison failed: %s", error)
                flash(str(error), "danger")

    return render_template(
        "compare.html",
        form=form,
        match_results=match_results,
        inputs_info=inputs_info,
    )


@main_bp.route("/resume/improve", methods=["GET", "POST"])
def improve_resume_route():
    """Analyze a resume (file or text) and generate AI-driven section-wise improvement suggestions."""
    form = ResumeImprovementForm()
    suggestions = None
    input_info = None

    if form.validate_on_submit():
        resume_file = form.resume_file.data
        resume_text_input = form.resume_text.data
        target_role = form.target_role.data or ""

        if not resume_file and not resume_text_input.strip():
            flash("Please upload a resume file or paste resume text to analyze.", "danger")
        else:
            try:
                if resume_file:
                    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
                    uploaded_resume = save_resume_upload(resume_file, upload_folder)
                    resume_text = extract_resume_text(uploaded_resume.path)
                    source_name = uploaded_resume.original_filename
                else:
                    resume_text = resume_text_input.strip()
                    source_name = "Pasted Resume Text"

                api_key = current_app.config.get("OPENAI_API_KEY")
                model = current_app.config.get("OPENAI_MODEL")

                suggestions = improve_resume(
                    resume_text=resume_text,
                    target_role=target_role,
                    api_key=api_key,
                    model=model,
                )

                input_info = {
                    "source_name": source_name,
                    "target_role": target_role,
                }

                flash("Resume improvement analysis completed successfully.", "success")
                current_app.logger.info("Resume improvement suggestions generated for: %s", source_name)
            except Exception as error:
                current_app.logger.exception("Resume improvement failed: %s", error)
                flash(str(error), "danger")

    return render_template(
        "resume_improvement.html",
        form=form,
        suggestions=suggestions,
        input_info=input_info,
    )





@main_bp.post("/resume/<int:resume_id>/generate")
def generate_resume(resume_id: int):
    """Generate a completed DOCX resume from saved details and a DOCX template."""
    resume = get_resume(resume_id)
    if resume is None:
        flash("Resume details were not found. Please submit the form again.", "warning")
        return redirect(url_for("main.resume_form"))

    form = build_generate_form()
    if not form.validate_on_submit():
        flash("Choose a DOCX template before generating a resume.", "danger")
        return redirect(url_for("main.resume_detail", resume_id=resume_id))

    try:
        upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
        generated_folder = Path(current_app.config["GENERATED_FOLDER"])
        template_path = resolve_uploaded_template(
            upload_folder,
            form.template_filename.data,
        )
        generated_resume = build_resume_from_template(
            resume_details=resume,
            template_path=template_path,
            output_folder=generated_folder,
            api_key=current_app.config["OPENAI_API_KEY"],
            model=current_app.config["OPENAI_MODEL"],
        )
    except (FileNotFoundError, ValueError, ResumeBuilderError) as error:
        current_app.logger.warning("Resume generation failed: %s", error)
        flash(str(error), "danger")
        return redirect(url_for("main.resume_detail", resume_id=resume_id))

    current_app.logger.info("Generated resume: %s", generated_resume.filename)
    flash("Completed resume generated successfully.", "success")
    return redirect(
        url_for("main.download_generated_resume", filename=generated_resume.filename)
    )


@main_bp.get("/generated/<path:filename>")
def download_generated_resume(filename: str):
    """Download a generated resume from the generated uploads folder."""
    return send_from_directory(
        Path(current_app.config["GENERATED_FOLDER"]),
        filename,
        as_attachment=True,
        download_name=filename,
    )


def build_generate_form() -> GenerateResumeForm:
    """Create a template-selection form with current DOCX uploads."""
    form = GenerateResumeForm()
    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    templates = list_docx_templates(upload_folder)
    form.template_filename.choices = [
        (template.stored_filename, template.original_filename)
        for template in templates
    ]
    return form
