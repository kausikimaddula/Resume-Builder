"""Service for analyzing resumes using OpenAI to generate an ATS compatibility score and feedback."""

from __future__ import annotations

import json
import re
from typing import Any
from openai import OpenAI, OpenAIError

# Module-level constant prompts to keep them reusable
ATS_SYSTEM_PROMPT = (
    "You are an advanced Application Tracking System (ATS) simulator and professional resume reviewer.\n"
    "Your objective is to analyze the formatting, section completeness, keyword usage, readability, "
    "action verbs, contact information, and experience quality of the provided resume text.\n\n"
    "You must return a valid JSON object containing exactly four keys:\n"
    "1. 'score': An integer from 0 to 100 representing the overall ATS compatibility and quality score.\n"
    "2. 'strengths': A list of strings highlighting the strong points of the resume (e.g. good formatting clues, strong action words, complete contact details).\n"
    "3. 'weaknesses': A list of strings indicating areas where the resume falls short (e.g. poor readability, passive language, lack of sections, missing contact metrics).\n"
    "4. 'suggestions': A list of actionable suggestions and recommendations for improvement to maximize the ATS score.\n\n"
    "Assess the resume rigorously, as a real ATS processor and hiring manager would."
)

ATS_USER_PROMPT_TEMPLATE = (
    "Please analyze the following resume text:\n\n"
    "--- START RESUME ---\n"
    "{resume_text}\n"
    "--- END RESUME ---\n"
)


class AtsAnalysisError(Exception):
    """Raised when ATS score analysis fails."""


def analyze_resume_ats(
    *,
    resume_text: str,
    api_key: str,
    model: str,
) -> dict[str, Any]:
    """Analyze resume text compatibility using OpenAI and return structured score details."""
    if not resume_text or not resume_text.strip():
        raise AtsAnalysisError("Resume text is empty. Cannot perform ATS analysis.")

    # Fallback to local heuristic analyzer if key is missing
    if not api_key:
        return _analyze_resume_heuristics(resume_text)

    client = OpenAI(api_key=api_key)
    user_prompt = ATS_USER_PROMPT_TEMPLATE.format(resume_text=resume_text)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": ATS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
    except OpenAIError as error:
        raise AtsAnalysisError(f"OpenAI request failed: {error}") from error

    raw_text = response.choices[0].message.content or ""
    if not raw_text:
        raise AtsAnalysisError("OpenAI returned an empty response.")

    result = _parse_ats_response(raw_text)
    result["analysis_type"] = "AI Assessment"
    return result


def _analyze_resume_heuristics(resume_text: str) -> dict[str, Any]:
    """Fallback local analyzer that calculates a heuristic ATS score and review notes."""
    score = 40
    strengths = []
    weaknesses = []
    suggestions = []

    words = resume_text.split()
    word_count = len(words)
    if word_count > 300:
        score += 15
        strengths.append("Word count is appropriate for a standard professional layout.")
    elif word_count > 100:
        score += 5
        weaknesses.append("Content length is somewhat short (less than 300 words).")
        suggestions.append("Expand on your roles and bullet points to provide more details about your achievements.")
    else:
        weaknesses.append("Extremely short content. The resume may be missing critical details.")
        suggestions.append("Add detailed work history, projects, and education sections.")

    # Check for contact info
    has_email = "@" in resume_text
    has_phone = any(char.isdigit() for char in resume_text) and len([c for c in resume_text if c.isdigit()]) >= 7
    if has_email and has_phone:
        score += 15
        strengths.append("Contains complete contact info (email and phone number parsed).")
    else:
        if not has_email:
            weaknesses.append("Missing email address.")
            suggestions.append("Add a professional email address to the header section.")
        if not has_phone:
            weaknesses.append("Missing phone contact information.")
            suggestions.append("Provide a phone number where hiring managers can reach you.")

    # Check for sections
    sections = {
        "experience": ["experience", "work history", "employment", "professional background"],
        "education": ["education", "academic", "university", "college", "degree"],
        "skills": ["skills", "technologies", "expertise", "competencies"],
        "projects": ["projects", "personal projects", "academic projects"],
    }
    
    found_sections = []
    text_lower = resume_text.lower()
    for name, keywords in sections.items():
        if any(keyword in text_lower for keyword in keywords):
            found_sections.append(name)
            score += 10
        else:
            weaknesses.append(f"Missing distinct '{name.capitalize()}' section header.")
            suggestions.append(f"Create a dedicated and clearly labeled section for '{name.capitalize()}'.")

    if len(found_sections) == len(sections):
        strengths.append("Excellent structural completeness with all core sections present.")
    elif len(found_sections) >= 2:
        strengths.append("Includes essential components like experience and education.")

    # Check for action verbs
    action_verbs = ["led", "developed", "designed", "implemented", "managed", "built", "created", "spearheaded", "optimized", "increased", "decreased", "engineered"]
    found_verbs = [verb for verb in action_verbs if verb in text_lower]
    if len(found_verbs) >= 4:
        score += 10
        strengths.append(f"Good utilization of action verbs (e.g. {', '.join(found_verbs[:3])}).")
    else:
        weaknesses.append("Experience bullet points rely on passive description rather than action verbs.")
        suggestions.append("Begin experience bullet points with strong power/action verbs (e.g. 'Spearheaded', 'Optimized', 'Engineered').")

    # Add a fallback warning suggestion to enable AI
    suggestions.append("Configure your OPENAI_API_KEY in the environment to unlock comprehensive AI-powered ATS diagnostics.")

    score = max(0, min(100, score))

    return {
        "score": score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
        "analysis_type": "Local Diagnostics",
    }


def _parse_ats_response(raw_text: str) -> dict[str, Any]:
    """Clean and parse JSON from OpenAI response."""
    cleaned = raw_text.strip()
    fenced = re.search(r"```(json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(2).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise AtsAnalysisError("OpenAI returned content that was not valid JSON.") from error

    if not isinstance(parsed, dict):
        raise AtsAnalysisError("OpenAI response is not a valid JSON object.")

    # Validate required keys
    required_keys = ["score", "strengths", "weaknesses", "suggestions"]
    for key in required_keys:
        if key not in parsed:
            raise AtsAnalysisError(f"Missing required key in ATS analysis JSON: '{key}'")

    # Coerce/verify types
    try:
        parsed["score"] = int(parsed["score"])
        parsed["score"] = max(0, min(100, parsed["score"]))
    except (ValueError, TypeError):
        parsed["score"] = 0

    for key in ["strengths", "weaknesses", "suggestions"]:
        if not isinstance(parsed[key], list):
            parsed[key] = [str(parsed[key])] if parsed[key] else []
        else:
            parsed[key] = [str(item) for item in parsed[key]]

    return parsed
