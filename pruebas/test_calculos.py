"""Recálculo independiente de las cifras centrales del artículo A5 (nivel A).

Parte de data/intermedios/ y de la configuración, con pandas y código escrito aquí, sin importar src/aps_evitable/calculo.py.
Viene de tests/verificar_aps.py del repositorio EEVV (estudio 43) y del recálculo del árbitro independiente del 5 de
noviembre de 2026. Comprueba: la lista contra la fuente; la clasificación de cada código observado; la conservación de
las defunciones; la tasa estandarizada nacional 2023–2025 con un estimador escrito aquí; la probabilidad de llegar a
los 65 con una tabla de vida escrita aquí; la tabla de referencia del GBD; el archivo de parámetros; y la transcripción y
las razones estandarizadas de hospitalización de la ADRES.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
INT, OUT, CONF = RAIZ / "data" / "intermedios", RAIZ / "output", RAIZ / "config"
ADRES = RAIZ / "data" / "raw" / "externos" / "adres"
CODS = [5, 8, 11, 13, 15, 17, 18, 19, 20, 23, 25, 27, 41, 44, 47, 50, 52, 54, 63, 66, 68, 70, 73, 76, 81, 85, 86, 88, 91, 94, 95, 97, 99]


def rango(a, b):
    return {f"{a[0]}{n:02d}" for n in range(int(a[1:]), int(b[1:]) + 1)}


# códigos de tres y cuatro caracteres de la Portaria SAS/MS 221 de 2008 (transcripción GAIS Informa n.º 18)
ESPERADO3 = {1: rango("A33", "A37") | {"A95", "B05", "B06", "B16", "B26"} | rango("A15", "A19") | rango("I00", "I02") | rango("A51", "A53") | rango("B50", "B54") | {"B77"},
             2: rango("A00", "A09") | {"E86"}, 3: {"D50"}, 4: rango("E40", "E46") | rango("E50", "E64"), 5: {"H66", "J00", "J01", "J02", "J03", "J06", "J31"},
             6: {"J13", "J14"}, 7: {"J45", "J46"}, 8: {"J20", "J21", "J40", "J41", "J42", "J43", "J44", "J47"}, 9: {"I10", "I11"}, 10: {"I20"},
             11: {"I50", "J81"}, 12: rango("I63", "I67") | {"I69", "G45", "G46"}, 13: rango("E10", "E14"), 14: {"G40", "G41"},
             15: {"N10", "N11", "N12", "N30", "N34"}, 16: {"A46", "L01", "L02", "L03", "L04", "L08"}, 17: {"N70", "N71", "N72", "N73", "N75", "N76"},
             18: rango("K25", "K28"), 19: {"O23", "A50"}}
ESPERADO4 = {1: {"G000"}, 6: {"J153", "J154", "J158", "J159", "J181"}, 15: {"N390"}, 18: {"K920", "K921", "K922"}, 19: {"P350"}}


def grupo_de(cb: str) -> int:
    cb = (cb or "").upper()
    for g, s4 in ESPERADO4.items():
        if cb[:4] in s4:
            return g
    for g, s3 in ESPERADO3.items():
        if cb[:3] in s3:
            return g
    return 0


@pytest.fixture(scope="module")
def R():
    return json.loads((OUT / "resultados.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def C():
    return pd.read_parquet(INT / "conteos.parquet")


@pytest.fixture(scope="module")
def P():
    return pd.read_parquet(INT / "poblacion.parquet")


def nacional(R, sexo="total"):
    return next(x for x in R["trienio"] if x["cod"] == 0 and x["sexo"] == sexo)


def test_lista_contra_la_fuente():
    import sys
    sys.path.insert(0, str(RAIZ / "src"))
    from aps_evitable.codigos import expandir
    L = pd.read_csv(CONF / "lista_aps_icsap2008.csv")
    assert sorted(L["grupo"]) == list(range(1, 20))
    for _, r in L.iterrows():
        t3, t4 = expandir(r["cie10"])
        assert t3 == ESPERADO3[r["grupo"]] and t4 == ESPERADO4.get(r["grupo"], set()), r["nombre"]


def test_codigos_observados_clasificados_igual():
    cls = pd.read_parquet(INT / "codigos.parquet")
    assert (cls["cb"].map(grupo_de) == cls["grupo"]).all()


def test_conservacion(C, R):
    assert C["n"].sum() == R["n_registros"] == 6218747
    assert abs(C.loc[C["g"] < 0, "n"].sum() - R["n_sin_edad_repartidos"]) < 1e-9


def _d_p(C, P, sexo=None):
    """Muertes por CSAA y población 2023–2025 en 0–4, 5–9, …, 70–74; la edad desconocida se reparte en proporción a
    la conocida dentro de las CSAA del mismo sexo (aproximación de esta prueba)."""
    c = C[C["anio"].between(2023, 2025) & (C["grupo"] > 0)]
    p = P[P["anio"].between(2023, 2025)]
    if sexo:
        c, p = c[c["sexo"] == sexo], p[p["sexo"] == sexo]
    fac = c["n"].sum() / c.loc[c["g"] >= 0, "n"].sum()
    q = lambda g: np.where(g <= 1, 0, g - 1)                     # 0 y 1–4 -> 0–4
    D = c[c["g"] >= 0].groupby(q(c.loc[c["g"] >= 0, "g"]))["n"].sum().reindex(range(18), fill_value=0).values * fac
    N = p.groupby(q(p["g"]))["pob"].sum().reindex(range(18), fill_value=0).values
    return D[:15], N[:15], c["n"].sum()


def test_tasa_nacional_recalculada(C, P, R):
    std = pd.read_csv(CONF / "poblacion_estandar_ocde2015.csv")["poblacion_ocde38_2015"].values
    w = std[:15] / std.sum()
    for sx, cod in (("total", None), ("hombres", 1), ("mujeres", 2)):
        D, N, tot = _d_p(C, P, cod)
        tee = (w * D / N).sum() * 1e5
        x = nacional(R, sx)
        assert abs(tee - x["tee_csaa"]) / x["tee_csaa"] < 0.01, (sx, tee, x["tee_csaa"])


def test_valores_del_arbitro(R):
    ARB = {(0, "total"): 53.41, (0, "hombres"): 67.28, (0, "mujeres"): 41.68, (27, "total"): 79.90, (11, "total"): 36.85, (63, "total"): 62.34}
    for (c, sx), v in ARB.items():
        x = next(y for y in R["trienio"] if y["cod"] == c and y["sexo"] == sx)
        assert abs(x["tee_csaa"] - v) <= 0.006


def test_p65_con_tabla_propia(C, P, R):
    """Grupos 0, 1–4, 5–9, …, 60–64. Chiang con ax = n/2 salvo 1a0 = 0,1 y 4a1 = 1,6 (aproximación de esta prueba)."""
    c = C[C["anio"].between(2023, 2025)]
    p = P[P["anio"].between(2023, 2025)]
    fac = c["n"].sum() / c.loc[c["g"] >= 0, "n"].sum()
    k = c[c["g"] >= 0]
    Dt = k.groupby("g")["n"].sum().reindex(range(14), fill_value=0).values * fac
    Dc = k[k["grupo"] > 0].groupby("g")["n"].sum().reindex(range(14), fill_value=0).values * fac
    Nn = p.groupby("g")["pob"].sum().reindex(range(14)).values
    n = np.array([1, 4] + [5] * 12, float); a = np.array([.1, 1.6] + [2.5] * 12)
    m = Dt / Nn; q = n * m / (1 + (n - a) * m)
    x0 = np.prod(1 - q); x1 = np.prod((1 - q) ** np.where(Dt > 0, (Dt - Dc) / Dt, 1))
    t = nacional(R)
    assert abs(x0 - t["p65"]) < 0.002 and abs((x1 - x0) - t["ganancia"]) < 0.0005


def test_tabla_referencia_gbd(C):
    rep = yaml.safe_load((CONF / "tabla_vida_referencia.yaml").read_text(encoding="utf-8"))["tabla_referencia_gbd"]
    pub = {0: 88.87, 1: 88.00, 5: 84.03, 10: 79.05, 15: 74.07, 20: 69.11, 25: 64.15, 30: 59.20, 35: 54.25, 40: 49.32, 45: 44.43,
           50: 39.63, 55: 34.91, 60: 30.25, 65: 25.68, 70: 21.29, 75: 17.10, 80: 13.24, 85: 9.99, 90: 7.62, 95: 5.92}
    x = np.array([0.1, 2.5] + [a + 2.5 for a in range(5, 75, 5)])
    ge = sorted(rep, key=float)
    y_rep = np.interp(x, [float(k) for k in ge], [rep[k] for k in ge]); y_pub = np.interp(x, list(pub), list(pub.values()))
    c = C[C["anio"].between(2023, 2025) & (C["grupo"] > 0) & C["g"].between(0, 15)]
    Dg = c.groupby("g")["n"].sum().reindex(range(16), fill_value=0).values
    assert abs((Dg * y_rep).sum() / (Dg * y_pub).sum() - 1) < 0.001


def test_parametros():
    Pm = pd.read_csv(OUT / "parametros" / "mortalidad_aps_parametros.csv")
    k = ["anio", "cod_dpto", "sexo", "grupo_edad"]
    assert not Pm.duplicated(k + ["grupo_causa"]).any()
    piv = Pm.pivot_table(index=k, columns="grupo_causa", values="defunciones", aggfunc="sum")
    partes = ["csaa_cardiometabolicas", "csaa_respiratorias", "csaa_infecciosas", "csaa_otras", "no_csaa"]
    assert np.allclose(piv[partes].sum(axis=1), piv["todas"], atol=1e-3)
    fr = Pm.pivot_table(index=k, columns="grupo_causa", values="fraccion", aggfunc="sum")
    assert np.allclose(fr[partes].sum(axis=1), 1, atol=1e-9)
    pk = Pm[Pm["poblacion"] > 0]
    assert np.allclose(pk["mx"] * pk["poblacion"], pk["defunciones"], rtol=1e-9, atol=1e-6)
    dp = json.loads((OUT / "parametros" / "datapackage.json").read_text(encoding="utf-8"))
    assert [f["name"] for f in dp["resources"][0]["schema"]["fields"]] == list(Pm.columns)


def test_transcripcion_adres():
    dep = pd.read_csv(ADRES / "adres_hecsap_2025_departamentos.csv"); con = pd.read_csv(ADRES / "adres_hecsap_2025_condiciones.csv")
    assert len(dep) == 33 and sorted(dep["cod_dpto"]) == CODS
    assert int(con["hospitalizaciones"].sum()) == 748212                       # cuadro 1
    assert abs(con["costo_total_cop"].sum() / 1e12 - 8.36) < 0.005             # cuadro 1: 8,36 billones
    assert ((dep["hosp_hecsap"] / dep["hosp_total"] * 100 - dep["pct_hecsap"]).abs() < 0.06).all()
    # grupos 1 y 17 tienen el mismo total en la fuente (10 823 + 1 380 = 12 203; cuadro 2, pág. 16)
    g = con.groupby("grupo_csaa")["hospitalizaciones"].sum()
    assert g[1] == g[17] == 12203
    eb = pd.read_csv(ADRES / "adres_hecsap_2025_edad.csv")
    assert abs(eb["pct_pacientes_hecsap"].sum() - 100.1) < 1e-9


def test_reh_recalculada():
    dep = pd.read_csv(ADRES / "adres_hecsap_2025_departamentos.csv").set_index("cod_dpto")
    p25 = pd.read_parquet(INT / "poblacion_2025_edad_simple.parquet")
    impl = dep["hosp_hecsap"] / dep["tasa_hecsap_10k"] * 1e4
    assert ((impl / p25.groupby("dp")["pob"].sum().reindex(impl.index) - 1).abs() < 0.005).all()
    eb = pd.read_csv(ADRES / "adres_hecsap_2025_edad.csv")
    bandas = pd.cut(p25["edad"], [-1, 17, 39, 59, 79, 200], labels=False)
    PB = p25.groupby(["dp", bandas])["pob"].sum().unstack(fill_value=0)
    hb = eb["pct_pacientes_hecsap"].values / eb["pct_pacientes_hecsap"].sum() * 748212
    reh = dep.reindex(PB.index)["hosp_hecsap"].values / (PB.values @ (hb / PB.sum(axis=0).values))
    H = pd.read_csv(OUT / "tablas" / "hospitalizaciones_vs_muertes_2025.csv").set_index("cod")
    assert np.allclose(reh, H.loc[PB.index, "reh"].values, atol=0.0006)


def test_rme_recalculada(C, P):
    """RME de 2025, todas las edades: muertes observadas / esperadas con las tasas nacionales en 19 grupos de edad. La
    edad desconocida se reparte dentro de cada departamento (aproximación de esta prueba)."""
    c = C[(C["anio"] == 2025) & (C["grupo"] > 0) & (C["d"] < 33)]
    p = P[P["anio"] == 2025]
    Dn = c[c["g"] >= 0].groupby("g")["n"].sum().reindex(range(19), fill_value=0) * (c["n"].sum() / c.loc[c["g"] >= 0, "n"].sum())
    Nn = p.groupby("g")["pob"].sum().reindex(range(19))
    m = (Dn / Nn).values
    H = pd.read_csv(OUT / "tablas" / "hospitalizaciones_vs_muertes_2025.csv").set_index("cod")
    for i, cod in enumerate(CODS):
        obs = c[c["d"] == i]["n"].sum()
        esp = (p[p["cod_dpto"] == cod].groupby("g")["pob"].sum().reindex(range(19), fill_value=0).values * m).sum()
        assert abs(obs / esp / H.loc[cod, "rme"] - 1) < 0.01, cod


def test_municipal_recalculado():
    """Razón municipal: suma de O = suma de E; suavizado de Marshall y clasificación recalculados aquí."""
    from scipy import stats
    t = pd.read_parquet(INT / "municipal_csaa.parquet")
    o, e = t["muertes_csaa75"].to_numpy(float), t["esperadas"].to_numpy()
    assert abs(o.sum() - e.sum()) < 1e-3 and len(t) == 1122
    m = o.sum() / e.sum(); s2 = (e * (o / e - m) ** 2).sum() / e.sum() - m / e.mean()
    a = m * m / s2; b = m / s2
    M = pd.read_csv(OUT / "municipal" / "rme_municipal_2023_2025.csv").set_index("mun").loc[t["mun"]]
    assert np.allclose(np.round((o + a) / (e + b), 3), M["rme_eb"].to_numpy(), atol=1e-3)
    lo = stats.chi2.ppf(.025, 2 * o) / 2 / e; hi = stats.chi2.ppf(.975, 2 * (o + 1)) / 2 / e
    alta = (o >= 10) & (np.nan_to_num(lo) > 1); baja = (o >= 10) & (hi < 1)
    R = json.loads((OUT / "municipal" / "resultados.json").read_text(encoding="utf-8"))
    assert (int((o >= 10).sum()), int(alta.sum()), int(baja.sum())) == (R["municipios_10"], R["n_alta"], R["n_baja"])


def test_tablas_territoriales_adres():
    t6 = pd.read_csv(ADRES / "adres_hecsap_2025_oe_departamentos.csv")
    assert ((t6["n_alto"] + t6["n_esperado"] + t6["n_bajo"]) == t6["n_mun"]).all() and t6["n_mun"].sum() == 1090
    d5 = pd.read_csv(ADRES / "adres_hecsap_2025_departamentos.csv").set_index("cod_dpto")
    t10 = pd.read_csv(ADRES / "adres_hecsap_2025_concentracion.csv").set_index("cod_dpto")
    dif = (100 * t10["n_hecsap_principal"] / d5.loc[t10.index, "hosp_hecsap"] - t10["peso_principal_pct"]).abs()
    assert set(t10.loc[dif > 0.1, "departamento"]) == {"Chocó", "Guainía"}
    top = pd.read_csv(OUT / "municipal" / "top_municipios_adres.csv")
    pob = pd.read_parquet(INT / "municipal_csaa.parquet").set_index("mun")["pob_2025"]
    assert np.allclose(top["hosp_por_10k"], np.round(1e4 * top["n_hecsap"] / pob.loc[top["mun"]].to_numpy(), 1))
