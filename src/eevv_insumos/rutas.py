"""Rutas del paquete de insumos EEVV. Ninguna ruta absoluta.

La raíz (RAIZ) es la carpeta del repositorio que contiene `src/eevv_insumos/`. Se resuelve así, en orden:

1. el argumento `--raiz` de cualquier script (lo fija `fijar_raiz`);
2. la variable de entorno `RAIZ`;
3. la primera carpeta, subiendo desde este archivo, que contenga `src/eevv_insumos/`.

Con la tercera regla el mismo código funciona en `_comun/` (scripts en `_comun/scripts/`) y copiado dentro de un
repositorio de artículo (scripts en `<repo>/scripts/insumos_eevv/`, paquete en `<repo>/src/eevv_insumos/`).

Debajo de RAIZ:
    data/raw/                  insumos originales (zips del DANE, proyecciones de población) y MANIFIESTO.csv
    data/interim/eevv/         microdato intermedio de defunciones 2020-2025 (01_extraer.py)
    data/processed/            bases que leen los artículos
"""
from __future__ import annotations

import os
from pathlib import Path


def _raiz_por_defecto() -> Path:
    if os.environ.get("RAIZ"):
        return Path(os.environ["RAIZ"]).resolve()
    for p in Path(__file__).resolve().parents:
        if (p / "src" / "eevv_insumos").is_dir():
            return p
    raise RuntimeError("No encuentro la raíz del repositorio (carpeta con src/eevv_insumos/). Use --raiz o RAIZ.")


RAIZ = _raiz_por_defecto()


def fijar_raiz(raiz: str | Path | None) -> Path:
    """Cambia la raíz para todo el proceso (lo llaman los scripts con --raiz)."""
    global RAIZ
    if raiz:
        RAIZ = Path(raiz).resolve()
    return RAIZ


def crudo() -> Path:
    return RAIZ / "data" / "raw"


def intermedio() -> Path:
    return RAIZ / "data" / "interim" / "eevv"


def procesado() -> Path:
    return RAIZ / "data" / "processed"


def ext() -> Path:
    return procesado() / "ext"


def manifiesto() -> Path:
    return crudo() / "MANIFIESTO.csv"


def relativa(p: Path) -> str:
    """Ruta relativa a RAIZ para imprimir (nunca se imprime una ruta absoluta)."""
    try:
        return str(Path(p).resolve().relative_to(RAIZ))
    except ValueError:
        return Path(p).name
