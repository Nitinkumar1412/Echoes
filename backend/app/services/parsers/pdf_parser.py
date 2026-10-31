# -*- coding: utf-8 -*-
"""PDF parser using PyMuPDF with optional OCR fallback for scanned pages."""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Union

import pymupdf

from .base import PageContent, ParsedDocument

logger = logging.getLogger(__name__)


def parse_pdf_file(file_path: Union[str, Path]) -> ParsedDocument:
    """
    Extract text, page numbers, and offsets from a PDF document.
    Falls back to OCR if page has minimal or no selectable text.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")

    doc = pymupdf.open(str(path))
    pages: list[PageContent] = []
    full_text_parts: list[str] = []
    current_offset = 0

    meta = doc.metadata or {}
    extracted_title = meta.get("title") or path.stem

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_num = page_idx + 1

        # 1. Extract digital text
        page_text = page.get_text("text").strip()

        # 2. OCR fallback for scanned / image-only pages
        if len(page_text) < 20:
            try:
                import pytesseract
                from PIL import Image

                pix = page.get_pixmap(dpi=150)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                ocr_text = pytesseract.image_to_string(img).strip()
                if ocr_text:
                    logger.info("[PDF] OCR recovered %d chars on page %d", len(ocr_text), page_num)
                    page_text = ocr_text
            except Exception as ocr_err:
                logger.debug("[PDF] OCR fallback skipped for page %d: %s", page_num, ocr_err)

        if page_text:
            start = current_offset
            end = start + len(page_text)
            pages.append(
                PageContent(
                    page_number=page_num,
                    text=page_text,
                    char_start=start,
                    char_end=end,
                )
            )
            full_text_parts.append(page_text)
            current_offset = end + 2  # account for "\n\n" joiner

    full_text = "\n\n".join(full_text_parts).strip()
    total_pages = len(doc)
    doc.close()

    return ParsedDocument(
        text=full_text,
        pages=pages,
        page_count=total_pages,
        word_count=len(full_text.split()),
        extracted_title=extracted_title,
        metadata={
            "filename": path.name,
            "author": meta.get("author"),
            "creation_date": meta.get("creationDate"),
        },
    )
