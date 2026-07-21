"""Service to analyze resume text against a job description using OpenAI, generating match details and suggestions."""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)

# Reusable prompts - Tailored for GPT-4o-mini
JD_MATCHER_SYSTEM_PROMPT = (
    "You are an expert recruiter and talent acquisition professional. Compare the provided Resume and Job Description.\n"
    "Identify key alignments, gaps, and actionable recommendations. Be highly concise and specific.\n\n"
    "You must return a valid JSON object containing exactly these eight keys:\n"
    "1. 'match_percentage': An integer between 0 and 100.\n"
    "2. 'matching_skills': A list of matching technical/professional skills found in both.\n"
    "3. 'missing_technical_skills': A list of top technical skills/tools from the job description missing or weak in the resume.\n"
    "4. 'missing_soft_skills': A list of top soft skills/competencies from the job description missing or weak in the resume.\n"
    "5. 'recommended_keywords': A list of important acronyms, terminology, or keywords from the job description to add.\n"
    "6. 'recommended_certifications': A list of certifications mentioned, implied, or highly recommended for the role that the resume lacks.\n"
    "7. 'recommended_projects': A list of 2-3 specific, concrete projects the candidate can build to prove competency in the missing technical skills.\n"
    "8. 'learning_roadmap': A list of sequential, concise steps (3-4 steps max) to acquire the missing skills and close the gap.\n\n"
    "Respond ONLY with a valid JSON object."
)

JD_MATCHER_USER_PROMPT_TEMPLATE = (
    "Compare this resume and job description using GPT-4o-mini:\n\n"
    "--- START RESUME ---\n"
    "{resume_text}\n"
    "--- END RESUME ---\n\n"
    "--- START JOB DESCRIPTION ---\n"
    "{jd_text}\n"
    "--- END JOB DESCRIPTION ---\n"
)


class JdMatcherError(Exception):
    """Raised when Resume vs JD matching fails."""


def match_resume_to_jd(
    *,
    resume_text: str,
    jd_text: str,
    api_key: str,
    model: str,
) -> dict[str, Any]:
    """Compare a resume text against a job description using OpenAI, returning matching metrics and feedback."""
    if not resume_text or not resume_text.strip():
        raise JdMatcherError("Resume text is empty. Cannot perform comparison.")
    if not jd_text or not jd_text.strip():
        raise JdMatcherError("Job description text is empty. Cannot perform comparison.")

    # Fallback to local heuristics if API key is missing
    if not api_key:
        logger.info("OpenAI API key not configured. Falling back to local diagnostics.")
        return _match_resume_to_jd_heuristics(resume_text, jd_text)

    client = OpenAI(api_key=api_key)
    user_prompt = JD_MATCHER_USER_PROMPT_TEMPLATE.format(
        resume_text=resume_text, jd_text=jd_text
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": JD_MATCHER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
    except OpenAIError as error:
        raise JdMatcherError(f"OpenAI request failed: {error}") from error

    raw_text = response.choices[0].message.content or ""
    if not raw_text:
        raise JdMatcherError("OpenAI returned an empty response.")

    result = _parse_matcher_response(raw_text)
    result["analysis_type"] = "AI Assessment"
    return result


def _match_resume_to_jd_heuristics(resume_text: str, jd_text: str) -> dict[str, Any]:
    """Fallback local analyzer that calculates mechanical word overlaps between resume and JD."""
    resume_lower = resume_text.lower()
    jd_lower = jd_text.lower()

    # Standard technical keywords we can look for
    tech_skills = [
        "python", "javascript", "typescript", "java", "c++", "c#", "ruby", "go", "rust",
        "react", "node", "express", "angular", "vue", "django", "flask", "fastapi", "spring",
        "html", "css", "sql", "nosql", "mongodb", "postgresql", "mysql", "redis",
        "aws", "azure", "gcp", "docker", "kubernetes", "git", "ci/cd",
        "machine learning", "deep learning", "openai", "pytorch", "tensorflow", "system design", "microservices"
    ]

    soft_skills = [
        "leadership", "communication", "team player", "agile", "scrum", "analytics", "statistics",
        "collaboration", "problem solving", "critical thinking", "mentoring", "negotiation"
    ]

    jd_tech = {skill for skill in tech_skills if _word_in_text(skill, jd_lower)}
    resume_tech = {skill for skill in tech_skills if _word_in_text(skill, resume_lower)}

    matching_tech = jd_tech.intersection(resume_tech)
    missing_tech = jd_tech.difference(resume_tech)

    jd_soft = {skill for skill in soft_skills if _word_in_text(skill, jd_lower)}
    resume_soft = {skill for skill in soft_skills if _word_in_text(skill, resume_lower)}

    matching_soft = jd_soft.intersection(resume_soft)
    missing_soft = jd_soft.difference(resume_soft)

    # Union matching
    matching_skills = sorted(list(matching_tech.union(matching_soft)))

    # Basic match percentage calculation based on skill overlap
    total_jd_expectations = len(jd_tech) + len(jd_soft)
    total_matching = len(matching_tech) + len(matching_soft)

    if total_jd_expectations:
        match_percentage = int((total_matching / total_jd_expectations) * 100)
    else:
        match_percentage = 45

    # Clamp match percentage
    match_percentage = max(15, min(95, match_percentage))

    # Missing technical skills list
    missing_tech_list = sorted(list(missing_tech))
    if not missing_tech_list:
        missing_tech_list = ["No significant technical skill gaps detected"]

    # Missing soft skills list
    missing_soft_list = sorted(list(missing_soft))
    if not missing_soft_list:
        missing_soft_list = ["No significant soft skill gaps detected"]

    # Keywords list
    recommended_keywords = [skill.upper() for skill in missing_tech_list[:5]]

    # Certs recommendation
    common_certs = ["aws", "certified", "pmp", "scrum master", "ccna", "comptia", "cissp", "cka"]
    jd_certs = [cert for cert in common_certs if cert in jd_lower]
    resume_certs = [cert for cert in common_certs if cert in resume_lower]
    missing_certs_set = set(jd_certs).difference(set(resume_certs))

    recommended_certifications = []
    for cert in missing_certs_set:
        if cert == "aws":
            recommended_certifications.append("AWS Solutions Architect Associate")
        elif cert == "cka":
            recommended_certifications.append("Certified Kubernetes Administrator (CKA)")
        elif cert == "scrum master":
            recommended_certifications.append("Certified ScrumMaster (CSM)")
        elif cert == "pmp":
            recommended_certifications.append("Project Management Professional (PMP)")
        else:
            recommended_certifications.append(f"{cert.upper()} Certification")

    if not recommended_certifications:
        recommended_certifications = ["Standard professional credentials related to the job type"]

    # Project recommendation based on missing technical skills
    recommended_projects = []
    if missing_tech:
        primary_missing = list(missing_tech)[0]
        recommended_projects.append(
            f"Build a clean end-to-end GitHub project that heavily features {primary_missing.capitalize()} setup and deployment."
        )
        if len(missing_tech) > 1:
            second_missing = list(missing_tech)[1]
            recommended_projects.append(
                f"Develop a small microservices mock application connecting {primary_missing.capitalize()} with {second_missing.capitalize()}."
            )
    else:
        recommended_projects.append(
            "Construct a fully-featured full-stack project demonstrating production-grade testing and automation."
        )

    # Learning roadmap based on missing keys
    learning_roadmap = []
    steps = 1
    if missing_tech:
        for tech in list(missing_tech)[:2]:
            learning_roadmap.append(f"Step {steps}: Complete tutorials and build test files focusing on {tech.capitalize()}.")
            steps += 1
    if missing_soft:
        primary_soft = list(missing_soft)[0]
        learning_roadmap.append(f"Step {steps}: Read Scrum/Agile guides to adapt to {primary_soft.capitalize()} standards.")
        steps += 1
    
    learning_roadmap.append(f"Step {steps}: Tailor and submit your revised resume matching the targeted JD requirements.")

    # Local warning additions
    learning_roadmap.append("Step Note: Set OPENAI_API_KEY to acquire complete AI personalized roadmap recommendations.")

    return {
        "match_percentage": match_percentage,
        "matching_skills": [s.capitalize() for s in matching_skills] if matching_skills else ["General Domain Competency"],
        "missing_technical_skills": [s.capitalize() for s in missing_tech_list],
        "missing_soft_skills": [s.capitalize() for s in missing_soft_list],
        "recommended_keywords": recommended_keywords,
        "recommended_certifications": recommended_certifications,
        "recommended_projects": recommended_projects,
        "learning_roadmap": learning_roadmap,
        "analysis_type": "Local Diagnostics",
    }


def _word_in_text(word: str, text: str) -> bool:
    """Helper to check if a word/phrase exists in text as a whole word."""
    pattern = r"\b" + re.escape(word) + r"\b"
    return bool(re.search(pattern, text))


def _parse_matcher_response(raw_text: str) -> dict[str, Any]:
    """Clean and parse JSON from OpenAI response."""
    cleaned = raw_text.strip()
    fenced = re.search(r"```(json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(2).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise JdMatcherError("OpenAI returned content that was not valid JSON.") from error

    if not isinstance(parsed, dict):
        raise JdMatcherError("OpenAI response is not a valid JSON object.")

    # Validate required keys
    required_keys = [
        "match_percentage",
        "matching_skills",
        "missing_technical_skills",
        "missing_soft_skills",
        "recommended_keywords",
        "recommended_certifications",
        "recommended_projects",
        "learning_roadmap",
    ]
    for key in required_keys:
        if key not in parsed:
            raise JdMatcherError(f"Missing required key in matching analysis JSON: '{key}'")

    # Coerce match_percentage
    try:
        parsed["match_percentage"] = int(parsed["match_percentage"])
        parsed["match_percentage"] = max(0, min(100, parsed["match_percentage"]))
    except (ValueError, TypeError):
        parsed["match_percentage"] = 0

    # Ensure list types
    list_keys = [
        "matching_skills",
        "missing_technical_skills",
        "missing_soft_skills",
        "recommended_keywords",
        "recommended_certifications",
        "recommended_projects",
        "learning_roadmap",
    ]
    for key in list_keys:
        if not isinstance(parsed[key], list):
            parsed[key] = [str(parsed[key])] if parsed[key] else []
        else:
            parsed[key] = [str(item) for item in parsed[key]]

    return parsed
