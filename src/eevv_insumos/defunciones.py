"""Defunciones no fetales 1979-2025: lectura de cada año y armonización.

La armonización (mapas de grupos de edad, residencia, causa básica) es la de scripts/30_base_defunciones.py del
repositorio EEVV, copiada sin cambios; las variables adicionales son las de scripts/50_base_extendida.py.

Una fila por defunción. Columnas de residencia (las de defunciones_eevv.parquet):

    anio   año de la defunción
    dp     departamento de RESIDENCIA del fallecido (código DANE, entero; nulo si «sin información»)
    mun    municipio de residencia (código DANE de cinco cifras; 0 si no se sabe)
    sexo   1 hombre · 2 mujer · 0 indeterminado
    g      grupo de edad abreviado 0..20 (0, 1-4, 5-9, …, 90-94, 95+); -1 = edad desconocida
    g1     menores de un año: 0 de 0 a 6 días, 1 de 7 a 27 días, 2 de 28 días a 11 meses (nulo en los demás)
    area   1 cabecera · 2 centro poblado · 3 rural disperso · 0 sin dato
    cb     causa básica CIE-10 (CIE-9 hasta 1996), cuatro caracteres sin punto, en mayúsculas
    cie    9 hasta 1996, 10 desde 1997
    etnia  pertenencia étnica (idpertet)
    reg    régimen de seguridad social (seg_social)
    c667   subgrupo de la lista 6/67 que asignó el DANE (cuando el archivo lo trae)

Variables adicionales de la base extendida (def_<año>.parquet): dp_oc, mun_oc (ocurrencia), mes, sit_defun,
asis_med, idprofcer, muerteporo, nivel_edu, est_civil, emb_fal, edad_madre, peso_nac, con los códigos del DANE.

De dónde sale cada año:
    1979-1997  antiguos/Defun<año>.zip, un .sav (catálogos 396, 397 y 398)     esquema antiguo de edad (1-25)
    1998-2007  «Defunciones <año>.zip», un .sav (catálogo 366)                esquema viejo de edad (1-26)
    2008-2011  cat375_2008-2011_Defunciones.zip, CSV anidado                    esquema nuevo (0-29)
    2012-2013  cat377_2012-2013_Defunciones.zip, .sav                           esquema nuevo
    2014-2019  cat420/475/519/652/696_..._Defunciones.zip, CSV anidado          esquema nuevo
    2020-2025  zips anuales (cat732, 775, 807, 876, 878, 915): .dta o .sav,     esquema nuevo
               convertidos a data/interim/eevv/def_<año>.parquet por 01_extraer.py

El esquema viejo de edad (los .sav de 1998-2007 no traen etiquetas) se decodificó cruzando gru_ed1 con gru_ed2 y con
los conteos del primer año del esquema nuevo: 1-6 menores de un año, 7-8 de 1 a 4, 9 de 5 a 9, … 24 de 80 a 84,
25 = 85 años y más y 26 = edad desconocida. En 1998-2007 el grupo g = 18 quiere decir «85 y más».
"""
from __future__ import annotations

import glob
import zipfile

import polars as pl

from . import lectura, rutas

ANIOS = range(1979, 2026)

# grupo abreviado K=21: 0, 1-4, 5-9, …, 90-94, 95+
NUEVO = {c: 0 for c in range(0, 7)}
NUEVO.update({7: 1, 8: 1})
NUEVO.update({c: c - 7 for c in range(9, 27)})      # 9 -> 2 (5-9) … 26 -> 19 (90-94)
NUEVO.update({27: 20, 28: 20})                       # 95-99, 100+
VIEJO = {c: 0 for c in range(1, 7)}
VIEJO.update({7: 1, 8: 1})
VIEJO.update({c: c - 7 for c in range(9, 26)})      # 9 -> 2 (5-9) … 24 -> 17 (80-84), 25 (85 y más) -> 18
# 26 = edad desconocida (gru_ed2 = 7): queda fuera del mapa y toma -1
# 1979-1997 (etiquetas DDI del DANE): 01-05 menores de un año, 06 un año, 07 de 2 a 4,
# 08 de 5 a 9 … 23 de 80 a 84, 24 = 85 y más, 25 = edad desconocida
ANTIGUO = {c: 0 for c in range(1, 6)}
ANTIGUO.update({6: 1, 7: 1})
ANTIGUO.update({c: c - 6 for c in range(8, 24)})    # 8 -> 2 (5-9) … 23 -> 17 (80-84)
ANTIGUO.update({24: 18})                             # 85 y más
# menores de un año, en tres tramos: 0 = de 0 a 6 días, 1 = de 7 a 27 días, 2 = de 28 días a 11 meses. El esquema
# de 1979-1997 junta de 7 a 29 días, así que antes de 1998 el tramo es aproximado.
SUB1 = {"nuevo": {0: 0, 1: 0, 2: 0, 3: 1, 4: 2, 5: 2, 6: 2}, "viejo": {1: 0, 2: 0, 3: 1, 4: 2, 5: 2, 6: 2},
        "antiguo": {1: 0, 2: 0, 3: 1, 4: 2, 5: 2}}

COLS = ["codptore", "codmunre", "sexo", "gru_ed1", "area_res", "c_bas1", "idpertet", "seg_social", "causa_667"]
EXTRA = ["cod_dpto", "cod_munic", "mes", "sit_defun", "asis_med", "idprofcer", "muerteporo", "nivel_edu", "est_civil",
         "emb_fal", "edad_madre", "peso_nac"]
LECTURA = COLS + [c for c in EXTRA if c not in COLS]      # columnas que se leen del archivo original
BASE = ["anio", "dp", "mun", "sexo", "g", "g1", "area", "cb", "cie", "etnia", "reg", "c667"]

SAV_CAT = {2012: "cat377_2012-2013_Defunciones.zip", 2013: "cat377_2012-2013_Defunciones.zip"}
CSVNEST = {2008: "cat375_2008-2011_Defunciones.zip", 2009: "cat375_2008-2011_Defunciones.zip",
           2010: "cat375_2008-2011_Defunciones.zip", 2011: "cat375_2008-2011_Defunciones.zip",
           2014: "cat420_2014_Defunciones.zip", 2015: "cat475_2015_Defunciones.zip",
           2016: "cat519_2016_Defunciones.zip", 2017: "cat652_2017-2018_Defunciones.zip",
           2018: "cat652_2017-2018_Defunciones.zip", 2019: "cat696_2019_Defunciones.zip"}
RECIENTES = {2020: "cat732_2020_nofetal2020.zip", 2021: "cat775_2021_nofetal2021.zip",
             2022: "cat807_2022_nofetal2022.zip", 2023: "cat876_2023_BD_EEVV_Defuncionesnofetales_2023.zip",
             2024: "cat878_2024_BD_EEVV_Defuncionesnofetales_2024.zip", 2025: "cat915_2025_Defunciones.zip"}


def archivo(anio: int) -> str:
    """Nombre (relativo a data/raw/) del zip que trae el año."""
    if anio <= 1997:
        return f"antiguos/Defun{anio}.zip"
    if anio in RECIENTES:
        return RECIENTES[anio]
    if anio in SAV_CAT:
        return SAV_CAT[anio]
    if anio in CSVNEST:
        return CSVNEST[anio]
    return sorted(glob.glob(str(rutas.crudo() / f"Defunciones*{anio}.zip")))[0].rsplit("/", 1)[-1]


def intermedio(anio: int):
    return rutas.intermedio() / f"def_{anio}.parquet"


def leer(anio: int, cols: list[str] = LECTURA) -> tuple[pl.DataFrame, dict]:
    """Columnas `cols` del archivo original del año, como texto, y el mapa de grupos de edad que le corresponde."""
    crudo = rutas.crudo()
    if anio <= 1997:                                  # catálogos 396, 397 y 398: un .sav por año, CIE-9 hasta 1996
        return lectura.sav_desde_bytes(lectura.miembro(crudo / archivo(anio), lambda x: x.lower().endswith(".sav")), cols), ANTIGUO
    if anio >= 2020:
        df = pl.read_parquet(intermedio(anio)).rename(lambda c: c.lower())
        df = df.select([pl.col(c).cast(pl.Utf8) if c in df.columns else pl.lit(None, pl.Utf8).alias(c) for c in cols])
        return df, NUEVO
    if anio in SAV_CAT:
        return lectura.sav_desde_bytes(lectura.miembro(crudo / SAV_CAT[anio], lambda x: str(anio) in x and x.lower().endswith(".sav")), cols), NUEVO
    if anio in CSVNEST:
        return lectura.csv_anidado_defunciones(crudo / CSVNEST[anio], anio, cols), NUEVO
    return lectura.sav_desde_bytes(lectura.miembro(crudo / archivo(anio), lambda x: x.lower().endswith(".sav")), cols), VIEJO


def _entero(col: str) -> pl.Expr:
    # "05", "5.0", "5" -> 5 ; basura -> null
    return pl.col(col).cast(pl.Utf8).str.strip_chars().str.replace(r"\.0+$", "").cast(pl.Int64, strict=False)


def normalizar(df: pl.DataFrame, mapa: dict, anio: int) -> pl.DataFrame:
    """Columnas de residencia armonizadas (30_base_defunciones.py: `normalizar`, sin cambios)."""
    df = df.with_columns(
        _entero("codptore").alias("dp"),
        _entero("codmunre").alias("munre"),
        _entero("sexo").alias("sexo"),
        _entero("gru_ed1").alias("ge"),
        _entero("area_res").alias("area"),
        pl.col("c_bas1").cast(pl.Utf8).str.strip_chars().str.to_uppercase().str.replace_all(r"[^A-Z0-9]", "").str.slice(0, 4).alias("cb"),
        _entero("idpertet").alias("etnia"),
        _entero("seg_social").alias("reg"),
        _entero("causa_667").alias("c667"),
    )
    df = df.with_columns(
        pl.col("ge").replace_strict(mapa, default=-1).alias("g"),
        pl.col("ge").replace_strict(SUB1["antiguo" if anio <= 1997 else "viejo" if mapa is VIEJO else "nuevo"], default=None).cast(pl.Int8).alias("g1"),
        # 01 = «Sin información» en las etiquetas del DANE; en 1980-1981 Caquetá aparece con su código viejo, 83
        pl.when(pl.col("dp") == 1).then(None).when((pl.col("dp") == 83) & (anio <= 1981)).then(18).otherwise(pl.col("dp")).alias("dp"),
        pl.when(pl.col("munre").is_null()).then(0)
          .when(pl.col("munre") >= 1000).then(pl.col("munre"))           # ya viene con el departamento
          .otherwise(pl.col("dp") * 1000 + pl.col("munre")).alias("mun"),
        pl.when(pl.col("sexo").is_in([1, 2])).then(pl.col("sexo")).otherwise(0).alias("sexo"),
        pl.when(pl.col("area").is_in([1, 2, 3])).then(pl.col("area")).otherwise(0).alias("area"),
        pl.lit(anio).alias("anio"),
    )
    df = df.with_columns(pl.lit(9 if anio <= 1996 else 10).alias("cie"),
                         pl.when(pl.col("dp").is_null()).then(0).otherwise(pl.col("mun")).alias("mun"))
    return df.select(BASE).with_columns(
        pl.col("cie").cast(pl.Int8),
        pl.col("anio").cast(pl.Int16), pl.col("dp").cast(pl.Int16), pl.col("mun").cast(pl.Int32),
        pl.col("sexo").cast(pl.Int8), pl.col("g").cast(pl.Int8), pl.col("area").cast(pl.Int8),
        pl.col("etnia").cast(pl.Int8, strict=False), pl.col("reg").cast(pl.Int8, strict=False),
        pl.col("c667").cast(pl.Int16, strict=False))


# ── variables adicionales (50_base_extendida.py, sin cambios) ─────────────────────────────────────────────────────
RENOMBRE = {"cod_dpto": "dp_oc", "cod_munic": "mun_oc"}


def enteros(df: pl.DataFrame, cols: list[str]) -> pl.DataFrame:
    return df.select([
        (pl.col(c).cast(pl.Utf8).str.strip_chars().str.replace(r"\.0+$", "").cast(pl.Int64, strict=False)
         if c in df.columns else pl.lit(None, pl.Int64)).alias(RENOMBRE.get(c, c)) for c in cols])


def mun_oc(df: pl.DataFrame) -> pl.DataFrame:
    # el municipio viene con el departamento (5 cifras) o sin él (3 cifras), según el año
    return df.with_columns(
        pl.when(pl.col("mun_oc").is_null() | pl.col("dp_oc").is_null()).then(0)
          .when(pl.col("mun_oc") >= 1000).then(pl.col("mun_oc"))
          .otherwise(pl.col("dp_oc") * 1000 + pl.col("mun_oc")).cast(pl.Int32).alias("mun_oc"),
        pl.col("dp_oc").cast(pl.Int16, strict=False))


def extendida(anio: int) -> pl.DataFrame:
    """def_<año>: columnas de residencia + variables adicionales, una fila por defunción."""
    crudo, mapa = leer(anio)
    base = normalizar(crudo, mapa, anio)
    extra = mun_oc(enteros(crudo, EXTRA))
    assert base.height == extra.height
    return base.hstack(extra)


def columnas_presentes(anio: int) -> list[str]:
    """Columnas de LECTURA que trae el archivo original del año (para las pruebas de insumos)."""
    crudo = rutas.crudo()
    if anio >= 2020:
        with zipfile.ZipFile(crudo / RECIENTES[anio]) as zf:
            info = lectura.elegir_miembro(zf)
            import tempfile
            from pathlib import Path
            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td) / Path(info.filename).name
                with zf.open(info) as a, open(tmp, "wb") as b:
                    while (buf := a.read(4 << 20)):
                        b.write(buf)
                import pyreadstat
                lector = pyreadstat.read_dta if tmp.suffix.lower() == ".dta" else pyreadstat.read_sav
                _, meta = lector(str(tmp), metadataonly=True)
                nombres = {lectura.normalizar_columna(c) for c in meta.column_names}
    elif anio in CSVNEST:
        b = lectura.miembro_anidado(crudo / CSVNEST[anio], lambda n: f"nofetal{anio}" in n.lower() and n.lower().endswith(".zip"),
                                    lambda n: n.lower().endswith(".csv"))
        nombres = {c.lower() for c in pl.read_csv(b[:20000], n_rows=0, infer_schema_length=0, encoding="utf8-lossy").columns}
    else:
        import os, tempfile, pyreadstat
        cond = (lambda x: str(anio) in x and x.lower().endswith(".sav")) if anio in SAV_CAT else (lambda x: x.lower().endswith(".sav"))
        data = lectura.miembro(crudo / archivo(anio), cond)
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "f.sav")
            with open(p, "wb") as fh:
                fh.write(data)
            _, meta = pyreadstat.read_sav(p, metadataonly=True)
        nombres = {c.lower() for c in meta.column_names}
    return [c for c in LECTURA if c in nombres]
