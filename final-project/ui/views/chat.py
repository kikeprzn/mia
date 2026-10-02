"""Chat page: ask a question and show the answer with its sources."""

from __future__ import annotations

import streamlit as st

from api import QUERY_TIMEOUT, call_api
from brochure import show_page


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
            text, page = st.columns(2)
            text.caption(c["source"])
            text.text(c["text"])
            with page:
                show_page(c["source"], c["page"], c["title"])


st.title("Asistente de agitadores Autmix")
st.caption("Responde solo con la información de los catálogos indexados, citando la fuente.")

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
                        "top_k": st.session_state.top_k,
                    },
                )
            if error:
                st.error(error)
            else:
                render_answer(response)
                st.session_state.history.append({"question": question, "response": response})
