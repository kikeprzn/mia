"""Split each page into overlapping chunks of whole words.

Adapted from the course's RAG/project/rag/chunk.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.loader import Page

FOOTER_MARKER = "¿NECESITAS AYUDA?"  # contact block repeated on every last page
MIN_WORDS = 20  # below this a page is a cover (title only), not evidence
FILENAME_PREFIX = "Autmix_Mixing_Solutions_"


@dataclass(frozen=True)
class Chunk:
    id: str  # "{source}:p{page}:c{index}", stable so re-ingesting overwrites
    title: str  # model identity, e.g. "Agitadores Anclas NC-NCH"
    source: str
    page: int
    index: int  # position of this chunk inside its page
    text: str  # clean text, shown to the user

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    @property
    def embed_text(self) -> str:
        # The brochures share one template, so the identity goes into the
        # vector; otherwise NC-NCH and NC-NCS chunks are nearly identical.
        return f"{self.title}. {self.text}"


def validate(size: int, overlap: int) -> None:
    if size < 1:
        raise ValueError("size must be >= 1")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must satisfy 0 <= overlap < size")


def title_from_source(source: str) -> str:
    stem = Path(source).stem.removeprefix(FILENAME_PREFIX)
    parts = stem.split("_")
    if len(parts) < 3:
        return " ".join(parts)
    return " ".join(parts[:-2]) + " " + "-".join(parts[-2:])


def _windows(words: list[str], size: int, overlap: int) -> list[list[str]]:
    if len(words) <= size:
        return [words]
    step = max(1, size - overlap)
    windows: list[list[str]] = []
    i = 0
    while i < len(words):
        windows.append(words[i : i + size])
        if i + size >= len(words):
            break
        i += step
    return windows


def chunk_pages(pages: list[Page], size: int = 100, overlap: int = 25) -> list[Chunk]:
    validate(size, overlap)
    chunks: list[Chunk] = []
    for page in pages:
        text = page.text.split(FOOTER_MARKER)[0].strip()
        words = text.split()
        if len(words) < MIN_WORDS:
            continue

        title = title_from_source(page.source)
        for index, window in enumerate(_windows(words, size, overlap)):
            chunks.append(
                Chunk(
                    id=f"{page.source}:p{page.page}:c{index}",
                    title=title,
                    source=page.source,
                    page=page.page,
                    index=index,
                    text=" ".join(window),
                )
            )
    return chunks
