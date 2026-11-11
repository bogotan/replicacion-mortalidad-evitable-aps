#!/usr/bin/env python3
"""Extrae el microdato de defunciones no fetales 2020-2025 de sus zips a data/interim/eevv/def_<año>.parquet.

Desde 2020 el DANE publica cada año el mismo microdato en .csv, .dta y .sav. Se toma el .dta (o el .sav si no
hay .dta, como en 2021), igual que scripts/01_extraer.py y 02_consolidar.py del repositorio EEVV, y se leen solo las
columnas que usa 02_base_defunciones.py. Los demás años se leen directo del zip en 02 y 03.

    python scripts/01_extraer.py                 # 2020-2025
    python scripts/01_extraer.py --anios 2021
"""
from __future__ import annotations

import gc
import json
import time

import _entorno
from eevv_insumos import defunciones, lectura, rutas


def main() -> int:
    ap = _entorno.argumentos(__doc__.splitlines()[0])
    ap.add_argument("--anios", default=None, help="por ejemplo 2020-2022,2025")
    args = ap.parse_args()
    _entorno.preparar(args)
    registro = {}
    for anio in _entorno.anios(args.anios, sorted(defunciones.RECIENTES)):
        t0 = time.time()
        z = rutas.crudo() / defunciones.RECIENTES[anio]
        info = lectura.extraer_a_parquet(z, defunciones.intermedio(anio), columnas=defunciones.LECTURA)
        registro[anio] = {"zip": defunciones.RECIENTES[anio], **info}
        print(f"  {anio}: {info['miembro']} ({info['formato']}, {info['codificacion']}) -> "
              f"{rutas.relativa(defunciones.intermedio(anio))}  {info['filas']} filas · {time.time() - t0:.0f} s", flush=True)
        gc.collect()
    p = rutas.intermedio() / "_extraccion.json"
    previo = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    previo.update({str(k): v for k, v in registro.items()})
    p.write_text(json.dumps(previo, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
