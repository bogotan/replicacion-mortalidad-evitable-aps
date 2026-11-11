#!/usr/bin/env python3
"""Verifica cada cifra del manuscrito A5 contra las salidas del repositorio (nivel A).

Lee output/resultados.json, output/aps_tablero.json y output/tablas/*.csv (scripts/03_estimar.py y 04_figuras.py),
recalcula las cifras derivadas (porcentajes, razones, conteos de departamentos, puestos) y comprueba que cada número,
con su redondeo exacto y en su contexto, aparece en manuscrito/manuscrito.md. Revisa además que los cuadros del texto
coinciden fila por fila con los CSV, que se cumplen las afirmaciones cualitativas, que las figuras existen y las
normas de la revista (extensión, título, referencias citadas en orden) y de estilo. Termina en «Todo coincide.» o lista
las fallas.

Uso: python pruebas/verificar_cifras.py
"""
import csv
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
OUT = RAIZ / "output"
_RUTA_TXT = RAIZ / "manuscrito" / "manuscrito.md"
if not _RUTA_TXT.exists():
    print("El texto del artículo no está en este repositorio; se agrega cuando se publique. Las pruebas de cálculo (pytest) sí corren.")
    sys.exit(0)
TXT = (RAIZ / "manuscrito" / "manuscrito.md").read_text(encoding="utf-8")
R = json.loads((OUT / "resultados.json").read_text(encoding="utf-8"))
T = json.loads((OUT / "aps_tablero.json").read_text(encoding="utf-8"))
fallas, n_ok = [], 0


def f(x, d=2):
    """Número en estilo de la revista: coma decimal y espacio como separador de miles."""
    s = f"{float(x):,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", " ").replace("-", "−")  # signo menos tipográfico


def esta(que, s):
    global n_ok
    if s in TXT:
        n_ok += 1
    else:
        fallas.append(f"{que}: no se encontró «{s}»")


def cumple(que, cond):
    global n_ok
    if cond:
        n_ok += 1
    else:
        fallas.append(f"afirmación del texto no se cumple: {que}")


def leer(nombre):
    return list(csv.DictReader(open(OUT / "tablas" / nombre, encoding="utf-8")))


def ic(lo, hi, d=2):
    return f"{f(lo, d)}–{f(hi, d)}"


# ── 1. registros y totales ────────────────────────────────────────────────────────────────────
esta("registros", f"{f(R['n_registros'], 0)} registros")
esta("sin edad", f"{f(R['n_sin_edad_repartidos'], 0)} sin edad")
tri = {(x["cod"], x["sexo"]): x for x in R["trienio"]}
N = tri[(0, "total")]
esta("muertes anuales", f"{f(N['def_csaa75'] / 3, 0)} muertes anuales por CSAA")
esta("muertes anuales (abstract)", f"there were {f(N['def_csaa75'] / 3, 0)} PCSC deaths")
esta("% <75", f"({f(100 * N['def_csaa75'] / N['def_menores75'], 1)} % de las muertes a esas edades)")
esta("% <75 resultados", f"el {f(100 * N['def_csaa75'] / N['def_menores75'], 1)} % de las {f(N['def_menores75'], 0)} muertes")
esta("tasa nacional", f"53,41 por 100 000 (IC 95 %: {ic(N['tee_csaa_lo'], N['tee_csaa_hi'])})")
cumple("tasa nacional 53,41", f(N["tee_csaa"]) == "53,41")
for sx, nombre in (("hombres", "en hombres"), ("mujeres", "en mujeres")):
    x = tri[(0, sx)]
    esta(f"tasa {sx}", f"{nombre}, {f(x['tee_csaa'])} ({ic(x['tee_csaa_lo'], x['tee_csaa_hi'])})")
H, M = tri[(0, "hombres")], tri[(0, "mujeres")]
esta("razón por sexo", f"una razón de {f(H['tee_csaa'] / M['tee_csaa'])}")
esta("AVPP", f"{f(N['avpp_csaa'] / 3, 0)} AVPP por año")
esta("tasa AVPP", f"{f(N['tee_avpp_csaa'])} por 100 000 ({ic(N['tee_avpp_csaa_lo'], N['tee_avpp_csaa_hi'])})")
esta("P65", f"La probabilidad de llegar a los 65 años fue {f(N['p65'], 5)}; sin las CSAA habría sido {f(N['p65_sin_csaa'], 5)}")
esta("ganancia", f"una ganancia de {f(N['ganancia'], 5)} ({ic(N['ganancia_lo'], N['ganancia_hi'], 5)})")
esta("ganancia en 100", f"1,7 de cada 100 recién nacidos más")
cumple("1,7 de cada 100", f(100 * N["ganancia"], 1) == "1,7")
esta("ganancia por sexo", f"La ganancia fue {f(H['ganancia'], 5)} en hombres y {f(M['ganancia'], 5)} en mujeres")
cumple("una de cada seis o siete muertes", 6 < N["def_menores75"] / N["def_csaa75"] < 7)

# ── 2. condiciones ────────────────────────────────────────────────────────────────────────────
gr = sorted(R["grupos_trienio"], key=lambda g: -g["def_anual"])
top4 = gr[:4]
esta("top 4 %", f"Cuatro grupos explicaron el {f(100 * sum(g['def_anual'] for g in top4) / (N['def_csaa75'] / 3), 1)} %")
cumple("los cuatro primeros son 13, 12, 8, 9", [g["grupo"] for g in top4] == [13, 12, 8, 9])
for g, et in zip(top4, ["diabetes mellitus", "enfermedad cerebrovascular", "enfermedades pulmonares crónicas y agudas", "hipertensión"]):
    s = f"{et} ({f(g['def_anual'], 0)} por año; tasa {f(g['tee'])})" if g is top4[0] else f"{et} ({f(g['def_anual'], 0)}; {f(g['tee'])})"
    esta(f"grupo {g['grupo']}", s)
esta("mal definidas", f"el {f(N['pct_maldef75'])} % de las muertes de menores de 75")
so = R["solapamiento_ocde"]
esta("solapamiento 1", f"El {f(so['pct_csaa_que_es_tratable_ocde'], 1)} % de las muertes por CSAA son mortalidad tratable")
esta("solapamiento 2", f"solo el {f(so['pct_tratable_ocde_que_es_csaa'], 1)} % de la mortalidad tratable es CSAA")

# ── 3. tendencia ──────────────────────────────────────────────────────────────────────────────
S = {x["anio"]: x for x in R["nacional"] if x["sexo"] == "total"}
esta("1998", f"bajó de {f(S[1998]['tee_csaa'])} ({ic(S[1998]['tee_csaa_lo'], S[1998]['tee_csaa_hi'])}) en 1998 a {f(S[2014]['tee_csaa'])} en 2014")
caida = 100 * (1 - S[2014]["tee_csaa"] / S[1998]["tee_csaa"])
esta("caída 48,3", f"una caída de {f(caida, 1)} %")
post = {a: S[a]["tee_csaa"] for a in range(2014, 2026)}
amin, amax = min(post, key=post.get), max(post, key=post.get)
esta("rango posterior", f"osciló entre {f(post[amin])} ({amin}) y {f(post[amax])} ({amax})")
esta("2025", f"en 2025 fue {f(S[2025]['tee_csaa'])} ({ic(S[2025]['tee_csaa_lo'], S[2025]['tee_csaa_hi'])})")
esta("cardiometabólico", f"(de {f(S[1998]['tee_cardiometabolicas'])} a {f(S[2025]['tee_cardiometabolicas'])} entre 1998 y 2025)")
cumple("cardiometabólico explica la mayor parte", (S[1998]["tee_cardiometabolicas"] - S[2025]["tee_cardiometabolicas"]) > 0.5 * (S[1998]["tee_csaa"] - S[2025]["tee_csaa"]))
esta("respiratorio", f"respiratorio (de {f(S[1998]['tee_respiratorias'])} a {f(S[2025]['tee_respiratorias'])})")
esta("otros", f"de otros (de {f(S[1998]['tee_otras'])} a {f(S[2025]['tee_otras'])})")
inf = {a: S[a]["tee_infecciosas"] for a in S}
amin_inf = min(inf, key=inf.get)
cumple("mínimo infeccioso en 2011", amin_inf == 2011)
esta("infeccioso", f"bajó de {f(inf[1998])} en 1998 a {f(inf[2011])} en 2011 y subió hasta {f(inf[2025])} en 2025")
cumple("infeccioso > respiratorio desde 2021 y no en 2020",
       all(S[a]["tee_infecciosas"] > S[a]["tee_respiratorias"] for a in range(2021, 2026)) and S[2020]["tee_infecciosas"] < S[2020]["tee_respiratorias"])

# ── 4. territorios ────────────────────────────────────────────────────────────────────────────
D = sorted([x for x in R["trienio"] if x["sexo"] == "total" and x["cod"] != 0], key=lambda x: -x["tee_csaa"])
nom = {x["territorio"]: x for x in D}
for n_ in ("Chocó", "Guainía"):
    x = nom[n_]
    esta(f"alto {n_}", f"{n_}, {f(x['tee_csaa'])} ({ic(x['tee_csaa_lo'], x['tee_csaa_hi'])})" if n_ == "Chocó" else f"{n_}, {f(x['tee_csaa'])} ({ic(x['tee_csaa_lo'], x['tee_csaa_hi'])})")
cumple("Chocó y Guainía son los dos primeros", [x["territorio"] for x in D[:2]] == ["Chocó", "Guainía"])
for n_ in ("Caquetá", "La Guajira", "Guaviare", "San Andrés y Providencia"):
    esta(f"alto {n_}", f"{n_} ({f(nom[n_]['tee_csaa'])})")
cumple("puestos 3 a 6", [x["territorio"] for x in D[2:6]] == ["Caquetá", "La Guajira", "Guaviare", "San Andrés y Providencia"])
b = nom["Bogotá D.C."]
esta("Bogotá", f"Bogotá, {f(b['tee_csaa'])} ({ic(b['tee_csaa_lo'], b['tee_csaa_hi'])})")
for n_ in ("Cundinamarca", "Cauca", "Santander", "Nariño", "Boyacá"):
    esta(f"bajo {n_}", f"{n_} ({f(nom[n_]['tee_csaa'])})")
cumple("los seis más bajos", [x["territorio"] for x in D[-6:]][::-1] == ["Bogotá D.C.", "Cundinamarca", "Cauca", "Santander", "Nariño", "Boyacá"])
esta("razón max/min", f"La razón entre la mayor y la menor fue {f(D[0]['tee_csaa'] / D[-1]['tee_csaa'])}")
esta("Chocó duplica", f"Chocó ({f(D[0]['tee_csaa'])}) duplicó a Bogotá ({f(D[-1]['tee_csaa'])})")
arriba = sum(x["tee_csaa_lo"] > N["tee_csaa"] for x in D); abajo = sum(x["tee_csaa_hi"] < N["tee_csaa"] for x in D)
cumple("18 arriba y 6 abajo", (arriba, abajo) == (18, 6))
esta("arriba/abajo", "dieciocho departamentos quedaron por encima del país y seis por debajo")
cumple("33 departamentos", len(D) == 33)

# ── 5. sensibilidad ───────────────────────────────────────────────────────────────────────────
sp = T["spearman"]
esta("sp maldef", f"fue {f(sp['tee_sens_maldef'], 3)} al repartir las causas mal definidas")
esta("sp inesp", f"{f(sp['tee_sens_sin_inesp'], 3)} sin los códigos poco específicos")
esta("sp 70", f"{f(sp['tee_sens_70'], 3)} con corte en 70 años")
esta("sp neum", f"{f(sp['tee_sens_neumonias'], 3)} con todas las neumonías")
esta("sp adres", f"y {f(sp['tee_sens_adres'], 3)} con la ampliación de la ADRES")
esta("sp omisión", f"con el escenario de omisión ({f(sp['tee_csaa_corr'], 3)})")
esta("sp tratable", f"con la mortalidad tratable ({f(sp['tee_tratable_ocde'], 3)})")
esta("omisión nacional", f"que llevó la tasa nacional a {f(N['tee_csaa_corr'])}")
esta("omisión Chocó y Guajira", f"la de Chocó a {f(nom['Chocó']['tee_csaa_corr'])} y la de La Guajira a {f(nom['La Guajira']['tee_csaa_corr'])}")
esta("omisión P65", f"bajó a {f(N['p65_corr'], 5)} y la ganancia por eliminar las CSAA subió a {f(N['ganancia_corr'], 5)}")
esta("omisión Cauca Nariño", f"pasaron a {f(nom['Cauca']['tee_csaa_corr'])} y {f(nom['Nariño']['tee_csaa_corr'])}")
esta("sin inespecíficos discusión", f"baja la tasa nacional de {f(N['tee_csaa'])} a {f(N['tee_sens_sin_inesp'])}")
grave = [r_["departamento"] for r_ in csv.DictReader(open(RAIZ / "config" / "completitud_territorial.csv", encoding="utf-8")) if r_["clase"] == "grave"]
esta("lista de omisión grave", "es grave en Chocó, La Guajira, Cauca, Córdoba, Nariño, Putumayo, Amazonas, Guainía, Vaupés y Vichada")
cumple("lista de omisión grave = config", set(grave) == {"Chocó", "La Guajira", "Cauca", "Córdoba", "Nariño", "Putumayo", "Amazonas", "Guainía", "Vaupés", "Vichada"})

# ── 6. hospitalizaciones ──────────────────────────────────────────────────────────────────────
h = T["hospitalizaciones"]
hn = h["nacional"]
esta("HECSAP", f"encontró {f(hn['hosp'], 0)} hospitalizaciones evitables, el {f(hn['pct_hosp'], 1)} % de las hospitalizaciones y el {f(hn['pct_gasto'], 1)} % del gasto")
hd = {x["territorio"]: x for x in h["departamentos"]}
esta("muertes por 1000 país", f"En 2025 hubo {f(hd['Colombia']['muertes_por_mil_hosp'], 1)} muertes por CSAA")
pc = {x["grupo"]: x for x in h["por_condicion"]}
esta("por condición", f"{f(pc[12]['muertes_por_mil_hosp'], 1)} en enfermedad cerebrovascular, {f(pc[13]['muertes_por_mil_hosp'], 1)} en diabetes, "
     f"{f(pc[4]['muertes_por_mil_hosp'], 1)} en deficiencias nutricionales, {f(pc[8]['muertes_por_mil_hosp'], 1)} en enfermedades pulmonares y "
     f"{f(pc[9]['muertes_por_mil_hosp'], 1)} en hipertensión, frente a {f(pc[15]['muertes_por_mil_hosp'], 1)} en infecciones urinarias y "
     f"{f(pc[16]['muertes_por_mil_hosp'], 1)} en infecciones de la piel")
cumple("las cinco más altas por 1000", sorted(pc, key=lambda g: -pc[g]["muertes_por_mil_hosp"])[:5] == [12, 13, 4, 8, 9])
sh = h["spearman"]
esta("rho cruda", f"tuvieron una correlación de {f(sh['tasa_hosp_vs_tee_2023_2025'], 3)}")
esta("rho REH RME", f"la REH y la RME, de {f(sh['reh_vs_rme_2025'], 3)}")
esta("rho resumen", f"(rho de Spearman {f(sh['reh_vs_rme_2025'], 3)})")
dd = [x for x in h["departamentos"] if x["cod"] != 0]
may = sorted([x for x in dd if x["rme_sobre_reh_lo"] > 1], key=lambda x: -x["rme_sobre_reh"])
men = sorted([x for x in dd if x["rme_sobre_reh_hi"] < 1], key=lambda x: x["rme_sobre_reh"])
cumple("19 mayores y 11 menores", (len(may), len(men)) == (19, 11))
esta("19 dptos", f"el cociente RME/REH fue mayor que 1 en {len(may)} departamentos")
esta("11 dptos", f"En {len(men)} fue menor que 1")
for x in may[:3]:
    esta(f"RME/REH {x['territorio']}", f"{x['territorio']} {f(x['rme_sobre_reh'], 3)} ({ic(x['rme_sobre_reh_lo'], x['rme_sobre_reh_hi'], 3)})")
esta("y otros 16", f"Chocó {f(may[2]['rme_sobre_reh'], 3)} ({ic(may[2]['rme_sobre_reh_lo'], may[2]['rme_sobre_reh_hi'], 3)}) y otros {len(may) - 3} (cuadro suplementario S1)")
cumple("orden de los 8 primeros", [x["territorio"] for x in may[:8]] == ["Guainía", "Vichada", "Chocó", "Vaupés", "San Andrés y Providencia", "Guaviare", "Risaralda", "Magdalena"])
hu = men[0]
cumple("el más bajo es Huila", hu["territorio"] == "Huila")
esta("Huila", f"Huila, {f(hu['rme_sobre_reh'], 3)} ({ic(hu['rme_sobre_reh_lo'], hu['rme_sobre_reh_hi'], 3)}), donde la REH fue {f(hu['reh'], 3)} y la RME {f(hu['rme'], 3)}")
cumple("puestos 2 a 7 de los menores", [x["territorio"] for x in men[1:7]] == ["Sucre", "Arauca", "Amazonas", "Boyacá", "Caquetá", "Bogotá D.C."])
crudo = [x["territorio"] for x in sorted(dd, key=lambda x: -x["muertes_por_mil_hosp"])]
est = [x["territorio"] for x in sorted(dd, key=lambda x: -x["rme_sobre_reh"])]
cumple("Risaralda, Quindío y Caldas: puestos 2 a 4 crudos", crudo[1:4] == ["Risaralda", "Quindío", "Caldas"])
cumple("y 7, 11 y 12 estandarizados", [est.index(n_) + 1 for n_ in ("Risaralda", "Quindío", "Caldas")] == [7, 11, 12])
se = {x["anio"]: x for x in h["serie"]}
esta("caída hosp", f"bajó {f(100 * (1 - se[2024]['tasa_hosp_10k'] / se[2019]['tasa_hosp_10k']), 0)} %")
esta("caída mort", f"la estandarizada de menores de 75 bajó {f(100 * (1 - se[2024]['tee'] / se[2019]['tee']), 0)} % (de {f(se[2019]['tee'])} a {f(se[2024]['tee'])})")
esta("mort cruda", f"subió {f(100 * (se[2024]['tasa_cruda_mort_100k'] / se[2019]['tasa_cruda_mort_100k'] - 1), 0)} % (de {f(se[2019]['tasa_cruda_mort_100k'])} a {f(se[2024]['tasa_cruda_mort_100k'])} por 100 000)")
esta("caída hosp discusión", f"La caída de {f(100 * (1 - se[2024]['tasa_hosp_10k'] / se[2019]['tasa_hosp_10k']), 0)} % en la tasa de hospitalización")


# ── 6b. análisis pedidos por el árbitro (output/sensibilidad.json) ────────────────────────────
SE = json.loads((OUT / "sensibilidad.json").read_text(encoding="utf-8"))
tc = SE["tendencia"]
def cpa(x):
    return f"{f(x['cpa'])} % ({f(x['lo'])} a {f(x['hi'])})"
esta("CPA 1998-2014", f"El CPA fue {cpa(tc['tee_csaa']['1998_2014'])} entre 1998 y 2014")
esta("CPA 2014-2025", f"y {cpa(tc['tee_csaa']['2014_2025_sin_2020_2021'])} entre 2014 y 2025, sin 2020 ni 2021")
x = tc["tee_todas75"]["2014_2025_sin_2020_2021"]
esta("CPA todas", f"tampoco bajó ({f(x['cpa'])} %; {f(x['lo'])} a {f(x['hi'])})")
cumple("CPA 2014-2025 CSAA y todas incluyen el cero", tc["tee_csaa"]["2014_2025_sin_2020_2021"]["lo"] < 0 < tc["tee_csaa"]["2014_2025_sin_2020_2021"]["hi"] and x["lo"] < 0 < x["hi"])
esta("CPA cardio", f"siguió bajando ({f(tc['tee_cardiometabolicas']['2014_2025_sin_2020_2021']['cpa'])} % anual)")
cumple("cardiometabólico baja con IC bajo cero", tc["tee_cardiometabolicas"]["2014_2025_sin_2020_2021"]["hi"] < 0)
xi = tc["tee_infecciosas"]["2014_2025_sin_2020_2021"]
esta("CPA infecciosas", f"subió {f(xi['cpa'])} % anual ({f(xi['lo'])} a {f(xi['hi'])})")
s14 = tc["tee_csaa"]["2014_2025_sin_2020_2021"]
esta("resumen CPA", f"La tasa bajó {f(-tc['tee_csaa']['1998_2014']['cpa'])} % por año entre 1998 y 2014 y no cambió entre 2014 y 2025 ({f(s14['cpa'])} % por año; IC 95 %: {f(s14['lo'])} a {f(s14['hi'])})")
esta("resumen infecciosas", f"las infecciosas subieron {f(xi['cpa'])} % por año")
gi = SE["grupos_infecciosos"]
esta("neumonías y urinarias", f"la tasa de neumonías bacterianas pasó de {f(gi['6']['t2011'])} a {f(gi['6']['t2025'])} y la de infecciones urinarias, de {f(gi['15']['t2011'])} a {f(gi['15']['t2025'])}")
cumple("neumonías y urinarias son los dos mayores aumentos absolutos", sorted(gi, key=lambda g: -(gi[g]["t2025"] - gi[g]["t2011"]))[:2] == ["6", "15"])
od = SE["sobredispersion"]
esta("phi tasas", f"fue {f(od['tasas']['phi'], 1)} veces la que produciría el azar")
cumple("cuasi-Poisson tasas: solo Bogotá abajo, ninguno arriba", od["tasas"]["abajo_lista"] == ["Bogotá D.C."] and od["tasas"]["arriba"] == 0)
esta("phi cociente", f"El factor de dispersión del cociente fue {f(od['rme_sobre_reh']['phi'], 1)}")
cumple("cuasi-Poisson cociente: solo Huila y Bogotá abajo", od["rme_sobre_reh"]["abajo_lista"] == ["Huila", "Bogotá D.C."] and od["rme_sobre_reh"]["arriba"] == 0)
rc = SE["reh_cruda"]
esta("REH cruda", f"casi no cambió (Spearman {f(rc['spearman_con_principal'], 3)})")
cumple("REH cruda: tres mayores iguales", rc["tres_mayores"] == ["Guainía", "Vichada", "Chocó"])
esta("0,46 %", "suma el 0,46 % de sus hospitalizaciones")


# ── 6c. municipios (output/municipal/, src/aps_evitable/municipal.py) ───────────────────────────
MU = json.loads((OUT / "municipal" / "resultados.json").read_text(encoding="utf-8"))
esta("municipios 10", f"De {f(MU['municipios_10'], 0)} municipios con 10 o más muertes, el {f(MU['pct_alta'], 1)} % tuvo una mortalidad por encima de lo esperado y el {f(MU['pct_baja'], 1)} % por debajo")
esta("ADRES 48,9 %", "en la ADRES, el 48,9 % de 1 091 municipios tuvo una razón de hospitalización alta")
cumple("534 de 1 091 = 48,9 % (texto de la ADRES; su tabla 6 suma 534 altos)", f(100 * MU["adres_n_alto"] / 1091, 1) == "48,9")
esta("spearman municipal", f"no se correlacionaron (Spearman {f(MU['spearman_dpto']['pct_alta_vs_adres_pct_alto'], 3)}; IC 95 %: {f(MU['spearman_dpto']['pct_alta_vs_adres_pct_alto_ic'][0], 2)} a {f(MU['spearman_dpto']['pct_alta_vs_adres_pct_alto_ic'][1], 2)})")
import pandas as _pd
_mc = _pd.read_parquet(RAIZ / "data" / "intermedios" / "municipal_csaa.parquet")
esta("potencia", f"unas {f(_mc['muertes_csaa75'].sum() / len(_mc), 0)} muertes en tres años frente a unas {f(round(MU['hosp_por_municipio'], -1), 0)} hospitalizaciones en un año")
dm = {r_["departamento"]: r_ for r_ in leer("../municipal/departamentos_municipal.csv")}
esta("Cundinamarca", f"Cundinamarca tuvo {f(dm['Cundinamarca']['adres_pct_alto'], 1)} % de municipios altos en hospitalización y {f(dm['Cundinamarca']['pct_alta'], 1)} % en mortalidad")
tp = MU["top"]
esta("top alto", f"cuatro tuvieron mortalidad por debajo de lo esperado y uno por encima")
cumple("top alto: 4 bajos y 1 alto", (tp["alto_n_mortalidad_baja"], tp["alto_n_mortalidad_alta"]) == (4, 1))
esta("top bajo", "ninguno tuvo mortalidad alta y cuatro hospitalizaron por habitante más que el país")
cumple("top bajo: 0 altos y 4 sobre la tasa nacional", (tp["bajo_n_mortalidad_alta"], tp["bajo_n_hosp_sobre_nacional"]) == (0, 4))
cc = MU["concentracion"]
esta("concentración", f"concentró en promedio el {f(cc['media_peso_hosp'], 1)} % de las hospitalizaciones evitables de su departamento, el {f(cc['media_peso_muertes'], 1)} % de las muertes por CSAA y el {f(cc['media_peso_pob'], 1)} % de la población, y pesó más en las hospitalizaciones que en las muertes en {cc['n_hosp_mayor_que_muertes']} de {cc['n']} departamentos")
CLS2 = {"alta": "no se publica; por encima de lo esperado", "baja": "no se publica; por debajo de lo esperado", "esperada": "no se publica; dentro de lo esperado"}
for x in leer("cuadroS2_municipios_adres.csv"):
    m_ = x["muertes_csaa75_publicable"]; m_ = m_ if m_ == "<5" else f(m_, 0)
    rm = CLS2[x["clase_eb"]] if x["rme_eb"] == "" else f"{f(x['rme_eb'], 2)} ({f(x['rme_eb_lo'], 2)}–{f(x['rme_eb_hi'], 2)})"
    esta(f"cuadro S2 {x['municipio']}", f"| {x['municipio']} | {x['departamento']} | {f(x['oe_hosp'], 3)} | {f(x['n_hecsap'], 0)} | {f(x['hosp_por_10k'], 1)} | {m_} | {rm} |")
    cumple(f"S2 {x['municipio']}: con 1 a 4 muertes no se publica la razón", (x["muertes_csaa75_publicable"] == "<5") == (x["rme_eb"] == ""))
cumple("cuadro S2 sin muertes de 1 a 4 publicadas", all(x["muertes_csaa75_publicable"] == "<5" or not (1 <= int(x["muertes_csaa75_publicable"]) <= 4) for x in leer("cuadroS2_municipios_adres.csv")))
cumple("Cundinamarca: mayor % alto ADRES con más de 4 municipios y menor % alto en mortalidad",
       max((r_ for r_ in dm.values() if int(r_["adres_n_mun"] or 0) > 4), key=lambda r_: float(r_["adres_pct_alto"]))["departamento"] == "Cundinamarca"
       and min((r_ for r_ in dm.values() if int(r_["n_mun_10"]) >= 3), key=lambda r_: float(r_["pct_alta"]))["departamento"] == "Cundinamarca")

# ── 7. cuadros: fila por fila contra los CSV ──────────────────────────────────────────────────
for x in leer("cuadro1_condiciones.csv"):
    esta(f"cuadro 1 grupo {x['grupo']}", f"| {x['grupo']} | {x['condicion']} | {f(x['muertes_menores75_anual'], 0)} | {f(x['tasa_estandarizada'])} "
         f"({ic(x['ic_inf'], x['ic_sup'])}) | {f(x['avpp_anual'], 0)} | {f(x['hospitalizaciones_2025'], 0)} | {f(x['muertes_por_mil_hosp'], 1)} |")
for x in leer("cuadro2a_colombia_sexo.csv"):
    esta(f"cuadro 2 {x['sexo']}", f"| {x['sexo'].capitalize()} | {f(x['muertes_anual'], 0)} | {f(x['pct_muertes_menores75'], 1)} | {f(x['tasa'])} ({ic(x['ic_inf'], x['ic_sup'])}) | "
         f"{f(x['avpp_anual'], 0)} | {f(x['p65'], 5)} | {f(x['p65_sin'], 5)} | {f(x['ganancia'], 5)} ({ic(x['ganancia_lo'], x['ganancia_hi'], 5)}) |")
for x in leer("cuadro2b_sensibilidad.csv"):
    esta(f"cuadro 2 {x['variante'][:30]}", f"| {x['variante']} | {f(x['tasa_colombia'])} | {f(x['spearman_departamentos'], 3)} |")
FP = {"mayor": "Mayor", "menor": "Menor", "": "Sin diferencia"}
for x in leer("cuadroS1_departamentos.csv"):
    esta(f"cuadro S1 {x['departamento']}", f"| {x['departamento']} | {f(x['muertes_trienio'], 0)} | {f(x['tasa'])} ({ic(x['ic_inf'], x['ic_sup'])}) | {FP[x['frente_al_pais']]} | "
         f"{f(x['tasa_escenario_omision'])} | {f(x['reh_2025'], 3)} | {f(x['rme_2025'], 3)} | {f(x['rme_sobre_reh'], 3)} ({ic(x['rme_sobre_reh_lo'], x['rme_sobre_reh_hi'], 3)}) |")
cumple("cuadro 1 tiene 19 filas", len(re.findall(r"^\| \d+ \| ", TXT, re.M)) == 19)
cumple("cuadros publicados sin celdas de 1 a 4 muertes",
       min(float(x["muertes_menores75_anual"]) for x in leer("cuadro1_condiciones.csv")) >= 5
       and min(float(x["muertes_trienio"]) for x in leer("cuadroS1_departamentos.csv")) >= 5)

# ── 8. figuras, revista y estilo ──────────────────────────────────────────────────────────────
for fig in re.findall(r"!\[[^\]]*\]\(\.\./(output/figuras/[^)]+)\)", TXT):
    cumple(f"existe {fig}", (RAIZ / fig).is_file())
cumple("tres figuras", len(re.findall(r"!\[Figura \d\]", TXT)) == 3)


def palabras(s):
    return len(re.findall(r"\S+", s))


cuerpo = TXT.split("## Introducción")[1].split("## Declaraciones")[0]
resumen = TXT.split("## Resumen")[1].split("**Palabras clave")[0]
titulos = re.findall(r"^# (.+)$", TXT, re.M)
cumple(f"cuerpo ≤ 3 500 palabras ({palabras(cuerpo)})", palabras(cuerpo) <= 3500)
cumple(f"resumen ≤ 250 palabras ({palabras(resumen)})", palabras(resumen) <= 250)
cumple(f"título ≤ 15 palabras ({palabras(titulos[0])})", palabras(titulos[0]) <= 15)
refs = re.findall(r"^(\d+)\. ", TXT.split("## Referencias")[1].split("## Cuadros")[0], re.M)
cumple(f"≤ 35 referencias ({len(refs)})", len(refs) <= 35)
texto_citas = TXT.split("## Referencias")[0] + TXT.split("## Cuadros")[1]
citas = []
for grupo in re.findall(r"\((\d{1,2}(?:, ?\d{1,2})*)\)", texto_citas):
    for c in re.split(r", ?", grupo):
        if int(c) not in citas and int(c) <= len(refs):
            citas.append(int(c))
cumple(f"referencias citadas en orden de aparición {citas}", citas == list(range(1, len(refs) + 1)))
cumple("sin rayas", "—" not in TXT)
prohibidas = ["Cabe ", "Es importante", "Asimismo", "No obstante", "Por otro lado", "Adicionalmente", "En conclusión", "crucial",
              "fundamental", "holístic", "potenciar", "abordar", "desafío", "panorama", "ecosistema", "sinergia", "significativ", "robust"]
for p in prohibidas:
    cumple(f"sin «{p}»", p.lower() not in TXT.lower())
cumple("autor en la hoja de presentación", "Daniel A. Garavito Jiménez" in TXT)

if fallas:
    print(f"{len(fallas)} fallas ({n_ok} comprobaciones bien):")
    for x in fallas:
        print("  -", x)
    sys.exit(1)
print(f"{n_ok} comprobaciones. Todo coincide.")
