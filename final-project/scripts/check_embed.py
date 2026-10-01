"""Check that related texts score closer to a question than unrelated ones."""

from __future__ import annotations

from pathlib import Path

from app.chunk import chunk_pages
from app.embed import embed_documents, embed_query
from app.loader import load_pdf
from utils.vectors import cosine

DATA = Path(__file__).resolve().parent.parent / "data"

QUESTION = "¿Qué materiales de fabricación tiene el agitador?"
RELATED = "Materiales: acero inoxidable AISI 316L, dúplex, titanio"
UNRELATED = "La receta del pastel lleva harina, huevos y azúcar"
# page 2, second chunk of the RT-RTG brochure: the materials list
REAL_PDF = "Autmix_Mixing_Solutions_Agitadores_Verticales_RT_RTG.pdf"
REAL_ID = f"{REAL_PDF}:p2:c1"


def main() -> None:
    chunks = chunk_pages(load_pdf(DATA / REAL_PDF))
    real = next(c for c in chunks if c.id == REAL_ID)

    question = embed_query(QUESTION)
    related, unrelated, real_vec = embed_documents([RELATED, UNRELATED, real.embed_text])

    related_score = cosine(question, related)
    unrelated_score = cosine(question, unrelated)
    real_score = cosine(question, real_vec)

    print(f"dimensions: {len(question)}")
    print(f"question vs related:    {related_score:.3f}")
    print(f"question vs unrelated:  {unrelated_score:.3f}")
    print(f"question vs real chunk: {real_score:.3f}  ({real.id})")
    print()
    print(f"related > unrelated: {related_score > unrelated_score}")


if __name__ == "__main__":
    main()
