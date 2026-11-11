"""Análisis que pidió el árbitro (5 de noviembre de 2026) y que no están en el estudio 43 del Termómetro.

Lee output/resultados.json y aps_tablero.json (los deja calculo.nivel_a()) y data/intermedios/, y escribe
output/sensibilidad.json y output/tablas/serie_grupos_infecciosos.csv:

  tendencia()      cambio porcentual anual (CPA) de las tasas nacionales con una regresión lineal del logaritmo de
                   la tasa sobre el año, 1998–2014 y 2014–2025 sin 2020 y 2021 (pandemia), con IC 95 % de la t.
  grupos()         tasas estandarizadas por grupo de CSAA, 2011 y 2025, para ver de dónde viene el repunte de las
                   infecciosas. Reparto proporcional de la edad desconocida dentro de cada año y grupo (aproximación
                   que difiere de calculo.repartir_edad() en menos de 1 %).
  sobredispersion() factor de dispersión de Pearson de las tasas departamentales frente a la nacional y del
                   logaritmo de RME/REH frente a 0; recuenta los departamentos por encima y por debajo con los
                   intervalos ensanchados por la raíz del factor (cuasi-Poisson).
  reh_cruda()      el cociente RME/REH con la razón de hospitalización cruda (tasa departamental / tasa nacional),
                   sin el perfil de edad de los pacientes de la ADRES.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy import stats

from .rutas import CONFIG, INTERMEDIOS, OUTPUT

Z = 1.959964


def _cpa(anios, tasas):
    x = np.asarray(anios, float); y = np.log(np.asarray(tasas, float))
    r = stats.linregress(x, y)
    t = stats.t.ppf(0.975, len(x) - 2)
    f = lambda b: round(100 * (np.exp(b) - 1), 2)
    return dict(cpa=f(r.slope), lo=f(r.slope - t * r.stderr), hi=f(r.slope + t * r.stderr), p=round(float(r.pvalue), 3), n=len(x))


def tendencia(R):
    S = {x["anio"]: x for x in R["nacional"] if x["sexo"] == "total"}
    out = {}
    for var in ("tee_csaa", "tee_todas75", "tee_cardiometabolicas", "tee_respiratorias", "tee_infecciosas", "tee_otras"):
        a1 = list(range(1998, 2015)); a2 = [a for a in range(2014, 2026) if a not in (2020, 2021)]
        out[var] = {"1998_2014": _cpa(a1, [S[a][var] for a in a1]), "2014_2025_sin_2020_2021": _cpa(a2, [S[a][var] for a in a2])}
    return out


def grupos():
    C = pd.read_parquet(INTERMEDIOS / "conteos.parquet")
    P = pd.read_parquet(INTERMEDIOS / "poblacion.parquet")
    std = pd.read_csv(CONFIG / "poblacion_estandar_ocde2015.csv")["poblacion_ocde38_2015"].to_numpy(float)
    w = std[:15] / std.sum()
    q = lambda g: np.where(g <= 1, 0, g - 1)
    filas = []
    for a in (2011, 2025):
        p = P[P["anio"] == a]
        N = p.groupby(q(p["g"].to_numpy()))["pob"].sum().reindex(range(18), fill_value=0).to_numpy()[:15]
        for g in (1, 2, 5, 6, 15, 16, 17):
            c = C[(C["anio"] == a) & (C["grupo"] == g)]
            k = c[c["g"] >= 0]
            fac = c["n"].sum() / k["n"].sum() if k["n"].sum() > 0 else 0
            D = k.groupby(q(k["g"].to_numpy()))["n"].sum().reindex(range(18), fill_value=0).to_numpy()[:15] * fac
            filas.append(dict(anio=a, grupo=g, tasa=round(float((w * D / N).sum() * 1e5), 2)))
    df = pd.DataFrame(filas).pivot(index="grupo", columns="anio", values="tasa").reset_index()
    df.columns = ["grupo", "tasa_2011", "tasa_2025"]
    df.to_csv(OUTPUT / "tablas" / "serie_grupos_infecciosos.csv", index=False)
    return {int(r.grupo): dict(t2011=r.tasa_2011, t2025=r.tasa_2025) for r in df.itertuples()}


def _dispersion(lnx, se, ref):
    z = (lnx - ref) / se
    phi = float((z ** 2).sum() / (len(z) - 1))
    s = se * np.sqrt(max(phi, 1.0))
    return phi, int(((lnx - Z * s) > ref).sum()), int(((lnx + Z * s) < ref).sum())


def sobredispersion(R, T):
    nac = next(x for x in R["trienio"] if x["cod"] == 0 and x["sexo"] == "total")
    d = [x for x in R["trienio"] if x["cod"] != 0 and x["sexo"] == "total"]
    lnr = np.log([x["tee_csaa"] for x in d]); se = (np.log([x["tee_csaa_hi"] for x in d]) - np.log([x["tee_csaa_lo"] for x in d])) / (2 * Z)
    phi_t, arr_t, aba_t = _dispersion(lnr, se, np.log(nac["tee_csaa"]))
    st = se * np.sqrt(max(phi_t, 1.0)); ref = np.log(nac["tee_csaa"])
    arr_tl = [x["territorio"] for x, l, s in zip(d, lnr, st) if l - Z * s > ref]
    aba_tl = [x["territorio"] for x, l, s in zip(d, lnr, st) if l + Z * s < ref]
    h = [x for x in T["hospitalizaciones"]["departamentos"] if x["cod"] != 0]
    lnc = np.log([x["rme_sobre_reh"] for x in h]); sec = (np.log([x["rme_sobre_reh_hi"] for x in h]) - np.log([x["rme_sobre_reh_lo"] for x in h])) / (2 * Z)
    phi_c, arr_c, aba_c = _dispersion(lnc, sec, 0.0)
    orden = sorted(h, key=lambda x: -x["rme_sobre_reh"])
    s_aj = dict(zip([x["territorio"] for x in h], sec * np.sqrt(phi_c)))
    top = [x["territorio"] for x in orden if np.log(x["rme_sobre_reh"]) - Z * s_aj[x["territorio"]] > 0]
    return dict(tasas=dict(phi=round(phi_t, 1), arriba=arr_t, abajo=aba_t, arriba_lista=arr_tl, abajo_lista=aba_tl),
                rme_sobre_reh=dict(phi=round(phi_c, 1), arriba=arr_c, abajo=aba_c, arriba_lista=top,
                                   abajo_lista=[x["territorio"] for x in orden[::-1] if np.log(x["rme_sobre_reh"]) + Z * s_aj[x["territorio"]] < 0]))


def reh_cruda(T):
    h = [x for x in T["hospitalizaciones"]["departamentos"] if x["cod"] != 0]
    tn = T["hospitalizaciones"]["nacional"]["tasa_10k"]
    df = pd.DataFrame(h)
    df["reh_cruda"] = df["tasa_hosp_10k"] / tn
    df["cociente_crudo"] = df["rme"] / df["reh_cruda"]
    se = np.sqrt(1 / df["muertes_csaa"] + 1 / df["hosp_hecsap"])
    lo = np.log(df["cociente_crudo"]) - Z * se; hi = np.log(df["cociente_crudo"]) + Z * se
    rho = stats.spearmanr(df["rme_sobre_reh"], df["cociente_crudo"]).statistic
    top = df.sort_values("cociente_crudo", ascending=False)["territorio"].head(3).tolist()
    return dict(spearman_con_principal=round(float(rho), 3), arriba=int((lo > 0).sum()), abajo=int((hi < 0).sum()), tres_mayores=top,
                spearman_reh_cruda_rme=round(float(stats.spearmanr(df["reh_cruda"], df["rme"]).statistic), 3))


def todo():
    R = json.loads((OUTPUT / "resultados.json").read_text(encoding="utf-8"))
    T = json.loads((OUTPUT / "aps_tablero.json").read_text(encoding="utf-8"))
    out = dict(tendencia=tendencia(R), grupos_infecciosos=grupos(), sobredispersion=sobredispersion(R, T), reh_cruda=reh_cruda(T))
    (OUTPUT / "sensibilidad.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return out
