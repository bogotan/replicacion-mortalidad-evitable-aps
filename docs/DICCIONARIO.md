# Diccionario de los intermedios y de las salidas del artículo A5

## Contenido

1. data/intermedios/
2. output/

## 1. data/intermedios/

**`conteos.parquet`** (una fila por celda; 308 389 filas)

| Variable | Qué es |
|---|---|
| `anio` | Año de la defunción, 1998–2025 |
| `d` | Índice del departamento de residencia en el orden de los códigos DIVIPOLA (0 = Antioquia … 32 = Vichada); 33 = desconocido |
| `sexo` | 1 hombre, 2 mujer, 3 sin dato |
| `g` | Grupo de edad: −1 desconocida, 0 menor de 1 año, 1 de 1 a 4, 2 de 5 a 9, …, 18 de 85 y más |
| `grupo` | Grupo de CSAA (1 a 19; 0 = otra causa) |
| `maldef`, `externa`, `inesp`, `neum`, `adres` | Marcas: causa mal definida (R00–R99), causa externa, código poco específico (I50, J81, E86), neumonía J12–J18 fuera de la lista, código de la ampliación de la ADRES |
| `n` | Defunciones |
| `t`, `t2` | Suma de pesos de la lista OCDE/Eurostat tratable y de sus cuadrados (para la varianza) |

**`poblacion.parquet`**: `anio`, `cod_dpto`, `sexo` (1, 2), `g` (como arriba, 0 a 18), `pob`.

**`poblacion_2025_edad_simple.parquet`**: `dp` (código del departamento), `edad` (años cumplidos), `pob` (2025).

**`esperadas_dane_2015_2017.parquet`**: `cod_dpto`, `sexo`, `g`, `esperadas` (defunciones de 2015–2017 implícitas en las tasas del DANE).

**`codigos.parquet`** y **`codigos_csaa.csv`**: cada código CIE-10 observado (`cb`) con su `grupo`, `bloque`, marcas, pesos prevenible y tratable (`prev`, `trat`) y si aplica solo a mujeres; el CSV agrega las defunciones de menores de 75 años de 2015–2025 de los códigos con grupo.

**`cruce_lista_667.csv`**, **`cruce_lista_105.csv`**: defunciones de menores de 75 por causa de la lista 6/67 (2015–2025) y de la lista 105 (2020–2025) y cuántas son CSAA o tratables.

**`municipal_csaa.parquet`** (1 122 municipios, 2023–2025): `cod_dpto`, `mun` (código DIVIPOLA), `pob_2025`, `muertes_csaa75` (O: muertes por CSAA de menores de 75 con edad y municipio conocidos), `esperadas` (E: con las tasas nacionales por edad, sexos juntos), `muertes_todas75`, `muertes_csaa_todas_edades`.

**`solapamiento_ocde.json`**: muertes CSAA, tratables y prevenibles 2015–2025 y los dos porcentajes de solapamiento.

## 2. output/

- **`resultados.json`**: metadatos (`n_registros`, `n_sin_edad_repartidos`), `grupos_trienio` (19 grupos: muertes, tasa, IC, AVPP), `nacional` y `departamentos_anual` (una fila por año, territorio y sexo), `trienio` (2023–2025 por territorio y sexo, con las siete variantes de sensibilidad, P(65), ganancia y escenario de omisión), `solapamiento_ocde`, `completitud_dane_2015_2017`.
  - `tee_*`: tasas estandarizadas por 100 000 (OCDE 2015, 0–74); `_lo`, `_hi`: IC 95 %.
  - `avpp_csaa`, `tee_avpp_csaa`: AVPP y su tasa estandarizada.
  - `p65`, `p65_sin_csaa`, `ganancia`: probabilidad de sobrevivir de 0 a 65 y diferencia al eliminar las CSAA.
  - `tee_sens_*`: variantes de sensibilidad; `*_corr`: escenario de omisión.
- **`aps_tablero.json`**: lo mismo, compacto, más `spearman` y `hospitalizaciones` (departamentos, por condición, serie, correlaciones, totales nacionales).
- **`tablas/`**: `cuadro1_condiciones.csv`, `cuadro2a_colombia_sexo.csv`, `cuadro2b_sensibilidad.csv`, `cuadroS1_departamentos.csv` (los cuadros del manuscrito), `hospitalizaciones_vs_muertes_2025.csv` (REH, RME y cociente por departamento), `hospitalizaciones_vs_muertes_por_condicion_2025.csv`, `serie_territorial.csv`, `trienio_2023_2025.csv`, cruces y códigos.
- **`parametros/`**: archivo de parámetros con esquema Frictionless (`datapackage.json`): defunciones, población, `mx` con IC, `fraccion` (participación de cada grupo de causa, suavizada hacia la composición nacional con un peso de 5 defunciones) y `registro` (clase de completitud), por año, departamento, sexo, grupo de edad y grupo de causa; y el costo por hospitalización evitable de 2025 por condición.
- **`sensibilidad.json`**: análisis pedidos por el árbitro (`src/aps_evitable/sensibilidad.py`): `tendencia` (CPA con IC y p por tramo y bloque), `grupos_infecciosos` (tasas de 2011 y 2025), `sobredispersion` (factor de dispersión y departamentos fuera de los límites cuasi-Poisson), `reh_cruda`. La tabla `serie_grupos_infecciosos.csv` acompaña.
- **`municipal/`**: `rme_municipal_2023_2025.csv` (razón observada con intervalo exacto, razón suavizada con intervalo bayesiano, clases), `departamentos_municipal.csv` (porcentaje de municipios por clase frente a la tabla 6 de la ADRES), `concentracion.csv` (peso del municipio principal en hospitalizaciones, muertes y población), `top_municipios_adres.csv` (tablas 8 y 9 con su mortalidad), `resultados.json` y, para la priorización del tablero (no la usa el manuscrito), `priorizacion_municipios.csv`, `priorizacion_departamentos.csv` y `priorizacion.json` (muertes en exceso por año y cuadrante de la matriz de riesgo y carga). `aps_municipal_tablero.json` lleva lo mismo al tablero, con las muertes de 1 a 4 como −1.
- **`figuras/`**: figuras 1 a 3 del manuscrito (PNG, 300 ppp).
