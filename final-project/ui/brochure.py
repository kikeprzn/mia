"""Show the brochure page a citation points to."""

from __future__ import annotations

from urllib.parse import quote

import streamlit as st

from api import PAGE_TIMEOUT, fetch_bytes


@st.cache_data(show_spinner=False, max_entries=64)
def _page_image(source: str, page: int) -> bytes:
    image, error = fetch_bytes(f"/pages/{quote(source)}/{page}", PAGE_TIMEOUT)
    if error:
        # Raising keeps failures out of the cache, so the page is fetched
        # again once the API is back.
        raise RuntimeError(error)
    return image


def show_page(source: str, page: int, title: str) -> None:
    try:
        st.image(_page_image(source, page), caption=f"{title}, p. {page}")
    except RuntimeError as e:
        st.caption(f"Página no disponible. {e}")
