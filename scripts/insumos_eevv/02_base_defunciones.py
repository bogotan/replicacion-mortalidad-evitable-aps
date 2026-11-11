#!/usr/bin/env python3
"""Defunciones no fetales 1979-2025: data/processed/ext/def_<año>.parquet y data/processed/defunciones_eevv.parquet.

Un año a la vez (lee el zip o el intermedio de 01_extraer.py, armoniza con eevv_insumos.defunciones y escribe
def_<año>); después apila las columnas de residencia de los 47 archivos en defunciones_eevv.parquet, también año
por año, sin cargar la serie entera en memoria.

    python scripts/02_base_defunciones.py                     # 1979-2025 y apilado
    python scripts/02_base_defunciones.py --anios 2008-2011   # solo esos años (no apila)
    python scripts/02_base_defunciones.py --solo-apilar
"""
from __future__ import annotations

import gc
import time

import polars as pl

import _entorno
from eevv_insumos import defunciones, rutas


def apilar() -> int:
    import pyarrow.parquet as pq
    salida = rutas.procesado() / "defunciones_eevv.parquet"
    tmp = salida.with_suffix(".parquet.part")
    escritor, filas, esquema = None, 0, None
    try:
        for anio in defunciones.ANIOS:
            t = pl.read_parquet(rutas.ext() / f"def_{anio}.parquet", columns=defunciones.BASE).to_arrow()
            if escritor is None:
                esquema = t.schema
                escritor = pq.ParquetWriter(tmp, esquema, compression="zstd")
            escritor.write_table(t.cast(esquema))
            filas += t.num_rows
            del t
    finally:
        if escritor is not None:
            escritor.close()
    tmp.replace(salida)
    print(f"-> {rutas.relativa(salida)}  {filas} filas", flush=True)
    return filas


def main() -> int:
    ap = _entorno.argumentos(__doc__.splitlines()[0])
    ap.add_argument("--anios", default=None)
    ap.add_argument("--solo-apilar", action="store_true")
    args = ap.parse_args()
    _entorno.preparar(args)
    rutas.ext().mkdir(parents=True, exist_ok=True)
    if not args.solo_apilar:
        for anio in _entorno.anios(args.anios, defunciones.ANIOS):
            t0 = time.time()
            df = defunciones.extendida(anio)
            df.write_parquet(rutas.ext() / f"def_{anio}.parquet", compression="zstd")
            print(f"def {anio}: {df.height:>7} defunciones · edad desconocida {int((df['g'] < 0).sum()):>5} · "
                  f"sin dpto {int(df['dp'].is_null().sum()):>4} · {time.time() - t0:.0f} s", flush=True)
            del df
            gc.collect()
    if args.solo_apilar or not args.anios:
        apilar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
