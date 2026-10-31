# -*- coding: utf-8 -*-
"""Parsers for Echoes Search."""
from .base import PageContent, ParsedDocument
from .docx_parser import parse_docx_file
from .factory import detect_file_type, parse_document
from .image_parser import parse_image_file
from .pdf_parser import parse_pdf_file
from .text_parser import parse_text_file

__all__ = [
    "PageContent",
    "ParsedDocument",
    "parse_document",
    "detect_file_type",
    "parse_pdf_file",
    "parse_docx_file",
    "parse_text_file",
    "parse_image_file",
]
