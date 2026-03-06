"""
PDF text extraction utilities using PyMuPDF (fitz).

This replaces Textract-based extraction when Textract is not yet available.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Try importing PyMuPDF. On AWS Lambda, this may not be available unless
# packaged correctly; we handle that gracefully so the Lambda doesn't crash.
try:  # pragma: no cover - import side-effect
    import fitz  # type: ignore  # PyMuPDF
except Exception:  # ModuleNotFoundError or binary import error
    fitz = None  # type: ignore
    logger.warning(
        "PyMuPDF (fitz) is not available in the current environment; "
        "PDF text extraction will be skipped and the document will be "
        "treated as scanned."
    )


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file using PyMuPDF.

    Args:
        file_path: Path to the PDF file on disk.

    Returns:
        Concatenated text from all pages. Returns an empty string if the PDF
        is corrupted or no text could be extracted.
    """
    # If PyMuPDF is not available (e.g., missing native deps in Lambda),
    # return empty text so the caller can fall back to a scanned-document
    # message instead of crashing.
    if fitz is None:  # type: ignore
        logger.warning("extract_text_from_pdf called but PyMuPDF is unavailable")
        return ""

    try:
        text_parts: list[str] = []

        with fitz.open(file_path) as doc:
            for page_index in range(len(doc)):
                try:
                    page = doc.load_page(page_index)
                    page_text = page.get_text() or ""
                    if page_text:
                        text_parts.append(page_text.strip())
                except Exception as page_error:
                    # Log and continue with other pages instead of failing whole document
                    logger.warning(
                        "Error extracting text from page %s: %s",
                        page_index,
                        str(page_error),
                    )

        full_text = "\n\n".join(part for part in text_parts if part)
        return full_text.strip()

    except Exception as e:
        # Handle corrupted PDFs or unsupported formats gracefully
        logger.error(f"Failed to extract text with PyMuPDF: {str(e)}")
        return ""

