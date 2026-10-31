# -*- coding: utf-8 -*-
"""Unit tests for the SentenceTransformers embedding service."""
import math
import pytest
from backend.app.services.embedding import EmbeddingService


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def test_embedding_dimensions_and_normalization():
    """Verify generated embeddings have expected length (384) and are unit-normalized."""
    service = EmbeddingService()
    vecs = service.embed_texts(["Echoes Search personal knowledge retrieval."])
    assert len(vecs) == 1
    assert len(vecs[0]) == 384

    # Unit norm check (sum of squares ≈ 1.0)
    norm = sum(x * x for x in vecs[0])
    assert abs(norm - 1.0) < 0.01


def test_semantic_similarity_ranking():
    """Verify semantically similar sentences yield higher similarity than unrelated ones."""
    service = EmbeddingService()
    query = "kickoff meeting in October"
    similar_text = "initial project kickoff meeting held in late October"
    unrelated_text = "freshly baked chocolate chip cookies recipe"

    q_vec = service.embed_query(query)
    sim_vec = service.embed_texts([similar_text])[0]
    unrel_vec = service.embed_texts([unrelated_text])[0]

    sim_score = cosine_similarity(q_vec, sim_vec)
    unrel_score = cosine_similarity(q_vec, unrel_vec)

    assert sim_score > unrel_score
    assert sim_score > 0.6  # Expect strong semantic match
