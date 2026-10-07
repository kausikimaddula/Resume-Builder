"""Web forms used by Resume Studio."""

from __future__ import annotations

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    BooleanField,
    EmailField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp


class LoginForm(FlaskForm):
    """Collect user login credentials."""

    email = EmailField(
        "Email Address",
        validators=[DataRequired(), Email(), Length(max=120)],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=6, max=100)],
    )
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Log In")


class ResetPasswordForm(FlaskForm):
    """Collect email and new password to directly reset password."""

    email = EmailField(
        "Email Address",
        validators=[DataRequired(), Email(), Length(max=120)],
    )
    new_password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=6, message="Password must be at least 6 characters long."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo("new_password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Reset Password")


class SignupForm(FlaskForm):
    """Collect new user registration details."""

    full_name = StringField(
        "Full Name",
        validators=[DataRequired(), Length(min=2, max=120)],
    )
    email = EmailField(
        "Email Address",
        validators=[DataRequired(), Email(), Length(max=120)],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=6, message="Password must be at least 6 characters long."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    terms_agree = BooleanField(
        "I agree to the Terms of Service and Privacy Policy",
        validators=[DataRequired(message="You must agree to the terms to sign up.")],
    )
    submit = SubmitField("Create Account")


class ResumeDetailsForm(FlaskForm):
    """Collect resume details before any AI features are added."""

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

    skills = TextAreaField(
        "Skills",
        validators=[
            DataRequired(),
            Length(max=1000, message="Keep skills under 1,000 characters."),
        ],
    )

    company = StringField("Company", validators=[DataRequired(), Length(max=160)])
    role = StringField("Role / Job Title", validators=[DataRequired(), Length(max=160)])
    duration = StringField(
        "Duration",
        validators=[
            DataRequired(),
            Length(max=60),
        ],
    )
    responsibilities = TextAreaField(
        "Key Responsibilities & Achievements",
        validators=[
            DataRequired(),
            Length(max=2000, message="Keep responsibilities under 2,000 characters."),
        ],
    )

    project_name = StringField("Project Name", validators=[Optional(), Length(max=160)])
    project_description = TextAreaField(
        "Project Description",
        validators=[Optional(), Length(max=1000)],
    )
    technologies = StringField(
        "Technologies Used",
        validators=[Optional(), Length(max=200)],
    )

    certifications = TextAreaField("Certifications", validators=[Optional(), Length(max=1000)])
    achievements = TextAreaField("Achievements", validators=[Optional(), Length(max=1000)])
    languages = StringField("Languages", validators=[Optional(), Length(max=200)])

    submit = SubmitField("Save Resume Details")


class ResumeTemplateUploadForm(FlaskForm):
    """Validate uploaded DOCX or PDF resume templates."""

    template_file = FileField(
        "Resume Template (DOCX or PDF)",
        validators=[
            FileRequired("Select a file to upload."),
            FileAllowed(["docx", "pdf"], "Only DOCX and PDF templates are allowed."),
        ],
    )
    submit = SubmitField("Upload Template")


class ResumeUploadForm(FlaskForm):
    """Validate uploaded resume DOCX or PDF file for parsing."""

    resume_file = FileField(
        "Upload Existing Resume (DOCX or PDF)",
        validators=[
            FileRequired("Select a resume file to parse."),
            FileAllowed(["docx", "pdf"], "Only DOCX and PDF files are allowed."),
        ],
    )
    submit = SubmitField("Upload & Parse Resume")


class GenerateResumeForm(FlaskForm):
    """Validate template choice when generating a finished DOCX resume."""

    template_filename = SelectField("Resume Template", validators=[DataRequired()])
    submit = SubmitField("Generate Completed Resume")


class JobDescriptionUploadForm(FlaskForm):
    """Validate job description upload (file or text)."""

    jd_file = FileField(
        "Upload Job Description File (DOCX/PDF/TXT)",
        validators=[
            Optional(),
            FileAllowed(["docx", "pdf", "txt"], "Only PDF, DOCX, and TXT files are allowed."),
        ],
    )
    jd_text = TextAreaField(
        "Or Paste Job Description Text",
        validators=[Optional(), Length(max=10000)],
    )
    submit = SubmitField("Process Job Description")


class ResumeJdCompareForm(FlaskForm):
    """Validate inputs for comparing a resume against a job description."""

    resume_file = FileField(
        "Upload Resume File (DOCX/PDF)",
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
            FileAllowed(["docx", "pdf", "txt"], "Only PDF, DOCX, and TXT files are allowed."),
        ],
    )
    jd_text = TextAreaField(
        "Or Paste Job Description Text",
        validators=[Optional(), Length(max=10000)],
    )
    submit = SubmitField("Compare Resume vs JD")


class ResumeImprovementForm(FlaskForm):
    """Validate inputs for AI resume improvement recommendations."""

    resume_file = FileField(
        "Upload Resume File (DOCX/PDF)",
        validators=[
            Optional(),
            FileAllowed(["docx", "pdf"], "Only DOCX and PDF resume files are allowed."),
        ],
    )
    resume_text = TextAreaField(
        "Or Paste Resume Text",
        validators=[Optional(), Length(max=10000)],
    )
    target_role = StringField(
        "Target Job Role / Industry (Optional)",
        validators=[Optional(), Length(max=150)],
    )
    submit = SubmitField("Get AI Resume Improvements")


class VersionCompareForm(FlaskForm):
    """Form to select two versions for comparison."""

    version_a = SelectField("Base Version (Version A)", coerce=int, validators=[DataRequired()])
    version_b = SelectField("Comparison Version (Version B)", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Compare Versions")
