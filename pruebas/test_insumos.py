"""Insumos propios del artículo A5: huellas de los archivos versionados, transcripción de la ADRES contra los totales
de su propio informe y reconstrucción de la población estándar de la OCDE desde World Population Prospects 2024.

Los insumos del DANE (microdatos y proyecciones) se prueban en pruebas/insumos_eevv/ (requieren el nivel B).
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
RAW = RAIZ / "data" / "raw"
MAN = [r for r in csv.DictReader(open(RAW / "MANIFIESTO.csv", encoding="utf-8")) if r["grupo"] == "a5"]
OCDE38 = ("AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN KOR LVA LTU LUX "
          "MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA").split()


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.mark.parametrize("fila", [r for r in MAN if r["redistribuye"] == "sí"], ids=lambda r: r["archivo"])
def test_huella_versionados(fila):
    p = RAW / fila["archivo"]
    assert p.stat().st_size == int(fila["bytes"]) and sha(p) == fila["sha256"]


def test_manifiesto_completo():
    assert {r["archivo"] for r in MAN} >= {f"externos/adres/{f}" for f in ("adres_hecsap_2025_departamentos.csv", "adres_hecsap_2025_condiciones.csv",
                                                                            "adres_hecsap_2025_edad.csv", "adres_hecsap_serie_nacional.csv",
                                                                            "adres_hecsap_2025_oe_departamentos.csv", "adres_hecsap_2025_oe_top_municipios.csv",
                                                                            "adres_hecsap_2025_concentracion.csv", "adres_hecsap_tendencias_2019_2024.csv")}
    assert all(r["url"] and r["licencia"] and len(r["sha256"]) == 64 for r in MAN)


def test_adres_cuadra_con_su_cuadro_1():
    d = RAW / "externos" / "adres"
    con = pd.read_csv(d / "adres_hecsap_2025_condiciones.csv")
    dep = pd.read_csv(d / "adres_hecsap_2025_departamentos.csv")
    ser = pd.read_csv(d / "adres_hecsap_serie_nacional.csv")
    assert len(con) == 20 and int(con["hospitalizaciones"].sum()) == 748212
    assert sorted(con["grupo_csaa"].unique()) == list(range(1, 20))
    assert abs(dep["hosp_hecsap"].sum() - 746822) == 0            # con residencia conocida (FUENTE.md)
    assert ser.set_index("anio").loc[2025, "tasa_hecsap_10k"] == 141.0


WPP = RAW / "externos" / "wpp2024" / "WPP2024_PopulationByAge5GroupSex_Medium.csv.gz"


@pytest.mark.skipif(not WPP.exists(), reason="WPP 2024 no descargado (make insumos)")
def test_poblacion_estandar_desde_wpp():
    fila = next(r for r in MAN if r["archivo"].endswith(WPP.name))
    assert sha(WPP) == fila["sha256"]
    w = pd.read_csv(WPP, usecols=["ISO3_code", "Time", "AgeGrpStart", "PopTotal"], dtype={"ISO3_code": str})
    w = w[w["ISO3_code"].isin(OCDE38) & (w["Time"] == 2015)]
    assert w["ISO3_code"].nunique() == 38
    x = w.groupby("AgeGrpStart")["PopTotal"].sum().sort_index()
    cfg = pd.read_csv(RAIZ / "config" / "poblacion_estandar_ocde2015.csv")
    assert list(cfg["edad_inicio"]) == list(x.index)
    assert (abs(cfg["poblacion_ocde38_2015"].values - x.values) < 1e-6).all()
    assert (abs(cfg["peso_0_74_por_poblacion_total"].values[:15] - x.values[:15] / x.sum()) < 1e-12).all()
