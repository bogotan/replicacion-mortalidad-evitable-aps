"""Lectura de data/raw/MANIFIESTO.csv y cálculo de huellas SHA-256.

Cada fila del manifiesto es un insumo crudo. Columnas:

    archivo         ruta relativa a data/raw/ (con la que la leen los scripts)
    grupo           «eevv» para los insumos de este paquete (un repositorio de artículo puede agregar otros grupos)
    fuente          entidad y producto
    catalogo        número de catálogo del Archivo Nacional de Datos (ANDA) del DANE, o vacío
    url             dirección de descarga directa
    fecha_descarga  fecha en que se descargó la copia cuya huella se registra (AAAA-MM-DD)
    bytes           tamaño en bytes
    sha256          huella SHA-256
    licencia        términos de uso que rigen el archivo
    redistribuye    «no» o «sí»: si el archivo puede ir dentro del repositorio
    uso             qué script lo lee y para qué
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from . import rutas

COLUMNAS = ["archivo", "grupo", "fuente", "catalogo", "url", "fecha_descarga", "bytes", "sha256", "licencia",
            "redistribuye", "uso"]


def leer(ruta: Path | None = None, grupo: str | None = "eevv") -> list[dict]:
    ruta = ruta or rutas.manifiesto()
    with open(ruta, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    return [r for r in filas if grupo is None or r.get("grupo") == grupo]


def escribir(filas: list[dict], ruta: Path | None = None) -> None:
    ruta = ruta or rutas.manifiesto()
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, lineterminator="\n")
        w.writeheader()
        for r in filas:
            w.writerow({k: r.get(k, "") for k in COLUMNAS})


def sha256(ruta: Path, bloque: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        while (b := f.read(bloque)):
            h.update(b)
    return h.hexdigest()


def verificar(fila: dict) -> tuple[bool, str]:
    """(correcto, mensaje) para un insumo: existe, tamaño y huella."""
    p = rutas.crudo() / fila["archivo"]
    if not p.exists():
        return False, "falta"
    if p.stat().st_size != int(fila["bytes"]):
        return False, f"tamaño {p.stat().st_size} distinto de {fila['bytes']}"
    h = sha256(p)
    if h != fila["sha256"]:
        return False, f"huella {h[:12]}… distinta de {fila['sha256'][:12]}…"
    return True, "ok"
