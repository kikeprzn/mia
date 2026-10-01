"""Index every PDF in data/ into ChromaDB and run a test question."""

from __future__ import annotations

from pathlib import Path

from app.chunk import chunk_pages
from app.embed import embed_documents, embed_query
from app.loader import load_pdf
from app.store import count, query, upsert

DATA = Path(__file__).resolve().parent.parent / "data"
QUESTION = "¿Qué materiales de fabricación tiene el agitador RT-RTG?"


def main() -> None:
    pages = []
    for path in sorted(DATA.glob("*.pdf")):
        pages += load_pdf(path)
    chunks = chunk_pages(pages)

    upsert(chunks, embed_documents([c.embed_text for c in chunks]))
    print(f"chunks indexed: {len(chunks)}  stored in collection: {count()}")

    print(f"\nquestion: {QUESTION}")
    for r in query(embed_query(QUESTION), k=3):
        print(f"  [{r.rank}] {r.score:.3f}  {r.chunk.id}")


if __name__ == "__main__":
    main()
