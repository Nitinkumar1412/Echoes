# -*- coding: utf-8 -*-
"""
Boundary-aware chunking engine for Echoes Search.
Splits text respecting paragraph and sentence boundaries, generating deterministic Chunk models.
"""
from __future__ import annotations

import re
from typing import List, Optional

from backend.app.core.config import settings
from backend.app.models.chunk import Chunk
from backend.app.services.parsers.base import PageContent, ParsedDocument

# Sentence split pattern: looks for sentence ending punctuation followed by space/newline
_SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[.!?])\s+")


def estimate_token_count(text: str) -> int:
    """
    Robust token estimation. Standard English text averages ~1.3 tokens per word,
    or ~4 characters per token.
    """
    if not text:
        return 0
    words = text.split()
    return max(1, int(len(words) * 1.3))


def find_page_number_for_offset(offset: int, pages: List[PageContent]) -> Optional[int]:
    """Find which page a character offset belongs to."""
    if not pages:
        return 1
    for p in pages:
        if p.char_start <= offset <= p.char_end:
            return p.page_number
    # Fallback to the last page if offset is beyond or at the end
    return pages[-1].page_number if pages else 1


def split_into_sentence_units(text: str) -> List[tuple[str, int, int]]:
    """
    Split text into sentence units preserving start and end character offsets.
    Returns list of (unit_text, start_offset, end_offset).
    """
    units: List[tuple[str, int, int]] = []
    paragraphs = text.split("\n\n")
    current_pos = 0

    for para in paragraphs:
        if not para.strip():
            current_pos += len(para) + 2
            continue

        # Split paragraph into sentences
        sentences = _SENTENCE_SPLIT_REGEX.split(para)
        para_search_start = current_pos

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Find exact position in text
            idx = text.find(sentence, para_search_start)
            if idx == -1:
                idx = para_search_start
            start = idx
            end = idx + len(sentence)
            para_search_start = end
            units.append((sentence, start, end))

        current_pos = para_search_start + 2

    return units


def chunk_document(
    parsed_doc: ParsedDocument,
    document_id: str,
    workspace_id: str,
    chunk_size: Optional[int] = None,
    overlap: Optional[int] = None,
) -> List[Chunk]:
    """
    Chunk a parsed document into boundary-aware Chunk domain models.

    Args:
        parsed_doc: Output from the document parser
        document_id: Parent document identifier
        workspace_id: Target workspace identifier
        chunk_size: Target token size (defaults to settings.CHUNK_SIZE = 512)
        overlap: Token overlap between consecutive chunks (defaults to settings.CHUNK_OVERLAP = 64)

    Returns:
        List of Chunk models with deterministic IDs ({document_id}__chunk_{i:04d})
    """
    target_chunk_size = chunk_size or settings.CHUNK_SIZE
    target_overlap = overlap or settings.CHUNK_OVERLAP
    raw_text = parsed_doc.text.strip()

    if not raw_text:
        return []

    sentence_units = split_into_sentence_units(raw_text)
    if not sentence_units:
        # Single block fallback
        tokens = estimate_token_count(raw_text)
        return [
            Chunk.create(
                document_id=document_id,
                workspace_id=workspace_id,
                index=0,
                text=raw_text,
                token_count=tokens,
                char_start=0,
                char_end=len(raw_text),
                chunk_size=target_chunk_size,
                overlap=target_overlap,
                page_number=1,
            )
        ]

    chunks: List[Chunk] = []
    current_units: List[tuple[str, int, int]] = []
    current_tokens = 0
    chunk_index = 0
    i = 0

    while i < len(sentence_units):
        unit_text, unit_start, unit_end = sentence_units[i]
        unit_tokens = estimate_token_count(unit_text)

        # If a single sentence is larger than target_chunk_size, we still accept it as a unit
        if current_tokens + unit_tokens > target_chunk_size and current_units:
            # Build current chunk
            chunk_text = " ".join([u[0] for u in current_units])
            chunk_start = current_units[0][1]
            chunk_end = current_units[-1][2]
            page_num = find_page_number_for_offset(chunk_start, parsed_doc.pages)

            chunk = Chunk.create(
                document_id=document_id,
                workspace_id=workspace_id,
                index=chunk_index,
                text=chunk_text,
                token_count=current_tokens,
                char_start=chunk_start,
                char_end=chunk_end,
                chunk_size=target_chunk_size,
                overlap=target_overlap,
                page_number=page_num,
            )
            chunks.append(chunk)
            chunk_index += 1

            # Calculate overlap: step backwards so next chunk shares ~target_overlap tokens
            accumulated_overlap = 0
            overlap_units = []
            for prev_unit in reversed(current_units):
                prev_tokens = estimate_token_count(prev_unit[0])
                if accumulated_overlap + prev_tokens <= target_overlap or not overlap_units:
                    overlap_units.insert(0, prev_unit)
                    accumulated_overlap += prev_tokens
                else:
                    break

            current_units = list(overlap_units)
            current_tokens = accumulated_overlap

        current_units.append((unit_text, unit_start, unit_end))
        current_tokens += unit_tokens
        i += 1

    # Final remaining chunk
    if current_units:
        chunk_text = " ".join([u[0] for u in current_units])
        chunk_start = current_units[0][1]
        chunk_end = current_units[-1][2]
        page_num = find_page_number_for_offset(chunk_start, parsed_doc.pages)

        chunk = Chunk.create(
            document_id=document_id,
            workspace_id=workspace_id,
            index=chunk_index,
            text=chunk_text,
            token_count=current_tokens,
            char_start=chunk_start,
            char_end=chunk_end,
            chunk_size=target_chunk_size,
            overlap=target_overlap,
            page_number=page_num,
        )
        chunks.append(chunk)

    return chunks
