"""Arranque común de los scripts: pone src/ en el camino de importación y lee --raiz.

Los scripts viven en `_comun/scripts/` o, copiados, en `<repo>/scripts/insumos_eevv/`; el paquete en `src/eevv_insumos/`
de la misma raíz. Se busca subiendo desde este archivo, sin rutas absolutas.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SRC = next(p / "src" for p in Path(__file__).resolve().parents if (p / "src" / "eevv_insumos").is_dir())
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from eevv_insumos import rutas  # noqa: E402


def argumentos(descripcion: str) -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=descripcion)
    ap.add_argument("--raiz", default=None,
                    help="raíz del repositorio (por defecto: variable RAIZ o la carpeta que contiene src/eevv_insumos)")
    return ap


def preparar(args) -> Path:
    raiz = rutas.fijar_raiz(args.raiz)
    print(f"[raíz] {raiz.name}/", flush=True)
    return raiz


def anios(texto: str | None, por_defecto) -> list[int]:
    """«1998-2001,2005» -> [1998, 1999, 2000, 2001, 2005]."""
    if not texto:
        return list(por_defecto)
    out = []
    for parte in texto.split(","):
        a, _, b = parte.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return out
