# Insumos del artículo A5

Una ficha por insumo propio del artículo. Los microdatos de Estadísticas Vitales y las proyecciones de población del DANE, comunes a los artículos A1–A5, están en `INSUMOS_EEVV.md`. Huellas completas en `data/raw/MANIFIESTO.csv`.

## Contenido

1. Defunciones y población del DANE
2. Informe HECSAP de la ADRES
3. World Population Prospects 2024
4. Configuración
5. Privacidad

## 1. Defunciones y población del DANE

- **Origen:** Archivo Nacional de Datos (ANDA) del DANE, catálogos de defunciones no fetales 1998–2025, y proyecciones y retroproyecciones de población con base en el censo de 2018 (actualización de julio de 2025). Detalle, URL, huellas y validación en `INSUMOS_EEVV.md`.
- **Uso en A5:** `calculo.py:contar()` clasifica la causa básica de cada defunción con la lista de CSAA, la lista OCDE/Eurostat y las marcas de sensibilidad, y agrega por año, departamento de residencia, sexo, grupo de edad y grupo de causa. Se excluyen los residentes en el exterior (código 75). `poblacion_b()` agrega la población por año, departamento, sexo y grupo de edad; `esperadas_dane()` multiplica las tasas de mortalidad del DANE de 2015–2017 (`DCD-Mor-EstSexNal-Dep-1985-2017_VP.xlsx`) por la población para el escenario de omisión.
- **Validación:** 6 218 747 defunciones de 1998 a 2025 en `data/intermedios/conteos.parquet`, igual que la base común; los totales anuales de la base común coinciden con los cuadros y boletines del DANE (`INSUMOS_EEVV.md`, tablas C y D).

## 2. Informe HECSAP de la ADRES

- **Origen:** ADRES, Innovación y Analítica (julio de 2026), *Hospitalizaciones evitables por condiciones sensibles a la Atención Primaria (HECSAP) en Colombia*, 73 páginas, publicado en la URL del manifiesto. Copia usada: la que entregó el autor el 5 de noviembre de 2026 (SHA-256 `9207d6f7…481b`), que trae un comentario de revisión al margen en la página 54. Cotejada el 5 de noviembre de 2026 con la versión publicada: las tablas usadas coinciden. El autor lideró el equipo que elaboró el informe; el conflicto está declarado en el manuscrito.
- **Archivos:** cuatro transcripciones manuales en `data/raw/externos/adres/` (ver `FUENTE.md` de esa carpeta): cuadro 5 (departamentos), cuadro 2 (20 condiciones, llevadas a los 19 grupos de la Portaria), cuadro 4 (edad de los pacientes) y figura 6 con el cuadro 1 (serie nacional).
- **Términos:** documento público de una entidad estatal; se usan cifras agregadas con cita.
- **Validación:** las 20 condiciones suman 748 212 hospitalizaciones y 8,36 billones, como el cuadro 1; el porcentaje de cada fila del cuadro 5 cuadra con sus conteos; las tasas del cuadro 5 implican la misma población del DANE 2025 del repositorio (diferencia < 0,5 %). Los grupos 1 y 17 tienen el mismo total, 12 203, en la fuente (10 823 + 1 380 en el grupo 1).
- **Inconsistencia de la fuente:** las hospitalizaciones totales del cuadro 5 suman 4 402 548 y el cuadro 1 da 3 832 336 para el país. Por eso solo se usan los conteos y tasas de hospitalizaciones evitables, que sí cuadran entre cuadros (746 822 con residencia conocida frente a 748 212).

## 2b. Tablas territoriales y municipales del informe HECSAP y DIVIPOLA

- **Archivos:** `data/raw/externos/adres/adres_hecsap_2025_oe_departamentos.csv` (tabla 6), `adres_hecsap_2025_oe_top_municipios.csv` (tablas 8 y 9), `adres_hecsap_2025_concentracion.csv` (tabla 10) y `adres_hecsap_tendencias_2019_2024.csv` (tabla 12), transcritas el 6 de noviembre de 2026 y cotejadas con el texto del PDF.
- **Validación:** cada fila de la tabla 6 suma sus municipios; la tabla suma 1 090 municipios (el texto dice 1 091). El peso del municipio principal cuadra con la tabla 5 salvo Chocó y Guainía. Detalle en `FUENTE.md` de esa carpeta.
- **Qué mide el O/E municipal de la ADRES:** composición del uso hospitalario (esperadas = total de hospitalizaciones del municipio × 19,5 %), no frecuencia por habitante.
- **DIVIPOLA:** `data/raw/externos/divipola/divipola_gdxc-w37w.csv` (datos.gov.co, CC BY-SA 4.0), para los nombres de los municipios.

## 3. World Population Prospects 2024

- **Origen:** Naciones Unidas, División de Población, `WPP2024_PopulationByAge5GroupSex_Medium.csv.gz` (URL en el manifiesto), descargado el 4 de noviembre de 2026; 29 948 947 bytes.
- **Términos:** CC BY 3.0 IGO. No se versiona por tamaño y porque basta la población estándar derivada.
- **Uso:** suma la población de 2015 de los 38 países de la OCDE por grupo quinquenal de edad: `config/poblacion_estandar_ocde2015.csv`. `pruebas/test_insumos.py` la reconstruye desde el archivo.

## 4. Configuración

| Archivo | Qué es | Fuente |
|---|---|---|
| `lista_aps_icsap2008.csv` | 19 grupos de CSAA con sus códigos CIE-10 y notas | Portaria SAS/MS 221 de 2008, transcrita en GAIS Informa n.º 18 (SES-SP, 2013); `test_calculos.py` la contrasta código por código |
| `mortalidad_evitable_ocde2022.csv` | Lista OCDE/Eurostat de mortalidad prevenible y tratable (enero de 2022) | Eurostat, *Causes of death statistics manual*, 2025, anexo H |
| `poblacion_estandar_ocde2015.csv` | Población estándar OCDE 2015 (38 países) y pesos de 0–4 a 70–74 por la población total | WPP 2024 |
| `tabla_vida_referencia.yaml` | Esperanza de vida de referencia del GBD 2019 para los AVPP | GBD 2019 Demographics Collaborators (2020); difiere de la publicada en menos de 0,01 % antes de los 75 (`test_calculos.py`) |
| `completitud_territorial.csv` | Exceso de la esperanza de vida al nacer calculada con el registro sobre la oficial del DANE (2015–2017, promedio de sexos) y clase por departamento: grave ≥ 7 años, incompleto ≥ 3 | Cubo de mortalidad del Termómetro (repositorio EEVV, `scripts/33_cubo_mortalidad.py:clases_completitud()`) |
| `causas_667.csv` | Lista 6/67 de la OPS con sus códigos | Repositorio EEVV |

## 5. Privacidad

Los intermedios y las salidas son agregados sin registros individuales. Los cuadros del manuscrito no tienen celdas de 1 a 4 defunciones (`verificar_cifras.py` lo comprueba). `codigos_csaa.csv` y los cruces con las listas 6/67 y 105 dan conteos nacionales por código o por causa de 11 años, sin geografía ni características personales.
