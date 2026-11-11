# Datos del artículo A5

| Carpeta | Qué tiene | Cómo se produce | ¿Versionado? |
|---|---|---|---|
| `raw/MANIFIESTO.csv` | Una fila por insumo: fuente, URL, fecha, tamaño, SHA-256, licencia y uso | A mano; `scripts/00_descargar_insumos.py` lo verifica | Sí |
| `raw/externos/adres/` | Cuatro transcripciones del informe HECSAP de la ADRES (cuadros 1, 2, 4 y 5 y figura 6) y `FUENTE.md` | Transcripción manual, verificada por `pruebas/test_insumos.py` y `test_calculos.py` | Sí (el PDF no) |
| `raw/externos/wpp2024/` | *World Population Prospects 2024*, población por edad quinquenal | `make insumos` | No |
| `raw/` (resto) | Microdatos de Estadísticas Vitales y proyecciones de población del DANE | `make insumos` | No |
| `processed/` | Bases comunes de Estadísticas Vitales (una fila por defunción) | `make bases-eevv` | No |
| `intermedios/` | Conteos agregados de defunciones por año, departamento, sexo, edad y causa; poblaciones; códigos observados y su clasificación; muertes esperadas del DANE 2015–2017; cruces con las listas 6/67 y 105 | `make intermedios` (nivel B) | Sí (1,3 MB) |
| `interim/` | Intermedios reconstruidos para comparar con los versionados | `make intermedios` | No |

Las variables de `intermedios/` están en `docs/DICCIONARIO.md`.
