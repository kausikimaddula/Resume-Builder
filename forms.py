"""Web forms used by the AI Resume Builder & Tracker."""

from __future__ import annotations

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import EmailField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import Email, Length, Optional, Regexp, DataRequired


class ResumeDetailsForm(FlaskForm):
    """Collect resume details before any AI features are added.

    Flask-WTF gives us CSRF protection and validation in one beginner-friendly
    place, so route functions can stay focused on request handling.
    """

    full_name = StringField(
        "Full Name",
        validators=[DataRequired(), Length(max=120)],
    )
    email = EmailField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=120)],
    )
    phone = StringField(
        "Phone",
        validators=[
            DataRequired(),
            Length(max=30),
            Regexp(
                r"^[0-9()+\-\s.]+$",
                message="Use only numbers, spaces, and phone symbols.",
            ),
        ],
    )
    linkedin = StringField("LinkedIn", validators=[Optional(), Length(max=200)])
    github = StringField("GitHub", validators=[Optional(), Length(max=200)])
    portfolio = StringField("Portfolio", validators=[Optional(), Length(max=200)])
    address = StringField("Address", validators=[Optional(), Length(max=250)])

    degree = StringField("Degree", validators=[DataRequired(), Length(max=120)])
    college = StringField("College", validators=[DataRequired(), Length(max=160)])
    graduation_year = StringField(
        "Graduation Year",
        validators=[
            DataRequired(),
            Regexp(r"^\d{4}$", message="Enter a 4-digit year."),
        ],
    )
    gpa = StringField("GPA", validators=[Optional(), Length(max=20)])

    skills = TextAreaField("Skills", validators=[DataRequired(), Length(max=2000)])

    company = StringField("Company", validators=[DataRequired(), Length(max=160)])
    role = StringField("Role", validators=[DataRequired(), Length(max=120)])
    duration = StringField("Duration", validators=[DataRequired(), Length(max=80)])
    responsibilities = TextAreaField(
        "Responsibilities",
        validators=[DataRequired(), Length(max=2500)],
    )

    project_name = StringField(
        "Project Name",
        validators=[DataRequired(), Length(max=160)],
    )
    project_description = TextAreaField(
        "Description",
        validators=[DataRequired(), Length(max=2000)],
    )
    technologies = StringField(
        "Technologies",
        validators=[DataRequired(), Length(max=250)],
    )

    certifications = TextAreaField(
        "Certifications",
        validators=[Optional(), Length(max=2000)],
    )
    achievements = TextAreaField(
        "Achievements",
        validators=[Optional(), Length(max=2000)],
    )
    languages = TextAreaField("Languages", validators=[Optional(), Length(max=1000)])

    submit = SubmitField("Save Resume Details")


class ResumeTemplateUploadForm(FlaskForm):
    """Validate resume template uploads.

    DOCX files can be edited later, while PDF files are accepted for display
    only. The app does not populate either file type yet.
    """

    template_file = FileField(
        "Resume Template",
        validators=[
            FileRequired(message="Choose a DOCX or PDF file."),
            FileAllowed(["docx", "pdf"], "Only DOCX and PDF files are allowed."),
        ],
    )
    submit = SubmitField("Upload Template")


class ResumeUploadForm(FlaskForm):
    """Validate uploaded resume files for text extraction."""

    resume_file = FileField(
        "Upload Resume",
        validators=[
            FileRequired(message="Choose a DOCX or PDF file to extract text from."),
            FileAllowed(["docx", "pdf"], "Only DOCX and PDF files are allowed."),
        ],
    )
    submit = SubmitField("Extract Text")


class JobDescriptionUploadForm(FlaskForm):
    """Validate uploaded job description files and text for text extraction."""

    jd_file = FileField(
        "Upload Job Description File",
        validators=[
            Optional(),
            FileAllowed(["docx", "pdf", "txt"], "Only PDF, DOCX, and TXT files are allowed."),
        ],
    )
    jd_text = TextAreaField(
        "Or Paste Job Description",
        validators=[Optional(), Length(max=10000)],
    )
    submit = SubmitField("Extract Text")



class GenerateResumeForm(FlaskForm):
    """Choose a saved DOCX template for AI resume generation."""

    template_filename = SelectField(
        "DOCX Template",
        validators=[DataRequired(message="Choose a DOCX template.")],
    )
    submit = SubmitField("Generate Resume")


class ResumeJdCompareForm(FlaskForm):
    """Validate inputs for comparing a Resume against a Job Description."""

    resume_file = FileField(
        "Upload Resume File",
        validators=[
            Optional(),
            FileAllowed(["docx", "pdf"], "Only DOCX and PDF resume files are allowed."),
        ],
    )
    resume_text = TextAreaField(
        "Or Paste Resume Text",
        validators=[Optional(), Length(max=10000)],
    )
    jd_file = FileField(
        "Upload Job Description File",
        validators=[
            Optional(),
            FileAllowed(["docx", "pdf", "txt"], "Only PDF, DOCX, and TXT job description files are allowed."),
        ],
    )
    jd_text = TextAreaField(
        "Or Paste Job Description Text",
        validators=[Optional(), Length(max=10000)],
    )
    submit = SubmitField("Compare Resume vs JD")

