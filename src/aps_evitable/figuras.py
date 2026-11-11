"""Figuras y cuadros del manuscrito (matplotlib; estilo de la casa: Inter, fondo blanco, coma decimal, 300 ppp).
Todo sale de output/ (nivel A); nada se recalcula aquí."""
from __future__ import annotations

import json

import numpy as np
import polars as pl

from .rutas import OUTPUT, CONFIG

AZUL, NARANJA, GRIS, VERDE, MORADO, OCRE = "#11607A", "#C0601E", "#8a8a8a", "#1BA578", "#7B4FA3", "#B5892F"
COL_B = {"cardiometabolicas": "#A4425A", "respiratorias": AZUL, "infecciosas": VERDE, "otras": OCRE}
NOM_B = {"cardiometabolicas": "Cardiometabólicas", "respiratorias": "Respiratorias", "infecciosas": "Infecciosas", "otras": "Otras"}
FIG = OUTPUT / "figuras"


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    fam = "Inter" if any("Inter" in f.name for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
    plt.rcParams.update({"font.family": fam, "figure.dpi": 300, "savefig.dpi": 300, "font.size": 8,
                         "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e3e3e3",
                         "grid.linewidth": 0.6, "axes.axisbelow": True, "axes.edgecolor": "#555555", "axes.titlesize": 8.5,
                         "axes.titleweight": "semibold", "axes.titlelocation": "left", "figure.facecolor": "white",
                         "axes.facecolor": "white", "legend.frameon": False, "svg.hashsalt": "a5", "pdf.fonttype": 42})
    return plt


def coma(x, dec=0):
    s_ = f"{x:,.{dec}f}"
    return s_.replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")


def _ejes_coma(ax, dec=0, eje="y"):
    from matplotlib.ticker import FuncFormatter
    f = FuncFormatter(lambda v, _: coma(v, dec))
    (ax.yaxis if eje == "y" else ax.xaxis).set_major_formatter(f)


def figura1(R):
    """Serie nacional 1998–2025: tasa estandarizada total y por sexo con IC 95 %, y por bloque de causas."""
    plt = _plt()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw={"wspace": 0.28})
    for sx, col, nom in (("total", AZUL, "Total"), ("hombres", NARANJA, "Hombres"), ("mujeres", MORADO, "Mujeres")):
        d = [x for x in R["nacional"] if x["sexo"] == sx]
        an = [x["anio"] for x in d]
        a1.plot(an, [x["tee_csaa"] for x in d], color=col, lw=1.4, label=nom)
        a1.fill_between(an, [x["tee_csaa_lo"] for x in d], [x["tee_csaa_hi"] for x in d], color=col, alpha=.18, lw=0)
    a1.axvspan(2019.5, 2021.5, color="#efefef", zorder=0)
    a1.text(2020.5, 3, "pandemia", ha="center", fontsize=6.5, color=GRIS)
    a1.set_title("A. Tasa estandarizada por edad, por 100.000")
    a1.set_ylim(0, None); a1.legend(loc="upper right", fontsize=7); _ejes_coma(a1)
    d = [x for x in R["nacional"] if x["sexo"] == "total"]
    an = [x["anio"] for x in d]
    for b in ("cardiometabolicas", "respiratorias", "infecciosas", "otras"):
        a2.plot(an, [x[f"tee_{b}"] for x in d], color=COL_B[b], lw=1.4, label=NOM_B[b])
    a2.axvspan(2019.5, 2021.5, color="#efefef", zorder=0)
    a2.set_title("B. Por bloque de condiciones, por 100.000")
    a2.set_ylim(0, None); a2.legend(loc="upper right", fontsize=7); _ejes_coma(a2)
    for a in (a1, a2):
        a.set_xticks([1998, 2003, 2008, 2013, 2018, 2023]); a.set_xlim(1997.5, 2025.5)
    fig.savefig(FIG / "figura1_serie_nacional.png", bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)


def figura2(R):
    """Departamentos 2023–2025: tasa estandarizada con IC 95 %, ordenada, con el subregistro grave marcado."""
    plt = _plt()
    cl = dict(pl.read_csv(CONFIG / "completitud_territorial.csv").select(["departamento", "clase"]).iter_rows())
    tri = [x for x in R["trienio"] if x["sexo"] == "total" and x["cod"] > 0]
    nac = next(x for x in R["trienio"] if x["sexo"] == "total" and x["cod"] == 0)
    tri.sort(key=lambda x: x["tee_csaa"])
    fig, ax = plt.subplots(figsize=(4.6, 6.2))
    y = np.arange(len(tri))
    for i, x in enumerate(tri):
        fuera = x["tee_csaa_lo"] > nac["tee_csaa"] or x["tee_csaa_hi"] < nac["tee_csaa"]
        col = NARANJA if x["tee_csaa_lo"] > nac["tee_csaa"] else AZUL if x["tee_csaa_hi"] < nac["tee_csaa"] else GRIS
        ax.plot([x["tee_csaa_lo"], x["tee_csaa_hi"]], [i, i], color=col, lw=1.1)
        ax.plot(x["tee_csaa"], i, "o", ms=3.6, color=col, mfc=col if fuera else "white")
    ax.axvline(nac["tee_csaa"], color="#555555", lw=.8, ls="--")
    ax.text(nac["tee_csaa"] + 1, len(tri) - .2, f"Colombia {coma(nac['tee_csaa'], 1)}", fontsize=6.5, color="#555555")
    ax.set_yticks(y)
    ax.set_yticklabels([x["territorio"].replace(" y Providencia", "") + (" *" if cl.get(x["territorio"]) == "grave" else "") for x in tri], fontsize=6.6)
    ax.set_xlim(0, None); ax.grid(axis="y", visible=False); _ejes_coma(ax, eje="x")
    ax.set_xlabel("Muertes antes de los 75 años por 100.000, estandarizadas por edad (IC 95 %)")
    fig.savefig(FIG / "figura2_departamentos.png", bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)


def figura3(T):
    """Razón estandarizada de hospitalización (ADRES, 2025) frente a razón estandarizada de mortalidad (2025)."""
    plt = _plt()
    H = [x for x in T["hospitalizaciones"]["departamentos"] if x["cod"] > 0 and x["reh"] is not None]
    fig, ax = plt.subplots(figsize=(4.8, 4.2))
    mx = max(x["hosp_hecsap"] for x in H)
    for x in H:
        col = NARANJA if x["rme_sobre_reh_lo"] > 1 else AZUL if x["rme_sobre_reh_hi"] < 1 else GRIS
        ax.scatter(x["reh"], x["rme"], s=10 + 220 * np.sqrt(x["hosp_hecsap"] / mx), color=col, alpha=.6, edgecolor=col, lw=.6)
        if x["rme_sobre_reh"] > 1.6 or x["rme_sobre_reh_hi"] < .75 or x["cod"] == 11:
            ax.annotate(x["territorio"].replace(" y Providencia", "").replace(" D.C.", ""), (x["reh"], x["rme"]), xytext=(4, 2),
                        textcoords="offset points", fontsize=6.3)
    ax.set_xscale("log"); ax.set_yscale("log")
    lo, hi = .14, 2.3
    ax.plot([lo, hi], [lo, hi], color="#555555", lw=.8, ls="--")
    ax.set_xlim(.14, 2.2); ax.set_ylim(.6, 2.2)
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator
    for e, t in ((ax.xaxis, [.2, .3, .5, .7, 1, 1.5, 2]), (ax.yaxis, [.7, .8, 1, 1.25, 1.5, 2])):
        e.set_major_locator(FixedLocator(t)); e.set_minor_locator(NullLocator()); e.set_major_formatter(FuncFormatter(lambda v, _: coma(v, 2).rstrip("0").rstrip(",")))
    ax.set_xlabel("Hospitalizaciones evitables: observadas / esperadas por edad")
    ax.set_ylabel("Muertes por las mismas condiciones: observadas / esperadas")
    ax.text(.15, 2.05, "más muertes que hospitalizaciones", fontsize=6.3, color=NARANJA, va="top")
    ax.text(2.1, .62, "más hospitalizaciones que muertes", fontsize=6.3, color=AZUL, ha="right")
    fig.savefig(FIG / "figura3_hospitalizaciones_muertes.png", bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)


def cuadros(R, T):
    """Cuadro 1 (condiciones) y cuadro 2 (Colombia por sexo y sensibilidades), en CSV."""
    tab = OUTPUT / "tablas"
    hc = {x["grupo"]: x for x in T["hospitalizaciones"]["por_condicion"]}
    filas = []
    for g in R["grupos_trienio"]:
        h = hc[g["grupo"]]
        filas.append(dict(grupo=g["grupo"], condicion=g["nombre"], bloque=g["bloque"], muertes_menores75_anual=g["def_anual"],
                          tasa_estandarizada=g["tee"], ic_inf=g["ic"][0], ic_sup=g["ic"][1], avpp_anual=g["avpp_anual"],
                          hospitalizaciones_2025=h["hospitalizaciones"], costo_por_hosp_millones=h["costo_por_hosp_millones"],
                          muertes_2025_todas_edades=h["muertes_2025"], muertes_por_mil_hosp=h["muertes_por_mil_hosp"]))
    pl.DataFrame(filas).write_csv(tab / "cuadro1_condiciones.csv")
    tri = {(x["cod"], x["sexo"]): x for x in R["trienio"]}
    filas = []
    for sx in ("total", "hombres", "mujeres"):
        x = tri[(0, sx)]
        filas.append(dict(sexo=sx, muertes_anual=round(x["def_csaa75"] / 3), pct_muertes_menores75=round(100 * x["def_csaa75"] / x["def_menores75"], 1),
                          tasa=x["tee_csaa"], ic_inf=x["tee_csaa_lo"], ic_sup=x["tee_csaa_hi"], avpp_anual=round(x["avpp_csaa"] / 3),
                          p65=x["p65"], p65_sin=x["p65_sin_csaa"], ganancia=x["ganancia"], ganancia_lo=x["ganancia_lo"], ganancia_hi=x["ganancia_hi"]))
    pl.DataFrame(filas).write_csv(tab / "cuadro2a_colombia_sexo.csv")
    sp = T["spearman"]
    nac = tri[(0, "total")]
    nomb = {"tee_sens_maldef": "Causas mal definidas (R00–R99) repartidas entre las naturales",
            "tee_sens_sin_inesp": "Sin códigos poco específicos (I50, J81, E86)", "tee_sens_70": "Corte en 70 años",
            "tee_sens_neumonias": "Todas las neumonías (J12–J18)", "tee_sens_adres": "Ampliación operativa de la ADRES (I12, I13, I15, N39)",
            "tee_csaa_corr": "Escenario con la omisión implícita del DANE", "tee_tratable_ocde": "Mortalidad tratable OCDE/Eurostat"}
    pl.DataFrame([dict(variante=nomb[k], tasa_colombia=nac[k], spearman_departamentos=sp[k]) for k in nomb]).write_csv(tab / "cuadro2b_sensibilidad.csv")
    # cuadro S1: departamentos, trienio 2023-2025 y cruce con la ADRES 2025
    hd = {int(x["cod"]): x for x in T["hospitalizaciones"]["departamentos"]}
    filas = []
    for x in sorted((v for (c, s), v in tri.items() if s == "total" and c != 0), key=lambda v: -v["tee_csaa"]):
        h = hd.get(int(x["cod"]), {})
        pos = ("mayor" if x["tee_csaa_lo"] > nac["tee_csaa"] else "menor" if x["tee_csaa_hi"] < nac["tee_csaa"] else "")
        filas.append(dict(cod=x["cod"], departamento=x["territorio"], muertes_trienio=round(x["def_csaa75"]),
                          tasa=x["tee_csaa"], ic_inf=x["tee_csaa_lo"], ic_sup=x["tee_csaa_hi"], frente_al_pais=pos,
                          tasa_escenario_omision=x["tee_csaa_corr"], pct_maldefinidas=x["pct_maldef75"],
                          reh_2025=h.get("reh"), rme_2025=h.get("rme"), rme_sobre_reh=h.get("rme_sobre_reh"),
                          rme_sobre_reh_lo=h.get("rme_sobre_reh_lo"), rme_sobre_reh_hi=h.get("rme_sobre_reh_hi")))
    pl.DataFrame(filas).write_csv(tab / "cuadroS1_departamentos.csv")
    # cuadro S2: los diez municipios de cada extremo de la razón de hospitalización de la ADRES y su mortalidad
    top = pl.read_csv(OUTPUT / "municipal" / "top_municipios_adres.csv")
    oculto = (pl.col("muertes_csaa75") >= 1) & (pl.col("muertes_csaa75") <= 4)     # con 1 a 4 muertes: solo la clase
    (top.with_columns(pl.when(oculto).then(pl.lit("<5")).otherwise(pl.col("muertes_csaa75").cast(pl.String)).alias("muertes_csaa75_publicable"),
                      *[pl.when(oculto).then(None).otherwise(pl.col(c)).alias(c) for c in ("rme_eb", "rme_eb_lo", "rme_eb_hi")])
        .select(["lado", "orden", "municipio", "departamento", "mun", "oe_hosp", "n_hecsap", "hosp_por_10k", "muertes_csaa75_publicable",
                 "rme_eb", "rme_eb_lo", "rme_eb_hi", "clase_eb"])
        .write_csv(tab / "cuadroS2_municipios_adres.csv"))


def todo():
    FIG.mkdir(parents=True, exist_ok=True)
    R = json.loads((OUTPUT / "resultados.json").read_text(encoding="utf-8"))
    T = json.loads((OUTPUT / "aps_tablero.json").read_text(encoding="utf-8"))
    figura1(R); figura2(R); figura3(T); cuadros(R, T)
