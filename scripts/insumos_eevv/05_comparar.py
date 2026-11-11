#!/usr/bin/env python3
"""Compara, por contenido, las bases de data/processed/ con las de otra carpeta (nivel B de reproducción).

Para cada archivo: mismas columnas en el mismo orden, mismos tipos, mismo número de filas y mismos valores. Primero
compara en el orden en que están las filas; si difieren, ordena las dos tablas por todas las columnas y vuelve a
comparar (una diferencia solo de orden queda registrada como tal). Los valores decimales se comparan exactos y, si
no coinciden, se informa la máxima diferencia absoluta (el estándar acepta hasta 1e-9). Las tablas grandes se
comparan año por año.

    python scripts/05_comparar.py --referencia <carpeta con defunciones_eevv.parquet, ext/, ...>
"""
from __future__ import annotations

import gc
import json
from pathlib import Path

import polars as pl

import _entorno
from eevv_insumos import defunciones, nacimientos, rutas

TOL = 1e-9


def _comparar(a: pl.DataFrame, b: pl.DataFrame) -> dict:
    r = {"filas": [a.height, b.height], "columnas_iguales": a.columns == b.columns,
         "tipos_iguales": a.schema == b.schema}
    if not r["columnas_iguales"]:
        r["solo_nuevo"] = [c for c in a.columns if c not in b.columns]
        r["solo_referencia"] = [c for c in b.columns if c not in a.columns]
        r["estado"] = "difiere"
        return r
    if not r["tipos_iguales"]:
        r["tipos"] = {c: [str(a.schema[c]), str(b.schema[c])] for c in a.columns if a.schema[c] != b.schema[c]}
        b = b.cast(a.schema, strict=False)
    if a.height != b.height:
        r["estado"] = "difiere"
        return r
    if a.equals(b, null_equal=True):
        r["estado"] = "igual"
        return r
    cols = a.columns
    a2, b2 = a.sort(cols, nulls_last=True), b.sort(cols, nulls_last=True)
    if a2.equals(b2, null_equal=True):
        r["estado"] = "igual salvo orden"
        return r
    r["estado"] = "difiere"
    dif = {}
    for c in cols:
        x, y = a2[c], b2[c]
        n = int((x.ne_missing(y)).sum())
        if n:
            dif[c] = {"valores_distintos": n}
            if x.dtype.is_float():
                m = float((x - y).abs().max())
                dif[c]["max_abs"] = m
    r["columnas_con_diferencias"] = dif
    if all(v.get("max_abs", 1.0) <= TOL for v in dif.values()):
        r["estado"] = "igual (coma flotante < 1e-9)"
    return r


def _por_partes(nuevo: Path, ref: Path, col: str) -> dict:
    ln, lr = pl.scan_parquet(nuevo), pl.scan_parquet(ref)
    claves = sorted(set(ln.select(col).unique().collect()[col].to_list()) | set(lr.select(col).unique().collect()[col].to_list()))
    estados, detalle, filas = {}, {}, [0, 0]
    sch_n, sch_r = ln.collect_schema(), lr.collect_schema()
    for k in claves:
        r = _comparar(ln.filter(pl.col(col) == k).collect(), lr.filter(pl.col(col) == k).collect())
        filas[0] += r["filas"][0]; filas[1] += r["filas"][1]
        estados[r["estado"]] = estados.get(r["estado"], 0) + 1
        if r["estado"] not in ("igual", "igual salvo orden"):
            detalle[str(k)] = r
        gc.collect()
    est = "igual" if set(estados) == {"igual"} else ("igual salvo orden" if set(estados) <= {"igual", "igual salvo orden"} else "difiere")
    # orden global de las filas: se comparan los dos archivos en tramos de un millón de filas, en su orden
    orden = filas[0] == filas[1]
    for i in range(0, filas[0], 1_000_000):
        if not orden:
            break
        orden = ln.slice(i, 1_000_000).collect().equals(lr.slice(i, 1_000_000).collect(), null_equal=True)
        gc.collect()
    if est == "igual" and not orden:
        est = "igual salvo orden"
    return {"estado": est, "filas": filas, "columnas_iguales": list(sch_n) == list(sch_r),
            "tipos_iguales": dict(sch_n) == dict(sch_r), "orden_global_igual": orden, "partes": estados, "detalle": detalle}


def main() -> int:
    ap = _entorno.argumentos(__doc__.splitlines()[0])
    ap.add_argument("--referencia", required=True, help="carpeta processed de referencia")
    ap.add_argument("--salida", default=None, help="JSON con el resultado (por defecto data/interim/eevv/comparacion.json)")
    args = ap.parse_args()
    _entorno.preparar(args)
    ref = Path(args.referencia)
    nuevo = rutas.procesado()
    res = {}
    for a in defunciones.ANIOS:
        f = f"ext/def_{a}.parquet"
        res[f] = _comparar(pl.read_parquet(nuevo / f), pl.read_parquet(ref / f)); gc.collect()
        print(f"  {f:<32} {res[f]['estado']}", flush=True)
    for a in nacimientos.ANIOS:
        f = f"ext/nac_{a}.parquet"
        res[f] = _comparar(pl.read_parquet(nuevo / f), pl.read_parquet(ref / f)); gc.collect()
        print(f"  {f:<32} {res[f]['estado']}", flush=True)
    f = "poblacion_eevv.parquet"
    res[f] = _comparar(pl.read_parquet(nuevo / f), pl.read_parquet(ref / f))
    print(f"  {f:<32} {res[f]['estado']}", flush=True)
    for f, col in (("defunciones_eevv.parquet", "anio"), ("mun_pob_edad.parquet", "ano")):
        res[f] = _por_partes(nuevo / f, ref / f, col)
        print(f"  {f:<32} {res[f]['estado']}  {res[f]['partes']}", flush=True)
    salida = Path(args.salida) if args.salida else rutas.intermedio() / "comparacion.json"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    malos = [k for k, v in res.items() if not v["estado"].startswith("igual")]
    print(f"\n{len(res) - len(malos)} de {len(res)} archivos coinciden." + (f" Difieren: {malos}" if malos else ""))
    return 1 if malos else 0


if __name__ == "__main__":
    raise SystemExit(main())
