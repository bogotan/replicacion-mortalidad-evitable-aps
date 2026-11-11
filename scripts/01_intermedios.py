#!/usr/bin/env python3
"""Nivel B. De las bases comunes de Estadísticas Vitales (data/processed/, o la carpeta de PROCESADO) y de los
insumos del DANE en data/raw/ a los intermedios publicables del nivel A:

    conteos.parquet                     defunciones 1998–2025 por año, departamento, sexo, grupo de edad (con la edad
                                        desconocida aparte) y marcas de clasificación; sin registros individuales
    codigos.parquet                     clasificación de cada código CIE-10 observado
    poblacion.parquet                   población por año, departamento, sexo y grupo de edad
    poblacion_2025_edad_simple.parquet  población de 2025 por departamento y edad simple (razones de hospitalización)
    esperadas_dane_2015_2017.parquet    defunciones esperadas con las tasas del DANE (escenario de omisión)
    cruce_lista_667.csv, cruce_lista_105.csv, codigos_csaa.csv, solapamiento_ocde.json
    municipal_csaa.parquet              por municipio, 2023–2025: muertes por CSAA <75 (O), esperadas con las tasas
                                        nacionales por edad (E), muertes <75 de todas las causas, muertes por CSAA de
                                        todas las edades y población 2025

    python scripts/01_intermedios.py [--salida data/intermedios]
"""
import argparse
import time
from pathlib import Path

import _entorno  # noqa: F401
from aps_evitable import calculo
from aps_evitable.rutas import INTERMEDIOS, RAIZ

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", default=str(INTERMEDIOS))
    a = ap.parse_args()
    salida = Path(a.salida) if Path(a.salida).is_absolute() else RAIZ / a.salida
    t0 = time.time()
    calculo.nivel_b(salida)
    print(f"{time.time() - t0:.0f} s")
