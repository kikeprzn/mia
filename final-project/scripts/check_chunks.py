"""Load every PDF in data/ and print the resulting chunks."""

from __future__ import annotations

from pathlib import Path

from app.chunk import FOOTER_MARKER, chunk_pages
from app.loader import load_pdf

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    pages = []
    for path in sorted(DATA.glob("*.pdf")):
        pages += load_pdf(path)

    chunks = chunk_pages(pages)
    for c in chunks:
        print(f"{c.id[24:]:<48} {c.word_count:>4}  {c.embed_text[:60]}")

    ids = [c.id for c in chunks]
    print()
    print(f"pages: {len(pages)}  chunks: {len(chunks)}")
    print(f"unique ids: {len(set(ids)) == len(ids)}")
    print(f"covers skipped: {not any(c.page == 1 for c in chunks)}")
    print(f"footer removed: {not any(FOOTER_MARKER in c.text for c in chunks)}")
    print(f"shortest chunk: {min(c.word_count for c in chunks)} words")


if __name__ == "__main__":
    main()
