"""
Shared text utilities used across Lambda handlers.

Centralises JSON-fence stripping and other text helpers that were previously
copy-pasted in grievance_handler, recommend_schemes, and pdf_status.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from typing import Any, Optional

logger = logging.getLogger(__name__)


def parse_llm_json(raw: str, fallback: Any = None) -> Any:
    """
    Parse JSON from LLM output, stripping markdown fences if present.

    Strategy (in order):
    1. Direct json.loads on the stripped string.
    2. Strip ```json ... ``` or ``` ... ``` fences then json.loads.
    3. Scan for the first '[' or '{' bracket and try to parse from there.
    4. Return *fallback* if all strategies fail.

    Args:
        raw:      Raw string returned by the LLM.
        fallback: Value to return when parsing fails (default: None).

    Returns:
        Parsed Python object, or *fallback*.
    """
    if not raw or not raw.strip():
        return fallback

    cleaned = raw.strip()

    # ── Strategy 1: direct parse ──────────────────────────────────────────────
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # ── Strategy 2: strip markdown fences ────────────────────────────────────
    # Handles ```json, ```JSON, ``` etc.
    fence_match = re.search(r"```(?:json|JSON)?\s*([\s\S]*?)```", cleaned)
    if fence_match:
        fenced_content = fence_match.group(1).strip()
        try:
            return json.loads(fenced_content)
        except json.JSONDecodeError:
            pass

    # ── Strategy 3: bracket scanning fallback ────────────────────────────────
    for start_char, end_char in [("[", "]"), ("{", "}")]:
        start_idx = cleaned.find(start_char)
        if start_idx == -1:
            continue
        # Walk backwards from end to find matching closing bracket
        end_idx = cleaned.rfind(end_char)
        if end_idx <= start_idx:
            continue
        candidate = cleaned[start_idx : end_idx + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    logger.warning(
        "parse_llm_json: all strategies failed. raw[:200]=%r", cleaned[:200]
    )
    return fallback


def sanitize_text(text: str, max_length: int = 5000) -> str:
    """
    Strip C0/C1 control characters (except common whitespace) and enforce a
    length limit.

    Args:
        text:       Input string.
        max_length: Maximum allowed length (truncated with '...' if exceeded).

    Returns:
        Sanitized string.
    """
    if not text:
        return ""

    # Remove control characters except tab, newline, carriage return
    sanitized = "".join(
        ch
        for ch in text
        if unicodedata.category(ch)[0] != "C" or ch in ("\t", "\n", "\r")
    )

    return truncate(sanitized, max_length)


def truncate(text: str, max_chars: int, suffix: str = "...") -> str:
    """
    Truncate *text* to *max_chars* characters, appending *suffix* if cut.

    Args:
        text:      Input string.
        max_chars: Maximum character count.
        suffix:    Appended when truncation occurs (default: '...').

    Returns:
        Possibly truncated string.
    """
    if not text or len(text) <= max_chars:
        return text
    return text[: max_chars - len(suffix)] + suffix
