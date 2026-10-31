"""Maestro de grupos y alumnos."""

from __future__ import annotations

import streamlit as st

from lib.data import (
    add_alumno,
    add_alumnos_bulk,
    add_grupo,
    delete_alumno,
    delete_grupo,
    load_db,
    migrate_local_json_to_sheets,
    rename_alumno,
    rename_grupo,
    reset_contadores_grupo,
    using_sheets,
    veces_de,
)

if using_sheets():
    st.caption("Almacenamiento: Google Sheets (los nombres se conservan en la nube).")
else:
    st.caption(
        "Almacenamiento: archivo local `data/grupos.json`. "
        "Para el móvil, configura Google Sheets en secrets."
    )
    with st.expander("Configurar Google Sheets"):
        st.markdown(
            "Sigue las instrucciones del `README.md`: cuenta de servicio, "
            "compartir la hoja y pegar secretos en `.streamlit/secrets.toml` "
            "(o en Streamlit Cloud)."
        )

try:
    db = load_db()
except Exception as exc:  # noqa: BLE001
    st.error(
        "No se pudieron cargar los datos. Revisa Google Sheets / secrets.\n\n"
        f"Detalle: {exc}"
    )
    st.stop()

grupos = db.get("grupos", [])

st.subheader("Grupos")

with st.form("nuevo_grupo", clear_on_submit=True):
    fila = st.container(horizontal=True, vertical_alignment="bottom")
    with fila:
        nombre_grupo = st.text_input(
            "Nombre del grupo",
            placeholder="Ej. 3º ESO B",
        )
        crear = st.form_submit_button(
            "Crear grupo",
            icon=":material/add:",
            type="primary",
        )
    if crear:
        if nombre_grupo.strip():
            add_grupo(nombre_grupo)
            st.success(f"Grupo «{nombre_grupo.strip()}» creado.", icon=":material/check:")
            st.rerun()
        else:
            st.warning("Escribe un nombre para el grupo.", icon=":material/warning:")

if not grupos:
    st.info(
        "Crea un grupo y después añade los nombres de los alumnos.",
        icon=":material/info:",
    )
    st.stop()

opciones = {g["nombre"]: g for g in grupos}
grupo_nombre = st.selectbox("Grupo a gestionar", options=list(opciones.keys()))
grupo = opciones[grupo_nombre]
alumnos = list(grupo.get("alumnos", []))

st.divider()
st.subheader(f"Alumnos de {grupo['nombre']}")

with st.form("nuevo_alumno", clear_on_submit=True):
    fila_a = st.container(horizontal=True, vertical_alignment="bottom")
    with fila_a:
        nombre_alumno = st.text_input(
            "Añadir alumno",
            placeholder="Nombre y apellidos",
        )
        ok_alumno = st.form_submit_button(
            "Añadir",
            icon=":material/person_add:",
            type="primary",
        )
    if ok_alumno:
        if nombre_alumno.strip():
            add_alumno(grupo["id"], nombre_alumno)
            st.rerun()
        else:
            st.warning("Escribe el nombre del alumno.", icon=":material/warning:")

with st.expander("Pegar lista (un nombre por línea)"):
    lista = st.text_area(
        "Lista de alumnos",
        height=160,
        placeholder="Ana López\nBruno Martín\nCarla Ruiz",
        label_visibility="collapsed",
    )
    if st.button("Importar lista", icon=":material/upload:"):
        lineas = lista.splitlines()
        n = add_alumnos_bulk(grupo["id"], lineas)
        if n:
            st.success(f"Se han añadido {n} alumnos.", icon=":material/check:")
            st.rerun()
        else:
            st.warning("No había nombres que importar.", icon=":material/warning:")

if not alumnos:
    st.caption("Todavía no hay alumnos en este grupo.")
else:
    total_veces = sum(veces_de(a) for a in alumnos)
    st.caption(f"{len(alumnos)} alumnos · {total_veces} selecciones")
    for alumno in sorted(alumnos, key=lambda a: a["nombre"].lower()):
        fila = st.container(horizontal=True, vertical_alignment="center", gap="small")
        with fila:
            nuevo = st.text_input(
                "Nombre",
                value=alumno["nombre"],
                key=f"nom_{alumno['id']}",
                label_visibility="collapsed",
            )
            st.caption(f"{veces_de(alumno)}×")
            if st.button(
                "",
                icon=":material/save:",
                key=f"save_{alumno['id']}",
                help="Guardar nombre",
            ):
                if nuevo.strip() and nuevo.strip() != alumno["nombre"]:
                    rename_alumno(grupo["id"], alumno["id"], nuevo)
                    st.rerun()
            if st.button(
                "",
                icon=":material/delete:",
                key=f"del_{alumno['id']}",
                help="Eliminar alumno",
                type="tertiary",
            ):
                delete_alumno(grupo["id"], alumno["id"])
                st.rerun()

st.divider()
st.subheader("Opciones del grupo")

with st.form("renombrar_grupo"):
    nuevo_nombre = st.text_input("Renombrar grupo", value=grupo["nombre"])
    if st.form_submit_button("Guardar nombre", icon=":material/edit:"):
        if nuevo_nombre.strip() and nuevo_nombre.strip() != grupo["nombre"]:
            rename_grupo(grupo["id"], nuevo_nombre)
            st.rerun()

if st.button(
    "Resetear cuenta del grupo",
    icon=":material/restart_alt:",
    help="Pone a cero las veces seleccionadas de todos los alumnos.",
):
    reset_contadores_grupo(grupo["id"])
    st.rerun()

if st.button(
    "Eliminar este grupo",
    icon=":material/delete_forever:",
    type="primary",
):
    delete_grupo(grupo["id"])
    st.session_state.historial_reciente.pop(grupo["id"], None)
    if st.session_state.get("ultimo_grupo_id") == grupo["id"]:
        st.session_state.ultimo_grupo_id = None
    st.rerun()

if using_sheets():
    st.divider()
    st.subheader("Migración")
    st.caption(
        "Si ya tenías listas en el JSON local, puedes subirlas a la hoja "
        "(sobrescribe el contenido actual de Sheets)."
    )
    if st.button(
        "Subir JSON local a Google Sheets",
        icon=":material/upload:",
    ):
        try:
            n = migrate_local_json_to_sheets()
            st.success(
                f"Migración hecha: {n} alumnos en la hoja.",
                icon=":material/check:",
            )
            st.rerun()
        except Exception as exc:  # noqa: BLE001 - mostrar error de configuración
            st.error(f"No se pudo migrar: {exc}")
