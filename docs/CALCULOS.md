# Cálculos del artículo A5: de cada cifra a su función, su salida y su prueba

`pruebas/verificar_cifras.py` comprueba cada cifra del manuscrito contra las salidas (261 comprobaciones). `pruebas/test_calculos.py` recalcula las centrales con código independiente desde `data/intermedios/`.

## Contenido

1. Métodos: ecuación o regla → función
2. Cifras del resumen, la introducción y las conclusiones
3. Cuadros y figuras

## 1. Métodos: ecuación o regla → función

| Método (manuscrito, «Materiales y métodos») | Función | Prueba |
|---|---|---|
| Clasificación de la causa básica con la lista de CSAA y marcas de sensibilidad | `src/aps_evitable/calculo.py:clasificar()`, `codigos.py:expandir()` | `test_calculos.py::test_lista_contra_la_fuente`, `::test_codigos_observados_clasificados_igual` |
| Conteo por año, departamento, sexo, edad y causa | `calculo.py:contar()` (nivel B) | `::test_conservacion`; `02_comparar_intermedios.py` |
| Reparto de la edad desconocida | `calculo.py:repartir_edad()` | `::test_conservacion` |
| Tasa estandarizada directa (OCDE 2015, 15 grupos de 0 a 74, por 100 000 de la población estándar total) con IC gamma de Fay y Feuer | `calculo.py:tasa_est()`, `gamma_ic()`; pesos en `ocde.py:pesos_ocde2015()` | `::test_tasa_nacional_recalculada`, `::test_valores_del_arbitro` |
| AVPP con la tabla de referencia GBD 2019 | `calculo.py:nivel_a()` (bloque AVPP) y `config/tabla_vida_referencia.yaml` | `::test_tabla_referencia_gbd` |
| P(65) con tablas de vida abreviadas y eliminación de causas (Chiang); IC por Monte Carlo (400 simulaciones Poisson, semilla 20261105) | `calculo.py:p65()`, `termo.py:tabla()` | `::test_p65_con_tabla_propia` |
| Escenario de omisión: completitud implícita del DANE 2015–2017, acotada entre 0,2 y 1 | `calculo.py:esperadas_dane()` (nivel B), `completitud()` | Comparación de intermedios; `verificar_cifras.py` (sección 5) |
| Variantes de sensibilidad y correlación de Spearman | `calculo.py:nivel_a()` (bloque «sensibilidad») | `verificar_cifras.py` (sección 5) |
| REH, RME y cociente RME/REH con IC logarítmico; muertes por 1 000 hospitalizaciones | `calculo.py:hospitalizaciones()` | `::test_reh_recalculada`, `::test_rme_recalculada`, `::test_transcripcion_adres` |
| CPA por tramos, tasas por grupo infeccioso, sobredispersión cuasi-Poisson y REH cruda (pedidos por el árbitro) | `src/aps_evitable/sensibilidad.py` → `output/sensibilidad.json` | `verificar_cifras.py` §6b |
| Razón municipal de mortalidad (tasas nacionales por edad), suavizado bayesiano empírico de Marshall, clasificación con intervalo exacto (≥ 10 muertes), cruce con las tablas 6, 8, 9 y 10 de la ADRES | `src/aps_evitable/municipal.py:contar()` (nivel B), `estimar()` (nivel A) | `test_calculos.py::test_municipal_recalculado`, `::test_tablas_territoriales_adres`; `verificar_cifras.py` §6c |
| Archivo de parámetros (`fraccion` suavizada hacia la composición nacional con peso de 5 defunciones) | `calculo.py:parametros()`, `esquema()` | `::test_parametros` |

## 2. Cifras del resumen, la introducción y las conclusiones

| Cifra en el texto | Sección | Qué es | Clave en las salidas | Prueba |
|---|---|---|---|---|
| 6 218 747 registros; 29 410 sin edad | Resumen, Métodos | Defunciones 1998–2025 | `resultados.json: n_registros, n_sin_edad_repartidos` | `test_conservacion` |
| 22 084 muertes anuales; 15,4 %; 430 370 | Resumen, Resultados | CSAA <75, promedio 2023–2025 | `trienio[cod=0,total].def_csaa75 / 3`, `def_menores75` | `verificar_cifras.py` §1 |
| 53,41 (53,00–53,82) | Resumen, Resultados, cuadro 2 | Tasa estandarizada 2023–2025 | `trienio[0,total].tee_csaa(_lo,_hi)` | `test_tasa_nacional_recalculada`, `test_valores_del_arbitro` |
| 67,28 y 41,68; razón 1,61 | Resultados | Tasas por sexo | `trienio[0,hombres/mujeres].tee_csaa` | ídem |
| 686 012 AVPP; 1 550,63 | Resultados | AVPP anuales y tasa | `trienio[0,total].avpp_csaa / 3`, `tee_avpp_csaa` | `verificar_cifras.py` §1 |
| 0,86133 → 0,87787; ganancia 0,01654 | Resultados, cuadro 2 | P(65) | `trienio[0,total].p65, p65_sin_csaa, ganancia` | `test_p65_con_tabla_propia` |
| 61,4 % en cuatro grupos | Resultados | Diabetes, cerebrovascular, pulmonares, hipertensión | `grupos_trienio[].def_anual` | §2 |
| 39,0 % y 19,8 % | Resultados | Solapamiento con la lista OCDE/Eurostat (2015–2025) | `solapamiento_ocde` | §2 |
| 106,84 (1998); 55,22 (2014); 48,3 %; 54,00 (2025) | Resumen, Resultados | Serie nacional | `nacional[sexo=total].tee_csaa` | §3 |
| 6,74 (2011) → 11,88 (2025) | Resumen, Resultados | Bloque infeccioso | `nacional[].tee_infecciosas` | §3 |
| Chocó 79,90; Bogotá 36,85; razón 2,17; 18 y 6 departamentos | Resumen, Resultados | Departamentos 2023–2025 | `trienio[cod,total].tee_csaa(_lo,_hi)` | §4, `test_valores_del_arbitro` |
| Spearman 0,994 … 0,785; 72,03; 0,82131 | Resultados, cuadro 2 | Sensibilidad | `aps_tablero.json: spearman`; `trienio[0,total].tee_sens_*`, `*_corr` | §5 |
| 748 212; 19,5 %; 20,2 % | Introducción | Hospitalizaciones evitables 2025 (ADRES) | `aps_tablero.json: hospitalizaciones.nacional` | `test_transcripcion_adres` |
| 0,119; −0,255 | Resumen, Resultados | Correlaciones REH–RME y tasa de hospitalización–tasa de mortalidad | `hospitalizaciones.spearman` | §6 |
| 19 y 11 departamentos; Guainía 7,081; Huila 0,586 | Resumen, Resultados | RME/REH | `tablas/hospitalizaciones_vs_muertes_2025.csv` | §6, `test_reh_recalculada`, `test_rme_recalculada` |
| 741 municipios; 18,6 % y 10,9 %; 49,0 % de 1 090; Spearman −0,031; Cundinamarca 82,8 % y 1,7 %; 54,3 %, 46,5 %, 42,3 %; 27 de 32 | Resultados («Municipios») | Mortalidad municipal y cruce con la ADRES | `output/municipal/resultados.json`, `departamentos_municipal.csv` | §6c, `test_municipal_recalculado` |
| 35 % y 3 % | Resultados, Discusión | Cambio 2019–2024 de hospitalización (RIPS) y mortalidad | `hospitalizaciones.serie` | §6 |

## 3. Cuadros y figuras

| Elemento | Archivo | Función |
|---|---|---|
| Cuadro 1 | `output/tablas/cuadro1_condiciones.csv` | `figuras.py:cuadros()` |
| Cuadro 2 | `cuadro2a_colombia_sexo.csv`, `cuadro2b_sensibilidad.csv` | ídem |
| Cuadro S1 | `cuadroS1_departamentos.csv` | ídem |
| Cuadro S2 | `cuadroS2_municipios_adres.csv` (muertes de 1 a 4 como «<5») | ídem |
| Figura 1 | `output/figuras/figura1_serie_nacional.png` | `figuras.py:figura1()` |
| Figura 2 | `figura2_departamentos.png` | `figuras.py:figura2()` |
| Figura 3 | `figura3_hospitalizaciones_muertes.png` | `figuras.py:figura3()` |

`verificar_cifras.py` (§7) compara cada fila de los cuadros del manuscrito con su CSV.
