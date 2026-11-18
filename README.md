# Mortalidad por condiciones sensibles a la atención primaria en Colombia, 1998–2025

Repositorio de replicación del artículo A5. Autor: Daniel A. Garavito Jiménez (Sinergística, Bogotá).

**Estado.** Artículo de Daniel A. Garavito Jiménez (Sinergística S.A.S., ORCID 0009-0009-6871-5807), enviado a la *Revista Panamericana de Salud Pública* en noviembre de 2026. El texto del artículo y sus entregables se agregan a este repositorio cuando se publique; mientras tanto, el código, los agregados y las pruebas reproducen todas las cifras. En la preparación se usó Claude (Anthropic) como asistente de código y redacción, bajo la dirección y revisión del autor; los registros de `docs/REVISION.md` son revisiones simuladas por esa misma herramienta, no arbitraje externo.

## Contribuciones

**Daniel A. Garavito Jiménez** (autor):

- definió la pregunta del artículo y eligió la revista;
- escogió las fuentes y aprobó el diseño: unidad de análisis, tratamiento o escenarios, especificaciones e inferencia;
- tomó las decisiones de privacidad y de licencia: no publicar celdas de 1 a 4 en cruces sensibles y licenciar por capa (código, método, datos y texto);
- aportó su conocimiento del sistema de salud y de las estadísticas públicas de Colombia, buena parte de él adquirido como asesor de Innovación y Analítica de la ADRES;
- revisó los resultados, ordenó las correcciones y responde por todo el contenido.

**Claude (Anthropic)**, herramienta de inteligencia artificial usada bajo su dirección: escribió y depuró el código, ejecutó los análisis, produjo cuadros y figuras, redactó borradores de la documentación y simuló revisiones de árbitro. No figura como autor.

## Contenido

1. Pregunta y hallazgos
2. Cómo reproducir
3. Mapa del repositorio
4. Licencias y cita

## 1. Pregunta y hallazgos

¿Cuántas personas mueren en Colombia antes de los 75 años por condiciones que una atención primaria oportuna puede evitar, dónde, y cómo se relacionan esas muertes con las hospitalizaciones evitables?

- En 2023–2025 hubo 22 084 muertes anuales por condiciones sensibles a la atención primaria (CSAA) en menores de 75 años, el 15,4 % de las muertes a esas edades: 53,41 por 100 000, estandarizada por edad (IC 95 %: 53,00–53,82).
- La tasa bajó 48,3 % entre 1998 y 2014 y desde entonces no ha vuelto a bajar (54,00 en 2025). Las causas infecciosas subieron de 6,74 en 2011 a 11,88 en 2025.
- Chocó (79,90) duplica a Bogotá (36,85); 18 departamentos están por encima del país y 6 por debajo.
- En los municipios, la razón de hospitalización evitable de la ADRES (que mide composición del uso hospitalario) no anticipa la mortalidad: de los diez municipios con la razón más alta, cuatro tienen mortalidad por debajo de lo esperado, y la proporción de municipios altos en una y otra medida no se correlaciona entre departamentos.
- Con las hospitalizaciones evitables publicadas por la ADRES para 2025, la razón estandarizada de mortalidad y la de hospitalización casi no se correlacionan (rho 0,119); en 19 departamentos se muere más de lo que anticipan sus hospitalizaciones.

## 2. Cómo reproducir

| Nivel | Comando | Qué necesita | Tiempo |
|---|---|---|---|
| A | `make nivel-a` y `make pruebas` | Este repositorio (intermedios versionados) | unos 10 s |
| B | `make nivel-b` | Microdatos del DANE (`make insumos`, unos 2 GB) | unos 15 min, casi todo en `bases-eevv` |

`pruebas/verificar_cifras.py` termina en «Todo coincide.» si cada cifra del manuscrito coincide con las salidas (requiere el texto del artículo, que se agrega cuando se publique; sin él, el verificador lo avisa y termina). Detalle en `docs/REPLICACION.md`.

## 3. Mapa del repositorio

```
config/                 lista de CSAA (Portaria 221/2008), lista OCDE/Eurostat, población estándar, tabla del GBD, completitud
src/aps_evitable/       cálculo (calculo.py), figuras y cuadros (figuras.py), funciones de los estudios 43 y 54
src/eevv_insumos/       paquete común de Estadísticas Vitales (lectura y armonización de los microdatos del DANE)
scripts/00…04           descarga, intermedios (nivel B), comparación, estimación y figuras
data/raw/               MANIFIESTO.csv y transcripciones de la ADRES (lo demás se descarga)
data/intermedios/       conteos agregados y poblaciones: punto de partida del nivel A
output/                 resultados.json, aps_tablero.json, tablas/, figuras/, parametros/
pruebas/                test_insumos.py, test_calculos.py, verificar_cifras.py, insumos_eevv/
docs/                   INSUMOS, CALCULOS, DICCIONARIO, REPLICACION, REVISION, RECORD, FUENTES_LITERATURA
```

`output/parametros/` es un archivo de parámetros con esquema Frictionless (mortalidad por condición, edad, sexo y departamento, y costo por hospitalización evitable) para alimentar modelos de simulación de políticas de atención primaria.

## 4. Licencias y cita

Código bajo MIT (`LICENSE`); texto, cuadros, figuras y datos derivados bajo CC BY-NC 4.0; documentación de método bajo CC BY 4.0 (`LICENSE-datos.md`). Cita en `CITATION.cff`.
