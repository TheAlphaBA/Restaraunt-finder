"""
LLM Client — wraps the Groq API call (OpenAI-compatible) with retry logic
and error handling.

Uses the OpenAI Python SDK with Groq's base URL for inference.
Supports models: openai/gpt-oss-120b, qwen/qwen3.6-27b, etc.
"""

import json
import os
import time
import logging

from openai import OpenAI

logger = logging.getLogger(__name__)


def _extract_json_from_response(text: str) -> dict:
    """Extract JSON from LLM response text, handling markdown code fences.

    Args:
        text: Raw response text from the LLM.

    Returns:
        Parsed JSON dict.

    Raises:
        json.JSONDecodeError: If no valid JSON can be extracted.
    """
    text = text.strip()

    # Try direct JSON parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences if present (```json ... ``` or ``` ... ```)
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        text = "\n".join(lines).strip()

    return json.loads(text)


def call_llm(system_prompt: str, user_prompt: str, config: dict) -> dict:
    """Call the Groq LLM API and return parsed JSON response.

    Uses the OpenAI SDK with Groq's base URL. Implements retry with
    exponential backoff (3 attempts).

    Args:
        system_prompt: System instruction for the LLM.
        user_prompt: User message containing preferences and restaurant list.
        config: Application config dict with llm.model, llm.temperature,
                llm.max_tokens, llm.base_url settings.

    Returns:
        Parsed JSON dict from the LLM response.

    Raises:
        RuntimeError: If the API call fails after 3 attempts.
        ValueError: If GROQ_API_KEY is not set.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY is not configured. "
            "Set it in your .env file with a valid Groq API key. "
            "Get one at https://console.groq.com/keys"
        )

    client = OpenAI(
        api_key=api_key,
        base_url=config["llm"].get("base_url", "https://api.groq.com/openai/v1")
    )

    last_error = None
    for attempt in range(3):
        try:
            logger.info(
                f"LLM call attempt {attempt + 1}/3 "
                f"(model: {config['llm']['model']})"
            )

            response = client.chat.completions.create(
                model=config["llm"]["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config["llm"].get("temperature", 0.4),
                max_tokens=config["llm"].get("max_tokens", 1024)
            )

            raw_text = response.choices[0].message.content
            logger.info(f"LLM response received ({len(raw_text)} chars)")

            result = _extract_json_from_response(raw_text)
            return result

        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(
                f"Attempt {attempt + 1}: Failed to parse JSON from LLM response. "
                f"Raw text: {raw_text[:200]}..."
            )
            if attempt < 2:
                time.sleep(2 ** attempt)
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1}: LLM API error: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)

    raise RuntimeError(
        f"LLM call failed after 3 attempts. Last error: {last_error}"
    )
