"""Apertura de los archivos del DANE tal como vienen en los zips del Archivo Nacional de Datos.

El DANE cambió tres veces la forma de publicar los microdatos de Estadísticas Vitales:

    1979-2007   un .sav por año (defunciones) o un texto separado por tabulador (nacimientos)
    2008-2019   CSV dentro de un zip anual dentro del zip del catálogo (salvo 2012-2013: .sav y texto)
    2020-2025   un zip por año con el mismo dato en .csv, .dta y .sav

Aquí solo se abre y se lee. Ninguna función de este módulo cambia un valor: todo sale como texto (o como lo entrega
pyreadstat, en el caso de los .sav y .dta) y la armonización se hace en `defunciones.py` y `nacimientos.py`.

Código tomado sin cambios de scripts/30_base_defunciones.py (`_sav`, `_csvnest`), 37_base_nacimientos.py (`_tabla`)
y src/eevv/lectura.py, src/eevv/nombres.py (`_leer_sav`, `normalizar_columna`) del repositorio EEVV.
"""
from __future__ import annotations

import io
import os
import re
import tempfile
import unicodedata
import zipfile
from pathlib import Path

import polars as pl

# Preferencia de formato para los zips 2020-2025 (como scripts/01_extraer.py del repositorio EEVV): el .dta lee
# limpio en todos los años; algunos .sav declaran mal su codificación.
PREFERENCIA = [".dta", ".sav", ".sas7bdat", ".csv"]
CODIFICACIONES = [None, "LATIN1", "WINDOWS-1252"]


def normalizar_columna(nombre: str) -> str:
    """Nombres de columna: minúsculas, sin tildes, snake_case."""
    t = unicodedata.normalize("NFKD", str(nombre))
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower().strip()
    return re.sub(r"[^a-z0-9_]+", "_", t).strip("_")


# ── .sav dentro de un zip (defunciones 1979-2007 y 2012-2013) ─────────────────────────────────────────────────────
def sav_desde_bytes(data: bytes, cols: list[str]) -> pl.DataFrame:
    """Lee las columnas `cols` (en minúscula) de un .sav; las que no están quedan nulas. Todo como texto."""
    import pyreadstat
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "f.sav")
        with open(p, "wb") as fh:
            fh.write(data)
        del data
        _, meta = pyreadstat.read_sav(p, metadataonly=True)
        cmap = {c.lower(): c for c in meta.column_names}
        use = [cmap[c] for c in cols if c in cmap]
        df, _ = pyreadstat.read_sav(p, usecols=use)
    df.columns = [c.lower() for c in df.columns]
    for c in cols:
        if c not in df.columns:
            df[c] = None
    for c in cols:
        df[c] = df[c].astype(str).where(df[c].notna(), None)
    return pl.from_pandas(df[cols])


# ── CSV dentro de un zip dentro de un zip (defunciones 2008-2011 y 2014-2019) ─────────────────────────────────────
def csv_anidado_defunciones(ruta_zip: Path, anio: int, cols: list[str]) -> pl.DataFrame:
    with zipfile.ZipFile(ruta_zip) as z:
        inner = [n for n in z.namelist() if f"nofetal{anio}" in n.lower() and n.lower().endswith(".zip")][0]
        interno = z.read(inner)
    with zipfile.ZipFile(io.BytesIO(interno)) as z2:
        csv = [n for n in z2.namelist() if n.lower().endswith(".csv")][0]
        contenido = z2.read(csv)
    del interno
    df = pl.read_csv(io.BytesIO(contenido), infer_schema_length=0, ignore_errors=True, encoding="utf8-lossy")
    del contenido
    df = df.rename({c: c.lower() for c in df.columns})
    return df.select([pl.col(c) if c in df.columns else pl.lit(None, pl.Utf8).alias(c) for c in cols])


# ── texto o CSV de nacimientos ────────────────────────────────────────────────────────────────────────────────────
def tabla_texto(contenido: bytes) -> pl.DataFrame:
    """CSV o texto con tabulador, todo como texto, nombres en minúscula (37_base_nacimientos.py: `_tabla`)."""
    primera = contenido[:2000].split(b"\n")[0]
    sep = "\t" if primera.count(b"\t") > primera.count(b",") else ","
    # el texto con tabulador trae comillas sueltas en los nombres de las instituciones: ahí no hay comillas que respetar
    df = pl.read_csv(io.BytesIO(contenido), separator=sep, infer_schema=False, encoding="utf8-lossy",
                     quote_char=None if sep == "\t" else '"', truncate_ragged_lines=True)
    return df.rename({c: c.strip().strip('"').lower() for c in df.columns})


def miembro(ruta_zip: Path, condicion) -> bytes:
    """Bytes del primer miembro del zip cuyo nombre cumple `condicion`."""
    with zipfile.ZipFile(ruta_zip) as z:
        return z.read([n for n in z.namelist() if condicion(n)][0])


def miembro_anidado(ruta_zip: Path, cond_zip, cond_archivo) -> bytes:
    """Bytes de un archivo que está dentro de un zip que está dentro de `ruta_zip`."""
    with zipfile.ZipFile(ruta_zip) as z:
        interno = z.read([n for n in z.namelist() if cond_zip(n)][0])
    with zipfile.ZipFile(io.BytesIO(interno)) as z2:
        return z2.read([n for n in z2.namelist() if cond_archivo(n)][0])


# ── zips 2020-2025: .dta / .sav con pyreadstat (scripts/01_extraer.py y src/eevv/lectura.py del repositorio EEVV) ──
def elegir_miembro(zf: zipfile.ZipFile) -> zipfile.ZipInfo:
    for ext in PREFERENCIA:
        m = [i for i in zf.infolist() if Path(i.filename).suffix.lower() == ext and not i.is_dir() and i.file_size > 0]
        if m:
            return m[0]
    raise FileNotFoundError("el zip no trae .dta, .sav, .sas7bdat ni .csv")


def _lector(ruta: Path):
    import pyreadstat
    return {".sav": pyreadstat.read_sav, ".dta": pyreadstat.read_dta, ".sas7bdat": pyreadstat.read_sas7bdat}[ruta.suffix.lower()]


def leer_spss_stata(ruta: Path, columnas: list[str] | None = None):
    """Lee un .sav/.dta probando codificaciones hasta que una no rompa (src/eevv/lectura.py: `_leer_sav`).

    `columnas` son nombres normalizados (minúscula, sin tildes); si se dan, solo se leen esas columnas del archivo,
    lo que baja la memoria sin cambiar los valores. Devuelve (DataFrame de pandas con nombres normalizados, códec)."""
    lector = _lector(ruta)
    ultimo = None
    for enc in CODIFICACIONES:
        try:
            kw = {"disable_datetime_conversion": True}
            if enc is not None:
                kw["encoding"] = enc
            if columnas is not None:
                _, meta = lector(str(ruta), metadataonly=True, **({"encoding": enc} if enc else {}))
                cmap = {normalizar_columna(c): c for c in meta.column_names}
                kw["usecols"] = [cmap[c] for c in columnas if c in cmap]
            df, _ = lector(str(ruta), **kw)
            df.columns = [normalizar_columna(c) for c in df.columns]
            return df, (enc or "utf-8")
        except Exception as e:                                    # noqa: BLE001
            if "decode" not in str(e).lower() and not isinstance(e, UnicodeDecodeError):
                raise
            ultimo = e
    raise ultimo


def extraer_a_parquet(ruta_zip: Path, destino: Path, columnas: list[str] | None = None) -> dict:
    """Microdato de un zip 2020-2025 -> parquet (como 01_extraer.py + 02_consolidar.py del repositorio EEVV)."""
    with zipfile.ZipFile(ruta_zip) as zf:
        info = elegir_miembro(zf)
        ext = Path(info.filename).suffix.lower()
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / f"microdato{ext}"
            with zf.open(info) as fsrc, open(tmp, "wb") as fdst:
                while (buf := fsrc.read(4 << 20)):
                    fdst.write(buf)
            if ext == ".csv":
                df = pl.read_csv(tmp, infer_schema_length=0)
                df = df.rename({c: normalizar_columna(c) for c in df.columns})
                if columnas is not None:
                    df = df.select([c for c in columnas if c in df.columns])
                enc = "utf-8"
            else:
                pdf, enc = leer_spss_stata(tmp, columnas)
                df = pl.from_pandas(pdf)
                del pdf
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(destino, compression="zstd")
    return {"miembro": info.filename, "formato": ext.lstrip("."), "codificacion": enc, "filas": df.height,
            "columnas": df.width}
