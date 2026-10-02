"""Compare page: put two to four agitator models side by side."""

from __future__ import annotations

import streamlit as st

from api import COMPARE_TIMEOUT, HEALTH_TIMEOUT, call_api

MAX_MODELS = 4


def render_table(result: dict) -> None:
    if not result["rows"]:
        st.warning("No se encontraron especificaciones comparables en estos catálogos.")
        return
    titles = [m["title"] for m in result["models"]]
    table = []
    for row in result["rows"]:
        line = {"Aspecto": row["aspect"]}
        for title, cell in zip(titles, row["cells"]):
            refs = f" [{', '.join(str(n) for n in cell['citations'])}]" if cell["citations"] else ""
            line[title] = cell["value"] + refs
        table.append(line)
    st.table(table, hide_index=True)


def render_passages(result: dict) -> None:
    st.caption("Pasajes usados")
    for p in result["passages"]:
        with st.expander(f"[{p['n']}] {p['title']}, p. {p['page']}"):
            st.text(p["text"])


st.title("Comparar agitadores")
st.caption("Elige entre 2 y 4 modelos para ver sus especificaciones lado a lado.")

sources, error = call_api("GET", "/sources", HEALTH_TIMEOUT)
if error:
    st.error(error)
    st.stop()
if len(sources) < 2:
    st.info("Indexa al menos 2 catálogos para poder compararlos.")
    st.stop()

titles = {s["source"]: s["title"] for s in sources}
selected = st.multiselect(
    "Modelos",
    options=list(titles),
    format_func=titles.get,
    max_selections=MAX_MODELS,
    placeholder="Elige entre 2 y 4 modelos",
)

if st.button("Comparar", type="primary", disabled=len(selected) < 2):
    with st.spinner("Comparando especificaciones..."):
        result, error = call_api("POST", "/compare", COMPARE_TIMEOUT, json={"sources": selected})
    if error:
        st.session_state.pop("comparison", None)
        st.error(error)
    else:
        st.session_state.comparison = result

if "comparison" in st.session_state:
    render_table(st.session_state.comparison)
    render_passages(st.session_state.comparison)
