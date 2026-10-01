"""Streamlit UI: upload PDFs, ask questions, and show answers with their sources.

Talks to the FastAPI backend over HTTP only.
"""

from __future__ import annotations

import os

import httpx
import streamlit as st

API_URL = os.getenv("RAG_API_URL", "http://localhost:8000")
HEALTH_TIMEOUT = 5
QUERY_TIMEOUT = 60
INGEST_TIMEOUT = 180

STATUS_LABELS = {
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

def render_answer(response: dict) -> None:
    if response["abstained"]:
        st.warning(response["answer"])
        heading = "Pasajes más cercanos (no se usaron para responder)"
    else:
        st.markdown(response["answer"])
        heading = "Fuentes"
    if not response["citations"]:
        return
    st.caption(heading)
    for c in response["citations"]:
        mark = "  ✓ citado" if c["cited"] else ""
        label = f"[{c['n']}] {c['title']}, p. {c['page']} · score {c['score']:.3f}{mark}"
        with st.expander(label):
            st.caption(c["source"])
            st.text(c["text"])

st.set_page_config(page_title="Agitadores Autmix · RAG", page_icon="🌀")
st.title("Asistente de agitadores Autmix")
st.caption("Responde solo con la información de los catálogos indexados, citando la fuente.")

with st.sidebar:
    status_box = st.container()
    st.header("Cargar documentos")
    uploaded = st.file_uploader("Catálogos en PDF", type="pdf", accept_multiple_files=True)
    if st.button("Indexar", disabled=not uploaded):
        files = [
            ("files", (f.name, f.getvalue(), "application/pdf"))
            for f in uploaded
        ]
        with st.spinner("Indexando..."):
            result, error = call_api("POST", "/ingest", INGEST_TIMEOUT, files=files)
        if error:
            st.error(error)
        else:
            st.success(f"{result['documents']} documentos · {result['chunks']} chunks indexados")
            for reason in result["skipped"]:
                st.warning(reason)
    st.header("Ajustes")
    top_k = st.slider("Pasajes a recuperar (top_k)", min_value=1, max_value=10, value=3)

if "history" not in st.session_state:
    st.session_state.history = []

for turn in st.session_state.history:
    with st.chat_message("user"):
        st.markdown(turn["question"])
    with st.chat_message("assistant"):
        render_answer(turn["response"])

question = st.chat_input("Escribe tu pregunta sobre los agitadores...", max_chars=500)
if question is not None:
    question = question.strip()
    if not question:
        st.warning("La pregunta está vacía.")
    else:
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Buscando en los documentos..."):
                response, error = call_api(
                    "POST", "/query", QUERY_TIMEOUT,
                    json={
                        "question": question,
                        "top_k": top_k,
                    },
                )
            if error:
                st.error(error)
            else:
                render_answer(response)
                st.session_state.history.append({"question": question, "response": response})

with status_box:
    st.header("Estado")
    health, error = call_api("GET", "/health", HEALTH_TIMEOUT)
    if error:
        st.error(error)
    elif health["status"] != "ok":
        st.error(f"Chroma no disponible: {health['chroma']}")
    elif health["chunks"] == 0:
        st.warning("No hay documentos indexados. Sube PDFs para empezar.")
    else:
        st.success(f"{health['chunks']} chunks indexados")