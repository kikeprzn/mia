"""Read a PDF into one record per page."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader


@dataclass(frozen=True)
class Page:
    source: str
    page: int
    text: str


def load_pdf(file: str | Path | BinaryIO, source: str | None = None) -> list[Page]:
    """Read a path, or an open binary stream plus its `source` name."""
    if source is None:
        if not isinstance(file, (str, Path)):
            raise ValueError("source is required when reading from a stream")
        source = Path(file).name

    reader = PdfReader(file)
    result = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = " ".join(text.split())
        result.append(Page(source, i, text))

    return result
