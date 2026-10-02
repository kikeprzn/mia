"""HTTP client for the RAG API, shared by every page."""

from __future__ import annotations

import os

import httpx

# 127.0.0.1 rather than localhost: on Windows "localhost" tries IPv6 first and
# waits about 2 s per request before falling back to the IPv4 address uvicorn uses.
API_URL = os.getenv("RAG_API_URL", "http://127.0.0.1:8000")
HEALTH_TIMEOUT = 5
QUERY_TIMEOUT = 60
COMPARE_TIMEOUT = 90
PAGE_TIMEOUT = 30
INGEST_TIMEOUT = 180

STATUS_LABELS = {
    404: "No encontrado",
    422: "Petición inválida",
    502: "Error de Google AI",
    503: "Servicio no disponible",
}


def call_api(method: str, path: str, timeout: float, **kwargs) -> tuple[dict | None, str | None]:
    try:
        response = httpx.request(method, f"{API_URL}{path}", timeout=timeout, **kwargs)
    except httpx.ConnectError:
        return None, "No se pudo conectar con la API. ¿Está corriendo uvicorn en el puerto 8000?"
    except httpx.TimeoutException:
        return None, "La API tardó demasiado en responder. Inténtalo de nuevo."

    if response.status_code == 200:
        return response.json(), None
    return None, _error_message(response)


def fetch_bytes(path: str, timeout: float) -> tuple[bytes | None, str | None]:
    try:
        response = httpx.get(f"{API_URL}{path}", timeout=timeout)
    except httpx.ConnectError:
        return None, "No se pudo conectar con la API. ¿Está corriendo uvicorn en el puerto 8000?"
    except httpx.TimeoutException:
        return None, "La API tardó demasiado en responder. Inténtalo de nuevo."

    if response.status_code == 200:
        return response.content, None
    return None, _error_message(response)


def _error_message(response: httpx.Response) -> str:
    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text
    if isinstance(detail, list): # 422: FastAPI sends a list of validation errors
        detail = "; " .join(item.get("msg", "") for item in detail)
    label = STATUS_LABELS.get(response.status_code, f"Error {response.status_code}")
    return f"{label}: {detail}"
