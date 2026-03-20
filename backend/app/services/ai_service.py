import os
import json
import litellm

litellm._turn_on_debug()

from app.schemas.job_posting import ImportPreview

AI_MODEL = os.getenv("AI_MODEL", "ollama/llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


class AIServiceError(Exception):
    pass


def _llm(messages: list, **kwargs) -> str:
    """Make a single LiteLLM completion call and return the text content."""
    call_kwargs = {}
    if AI_MODEL.startswith("ollama/"):
        call_kwargs["api_base"] = OLLAMA_BASE_URL
    call_kwargs.update(kwargs)
    response = litellm.completion(
        model=AI_MODEL,
        messages=messages,
        timeout=30,
        **call_kwargs,
    )
    return response.choices[0].message.content


def _strip_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        first_newline = stripped.find("\n")
        if first_newline != -1:
            stripped = stripped[first_newline + 1:]
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3].rstrip()
    return stripped


def extract_job_posting(raw_text: str) -> ImportPreview:
    raw_text = raw_text[:16000]

    # Step 1: extract structured fields only (no description)
    try:
        fields_content = _llm([
            {
                "role": "system",
                "content": "You are a job posting parser. Return valid JSON only — no explanation, no markdown fences.",
            },
            {
                "role": "user",
                "content": (
                    "Extract these fields from the job posting. Use null for any not mentioned.\n"
                    "If multiple salary ranges are listed, prefer the remote/location-agnostic range.\n\n"
                    'Return JSON only: {"title": "...", "company_name": "...", "location": "...", '
                    '"remote_type": "remote"|"hybrid"|"onsite"|null, "salary_min": integer|null, "salary_max": integer|null}\n\n'
                    f"Job posting:\n{raw_text}"
                ),
            },
        ])
        parsed = json.loads(_strip_fences(fields_content))
    except json.JSONDecodeError as e:
        raise AIServiceError(f"Failed to parse JSON from AI response: {e}") from e
    except litellm.exceptions.Timeout as e:
        raise AIServiceError(f"AI request timed out: {e}") from e
    except Exception as e:
        raise AIServiceError(f"AI service error: {e}") from e

    # Step 2: generate description as plain markdown
    try:
        description = _llm([
            {
                "role": "system",
                "content": "You are a job posting summarizer. Return only markdown — no JSON, no explanation.",
            },
            {
                "role": "user",
                "content": (
                    "Write a markdown summary of this job posting using these sections "
                    "(omit any section not present in the posting):\n"
                    "- ## Role Overview\n"
                    "- ## Key Responsibilities\n"
                    "- ## Requirements\n"
                    "- ## Compensation & Benefits\n"
                    "- ## Work Arrangement (only if hybrid)\n\n"
                    f"Job posting:\n{raw_text}"
                ),
            },
        ])
    except Exception:
        description = None

    preview = ImportPreview(**parsed)
    preview.description = description
    preview.raw_content = raw_text
    preview.ai_used = True
    return preview


def summarize_posting(raw_content: str) -> str:
    raw_content = raw_content[:16000]

    try:
        return _llm([
            {
                "role": "system",
                "content": "You are a job posting summarizer. Return only markdown — no JSON, no explanation.",
            },
            {
                "role": "user",
                "content": (
                    "Write a markdown summary of this job posting using these sections "
                    "(omit any section not present in the posting):\n"
                    "- ## Role Overview\n"
                    "- ## Key Responsibilities\n"
                    "- ## Requirements\n"
                    "- ## Compensation & Benefits\n"
                    "- ## Work Arrangement (only if hybrid)\n\n"
                    f"Job posting:\n{raw_content}"
                ),
            },
        ])
    except litellm.exceptions.Timeout as e:
        raise AIServiceError(f"AI request timed out: {e}") from e
    except Exception as e:
        raise AIServiceError(f"AI service error: {e}") from e
