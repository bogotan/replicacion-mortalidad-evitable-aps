"""Cálculo del artículo A5: mortalidad evitable por atención primaria (APS) en Colombia, 1998–2025.

Es el mismo cálculo del estudio 43 del Termómetro de las Estadísticas Vitales (scripts/43_mortalidad_aps.py del
repositorio EEVV), partido en dos niveles:

  nivel_b(salida)   microdatos procesados (data/processed o PROCESADO) -> data/intermedios/ (conteos agregados)
  nivel_a()         data/intermedios/ -> output/ (resultados.json, tablas, parámetros)

Qué hace el nivel A
  1. Reparte la edad desconocida con la distribución conocida de la misma celda.
  2. Tasas estandarizadas por edad (población estándar OCDE 2015, por 100.000, edades 0–74) con intervalo de
     Fay y Feuer; AVPP contra la tabla de referencia GBD 2019, con intervalo gamma.
  3. Probabilidad de sobrevivir de 0 a 65 años con y sin las muertes por condiciones sensibles (decremento
     eliminado de Chiang); intervalos por Monte Carlo con defunciones Poisson (semilla fija).
  4. Sensibilidades: causas mal definidas, códigos poco específicos, corte en 70, todas las neumonías, ampliación
     de la ADRES y escenario con la omisión implícita del DANE.
  5. Cruce con las hospitalizaciones evitables de la ADRES (2026): razones estandarizadas indirectas.
  6. Archivo de parámetros con esquema fijo (output/parametros/).
"""
from __future__ import annotations
import json, os, sys
for _v in ("POLARS_MAX_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
from pathlib import Path
import numpy as np, polars as pl, yaml

from . import termo as T
from . import ocde as m54
from .codigos import clasificador
from .rutas import RAIZ, CONFIG, ADRES, INTERMEDIOS, OUTPUT, PAR, procesado

SAL = OUTPUT
VERSION = "2026.1"
ANIOS = list(range(1998, 2026)); NA = len(ANIOS)
G = T.G; Q75 = 16; Q70 = 15; I65 = T.I65
DEP, CODS, ND, DIX = m54.DEP, m54.CODS, m54.ND, m54.DIX
SEMILLA = 20261105
NSIM = 400
ULT = (2023, 2024, 2025)

# Lista: grupos 1..19 y bloques para el simulador
BLOQUES = ["cardiometabolicas", "respiratorias", "infecciosas", "otras"]
BLOQUE_NOMBRE = {"cardiometabolicas": "Cardiometabólicas (hipertensión, angina, insuficiencia cardíaca, cerebrovascular, diabetes)",
                 "respiratorias": "Respiratorias (asma, EPOC y otras pulmonares)",
                 "infecciosas": "Infecciosas e inmunoprevenibles",
                 "otras": "Otras sensibles (anemia, nutrición, epilepsia, úlcera, prenatal y parto)"}
INESP = ("I50", "J81", "E86")                     # códigos poco específicos como causa básica

# Categorías del arreglo D[a, d, s, g, k]
K = (["todas", "csaa", "maldef", "externas", "csaa_inesp", "trat", "trat2", "neum_extra", "adres_extra"]
     + [f"g{i}" for i in range(1, 20)] + [f"b_{b}" for b in BLOQUES])
KX = {k: i for i, k in enumerate(K)}


# ── 1. clasificación ─────────────────────────────────────────────────────────
def lista_aps():
    L = pl.read_csv(CONFIG / "lista_aps_icsap2008.csv")
    f = clasificador([(r["grupo"], r["cie10"], "") for r in L.iter_rows(named=True)])
    return L, f


def clasificar(codigos):
    L, f = lista_aps()
    bloque = dict(zip(L["grupo"], L["bloque"]))
    LO, fo = m54.lista()
    W = {r["id"]: (r["prevenible"], r["tratable"], r["sexo"]) for r in LO.iter_rows(named=True)}
    filas = []
    for cb in codigos:
        cb = cb or ""
        ok = len(cb) >= 3 and cb[0].isalpha()
        g = (f(cb) or 0) if ok else 0
        fid = fo(cb) if ok else None
        p, t, sx = W.get(fid, (0.0, 0.0, None))
        filas.append((cb, int(g), bloque.get(g, "ninguno"), int(ok and cb[0] == "R"),
                      int(ok and ("V01" <= cb[:3] <= "Y98")), int(g > 0 and cb[:3] in INESP),
                      int(ok and g == 0 and "J12" <= cb[:3] <= "J18"),
                      int(ok and g == 0 and (cb[:3] in ("I12", "I13", "I15") or (cb[:3] == "N39" and cb[:4] != "N390"))),
                      float(p), float(t), int(sx == "F")))
    return pl.DataFrame(filas, schema=["cb", "grupo", "bloque", "maldef", "externa", "inesp", "neum", "adres", "prev", "trat", "solo_mujer"], orient="row")


# ── 2. conteos ───────────────────────────────────────────────────────────────
CLAVES = ["anio", "d", "sexo", "grupo", "maldef", "externa", "inesp", "neum", "adres"]
MED = ["n", "t", "t2"]


def contar():
    base = procesado() / "defunciones_eevv.parquet"
    codigos = sorted(pl.scan_parquet(base).filter(pl.col("anio") >= ANIOS[0]).select("cb").unique().collect()["cb"].drop_nulls().to_list())
    cls = clasificar(codigos)
    partes = []
    for a in ANIOS:
        d = (pl.scan_parquet(base).filter((pl.col("anio") == a) & (pl.col("dp").is_null() | (pl.col("dp") != 75)))
             .select(["dp", "sexo", "g", "cb"]).collect())
        d = d.with_columns(pl.col("cb").fill_null("")).join(cls, on="cb", how="left").with_columns(
            [pl.col(c).fill_null(0) for c in ("grupo", "maldef", "externa", "inesp", "neum", "adres", "solo_mujer")]
            + [pl.col("trat").fill_null(0.0)])
        d = d.with_columns(pl.when((pl.col("solo_mujer") == 1) & (pl.col("sexo") != 2)).then(0.0).otherwise(pl.col("trat")).alias("trat"),
                           pl.col("dp").replace_strict(DIX, default=ND).fill_null(ND).alias("d"),
                           pl.min_horizontal(pl.col("g"), G - 1).alias("g"),
                           pl.when(pl.col("sexo").is_in([1, 2])).then(pl.col("sexo")).otherwise(3).alias("sexo"))
        agg = d.group_by(["d", "sexo", "g", "grupo", "maldef", "externa", "inesp", "neum", "adres"]).agg(
            pl.len().cast(pl.Float64).alias("n"), pl.col("trat").sum().alias("t"), (pl.col("trat") ** 2).sum().alias("t2"))
        partes.append(agg.with_columns(pl.lit(a).alias("anio")))
        print(f"  {a}: {d.height:>7} defunciones", flush=True)
    return pl.concat(partes), cls


def repartir_edad(C):
    """Reparte la edad desconocida (g = -1) con la distribución de edades conocidas de la misma celda;
    si la celda no tiene edades conocidas, con niveles cada vez más gruesos. No se pierde ninguna muerte."""
    niveles = [CLAVES, ["anio", "sexo", "grupo", "maldef", "externa", "inesp", "neum", "adres"], ["anio", "sexo"], ["anio"]]
    con, des = C.filter(pl.col("g") >= 0), C.filter(pl.col("g") < 0).drop("g")
    rep = []
    for k in niveles:
        if des.height == 0:
            break
        x = con.group_by(k + ["g"]).agg(pl.col("n").sum().alias("ng"))
        x = x.join(x.group_by(k).agg(pl.col("ng").sum().alias("N")), on=k).with_columns((pl.col("ng") / pl.col("N")).alias("w")).select(k + ["g", "w"])
        hit = des.join(x, on=k, how="inner")
        rep.append(hit.with_columns([(pl.col(m) * pl.col("w")).alias(m) for m in MED]).drop("w").select(C.columns))
        des = des.join(x.select(k).unique(), on=k, how="anti")
    total_des = float(C.filter(pl.col("g") < 0)["n"].sum())
    assert des.height == 0 and abs(sum(float(r_["n"].sum()) for r_ in rep) - total_des) < 1e-6
    out = (pl.concat([con] + rep).sort(CLAVES + ["g", "n"]).group_by(CLAVES + ["g"], maintain_order=True)
           .agg([pl.col(m).sum() for m in MED]).sort(CLAVES + ["g"]))
    return out, total_des


def arreglo(C, cls_bloque):
    """D[a, d(34), s(3: H, M, indet.), g(19), k]."""
    D = np.zeros((NA, ND + 1, 3, G, len(K)))
    C = C.with_columns((pl.col("anio") - ANIOS[0]).alias("a"), (pl.col("sexo") - 1).alias("s"))
    idx = lambda df: tuple(df[c].to_numpy().astype(int) for c in ("a", "d", "s", "g"))

    def poner(k, df, col="n"):
        if df.height:
            np.add.at(D[..., KX[k]], idx(df), df[col].to_numpy())
    poner("todas", C)
    poner("maldef", C.filter(pl.col("maldef") == 1))
    poner("externas", C.filter(pl.col("externa") == 1))
    poner("trat", C, "t"); poner("trat2", C, "t2")
    poner("neum_extra", C.filter(pl.col("neum") == 1))
    poner("adres_extra", C.filter(pl.col("adres") == 1))
    cs = C.filter(pl.col("grupo") > 0)
    poner("csaa", cs)
    poner("csaa_inesp", cs.filter(pl.col("inesp") == 1))
    for gi in range(1, 20):
        poner(f"g{gi}", cs.filter(pl.col("grupo") == gi))
    for b in BLOQUES:
        poner(f"b_{b}", cs.filter(pl.col("grupo").is_in([g for g, bb in cls_bloque.items() if bb == b])))
    return D


# ── 3. estimadores ───────────────────────────────────────────────────────────
def gamma_ic(y, v, wm, alfa=.05):
    """Intervalo gamma de Fay y Feuer (1997) para una suma ponderada de conteos Poisson con media y,
    varianza v y peso máximo wm."""
    from scipy.stats import chi2
    y, v, wm = np.asarray(y, float), np.asarray(v, float), np.asarray(wm, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        lo = np.where(y > 0, v / (2 * y) * chi2.ppf(alfa / 2, 2 * y ** 2 / np.where(v > 0, v, 1)), 0.0)
        hi = (v + wm ** 2) / (2 * (y + wm)) * chi2.ppf(1 - alfa / 2, 2 * (y + wm) ** 2 / (v + wm ** 2))
    return np.nan_to_num(lo), hi


def tasa_est(D, N, w, V=None, peso=None, mult=1e5):
    """Tasa directamente estandarizada (0–74 en 15 grupos) con IC gamma. D, N: [..., 15]."""
    pm = np.ones(D.shape[-1]) if peso is None else peso
    V = D if V is None else V
    c = np.divide(w * pm, N, out=np.zeros(np.broadcast(D, N).shape), where=N > 0)
    y = (c * D).sum(-1); v = (c ** 2 * V).sum(-1); wm = c.max(-1)
    lo, hi = gamma_ic(y, v, wm)
    return y * mult, lo * mult, hi * mult


def p65(D, Dk, N, sexo):
    """Probabilidad de sobrevivir de 0 a 65 con todas las causas y sin las causas Dk (decremento
    eliminado de Chiang: p_x^(-k) = p_x^((D-Dk)/D)). D, Dk, N: [..., G]."""
    D = np.asarray(D, float); Dk = np.asarray(Dk, float)
    t = T.tabla(D, N, sexo)
    p = 1 - t["q"][..., :I65]
    R = np.divide(D - Dk, D, out=np.ones_like(D), where=D > 0)[..., :I65]
    return np.prod(p, -1), np.prod(p ** R, -1)


def r(x, k=1):
    if x is None:
        return None
    x = float(x)
    return None if not np.isfinite(x) else round(x, k)


# ── 4. completitud implícita del DANE (sensibilidad) ─────────────────────────
BANDA_G = np.array([0, 1] + [2] * 8 + [3] * 4 + [4] * 2 + [5] * 3)   # <1, 1-4, 5-44, 45-64, 65-74, 75+


def leer_mx():
    """Tasas de mortalidad por edad simple, sexo y departamento estimadas por el DANE, 1985–2017 (base CNPV 2018);
    mismo lector que scripts/35_completitud_cnpv2018.py del repositorio EEVV."""
    from python_calamine import CalamineWorkbook
    from eevv_insumos import rutas as ru
    filas = []
    r_ = CalamineWorkbook.from_path(str(ru.crudo() / "poblacion" / "dane_mor" / "DCD-Mor-EstSexNal-Dep-1985-2017_VP.xlsx")).get_sheet_by_name("Mx").to_python()
    cab = r_[6]; edades = [int(float(x)) for x in cab[5:]]
    for x in r_[7:]:
        if x[0] == "" or x[3] != "TOTAL":
            continue
        dp = 0 if x[1] == "00" else int(x[1])
        for e, m in zip(edades, x[5:]):
            filas.append((int(x[0]), dp, 1 if x[4] == "Hombres" else 2, e, float(m)))
    return pl.DataFrame(filas, schema=["anio", "dp", "sexo", "edad", "mx"], orient="row")


def esperadas_dane():
    """Nivel B. Defunciones esperadas con las tasas del DANE, 2015–2017, por departamento, sexo y grupo de edad."""
    mx = leer_mx().filter(pl.col("anio").is_between(2015, 2017) & (pl.col("dp") > 0))
    pob = (pl.read_parquet(procesado() / "poblacion_eevv.parquet").group_by(["anio", "dp", "sexo", "edad"]).agg(pl.col("pob").sum())
           .with_columns([pl.col(c).cast(pl.Int64) for c in ("anio", "dp", "sexo", "edad")]))
    e = pl.col("edad")
    gexpr = pl.when(e == 0).then(0).when(e < 5).then(1).otherwise(pl.min_horizontal(e // 5 + 1, G - 1))
    esp = (mx.join(pob, on=["anio", "dp", "sexo", "edad"]).with_columns(gexpr.alias("g"), (pl.col("mx") * pl.col("pob")).alias("esp"))
           .filter(pl.col("dp").is_in(CODS)).sort(["dp", "sexo", "g", "anio", "edad"]))
    E = np.zeros((ND, 2, G))
    np.add.at(E, (np.array([DIX[d] for d in esp["dp"].to_list()]), esp["sexo"].to_numpy() - 1, esp["g"].to_numpy()), esp["esp"].to_numpy())
    return pl.DataFrame([dict(cod_dpto=CODS[i], sexo=s_ + 1, g=g, esperadas=float(E[i, s_, g])) for i in range(ND) for s_ in range(2) for g in range(G)])


def completitud():
    """Nivel A: [33, 2, G] de data/intermedios/esperadas_dane_2015_2017.parquet."""
    x = pl.read_parquet(INTERMEDIOS / "esperadas_dane_2015_2017.parquet")
    E = np.zeros((ND, 2, G))
    for c, s_, g, v in x.select(["cod_dpto", "sexo", "g", "esperadas"]).iter_rows():
        E[DIX[c], s_ - 1, g] = v
    return E


def poblacion_b():
    """Nivel B. Población por año, departamento, sexo y grupo de edad (1998–2025), como poblacion() del estudio 54."""
    pob = pl.read_parquet(procesado() / "poblacion_eevv.parquet").filter(pl.col("anio").is_between(ANIOS[0], ANIOS[-1]) & (pl.col("dp") > 0))
    e = pob["edad"].to_numpy()
    pob = pob.with_columns(pl.Series("g", np.minimum(np.where(e == 0, 0, np.where(e < 5, 1, e // 5 + 1)), G - 1)))
    return (pob.group_by(["anio", "dp", "sexo", "g"]).agg(pl.col("pob").sum()).sort(["anio", "dp", "sexo", "g"])
            .rename({"dp": "cod_dpto"}).with_columns([pl.col(c).cast(pl.Int16) for c in ("anio", "cod_dpto", "sexo", "g")]))


def poblacion():
    """Nivel A: [a, 33, 2, G]."""
    x = pl.read_parquet(INTERMEDIOS / "poblacion.parquet")
    P = np.zeros((NA, ND, 2, G))
    np.add.at(P, ((x["anio"].to_numpy() - ANIOS[0]).astype(int), np.array([DIX[int(c)] for c in x["cod_dpto"].to_list()]),
                  x["sexo"].to_numpy().astype(int) - 1, x["g"].to_numpy().astype(int)), x["pob"].to_numpy())
    return P


# ── 5. principal ─────────────────────────────────────────────────────────────
def nivel_a():
    SAL.mkdir(parents=True, exist_ok=True); PAR.mkdir(parents=True, exist_ok=True)
    (SAL / "tablas").mkdir(exist_ok=True)
    L, _ = lista_aps()
    cls_bloque = dict(zip(L["grupo"], L["bloque"]))
    C = pl.read_parquet(INTERMEDIOS / "conteos.parquet")
    n_reg = float(C["n"].sum())
    C, n_sin_edad = repartir_edad(C)
    assert abs(float(C["n"].sum()) - n_reg) < 1e-6
    D = arreglo(C, cls_bloque)
    P = poblacion()                                               # [a, d(33), s(2), g]
    w = m54.pesos_ocde2015()                                      # 15 pesos 0–74, por la población estándar total
    w70 = w[:14]
    gbd = yaml.safe_load((CONFIG / "tabla_vida_referencia.yaml").read_text(encoding="utf-8"))["tabla_referencia_gbd"]
    ge = np.array(sorted(float(k) for k in gbd)); gv = np.array([gbd[k] for k in sorted(gbd, key=float)], float)
    yll = np.interp(np.array([0.1, 2.5] + [x + 2.5 for x in range(5, 75, 5)]), ge, gv)    # 16 grupos < 75
    a15 = m54.a15

    # territorios: 0..32 departamentos, 33 = nacional (incluye departamento desconocido en las muertes)
    Dn = np.concatenate([D[:, :ND], D.sum(1, keepdims=True)], axis=1)            # [a, 34, s3, g, k]
    Pn = np.concatenate([P, P.sum(1, keepdims=True)], axis=1)                     # [a, 34, s2, g]
    TER = [(c, DEP[c]) for c in CODS] + [(0, "Colombia")]
    NT = len(TER)
    SXS = {"total": ([0, 1, 2], [0, 1], "t"), "hombres": ([0], [0], "h"), "mujeres": ([1], [1], "m")}

    def dsel(k, sx):                       # [a, t, g]
        return Dn[..., KX[k]][:, :, SXS[sx][0]].sum(2)

    def psel(sx):
        return Pn[:, :, SXS[sx][1]].sum(2)

    # AVPP por grupo de 15 (0-4 junto): el AVPP de 0-4 es el ponderado por las muertes de 0 y 1-4
    def avpp15(Dg):                         # Dg [..., G] -> AVPP por muerte en 15 grupos
        d0, d1 = Dg[..., 0], Dg[..., 1]
        y0 = np.divide(d0 * yll[0] + d1 * yll[1], d0 + d1, out=np.full(d0.shape, yll[1]), where=(d0 + d1) > 0)
        return np.concatenate([y0[..., None], np.broadcast_to(yll[2:Q75], Dg.shape[:-1] + (Q75 - 2,))], -1)

    res = {}
    # ── tasas anuales y trienio por territorio y sexo ──
    def bloque_tasas(Dk, N, Vk=None, edad=Q75, ww=w):
        D15, N15 = a15(Dk)[..., :edad - 1], a15(N)[..., :edad - 1]
        V15 = None if Vk is None else a15(Vk)[..., :edad - 1]
        return tasa_est(D15, N15, ww, V15)

    series = []
    for sx in SXS:
        Nt = psel(sx)
        Dt, Dc = dsel("todas", sx), dsel("csaa", sx)
        tee_c = bloque_tasas(Dc, Nt)
        tee_t = bloque_tasas(Dt, Nt)
        tee_o = bloque_tasas(dsel("trat", sx), Nt, dsel("trat2", sx))
        tee_b = {b: bloque_tasas(dsel(f"b_{b}", sx), Nt) for b in BLOQUES}
        # AVPP
        y15 = avpp15(Dc[..., :Q75])
        Dc15 = a15(Dc)
        avpp = (Dc15 * y15).sum(-1)
        av_lo, av_hi = gamma_ic(avpp, (Dc15 * y15 ** 2).sum(-1), y15.max(-1))
        av_tee = tasa_est(Dc15, a15(Nt), w, peso=y15)
        mald = dsel("maldef", sx)[..., :Q75].sum(-1); m75 = Dt[..., :Q75].sum(-1)
        for ai, a in enumerate(ANIOS):
            for ti, (c, nom) in enumerate(TER):
                series.append(dict(
                    anio=a, cod=c, territorio=nom, sexo=sx,
                    def_todas=Dt[ai, ti].sum(), def_menores75=m75[ai, ti], def_csaa75=Dc[ai, ti, :Q75].sum(),
                    pob=Nt[ai, ti].sum(), pob_menor75=Nt[ai, ti, :Q75].sum(),
                    tee_csaa=tee_c[0][ai, ti], tee_csaa_lo=tee_c[1][ai, ti], tee_csaa_hi=tee_c[2][ai, ti],
                    tee_todas75=tee_t[0][ai, ti], tee_tratable_ocde=tee_o[0][ai, ti],
                    **{f"tee_{b}": tee_b[b][0][ai, ti] for b in BLOQUES},
                    avpp_csaa=avpp[ai, ti], avpp_csaa_lo=av_lo[ai, ti], avpp_csaa_hi=av_hi[ai, ti],
                    tee_avpp_csaa=av_tee[0][ai, ti], tee_avpp_csaa_lo=av_tee[1][ai, ti], tee_avpp_csaa_hi=av_tee[2][ai, ti],
                    pct_maldef75=100 * mald[ai, ti] / m75[ai, ti] if m75[ai, ti] > 0 else np.nan))
    S = pl.DataFrame(series)

    # ── P(65) y su ganancia sin CSAA, con IC Monte Carlo ──
    rng = np.random.default_rng(SEMILLA)
    E = completitud()
    En = np.concatenate([E, E.sum(0, keepdims=True)], 0)          # [34, s2, g]
    p65f = []; FAC = {}
    for sx, (si, pi, sexo) in SXS.items():
        Dt, Dc, Nt = dsel("todas", sx), dsel("csaa", sx), psel(sx)
        base, sin = p65(Dt, Dc, Nt, sexo)
        sims_b, sims_g = np.empty((NSIM,) + base.shape), np.empty((NSIM,) + base.shape)
        resto = np.maximum(Dt - Dc, 0)
        for k in range(NSIM):
            dc = rng.poisson(Dc); dr = rng.poisson(resto)
            b_, s_ = p65(dc + dr, dc, Nt, sexo)
            sims_b[k], sims_g[k] = b_, s_ - b_
        bl, bh = np.percentile(sims_b, [2.5, 97.5], 0)
        gl, gh = np.percentile(sims_g, [2.5, 97.5], 0)
        # corregido por la omisión implícita del DANE (2015–2017), aplicado a todos los años
        Ereg = Dt[[ANIOS.index(a) for a in (2015, 2016, 2017)]].sum(0)               # [34, g]
        Esp = En[:, pi].sum(1)
        cb_ = np.zeros((NT, 6))
        for b in range(6):
            m = BANDA_G == b
            cb_[:, b] = np.clip(np.divide(Ereg[:, m].sum(-1), Esp[:, m].sum(-1), out=np.ones(NT), where=Esp[:, m].sum(-1) > 0), 0.2, 1.0)
        fac = 1 / cb_[:, BANDA_G]                                                       # [34, g]
        FAC[sx] = fac
        tcorr = bloque_tasas(Dc * fac[None], Nt)
        bc, sc = p65(Dt * fac, Dc * fac, Nt, sexo)
        for ai, a in enumerate(ANIOS):
            for ti, (c, nom) in enumerate(TER):
                p65f.append(dict(anio=a, cod=c, sexo=sx, p65=base[ai, ti], p65_lo=bl[ai, ti], p65_hi=bh[ai, ti],
                                 p65_sin_csaa=sin[ai, ti], ganancia=sin[ai, ti] - base[ai, ti], ganancia_lo=gl[ai, ti], ganancia_hi=gh[ai, ti],
                                 p65_corr=bc[ai, ti], ganancia_corr=sc[ai, ti] - bc[ai, ti], tee_csaa_corr=tcorr[0][ai, ti]))
        if sx == "total":
            compl = {TER[ti][0]: [r(x, 3) for x in cb_[ti]] for ti in range(NT)}
    S = S.join(pl.DataFrame(p65f), on=["anio", "cod", "sexo"])

    # ── trienio 2023–2025 (mapa) ──
    ia = [ANIOS.index(a) for a in ULT]
    tri = []
    for sx in SXS:
        Nt = psel(sx)[ia].sum(0)
        Dt, Dc = dsel("todas", sx)[ia].sum(0), dsel("csaa", sx)[ia].sum(0)
        tc = bloque_tasas(Dc, Nt); tt = bloque_tasas(Dt, Nt)
        to = bloque_tasas(dsel("trat", sx)[ia].sum(0), Nt, dsel("trat2", sx)[ia].sum(0))
        tb = {b: bloque_tasas(dsel(f"b_{b}", sx)[ia].sum(0), Nt) for b in BLOQUES}
        y15 = avpp15(Dc[..., :Q75]); Dc15 = a15(Dc)
        avt = tasa_est(Dc15, a15(Nt), w, peso=y15)
        mald = dsel("maldef", sx)[ia].sum(0)[..., :Q75].sum(-1); m75 = Dt[..., :Q75].sum(-1)
        # sensibilidades
        ext = dsel("externas", sx)[ia].sum(0); md = dsel("maldef", sx)[ia].sum(0)
        nat = np.maximum(Dt - ext - md, 1e-9)
        Dc_r = Dc * (1 + md / nat)                                       # mal definidas repartidas entre naturales
        tr = bloque_tasas(Dc_r, Nt)
        ti_ = bloque_tasas(Dc - dsel("csaa_inesp", sx)[ia].sum(0), Nt)
        t70 = bloque_tasas(Dc, Nt, edad=Q70, ww=w70)
        tne = bloque_tasas(Dc + dsel("neum_extra", sx)[ia].sum(0), Nt)               # con todas las neumonías J12–J18
        tad = bloque_tasas(Dc + dsel("adres_extra", sx)[ia].sum(0), Nt)              # con la ampliación operativa de la ADRES (2026)
        tco = bloque_tasas(Dc * FAC[sx], Nt)
        bc3, sc3 = p65(Dt * FAC[sx] / 3, Dc * FAC[sx] / 3, Nt / 3, SXS[sx][2])
        b3, s3 = p65(Dt / 3, Dc / 3, Nt / 3, SXS[sx][2])
        for ti, (c, nom) in enumerate(TER):
            tri.append(dict(cod=c, territorio=nom, sexo=sx, def_csaa75=Dc[ti, :Q75].sum(), def_menores75=m75[ti],
                            tee_csaa=tc[0][ti], tee_csaa_lo=tc[1][ti], tee_csaa_hi=tc[2][ti], tee_todas75=tt[0][ti],
                            tee_tratable_ocde=to[0][ti], **{f"tee_{b}": tb[b][0][ti] for b in BLOQUES},
                            tee_avpp_csaa=avt[0][ti], tee_avpp_csaa_lo=avt[1][ti], tee_avpp_csaa_hi=avt[2][ti],
                            avpp_csaa=(Dc15[ti] * y15[ti]).sum(), pct_maldef75=100 * mald[ti] / m75[ti],
                            tee_sens_maldef=tr[0][ti], tee_sens_sin_inesp=ti_[0][ti], tee_sens_70=t70[0][ti], tee_sens_neumonias=tne[0][ti], tee_sens_adres=tad[0][ti], tee_csaa_corr=tco[0][ti],
                            p65_corr=bc3[ti], ganancia_corr=sc3[ti] - bc3[ti],
                            p65=b3[ti], p65_sin_csaa=s3[ti], ganancia=s3[ti] - b3[ti]))
    TR = pl.DataFrame(tri)
    # IC de la ganancia del trienio con Monte Carlo
    extras = []
    for sx in SXS:
        Nt = psel(sx)[ia].sum(0); Dt, Dc = dsel("todas", sx)[ia].sum(0), dsel("csaa", sx)[ia].sum(0)
        g_s = np.empty((NSIM, NT)); b_s = np.empty((NSIM, NT))
        for k in range(NSIM):
            dc = rng.poisson(Dc); dr = rng.poisson(np.maximum(Dt - Dc, 0))
            b_, s_ = p65((dc + dr) / 3, dc / 3, Nt / 3, SXS[sx][2]); g_s[k] = s_ - b_; b_s[k] = b_
        gl, gh = np.percentile(g_s, [2.5, 97.5], 0); bl, bh = np.percentile(b_s, [2.5, 97.5], 0)
        extras.append(pl.DataFrame({"cod": [c for c, _ in TER], "sexo": [sx] * NT, "ganancia_lo": gl, "ganancia_hi": gh, "p65_lo": bl, "p65_hi": bh}))
    TR = TR.join(pl.concat(extras), on=["cod", "sexo"], how="left")

    # ── grupos CSAA: nacional, trienio, menores de 75 ──
    grupos = []
    Nt = psel("total")[ia].sum(0)[-1]
    for gi in range(1, 20):
        Dg = dsel(f"g{gi}", "total")[ia].sum(0)[-1]
        t_ = bloque_tasas(Dg[None], Nt[None])
        y15 = avpp15(Dg[None, :Q75])
        fila = L.filter(pl.col("grupo") == gi).row(0, named=True)
        grupos.append(dict(grupo=gi, nombre=fila["nombre"], bloque=fila["bloque"], def_trienio=r(Dg[:Q75].sum(), 0),
                           def_anual=r(Dg[:Q75].sum() / 3, 0), tee=r(t_[0][0], 2), ic=[r(t_[1][0], 2), r(t_[2][0], 2)],
                           avpp_anual=r((a15(Dg[None])[0] * y15[0]).sum() / 3, 0)))
    grupos.sort(key=lambda x: -x["def_trienio"])

    # ── hospitalizaciones evitables (ADRES, 2026) frente a las muertes por las mismas condiciones ──
    hosp = hospitalizaciones(dsel, psel, bloque_tasas, TER, L)

    # ── cruces con las listas 6/67 y 105 y con la OCDE/Eurostat: vienen del nivel B ──
    for f in ("cruce_lista_667.csv", "cruce_lista_105.csv", "codigos_csaa.csv"):
        pl.read_csv(INTERMEDIOS / f).write_csv(SAL / "tablas" / f)
    solap_res = json.loads((INTERMEDIOS / "solapamiento_ocde.json").read_text(encoding="utf-8"))

    # ── archivo de parámetros ──
    parametros(D, P, Dn, Pn, TER, cls_bloque, compl)

    # ── resultados para el tablero ──
    S, TR = S.sort(["sexo", "cod", "anio"]), TR.sort(["sexo", "cod"])
    S.write_csv(SAL / "tablas" / "serie_territorial.csv"); TR.write_csv(SAL / "tablas" / "trienio_2023_2025.csv")
    def fila(d):
        return {k: (r(v, 5) if k.startswith("p65") or k.startswith("ganancia") else r(v, 2) if isinstance(v, float) else v) for k, v in d.items()}
    nac = S.filter((pl.col("cod") == 0)).sort(["sexo", "anio"])
    out = dict(
        version=VERSION,
        fuente="DANE, EEVV defunciones no fetales 1998–2025 y proyecciones de población; Lista brasileña de condiciones sensibles a la atención primaria (Portaria SAS/MS 221 de 2008)",
        lista=dict(archivo="config/lista_aps_icsap2008.csv", grupos=19, edad_max=74, bloques=BLOQUE_NOMBRE),
        estandar="OCDE 2015 (38 países, WPP 2024), por 100.000 de la población estándar total; edades 0 a 74",
        n_registros=r(n_reg, 0), n_sin_edad_repartidos=r(n_sin_edad, 0),
        solapamiento_ocde=solap_res,
        grupos_trienio=grupos,
        nacional=[fila(x) for x in nac.iter_rows(named=True)],
        departamentos_anual=[fila(x) for x in S.filter((pl.col("cod") > 0) & (pl.col("sexo") == "total")).sort(["cod", "anio"]).iter_rows(named=True)],
        trienio=[fila(x) for x in TR.sort(["sexo", "cod"]).iter_rows(named=True)],
        completitud_dane_2015_2017=dict(bandas=["<1", "1-4", "5-44", "45-64", "65-74", "75+"], por_territorio=compl),
    )
    (SAL / "resultados.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    tablero(S, TR, grupos, solap_res, L, hosp)
    t = TR.filter((pl.col("cod") == 0) & (pl.col("sexo") == "total")).row(0, named=True)
    print(f"Colombia 2023–2025: {t['def_csaa75']/3:,.0f} muertes CSAA <75 al año · TEE {t['tee_csaa']:.1f} ({t['tee_csaa_lo']:.1f}–{t['tee_csaa_hi']:.1f})"
          f" · P(65) {t['p65']:.4f} → {t['p65_sin_csaa']:.4f}")


# ── 5b. hospitalizaciones evitables de la ADRES ─────────────────────────────
EXT = ADRES


def hospitalizaciones(dsel, psel, bloque_tasas, TER, L):
    """Cruza las hospitalizaciones evitables por condiciones sensibles a la atención primaria (HECSAP) que publicó la
    ADRES (julio de 2026; FEV-RIPS 2025, cuadros 2 y 5; RIPS 2019–2024, figura 6) con las muertes por las mismas
    condiciones. La ADRES usa la lista de Alfradique et al. (2009) en 20 grupos, que tiene los mismos códigos que los
    19 de la Portaria 221 (el grupo 1 se parte en dos), con diagnóstico principal de egreso, todas las edades, tasas
    crudas por 10.000 con la misma población del DANE 2025 que usa este estudio.

    Lo que se calcula (2025, todas las edades, sexos juntos, la misma lista):
      · muertes por CSAA por cada 1.000 hospitalizaciones HECSAP: cuántas muertes hay por cada hospitalización que
        el sistema alcanzó a hacer. Alta = se muere más de lo que se hospitaliza (barrera de acceso, llegada tardía o
        muerte fuera del hospital); baja = el sistema hospitaliza mucho para las muertes que hay;
      · la tasa cruda de mortalidad por CSAA (por 100.000) y la estandarizada <75 de 2025 y 2023–2025;
      · por condición: hospitalizaciones, costo y muertes de 2025.
    Las dos fuentes no cubren lo mismo: FEV-RIPS es el régimen contributivo y el subsidiado; el registro de defunciones,
    a todos."""
    a25 = ANIOS.index(2025); ia = [ANIOS.index(a) for a in ULT]
    dep = pl.read_csv(EXT / "adres_hecsap_2025_departamentos.csv")
    con = pl.read_csv(EXT / "adres_hecsap_2025_condiciones.csv")
    ser = pl.read_csv(EXT / "adres_hecsap_serie_nacional.csv")
    Dc = dsel("csaa", "total"); Nt = psel("total")
    t25 = bloque_tasas(Dc[a25], Nt[a25]); t3 = bloque_tasas(Dc[ia].sum(0), Nt[ia].sum(0))
    h = {int(r_["cod_dpto"]): r_ for r_ in dep.iter_rows(named=True)}
    filas = []
    tot_h = int(con["hospitalizaciones"].sum())
    for ti, (c, nom) in enumerate(TER):
        x = h.get(c)
        hh = tot_h if c == 0 else (x["hosp_hecsap"] if x else None)
        th = 141.0 if c == 0 else (x["tasa_hecsap_10k"] if x else None)
        gasto = 8359.7 if c == 0 else (x["gasto_hecsap_mm"] if x else None)
        m = float(Dc[a25, ti].sum())
        filas.append(dict(cod=c, territorio=nom, hosp_hecsap=hh, tasa_hosp_10k=th, gasto_mm=gasto, muertes_csaa=round(m, 1),
                          muertes_csaa75=round(float(Dc[a25, ti, :Q75].sum()), 1),
                          tasa_cruda_mort_100k=round(1e5 * m / float(Nt[a25, ti].sum()), 2),
                          tee_2025=round(float(t25[0][ti]), 2), tee_2025_lo=round(float(t25[1][ti]), 2), tee_2025_hi=round(float(t25[2][ti]), 2),
                          tee_2023_2025=round(float(t3[0][ti]), 2),
                          muertes_por_mil_hosp=round(1e3 * m / hh, 1) if hh else None))
    H = pl.DataFrame(filas)
    # ── razones estandarizadas indirectas (2025): hospitalización (REH) y mortalidad (RME) ──
    # La ADRES no publica hospitalizaciones por edad y departamento; sí la distribución por edad de los pacientes
    # HECSAP del país (cuadro 4). Con ella se arman tasas nacionales por banda de edad, y las hospitalizaciones esperadas
    # de cada departamento son esas tasas por su población. Así la comparación entre departamentos no depende de cuán
    # viejos son. La mortalidad se estandariza igual, con las tasas nacionales de 2025 en los 19 grupos de edad.
    eb = pl.read_csv(EXT / "adres_hecsap_2025_edad.csv")
    pob = pl.read_parquet(INTERMEDIOS / "poblacion_2025_edad_simple.parquet").sort(["dp", "edad"])
    banda = np.zeros(len(pob), int)
    for bi, r_ in enumerate(eb.iter_rows(named=True)):
        banda[(pob["edad"].to_numpy() >= r_["edad_min"]) & (pob["edad"].to_numpy() <= r_["edad_max"])] = bi
    PB = np.zeros((ND, len(eb)))
    np.add.at(PB, (np.array([DIX[int(x)] for x in pob["dp"].to_list()]), banda), pob["pob"].to_numpy())
    hb = eb["pct_pacientes_hecsap"].to_numpy() / eb["pct_pacientes_hecsap"].sum() * tot_h
    tasa_b = hb / PB.sum(0)
    esp_h = PB @ tasa_b
    m_nac = np.divide(Dc[a25, -1], Nt[a25, -1], out=np.zeros(G), where=Nt[a25, -1] > 0)
    esp_m = Nt[a25, :ND] @ m_nac
    reh, rme = [], []
    for ti, (c, nom) in enumerate(TER):
        if c == 0:
            reh.append(1.0); rme.append(1.0); continue
        x = h.get(c)
        reh.append(x["hosp_hecsap"] / esp_h[ti] if x else None)
        rme.append(float(Dc[a25, ti].sum()) / esp_m[ti])
    H = H.with_columns(pl.Series("reh", [None if v is None else round(v, 3) for v in reh]), pl.Series("rme", [round(v, 3) for v in rme]))
    H = H.with_columns((pl.col("rme") / pl.col("reh")).round(3).alias("rme_sobre_reh"))
    # IC 95 % del cociente con la aproximación logarítmica: var(ln RME/REH) = 1/muertes + 1/hospitalizaciones
    se = (1 / pl.col("muertes_csaa") + 1 / pl.col("hosp_hecsap")).sqrt()
    H = H.with_columns((pl.col("rme_sobre_reh") * (-1.959964 * se).exp()).round(3).alias("rme_sobre_reh_lo"),
                       (pl.col("rme_sobre_reh") * (1.959964 * se).exp()).round(3).alias("rme_sobre_reh_hi"))
    H.write_csv(SAL / "tablas" / "hospitalizaciones_vs_muertes_2025.csv")
    d = H.filter(pl.col("cod") > 0)
    rho = {"tasa_hosp_vs_tee_2023_2025": round(float(d.select(pl.corr("tasa_hosp_10k", "tee_2023_2025", method="spearman")).item()), 3),
           "reh_vs_rme_2025": round(float(d.select(pl.corr("reh", "rme", method="spearman")).item()), 3),
           "reh_vs_tasa_cruda_hosp": round(float(d.select(pl.corr("reh", "tasa_hosp_10k", method="spearman")).item()), 3),
           "tasa_hosp_vs_mort_cruda_2025": round(float(d.select(pl.corr("tasa_hosp_10k", "tasa_cruda_mort_100k", method="spearman")).item()), 3)}
    # por condición: los 20 grupos de la ADRES llevados a los 19 de la Portaria
    cg = con.group_by("grupo_csaa").agg(pl.col("hospitalizaciones").sum(), pl.col("costo_total_cop").sum(), pl.col("pacientes").sum()).sort("grupo_csaa")
    porg = []
    for r_ in cg.iter_rows(named=True):
        gi = r_["grupo_csaa"]
        m = float(dsel(f"g{gi}", "total")[a25, -1].sum())
        f = L.filter(pl.col("grupo") == gi).row(0, named=True)
        porg.append(dict(grupo=gi, nombre=f["nombre"], bloque=f["bloque"], hospitalizaciones=r_["hospitalizaciones"], pacientes=r_["pacientes"],
                         costo_mm=round(r_["costo_total_cop"] / 1e9, 1), costo_por_hosp_millones=round(r_["costo_total_cop"] / r_["hospitalizaciones"] / 1e6, 2),
                         muertes_2025=round(m, 0), muertes_por_mil_hosp=round(1e3 * m / r_["hospitalizaciones"], 1)))
    pl.DataFrame(porg).write_csv(SAL / "tablas" / "hospitalizaciones_vs_muertes_por_condicion_2025.csv")
    PAR.mkdir(parents=True, exist_ok=True)
    (pl.DataFrame(porg).select(["grupo", "nombre", "bloque", "hospitalizaciones", "pacientes", "costo_mm", "costo_por_hosp_millones", "muertes_2025"])
     .rename({"nombre": "condicion", "costo_mm": "costo_total_mm_cop", "costo_por_hosp_millones": "costo_por_hospitalizacion_millones_cop"})
     .write_csv(PAR / "hospitalizaciones_evitables_costo_2025.csv"))
    # serie nacional: hospitalizaciones (ADRES) y muertes (este estudio)
    serie = []
    for r_ in ser.iter_rows(named=True):
        ai = ANIOS.index(r_["anio"])
        tt = bloque_tasas(Dc[ai, -1][None], Nt[ai, -1][None])
        serie.append(dict(anio=r_["anio"], tasa_hosp_10k=r_["tasa_hecsap_10k"], fuente_hosp=r_["fuente"], tee=round(float(tt[0][0]), 2),
                          tee_lo=round(float(tt[1][0]), 2), tee_hi=round(float(tt[2][0]), 2),
                          tasa_cruda_mort_100k=round(1e5 * float(Dc[ai, -1].sum()) / float(Nt[ai, -1].sum()), 2)))
    return dict(fuente="ADRES (2026). Hospitalizaciones evitables por condiciones sensibles a la Atención Primaria (HECSAP) en Colombia. Innovación y Analítica, julio de 2026; FEV-RIPS 2025 y RIPS 2019–2024",
                url="https://consultorsalud.com/wp-content/uploads/2026/07/Hospitalizaciones_evitables_por_condiciones_sensibles_a_la_Atencion_Primaria.pdf",
                departamentos=H.to_dicts(), por_condicion=porg, serie=serie, spearman=rho,
                nacional=dict(hosp=tot_h, tasa_10k=141.0, gasto_billones=8.36, pct_hosp=19.5, pct_gasto=20.2))


# ── 6. lo que viaja al tablero ───────────────────────────────────────────────
CAMPOS = ["tee_csaa", "tee_csaa_lo", "tee_csaa_hi", "tee_avpp_csaa", "tee_avpp_csaa_lo", "tee_avpp_csaa_hi",
          "ganancia", "ganancia_lo", "ganancia_hi", "def_csaa75", "pct_maldef75", "tee_csaa_corr", "ganancia_corr",
          "p65", "p65_sin_csaa", "p65_corr", "avpp_csaa", "tee_tratable_ocde"] + [f"tee_{b}" for b in BLOQUES]


def tablero(S, TR, grupos, solap, L, hosp):
    """output/tablas/aps_tablero.json: compacto, una lista de valores por territorio (CAMPOS en orden)."""
    def val(x, c):
        v = x.get(c)
        if v is None or not np.isfinite(v):
            return None
        return round(float(v), 5 if c.startswith(("p65", "ganancia")) else 0 if c in ("def_csaa75", "avpp_csaa") else 2)
    serie = {sx: {} for sx in ("total", "hombres", "mujeres")}
    for x in S.sort(["sexo", "cod", "anio"]).iter_rows(named=True):
        serie[x["sexo"]].setdefault(str(x["cod"]), []).append([x["anio"]] + [val(x, c) for c in CAMPOS])
    tri = {sx: {} for sx in serie}
    for x in TR.iter_rows(named=True):
        tri[x["sexo"]][str(x["cod"])] = [val(x, c) for c in CAMPOS] + [val(x, "tee_sens_maldef"), val(x, "tee_sens_sin_inesp"), val(x, "tee_sens_70"), val(x, "tee_sens_neumonias"), val(x, "tee_sens_adres")]
    d = TR.filter((pl.col("sexo") == "total") & (pl.col("cod") > 0))
    rho = {c: round(float(d.select(pl.corr("tee_csaa", c, method="spearman")).item()), 3)
           for c in ("tee_sens_maldef", "tee_sens_sin_inesp", "tee_sens_70", "tee_sens_neumonias", "tee_sens_adres", "tee_csaa_corr", "tee_tratable_ocde")}
    out = dict(version=VERSION, campos=CAMPOS, campos_trienio=CAMPOS + ["tee_sens_maldef", "tee_sens_sin_inesp", "tee_sens_70", "tee_sens_neumonias", "tee_sens_adres"],
               periodo=f"{ULT[0]}–{ULT[-1]}", anios=[ANIOS[0], ANIOS[-1]], bloques=BLOQUES, bloque_nombre=BLOQUE_NOMBRE,
               serie=serie, trienio=tri, grupos=grupos, solapamiento_ocde=solap, spearman=rho,
               lista=[dict(grupo=r_["grupo"], nombre=r_["nombre"], cie10=r_["cie10"], bloque=r_["bloque"]) for r_ in L.iter_rows(named=True)],
               hospitalizaciones=hosp)
    (SAL / "aps_tablero.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


# ── 7. parámetros ────────────────────────────────────────────────────────────
GRUPOS_PAR = ["todas"] + [f"b_{b}" for b in BLOQUES] + ["no_csaa"]
NOM_PAR = {"todas": "todas", **{f"b_{b}": f"csaa_{b}" for b in BLOQUES}, "no_csaa": "no_csaa"}


A_PRIOR = 5.0           # peso de la composición nacional en la fracción por causa, en defunciones


def parametros(D, P, Dn, Pn, TER, cls_bloque, compl):
    """Esquema fijo: una fila por año, territorio, sexo, grupo de edad y grupo de causa.

    Lo que sirve a un modelo de población es la FRACCIÓN de las muertes de cada celda que es de cada grupo de causa,
    no el nivel de la tasa registrada: el registro omite muertes (más en unos departamentos, edades y años que en
    otros) y las tablas de vida armadas con él dan esperanzas de vida imposibles donde el registro es grave. El nivel
    debe venir de las tablas de vida oficiales del DANE, que corrigen la omisión; la fracción supone que la omisión no
    depende de la causa. La fracción se suaviza hacia la composición nacional de la misma celda (año, sexo, edad) con
    un peso de A_PRIOR defunciones, para que las celdas con pocas muertes no salten entre 0 y 1."""
    Dk = np.stack([Dn[:, :, :2, :, KX["todas"]] - Dn[:, :, :2, :, KX["csaa"]] if gc == "no_csaa" else Dn[:, :, :2, :, KX[gc]]
                   for gc in GRUPOS_PAR], -1)                                                  # [a, t, s, g, grupo]
    Nk = np.broadcast_to(Pn[..., None], Dk.shape)
    Dt = Dk[..., :1]
    fnac = np.divide(Dk[:, -1:], Dt[:, -1:], out=np.zeros_like(Dk[:, -1:]), where=Dt[:, -1:] > 0)          # composición nacional
    fnac[..., 0] = 1.0
    frac = (Dk + A_PRIOR * fnac) / (Dt + A_PRIOR)
    frac[:, -1] = np.where(Dt[:, -1] > 0, Dk[:, -1] / np.where(Dt[:, -1] > 0, Dt[:, -1], 1), fnac[:, 0])  # Colombia: observada
    clase = dict(pl.read_csv(CONFIG / "completitud_territorial.csv").select(["departamento", "clase"]).iter_rows())
    reg = np.array(["nacional" if c == 0 else clase.get(n, "sin_dato") for c, n in TER], dtype=object)
    with np.errstate(divide="ignore", invalid="ignore"):
        mx = np.where(Nk > 0, Dk / Nk, np.nan)
        lo, hi = gamma_ic(mx, Dk / Nk ** 2, 1 / Nk)
    ii = np.indices(Dk.shape).reshape(5, -1)
    cods = np.array([c for c, _ in TER]); noms = np.array([n for _, n in TER], dtype=object)
    X = pl.DataFrame({
        "anio": np.array(ANIOS)[ii[0]], "cod_dpto": cods[ii[1]], "territorio": noms[ii[1]], "sexo": ii[2] + 1, "grupo_edad": ii[3],
        "edad": np.array(T.ETQ, dtype=object)[ii[3]], "grupo_causa": np.array([NOM_PAR[g] for g in GRUPOS_PAR], dtype=object)[ii[4]],
        "defunciones": Dk.reshape(-1), "poblacion": Nk.reshape(-1), "mx": mx.reshape(-1), "mx_ic_inf": lo.reshape(-1),
        "mx_ic_sup": hi.reshape(-1), "fraccion": frac.reshape(-1), "registro": reg[ii[1]]})
    X = X.with_columns(
        pl.col("anio").cast(pl.Int16), pl.col("cod_dpto").cast(pl.Int16), pl.col("sexo").cast(pl.Int8), pl.col("grupo_edad").cast(pl.Int8),
        pl.col("territorio").cast(pl.String), pl.col("edad").cast(pl.String), pl.col("grupo_causa").cast(pl.String), pl.col("registro").cast(pl.String),
        pl.col("defunciones").round(6), pl.col("poblacion").round(4)).sort(["anio", "cod_dpto", "sexo", "grupo_causa", "grupo_edad"])
    X.write_parquet(PAR / "mortalidad_aps_parametros.parquet")
    X.write_csv(PAR / "mortalidad_aps_parametros.csv")
    (PAR / "datapackage.json").write_text(json.dumps(esquema(), ensure_ascii=False, indent=1), encoding="utf-8")


def esquema():
    f = lambda n, t, d, **k: dict(name=n, type=t, description=d, **k)
    comunes = [
        f("anio", "integer", "Año de la defunción (1998–2025)", constraints={"minimum": 1998, "maximum": 2025}),
        f("cod_dpto", "integer", "Código DIVIPOLA del departamento de residencia; 0 = Colombia"),
        f("territorio", "string", "Nombre del departamento o Colombia"),
        f("sexo", "integer", "1 = hombres, 2 = mujeres", constraints={"enum": [1, 2]}),
        f("grupo_edad", "integer", "Índice del grupo de edad: 0 = menor de 1 año, 1 = 1–4, 2 = 5–9, …, 17 = 80–84, 18 = 85 y más",
          constraints={"minimum": 0, "maximum": 18}),
        f("edad", "string", "Etiqueta del grupo de edad"),
    ]
    return {
        "name": "mortalidad-aps-parametros", "version": VERSION, "title": "Insumos de mortalidad por edad, sexo, departamento y grupo de causa",
        "description": ("Insumo de mortalidad por causa básica (no por estado de salud) para el simulador de sostenibilidad y Tessella Salud: defunciones registradas, tasas con su intervalo y fracción de cada grupo de causa. "
                        "El nivel de la mortalidad por todas las causas debe tomarse de las tablas de vida oficiales del DANE, que corrigen la omisión; este archivo da cómo se reparte entre grupos de causa. "
                        "Grupos de causa según la Lista brasileña de condiciones sensibles a la atención primaria (Portaria SAS/MS 221 de 2008)."),
        "licenses": [{"name": "CC-BY-NC-4.0", "path": "https://creativecommons.org/licenses/by-nc/4.0/"}],
        "sources": [{"title": "DANE, Estadísticas Vitales, defunciones no fetales; proyecciones de población"}],
        "contributors": [{"title": "Daniel A. Garavito Jiménez", "role": "author"}, {"title": "Sinergística", "role": "publisher", "path": "https://sinergistica.com"}],
        "resources": [
            {"name": "mortalidad_aps_parametros", "path": "mortalidad_aps_parametros.csv", "format": "csv", "encoding": "utf-8",
             "schema": {"primaryKey": ["anio", "cod_dpto", "sexo", "grupo_edad", "grupo_causa"], "fields": comunes + [
                 f("grupo_causa", "string", "todas; csaa_cardiometabolicas; csaa_respiratorias; csaa_infecciosas; csaa_otras; no_csaa. "
                   "Los cuatro csaa_* y no_csaa suman todas. La lista se aplica en todas las edades; el indicador de mortalidad evitable usa 0–74",
                   constraints={"enum": [NOM_PAR[g] for g in GRUPOS_PAR]}),
                 f("defunciones", "number", "Defunciones registradas (con la edad desconocida repartida; por eso puede tener decimales)"),
                 f("poblacion", "number", "Población a mitad de año, proyecciones del DANE"),
                 f("mx", "number", "Tasa central de mortalidad: defunciones / población (por persona-año)"),
                 f("mx_ic_inf", "number", "Límite inferior del IC 95 % (gamma, Poisson)"),
                 f("mx_ic_sup", "number", "Límite superior del IC 95 % (gamma, Poisson)"),
                 f("fraccion", "number", "Parte de las defunciones de la celda (año, territorio, sexo, edad) que es del grupo de causa; 1 en todas. Suavizada hacia la composición nacional de la misma celda con un peso de 5 defunciones; en Colombia es la observada. Uso: mx oficial del DANE por fraccion = mx del grupo de causa", constraints={"minimum": 0, "maximum": 1}),
                 f("registro", "string", "Completitud del registro de defunciones del territorio según el Termómetro (completo, incompleto, grave); nacional para Colombia. Con registro incompleto o grave, mx subestima la mortalidad; la fraccion es más robusta si la omisión no depende de la causa"),
             ]}},
            {"name": "hospitalizaciones_evitables_costo_2025", "path": "hospitalizaciones_evitables_costo_2025.csv", "format": "csv", "encoding": "utf-8",
             "sources": [{"title": "ADRES (2026). Hospitalizaciones evitables por condiciones sensibles a la Atención Primaria (HECSAP) en Colombia, cuadro 2. FEV-RIPS 2025",
                          "path": "https://consultorsalud.com/wp-content/uploads/2026/07/Hospitalizaciones_evitables_por_condiciones_sensibles_a_la_Atencion_Primaria.pdf"}],
             "schema": {"primaryKey": ["grupo"], "fields": [
                 f("grupo", "integer", "Grupo de la lista (1–19, Portaria SAS/MS 221 de 2008)"), f("condicion", "string", "Nombre del grupo"),
                 f("bloque", "string", "Bloque del simulador (cardiometabolicas, respiratorias, infecciosas, otras)"),
                 f("hospitalizaciones", "integer", "Hospitalizaciones con diagnóstico principal del grupo, Colombia 2025 (ADRES, FEV-RIPS; regímenes contributivo y subsidiado)"),
                 f("pacientes", "integer", "Pacientes únicos (ADRES); en el grupo 1, suma de los dos grupos de la ADRES, que pueden compartir pacientes"), f("costo_total_mm_cop", "number", "Costo total facturado, miles de millones de pesos corrientes de 2025 (sin episodios de costo cero o negativo)"),
                 f("costo_por_hospitalizacion_millones_cop", "number", "Costo medio por hospitalización, millones de pesos de 2025"),
                 f("muertes_2025", "number", "Defunciones de 2025 con causa básica del grupo, todas las edades (DANE; edad desconocida repartida)"),
             ]}},
        ],
    }


# ── 8. nivel B: de los microdatos procesados a data/intermedios/ ─────────────
def nivel_b(salida: Path):
    salida.mkdir(parents=True, exist_ok=True)
    C, cls = contar()
    C = C.sort(CLAVES + ["g"])
    C.write_parquet(salida / "conteos.parquet"); cls.sort("cb").write_parquet(salida / "codigos.parquet")
    poblacion_b().write_parquet(salida / "poblacion.parquet")
    (pl.read_parquet(procesado() / "poblacion_eevv.parquet").filter((pl.col("anio") == 2025) & (pl.col("dp") > 0))
     .group_by(["dp", "edad"]).agg(pl.col("pob").sum()).sort(["dp", "edad"])
     .with_columns(pl.col("dp").cast(pl.Int16), pl.col("edad").cast(pl.Int16))
     .write_parquet(salida / "poblacion_2025_edad_simple.parquet"))
    esperadas_dane().write_parquet(salida / "esperadas_dane_2015_2017.parquet")
    cruces(cls, salida)
    from . import municipal
    municipal.nivel_b(salida)                                     # municipal_csaa.parquet
    print(f"nivel B: {float(C['n'].sum()):,.0f} defunciones 1998–2025 -> {salida}")


def cruces(cls, salida: Path):
    """Cruce de cada código con las listas 6/67 (CAUSA_667) y 105 (CAU_HOMOL, 2020–2025) y con la OCDE/Eurostat;
    muertes con edad conocida menores de 75 años."""
    base = procesado() / "defunciones_eevv.parquet"
    m75q = (pl.scan_parquet(base).filter((pl.col("anio") >= 2015) & pl.col("g").is_between(0, Q75 - 1))
            .select(["c667", "cb", "sexo"]).collect().with_columns(pl.col("cb").fill_null("")).join(cls.select(["cb", "grupo", "trat", "prev", "solo_mujer"]), on="cb", how="left")
            .with_columns(pl.col("grupo").fill_null(0), pl.col("trat").fill_null(0.0), pl.col("prev").fill_null(0.0))
            .with_columns(pl.when((pl.col("solo_mujer") == 1) & (pl.col("sexo") != 2)).then(0.0).otherwise(pl.col("trat")).alias("trat")))
    c667 = (m75q.group_by("c667").agg(pl.len().alias("def_menores75_2015_2025"), (pl.col("grupo") > 0).sum().alias("def_csaa"),
                                       pl.col("trat").sum().alias("def_tratable_ocde"))
            .with_columns((100 * pl.col("def_csaa") / pl.col("def_menores75_2015_2025")).round(1).alias("pct_csaa"),
                          (100 * pl.col("def_tratable_ocde") / pl.col("def_menores75_2015_2025")).round(1).alias("pct_tratable_ocde"))
            .sort("c667"))
    et = {int(k): v for k, v in pl.read_csv(CONFIG / "causas_667.csv").select(["c667", "etiqueta"]).iter_rows()}
    et[109] = "Resto de ciertas enfermedades infecciosas y parasitarias (incluye COVID-19 desde 2020)"
    c667 = c667.with_columns(pl.col("c667").map_elements(lambda v: et.get(int(v), "") if v is not None else "", return_dtype=pl.String).alias("etiqueta"))
    c667.write_csv(salida / "cruce_lista_667.csv")
    # lista 105: CAU_HOMOL, que el paquete común no guarda; se lee del zip original de cada año
    import tempfile
    from eevv_insumos import defunciones, lectura, rutas as ru
    f105 = []
    with tempfile.TemporaryDirectory() as td:
        for a in range(2020, 2026):
            ya = procesado() / "defunciones_no_fetales" / f"{a}.parquet"     # copia ya extraída (repositorio EEVV), si existe
            if ya.exists():
                x = pl.read_parquet(ya).rename(lambda c: c.lower())
            else:
                dst = Path(td) / f"{a}.parquet"
                lectura.extraer_a_parquet(ru.crudo() / defunciones.RECIENTES[a], dst, columnas=["c_bas1", "cau_homol", "gru_ed1", "codptore"])
                x = pl.read_parquet(dst).rename(lambda c: c.lower())
            x = x.with_columns(pl.col("gru_ed1").cast(pl.String).cast(pl.Float64, strict=False).cast(pl.Int64), pl.col("codptore").cast(pl.String).cast(pl.Float64, strict=False).cast(pl.Int64),
                               pl.col("cau_homol").cast(pl.String).cast(pl.Float64, strict=False).cast(pl.Int64), pl.col("c_bas1").cast(pl.String))
            f105.append(x.filter(pl.col("gru_ed1").is_between(0, 22) & (pl.col("codptore").is_null() | (pl.col("codptore") != 75))).select(["c_bas1", "cau_homol", "gru_ed1", "codptore"]))
    x = pl.concat(f105).rename({"c_bas1": "cb"}).with_columns(pl.col("cb").fill_null("").str.replace_all(r"[^A-Za-z0-9]", "").str.to_uppercase())
    x = x.join(cls.select(["cb", "grupo"]), on="cb", how="left").with_columns(pl.col("grupo").fill_null(0))
    top = (x.group_by(["cau_homol", "cb"]).len().sort(["cau_homol", "len", "cb"], descending=[False, True, False])
           .group_by("cau_homol", maintain_order=True).agg(pl.col("cb").head(3).str.join(", ").alias("cie_mas_frecuentes")))
    (x.group_by("cau_homol").agg(pl.len().alias("def_menores75_2020_2025"), (pl.col("grupo") > 0).sum().alias("def_csaa"))
     .with_columns((100 * pl.col("def_csaa") / pl.col("def_menores75_2020_2025")).round(1).alias("pct_csaa"))
     .join(top, on="cau_homol").sort("cau_homol").write_csv(salida / "cruce_lista_105.csv"))
    (m75q.group_by("cb").agg(pl.len().alias("def_menores75_2015_2025")).join(cls, on="cb").filter(pl.col("grupo") > 0)
     .sort(["def_menores75_2015_2025", "cb"], descending=[True, False]).write_csv(salida / "codigos_csaa.csv"))
    solap = m75q.filter(pl.col("grupo") > 0)
    res = dict(def_csaa=solap.height, tratable_ocde=r(solap["trat"].sum(), 0), prevenible_ocde=r(solap["prev"].sum(), 0),
               pct_csaa_que_es_tratable_ocde=r(100 * solap["trat"].sum() / solap.height, 1),
               pct_tratable_ocde_que_es_csaa=r(100 * solap["trat"].sum() / m75q["trat"].sum(), 1))
    (salida / "solapamiento_ocde.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
