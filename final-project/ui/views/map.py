"""Map page: every chunk of the index in 2D, and where a question lands."""

from __future__ import annotations

import altair as alt
import streamlit as st

from api import QUERY_TIMEOUT, call_api

# Two validated hues (light / dark steps) plus a neutral for everything else.
# Five families can't each get a colour that stays distinguishable in a
# scatter plot, so the group is shown by shape (named in the legend), and
# colour only marks what the question retrieved.
COLORS = {
    "light": {"retrieved": "#2a78d6", "question": "#eb6834"},
    "dark": {"retrieved": "#3987e5", "question": "#d95926"},
}
NEUTRAL = "#8f8f88"
STAR = "M0,-1L0.29,-0.4L0.95,-0.31L0.48,0.15L0.59,0.81L0,0.5L-0.59,0.81L-0.48,0.15L-0.95,-0.31L-0.29,-0.4Z"
GROUPINGS = {"Familia": "family", "Página": "page_label"}


def fetch_map(question: str | None) -> None:
    body = {"question": question, "top_k": st.session_state.top_k} if question else {}
    with st.spinner("Calculando el mapa..."):
        data, error = call_api("POST", "/map", QUERY_TIMEOUT, json=body)
    if error:
        st.error(error)
    else:
        st.session_state.map_data = data


def build_chart(data: dict, group: str, palette: dict) -> alt.LayerChart:
    neighbors = {n["id"]: n for n in data["question"]["neighbors"]} if data["question"] else {}
    rows = []
    for p in data["points"]:
        n = neighbors.get(p["id"])
        rows.append({
            "x": p["x"], "y": p["y"],
            "title": p["title"],
            "family": p["family"],
            "page_label": f"Página {p['page']}",
            "where": f"{p['title']}, p. {p['page']}",
            "role": f"Recuperado [{n['rank']}]" if n else "Resto",
            "kind": "Recuperado" if n else "Resto",
            "score": n["score"] if n else None,
            "snippet": p["text"][:140] + ("…" if len(p["text"]) > 140 else ""),
        })
    points = alt.Data(values=rows)
    pc1, pc2 = data["explained"]
    x = alt.X("x:Q", title=f"Componente 1 ({pc1:.0%} de la variación)", axis=alt.Axis(labels=False, ticks=False))
    y = alt.Y("y:Q", title=f"Componente 2 ({pc2:.0%} de la variación)", axis=alt.Axis(labels=False, ticks=False))
    group_title = "Familia" if group == "family" else "Página"

    chunks = alt.Chart(points).mark_point(filled=True, size=140, opacity=0.9, strokeWidth=0).encode(
        x=x,
        y=y,
        shape=alt.Shape(
            f"{group}:N",
            title=group_title,
            legend=alt.Legend(symbolFillColor=NEUTRAL, symbolStrokeColor=NEUTRAL, symbolSize=140),
        ),
        color=alt.Color(
            "kind:N",
            title="Pregunta",
            scale=alt.Scale(domain=["Recuperado", "Resto"], range=[palette["retrieved"], NEUTRAL]),
            legend=alt.Legend() if neighbors else None,
        ),
        order=alt.Order("kind:N", sort="descending"),  # retrieved chunks drawn on top
        tooltip=[
            alt.Tooltip("where:N", title="Chunk"),
            alt.Tooltip("role:N", title="Rol"),
            alt.Tooltip("score:Q", title="Score", format=".3f"),
            alt.Tooltip("snippet:N", title="Texto"),
        ],
    )

    layers = [chunks]
    if data["question"]:
        q = data["question"]
        retrieved = [r for r in rows if r["kind"] == "Recuperado"]
        links = alt.Chart(alt.Data(values=[
            {"x": q["x"], "y": q["y"], "x2": r["x"], "y2": r["y"]} for r in retrieved
        ])).mark_rule(color=palette["retrieved"], strokeWidth=1.5, opacity=0.6).encode(
            x="x:Q", y="y:Q", x2="x2:Q", y2="y2:Q",
        )
        star = alt.Chart(alt.Data(values=[{"x": q["x"], "y": q["y"], "text": q["text"]}])).mark_point(
            shape=STAR, size=420, filled=True, color=palette["question"], opacity=1,
        ).encode(x="x:Q", y="y:Q", tooltip=[alt.Tooltip("text:N", title="Pregunta")])
        layers = [links, chunks, star]

    return alt.layer(*layers).properties(height=520)


st.title("Mapa de embeddings")
st.caption(
    "Cada punto es un chunk del índice, proyectado de 3 072 dimensiones a 2. "
    "Escribe una pregunta para ver dónde cae y qué chunks recupera."
)

with st.form("map_question"):
    question = st.text_input("Pregunta (opcional)", max_chars=500, placeholder="¿Qué materiales tiene el agitador RT-RTG?")
    if st.form_submit_button("Mostrar en el mapa", type="primary"):
        fetch_map(question.strip() or None)

if "map_data" not in st.session_state:
    fetch_map(None)
if "map_data" not in st.session_state:
    st.stop()

data = st.session_state.map_data
group = GROUPINGS[st.radio("Agrupar por", list(GROUPINGS), horizontal=True)]
theme = "dark" if getattr(st.context.theme, "type", "dark") == "dark" else "light"
st.altair_chart(build_chart(data, group, COLORS[theme]), width="stretch")

pc1, pc2 = data["explained"]
st.caption(
    f"Los dos ejes conservan {pc1 + pc2:.0%} de la variación entre los vectores: "
    "estar cerca en el mapa es solo una pista. Las líneas van a los vecinos reales, "
    "medidos con las 3 072 dimensiones."
)

if data["question"]:
    titles = {p["id"]: f"{p['title']}, p. {p['page']}" for p in data["points"]}
    st.markdown("**Chunks recuperados**")
    for n in data["question"]["neighbors"]:
        st.markdown(f"[{n['rank']}] {titles.get(n['id'], n['id'])} · score {n['score']:.3f}")

with st.expander("Ver los datos del mapa"):
    st.dataframe(
        [{"Chunk": f"{p['title']}, p. {p['page']}", "Familia": p["family"], "x": round(p["x"], 3), "y": round(p["y"], 3)}
         for p in data["points"]],
        hide_index=True,
    )
