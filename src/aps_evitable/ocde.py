"""Constantes de territorio y funciones tomadas del estudio 54 del Termómetro (lista OCDE/Eurostat de 2022, población
estándar de la OCDE de 2015 y agrupación de edades), sin cambios de cálculo."""
from __future__ import annotations

import numpy as np
import polars as pl

from .codigos import clasificador
from .rutas import CONFIG
from . import termo as T

G = T.G
Q75 = 16
DEP = {5: "Antioquia", 8: "Atlántico", 11: "Bogotá D.C.", 13: "Bolívar", 15: "Boyacá", 17: "Caldas",
       18: "Caquetá", 19: "Cauca", 20: "Cesar", 23: "Córdoba", 25: "Cundinamarca", 27: "Chocó",
       41: "Huila", 44: "La Guajira", 47: "Magdalena", 50: "Meta", 52: "Nariño", 54: "Norte de Santander",
       63: "Quindío", 66: "Risaralda", 68: "Santander", 70: "Sucre", 73: "Tolima", 76: "Valle del Cauca",
       81: "Arauca", 85: "Casanare", 86: "Putumayo", 88: "San Andrés y Providencia", 91: "Amazonas",
       94: "Guainía", 95: "Guaviare", 97: "Vaupés", 99: "Vichada"}
CODS = sorted(DEP)
ND = len(CODS)                                      # 33; índice 33 = departamento desconocido
DIX = {c: i for i, c in enumerate(CODS)}


def lista():
    """Lista conjunta OCDE/Eurostat de causas prevenibles y tratables (enero de 2022)."""
    L = pl.read_csv(CONFIG / "mortalidad_evitable_ocde2022.csv")
    L = L.with_columns(pl.col("prevenible").cast(pl.Float64), pl.col("tratable").cast(pl.Float64))
    f = clasificador([(r["id"], r["cie10"], r["excluye"] or "") for r in L.iter_rows(named=True)])
    return L, f


def pesos_ocde2015():
    """15 pesos de 0–4 … 70–74 por la población estándar total (OCDE 2015, 38 países, WPP 2024)."""
    x = pl.read_csv(CONFIG / "poblacion_estandar_ocde2015.csv")
    std = x["poblacion_ocde38_2015"].to_numpy().astype(float)
    return std[:15] / std.sum()


def a15(X):
    """[..., G] (0, 1-4, 5-9, …) -> [..., 15] (0-4, 5-9, …, 70-74)."""
    X = np.asarray(X, float)
    return np.concatenate([X[..., :1] + X[..., 1:2], X[..., 2:Q75]], axis=-1)
