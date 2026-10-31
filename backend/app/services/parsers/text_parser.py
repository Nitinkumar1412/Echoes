# -*- coding: utf-8 -*-
"""Parser for plain text and markdown documents."""
from __future__ import annotations

from pathlib import Path
from typing import Union

from .base import PageContent, ParsedDocument


def parse_text_file(file_path: Union[str, Path]) -> ParsedDocument:
    """Read a .txt or .md file with automatic fallback for text encodings."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    raw_bytes = path.read_bytes()
    text = ""
    used_encoding = "utf-8"

    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            text = raw_bytes.decode(enc)
            used_encoding = enc
            break
        except UnicodeDecodeError:
            continue

    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()

    # Try extracting title from markdown first header if available
    extracted_title = None
    for line in text.split("\n"):
        clean = line.strip()
        if clean.startswith("# "):
            extracted_title = clean[2:].strip()
            break

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
        encoding=used_encoding,
        extracted_title=extracted_title or path.stem,
        metadata={"filename": path.name},
    )
