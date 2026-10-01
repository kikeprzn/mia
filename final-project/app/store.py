"""ChromaDB: add chunks with their Google AI vectors and query the top-k.

The Retrieved shape is adapted from the course's RAG/project/rag/retrieve.py.
"""

from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from app.chunk import Chunk
import chromadb

CHROMA_PATH = Path(__file__).resolve().parent.parent / "chroma"
COLLECTION = "autmix_agitators"

@dataclass(frozen=True)
class Retrieved:
    rank: int
    chunk: Chunk
    score: float  # cosine similarity: 1 - Chroma distance

@lru_cache(maxsize=1)
def _collection():
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_or_create_collection(
        COLLECTION,
        configuration={"hnsw": {"space": "cosine"}},
        embedding_function=None,
    )

def count() -> int:
    return _collection().count()


def upsert(chunks: list[Chunk], embeddings: list[list[float]]) -> None:
    if len(chunks) != len(embeddings):
        raise ValueError(f"{len(chunks)} chunks but {len(embeddings)} embeddings")

    _collection().upsert(
        ids=[c.id for c in chunks],
        embeddings=embeddings,
        documents = [c.text for c in chunks],
        metadatas=[
            {
                "title": c.title, 
                "source": c.source, 
                "page": c.page, 
                "index": c.index
            }  for c in chunks
        ]
    )

def query(embedding: list[float], k: int, source: str | None = None) -> list[Retrieved]:
    if count() == 0:
        return []
    result = _collection().query(
        query_embeddings=[embedding],
        n_results = k,
        where = {"source": source} if source else None,
    )

    ids = result["ids"][0]
    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]

    retrieved = []
    for rank, (id_, text, meta, distance) in enumerate(zip(ids, documents, metadatas, distances), start=1):
        chunk = Chunk(
            id=id_,
            title=meta["title"],
            source=meta["source"],
            page=meta["page"],
            index=meta["index"],
            text=text,
        )

        retrieved.append(Retrieved(rank=rank, chunk=chunk, score= 1 - distance))
    return retrieved