"""HTTP client for the RAG API, shared by every page."""

from __future__ import annotations

import os

import httpx

API_URL = os.getenv("RAG_API_URL", "http://localhost:8000")
HEALTH_TIMEOUT = 5
QUERY_TIMEOUT = 60
COMPARE_TIMEOUT = 90
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

    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text
    if isinstance(detail, list): # 422: FastAPI sends a list of validation errors
        detail = "; " .join(item.get("msg", "") for item in detail)
    label = STATUS_LABELS.get(response.status_code, f"Error {response.status_code}")
    return None, f"{label}: {detail}"
