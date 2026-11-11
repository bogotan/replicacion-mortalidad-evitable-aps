#!/usr/bin/env python3
"""Corre un comando y anota su duración y su memoria máxima (RSS) en un registro.

    python scripts/medir.py <registro.tsv> <etiqueta> -- <comando ...>

Agrega al registro una línea: etiqueta, fecha de inicio, segundos, memoria máxima en MB, código de salida. La memoria
es la del mayor proceso hijo (getrusage RUSAGE_CHILDREN), que en Linux se informa en kB.
"""
from __future__ import annotations

import datetime as dt
import resource
import subprocess
import sys
import time


def main() -> int:
    registro, etiqueta = sys.argv[1], sys.argv[2]
    cmd = sys.argv[sys.argv.index("--") + 1:]
    inicio = dt.datetime.now().isoformat(timespec="seconds")
    t0 = time.time()
    rc = subprocess.call(cmd)
    seg = time.time() - t0
    mb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024
    with open(registro, "a", encoding="utf-8") as f:
        f.write(f"{etiqueta}\t{inicio}\t{seg:.0f}\t{mb:.0f}\t{rc}\n")
    print(f"[medir] {etiqueta}: {seg:.0f} s, {mb:.0f} MB, salida {rc}", flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
