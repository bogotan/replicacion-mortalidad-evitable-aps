#!/usr/bin/env python3
"""Nivel A. Figuras (output/figuras/, PNG a 300 ppp) y cuadros del manuscrito (output/tablas/cuadro*.csv)."""
import _entorno  # noqa: F401
from aps_evitable import figuras

if __name__ == "__main__":
    figuras.todo()
    print("figuras y cuadros listos")
