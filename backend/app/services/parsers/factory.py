# -*- coding: utf-8 -*-
"""Parser factory for choosing the correct parser based on file extension and MIME type."""
from __future__ import annotations

from pathlib import Path
from typing import Tuple, Union

from backend.app.models.document import FileType
from .base import ParsedDocument
from .docx_parser import parse_docx_file
from .image_parser import parse_image_file
from .pdf_parser import parse_pdf_file
from .text_parser import parse_text_file

EXTENSION_MAP = {
    ".pdf": (FileType.PDF, parse_pdf_file),
    ".docx": (FileType.DOCX, parse_docx_file),
    ".doc": (FileType.DOCX, parse_docx_file),
    ".txt": (FileType.TXT, parse_text_file),
    ".md": (FileType.TXT, parse_text_file),
    ".markdown": (FileType.TXT, parse_text_file),
    ".log": (FileType.TXT, parse_text_file),
    ".csv": (FileType.TXT, parse_text_file),
    ".json": (FileType.TXT, parse_text_file),
    ".png": (FileType.IMAGE, parse_image_file),
    ".jpg": (FileType.IMAGE, parse_image_file),
    ".jpeg": (FileType.IMAGE, parse_image_file),
    ".webp": (FileType.IMAGE, parse_image_file),
    ".bmp": (FileType.IMAGE, parse_image_file),
}


def detect_file_type(filename: str) -> FileType:
    """Return the Echoes FileType for a filename."""
    ext = Path(filename).suffix.lower()
    return EXTENSION_MAP.get(ext, (FileType.OTHER, parse_text_file))[0]


def parse_document(file_path: Union[str, Path]) -> Tuple[ParsedDocument, FileType]:
    """
    Automatically select the correct parser and extract text & metadata.
    Returns (ParsedDocument, FileType).
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext in EXTENSION_MAP:
        file_type, parser_fn = EXTENSION_MAP[ext]
        return parser_fn(path), file_type

    # Default fallback: attempt text parse
    try:
        return parse_text_file(path), FileType.TXT
    except Exception:
        return (
            ParsedDocument(
                text="",
                pages=[],
                page_count=1,
                word_count=0,
                extracted_title=path.stem,
                metadata={"filename": path.name, "unsupported": True},
            ),
            FileType.OTHER,
        )
