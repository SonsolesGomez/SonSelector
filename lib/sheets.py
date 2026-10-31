"""Persistencia en Google Sheets (grupos y alumnos)."""

from __future__ import annotations

import uuid
from typing import Any

import streamlit as st

WS_GRUPOS = "grupos"
WS_ALUMNOS = "alumnos"
HEADERS_GRUPOS = ["id", "nombre"]
HEADERS_ALUMNOS = ["id", "grupo_id", "nombre", "veces"]


def sheets_configured() -> bool:
    try:
        secrets = st.secrets
    except Exception:
        return False
    if "gcp_service_account" not in secrets:
        return False
    sheets = secrets.get("sheets", {})
    return bool(sheets.get("spreadsheet_id") or sheets.get("spreadsheet"))


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def veces_de(alumno: dict[str, Any]) -> int:
    try:
        return max(0, int(alumno.get("veces", 0)))
    except (TypeError, ValueError):
        return 0


@st.cache_resource(show_spinner=False)
def _client():
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    info = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)


def _spreadsheet():
    client = _client()
    sheets = st.secrets["sheets"]
    spreadsheet_id = sheets.get("spreadsheet_id")
    try:
        if spreadsheet_id:
            return client.open_by_key(str(spreadsheet_id))
        name = sheets.get("spreadsheet")
        if not name:
            raise RuntimeError(
                "Falta sheets.spreadsheet_id o sheets.spreadsheet en secrets."
            )
        return client.open(str(name))
    except PermissionError as exc:
        email = st.secrets.get("gcp_service_account", {}).get("client_email", "")
        raise RuntimeError(
            "Sin permiso para abrir la hoja. Comprueba: "
            "1) En Google Cloud, activa **Google Sheets API** y **Google Drive API** "
            "en el mismo proyecto de la cuenta de servicio. "
            "2) Comparte el Spreadsheet con este email (Editor): "
            f"{email}"
        ) from exc
    except Exception as exc:
        msg = str(exc) or type(exc).__name__
        if "has not been used" in msg or "SERVICE_DISABLED" in msg or "disabled" in msg.lower():
            raise RuntimeError(
                "La API de Google Sheets no está activada en tu proyecto de Google Cloud. "
                "Actívala aquí: https://console.cloud.google.com/apis/library/sheets.googleapis.com "
                "y también Drive API. Espera 1–2 minutos y reintenta."
            ) from exc
        raise RuntimeError(f"No se pudo abrir Google Sheets: {msg}") from exc


def _ensure_worksheet(sh, title: str, headers: list[str]):
    try:
        ws = sh.worksheet(title)
    except Exception:
        ws = sh.add_worksheet(title=title, rows=2000, cols=len(headers))
        ws.append_row(headers, value_input_option="USER_ENTERED")
        return ws

    values = ws.get_all_values()
    if not values:
        ws.append_row(headers, value_input_option="USER_ENTERED")
    elif [c.strip().lower() for c in values[0]] != headers:
        # Cabeceras distintas: no machacar datos; exigir formato correcto
        raise RuntimeError(
            f"La hoja «{title}» debe empezar con: {', '.join(headers)}"
        )
    return ws


def _worksheets():
    sh = _spreadsheet()
    grupos = _ensure_worksheet(sh, WS_GRUPOS, HEADERS_GRUPOS)
    alumnos = _ensure_worksheet(sh, WS_ALUMNOS, HEADERS_ALUMNOS)
    return grupos, alumnos


def clear_load_cache() -> None:
    load_db.clear()


@st.cache_data(ttl=15, show_spinner="Cargando grupos…")
def load_db() -> dict[str, Any]:
    ws_grupos, ws_alumnos = _worksheets()
    grupos_rows = ws_grupos.get_all_records()
    alumnos_rows = ws_alumnos.get_all_records()

    grupos: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for row in grupos_rows:
        gid = str(row.get("id", "")).strip()
        nombre = str(row.get("nombre", "")).strip()
        if not gid or not nombre:
            continue
        grupo = {"id": gid, "nombre": nombre, "alumnos": []}
        grupos.append(grupo)
        by_id[gid] = grupo

    for row in alumnos_rows:
        gid = str(row.get("grupo_id", "")).strip()
        aid = str(row.get("id", "")).strip()
        nombre = str(row.get("nombre", "")).strip()
        if not gid or not aid or not nombre:
            continue
        if gid not in by_id:
            # Alumno huérfano: crear grupo placeholder
            by_id[gid] = {"id": gid, "nombre": f"(grupo {gid})", "alumnos": []}
            grupos.append(by_id[gid])
        by_id[gid]["alumnos"].append(
            {"id": aid, "nombre": nombre, "veces": veces_de({"veces": row.get("veces", 0)})}
        )
    return {"grupos": grupos}


def get_grupo(db: dict[str, Any], grupo_id: str) -> dict[str, Any] | None:
    for grupo in db.get("grupos", []):
        if grupo.get("id") == grupo_id:
            return grupo
    return None


def add_grupo(nombre: str) -> dict[str, Any]:
    ws_grupos, _ = _worksheets()
    grupo = {"id": new_id(), "nombre": nombre.strip(), "alumnos": []}
    ws_grupos.append_row(
        [grupo["id"], grupo["nombre"]], value_input_option="USER_ENTERED"
    )
    clear_load_cache()
    return grupo


def _find_in_column(ws, value: str, column: int = 1):
    return ws.find(value, in_column=column)


def rename_grupo(grupo_id: str, nombre: str) -> None:
    ws_grupos, _ = _worksheets()
    cell = _find_in_column(ws_grupos, grupo_id, 1)
    if cell is None:
        return
    ws_grupos.update_cell(cell.row, 2, nombre.strip())
    clear_load_cache()


def delete_grupo(grupo_id: str) -> None:
    ws_grupos, ws_alumnos = _worksheets()
    alumnos_vals = ws_alumnos.get_all_values()
    for i in range(len(alumnos_vals) - 1, 0, -1):
        row = alumnos_vals[i]
        if len(row) > 1 and row[1].strip() == grupo_id:
            ws_alumnos.delete_rows(i + 1)
    cell = _find_in_column(ws_grupos, grupo_id, 1)
    if cell is not None:
        ws_grupos.delete_rows(cell.row)
    clear_load_cache()


def add_alumno(grupo_id: str, nombre: str) -> dict[str, Any] | None:
    db = load_db()
    if get_grupo(db, grupo_id) is None:
        return None
    _, ws_alumnos = _worksheets()
    alumno = {"id": new_id(), "nombre": nombre.strip(), "veces": 0}
    ws_alumnos.append_row(
        [alumno["id"], grupo_id, alumno["nombre"], 0],
        value_input_option="USER_ENTERED",
    )
    clear_load_cache()
    return alumno


def add_alumnos_bulk(grupo_id: str, nombres: list[str]) -> int:
    db = load_db()
    if get_grupo(db, grupo_id) is None:
        return 0
    rows = []
    for raw in nombres:
        nombre = raw.strip()
        if not nombre:
            continue
        rows.append([new_id(), grupo_id, nombre, 0])
    if not rows:
        return 0
    _, ws_alumnos = _worksheets()
    ws_alumnos.append_rows(rows, value_input_option="USER_ENTERED")
    clear_load_cache()
    return len(rows)


def rename_alumno(grupo_id: str, alumno_id: str, nombre: str) -> None:
    _, ws_alumnos = _worksheets()
    cell = _find_in_column(ws_alumnos, alumno_id, 1)
    if cell is None:
        return
    row = ws_alumnos.row_values(cell.row)
    if len(row) < 2 or row[1].strip() != grupo_id:
        return
    ws_alumnos.update_cell(cell.row, 3, nombre.strip())
    clear_load_cache()


def delete_alumno(grupo_id: str, alumno_id: str) -> None:
    _, ws_alumnos = _worksheets()
    cell = _find_in_column(ws_alumnos, alumno_id, 1)
    if cell is None:
        return
    row = ws_alumnos.row_values(cell.row)
    if len(row) < 2 or row[1].strip() != grupo_id:
        return
    ws_alumnos.delete_rows(cell.row)
    clear_load_cache()


def incrementar_seleccion(grupo_id: str, alumno_id: str) -> int:
    _, ws_alumnos = _worksheets()
    cell = _find_in_column(ws_alumnos, alumno_id, 1)
    if cell is None:
        return -1
    row = ws_alumnos.row_values(cell.row)
    if len(row) < 2 or row[1].strip() != grupo_id:
        return -1
    actual = 0
    if len(row) >= 4:
        try:
            actual = max(0, int(row[3]))
        except ValueError:
            actual = 0
    nuevo = actual + 1
    ws_alumnos.update_cell(cell.row, 4, nuevo)
    clear_load_cache()
    return nuevo


def reset_contadores_grupo(grupo_id: str) -> int:
    _, ws_alumnos = _worksheets()
    values = ws_alumnos.get_all_values()
    n = 0
    for i, row in enumerate(values[1:], start=2):
        if len(row) > 1 and row[1].strip() == grupo_id:
            ws_alumnos.update_cell(i, 4, 0)
            n += 1
    clear_load_cache()
    return n


def replace_all_from_db(data: dict[str, Any]) -> None:
    """Sobrescribe las hojas con el contenido de un dict estilo JSON local."""
    ws_grupos, ws_alumnos = _worksheets()
    ws_grupos.clear()
    ws_alumnos.clear()
    ws_grupos.append_row(HEADERS_GRUPOS, value_input_option="USER_ENTERED")
    ws_alumnos.append_row(HEADERS_ALUMNOS, value_input_option="USER_ENTERED")

    grupos_rows = []
    alumnos_rows = []
    for grupo in data.get("grupos", []):
        gid = str(grupo.get("id") or new_id())
        gnom = str(grupo.get("nombre", "")).strip()
        if not gnom:
            continue
        grupos_rows.append([gid, gnom])
        for alumno in grupo.get("alumnos", []):
            aid = str(alumno.get("id") or new_id())
            anom = str(alumno.get("nombre", "")).strip()
            if not anom:
                continue
            alumnos_rows.append([aid, gid, anom, veces_de(alumno)])

    if grupos_rows:
        ws_grupos.append_rows(grupos_rows, value_input_option="USER_ENTERED")
    if alumnos_rows:
        ws_alumnos.append_rows(alumnos_rows, value_input_option="USER_ENTERED")
    clear_load_cache()
