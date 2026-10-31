"""Persistencia local en JSON (desarrollo / OneDrive)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_FILE = DATA_DIR / "grupos.json"
EMPTY_DB: dict[str, Any] = {"grupos": []}


def _ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        save_db(EMPTY_DB)


def load_db() -> dict[str, Any]:
    _ensure_storage()
    try:
        with DATA_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"grupos": []}
    if not isinstance(data, dict) or "grupos" not in data:
        return {"grupos": []}
    return data


def save_db(data: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def get_grupo(db: dict[str, Any], grupo_id: str) -> dict[str, Any] | None:
    for grupo in db.get("grupos", []):
        if grupo.get("id") == grupo_id:
            return grupo
    return None


def veces_de(alumno: dict[str, Any]) -> int:
    try:
        return max(0, int(alumno.get("veces", 0)))
    except (TypeError, ValueError):
        return 0


def add_grupo(nombre: str) -> dict[str, Any]:
    db = load_db()
    grupo = {"id": new_id(), "nombre": nombre.strip(), "alumnos": []}
    db["grupos"].append(grupo)
    save_db(db)
    return grupo


def rename_grupo(grupo_id: str, nombre: str) -> None:
    db = load_db()
    grupo = get_grupo(db, grupo_id)
    if grupo is None:
        return
    grupo["nombre"] = nombre.strip()
    save_db(db)


def delete_grupo(grupo_id: str) -> None:
    db = load_db()
    db["grupos"] = [g for g in db.get("grupos", []) if g.get("id") != grupo_id]
    save_db(db)


def add_alumno(grupo_id: str, nombre: str) -> dict[str, Any] | None:
    db = load_db()
    grupo = get_grupo(db, grupo_id)
    if grupo is None:
        return None
    alumno = {"id": new_id(), "nombre": nombre.strip(), "veces": 0}
    grupo.setdefault("alumnos", []).append(alumno)
    save_db(db)
    return alumno


def add_alumnos_bulk(grupo_id: str, nombres: list[str]) -> int:
    db = load_db()
    grupo = get_grupo(db, grupo_id)
    if grupo is None:
        return 0
    added = 0
    for raw in nombres:
        nombre = raw.strip()
        if not nombre:
            continue
        grupo.setdefault("alumnos", []).append(
            {"id": new_id(), "nombre": nombre, "veces": 0}
        )
        added += 1
    if added:
        save_db(db)
    return added


def rename_alumno(grupo_id: str, alumno_id: str, nombre: str) -> None:
    db = load_db()
    grupo = get_grupo(db, grupo_id)
    if grupo is None:
        return
    for alumno in grupo.get("alumnos", []):
        if alumno.get("id") == alumno_id:
            alumno["nombre"] = nombre.strip()
            break
    save_db(db)


def delete_alumno(grupo_id: str, alumno_id: str) -> None:
    db = load_db()
    grupo = get_grupo(db, grupo_id)
    if grupo is None:
        return
    grupo["alumnos"] = [
        a for a in grupo.get("alumnos", []) if a.get("id") != alumno_id
    ]
    save_db(db)


def incrementar_seleccion(grupo_id: str, alumno_id: str) -> int:
    db = load_db()
    grupo = get_grupo(db, grupo_id)
    if grupo is None:
        return -1
    for alumno in grupo.get("alumnos", []):
        if alumno.get("id") == alumno_id:
            nuevo = veces_de(alumno) + 1
            alumno["veces"] = nuevo
            save_db(db)
            return nuevo
    return -1


def reset_contadores_grupo(grupo_id: str) -> int:
    db = load_db()
    grupo = get_grupo(db, grupo_id)
    if grupo is None:
        return 0
    alumnos = grupo.get("alumnos", [])
    for alumno in alumnos:
        alumno["veces"] = 0
    save_db(db)
    return len(alumnos)
