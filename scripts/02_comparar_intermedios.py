#!/usr/bin/env python3
"""Compara intermedios reconstruidos (nivel B) con los versionados: mismas filas y valores; las diferencias de
coma flotante deben quedar por debajo de 1e-9.

    python scripts/02_comparar_intermedios.py --nuevo data/interim/a5/intermedios_b --referencia data/intermedios
"""
import argparse
import json
import sys
from pathlib import Path

import polars as pl

import _entorno  # noqa: F401
from aps_evitable.rutas import RAIZ


def comparar(a: Path, b: Path) -> str | None:
    if a.suffix == ".json":
        return None if json.loads(a.read_text(encoding="utf-8")) == json.loads(b.read_text(encoding="utf-8")) else "contenido distinto"
    x = pl.read_parquet(a) if a.suffix == ".parquet" else pl.read_csv(a)
    y = pl.read_parquet(b) if b.suffix == ".parquet" else pl.read_csv(b)
    if x.columns != y.columns or x.height != y.height:
        return f"forma distinta {x.shape} vs {y.shape}"
    x, y = x.sort(x.columns), y.sort(y.columns)
    for c in x.columns:
        if x[c].dtype.is_numeric():
            d = (x[c].cast(pl.Float64) - y[c].cast(pl.Float64)).abs().max()
            if d is not None and d > 1e-9:
                return f"{c}: diferencia máxima {d}"
        elif not x[c].equals(y[c]):
            return f"{c}: valores distintos"
    return None


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--nuevo", required=True)
    ap.add_argument("--referencia", default="data/intermedios")
    a = ap.parse_args()
    n, r = (Path(p) if Path(p).is_absolute() else RAIZ / p for p in (a.nuevo, a.referencia))
    fallas = 0
    for f in sorted(r.iterdir()):
        if f.suffix not in (".parquet", ".csv", ".json"):
            continue
        res = comparar(n / f.name, f) if (n / f.name).exists() else "falta en la reconstrucción"
        print(f"  {'ok   ' if res is None else 'FALLA'} {f.name}{'' if res is None else ': ' + res}")
        fallas += res is not None
    print("Intermedios idénticos." if not fallas else f"{fallas} diferencias")
    sys.exit(1 if fallas else 0)
