"""Streamlit UI: upload PDFs, ask questions, and compare agitator models.

Talks to the FastAPI backend over HTTP only.
"""

from __future__ import annotations

import streamlit as st

from api import HEALTH_TIMEOUT, INGEST_TIMEOUT, call_api

st.set_page_config(page_title="Agitadores Autmix · RAG", page_icon="🌀")

pg = st.navigation([
    st.Page("views/chat.py", title="Preguntar", icon="💬", default=True),
    st.Page("views/compare.py", title="Comparar", icon="📊"),
    st.Page("views/select.py", title="Seleccionar", icon="🎯"),
])

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
            for warning in result["warnings"]:
                st.warning(warning)
    st.header("Ajustes")
    st.slider("Pasajes a recuperar (top_k)", min_value=1, max_value=10, value=3, key="top_k")

pg.run()

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
