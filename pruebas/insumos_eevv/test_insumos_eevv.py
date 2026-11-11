"""Pruebas de los insumos de Estadísticas Vitales (EEVV) y de las bases que se construyen con ellos.

    pytest pruebas/test_insumos_eevv.py            (desde la raíz; RAIZ o --raiz no hacen falta)

1. Huellas: cada archivo de data/raw/MANIFIESTO.csv (grupo «eevv») existe y tiene el tamaño y la huella SHA-256
   registrados. Falla si el DANE cambió un archivo o si falta uno (corra scripts/00_descargar_microdatos.py).
2. Columnas: para cada año, el archivo original trae las columnas que el código lee
   (pruebas/columnas_esperadas.json). Falla si el DANE agrega o quita una de esas columnas.
3. Totales de registros: filas de data/processed/ext/nac_<año>.parquet y def_<año>.parquet (una fila por evento,
   sin filtros) frente a los nacidos vivos y las defunciones no fetales publicados por el DANE
   (pruebas/totales_publicados_dane.csv: cuadros definitivos 1979-2015 y boletín técnico de septiembre de 2026 para
   2016-2025). Tolerancia: 0 registros. Los cuadros del DANE se tabulan del mismo archivo definitivo que se publica
   en el Archivo Nacional de Datos; cualquier diferencia indica otra versión del archivo, no un redondeo.
4. Población: total de poblacion_eevv.parquet y de mun_pob_edad.parquet (área «Total») por año frente al total
   nacional que el DANE publica por separado (PPED-AreaNac-1950-2017.xlsx y PPED-AreaNac-2018-2070.xlsx).
   Tolerancia: 1 persona por año. Los totales publicados son enteros y las bases suman enteros guardados como
   decimales; 1 persona cubre el error de coma flotante de sumar unos 200.000 valores, nada más.

Las pruebas 3 y 4 necesitan las bases ya construidas (scripts 01 a 04); si faltan, se omiten con un aviso.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import polars as pl
import pytest

_SRC = next(p / "src" for p in Path(__file__).resolve().parents if (p / "src" / "eevv_insumos").is_dir())
sys.path.insert(0, str(_SRC))
from eevv_insumos import defunciones, manifiesto, nacimientos, rutas  # noqa: E402

AQUI = Path(__file__).resolve().parent
TOL_REGISTROS = 0
TOL_PERSONAS = 1.0
FILAS = manifiesto.leer()


# ── 1. huellas ────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("fila", FILAS, ids=[f["archivo"] for f in FILAS])
def test_huella(fila):
    ok, msg = manifiesto.verificar(fila)
    assert ok, f"{fila['archivo']}: {msg}. Corra scripts/00_descargar_microdatos.py"


def test_manifiesto_completo():
    """Cada zip que lee el código tiene su fila en el manifiesto."""
    en_manifiesto = {f["archivo"] for f in FILAS}
    usados = {defunciones.archivo(a) for a in defunciones.ANIOS} | {nacimientos.archivo(a) for a in nacimientos.ANIOS}
    faltan = usados - en_manifiesto
    assert not faltan, f"archivos usados sin fila en el manifiesto: {sorted(faltan)}"


# ── 2. columnas ───────────────────────────────────────────────────────────────────────────────────────────────────
ESPERADAS = json.loads((AQUI / "columnas_esperadas.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("anio", list(defunciones.ANIOS))
def test_columnas_defunciones(anio):
    assert defunciones.columnas_presentes(anio) == ESPERADAS["defunciones_no_fetales"][str(anio)]


@pytest.mark.parametrize("anio", list(nacimientos.ANIOS))
def test_columnas_nacimientos(anio):
    assert nacimientos.columnas_presentes(anio) == ESPERADAS["nacimientos"][str(anio)]


# ── 3. totales de registros ───────────────────────────────────────────────────────────────────────────────────────
PUBLICADOS = list(csv.DictReader(open(AQUI / "totales_publicados_dane.csv", encoding="utf-8")))


def _filas(tipo: str, anio: int) -> int:
    import pyarrow.parquet as pq
    p = rutas.ext() / f"{'nac' if tipo == 'nacimientos' else 'def'}_{anio}.parquet"
    if not p.exists():
        pytest.skip(f"falta {rutas.relativa(p)}: corra los scripts 01 a 03")
    return pq.ParquetFile(p).metadata.num_rows


@pytest.mark.parametrize("pub", PUBLICADOS, ids=[f"{p['tipo']}-{p['anio']}" for p in PUBLICADOS])
def test_total_registros(pub):
    n = _filas(pub["tipo"], int(pub["anio"]))
    assert abs(n - int(pub["total_publicado"])) <= TOL_REGISTROS, \
        f"{pub['tipo']} {pub['anio']}: base {n}, DANE {pub['total_publicado']} ({pub['documento']})"


def test_totales_cubren_la_serie():
    anios = {(p["tipo"], int(p["anio"])) for p in PUBLICADOS}
    assert {("defunciones_no_fetales", a) for a in defunciones.ANIOS} <= anios
    assert {("nacimientos", a) for a in nacimientos.ANIOS} <= anios


def test_defunciones_eevv_apila_def():
    """defunciones_eevv.parquet tiene, año por año, las mismas filas que def_<año>.parquet."""
    p = rutas.procesado() / "defunciones_eevv.parquet"
    if not p.exists():
        pytest.skip("falta defunciones_eevv.parquet")
    n = dict(pl.scan_parquet(p).group_by("anio").len().collect().iter_rows())
    for a in defunciones.ANIOS:
        assert n.get(a) == _filas("defunciones_no_fetales", a), a


# ── 4. población ──────────────────────────────────────────────────────────────────────────────────────────────────
def _nacional_publicado() -> dict[int, float]:
    from python_calamine import CalamineWorkbook
    out = {}
    for f, ia, iar, itot in (("PPED-AreaNac-1950-2017.xlsx", 2, 3, 4), ("PPED-AreaNac-2018-2070.xlsx", 1, 2, 3)):
        wb = CalamineWorkbook.from_path(str(rutas.crudo() / "poblacion" / "referencia" / f))
        for r in wb.get_sheet_by_name(wb.sheet_names[-1]).to_python():
            if len(r) > itot and str(r[iar]).strip() == "Total" and isinstance(r[ia], (int, float)):
                out[int(r[ia])] = float(r[itot])
    return out


def test_poblacion_departamental_total_nacional():
    p = rutas.procesado() / "poblacion_eevv.parquet"
    if not p.exists():
        pytest.skip("falta poblacion_eevv.parquet: corra scripts/04_poblacion.py")
    pub = _nacional_publicado()
    tot = dict(pl.read_parquet(p).group_by("anio").agg(pl.col("pob").sum()).iter_rows())
    assert sorted(tot) == list(range(1981, 2026))
    malos = {a: (t, pub[a]) for a, t in tot.items() if abs(t - pub[a]) > TOL_PERSONAS}
    assert not malos, malos


def test_poblacion_municipal_total_nacional():
    p = rutas.procesado() / "mun_pob_edad.parquet"
    if not p.exists():
        pytest.skip("falta mun_pob_edad.parquet: corra scripts/04_poblacion.py")
    pub = _nacional_publicado()
    tot = dict(pl.scan_parquet(p).filter(pl.col("area") == "Total").group_by("ano").agg(pl.col("pob").sum()).collect().iter_rows())
    assert sorted(tot) == list(range(1985, 2026))
    malos = {a: (t, pub[a]) for a, t in tot.items() if abs(t - pub[a]) > TOL_PERSONAS}
    assert not malos, malos
