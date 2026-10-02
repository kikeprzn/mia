import os
from pathlib import Path
from dotenv import load_dotenv
from functools import lru_cache

import httpx
from google.genai import Client, types


ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
EMBED_MODEL = "gemini-embedding-001"
BATCH_SIZE = 50

@lru_cache(maxsize=1)
def get_client() -> Client:
    load_dotenv(ENV_PATH)
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set")    
    
    # Google returns 429/503 when the model is busy; retry those with backoff.
    retry = types.HttpRetryOptions(attempts=5, initial_delay=1.0, http_status_codes=[429, 503])
    return Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            retry_options=retry,
            # Connect over IPv4: on networks with a broken IPv6 route, httpx waits
            # for the IPv6 attempt to time out on every request.
            client_args={"transport": httpx.HTTPTransport(local_address="0.0.0.0")},
            timeout=60_000,  # ms; a network problem becomes an error, not a hang
        ),
    )

def _embed(texts: list[str], task_type: str) -> list[list[float]]:
    client = get_client()
    vectors : list[list[float]] = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]
        response = client.models.embed_content(
            model=EMBED_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(task_type=task_type)
        )
        vectors += [e.values for e in response.embeddings]
    return vectors

def embed_documents(texts: list[str]) -> list[list[float]]:
    return _embed(texts, "RETRIEVAL_DOCUMENT")

def embed_query(text: str) -> list[float]:
    return _embed([text], "RETRIEVAL_QUERY")[0]
