# Reconstrucción en limpio

Registro de la corrida que reconstruyó todas las bases desde los archivos originales del DANE, en una carpeta nueva, y las comparó con las del repositorio EEVV.

## Contenido

1. Resultado
2. Cómo se hizo
3. Tiempos y memoria
4. Comparación archivo por archivo
5. Qué cambió frente al código del repositorio EEVV
6. Advertencias que aparecen al correr
7. Cómo repetirla

## 1. Resultado

Los 78 archivos que produce el paquete son idénticos a los de `eevv-repo/data/processed/`: mismas columnas en el mismo orden, mismos tipos, mismo número de filas y mismos valores, en el mismo orden de filas. No hizo falta ordenar para que coincidieran y no hay diferencias de coma flotante. Las 234 pruebas de `pruebas/test_insumos_eevv.py` pasaron.

## 2. Cómo se hizo

- **Fecha:** 29 de octubre de 2026, de 21:14 a 21:24 (hora UTC).
- **Máquina:** 2 núcleos (Intel Xeon a 2,1 GHz), 7,8 GB de RAM compartidos con otros cuatro procesos, Linux. Todo con `nice -n 10`.
- **Programas:** Python 3.13.16 y las versiones de `requirements.txt` (polars 2.0.0, pyarrow 26.0.0, pyreadstat 1.3.6, pandas 3.0.5, openpyxl 3.1.5, python-calamine 0.9.0, pytest 9.2.0).
- **Carpeta:** una carpeta nueva fuera de cualquier repositorio, con solo `src/`, `scripts/`, `pruebas/`, `Makefile`, `requirements.txt` y `data/raw/MANIFIESTO.csv` copiados de `_comun/`. Sin `data/interim/`, sin `data/processed/`, sin `__pycache__`.
- **Insumos:**
  - 60 zips de microdatos: enlaces simbólicos, de solo lectura, a las copias de `eevv-repo/data/raw/`. No se modificó ninguno; `00_descargar_microdatos.py` verificó su huella.
  - 5 zips de defunciones 2020-2024 (catálogos 732, 775, 807, 876 y 878): no estaban en `eevv-repo/data/raw/`. Los bajó `00_descargar_microdatos.py` del ANDA y coincidieron con la huella del manifiesto.
  - 13 archivos de población y estimaciones demográficas: los bajó `00_descargar_microdatos.py` de www.dane.gov.co. Todos tienen la misma huella que la copia del repositorio EEVV (los 11 que estaban allí) o la registrada en el manifiesto (los 2 totales nacionales de referencia).
  - `poblacion/Mun-2020-2035.xlsx`: enlace a la copia del repositorio EEVV (no tiene URL pública; ver `docs/INSUMOS.md`, 3.6).
- **Orden:** `00` → `01` → `02` → `03` → `04` → pruebas → `05_comparar.py --referencia eevv-repo/data/processed`.

Antes de esta corrida hubo una de prueba en otra carpeta nueva. En ella `04_poblacion.py` leía la población municipal con python-calamine, como el script 31b original, y llegó a 2.052 MB de memoria, por encima del límite de 2 GB. Se cambió la lectura (sección 5) y se repitió todo desde cero.

## 3. Tiempos y memoria

Memoria: pico del conjunto residente (RSS) del proceso, medido con `scripts/medir.py`.

| Paso | Segundos | Memoria máxima (MB) |
|---|---|---|
| `00_descargar_microdatos.py` (18 descargas, 79 huellas) | 81 | 39 |
| `01_extraer.py` (defunciones 2020-2025) | 12 | 402 |
| `02_base_defunciones.py` (47 años y apilado) | 65 | 666 |
| `03_base_nacimientos.py` (28 años) | 66 | 932 |
| `04_poblacion.py` (departamental y municipal) | 293 | 491 |
| `pytest pruebas/` (234 pruebas) | 51 | 429 |
| `05_comparar.py` (78 archivos) | 35 | 343 |
| **Total** | **604** | **932** |

Sin la descarga, construir las bases toma unos 7 minutos. El paso más lento es la población municipal (unos 5 minutos), porque se recorren fila por fila unos 195.000 renglones de Excel con más de 250 columnas cada uno. Las bases ocupan 225 MB y el intermedio 15 MB.

## 4. Comparación archivo por archivo

`05_comparar.py` compara cada archivo nuevo con el del repositorio EEVV: nombres y orden de columnas, tipos, número de filas y valores fila por fila en el orden en que están (y, si eso fallara, después de ordenar por todas las columnas). Las dos tablas grandes se comparan año por año y, además, en tramos de un millón de filas para comprobar el orden global.

| Archivo | Filas | Resultado |
|---|---|---|
| `ext/def_1979.parquet` … `ext/def_2025.parquet` (47) | 9.109.285 | idénticos los 47 |
| `ext/nac_1998.parquet` … `ext/nac_2025.parquet` (28) | 18.450.346 | idénticos los 28 |
| `defunciones_eevv.parquet` | 9.109.285 | idéntico en los 47 años y en el orden global |
| `poblacion_eevv.parquet` | 548.228 | idéntico |
| `mun_pob_edad.parquet` | 11.870.580 | idéntico en los 41 años y en el orden global |

El detalle queda en `data/interim/eevv/comparacion.json` de la carpeta donde se corra.

## 5. Qué cambió frente al código del repositorio EEVV

La armonización (mapas de edad, residencia, causa, códigos de departamento) se copió sin cambios. Cambió la forma de leer y de escribir:

1. **Rutas.** Todo es relativo a una raíz (`--raiz`, variable `RAIZ` o la carpeta que contiene `src/eevv_insumos/`). El original fijaba la raíz con `Path(__file__).parents[1]` en cada script.
2. **Defunciones 2020-2025.** El original leía `data/processed/defunciones_no_fetales/<año>.parquet`, hechos antes con `00_descargar.py` → `01_extraer.py` → `02_consolidar.py` (todas las columnas). El de 2025 no tenía diccionario y su origen no estaba documentado. Ahora `01_extraer.py` toma el .dta (o el .sav) del zip y lee solo las 21 columnas que se usan. Los valores son los mismos, también en 2025.
3. **Una sola lectura por año.** El original leía cada zip dos veces: una en `30_base_defunciones.py`/`37_base_nacimientos.py` y otra en `50_base_extendida.py`. Ahora se lee una vez, se escribe `def_<año>`/`nac_<año>`, y `defunciones_eevv.parquet` se arma apilando las 12 columnas de residencia de los `def_<año>`, escribiendo año por año. Así ninguna etapa tiene en memoria más de un año de microdato.
4. **Población municipal.** El 31b original cargaba cada hoja entera con python-calamine (`to_python`); con `Mun-edad-2018-2042.xlsx` eso pasa de 1,8 GB. Ahora se recorre con openpyxl en modo de solo lectura y la salida se escribe por partes de 400.000 filas. La lógica de 31b (qué fila es el encabezado, qué columna es el municipio, cómo se suman hombres y mujeres) es la misma. Cuesta más tiempo (unos 290 s frente a unos 55 s) y baja el pico de memoria de 2.052 MB a 491 MB.
5. **Sin pasos que el artículo no usa.** No se producen `nacimientos_eevv.parquet`, las series apiladas `serie_*.parquet` ni las defunciones fetales, que ninguno de los cuatro artículos lee.

## 6. Advertencias que aparecen al correr

Al leer los CSV anidados de defunciones de 2011, 2014 y 2015, polars avisa «CSV malformed: expected … rows, actual … rows». Es un aviso del lector en paralelo sobre el tamaño de los tramos que estimó; se lee con `ignore_errors=True`, igual que en el original, y el número de filas de cada año coincide con el total publicado por el DANE. No cambia ningún valor (la comparación de la sección 4 lo confirma).

## 7. Cómo repetirla

```bash
# en una carpeta nueva con src/, scripts/, pruebas/, requirements.txt y data/raw/MANIFIESTO.csv
pip install -r requirements.txt
python scripts/medir.py tiempos.tsv 00 -- python scripts/00_descargar_microdatos.py
python scripts/medir.py tiempos.tsv 01 -- python scripts/01_extraer.py
python scripts/medir.py tiempos.tsv 02 -- python scripts/02_base_defunciones.py
python scripts/medir.py tiempos.tsv 03 -- python scripts/03_base_nacimientos.py
python scripts/medir.py tiempos.tsv 04 -- python scripts/04_poblacion.py
python -m pytest pruebas/ -q
python scripts/05_comparar.py --referencia <carpeta processed de referencia>
```

Para no volver a bajar 2,5 GB se pueden enlazar los zips de otra copia en `data/raw/` con los mismos nombres; `00_descargar_microdatos.py` los verifica por su huella y baja solo lo que falte.
