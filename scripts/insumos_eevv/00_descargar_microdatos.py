#!/usr/bin/env python3
"""Descarga y verifica los insumos crudos de EEVV: microdatos del DANE y proyecciones de población.

Lee data/raw/MANIFIESTO.csv (filas del grupo «eevv»). Para cada archivo:
  · si ya está en data/raw/ con el tamaño y la huella SHA-256 del manifiesto, no hace nada;
  · si falta, lo descarga de la URL del manifiesto (reanudable) y verifica tamaño y huella;
  · si está pero no coincide, lo informa y no lo toca (use --forzar para volver a bajarlo).

Fuentes:
  · Archivo Nacional de Datos (ANDA) del DANE, https://microdatos.dane.gov.co, catálogos de Estadísticas Vitales
    366, 375, 377, 396, 397, 398, 420, 475, 519, 652, 696, 732, 775, 807, 876, 878 y 915. Son «microdatos
    anonimizados de uso público» con acceso directo: en octubre de 2026 la descarga no pedía registro, formulario
    ni aceptación de términos. Si el portal llega a pedirlos, el servidor devuelve una página HTML en vez del zip;
    el script lo detecta, se detiene y explica el paso manual. No intenta saltarse ese paso.
  · Proyecciones de población y estimaciones del cambio demográfico del DANE (www.dane.gov.co/files/censo2018/).

Términos de uso (léalos antes de usar los datos; resumen en docs/INSUMOS.md): se autoriza el uso, transformación y
análisis con la cita «Fuente: Departamento Administrativo Nacional de Estadística: www.dane.gov.co», y los términos
de los catálogos de microdatos prohíben copiar o reproducir los datos en un medio que los ponga a disposición de
múltiples usuarios sin visto bueno escrito del DANE. Por eso los zips no se versionan: se bajan con este script.

Uso:
    python scripts/00_descargar_microdatos.py                 # baja lo que falta y verifica todo
    python scripts/00_descargar_microdatos.py --verificar     # solo verifica huellas (no descarga)
    python scripts/00_descargar_microdatos.py --listar        # muestra qué bajaría
    python scripts/00_descargar_microdatos.py --solo antiguos/Defun1979.zip --solo poblacion/
"""
from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request

import _entorno
from eevv_insumos import manifiesto, rutas

UA = {"User-Agent": "Mozilla/5.0 (insumos-eevv; descarga de datos abiertos del DANE para investigación)"}
PASO_MANUAL = """
El servidor devolvió una página web y no el archivo. Puede que el portal pida ahora registro o aceptar términos.
Paso manual:
  1. Abra {pagina} en un navegador.
  2. Lea y acepte las condiciones de uso del DANE, si las pide.
  3. Descargue el archivo «{original}» y guárdelo como data/raw/{archivo}
  4. Corra de nuevo: python scripts/00_descargar_microdatos.py --verificar
"""


def _pagina(fila: dict) -> str:
    if fila["catalogo"]:
        return f"https://microdatos.dane.gov.co/index.php/catalog/{fila['catalogo']}/get-microdata"
    return fila["url"]


def descargar(fila: dict, intentos: int = 3) -> None:
    destino = rutas.crudo() / fila["archivo"]
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_name(destino.name + ".part")
    esperado = int(fila["bytes"])
    for intento in range(1, intentos + 1):
        escrito = tmp.stat().st_size if tmp.exists() else 0
        h = dict(UA)
        if escrito:
            h["Range"] = f"bytes={escrito}-"
        try:
            with urllib.request.urlopen(urllib.request.Request(fila["url"], headers=h), timeout=300) as r:
                tipo = r.headers.get("Content-Type", "")
                if "text/html" in tipo:
                    tmp.unlink(missing_ok=True)
                    original = fila["url"].rsplit("/", 1)[-1]
                    sys.exit(PASO_MANUAL.format(pagina=_pagina(fila), original=original, archivo=fila["archivo"]))
                if escrito and r.status != 206:          # el servidor no aceptó la reanudación
                    escrito = 0
                    tmp.unlink(missing_ok=True)
                with open(tmp, "ab") as f:
                    while (b := r.read(1 << 20)):
                        f.write(b)
            break
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if getattr(e, "code", None) == 416:          # ya estaba completo
                break
            print(f"    intento {intento}: {e}", flush=True)
            if intento == intentos:
                raise
            time.sleep(5 * intento)
    if tmp.stat().st_size != esperado:
        sys.exit(f"ALTO: {fila['archivo']} quedó con {tmp.stat().st_size} bytes y se esperaban {esperado}; corra de nuevo.")
    tmp.replace(destino)


def main() -> int:
    ap = _entorno.argumentos("Descarga y verifica los insumos crudos de EEVV")
    ap.add_argument("--verificar", action="store_true", help="solo verifica; no descarga")
    ap.add_argument("--listar", action="store_true", help="muestra qué bajaría")
    ap.add_argument("--forzar", action="store_true", help="vuelve a bajar los archivos cuya huella no coincide")
    ap.add_argument("--solo", action="append", default=[], help="prefijo de data/raw/ a procesar (se puede repetir)")
    args = ap.parse_args()
    _entorno.preparar(args)
    filas = manifiesto.leer()
    if args.solo:
        filas = [f for f in filas if any(f["archivo"].startswith(s) for s in args.solo)]
    print(f"{len(filas)} insumos en el manifiesto. Fuente: Departamento Administrativo Nacional de Estadística: www.dane.gov.co\n")
    fallas = []
    for i, fila in enumerate(filas, 1):
        p = rutas.crudo() / fila["archivo"]
        etiqueta = f"[{i:>2}/{len(filas)}] {fila['archivo']}"
        if p.exists():
            ok, msg = manifiesto.verificar(fila)
            if ok:
                print(f"  ok      {etiqueta}", flush=True)
                continue
            if not args.forzar or args.verificar or args.listar:
                print(f"  FALLA   {etiqueta}: {msg}", flush=True)
                fallas.append((fila["archivo"], msg))
                continue
            p.unlink()
        if args.verificar:
            print(f"  FALTA   {etiqueta}", flush=True)
            fallas.append((fila["archivo"], "falta"))
            continue
        if args.listar:
            print(f"  bajaría {etiqueta}  {int(fila['bytes']) / 1e6:.1f} MB  <- {fila['url']}", flush=True)
            continue
        if not fila["url"]:
            print(f"  SIN URL {etiqueta}: el DANE ya no lo publica. {fila['fuente']}. Copie el archivo con este nombre "
                  f"desde una copia verificada (por ejemplo, la del repositorio EEVV) y corra --verificar.", flush=True)
            fallas.append((fila["archivo"], "sin URL pública; copia manual"))
            continue
        t0 = time.time()
        descargar(fila)
        ok, msg = manifiesto.verificar(fila)
        print(f"  {'bajado' if ok else 'FALLA '}  {etiqueta}  {int(fila['bytes']) / 1e6:.1f} MB en {time.time() - t0:.0f} s"
              + ("" if ok else f": {msg}. El DANE pudo haber publicado una versión nueva; compárela antes de usarla."), flush=True)
        if not ok:
            fallas.append((fila["archivo"], msg))
        time.sleep(1)
    if fallas:
        print(f"\n{len(fallas)} insumos con problemas:")
        for a, m in fallas:
            print(f"  {a}: {m}")
        return 1
    print("\nTodos los insumos están y coinciden con su huella.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
