"""Carpetas del repositorio, sin rutas absolutas. PROCESADO (variable de entorno) apunta a otra copia de las bases
comunes de Estadísticas Vitales; por defecto, data/processed/ dentro del repositorio (la que construye el nivel B)."""
from __future__ import annotations

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CONFIG = RAIZ / "config"
RAW = RAIZ / "data" / "raw"
ADRES = RAW / "externos" / "adres"
INTERMEDIOS = RAIZ / "data" / "intermedios"
OUTPUT = RAIZ / "output"
PAR = OUTPUT / "parametros"


def procesado() -> Path:
    p = os.environ.get("PROCESADO")
    return Path(p) if p else RAIZ / "data" / "processed"


def crudo() -> Path:
    return RAW
