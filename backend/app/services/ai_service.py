import os
import json
import litellm
from app.schemas.job_posting import ImportPreview

AI_MODEL = os.getenv("AI_MODEL", "ollama/llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


class AIServiceError(Exception):
    pass


def extract_job_posting(raw_text: str) -> ImportPreview:
    raw_text = raw_text[:16000]

    kwargs = {}
    if AI_MODEL.startswith("ollama/"):
        kwargs["api_base"] = OLLAMA_BASE_URL

    system_prompt = (
        "You are a job posting parser. Extract structured information from the raw job posting text "
        "and return valid JSON only — no explanation, no markdown fences, no surrounding text."
    )

    user_prompt = (
        "Extract the following fields from this job posting. Use null for any field not mentioned.\n\n"
        "For description, write a clean markdown summary using these sections (omit any section not present in the posting):\n"
        "- ## Role Overview\n"
        "- ## Key Responsibilities  \n"
        "- ## Requirements\n"
        "- ## Compensation & Benefits\n"
        "- ## Work Arrangement (ONLY include this section if the role is hybrid — describe the hybrid details such as days in office, office location, and schedule flexibility)\n\n"
        "If multiple salary ranges are listed (e.g., for different locations), prefer the location-agnostic or remote salary. Use null if no salary is mentioned.\n\n"
        'Return JSON only:\n'
        '{"title": "...", "company_name": "...", "location": "...", "remote_type": "remote"|"hybrid"|"onsite"|null, "salary_min": integer|null, "salary_max": integer|null, "description": "..."}\n\n'
        f"Job posting:\n{raw_text}"
    )

    try:
        response = litellm.completion(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            timeout=30,
            **kwargs,
        )
        content = response.choices[0].message.content

        # Strip markdown fences if present
        stripped = content.strip()
        if stripped.startswith("```"):
            # Remove opening fence (e.g. ```json or ```)
            first_newline = stripped.find("\n")
            if first_newline != -1:
                stripped = stripped[first_newline + 1:]
            # Remove closing fence
            if stripped.rstrip().endswith("```"):
                stripped = stripped.rstrip()[:-3].rstrip()
            content = stripped

        parsed = json.loads(content)
        preview = ImportPreview(**parsed)
        preview.raw_content = raw_text
        return preview
    except json.JSONDecodeError as e:
        raise AIServiceError(f"Failed to parse JSON from AI response: {e}") from e
    except litellm.exceptions.Timeout as e:
        raise AIServiceError(f"AI request timed out: {e}") from e
    except Exception as e:
        raise AIServiceError(f"AI service error: {e}") from e


def summarize_posting(raw_content: str) -> str:
    raw_content = raw_content[:16000]

    kwargs = {}
    if AI_MODEL.startswith("ollama/"):
        kwargs["api_base"] = OLLAMA_BASE_URL

    system_prompt = (
        "You are a job posting summarizer. Write clean, well-structured markdown summaries of job postings. "
        "Return only markdown — no JSON, no explanation, no surrounding text."
    )

    user_prompt = (
        "Write a clean markdown summary of this job posting using these sections (omit any section not present in the posting):\n"
        "- ## Role Overview\n"
        "- ## Key Responsibilities\n"
        "- ## Requirements\n"
        "- ## Compensation & Benefits\n"
        "- ## Work Arrangement (ONLY include this section if the role is hybrid — describe the hybrid details such as days in office, office location, and schedule flexibility)\n\n"
        "Return only the markdown — no JSON, no explanation.\n\n"
        f"Job posting:\n{raw_content}"
    )

    try:
        response = litellm.completion(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            timeout=30,
            **kwargs,
        )
        return response.choices[0].message.content
    except litellm.exceptions.Timeout as e:
        raise AIServiceError(f"AI request timed out: {e}") from e
    except Exception as e:
        raise AIServiceError(f"AI service error: {e}") from e
