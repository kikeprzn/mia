"""Select page: find the agitator models that meet a set of requirements."""

from __future__ import annotations

import streamlit as st

from api import HEALTH_TIMEOUT, QUERY_TIMEOUT, call_api

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


st.title("Seleccionar agitador")
st.caption("Indica los requisitos de tu proceso; deja vacío lo que no importe.")

specs, error = call_api("GET", "/specs", HEALTH_TIMEOUT)
if error:
    st.error(error)
    st.stop()
if not specs:
    st.info("Aún no hay especificaciones extraídas. Indexa los catálogos o ejecuta `python -m scripts.build_specs`.")
    st.stop()

materials = sorted({m for s in specs for m in s["materials"]})

with st.form("requirements"):
    left, right = st.columns(2)
    values = {}
    for i, (field, label, unit, step) in enumerate(NUMBERS):
        column = left if i % 2 == 0 else right
        values[field] = column.number_input(
            f"{label} ({unit})", min_value=0.0, value=None, step=step, placeholder="sin requisito",
        )
    values["material"] = st.selectbox("Material", materials, index=None, placeholder="sin requisito")
    submitted = st.form_submit_button("Buscar", type="primary")

if submitted:
    body = {k: v for k, v in values.items() if v not in (None, 0.0)}
    if not body:
        st.warning("Indica al menos un requisito.")
        st.session_state.pop("selection", None)
    else:
        result, error = call_api("POST", "/select", QUERY_TIMEOUT, json=body)
        if error:
            st.session_state.pop("selection", None)
            st.error(error)
        else:
            st.session_state.selection = result

if "selection" in st.session_state:
    result = st.session_state.selection
    matches, rejected = result["matches"], result["rejected"]
    if matches:
        st.subheader(f"{len(matches)} modelo(s) cumplen todos los requisitos")
        for fit in matches:
            with st.container(border=True):
                st.markdown(f"**{fit['title']}**")
                render_fit(fit)
    else:
        st.warning("Ningún modelo cumple todos los requisitos.")
    if rejected:
        with st.expander(f"Modelos descartados ({len(rejected)})"):
            for fit in rejected:
                st.markdown(f"**{fit['title']}**")
                render_fit(fit, only_failures=True)
