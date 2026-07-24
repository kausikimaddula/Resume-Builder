"""Centralized AI service module handling all OpenAI API calls, client initialization, and JSON parsing."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

from services.exceptions import (
    MissingApiKeyError,
    OpenAiApiError,
    OpenAiRateLimitError,
    OpenAiTimeoutError,
)

logger = logging.getLogger(__name__)


# Backwards compatibility alias while inheriting from OpenAiApiError
class OpenAiServiceError(OpenAiApiError):
    """Base exception for failures occurring during OpenAI API requests or response parsing."""


def create_client(api_key: str) -> OpenAI:
    """Instantiate and return an OpenAI client using the supplied API key."""
    if not api_key or not api_key.strip():
        logger.error("OpenAI API key validation failed: key is empty or missing.")
        raise MissingApiKeyError(
            message="OpenAI API key is missing or empty.",
            user_message="OpenAI API key is missing. Please configure your API key to use AI features.",
        )
    return OpenAI(api_key=api_key)


def parse_and_clean_json(raw_text: str) -> dict[str, Any]:
    """Clean markdown code fences and parse JSON string into a python dictionary."""
    if not raw_text or not raw_text.strip():
        logger.error("OpenAI response parsing failed: empty response body.")
        raise OpenAiServiceError(
            message="OpenAI returned an empty response.",
            user_message="AI service returned an empty response. Please try again.",
        )

    cleaned = raw_text.strip()
    fenced = re.search(r"```(json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(2).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as error:
        logger.error("OpenAI response parsing failed: invalid JSON syntax: %s", error, exc_info=True)
        raise OpenAiServiceError(
            message=f"OpenAI returned content that was not valid JSON: {error}",
            user_message="AI service response could not be parsed. Please try again.",
        ) from error

    if not isinstance(parsed, dict):
        logger.error("OpenAI response parsing failed: parsed JSON is type %s, expected dict.", type(parsed).__name__)
        raise OpenAiServiceError(
            message=f"OpenAI response is not a valid JSON object: {type(parsed).__name__}",
            user_message="AI service returned an unexpected data structure. Please try again.",
        )

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
    except AuthenticationError as error:
        logger.error("OpenAI Authentication Error: %s", error, exc_info=True)
        raise MissingApiKeyError(
            message=f"OpenAI authentication failed: {error}",
            user_message="OpenAI API key is invalid or unauthorized. Please check your configuration.",
        ) from error
    except APITimeoutError as error:
        logger.error("OpenAI API Timeout Error: %s", error, exc_info=True)
        raise OpenAiTimeoutError(
            message=f"OpenAI request timed out: {error}",
            user_message="The request to the AI service timed out. Please try again.",
        ) from error
    except RateLimitError as error:
        logger.error("OpenAI Rate Limit Exceeded: %s", error, exc_info=True)
        raise OpenAiRateLimitError(
            message=f"OpenAI rate limit or quota exceeded: {error}",
            user_message="AI service rate limit exceeded or quota reached. Please wait a moment and try again.",
        ) from error
    except APIConnectionError as error:
        logger.error("OpenAI API Connection Error: %s", error, exc_info=True)
        raise OpenAiApiError(
            message=f"OpenAI connection error: {error}",
            user_message="Could not connect to the AI service. Please check your internet connection.",
        ) from error
    except OpenAIError as error:
        logger.error("OpenAI API Error: %s", error, exc_info=True)
        raise OpenAiApiError(
            message=f"OpenAI request failed: {error}",
            user_message="AI service encountered an error while processing your request. Please try again.",
        ) from error

    raw_text = response.choices[0].message.content or ""
    return parse_and_clean_json(raw_text)
