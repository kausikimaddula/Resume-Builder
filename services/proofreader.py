"""Service for proofreading resumes using OpenAI or heuristic rules to detect spelling and grammatical issues."""

from __future__ import annotations

import json
import re
from typing import Any
from openai import OpenAI, OpenAIError

# Reusable module-level prompts for the proofreader
PROOFREADER_SYSTEM_PROMPT = (
    "You are a professional resume proofreader and copy editor assistant.\n"
    "Your task is to analyze the provided resume text for any grammar mistakes, spelling mistakes, "
    "punctuation errors, repeated words, weak wording, passive voice constructs, and inconsistent tenses.\n\n"
    "You must return a valid JSON object containing exactly one key 'mistakes', which maps to a list of objects.\n"
    "Each object in the 'mistakes' list must contain exactly these four keys:\n"
    "1. 'original': The complete original sentence or phrase containing the mistake.\n"
    "2. 'correction': The corrected version of that complete sentence or phrase.\n"
    "3. 'reason': A brief, helpful explanation of the rule violated (e.g. grammar, typo, passive voice, weak word choice).\n"
    "4. 'mistake_word': The exact substring within the original sentence that is incorrect or sub-optimal.\n\n"
    "If no mistakes are found, return the list as empty."
)

PROOFREADER_USER_PROMPT_TEMPLATE = (
    "Please proofread the following resume text:\n\n"
    "--- START RESUME ---\n"
    "{resume_text}\n"
    "--- END RESUME ---\n"
)


class ProofreaderError(Exception):
    """Raised when proofreading analysis fails."""


def proofread_resume(
    *,
    resume_text: str,
    api_key: str,
    model: str,
) -> dict[str, Any]:
    """Review resume text for grammar and spelling errors. Calls OpenAI or falls back to local heuristics."""
    if not resume_text or not resume_text.strip():
        raise ProofreaderError("Resume text is empty. Cannot perform proofreading analysis.")

    # Fallback to local heuristic analyzer if key is missing
    if not api_key:
        return _proofread_heuristics(resume_text)

    client = OpenAI(api_key=api_key)
    user_prompt = PROOFREADER_USER_PROMPT_TEMPLATE.format(resume_text=resume_text)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": PROOFREADER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
    except OpenAIError as error:
        raise ProofreaderError(f"OpenAI request failed: {error}") from error

    raw_text = response.choices[0].message.content or ""
    if not raw_text:
        raise ProofreaderError("OpenAI returned an empty response.")

    result = _parse_proofreader_response(raw_text)
    result["analysis_type"] = "AI Assessment"
    return result


def _parse_proofreader_response(raw_text: str) -> dict[str, Any]:
    """Clean and parse JSON from OpenAI response for proofreader."""
    cleaned = raw_text.strip()
    fenced = re.search(r"```(json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(2).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise ProofreaderError("OpenAI returned content that was not valid JSON.") from error

    if not isinstance(parsed, dict) or "mistakes" not in parsed:
        raise ProofreaderError("OpenAI response matches incorrect JSON schema (missing 'mistakes').")

    mistakes = parsed["mistakes"]
    if not isinstance(mistakes, list):
        mistakes = [mistakes] if mistakes else []

    verified_mistakes = []
    required_keys = ["original", "correction", "reason", "mistake_word"]

    for idx, mistake in enumerate(mistakes):
        if not isinstance(mistake, dict):
            continue
        # Ensure all required keys exist
        is_valid = True
        for key in required_keys:
            if key not in mistake:
                is_valid = False
                break
        if is_valid:
            verified_mistakes.append({
                "original": str(mistake["original"]),
                "correction": str(mistake["correction"]),
                "reason": str(mistake["reason"]),
                "mistake_word": str(mistake["mistake_word"]),
            })

    return {"mistakes": verified_mistakes}


def _proofread_heuristics(resume_text: str) -> dict[str, Any]:
    """Fallback local scanner to detect double words, passive voice, weak choices, and simple typos."""
    mistakes = []
    # Split text into sentences using simple regex
    sentences = re.split(r"(?<=[.!?])\s+", resume_text)

    # Heuristic matching catalogs
    typos = {
        r"\bteh\b": ("the", "Typo: 'teh' is a common spelling mistake for 'the'."),
        r"\brecieve\b": ("receive", "Typo: 'recieve' violates the 'i before e except after c' spelling rule."),
        r"\bseperate\b": ("separate", "Typo: 'seperate' is misspelled. Correct spelling is 'separate'."),
        r"\bdefinately\b": ("definitely", "Typo: 'definately' is misspelled. Correct spelling is 'definitely'."),
    }

    double_word_pattern = re.compile(r"\b(\w+)\s+\1\b", re.IGNORECASE)
    passive_pattern = re.compile(r"\b(was|were|been)\s+(\w+ed|developed|created|managed|designed)\s+by\b", re.IGNORECASE)
    weak_verbs = {
        "helped": "assisted / facilitated / supported",
        "worked on": "engineered / spearheaded / led",
        "handled": "executed / directed / managed",
    }

    for sentence in sentences:
        sentence_stripped = sentence.strip()
        if not sentence_stripped:
            continue

        # 1. Spelling/Typo Matches
        for pattern, (correction_word, explanation) in typos.items():
            match = re.search(pattern, sentence_stripped, re.IGNORECASE)
            if match:
                mistake_word = match.group(0)
                corrected_sentence = re.sub(pattern, correction_word, sentence_stripped, flags=re.IGNORECASE)
                mistakes.append({
                    "original": sentence_stripped,
                    "correction": corrected_sentence,
                    "reason": explanation,
                    "mistake_word": mistake_word,
                })

        # 2. Repeated Consecutive Words
        match_dw = double_word_pattern.search(sentence_stripped)
        if match_dw:
            mistake_word = match_dw.group(0)
            repeated = match_dw.group(1)
            corrected_sentence = double_word_pattern.sub(repeated, sentence_stripped)
            mistakes.append({
                "original": sentence_stripped,
                "correction": corrected_sentence,
                "reason": f"Repeated words: Recurrent word '{repeated}' detected consecutively.",
                "mistake_word": mistake_word,
            })

        # 3. Passive Voice Formats
        match_pv = passive_pattern.search(sentence_stripped)
        if match_pv:
            mistake_word = match_pv.group(0)
            verb = match_pv.group(2)
            # Make a simple active suggestion (e.g. Led project instead of was led by)
            mistakes.append({
                "original": sentence_stripped,
                "correction": f"[Active Suggestion]: Rephrase to use direct verbs (e.g. 'I {verb} ...')",
                "reason": f"Passive voice construct: '{mistake_word}' sounds passive. Use active voice verbs (e.g. 'spearheaded', 'managed') for stronger resume impacts.",
                "mistake_word": mistake_word,
            })

        # 4. Weak Word Usages
        for weak_word, suggestions in weak_verbs.items():
            pattern = rf"\b{weak_word}\b"
            match_ww = re.search(pattern, sentence_stripped, re.IGNORECASE)
            if match_ww:
                mistake_word = match_ww.group(0)
                corrected_sentence = re.sub(pattern, suggestions.split(" / ")[0], sentence_stripped, flags=re.IGNORECASE)
                mistakes.append({
                    "original": sentence_stripped,
                    "correction": corrected_sentence,
                    "reason": f"Weak wording: '{mistake_word}' is generic. Consider replacing it with a more descriptive action verb, such as: {suggestions}.",
                    "mistake_word": mistake_word,
                })

    return {
        "mistakes": mistakes,
        "analysis_type": "Local Diagnostics",
    }
