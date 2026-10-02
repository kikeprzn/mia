"""Project every chunk's embedding to 2D, so the index can be looked at.

PCA keeps the two directions in which the 3072-dimension vectors differ most.
It's deterministic and a question can be placed with the same projection, but
two axes keep only part of the information: closeness on the map is a hint,
and the real neighbours are the ones Chroma returns.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.chunk import Chunk
from app.store import all_vectors


@dataclass(frozen=True)
class Projection:
    chunks: list[Chunk]
    points: np.ndarray  # one (x, y) per chunk
    explained: tuple[float, float]  # share of the variation each axis keeps
    mean: np.ndarray
    axes: np.ndarray  # (2, dimensions)

    def place(self, vector: list[float]) -> tuple[float, float]:
        x, y = (np.asarray(vector) - self.mean) @ self.axes.T
        return float(x), float(y)


def project() -> Projection | None:
    chunks, vectors = all_vectors()
    if len(chunks) < 3:
        return None
    matrix = np.asarray(vectors)
    mean = matrix.mean(axis=0)
    centered = matrix - mean
    _, singular, rows = np.linalg.svd(centered, full_matrices=False)
    variance = singular**2 / (singular**2).sum()
    axes = rows[:2]
    return Projection(
        chunks=chunks,
        points=centered @ axes.T,
        explained=(float(variance[0]), float(variance[1])),
        mean=mean,
        axes=axes,
    )


def family(title: str) -> str:
    # "Agitadores Anclas NC-NCH" -> "Anclas"
    words = title.split()
    return words[1] if len(words) > 2 and words[0] == "Agitadores" else title
