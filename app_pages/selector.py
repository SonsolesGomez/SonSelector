"""Pantalla principal: selector aleatorio de alumnos."""

from __future__ import annotations

import random

import streamlit as st

from lib import data as store
from lib.roulette import show_roulette

HISTORIAL_MAX = 15


def _init_session() -> None:
    defaults = {
        "spin_id": 0,
        "winner_name": None,
        "winner_id": None,
        "historial_reciente": {},  # grupo_id -> lista de alumno_id recientes
        "ultimo_grupo_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _historial(grupo_id: str) -> list[str]:
    return list(st.session_state.historial_reciente.get(grupo_id, []))


def _registrar(grupo_id: str, alumno_id: str, evitar: int) -> None:
    hist = _historial(grupo_id)
    hist.append(alumno_id)
    # 0 = sin repetición en toda la sesión → guardar historial completo
    if evitar == 0:
        st.session_state.historial_reciente[grupo_id] = hist
    else:
        st.session_state.historial_reciente[grupo_id] = hist[-HISTORIAL_MAX:]


_init_session()

try:
    db = store.load_db()
except Exception as exc:  # noqa: BLE001
    st.error(
        "No se pudieron cargar los datos. Revisa la configuración de Google Sheets "
        f"en secrets.\n\nDetalle: {exc}"
    )
    st.stop()

grupos = db.get("grupos", [])

if store.using_sheets():
    st.caption("Datos en Google Sheets")

if not grupos:
    st.info(
        "Todavía no hay grupos. Ve a **Grupos y alumnos** para crear el primero "
        "y añadir nombres.",
        icon=":material/info:",
    )
    st.stop()

opciones = {g["nombre"]: g for g in grupos}
nombres_grupo = list(opciones.keys())

default_index = 0
if st.session_state.ultimo_grupo_id:
    for i, g in enumerate(grupos):
        if g["id"] == st.session_state.ultimo_grupo_id:
            default_index = i
            break

fila = st.container(horizontal=True, vertical_alignment="bottom", gap="medium")
with fila:
    grupo_nombre = st.selectbox(
        "Grupo",
        options=nombres_grupo,
        index=default_index,
    )
    if "evitar_ultimos" not in st.session_state:
        st.session_state.evitar_ultimos = 2
    elif not isinstance(st.session_state.evitar_ultimos, int):
        st.session_state.evitar_ultimos = 2
    else:
        st.session_state.evitar_ultimos = max(
            0, min(HISTORIAL_MAX, int(st.session_state.evitar_ultimos))
        )
    evitar_n = st.number_input(
        "No repetir últimos",
        min_value=0,
        max_value=HISTORIAL_MAX,
        step=1,
        key="evitar_ultimos",
        help=(
            "0 = no se repite nunca en la sesión (hasta que salgan todos). "
            "1–15 = no salen los últimos N alumnos elegidos."
        ),
        width=160,
    )

grupo = opciones[grupo_nombre]
st.session_state.ultimo_grupo_id = grupo["id"]
evitar_n = int(evitar_n if evitar_n is not None else 2)

alumnos = list(grupo.get("alumnos", []))
hist = _historial(grupo["id"])
if evitar_n == 0:
    recientes = set(hist)  # nadie ya salido en la sesión
else:
    recientes = set(hist[-evitar_n:]) if hist else set()
candidatos = [a for a in alumnos if a["id"] not in recientes]
if not candidatos:
    if evitar_n == 0 and alumnos:
        # Ronda completa: al pulsar de nuevo se podrá empezar otra
        candidatos = list(alumnos)
    elif hist:
        candidatos = [a for a in alumnos if a["id"] != hist[-1]] or list(alumnos)
    else:
        candidatos = list(alumnos)

total_veces = sum(store.veces_de(a) for a in alumnos)
st.caption(f"{len(alumnos)} alumnos · {total_veces} selecciones registradas")

nombres_visibles = [a["nombre"] for a in alumnos]
puede_seleccionar = bool(candidatos)

pulsado = show_roulette(
    names=nombres_visibles,
    winner=st.session_state.winner_name,
    spin_id=st.session_state.spin_id,
    enabled=puede_seleccionar,
)
if pulsado and puede_seleccionar:
    if evitar_n == 0 and set(hist) >= {a["id"] for a in alumnos}:
        st.session_state.historial_reciente[grupo["id"]] = []
        hist = []
        candidatos = list(alumnos)
    elegido = random.choice(candidatos)
    st.session_state.winner_name = elegido["nombre"]
    st.session_state.winner_id = elegido["id"]
    st.session_state.spin_id = int(st.session_state.spin_id) + 1
    _registrar(grupo["id"], elegido["id"], evitar_n)
    store.incrementar_seleccion(grupo["id"], elegido["id"])
    st.rerun()

if not alumnos:
    st.warning(
        "Este grupo no tiene alumnos. Añádelos en **Grupos y alumnos**.",
        icon=":material/warning:",
    )
else:
    ranking = sorted(
        alumnos,
        key=lambda a: (-store.veces_de(a), a["nombre"].lower()),
    )
    with st.expander(f"Registro de selecciones ({total_veces})"):
        for alumno in ranking:
            st.write(f"**{store.veces_de(alumno)}** · {alumno['nombre']}")
        if st.button(
            "Resetear cuenta del grupo",
            icon=":material/restart_alt:",
            help="Pone a cero las veces de todos los alumnos de este grupo.",
            key=f"reset_veces_{grupo['id']}",
        ):
            store.reset_contadores_grupo(grupo["id"])
            st.rerun()
