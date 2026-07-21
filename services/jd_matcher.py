"""Service to analyze resume text against a job description using OpenAI, generating match details and suggestions."""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)

# Reusable prompts
JD_MATCHER_SYSTEM_PROMPT = (
    "You are an expert recruiter and talent acquisition professional who specializes in comparing candidates' resumes against job descriptions.\n"
    "Your goal is to compare the provided Resume and Job Description texts, and analyze the candidate's alignment, matching skills, gaps, keywords, certifications, and areas for improvement.\n\n"
    "You must return a valid JSON object containing exactly six keys:\n"
    "1. 'match_percentage': An integer between 0 and 100 representing how well the resume matches the requirements of the job description.\n"
    "2. 'matching_skills': A list of strings showing the skills, technologies, or tools present in both the resume and the job description.\n"
    "3. 'missing_skills': A list of strings showing critical skills, technologies, or tools mentioned in the job description that are NOT found or are weak in the resume.\n"
    "4. 'recommended_keywords': A list of strings listing important keywords, buzzwords, or technical terms from the job description that the candidate should add or emphasize in their resume.\n"
    "5. 'important_certifications_missing': A list of strings showing industry-standard certifications requested or implied by the job description but not present on the resume.\n"
    "6. 'recommended_improvements': A list of actionable suggestions and strategies to tailor the resume and make it a stronger fit for this job description.\n\n"
    "Respond ONLY with a valid JSON object. Do not include any explanations before or after the JSON."
)

JD_MATCHER_USER_PROMPT_TEMPLATE = (
    "Please compare the following resume and job description:\n\n"
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

    # Extract potential keywords/skills from the Job Description
    # Standard technical keywords we can look for
    common_skills = [
        "python", "javascript", "typescript", "java", "c++", "c#", "ruby", "go", "rust",
        "react", "node", "express", "angular", "vue", "django", "flask", "fastapi", "spring",
        "html", "css", "sql", "nosql", "mongodb", "postgresql", "mysql", "redis",
        "aws", "azure", "gcp", "docker", "kubernetes", "git", "ci/cd", "agile", "scrum",
        "communication", "leadership", "analytics", "statistics", "machine learning", "deep learning",
        "openai", "pytorch", "tensorflow", "system design", "microservices"
    ]

    jd_skills = {skill for skill in common_skills if _word_in_text(skill, jd_lower)}
    resume_skills = {skill for skill in common_skills if _word_in_text(skill, resume_lower)}

    matching_skills_set = jd_skills.intersection(resume_skills)
    missing_skills_set = jd_skills.difference(resume_skills)

    matching_skills = sorted(list(matching_skills_set))
    missing_skills = sorted(list(missing_skills_set))

    # Basic match percentage calculation based on skill overlap
    if jd_skills:
        match_percentage = int((len(matching_skills_set) / len(jd_skills)) * 100)
    else:
        # Default fallback match calculation based on overall common word sets
        jd_words = set(re.findall(r"\b\w{4,15}\b", jd_lower))
        res_words = set(re.findall(r"\b\w{4,15}\b", resume_lower))
        overlap = jd_words.intersection(res_words)
        if jd_words:
            match_percentage = int((len(overlap) / len(jd_words)) * 100) 
        else:
            match_percentage = 50

    # Ensure match_percentage is between normal bounds
    match_percentage = max(10, min(95, match_percentage))

    # Recommended keywords to add
    recommended_keywords = [skill.upper() for skill in missing_skills[:5]] if missing_skills else ["DEVELOPER", "ENGINEER", "TEAM PLAYER"]

    # Simple heuristic to identify possible missing certifications
    common_certs = ["aws", "certified", "pmp", "scrum master", "ccna", "comptia", "cissp"]
    jd_certs = [cert for cert in common_certs if cert in jd_lower]
    resume_certs = [cert for cert in common_certs if cert in resume_lower]
    missing_certs_set = set(jd_certs).difference(set(resume_certs))

    important_certifications_missing = []
    for cert in missing_certs_set:
        if cert == "aws":
            important_certifications_missing.append("AWS Certified Cloud Practitioner/Solutions Architect")
        elif cert == "scrum master":
            important_certifications_missing.append("Certified ScrumMaster (CSM)")
        elif cert == "pmp":
            important_certifications_missing.append("Project Management Professional (PMP)")
        else:
            important_certifications_missing.append(f"{cert.upper()} Certification")

    if not important_certifications_missing:
        # Fallback placeholder list to keep it constructive
        important_certifications_missing = ["Relevant Professional Certifications based on role seniority"]

    # Recommended improvements
    recommended_improvements = [
        "Include more quantifiable metrics in your resume bullets to showcase impact (e.g. 'Improved efficiency by 20%').",
        f"Make sure to mention critical competencies matching the JD, specifically: {', '.join(missing_skills[:3])}." if missing_skills else "Align your summary statement to focus on the company's core technology stack.",
        "Add a dedicated skills section separating frontend, backend, and platform/database tools."
    ]

    # Add a fallback warning suggestion to enable AI
    recommended_improvements.append(
        "Configure your OPENAI_API_KEY in the environment to unlock comprehensive AI-powered matching diagnostics."
    )

    return {
        "match_percentage": match_percentage,
        "matching_skills": [s.capitalize() for s in matching_skills] if matching_skills else ["General Industry Skills"],
        "missing_skills": [s.capitalize() for s in missing_skills] if missing_skills else ["No obvious missing skills found"],
        "recommended_keywords": recommended_keywords,
        "important_certifications_missing": important_certifications_missing,
        "recommended_improvements": recommended_improvements,
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
        "missing_skills",
        "recommended_keywords",
        "important_certifications_missing",
        "recommended_improvements",
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
        "missing_skills",
        "recommended_keywords",
        "important_certifications_missing",
        "recommended_improvements",
    ]
    for key in list_keys:
        if not isinstance(parsed[key], list):
            parsed[key] = [str(parsed[key])] if parsed[key] else []
        else:
            parsed[key] = [str(item) for item in parsed[key]]

    return parsed
