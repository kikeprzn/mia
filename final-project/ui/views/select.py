"""Select page: find the agitator models that meet a set of requirements."""

from __future__ import annotations

import streamlit as st

from api import HEALTH_TIMEOUT, QUERY_TIMEOUT, call_api
from brochure import show_page

# (field, label, unit, step) in the same order as the API's checks
NUMBERS = [
    ("tank_volume_m3", "Volumen del tanque", "m³", 1.0),
    ("propeller_diameter_mm", "Diámetro de hélice", "mm", 100.0),
    ("anchor_diameter_mm", "Diámetro de ancla", "mm", 100.0),
    ("shaft_length_mm", "Longitud de eje", "mm", 100.0),
    ("motor_power_kw", "Potencia del motor", "kW", 0.5),
    ("output_speed_rpm", "Velocidad de salida", "RPM", 10.0),
]
MARKS = {True: "✅", False: "❌", None: "❔"}


def render_fit(fit: dict, only_failures: bool = False) -> None:
    for c in fit["checks"]:
        if only_failures and c["ok"]:
            continue
        pages = f" (p. {', '.join(str(p) for p in c['pages'])})" if c["pages"] else ""
        st.markdown(f"{MARKS[c['ok']]} **{c['aspect']}**: pides {c['required']}, ofrece {c['offered']}{pages}")


def search(body: dict) -> None:
    st.session_state.pop("selection", None)
    st.session_state.pop("select_error", None)
    if not body:
        st.session_state.select_error = "Indica al menos un requisito."
        return
    result, error = call_api("POST", "/select", QUERY_TIMEOUT, json=body)
    if error:
        st.session_state.select_error = error
    else:
        st.session_state.selection = result


def form_body() -> dict:
    body = {field: st.session_state.get(f"req_{field}") for field, *_ in NUMBERS}
    body["material"] = st.session_state.get("req_material")
    return {k: v for k, v in body.items() if v not in (None, 0.0)}


def interpret() -> None:
    # Runs before the page is redrawn, so the form shows the new values.
    st.session_state.pop("understood", None)
    text = st.session_state.request_text.strip()
    if not text:
        st.session_state.select_error = "Escribe qué necesitas."
        return
    parsed, error = call_api("POST", "/select/parse", QUERY_TIMEOUT, json={"text": text})
    if error:
        st.session_state.select_error = error
        return
    for field, *_ in NUMBERS:
        st.session_state[f"req_{field}"] = parsed[field]
    st.session_state.req_material = parsed["material"]
    st.session_state.understood = parsed
    search(form_body())


st.title("Seleccionar agitador")
st.caption("Describe tu proceso con tus palabras, o llena los requisitos a mano; deja vacío lo que no importe.")

specs, error = call_api("GET", "/specs", HEALTH_TIMEOUT)
if error:
    st.error(error)
    st.stop()
if not specs:
    st.info("Aún no hay especificaciones extraídas. Indexa los catálogos o ejecuta `python -m scripts.build_specs`.")
    st.stop()

materials = sorted({m for s in specs for m in s["materials"]})
for field, *_ in NUMBERS:
    st.session_state.setdefault(f"req_{field}", None)
st.session_state.setdefault("req_material", None)

st.text_input(
    "¿Qué necesitas?",
    key="request_text",
    max_chars=500,
    placeholder="Tanque de 3 m³ en titanio con motor de 4 kW",
)
st.button("Interpretar y buscar", on_click=interpret)

if "understood" in st.session_state:
    parsed = st.session_state.understood
    parts = [
        f"{label} {parsed[field]:g} {unit}" for field, label, unit, _ in NUMBERS if parsed[field] is not None
    ]
    if parsed["material"]:
        parts.append(f"Material {parsed['material']}")
    st.info("Entendí: " + (" · ".join(parts) if parts else "ningún requisito que pueda filtrar") + ". Puedes corregirlo abajo.")
    if parsed["unsupported"]:
        st.warning("No puedo filtrar por: " + ", ".join(parsed["unsupported"]) + ". Los catálogos no tienen ese dato.")

with st.form("requirements"):
    left, right = st.columns(2)
    for i, (field, label, unit, step) in enumerate(NUMBERS):
        column = left if i % 2 == 0 else right
        column.number_input(
            f"{label} ({unit})", key=f"req_{field}", min_value=0.0, step=step, placeholder="sin requisito",
        )
    st.selectbox("Material", materials, key="req_material", placeholder="sin requisito")
    if st.form_submit_button("Buscar", type="primary"):
        st.session_state.pop("understood", None)
        search(form_body())

if "select_error" in st.session_state:
    st.warning(st.session_state.select_error)

if "selection" in st.session_state:
    result = st.session_state.selection
    matches, rejected = result["matches"], result["rejected"]
    if matches:
        st.subheader(f"{len(matches)} modelo(s) cumplen todos los requisitos")
        for fit in matches:
            with st.container(border=True):
                st.markdown(f"**{fit['title']}**")
                render_fit(fit)
                pages = sorted({p for c in fit["checks"] for p in c["pages"]})
                if pages:
                    with st.expander("Ver páginas citadas"):
                        for column, page in zip(st.columns(len(pages)), pages):
                            with column:
                                show_page(fit["source"], page, fit["title"])
    else:
        st.warning("Ningún modelo cumple todos los requisitos.")
    if rejected:
        with st.expander(f"Modelos descartados ({len(rejected)})"):
            for fit in rejected:
                st.markdown(f"**{fit['title']}**")
                render_fit(fit, only_failures=True)
