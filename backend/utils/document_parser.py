"""
Multi-format document parser for Saarthi.AI
Supports: PDF, DOCX, TXT, Images (PNG/JPG), HTML

Uses image preprocessing (grayscale, contrast, sharpening, upscaling)
before OCR to dramatically improve Tesseract accuracy on real-world
government documents, ID cards, and scanned forms.
"""

import os
import sys

# ── PDF ────────────────────────────────────────────────────────
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# ── DOCX ───────────────────────────────────────────────────────
try:
    import docx  # python-docx
except ImportError:
    docx = None

# ── OCR (Tesseract + Pillow) ───────────────────────────────────
try:
    import pytesseract
    from PIL import Image, ImageFilter, ImageEnhance, ImageOps

    # Auto-detect Tesseract on Windows when it's not in PATH
    import platform, shutil
    if platform.system() == "Windows" and not shutil.which("tesseract"):
        for _path in [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]:
            if os.path.isfile(_path):
                pytesseract.pytesseract.tesseract_cmd = _path
                break
except ImportError:
    pytesseract = None
    Image = None
    ImageFilter = None
    ImageEnhance = None
    ImageOps = None

# ── HTML ───────────────────────────────────────────────────────
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


# ───────────────────────────────────────────────────────────────
# Tesseract configuration for Indian government documents
# ───────────────────────────────────────────────────────────────
# Use page segmentation mode 6 which works well for forms and documents.
TESSERACT_CONFIG = r"--psm 6"


def _preprocess_for_ocr(img):
    """
    Preprocess a PIL Image for optimal Tesseract OCR accuracy.

    Pipeline:
      1. Convert to grayscale
      2. Upscale small images (< 1500px wide) to ~2x
      3. Auto-contrast to normalize lighting
      4. Sharpen to make edges crisper
      5. Binarize with adaptive threshold for clean black/white text
    """
    # 1. Grayscale
    img = img.convert("L")

    # 2. Upscale small images — Tesseract needs ~300+ DPI for good results
    w, h = img.size
    if w < 1500:
        scale = max(2, 3000 // w)
        img = img.resize((w * scale, h * scale), Image.LANCZOS)

    # 3. Auto-contrast — equalizes lighting differences
    img = ImageOps.autocontrast(img, cutoff=1)

    # 4. Sharpen — makes character edges crisper
    img = img.filter(ImageFilter.SHARPEN)
    img = img.filter(ImageFilter.SHARPEN)  # double-sharpen for scans

    # 5. Binarize — convert to pure black/white
    #    Threshold of 140 works well for most government docs
    img = img.point(lambda x: 255 if x > 140 else 0, mode="1")

    return img


def _ocr_image(img):
    """Run Tesseract OCR on a preprocessed image with optimized config."""
    processed = _preprocess_for_ocr(img)
    return pytesseract.image_to_string(
        processed,
        lang="eng",
        config=TESSERACT_CONFIG,
    )


# ───────────────────────────────────────────────────────────────
# File type detection
# ───────────────────────────────────────────────────────────────

def detect_file_type(filename: str) -> str:
    if not filename:
        return "unknown"
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return "pdf"
    elif ext in ("docx", "doc"):
        return "docx"
    elif ext == "txt":
        return "txt"
    elif ext in ("png", "jpg", "jpeg", "bmp", "tiff", "webp"):
        return "image"
    elif ext in ("html", "htm"):
        return "html"
    return "unknown"


# ───────────────────────────────────────────────────────────────
# Main extraction
# ───────────────────────────────────────────────────────────────

def extract_text(file_path: str, filename: str = None) -> str:
    """
    Extract text from a file.  Automatically detects the format
    from *filename* and applies the appropriate parser.

    For images and scanned PDFs, applies image preprocessing
    before OCR.

    Args:
        file_path: Path to the file on disk.
        filename:  Original filename (used for type detection).

    Returns:
        Extracted text string (may be empty on failure).
    """
    if not filename:
        filename = os.path.basename(file_path)

    file_type = detect_file_type(filename)

    try:
        # ── PDF ────────────────────────────────────────────────
        if file_type == "pdf":
            if not fitz:
                raise ImportError("PyMuPDF (fitz) is not installed.")

            text = ""
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text() or ""

            # Scanned PDF fallback — render pages as images and OCR
            if not text.strip():
                if pytesseract and Image:
                    try:
                        ocr_text = ""
                        with fitz.open(file_path) as doc:
                            for page in doc:
                                pix = page.get_pixmap(dpi=300)
                                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                                ocr_text += _ocr_image(img) + "\n"
                        if ocr_text.strip():
                            return ocr_text
                    except Exception as ocr_err:
                        print(f"Warning: OCR fallback for scanned PDF failed: {ocr_err}", file=sys.stderr)

                return "[Scanned PDF — no selectable text found. Install Tesseract OCR for text extraction.]"

            return text

        # ── DOCX ───────────────────────────────────────────────
        elif file_type == "docx":
            if not docx:
                raise ImportError("python-docx is not installed.")
            doc = docx.Document(file_path)
            return "\n".join(para.text for para in doc.paragraphs)

        # ── TXT ────────────────────────────────────────────────
        elif file_type == "txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        # ── IMAGE ──────────────────────────────────────────────
        elif file_type == "image":
            if not Image:
                raise ImportError("PIL (pillow) is not installed.")
            if not pytesseract:
                raise ImportError("pytesseract is not installed.")
            img = Image.open(file_path)
            return _ocr_image(img)

        # ── HTML ───────────────────────────────────────────────
        elif file_type == "html":
            if not BeautifulSoup:
                raise ImportError("beautifulsoup4 is not installed.")
            with open(file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
                return soup.get_text(separator="\n", strip=True)

        else:
            raise ValueError(f"Unsupported file type for {filename}")

    except Exception as e:
        print(f"Error extracting text from {file_path} (Type: {file_type}): {e}", file=sys.stderr)
        return ""
