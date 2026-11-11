#!/usr/bin/env python3
"""Nacidos vivos 1998-2025: data/processed/ext/nac_<año>.parquet, un año a la vez.

    python scripts/03_base_nacimientos.py
    python scripts/03_base_nacimientos.py --anios 2008-2011
"""
from __future__ import annotations

import gc
import time

import _entorno
from eevv_insumos import nacimientos, rutas


def main() -> int:
    ap = _entorno.argumentos(__doc__.splitlines()[0])
    ap.add_argument("--anios", default=None)
    args = ap.parse_args()
    _entorno.preparar(args)
    rutas.ext().mkdir(parents=True, exist_ok=True)
    for anio in _entorno.anios(args.anios, nacimientos.ANIOS):
        t0 = time.time()
        df = nacimientos.extendida(anio)
        df.write_parquet(rutas.ext() / f"nac_{anio}.parquet", compression="zstd")
        print(f"nac {anio}: {df.height:>7} nacidos vivos · sin departamento {df['dp'].is_null().sum():>5} · "
              f"exterior {(df['dp'] == 75).sum():>4} · {time.time() - t0:.0f} s", flush=True)
        del df
        gc.collect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
