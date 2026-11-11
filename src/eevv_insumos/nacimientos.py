"""Nacidos vivos 1998-2025: lectura de cada año y armonización.

La armonización es la de scripts/37_base_nacimientos.py del repositorio EEVV, copiada sin cambios; las variables
adicionales son las de scripts/50_base_extendida.py. Se cuenta, como el DANE, por departamento y municipio de
residencia de la madre.

Columnas de nac_<año>.parquet:
    anio, dp (residencia de la madre; nulo si «sin información»; 75 = exterior), mun, area (1 cabecera, 2 centro
    poblado, 3 rural disperso, 0 sin dato), sexo (1, 2; 0 sin dato), edad_madre, peso_nac, t_ges, numconsul,
    tipo_parto, mul_parto, sit_parto, aten_par, reg (seg_social), etnia (idpertet), t_ges_cie (t_ges_agru_cie),
    pais_madre (codpaisnacmad), n_hijosv
    y además dp_oc, mun_oc (ocurrencia del parto), mes, edad_padre, niv_edum, niv_edup, est_civm, n_emb, codpres,
    idclasadmi. Los códigos quedan como los publica el DANE en cada año.

Archivos (data/raw/):
    1998-2007  «Nacimientos <año>.zip» / «Nacimientos_<año>.zip»      texto separado por tabulador (catálogo 366)
    2008-2011  cat375_2008-2011_Nacidos.zip                           CSV dentro de un zip por año
    2012-2013  cat377_2012-2013_Nacidos_vivos_txt.zip                 texto separado por tabulador
    2014-2019  cat420/475/519/652/696_..._Nacimientos.zip             CSV dentro de un zip por año
    2020-2024  cat732/775/807/876/878_...zip                          CSV
    2025       BD-EEVV-Nacimientos-2025.zip                           CSV (catálogo 915)
"""
from __future__ import annotations

import glob

import polars as pl

from . import lectura, rutas
from .defunciones import mun_oc, enteros

ANIOS = range(1998, 2026)

COLS = {"codptore": "dp", "codmunre": "munre", "area_res": "area", "sexo": "sexo", "edad_madre": "edad_madre",
        "peso_nac": "peso_nac", "t_ges": "t_ges", "numconsul": "numconsul", "tipo_parto": "tipo_parto",
        "mul_parto": "mul_parto", "sit_parto": "sit_parto", "aten_par": "aten_par", "seg_social": "reg", "idpertet": "etnia",
        "t_ges_agru_cie": "t_ges_cie", "codpaisnacmad": "pais_madre", "n_hijosv": "n_hijosv"}
EXTRA = ["cod_dpto", "cod_munic", "mes", "edad_padre", "niv_edum", "niv_edup", "est_civm", "n_emb", "codpres", "idclasadmi"]
ANIDADOS = {2008: "cat375_2008-2011_Nacidos.zip", 2009: "cat375_2008-2011_Nacidos.zip", 2010: "cat375_2008-2011_Nacidos.zip",
            2011: "cat375_2008-2011_Nacidos.zip", 2014: "cat420_2014_Nacimientos.zip", 2015: "cat475_2015_Nacimientos.zip",
            2016: "cat519_2016_Nacimientos.zip", 2017: "cat652_2017-2018_Nacimientos.zip", 2018: "cat652_2017-2018_Nacimientos.zip",
            2019: "cat696_2019_Nacimientos.zip"}
DIRECTOS = {2020: "cat732_2020_nac2020.zip", 2021: "cat775_2021_nacimientos2021.zip", 2022: "cat807_2022_nac2022.zip",
            2023: "cat876_2023_BD_EEVV_Nacimientos_2023.zip", 2024: "cat878_2024_BD_EEVV_Nacimientos_2024.zip",
            2025: "BD-EEVV-Nacimientos-2025.zip"}
TXT_2012_2013 = "cat377_2012-2013_Nacidos_vivos_txt.zip"


def archivo(anio: int) -> str:
    if anio <= 2007:
        return sorted(glob.glob(str(rutas.crudo() / f"Nacimientos*{anio}.zip")))[0].rsplit("/", 1)[-1]
    if anio in (2012, 2013):
        return TXT_2012_2013
    return ANIDADOS.get(anio) or DIRECTOS[anio]


def contenido(anio: int) -> bytes:
    """Bytes del archivo de datos del año, tal como viene en el zip."""
    z = rutas.crudo() / archivo(anio)
    if anio <= 2007:
        return lectura.miembro(z, lambda n: n.lower().endswith(".txt"))
    if anio in (2012, 2013):
        return lectura.miembro(z, lambda n: n.endswith(f"Nac_{anio}.txt"))
    if anio in ANIDADOS:
        return lectura.miembro_anidado(z, lambda n: n.lower().endswith(f"nac{anio}.zip"), lambda n: n.lower().endswith(".csv"))
    return lectura.miembro(z, lambda n: n.lower().endswith(".csv"))


def crudo(anio: int) -> pl.DataFrame:
    return lectura.tabla_texto(contenido(anio))


def entero(c: str) -> pl.Expr:
    return pl.col(c).cast(pl.Utf8).str.strip_chars().str.replace(r"\.0+$", "").cast(pl.Int64, strict=False)


def normalizar(df: pl.DataFrame, anio: int) -> pl.DataFrame:
    """37_base_nacimientos.py: `normalizar`, sin cambios."""
    df = df.select([entero(c).alias(n) if c in df.columns else pl.lit(None, pl.Int64).alias(n) for c, n in COLS.items()])
    return df.with_columns(
        pl.lit(anio).cast(pl.Int16).alias("anio"),
        # 01 y 00 = sin información; 75 = residente en el exterior (se cuenta en el total, en ningún departamento)
        pl.when(pl.col("dp").is_in([0, 1]) | pl.col("dp").is_null()).then(None).otherwise(pl.col("dp")).cast(pl.Int16).alias("dp"),
        pl.when(pl.col("sexo").is_in([1, 2])).then(pl.col("sexo")).otherwise(0).cast(pl.Int8).alias("sexo"),
        pl.when(pl.col("area").is_in([1, 2, 3])).then(pl.col("area")).otherwise(0).cast(pl.Int8).alias("area"),
    ).with_columns(
        pl.when(pl.col("dp").is_null() | pl.col("munre").is_null()).then(0)
          .when(pl.col("munre") >= 1000).then(pl.col("munre"))
          .otherwise(pl.col("dp").cast(pl.Int32) * 1000 + pl.col("munre")).cast(pl.Int32).alias("mun"),
    ).select(["anio", "dp", "mun", "area", "sexo", "edad_madre", "peso_nac", "t_ges", "numconsul", "tipo_parto",
              "mul_parto", "sit_parto", "aten_par", "reg", "etnia", "t_ges_cie", "pais_madre", "n_hijosv"])


def extendida(anio: int) -> pl.DataFrame:
    """nac_<año>: columnas de residencia + variables adicionales, una fila por nacido vivo."""
    df = crudo(anio)
    base = normalizar(df, anio)
    extra = mun_oc(enteros(df, EXTRA))
    assert base.height == extra.height
    return base.hstack(extra)


def columnas_presentes(anio: int) -> list[str]:
    """Columnas de COLS y EXTRA que trae el archivo original del año (para las pruebas de insumos)."""
    b = contenido(anio)
    cab = b[:20000].split(b"\n")[0].decode("latin-1")
    sep = "\t" if cab.count("\t") > cab.count(",") else ","
    nombres = {c.strip().strip('"').strip().lower() for c in cab.rstrip("\r").split(sep)}
    return [c for c in list(COLS) + EXTRA if c in nombres]
