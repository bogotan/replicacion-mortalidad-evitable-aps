#!/usr/bin/env python3
"""Descarga y verifica los insumos del artículo A5.

    python scripts/00_descargar_insumos.py              # baja lo que falte (grupos «a5» y «eevv») y verifica huellas
    python scripts/00_descargar_insumos.py --verificar  # solo verifica
    python scripts/00_descargar_insumos.py --sin-eevv   # solo los insumos propios del artículo

Grupo «a5» (data/raw/externos/): las cuatro transcripciones del informe de la ADRES están versionadas; el informe en PDF y
el archivo de World Population Prospects 2024 (del que sale config/poblacion_estandar_ocde2015.csv) no se versionan y se
bajan de la URL del manifiesto. El PDF de la ADRES descargado puede no tener la huella registrada (la del manifiesto es
la copia que entregó el autor): ver data/raw/externos/adres/FUENTE.md. Grupo «eevv» (microdatos y proyecciones del DANE):
lo hace scripts/insumos_eevv/00_descargar_microdatos.py, que este script llama.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import urllib.request
from pathlib import Path

import _entorno  # noqa: F401
from aps_evitable.rutas import RAIZ, RAW

sys.path.insert(0, str(RAIZ / "src"))
from eevv_insumos import manifiesto  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verificar", action="store_true")
    ap.add_argument("--sin-eevv", action="store_true", help="no tocar los insumos del DANE de Estadísticas Vitales")
    a = ap.parse_args()
    fallas = 0
    for grupo in ("a5",):
        for f in manifiesto.leer(RAW / "MANIFIESTO.csv", grupo=grupo):
            p = (RAW / f["archivo"]).resolve()
            if not p.exists() and not a.verificar and f["redistribuye"] == "no" and f["url"]:
                p.parent.mkdir(parents=True, exist_ok=True)
                print(f"  bajando {f['archivo']} …", flush=True)
                parte = p.with_suffix(p.suffix + ".part")
                try:
                    urllib.request.urlretrieve(f["url"].replace(" ", "%20"), parte)
                    parte.rename(p)
                except OSError as e:          # servidor caído o conexión cortada: se informa y se sigue con los demás
                    print(f"  no se pudo bajar {f['archivo']}: {e}", flush=True)
                    parte.unlink(missing_ok=True)
            ok = p.exists() and p.stat().st_size == int(f["bytes"]) and manifiesto.sha256(p) == f["sha256"]
            if not ok and p.exists() and p.suffix == ".pdf":   # informe de la ADRES: no lo lee ningún script (FUENTE.md)
                print(f"  aviso {f['archivo']}: la huella difiere de la copia del autor; las transcripciones no cambian", flush=True)
                continue
            print(f"  {'ok   ' if ok else 'FALLA'} {f['archivo']}", flush=True)
            fallas += not ok
    if not a.sin_eevv:
        cmd = [sys.executable, str(RAIZ / "scripts" / "insumos_eevv" / "00_descargar_microdatos.py"), "--raiz", str(RAIZ)]
        if a.verificar:
            cmd.append("--verificar")
        fallas += subprocess.run(cmd).returncode != 0
    print("Insumos verificados." if not fallas else f"{fallas} insumos con problemas.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
