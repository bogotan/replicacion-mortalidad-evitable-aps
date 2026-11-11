#!/usr/bin/env python3
"""Población del DANE (base CNPV 2018): data/processed/poblacion_eevv.parquet y data/processed/mun_pob_edad.parquet.

    python scripts/04_poblacion.py
    python scripts/04_poblacion.py --solo departamental
"""
from __future__ import annotations

import gc
import json
import time

import polars as pl

import _entorno
from eevv_insumos import poblacion, rutas


def main() -> int:
    ap = _entorno.argumentos(__doc__.splitlines()[0])
    ap.add_argument("--solo", choices=["departamental", "municipal"], default=None)
    args = ap.parse_args()
    _entorno.preparar(args)
    rutas.procesado().mkdir(parents=True, exist_ok=True)
    sal_dep = rutas.procesado() / "poblacion_eevv.parquet"
    controles = {}
    t0 = time.time()
    if args.solo != "municipal":
        dep, controles["departamental"] = poblacion.departamental()
        dep.write_parquet(sal_dep)
        print(f"-> {rutas.relativa(sal_dep)}  {dep.height} filas · {time.time() - t0:.0f} s", flush=True)
        for anio, p in dep.group_by("anio").agg(pl.col("pob").sum()).sort("anio").iter_rows():
            print(f"   {anio} {p:,.0f}")
    if args.solo != "departamental":
        dep = pl.read_parquet(sal_dep)
        gc.collect()
        t1 = time.time()
        sal_mun = rutas.procesado() / "mun_pob_edad.parquet"
        r = poblacion.municipal(sal_mun, dep)
        controles["municipal"] = {"filas": r["filas"],
                                  "max_dif_rel_mun_vs_dep": max(abs(v[2]) for v in r["control_anual"].values())}
        print(f"-> {rutas.relativa(sal_mun)}  {r['filas']} filas · {time.time() - t1:.0f} s · "
              f"máxima diferencia relativa municipal vs departamental {controles['municipal']['max_dif_rel_mun_vs_dep']:.2e}", flush=True)
    (rutas.intermedio()).mkdir(parents=True, exist_ok=True)
    (rutas.intermedio() / "_controles_poblacion.json").write_text(json.dumps(controles, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
