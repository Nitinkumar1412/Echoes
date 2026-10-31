# -*- coding: utf-8 -*-
"""Image and screenshot parser using OCR via pytesseract."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

from PIL import Image

from .base import PageContent, ParsedDocument

logger = logging.getLogger(__name__)


def parse_image_file(file_path: Union[str, Path]) -> ParsedDocument:
    """Extract text from an image or screenshot using OCR."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")

    text = ""
    try:
        import pytesseract

        img = Image.open(path)
        # Convert to RGB if palette or alpha
        if img.mode not in ("L", "RGB"):
            img = img.convert("RGB")
        text = pytesseract.image_to_string(img).strip()
    except Exception as exc:
        logger.warning("[IMAGE PARSER] OCR extraction failed or Tesseract not installed: %s", exc)
        text = f"[Image file: {path.name} — OCR extraction unavailable]"

    pages = [
        PageContent(
            page_number=1,
            text=text,
            char_start=0,
            char_end=len(text),
        )
    ]

    return ParsedDocument(
        text=text,
        pages=pages,
        page_count=1,
        word_count=len(text.split()),
        extracted_title=path.stem,
        metadata={"filename": path.name, "format": path.suffix.lower()},
    )
