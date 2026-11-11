# Replicación del artículo A5

## Contenido

1. Requisitos
2. Nivel A (desde los intermedios versionados)
3. Nivel B (desde los microdatos)
4. Determinismo
5. Corrida registrada

## 1. Requisitos

Python 3.13.16 con los paquetes de `requirements.txt` (`pip install -r requirements.txt`). Para los entregables, pandoc 3.1.3 y XeLaTeX (TeX Live 2023) con las fuentes FreeSerif e Inter. Memoria: 0,4 GB en el nivel A y 1,1 GB en el nivel B.

## 2. Nivel A (desde los intermedios versionados)

```
make nivel-a        # 03_estimar.py, 04_figuras.py y verificar_cifras.py
make pruebas        # pytest pruebas/ (sin insumos_eevv) y verificar_cifras.py
make manuscrito     # docx y pdf con autor y anónimos, y tablas.xlsx
```

`03_estimar.py` lee `data/intermedios/`, `config/` y `data/raw/externos/adres/` y escribe `output/`. No necesita los microdatos.

## 3. Nivel B (desde los microdatos)

```
make insumos        # baja y verifica los microdatos y proyecciones del DANE y los externos (unos 2 GB)
make bases-eevv     # bases comunes en data/processed/ (unos 10 minutos)
make pruebas-eevv   # huellas, columnas y totales contra el DANE
make intermedios    # 01_intermedios.py --salida data/interim/a5/intermedios_b
make comparar       # 02_comparar_intermedios.py: debe decir «Intermedios idénticos.»
```

Si las bases comunes ya existen en otra copia (por ejemplo, el repositorio EEVV), basta con `PROCESADO=<carpeta data/processed> RAIZ=<repositorio que tiene data/raw/poblacion/dane_mor/> make intermedios comparar`. `PROCESADO` indica dónde están las bases y `RAIZ` dónde están las tasas de mortalidad del DANE para el escenario de omisión.

## 4. Determinismo

`scripts/_entorno.py` y el `Makefile` fijan `PYTHONHASHSEED=0` y un solo hilo en polars y BLAS; las agregaciones se ordenan antes de escribir y las sumas por índice usan `np.add.at`. El Monte Carlo de P(65) usa la semilla 20261105 y 400 simulaciones. Dos corridas con semillas de hash distintas dieron salidas idénticas byte a byte.

## 5. Corrida registrada

5 de noviembre de 2026, máquina de 2 núcleos y 7 GB de RAM compartida, Linux, Python 3.13.16.

| Corrida | Dónde | Duración | Memoria máxima | Resultado |
|---|---|---|---|---|
| Nivel A | Copia limpia del repositorio, sin `output/` ni cachés (repetida el 6 de noviembre con la parte municipal) | 6,7 s | 470 MB | `verificar_cifras.py`: «261 comprobaciones. Todo coincide.»; `resultados.json`, `aps_tablero.json`, cuadros y parámetros idénticos byte a byte a los versionados |
| Nivel B (`intermedios` y `comparar`) | Misma copia, con las bases comunes del repositorio EEVV (`PROCESADO`) | 6,1 s | 1,1 GB | «Intermedios idénticos.» en los diez archivos (con `municipal_csaa.parquet`) |
| Pruebas | Repositorio | 4 s | — | `test_calculos.py` 13 pasan; `test_insumos.py` 12 pasan (con WPP 2024 descargado) |

El nivel A del artículo reproduce además, byte a byte, las salidas del estudio 43 del Termómetro de las Estadísticas Vitales en el repositorio EEVV (`output/estudios/43_mortalidad_aps/`), del que sale el cálculo.
