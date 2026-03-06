from __future__ import annotations

"""
Utility functions for cleaning and normalizing OCR / extracted text.

Goals:
- remove broken line fragments
- merge sentences split by OCR line breaks
- remove duplicate whitespace
- strip non-printable characters
- remove obvious stray OCR symbols
"""

import logging
import re
import string
from typing import Final

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SENTENCE_END_CHARS: Final[str] = ".?!:;।\"'”’）)]}"


def _strip_non_printable(text: str) -> str:
    """Remove non-printable characters but keep Unicode letters (Hindi/Marathi/etc)."""
    return "".join(ch for ch in text if ch == "\n" or ch.isprintable())


def _remove_noise_symbols(text: str) -> str:
    """
    Remove common noisy OCR symbols that appear alone or repeated, e.g.
    bullets, boxes, decorative characters.
    """
    # Replace bullet-like characters with a simple dash
    text = re.sub(r"[•●◼■▪▫◾◽]", "-", text)
    # Remove sequences of stray punctuation/symbols
    text = re.sub(r"[^\w\s।\-,:;\'\"()₹₹/]+", " ", text)
    return text


def _merge_broken_lines(text: str) -> str:
    """
    Merge lines that are likely part of the same sentence.

    Heuristics:
    - If a line does not end with sentence-ending punctuation,
      and the next line starts with a lowercase letter or digit,
      join them with a space.
    """
    lines = [ln.strip() for ln in text.splitlines()]
    merged_lines: list[str] = []
    buffer = ""

    for line in lines:
        if not line:
            # Empty line: flush buffer as a paragraph boundary
            if buffer:
                merged_lines.append(buffer)
                buffer = ""
            continue

        if not buffer:
            buffer = line
            continue

        starts_with = line[0]
        should_join = (
            buffer[-1] not in SENTENCE_END_CHARS
            and (starts_with.islower() or starts_with.isdigit())
        )

        if should_join:
            buffer = f"{buffer} {line}"
        else:
            merged_lines.append(buffer)
            buffer = line

    if buffer:
        merged_lines.append(buffer)

    return "\n".join(merged_lines)


def clean_text(text: str) -> str:
    """
    Clean and normalize raw extracted/OCR text.
    """
    if not text:
        return ""

    logger.info("Cleaning extracted text (original length=%d)", len(text))

    # Normalize newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Strip non-printable characters
    text = _strip_non_printable(text)

    # Remove obviously noisy symbols
    text = _remove_noise_symbols(text)

    # Merge broken lines into smoother paragraphs
    text = _merge_broken_lines(text)

    # Collapse excessive whitespace but keep paragraph breaks
    # First, collapse spaces/tabs within lines
    text = re.sub(r"[ \t]+", " ", text)

    # Then collapse more than 2 consecutive newlines to exactly 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Finally, strip leading/trailing whitespace
    cleaned = text.strip()

    logger.info("Cleaned text length=%d", len(cleaned))
    return cleaned

