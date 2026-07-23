"""Centralized AI service module handling all OpenAI API calls, client initialization, and JSON parsing."""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)


class OpenAiServiceError(Exception):
    """Base exception for failures occurring during OpenAI API requests or response parsing."""


def create_client(api_key: str) -> OpenAI:
    """Instantiate and return an OpenAI client using the supplied API key."""
    if not api_key:
        raise OpenAiServiceError("OpenAI API key is missing or empty.")
    return OpenAI(api_key=api_key)


def parse_and_clean_json(raw_text: str) -> dict[str, Any]:
    """Clean markdown code fences and parse JSON string into a python dictionary."""
    if not raw_text or not raw_text.strip():
        raise OpenAiServiceError("OpenAI returned an empty response.")

    cleaned = raw_text.strip()
    fenced = re.search(r"```(json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(2).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise OpenAiServiceError("OpenAI returned content that was not valid JSON.") from error

    if not isinstance(parsed, dict):
        raise OpenAiServiceError("OpenAI response is not a valid JSON object.")

    return parsed


def execute_json_chat_completion(
    *,
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    model: str,
    client: OpenAI | None = None,
) -> dict[str, Any]:
    """Execute an OpenAI Chat Completion request with json_object format and return parsed dictionary.
    
    If `client` is not supplied, a new OpenAI client will be instantiated with `api_key`.
    """
    if client is None:
        client = create_client(api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
    except OpenAIError as error:
        logger.error(f"OpenAI chat completion failed: {error}")
        raise OpenAiServiceError(f"OpenAI request failed: {error}") from error

    raw_text = response.choices[0].message.content or ""
    return parse_and_clean_json(raw_text)
