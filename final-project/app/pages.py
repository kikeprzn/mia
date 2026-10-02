"""Render brochure pages as images, so citations can show the page they point to."""

from __future__ import annotations

import io
import re
from functools import lru_cache
from pathlib import Path

import pypdfium2 as pdfium

DOCS_DIR = Path(__file__).resolve().parent.parent / "data"
RENDER_SCALE = 1.5  # 72 dpi * 1.5 = 108 dpi, readable without being heavy
JPEG_QUALITY = 80


class PageNotFoundError(Exception):
    pass


_UNSAFE_CHARS = re.compile(r"[^\w.-]+")  # \w keeps accented letters
_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def safe_filename(raw: str) -> str | None:
    """Turn an uploaded file's name into one that is safe to write in DOCS_DIR.

    Directory parts are dropped (with either slash), characters other than
    letters, digits, ".", "_" and "-" become "_", and the result must be a
    .pdf whose name isn't reserved on Windows (CON, NUL, COM1...).
    Returns None when no usable name is left.
    """
    name = Path(raw.replace("\\", "/")).name
    stem, suffix = Path(name).stem, Path(name).suffix.lower()
    stem = _UNSAFE_CHARS.sub("_", stem).strip("._")
    if suffix != ".pdf" or not stem or stem.split(".")[0].upper() in _RESERVED:
        return None
    return f"{stem[:150]}.pdf"


def document_path(source: str) -> Path:
    # `source` comes from the URL, so it must name a PDF directly inside
    # DOCS_DIR; anything like "../.env" is rejected.
    path = (DOCS_DIR / source).resolve()
    if path.parent != DOCS_DIR or path.suffix.lower() != ".pdf" or not path.is_file():
        raise PageNotFoundError(f"{source} no está disponible")
    return path


@lru_cache(maxsize=64)
def render_page(source: str, page: int) -> bytes:
    pdf = pdfium.PdfDocument(document_path(source))
    try:
        if not 1 <= page <= len(pdf):
            raise PageNotFoundError(f"{source} no tiene página {page}")
        image = pdf[page - 1].render(scale=RENDER_SCALE).to_pil()
    finally:
        pdf.close()
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, "JPEG", quality=JPEG_QUALITY)
    return buffer.getvalue()
