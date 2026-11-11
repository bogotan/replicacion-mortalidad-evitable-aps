"""Proyecciones y retroproyecciones de población del DANE con base en el CNPV 2018.

Departamental (poblacion_eevv.parquet; scripts/31_poblacion.py del repositorio EEVV, lectura sin cambios):
    PPED-AreaSexoEdadNac-1950-2017.xlsx                      1981-1984, solo el total nacional (dp = 0)
    dane_dep/DCD-area-sexo-edad-proypoblacion-dep-1985-1992.xlsx
    dane_dep/DCD-area-sexo-edad-proypoblacion-dep-1993-2004.xlsx
    dane_dep/DCD-area-sexo-edad-proypoblacion-dep-2005-2017_VP.xlsx
    dane_dep/PPED-AreaSexoEdadDep-2018-2050_VP.xlsx          2018-2025 (actualización del 30 de julio de 2025)
    Salida: anio · dp · area (1 cabecera, 2 centros poblados y rural disperso) · sexo (1, 2) · edad (0..100) · pob

Municipal (mun_pob_edad.parquet; scripts/31b_poblacion_municipal.py, misma lógica; la hoja se lee fila por fila
y la salida se escribe por partes para no pasar de unos cientos de MB de memoria):
    dane_mun/DCD-area-sexo-edad-proypoblacion-Mun-1985-1994.xlsx   (edad simple hasta 85 y más)
    dane_mun/DCD-area-sexo-edad-proypoblacion-Mun-1995-2004.xlsx
    dane_mun/DCD-area-sexo-edad-proypoblacion-Mun-2005-2017_VP.xlsx
    Mun-edad-2018-2042.xlsx  (= PPED-AreaSexoEdadMun-2018-2042_VP.xlsx, actualización del 30 de julio de 2025)
    Salida: dp, mpio (texto de cinco cifras), ano, area («Cabecera Municipal» | «Centros Poblados y Rural Disperso» |
    «Total»), edad (0..85; 85 = 85 y más), pob (hombres + mujeres)
"""
from __future__ import annotations

import re
from pathlib import Path

import polars as pl

from . import rutas

# ── departamental ─────────────────────────────────────────────────────────────────────────────────────────────────
NACIONAL = "PPED-AreaSexoEdadNac-1950-2017.xlsx"
ARCHIVOS_DEP = [(NACIONAL, range(1981, 1985)),
                ("dane_dep/DCD-area-sexo-edad-proypoblacion-dep-1985-1992.xlsx", range(1985, 1993)),
                ("dane_dep/DCD-area-sexo-edad-proypoblacion-dep-1993-2004.xlsx", range(1993, 2005)),
                ("dane_dep/DCD-area-sexo-edad-proypoblacion-dep-2005-2017_VP.xlsx", range(2005, 2018)),
                ("dane_dep/PPED-AreaSexoEdadDep-2018-2050_VP.xlsx", range(2018, 2026))]
AREA = {"cabecera": 1, "cabecera municipal": 1, "centros poblados y rural disperso": 2, "total": 0}


def leer_departamental(nombre: str, anios) -> list[tuple]:
    """31_poblacion.py: `leer`, sin cambios salvo la ruta (relativa a data/raw/poblacion/)."""
    import openpyxl
    wb = openpyxl.load_workbook(rutas.crudo() / "poblacion" / nombre, read_only=True, data_only=True)
    hoja = [s for s in wb.sheetnames if "departamental" in s.lower()] or wb.sheetnames
    ws = wb[hoja[0]]                                  # el archivo de 2025 abre con un índice
    filas = ws.iter_rows(values_only=True)
    hdr = None
    for r in filas:                                   # la cabecera es la fila que empieza con DP
        if r and str(r[0]).strip().upper() == "DP":
            hdr = [str(h).strip() if h is not None else "" for h in r]; break
    # Formato 2025 (PPED actualizado el 30-jul-2025): la edad va en una segunda
    # fila de encabezado ("Hombres 0 años", "Mujeres 100 años  y más").
    if not any(h.startswith("Hombres_") for h in hdr):
        r2 = next(filas)
        hdr = [b or a for a, b in zip(hdr, [" ".join(str(h).split()) if h is not None else "" for h in r2])]
    idx = {h: i for i, h in enumerate(hdr)}

    def col(sexo, a):
        for h, i in idx.items():
            if (h == f"{sexo}_{a}" or h.startswith(f"{sexo}_{a} ")
                    or h in (f"{sexo} {a} años", f"{sexo} {a} año", f"{sexo} {a} años y más")):
                return i
        raise KeyError(f"{sexo}_{a} en {nombre}")
    H = [col("Hombres", a) for a in range(101)]; M = [col("Mujeres", a) for a in range(101)]
    iDP, iA, iAR = idx["DP"], idx["AÑO"], idx["ÁREA GEOGRÁFICA"]
    out = []
    for r in filas:
        if not r or r[iDP] is None or r[iA] is None:
            continue
        anio = int(r[iA])
        if anio not in anios:
            continue
        ar = AREA.get(str(r[iAR]).strip().lower())
        if ar is None:
            continue
        dp = int(str(r[iDP]).strip())
        for a in range(101):
            out.append((anio, dp, ar, 1, a, float(r[H[a]] or 0)))
            out.append((anio, dp, ar, 2, a, float(r[M[a]] or 0)))
    wb.close()
    return out


def departamental() -> tuple[pl.DataFrame, dict]:
    """poblacion_eevv con los dos controles de 31_poblacion.py. Devuelve (tabla, controles)."""
    filas = []
    for nombre, anios in ARCHIVOS_DEP:
        filas += leer_departamental(nombre, set(anios))
        print(f"  {nombre} ok", flush=True)
    df = pl.DataFrame(filas, schema=["anio", "dp", "area", "sexo", "edad", "pob"], orient="row")
    del filas
    tot = df.filter(pl.col("area") == 0).group_by(["anio", "dp"]).agg(pl.col("pob").sum().alias("t"))
    sum_ar = df.filter(pl.col("area") > 0).group_by(["anio", "dp"]).agg(pl.col("pob").sum().alias("s"))
    chk = tot.join(sum_ar, on=["anio", "dp"])
    dif = float((chk["t"] - chk["s"]).abs().max())
    assert dif < 5, "las áreas no suman al total"
    df = df.filter(pl.col("area") > 0).with_columns(
        pl.col("anio").cast(pl.Int16), pl.col("dp").cast(pl.Int16), pl.col("area").cast(pl.Int8),
        pl.col("sexo").cast(pl.Int8), pl.col("edad").cast(pl.Int8))
    # control: el total nacional de 1985 a 1992 sale igual sumando departamentos que en la serie nacional
    nac = pl.DataFrame(leer_departamental(NACIONAL, set(range(1985, 1993))), schema=["anio", "dp", "area", "sexo", "edad", "pob"], orient="row")
    a = nac.filter(pl.col("area") > 0).group_by("anio").agg(pl.col("pob").sum().alias("nac"))
    b = df.filter((pl.col("anio").is_between(1985, 1992)) & (pl.col("dp") > 0)).group_by("anio").agg(pl.col("pob").sum().alias("dep"))
    c = a.join(b.with_columns(pl.col("anio").cast(pl.Int64)), on="anio").with_columns(((pl.col("dep") - pl.col("nac")) / pl.col("nac")).alias("dif"))
    assert c["dif"].abs().max() < 1e-3, "la suma departamental no cuadra con la serie nacional"
    return df, {"max_dif_total_vs_areas_personas": dif, "max_dif_rel_dep_vs_nacional_1985_1992": float(c["dif"].abs().max())}


# ── municipal ─────────────────────────────────────────────────────────────────────────────────────────────────────
FUENTES_MUN = [("dane_mun/DCD-area-sexo-edad-proypoblacion-Mun-1985-1994.xlsx", None, range(1985, 1995)),
               ("dane_mun/DCD-area-sexo-edad-proypoblacion-Mun-1995-2004.xlsx", None, range(1995, 2005)),
               ("dane_mun/DCD-area-sexo-edad-proypoblacion-Mun-2005-2017_VP.xlsx", None, range(2005, 2018)),
               ("Mun-edad-2018-2042.xlsx", "PobMunicipalxÁreaSexoEdad", range(2018, 2026))]
ESQUEMA_MUN = {"dp": pl.Utf8, "mpio": pl.Utf8, "ano": pl.Int64, "area": pl.Utf8, "edad": pl.Int64, "pob": pl.Float64}


def _a_tabla(reg: list[tuple]) -> pl.DataFrame:
    return pl.DataFrame(reg, schema=ESQUEMA_MUN, orient="row").with_columns(pl.col("ano").cast(pl.Int32), pl.col("edad").cast(pl.Int16))


def leer_municipal(rel: str, hoja: str | None, anios, lote: int = 400_000):
    """31b_poblacion_municipal.py: `leer`, recorriendo la hoja fila por fila. Entrega tablas de hasta `lote` filas.

    31b leía la hoja entera con python-calamine (`to_python`); con el archivo 2018-2042 eso pasa de 1,8 GB de memoria.
    Aquí se lee con openpyxl en modo de solo lectura, que recorre el XML sin cargarlo: unos 50 MB y unos minutos.
    Las celdas vacías llegan como None en vez de «''» y los números enteros como int en vez de float; la lógica de
    31b ya los trata igual (`str(x or "")`, `float(x or 0)`, `int(float(x))`)."""
    import openpyxl
    wb = openpyxl.load_workbook(rutas.crudo() / "poblacion" / rel, read_only=True, data_only=True)
    it = wb[hoja or wb.sheetnames[-1]].iter_rows(values_only=True)
    for f in it:
        if f and str(f[0]).strip() == "DP":
            fila0 = f
            break
    cab = [str(x or "").strip() for x in fila0]
    # el archivo de 2018-2042 trae la edad en una segunda fila de encabezado
    if not any(re.match(r"Hombres[ _]\d", c) for c in cab):
        cab = [str(b or a).strip() for a, b in zip(fila0, next(it))]
    col = {"Hombres": {}, "Mujeres": {}}
    for j, t in enumerate(cab):
        m = re.match(r"(Hombres|Mujeres)[ _](\d+)", t)
        if m:
            col[m.group(1)][min(int(m.group(2)), 85)] = col[m.group(1)].get(min(int(m.group(2)), 85), []) + [j]
    assert sorted(col["Hombres"]) == list(range(86)), f"edades inesperadas en {rel}"
    iA, iAR = cab.index("AÑO"), cab.index("ÁREA GEOGRÁFICA")
    reg = []
    for f in it:
        if not f or not str(f[0]).strip().isdigit():
            continue
        anio = int(float(f[iA]))
        if anio not in anios:
            continue
        # el código municipal es la columna de cinco cifras (en 2005-2017 DPMP y MPIO vienen cruzados)
        mpio = next(str(f[j]).strip() for j in (2, 3) if re.fullmatch(r"\d{5}", str(f[j]).strip()))
        for e in range(86):
            reg.append((str(f[0]).strip().zfill(2), mpio, anio, str(f[iAR]).strip(), e,
                        sum(float(f[j] or 0) for s in ("Hombres", "Mujeres") for j in col[s][e])))
        if len(reg) >= lote:
            yield _a_tabla(reg)
            reg = []
    if reg:
        yield _a_tabla(reg)
    wb.close()


def municipal(salida: Path, dep: pl.DataFrame) -> dict:
    """Escribe mun_pob_edad.parquet por partes y controla, año por año, que el total municipal cuadre con el
    departamental (tolerancia relativa 1e-4, la de 31b_poblacion_municipal.py)."""
    import pyarrow.parquet as pq
    salida.parent.mkdir(parents=True, exist_ok=True)
    tmp = salida.with_suffix(".parquet.part")
    escritor, filas, tot = None, 0, {}
    try:
        for rel, hoja, anios in FUENTES_MUN:
            n0 = filas
            for t in leer_municipal(rel, hoja, set(anios)):
                for anio, p in t.filter(pl.col("area") == "Total").group_by("ano").agg(pl.col("pob").sum()).iter_rows():
                    tot[anio] = tot.get(anio, 0.0) + p
                a = t.to_arrow()
                if escritor is None:
                    escritor = pq.ParquetWriter(tmp, a.schema, compression="zstd")
                escritor.write_table(a)
                filas += t.height
            print(f"  {rel} ok {filas - n0}", flush=True)
    finally:
        if escritor is not None:
            escritor.close()
    control = {}
    d = dep.filter(pl.col("dp") > 0).group_by("anio").agg(pl.col("pob").sum()).sort("anio")
    qd = dict(d.iter_rows())
    for anio in sorted(tot):
        q = qd[anio]
        control[anio] = (tot[anio], q, (tot[anio] - q) / q)
        assert abs(tot[anio] - q) / q < 1e-4, "la suma municipal no cuadra con la departamental"
    tmp.replace(salida)
    return {"filas": filas, "control_anual": control}
