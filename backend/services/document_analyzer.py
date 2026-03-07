from __future__ import annotations

"""
High-level document analysis service.

Takes cleaned document text and uses Bedrock (Nova / Titan via invoke_claude)
to produce a structured analysis suitable for the frontend.
"""

import json
import logging
from typing import Any, Dict, List

from utils.aws.bedrock import invoke_claude

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


SYSTEM_PROMPT = (
    "You are an AI system that analyzes government documents and "
    "explains them in simple language for citizens."
)


def _build_prompt(text: str) -> str:
    return (
        "You are an AI system that analyzes government documents.\n\n"
        "Given the following document text, generate a structured analysis.\n\n"
        "Return a valid JSON object with the following fields:\n"
        '  - "document_type": short string (e.g., "Government Scheme Guideline", '
        '"Notification", "Application Form", etc.)\n'
        '  - "purpose": 2-3 sentence description of what this document is for\n'
        '  - "key_points": array of 3-8 bullet-point style strings capturing the most '
        "important information and eligibility rules\n"
        '  - "instructions": array of 3-8 bullet-point style strings describing any '
        "steps citizens must follow or actions they should take\n"
        '  - "summary": a concise plain-language summary (8-12 sentences) that a '
        "10th-grade student can understand\n\n"
        "The JSON must be the ONLY thing in your reply. Do not include any "
        "markdown, bullet markers, or explanations outside the JSON.\n\n"
        "Document Text:\n"
        f"{text}\n"
    )


def _ensure_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        # Split on newlines or numbered bullets if the model returned plain text
        parts = [p.strip("-• ").strip() for p in value.splitlines() if p.strip()]
        if parts:
            return parts
    return []


def analyze_document(text: str) -> Dict[str, Any]:
    """
    Analyze a cleaned document and return structured fields:
    - document_type
    - purpose
    - key_points
    - instructions
    - summary
    """
    if not text:
        return {
            "document_type": "Unknown",
            "purpose": "",
            "key_points": [],
            "instructions": [],
            "summary": "",
        }

    prompt = _build_prompt(text)

    try:
        # Keep analysis latency low: limit max_tokens so we stay under API Gateway limits
        logger.info("Invoking Bedrock for document analysis (text length=%d)", len(text))
        raw = invoke_claude(prompt, system_prompt=SYSTEM_PROMPT, max_tokens=1024)
        logger.debug("Raw document analysis response: %s", raw[:500])

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Model did not return valid JSON; attempting to recover.")
            # Try to find JSON object inside the string
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                data = json.loads(raw[start : end + 1])
            else:
                raise

        document_type = str(data.get("document_type", "Unknown")).strip() or "Unknown"
        purpose = str(data.get("purpose", "")).strip()
        key_points = _ensure_list(data.get("key_points"))
        instructions = _ensure_list(data.get("instructions"))
        summary = str(data.get("summary", "")).strip()

        return {
            "document_type": document_type,
            "purpose": purpose,
            "key_points": key_points,
            "instructions": instructions,
            "summary": summary,
        }

    except Exception as e:
        logger.error("Document analysis failed: %s", str(e), exc_info=True)
        # Fallback: simple heuristic summary + key points
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
        summary = ". ".join(sentences[:8])
        if summary and not summary.endswith("."):
            summary += "."
        key_points = sentences[:5]

        return {
            "document_type": "Unknown",
            "purpose": "",
            "key_points": key_points,
            "instructions": [],
            "summary": summary or text[:500],
        }

