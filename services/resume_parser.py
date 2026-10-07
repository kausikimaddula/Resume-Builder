"""Service for parsing and extracting text from PDF and DOCX resume files."""

from __future__ import annotations

import logging
from pathlib import Path
from docx import Document
from pypdf import PdfReader

from services.exceptions import InvalidFileError

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract all text page-by-page from a PDF file."""
    logger.info("Extracting text from PDF: %s", file_path)
    try:
        reader = PdfReader(file_path)
        text_parts = []
        for index, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
            else:
                logger.warning("Empty page text retrieved from page %d of %s", index, file_path)
        
        extracted = "\n".join(text_parts).strip()
        logger.info("Extracted %d characters from PDF: %s", len(extracted), file_path)
        return extracted
    except Exception as e:
        logger.error("Failed to extract text from PDF file '%s': %s", file_path, e, exc_info=True)
        raise InvalidFileError(
            message=f"Error reading PDF file {file_path}: {e}",
            user_message="Could not read text from the uploaded PDF file. The file may be damaged or password-protected.",
        ) from e


def extract_text_from_docx(file_path: Path) -> str:
    """Extract all text from paragraphs and tables in a DOCX file."""
    logger.info("Extracting text from DOCX: %s", file_path)
    try:
        doc = Document(file_path)
        text_parts = []
        
        # Read paragraphs
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
                
        # Read tables to not miss crucial content like resume grids
        for table in doc.tables:
            for row in table.rows:
                # Merge duplicate cells in rows (often happens with merged columns)
                cells_text = []
                for cell in row.cells:
                    c_text = cell.text.strip()
                    if c_text and (not cells_text or cells_text[-1] != c_text):
                        cells_text.append(c_text)
                if cells_text:
                    text_parts.append(" | ".join(cells_text))
                    
        extracted = "\n".join(text_parts).strip()
        logger.info("Extracted %d characters from DOCX: %s", len(extracted), file_path)
        return extracted
    except Exception as e:
        logger.error("Failed to extract text from DOCX file '%s': %s", file_path, e, exc_info=True)
        raise InvalidFileError(
            message=f"Error reading DOCX file {file_path}: {e}",
            user_message="Could not read text from the uploaded DOCX file. The document may be corrupted.",
        ) from e


def extract_resume_text(file_path: Path) -> str:
    """Detect file type and extract text from the resume.

    Supported formats: PDF, DOCX.
    """
    if not file_path.exists():
        logger.error("Resume file not found at path: %s", file_path)
        raise InvalidFileError(
            message=f"Resume file not found at: {file_path}",
            user_message="The uploaded resume file could not be found on the server.",
        )

    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix == ".docx":
        return extract_text_from_docx(file_path)
    else:
        logger.warning("Unsupported file type '%s' requested for text extraction.", suffix)
        raise InvalidFileError(
            message=f"Unsupported resume file type: {suffix}",
            user_message=f"Unsupported file format '{suffix}'. Only PDF and DOCX files are allowed.",
        )


def parse_resume_to_structured_data(
    resume_text: str,
    api_key: str = "",
    model: str = "",
) -> dict[str, Any]:
    """Parse unstructured resume text into a complete structured dictionary (Personal, Education, Experience, Skills, Projects, etc.)."""
    if not resume_text or not resume_text.strip():
        return {}

    # Try AI-powered parsing first if API key is provided
    if api_key:
        try:
            from services.openai_service import execute_json_chat_completion
            from services.prompts import RESUME_PARSER_SYSTEM_PROMPT, RESUME_PARSER_USER_PROMPT_TEMPLATE

            user_prompt = RESUME_PARSER_USER_PROMPT_TEMPLATE.format(resume_text=resume_text)
            parsed = execute_json_chat_completion(
                system_prompt=RESUME_PARSER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                api_key=api_key,
                model=model or "gpt-4o-mini",
            )
            if isinstance(parsed, dict) and "personal" in parsed:
                return _normalize_parsed_resume(parsed, resume_text)
        except Exception as ai_err:
            logger.warning("AI resume parsing failed, using rule-based parser fallback: %s", ai_err)

    return _parse_resume_heuristics(resume_text)


def _normalize_parsed_resume(data: dict[str, Any], raw_text: str) -> dict[str, Any]:
    """Ensure all required resume sections are present and valid."""
    personal = data.get("personal", {})
    if not isinstance(personal, dict):
        personal = {}

    # Fallback to heuristic email/name if missing
    if not personal.get("email"):
        import re
        m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_text)
        if m:
            personal["email"] = m.group(0)

    if not personal.get("full_name"):
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        if lines:
            personal["full_name"] = lines[0][:60]

    education = data.get("education", {})
    if not isinstance(education, (dict, list)):
        education = {}

    experience = data.get("experience", {})
    if not isinstance(experience, (dict, list)):
        experience = {}

    return {
        "personal": personal,
        "education": education,
        "experience": experience,
        "skills": data.get("skills", ""),
        "projects": data.get("projects", {}),
        "certifications": data.get("certifications", ""),
        "achievements": data.get("achievements", ""),
        "languages": data.get("languages", ""),
    }


def _parse_resume_heuristics(raw_text: str) -> dict[str, Any]:
    """Parse resume text using regex and header section detection."""
    import re

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    full_name = lines[0][:60] if lines else "Candidate"
    
    # Extract email & phone
    email = ""
    phone = ""
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_text)
    if email_match:
        email = email_match.group(0)

    phone_match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", raw_text)
    if phone_match:
        phone = phone_match.group(0)

    linkedin = ""
    li_match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+", raw_text, re.IGNORECASE)
    if li_match:
        linkedin = li_match.group(0)

    github = ""
    gh_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/[\w\-]+", raw_text, re.IGNORECASE)
    if gh_match:
        github = gh_match.group(0)

    # Detect sections
    sections: dict[str, list[str]] = {
        "summary": [],
        "education": [],
        "experience": [],
        "skills": [],
        "projects": [],
        "certifications": [],
    }
    current_sec = "summary"

    for line in lines[1:]:
        upper = line.upper().strip(":#=-* ")
        if upper in ["SUMMARY", "PROFESSIONAL SUMMARY", "ABOUT ME", "EXECUTIVE SUMMARY"]:
            current_sec = "summary"
            continue
        elif upper in ["EDUCATION", "ACADEMIC BACKGROUND", "QUALIFICATIONS"]:
            current_sec = "education"
            continue
        elif upper in ["EXPERIENCE", "WORK EXPERIENCE", "EMPLOYMENT", "PROFESSIONAL EXPERIENCE", "WORK HISTORY"]:
            current_sec = "experience"
            continue
        elif upper in ["SKILLS", "TECHNICAL SKILLS", "CORE COMPETENCIES", "SKILLS & TOOLS"]:
            current_sec = "skills"
            continue
        elif upper in ["PROJECTS", "PERSONAL PROJECTS", "ACADEMIC PROJECTS"]:
            current_sec = "projects"
            continue
        elif upper in ["CERTIFICATIONS", "LICENSES", "CERTIFICATES"]:
            current_sec = "certifications"
            continue

        if current_sec in sections:
            sections[current_sec].append(line)

    summary_text = "\n".join(sections["summary"]).strip()
    skills_text = ", ".join(sections["skills"]).strip() if sections["skills"] else ""
    certs_text = ", ".join(sections["certifications"]).strip() if sections["certifications"] else ""
    
    edu_text = "\n".join(sections["education"]).strip()
    exp_text = "\n".join(sections["experience"]).strip()
    proj_text = "\n".join(sections["projects"]).strip()

    return {
        "personal": {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "linkedin": linkedin,
            "github": github,
            "summary": summary_text,
        },
        "education": {
            "degree": edu_text[:120] if edu_text else "",
            "college": "",
            "graduation_year": "",
            "gpa": "",
        } if edu_text else {},
        "experience": {
            "company": "",
            "role": "",
            "duration": "",
            "responsibilities": exp_text if exp_text else "",
        },
        "skills": skills_text,
        "projects": {
            "project_name": proj_text[:80] if proj_text else "",
            "description": proj_text,
            "technologies": "",
        } if proj_text else {},
        "certifications": certs_text,
        "achievements": "",
        "languages": "",
    }

