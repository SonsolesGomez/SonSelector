"""Son Selector Alumnos — elige al azar a quién preguntar en clase."""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Son Selector Alumnos",
    page_icon=":material/diversity_3:",
    layout="centered",
)

# Estado compartido entre páginas
if "historial_reciente" not in st.session_state:
    st.session_state.historial_reciente = {}
if "spin_id" not in st.session_state:
    st.session_state.spin_id = 0
if "winner_name" not in st.session_state:
    st.session_state.winner_name = None
if "winner_id" not in st.session_state:
    st.session_state.winner_id = None
if "ultimo_grupo_id" not in st.session_state:
    st.session_state.ultimo_grupo_id = None

page = st.navigation(
    [
        st.Page(
            "app_pages/selector.py",
            title="Selector",
            icon=":material/casino:",
            default=True,
        ),
        st.Page(
            "app_pages/grupos.py",
            title="Grupos y alumnos",
            icon=":material/groups:",
        ),
    ],
    position="top",
)

st.title(page.title, icon=page.icon)
page.run()
