"""Acceso a datos: Google Sheets si hay secrets; si no, JSON local."""

from __future__ import annotations

from typing import Any

from lib import json_store


def using_sheets() -> bool:
    try:
        from lib import sheets

        return sheets.sheets_configured()
    except Exception:
        return False


def _store():
    if using_sheets():
        from lib import sheets

        return sheets
    return json_store


def load_db() -> dict[str, Any]:
    return _store().load_db()


def get_grupo(db: dict[str, Any], grupo_id: str) -> dict[str, Any] | None:
    return _store().get_grupo(db, grupo_id)


def veces_de(alumno: dict[str, Any]) -> int:
    return _store().veces_de(alumno)


def add_grupo(nombre: str) -> dict[str, Any]:
    return _store().add_grupo(nombre)


def rename_grupo(grupo_id: str, nombre: str) -> None:
    _store().rename_grupo(grupo_id, nombre)


def delete_grupo(grupo_id: str) -> None:
    _store().delete_grupo(grupo_id)


def add_alumno(grupo_id: str, nombre: str) -> dict[str, Any] | None:
    return _store().add_alumno(grupo_id, nombre)


def add_alumnos_bulk(grupo_id: str, nombres: list[str]) -> int:
    return _store().add_alumnos_bulk(grupo_id, nombres)


def rename_alumno(grupo_id: str, alumno_id: str, nombre: str) -> None:
    _store().rename_alumno(grupo_id, alumno_id, nombre)


def delete_alumno(grupo_id: str, alumno_id: str) -> None:
    _store().delete_alumno(grupo_id, alumno_id)


def incrementar_seleccion(grupo_id: str, alumno_id: str) -> int:
    return _store().incrementar_seleccion(grupo_id, alumno_id)


def reset_contadores_grupo(grupo_id: str) -> int:
    return _store().reset_contadores_grupo(grupo_id)


def migrate_local_json_to_sheets() -> int:
    """Copia data/grupos.json a Google Sheets (sobrescribe las hojas)."""
    if not using_sheets():
        raise RuntimeError("Google Sheets no está configurado en secrets.")
    from lib import sheets

    data = json_store.load_db()
    sheets.replace_all_from_db(data)
    return sum(len(g.get("alumnos", [])) for g in data.get("grupos", []))
