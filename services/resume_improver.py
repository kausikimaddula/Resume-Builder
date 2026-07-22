"""Service for providing AI-driven section-wise resume improvement suggestions."""

from __future__ import annotations

import json
import re
from typing import Any
from openai import OpenAI, OpenAIError

IMPROVER_SYSTEM_PROMPT = (
    "You are an expert resume writer, hiring manager, and ATS optimization specialist.\n"
    "Your goal is to analyze a candidate's resume and generate actionable, section-wise improvement suggestions.\n\n"
    "You must return a valid JSON object containing exactly six section keys:\n"
    "1. 'project_descriptions': A list of objects with keys 'original', 'improved', and 'reason'. Enhance impact, quantify achievements, and highlight technologies.\n"
    "2. 'experience_wording': A list of objects with keys 'original', 'improved', and 'impact'. Upgrade weak bullet points into high-impact accomplishment statements.\n"
    "3. 'summaries': A list of objects with keys 'title' and 'text'. Provide compelling executive summary variations (e.g. Impact-Driven, Technical Focus, Executive Overview).\n"
    "4. 'skills_ordering': A list of objects with keys 'category', 'ordered_skills', and 'rationale'. Categorize and order skills logically (e.g., Core technical first, tools later).\n"
    "5. 'action_verbs': A list of objects with keys 'weak_verb', 'power_verb', and 'example'. Identify passive/overused verbs in the resume and suggest high-power action verbs.\n"
    "6. 'ats_optimization': A list of objects with keys 'area', 'suggestion', and 'importance'. Provide formatting, keyword placement, and header optimization tips to maximize ATS parser compatibility.\n\n"
    "Keep suggestions concrete, professional, and tailored to the provided resume and optional target role."
)

IMPROVER_USER_PROMPT_TEMPLATE = (
    "Please provide comprehensive resume improvement suggestions for the following resume:\n\n"
    "{target_role_info}"
    "--- START RESUME ---\n"
    "{resume_text}\n"
    "--- END RESUME ---\n"
)


class ResumeImproverError(Exception):
    """Raised when resume improvement analysis fails."""


def improve_resume(
    *,
    resume_text: str,
    target_role: str = "",
    api_key: str = "",
    model: str = "",
) -> dict[str, Any]:
    """Analyze resume text and return section-wise improvement recommendations."""
    if not resume_text or not resume_text.strip():
        raise ResumeImproverError("Resume text is empty. Cannot generate improvement suggestions.")

    # Fallback to local heuristic improver if API key is not configured
    if not api_key:
        return _improve_resume_heuristics(resume_text, target_role)

    client = OpenAI(api_key=api_key)
    target_role_info = f"Target Job Role: {target_role}\n\n" if target_role and target_role.strip() else ""
    user_prompt = IMPROVER_USER_PROMPT_TEMPLATE.format(
        target_role_info=target_role_info,
        resume_text=resume_text,
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": IMPROVER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
    except OpenAIError as error:
        raise ResumeImproverError(f"OpenAI request failed: {error}") from error

    raw_text = response.choices[0].message.content or ""
    if not raw_text:
        raise ResumeImproverError("OpenAI returned an empty response.")

    result = _parse_improver_response(raw_text)
    result["analysis_type"] = "AI Powered Assessment"
    return result


def _parse_improver_response(raw_text: str) -> dict[str, Any]:
    """Parse JSON output from OpenAI and validate section schema."""
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as error:
        raise ResumeImproverError("AI response was not valid JSON.") from error

    if not isinstance(data, dict):
        raise ResumeImproverError("AI response root must be a JSON object.")

    required_keys = [
        "project_descriptions",
        "experience_wording",
        "summaries",
        "skills_ordering",
        "action_verbs",
        "ats_optimization",
    ]

    for key in required_keys:
        if key not in data or not isinstance(data[key], list):
            raise ResumeImproverError(f"AI response is missing required section key: '{key}'.")

    return data


def _improve_resume_heuristics(resume_text: str, target_role: str = "") -> dict[str, Any]:
    """Fallback local analyzer that creates structured section-wise improvement suggestions."""
    role_suffix = f" for {target_role}" if target_role and target_role.strip() else ""
    
    # 1. Project Descriptions
    project_descriptions = [
        {
            "original": "Built a web application using Flask and Python.",
            "improved": f"Architected and deployed a responsive web application{role_suffix} using Flask and Python, reducing page load latency by 35% and supporting concurrent users.",
            "reason": "Quantifies performance gains, highlights architectural leadership, and specifies technical scale.",
        },
        {
            "original": "Worked on database design and API endpoints.",
            "improved": "Engineered scalable RESTful API endpoints and optimized SQL schema indexes, boosting query execution efficiency by 40%.",
            "reason": "Replaces generic action words ('worked on') with power verbs ('engineered', 'optimized') and measurable impact.",
        },
    ]

    # 2. Experience Wording
    experience_wording = [
        {
            "original": "Responsible for managing project schedules and team meetings.",
            "improved": "Spearheaded cross-functional sprint planning and daily standups, ensuring on-time delivery across 4 major release cycles.",
            "reason": "Shifts focus from passive job responsibilities to active leadership and delivered outcomes.",
        },
        {
            "original": "Handled customer inquiries and resolved technical issues.",
            "improved": "Resolved 50+ complex technical customer inquiries weekly with a 98% first-contact resolution rate.",
            "reason": "Injects concrete metrics (50+ weekly, 98% resolution rate) to demonstrate productivity and customer satisfaction.",
        },
    ]

    # 3. Summaries
    summaries = [
        {
            "title": "Impact-Driven Professional Summary",
            "text": f"Results-focused Software Engineer{role_suffix} with expertise in building scalable applications, optimizing workflow automation, and delivering high-quality user experiences. Proven track record of improving system efficiency and driving technical excellence.",
        },
        {
            "title": "Technical & Core Strengths Summary",
            "text": f"Versatile Technical Specialist{role_suffix} adept in modern web stacks, API design, data modeling, and cloud deployments. Passionate about writing clean, maintainable code and solving complex engineering challenges.",
        },
    ]

    # 4. Skills Ordering
    skills_ordering = [
        {
            "category": "Core Engineering & Languages",
            "ordered_skills": "Python, JavaScript, SQL, HTML5/CSS3, TypeScript",
            "rationale": "Place high-demand primary programming languages at the top of your Skills section for quick recruiter scanning.",
        },
        {
            "category": "Frameworks & Libraries",
            "ordered_skills": "Flask, React.js, Node.js, Bootstrap, Tailwind CSS",
            "rationale": "Group web frameworks immediately below core languages to demonstrate full-stack capabilities.",
        },
        {
            "category": "Tools & Infrastructure",
            "ordered_skills": "Git, Docker, PostgreSQL, Linux, REST APIs",
            "rationale": "List developer tools, databases, and DevOps utilities in a distinct secondary category.",
        },
    ]

    # 5. Action Verbs
    action_verbs = [
        {
            "weak_verb": "Worked on / Helped",
            "power_verb": "Architected / Facilitated / Spearheaded",
            "example": "Replace 'Helped design the database' with 'Architected high-availability database schema'.",
        },
        {
            "weak_verb": "Managed / Handled",
            "power_verb": "Orchestrated / Directing / Oversaw",
            "example": "Replace 'Managed team tasks' with 'Orchestrated multi-phase feature rollout across engineering teams'.",
        },
        {
            "weak_verb": "Made / Created",
            "power_verb": "Engineered / Pioneered / Implemented",
            "example": "Replace 'Made an automated script' with 'Engineered automated CI/CD deployment pipelines'.",
        },
    ]

    # 6. ATS Optimization
    ats_optimization = [
        {
            "area": "Standard Section Headings",
            "suggestion": "Ensure section headers use universal labels like 'Work Experience', 'Education', 'Skills', and 'Projects' so ATS software parses them correctly.",
            "importance": "High",
        },
        {
            "area": "Action-Keyword Density",
            "suggestion": f"Incorporate industry-standard keywords related to {target_role or 'your field'} (e.g. Agile, REST APIs, Microservices) naturally within experience bullet points.",
            "importance": "High",
        },
        {
            "area": "Clean Formatting & File Type",
            "suggestion": "Avoid text boxes, multi-column tables, or complex graphic elements that can scramble automated ATS parsers. Submit standard DOCX or text-based PDF files.",
            "importance": "Medium",
        },
    ]

    return {
        "project_descriptions": project_descriptions,
        "experience_wording": experience_wording,
        "summaries": summaries,
        "skills_ordering": skills_ordering,
        "action_verbs": action_verbs,
        "ats_optimization": ats_optimization,
        "analysis_type": "Local Diagnostics (Offline)",
    }
