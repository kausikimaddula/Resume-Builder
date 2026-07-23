"""Service for analyzing resumes using OpenAI to generate an ATS compatibility score and feedback."""

from __future__ import annotations

import re
from typing import Any

# Import shared AI service helpers and centralized prompts
from services.openai_service import OpenAI, OpenAiServiceError, execute_json_chat_completion
from services.prompts import ATS_SYSTEM_PROMPT, ATS_USER_PROMPT_TEMPLATE


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
        raw_json = execute_json_chat_completion(
            system_prompt=ATS_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            api_key=api_key,
            model=model,
            client=client,
        )
    except OpenAiServiceError as error:
        raise AtsAnalysisError(str(error)) from error

    result = _validate_ats_schema(raw_json)
    result["analysis_type"] = "AI Assessment"
    return result


def _validate_ats_schema(parsed: dict[str, Any]) -> dict[str, Any]:
    """Validate and coerce required keys from ATS analysis JSON response."""
    required_keys = ["score", "strengths", "weaknesses", "suggestions"]
    for key in required_keys:
        if key not in parsed:
            raise AtsAnalysisError(f"Missing required key in ATS analysis JSON: '{key}'")

    # Coerce/verify score
    try:
        parsed["score"] = int(parsed["score"])
        parsed["score"] = max(0, min(100, parsed["score"]))
    except (ValueError, TypeError):
        parsed["score"] = 0

    # Ensure list types for strings
    for key in ["strengths", "weaknesses", "suggestions"]:
        if not isinstance(parsed[key], list):
            parsed[key] = [str(parsed[key])] if parsed[key] else []
        else:
            parsed[key] = [str(item) for item in parsed[key]]

    return parsed


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
