# -*- coding: utf-8 -*-
"""Base interfaces and data structures for document parsing."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class PageContent:
    """Represents text extracted from a single page (for paginated docs like PDF)."""
    page_number: int                    # 1-indexed
    text: str
    char_start: int                     # character offset in full document
    char_end: int


@dataclass
class ParsedDocument:
    """Structured output from any document parser."""
    text: str                           # full aggregated text
    pages: list[PageContent] = field(default_factory=list)
    page_count: int = 1
    word_count: int = 0
    language: Optional[str] = "en"
    encoding: Optional[str] = "utf-8"
    extracted_title: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.word_count and self.text:
            self.word_count = len(self.text.split())
        if not self.page_count:
            self.page_count = len(self.pages) if self.pages else 1
