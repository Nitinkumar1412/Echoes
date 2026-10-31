# -*- coding: utf-8 -*-
"""
Prompt construction for evidence-grounded answer generation with strict citations.
"""
from __future__ import annotations

from typing import Any, Dict, List

SYSTEM_PROMPT = """You are Echoes Search, an intelligent personal knowledge assistant.
Your goal is to answer the user's question using ONLY the provided evidence chunks, timeline events, and knowledge graph facts.

CRITICAL RULES:
1. Grounding: Answer strictly from the provided EVIDENCE. Do not use outside knowledge or hallucinate details.
2. Citations: Every single factual sentence or claim in your response MUST be cited with the chunk reference tag, e.g. [CHUNK_1] or [CHUNK_2].
3. Unfound Information: If the evidence does not contain enough information to answer the question, state: "I do not have enough evidence in your uploaded documents to answer this question." Do NOT guess or extrapolate.
4. Confidence: In your final sentence, output a confidence assessment tag: [CONFIDENCE: high | medium | low | insufficient_evidence].
5. Tone: Objective, factual, concise, and helpful.
"""


def build_rag_prompt(
    query: str,
    chunks: List[Dict[str, Any]],
    events: Optional[List[Dict[str, Any]]] = None,
    relationships: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Assemble the complete prompt containing evidence chunks, timeline events,
    knowledge graph connections, and the user's query.
    """
    prompt_parts: List[str] = []

    # 1. Evidence Chunks
    prompt_parts.append("=== RETRIEVED EVIDENCE CHUNKS ===")
    if not chunks:
        prompt_parts.append("No relevant chunks found in the database.")
    else:
        for idx, ch in enumerate(chunks, start=1):
            doc_name = ch.get("document_name", "Unknown Document")
            cid = ch.get("chunk_id", f"chunk_{idx}")
            page = ch.get("page_number", 1)
            text = ch.get("text", "").strip()
            prompt_parts.append(
                f"[CHUNK_{idx}] (Document: '{doc_name}', Page: {page}, ID: {cid}):\n{text}\n"
            )

    # 2. Chronological Timeline Context
    if events:
        prompt_parts.append("\n=== TIMELINE CONTEXT ===")
        for ev in events:
            date_str = ev.get("original_expression") or str(ev.get("normalized_date", ""))
            title = ev.get("title", "")
            prompt_parts.append(f"- Date: {date_str} | Event: {title}")

    # 3. Knowledge Graph Connections
    if relationships:
        prompt_parts.append("\n=== KNOWLEDGE GRAPH RELATIONSHIPS ===")
        for rel in relationships:
            u = rel.get("from_name", "Entity")
            v = rel.get("to_name", "Entity")
            rtype = rel.get("relationship_type", "RELATED_TO")
            prompt_parts.append(f"- {u} --[{rtype}]--> {v}")

    # 4. User Question
    prompt_parts.append("\n=== USER QUESTION ===")
    prompt_parts.append(query)
    prompt_parts.append("\nProvide an evidence-grounded answer with strict [CHUNK_X] citations:")

    return "\n".join(prompt_parts)
