"""Mortalidad por condiciones sensibles a la atención primaria (CSAA) por municipio, y cruce con el análisis
territorial y municipal del informe HECSAP de la ADRES (julio de 2026). Es scripts/43b_aps_municipal.py del
repositorio EEVV partido en dos niveles: nivel_b() escribe data/intermedios/municipal_csaa.parquet desde los
microdatos; nivel_a() estima desde ese intermedio. Las salidas son idénticas a las del repositorio EEVV.

Lo que calcula, para 2023–2025 y los 1.122 municipios con residentes (sin residentes en el exterior):

  1. contar(): muertes por CSAA de menores de 75 años con edad y municipio conocidos (O; 589 de 66.251 no traen
     municipio y quedan fuera), todas las muertes de menores de 75
     (para la proporción), muertes por CSAA de todas las edades y población 2025. Las esperadas (E) aplican la
     tasa nacional por grupo de edad (0, 1–4, 5–9, …, 70–74; sexos juntos, porque la proyección municipal por
     edad no trae sexo) a la población de cada municipio en los tres años. Así la suma de O es igual a la de E.
  2. estimar(): razón estandarizada de mortalidad (RME = O/E) con intervalo exacto de Poisson (el análogo del
     método de Byar que usa la ADRES), y RME suavizada con un modelo Poisson-gamma bayesiano empírico (momentos
     de Marshall, 1991): (O + a)/(E + b), con intervalo de la gamma posterior. Clasificación como la de la ADRES,
     con intervalo exacto y solo municipios con 10 o más muertes: alta (IC inferior > 1), esperada o baja (IC
     superior < 1); y la misma clasificación con el intervalo bayesiano, que descuenta el ruido de los municipios
     pequeños.
  3. Por departamento: porcentaje de municipios en cada clase, frente a la tabla 6 de la ADRES (porcentaje de
     municipios con O/E de hospitalización alto). El O/E de la ADRES es otra cosa: hospitalizaciones por CSAA
     sobre las esperadas con la proporción nacional (19,5 %) de las hospitalizaciones del municipio (anexo A,
     10.1.5); mide composición del uso hospitalario, no frecuencia por habitante.
  4. Concentración: peso del municipio principal (tabla 10 de la ADRES) en las hospitalizaciones por CSAA, en las
     muertes por CSAA de todas las edades y en la población del departamento.
  5. Los diez municipios con O/E de hospitalización más alto y más bajo (tablas 8 y 9): su RME de mortalidad.

  6. priorizar(): matriz de dos ejes para departamentos y municipios. Riesgo: razón de mortalidad (suavizada en
     municipios) de al menos 1,25 con intervalo sobre 1. Carga: muertes en exceso por año, E·(razón − 1)/3, de al
     menos 10 en un municipio o 100 en un departamento. Cuadrantes: foco intensivo (riesgo y carga), foco por volumen
     (intervalo sobre 1, razón menor que 1,25 y carga), foco por riesgo (riesgo sin carga) y vigilancia. Los umbrales
     son convenciones: el resumen trae cuántos municipios caen en cada cuadrante con 1,2 / 1,25 / 1,3 y 5 / 10 / 20.

Salidas: output/estudios/43_mortalidad_aps/municipal/ (CSV, resultados.json y priorizacion.json) y
output/tablas/aps_municipal_tablero.json.
Publicación: cuando un municipio tiene entre 1 y 4 muertes, el tablero no muestra el número, las esperadas ni las
razones (se despejaría el número), solo la clase.
"""
from __future__ import annotations

import json
import os
import sys
import unicodedata
from pathlib import Path

for _v in ("POLARS_MAX_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import numpy as np
import polars as pl
from scipy import stats

from .rutas import ADRES as EXT, INTERMEDIOS, OUTPUT, RAW, procesado

DIVIPOLA = RAW / "externos" / "divipola" / "divipola_gdxc-w37w.csv"
HOSP = OUTPUT / "tablas" / "hospitalizaciones_vs_muertes_2025.csv"
ULT = (2023, 2024, 2025)
Q75 = 16                     # grupos 0..15 = menores de 75
MIN_MUERTES = 10             # como el mínimo de 10 casos de la ADRES
# Priorización (matriz de dos ejes; convenciones explícitas, con sensibilidad en el resumen)
UMBRAL_RIESGO = 1.25         # razón de mortalidad: al menos 25 % por encima de lo esperado (y su intervalo sobre 1)
UMBRAL_CARGA_MUN = 10        # muertes en exceso por año en un municipio
UMBRAL_CARGA_DEP = 100       # muertes en exceso por año en un departamento
CUADRANTES = ["foco intensivo", "foco por volumen", "foco por riesgo", "vigilancia"]


def grupo_edad(e):
    e = np.asarray(e)
    return np.where(e == 0, 0, np.where(e < 5, 1, e // 5 + 1))


# ── 1. conteos (necesita los microdatos procesados) ─────────────────────────────────────────────
def contar(codigos: pl.DataFrame) -> pl.DataFrame:
    """Una fila por municipio con O, E, muertes <75 de todas las causas, CSAA de todas las edades y población."""
    csaa = codigos.filter(pl.col("grupo") > 0).select("cb").with_columns(pl.lit(1).alias("es_csaa"))
    d = (pl.scan_parquet(procesado() / "defunciones_eevv.parquet")
         .filter(pl.col("anio").is_in(ULT) & (pl.col("dp") != 75))
         .select(["mun", "g", "cb"]).collect()
         .with_columns(pl.col("cb").fill_null(""))
         .join(csaa, on="cb", how="left").with_columns(pl.col("es_csaa").fill_null(0)))
    p = (pl.read_parquet(procesado() / "mun_pob_edad.parquet")
         .filter((pl.col("area") == "Total") & pl.col("ano").is_in(ULT))
         .with_columns(pl.col("mpio").cast(pl.Int64).alias("mun"),
                       pl.Series("g", grupo_edad(pl.read_parquet(procesado() / "mun_pob_edad.parquet")
                                                  .filter((pl.col("area") == "Total") & pl.col("ano").is_in(ULT))["edad"].to_numpy()))))
    menor = d.filter((pl.col("g") >= 0) & (pl.col("g") < Q75))
    O = menor.filter(pl.col("es_csaa") == 1).group_by(["mun", "g"]).agg(pl.len().alias("o"))
    Pg = p.filter(pl.col("g") < Q75).group_by(["mun", "g"]).agg(pl.col("pob").sum())
    nac = (O.group_by("g").agg(pl.col("o").sum()).join(Pg.group_by("g").agg(pl.col("pob").sum()), on="g")
           .with_columns((pl.col("o") / pl.col("pob")).alias("tasa")).sort("g"))
    E = Pg.join(nac.select(["g", "tasa"]), on="g").group_by("mun").agg((pl.col("pob") * pl.col("tasa")).sum().alias("esperadas"))
    t = (p.filter(pl.col("ano") == 2025).group_by("mun").agg(pl.col("pob").sum().alias("pob_2025"))
         .join(O.group_by("mun").agg(pl.col("o").sum().alias("muertes_csaa75")), on="mun", how="left")
         .join(E, on="mun", how="left")
         .join(menor.group_by("mun").agg(pl.len().alias("muertes_todas75")), on="mun", how="left")
         .join(d.filter(pl.col("es_csaa") == 1).group_by("mun").agg(pl.len().alias("muertes_csaa_todas_edades")), on="mun", how="left")
         .with_columns([pl.col(c).fill_null(0) for c in ("muertes_csaa75", "muertes_todas75", "muertes_csaa_todas_edades")])
         .with_columns((pl.col("mun") // 1000).alias("cod_dpto"))
         .sort("mun"))
    t = t.with_columns(pl.col("muertes_csaa75").cast(pl.Int64), pl.col("muertes_todas75").cast(pl.Int64),
                       pl.col("muertes_csaa_todas_edades").cast(pl.Int64))
    assert abs(t["muertes_csaa75"].sum() - t["esperadas"].sum()) < 1e-6 * t["esperadas"].sum()
    # sin población proyectada en 2023–2025 (Mapiripana, área no municipalizada de Guainía): no tiene tasa
    sin = t.filter(~(pl.col("esperadas") > 0))
    if sin.height:
        print(f"  sin población: {sin['mun'].to_list()} con {int(sin['muertes_csaa75'].sum())} muertes por CSAA <75; se excluyen")
    t = t.filter(pl.col("esperadas") > 0)
    # las sumas de polars cambian en la última cifra con el orden de los hilos: se redondea a 8 decimales
    t = t.with_columns(pl.col("esperadas").round(8), pl.col("pob_2025").round(3))
    return t.select(["cod_dpto", "mun", "pob_2025", "muertes_csaa75", "esperadas", "muertes_todas75", "muertes_csaa_todas_edades"])


# ── 2. estimación ───────────────────────────────────────────────────────────────────────────────
def exacto(o, e, alfa=0.05):
    lo = np.where(o > 0, stats.chi2.ppf(alfa / 2, 2 * o) / 2, 0.0) / e
    hi = stats.chi2.ppf(1 - alfa / 2, 2 * (o + 1)) / 2 / e
    return lo, hi


def bayes_empirico(o, e):
    """Momentos de Marshall (1991): media m = ΣO/ΣE; varianza s2 = Σ E(r − m)² / ΣE − m / Ē (mínimo 0)."""
    r = o / e
    m = o.sum() / e.sum()
    s2 = max((e * (r - m) ** 2).sum() / e.sum() - m / e.mean(), 1e-9)
    b = m / s2; a = m * b
    post = (o + a) / (e + b)
    lo = stats.gamma.ppf(0.025, o + a, scale=1 / (e + b)); hi = stats.gamma.ppf(0.975, o + a, scale=1 / (e + b))
    return post, lo, hi, dict(m=m, s2=s2, a=a, b=b)


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    return " ".join(s.replace(",", " ").replace(".", " ").split())


ALIAS = {"CALI": "SANTIAGO DE CALI", "CUCUTA": "SAN JOSE DE CUCUTA", "BOGOTA D C": "BOGOTA D C",
         "SAN ANDRES": "SAN ANDRES"}


def codigo_municipio(div, cod_dpto, nombre):
    n = norm(nombre)
    sub = div.filter(pl.col("cod_dpto") == cod_dpto)
    for cand in (n, ALIAS.get(n, n)):
        hit = sub.filter(pl.col("nombre_n") == cand)
        if hit.height == 1:
            return int(hit["mun"][0])
    hit = sub.filter(pl.col("nombre_n").str.contains(n.split()[0]) & pl.col("nombre_n").str.contains(n.split()[-1]))
    if hit.height == 1:
        return int(hit["mun"][0])
    raise ValueError(f"no se encontró {nombre} ({cod_dpto}) en la DIVIPOLA: {hit['nombre_n'].to_list()}")


MINUS = {"de", "del", "la", "las", "los", "el", "y", "e", "en"}


def titulo(nombre):
    """MEDELLÍN -> Medellín; SAN JUAN DE RIOSECO -> San Juan de Rioseco; BOGOTÁ, D.C. -> Bogotá, D.C."""
    out = []
    for i, w in enumerate(str(nombre).split()):
        lw = w.lower()
        if "." in w and len(w) <= 5:
            out.append(w.upper())
        elif i > 0 and lw in MINUS:
            out.append(lw)
        else:
            out.append("-".join(x[:1].upper() + x[1:] for x in lw.split("-")))
    return " ".join(out)


def divipola():
    d = pl.read_csv(DIVIPOLA, infer_schema_length=0)
    return d.select(pl.col("Código Departamento").cast(pl.Int64).alias("cod_dpto"), pl.col("Código Municipio").cast(pl.Int64).alias("mun"),
                    pl.col("Nombre Municipio").map_elements(titulo, return_dtype=pl.String).alias("municipio"), pl.col("Nombre Departamento").alias("depto_mayus")).with_columns(
        pl.col("municipio").map_elements(norm, return_dtype=pl.String).alias("nombre_n"))


def estimar(t: pl.DataFrame, nombres_dpto: dict) -> dict:
    o = t["muertes_csaa75"].to_numpy().astype(float); e = t["esperadas"].to_numpy()
    lo, hi = exacto(o, e)
    eb, eblo, ebhi, prior = bayes_empirico(o, e)
    suf = o >= MIN_MUERTES
    clase = np.where(~suf, "pocas muertes", np.where(lo > 1, "alta", np.where(hi < 1, "baja", "esperada")))
    clase_eb = np.where(eblo > 1, "alta", np.where(ebhi < 1, "baja", "esperada"))
    div = divipola()
    t = (t.with_columns(pl.Series("rme", np.round(o / e, 3)), pl.Series("rme_lo", np.round(lo, 3)), pl.Series("rme_hi", np.round(hi, 3)),
                        pl.Series("rme_eb", np.round(eb, 3)), pl.Series("rme_eb_lo", np.round(eblo, 3)), pl.Series("rme_eb_hi", np.round(ebhi, 3)),
                        pl.Series("clase", clase), pl.Series("clase_eb", clase_eb),
                        pl.Series("pct_csaa_de_muertes75", np.round(np.divide(100 * o, t["muertes_todas75"].to_numpy(), out=np.full(len(o), np.nan), where=t["muertes_todas75"].to_numpy() > 0), 1)))
         .join(div.select(["mun", "municipio"]), on="mun", how="left"))
    # por departamento, frente a la tabla 6 de la ADRES
    a6 = pl.read_csv(EXT / "adres_hecsap_2025_oe_departamentos.csv")
    filas = []
    for c in sorted(nombres_dpto):
        x = t.filter((pl.col("cod_dpto") == c) & (pl.col("clase") != "pocas muertes"))
        n = x.height
        f = lambda k: round(100 * (x["clase"] == k).sum() / n, 1) if n else None
        xe = t.filter(pl.col("cod_dpto") == c)
        filas.append(dict(cod_dpto=c, departamento=nombres_dpto[c], n_mun_total=xe.height, n_mun_10=n,
                          pct_alta=f("alta"), pct_esperada=f("esperada"), pct_baja=f("baja"),
                          pct_alta_eb=round(100 * (xe["clase_eb"] == "alta").sum() / xe.height, 1),
                          pct_baja_eb=round(100 * (xe["clase_eb"] == "baja").sum() / xe.height, 1),
                          rme_dpto=round(xe["muertes_csaa75"].sum() / xe["esperadas"].sum(), 3)))
    dep = pl.DataFrame(filas).join(a6.select(["cod_dpto", "n_mun", "pct_alto", "pct_bajo", "oe_ponderado"]).rename(
        {"n_mun": "adres_n_mun", "pct_alto": "adres_pct_alto", "pct_bajo": "adres_pct_bajo", "oe_ponderado": "adres_oe_ponderado"}), on="cod_dpto", how="left")
    dd = dep.filter(pl.col("n_mun_10") >= 3)
    rho = lambda a, b: round(float(stats.spearmanr(dd[a].to_numpy(), dd[b].to_numpy()).statistic), 3)
    def rho_ic(a, b):            # transformación de Fisher, error estándar 1/sqrt(n − 3)
        z = np.arctanh(rho(a, b)); se = 1 / np.sqrt(dd.height - 3)
        return [round(float(np.tanh(z - 1.959964 * se)), 2), round(float(np.tanh(z + 1.959964 * se)), 2)]
    # concentración
    a10 = pl.read_csv(EXT / "adres_hecsap_2025_concentracion.csv")
    conc = []
    for r in a10.iter_rows(named=True):
        m = codigo_municipio(div, r["cod_dpto"], r["municipio_principal"])
        xe = t.filter(pl.col("cod_dpto") == r["cod_dpto"]); xm = xe.filter(pl.col("mun") == m)
        conc.append(dict(cod_dpto=r["cod_dpto"], departamento=r["departamento"], municipio=r["municipio_principal"], mun=m,
                         peso_hospitalizaciones=r["peso_principal_pct"],
                         peso_muertes=round(100 * xm["muertes_csaa_todas_edades"].sum() / xe["muertes_csaa_todas_edades"].sum(), 1),
                         peso_poblacion=round(100 * xm["pob_2025"].sum() / xe["pob_2025"].sum(), 1)))
    conc = pl.DataFrame(conc).with_columns((pl.col("peso_hospitalizaciones") - pl.col("peso_muertes")).round(1).alias("brecha_hosp_muertes"))
    cc = conc.filter(pl.col("cod_dpto") != 11)
    # los diez de cada extremo
    a89 = pl.read_csv(EXT / "adres_hecsap_2025_oe_top_municipios.csv")
    top = []
    for r in a89.iter_rows(named=True):
        m = codigo_municipio(div, r["cod_dpto"], r["municipio"])
        x = t.filter(pl.col("mun") == m).row(0, named=True)
        top.append(dict(lado=r["lado"], orden=r["orden"], municipio=r["municipio"], departamento=r["departamento"], mun=m,
                        oe_hosp=r["oe"], n_hecsap=r["n_hecsap"], pob_2025=round(x["pob_2025"]),
                        hosp_por_10k=round(1e4 * r["n_hecsap"] / x["pob_2025"], 1),
                        muertes_csaa75=x["muertes_csaa75"], rme=x["rme"], rme_lo=x["rme_lo"], rme_hi=x["rme_hi"],
                        rme_eb=x["rme_eb"], rme_eb_lo=x["rme_eb_lo"], rme_eb_hi=x["rme_eb_hi"], clase_eb=x["clase_eb"]))
    top = pl.DataFrame(top)
    tasa_nac_hosp = 141.0
    res = dict(
        periodo="2023–2025", municipios=t.height, municipios_10=int(suf.sum()),
        pct_alta=round(100 * (clase == "alta").sum() / suf.sum(), 1), pct_baja=round(100 * (clase == "baja").sum() / suf.sum(), 1),
        n_alta=int((clase == "alta").sum()), n_baja=int((clase == "baja").sum()),
        n_alta_eb=int((clase_eb == "alta").sum()), n_baja_eb=int((clase_eb == "baja").sum()),
        prior=dict(m=round(prior["m"], 4), varianza=round(prior["s2"], 4), a=round(prior["a"], 2), b=round(prior["b"], 2)),
        rme_eb_p05_p95=[round(float(np.percentile(eb, 5)), 3), round(float(np.percentile(eb, 95)), 3)],
        rme_cruda_p05_p95=[round(float(np.percentile(o[e > 0] / e[e > 0], 5)), 3), round(float(np.percentile(o[e > 0] / e[e > 0], 95)), 3)],
        adres_n_mun=int(a6["n_mun"].sum()), adres_n_alto=int(a6["n_alto"].sum()), adres_n_bajo=int(a6["n_bajo"].sum()),
        muertes_por_municipio=round(float(o.mean()), 1), hosp_por_municipio=round(748212 / t.height, 0),
        spearman_dpto=dict(pct_alta_vs_adres_pct_alto=rho("pct_alta", "adres_pct_alto"), pct_alta_vs_adres_pct_alto_ic=rho_ic("pct_alta", "adres_pct_alto"),
                           rme_dpto_vs_adres_oe_ic=rho_ic("rme_dpto", "adres_oe_ponderado"), pct_alta_eb_vs_adres_pct_alto=rho("pct_alta_eb", "adres_pct_alto"),
                           rme_dpto_vs_adres_oe=rho("rme_dpto", "adres_oe_ponderado"), n_departamentos=dd.height),
        concentracion=dict(media_peso_hosp=round(float(cc["peso_hospitalizaciones"].mean()), 1), media_peso_muertes=round(float(cc["peso_muertes"].mean()), 1),
                           media_peso_pob=round(float(cc["peso_poblacion"].mean()), 1),
                           n_hosp_mayor_que_muertes=int((cc["brecha_hosp_muertes"] > 0).sum()), n=cc.height,
                           spearman_brecha_vs_rme_sobre_reh=round(float(stats.spearmanr(*cc.join(pl.read_csv(HOSP).select(
                               pl.col("cod").alias("cod_dpto"), "rme_sobre_reh"), on="cod_dpto").select(["brecha_hosp_muertes", "rme_sobre_reh"]).to_numpy().T).statistic), 3)),
        top=dict(alto_n_mortalidad_baja=int(((top["lado"] == "alto") & (top["clase_eb"] == "baja")).sum()),
                 alto_n_mortalidad_alta=int(((top["lado"] == "alto") & (top["clase_eb"] == "alta")).sum()),
                 bajo_n_mortalidad_alta=int(((top["lado"] == "bajo") & (top["clase_eb"] == "alta")).sum()),
                 bajo_n_hosp_sobre_nacional=int(((top["lado"] == "bajo") & (top["hosp_por_10k"] > 141.0)).sum()),
                 alto_rme_eb_mediana=float(top.filter(pl.col("lado") == "alto")["rme_eb"].median()),
                 bajo_rme_eb_mediana=float(top.filter(pl.col("lado") == "bajo")["rme_eb"].median()),
                 alto_hosp_10k_mediana=float(top.filter(pl.col("lado") == "alto")["hosp_por_10k"].median()),
                 bajo_hosp_10k_mediana=float(top.filter(pl.col("lado") == "bajo")["hosp_por_10k"].median()),
                 tasa_nacional_hosp_10k=tasa_nac_hosp))
    return dict(municipios=t, departamentos=dep, concentracion=conc, top=top, resumen=res)


def cuadrante(riesgo_sig, razon, exceso, umbral_r, umbral_c):
    """foco intensivo: razón ≥ umbral (con intervalo sobre 1) y exceso ≥ umbral; foco por volumen: intervalo sobre 1,
    razón menor que el umbral y exceso ≥ umbral; foco por riesgo: razón ≥ umbral con intervalo sobre 1 y exceso menor;
    vigilancia: el resto."""
    alto_r = riesgo_sig & (razon >= umbral_r); carga = exceso >= umbral_c
    return np.where(alto_r & carga, "foco intensivo", np.where(riesgo_sig & ~alto_r & carga, "foco por volumen",
                    np.where(alto_r, "foco por riesgo", "vigilancia")))


def priorizar(R: dict) -> dict:
    t = R["municipios"]
    e = t["esperadas"].to_numpy(); r = t["rme_eb"].to_numpy(); sig = t["rme_eb_lo"].to_numpy() > 1
    exc = e * (r - 1) / 3
    cu = cuadrante(sig, r, exc, UMBRAL_RIESGO, UMBRAL_CARGA_MUN)
    t = t.with_columns(pl.Series("exceso_anual", np.round(exc, 2)), pl.Series("cuadrante", cu))
    # departamentos: la misma razón indirecta con los municipios (menores de 75, edad, sexos juntos), intervalo exacto
    reg = dict(pl.read_parquet(OUTPUT / "parametros" / "mortalidad_aps_parametros.parquet").select(["cod_dpto", "registro"]).unique().iter_rows())
    d = t.group_by("cod_dpto").agg(pl.col("muertes_csaa75").sum().alias("o"), pl.col("esperadas").sum().alias("e"), pl.col("pob_2025").sum().alias("pob_2025")).sort("cod_dpto")
    o = d["o"].to_numpy().astype(float); ed = d["e"].to_numpy(); lo, hi = exacto(o, ed)
    excd = (o - ed) / 3
    cud = cuadrante(lo > 1, o / ed, excd, UMBRAL_RIESGO, UMBRAL_CARGA_DEP)
    hosp = pl.read_csv(HOSP).select(pl.col("cod").alias("cod_dpto"), "tasa_hosp_10k", "reh", "rme_sobre_reh", "rme_sobre_reh_lo", "rme_sobre_reh_hi")
    dep = (d.with_columns(pl.Series("razon", np.round(o / ed, 3)), pl.Series("razon_lo", np.round(lo, 3)), pl.Series("razon_hi", np.round(hi, 3)),
                          pl.Series("exceso_anual", np.round(excd, 1)), pl.Series("muertes_anio", np.round(o / 3, 1)), pl.Series("cuadrante", cud),
                          pl.col("cod_dpto").replace_strict(reg, default=None).alias("registro"), pl.col("e").round(3))
           .join(R["departamentos"].select(["cod_dpto", "departamento", "adres_pct_alto"]), on="cod_dpto", how="left")
           .join(hosp, on="cod_dpto", how="left").sort(["exceso_anual", "cod_dpto"], descending=[True, False]))
    # resumen y sensibilidad a los umbrales
    pos = np.clip(exc, 0, None)
    focos = np.isin(cu, ["foco intensivo", "foco por volumen"])
    sens = {}
    for ur in (1.2, 1.25, 1.3):
        for uc in (5, 10, 20):
            c2 = cuadrante(sig, r, exc, ur, uc)
            sens[f"{ur}_{uc}"] = {k: int((c2 == k).sum()) for k in CUADRANTES}
    orden = t.filter(pl.col("muertes_csaa75") >= 5).sort(["exceso_anual", "mun"], descending=[True, False])
    res = dict(umbral_riesgo=UMBRAL_RIESGO, umbral_carga_mun=UMBRAL_CARGA_MUN, umbral_carga_dep=UMBRAL_CARGA_DEP,
               municipios={k: int((cu == k).sum()) for k in CUADRANTES}, departamentos={k: int((cud == k).sum()) for k in CUADRANTES},
               exceso_positivo_total=round(float(pos.sum()), 1), exceso_en_focos=round(float(pos[focos].sum()), 1),
               pct_exceso_en_focos=round(float(100 * pos[focos].sum() / pos.sum()), 1), n_focos=int(focos.sum()),
               pob_focos_pct=round(float(100 * t["pob_2025"].to_numpy()[focos].sum() / t["pob_2025"].sum()), 1),
               top10=[dict(municipio=x["municipio"], cod_dpto=x["cod_dpto"], exceso_anual=x["exceso_anual"], rme_eb=x["rme_eb"], cuadrante=x["cuadrante"])
                      for x in orden.head(10).iter_rows(named=True)],
               sensibilidad_umbrales_municipios=sens,
               dep_grave_en_focos=[x["departamento"] for x in dep.filter(pl.col("cuadrante").is_in(["foco intensivo", "foco por riesgo"]) & (pl.col("registro") == "grave")).iter_rows(named=True)])
    R = dict(R); R["municipios"] = t; R["prioridad_dep"] = dep; R["prioridad"] = res
    return R


def publicar(R: dict, salida: Path, tablas: Path):
    salida.mkdir(parents=True, exist_ok=True)
    R["municipios"].sort("mun").write_csv(salida / "rme_municipal_2023_2025.csv")
    R["departamentos"].write_csv(salida / "departamentos_municipal.csv")
    R["concentracion"].write_csv(salida / "concentracion.csv")
    R["top"].write_csv(salida / "top_municipios_adres.csv")
    (salida / "resultados.json").write_text(json.dumps(R["resumen"], ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    R["municipios"].select(["cod_dpto", "mun", "municipio", "pob_2025", "muertes_csaa75", "esperadas", "rme_eb", "rme_eb_lo", "rme_eb_hi", "exceso_anual", "cuadrante"]
                           ).sort(["exceso_anual", "mun"], descending=[True, False]).write_csv(salida / "priorizacion_municipios.csv")
    R["prioridad_dep"].write_csv(salida / "priorizacion_departamentos.csv")
    (salida / "priorizacion.json").write_text(json.dumps(R["prioridad"], ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    # tablero: muertes de 1 a 4 se publican como «<5»
    m = R["municipios"].sort("mun")
    oculto = lambda r: 1 <= r["muertes_csaa75"] <= 4            # con E y la razón suavizada se despejaría O
    filas = [[r["mun"], r["cod_dpto"], r["municipio"], round(r["pob_2025"]),
              (-1 if oculto(r) else r["muertes_csaa75"]),
              (None if oculto(r) else round(r["esperadas"], 1)), *([None] * 3 if oculto(r) else [r["rme_eb"], r["rme_eb_lo"], r["rme_eb_hi"]]), r["clase_eb"],
              (r["rme"] if r["muertes_csaa75"] >= MIN_MUERTES else None), r["clase"],
              (None if oculto(r) else r["exceso_anual"]), (None if oculto(r) else r["cuadrante"])] for r in m.iter_rows(named=True)]
    top = [{k: (None if (1 <= x["muertes_csaa75"] <= 4 and k in ("muertes_csaa75", "rme", "rme_lo", "rme_hi", "rme_eb", "rme_eb_lo", "rme_eb_hi")) else v)
            for k, v in x.items()} for x in R["top"].to_dicts()]
    tab = dict(campos=["mun", "cod_dpto", "municipio", "pob_2025", "muertes", "esperadas", "rme_eb", "rme_eb_lo", "rme_eb_hi", "clase_eb", "rme", "clase", "exceso_anual", "cuadrante"],
               nota_muertes="-1 = entre 1 y 4 muertes: no se publican el número, las esperadas ni las razones, solo la clase",
               municipios=filas, departamentos=R["departamentos"].to_dicts(), concentracion=R["concentracion"].to_dicts(),
               top=top, resumen=R["resumen"], prioridad=R["prioridad"], prioridad_dep=R["prioridad_dep"].to_dicts())
    (tablas / "aps_municipal_tablero.json").write_text(json.dumps(tab, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def nivel_b(salida: Path):
    contar(pl.read_parquet(salida / "codigos.parquet")).write_parquet(salida / "municipal_csaa.parquet")


def nivel_a():
    t = pl.read_parquet(INTERMEDIOS / "municipal_csaa.parquet")
    R0 = json.loads((OUTPUT / "resultados.json").read_text(encoding="utf-8"))
    nombres = {int(x["cod"]): x["territorio"] for x in R0["trienio"] if x["sexo"] == "total" and x["cod"] != 0}
    R = priorizar(estimar(t, nombres))
    publicar(R, OUTPUT / "municipal", OUTPUT)
    return R
