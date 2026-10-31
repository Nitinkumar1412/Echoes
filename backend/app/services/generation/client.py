# -*- coding: utf-8 -*-
"""
Gemini 2.5 Flash LLM client using google-genai SDK with fallback synthesizer.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings
from .prompt import SYSTEM_PROMPT

logger = logging.getLogger("echoes.generation.client")


class GeminiClient:
    """Wrapper around Gemini 2.5 Flash with fallback extractive generation."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.MODEL_NAME
        self._genai_client = None

        if self.api_key and self.api_key not in ("your_gemini_api_key", ""):
            try:
                from google import genai

                self._genai_client = genai.Client(api_key=self.api_key)
                logger.info("[GEMINI] Client initialized for model '%s'", self.model_name)
            except Exception as exc:
                logger.warning("[GEMINI] Failed to initialize google-genai client: %s", exc)

    def is_live_configured(self) -> bool:
        """Return True if a valid Gemini API key is configured."""
        return self._genai_client is not None

    async def generate_answer(
        self,
        prompt: str,
        query: str,
        chunks: List[Dict[str, Any]],
    ) -> str:
        """
        Generate answer via Gemini 2.5 Flash or fallback to extractive synthesizer.
        """
        # If no evidence chunks at all
        if not chunks:
            return (
                "I do not have enough evidence in your uploaded documents to answer this question. "
                "[CONFIDENCE: insufficient_evidence]"
            )

        # 1. Try Live Gemini API call if configured
        if self._genai_client:
            try:
                full_contents = f"{SYSTEM_PROMPT}\n\n{prompt}"
                response = self._genai_client.models.generate_content(
                    model=self.model_name,
                    contents=full_contents,
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as exc:
                logger.warning("[GEMINI CALL WARN] Gemini generation error: %s. Using extractive fallback.", exc)

        # 2. Extractive Grounded Fallback
        return self._extractive_fallback(query, chunks)

    def _extractive_fallback(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Deterministic, evidence-grounded fallback synthesizer when live LLM is unavailable.
        Extracts relevant sentences from top chunks and attributes with [CHUNK_X].
        """
        query_words = set(re.findall(r"\w+", query.lower()))
        selected_sentences: List[str] = []

        for idx, ch in enumerate(chunks[:3], start=1):
            text = ch.get("text", "")
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
            for s in sentences:
                s_words = set(re.findall(r"\w+", s.lower()))
                overlap = len(query_words.intersection(s_words))
                if overlap >= 2 or len(selected_sentences) < 2:
                    selected_sentences.append(f"{s} [CHUNK_{idx}]")
                    if len(selected_sentences) >= 3:
                        break
            if len(selected_sentences) >= 3:
                break

        if not selected_sentences:
            return (
                "I do not have enough evidence in your uploaded documents to answer this question. "
                "[CONFIDENCE: insufficient_evidence]"
            )

        answer_text = " ".join(selected_sentences) + " [CONFIDENCE: high]"
        return answer_text
