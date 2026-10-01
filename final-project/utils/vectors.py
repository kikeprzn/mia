"""Dot product, norm, and cosine similarity.

Copied from the course's RAG/project/rag/vectors.py. Chroma computes the
similarity used in production.
"""

from __future__ import annotations

import math

Vector = list[float]


def dot(a: Vector, b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b))


def norm(a: Vector) -> float:
    return math.sqrt(dot(a, a))


def cosine(a: Vector, b: Vector) -> float:
    na, nb = norm(a), norm(b)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot(a, b) / (na * nb)
