#!/usr/bin/env python3
"""Nivel A. De data/intermedios/ a output/: resultados.json, tablas/ (CSV), aps_tablero.json, parametros/ y
sensibilidad.json (análisis pedidos por el árbitro: tendencia, sobredispersión, REH cruda, grupos infecciosos) y
municipal/ con aps_municipal_tablero.json (mortalidad municipal y tablas territoriales de la ADRES).

    python scripts/03_estimar.py
"""
import time

import _entorno  # noqa: F401
from aps_evitable import calculo, municipal, sensibilidad

if __name__ == "__main__":
    t0 = time.time()
    calculo.nivel_a()
    sensibilidad.todo()
    municipal.nivel_a()
    print(f"{time.time() - t0:.0f} s")
