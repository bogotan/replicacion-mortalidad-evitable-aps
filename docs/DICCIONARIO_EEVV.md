# Diccionario de las bases

Bases que produce el paquete en `data/processed/`. Fuente: DANE, Estadísticas Vitales (EEVV) y proyecciones de población con base en el CNPV 2018.

## Contenido

1. Reglas generales
2. `ext/def_<año>.parquet` y `defunciones_eevv.parquet`
3. `ext/nac_<año>.parquet`
4. `poblacion_eevv.parquet`
5. `mun_pob_edad.parquet`
6. Años en que el archivo original trae cada variable

## 1. Reglas generales

- Una fila por evento en las bases de defunciones y nacimientos. Sin filtros: el número de filas de cada año es el total que publica el DANE (ver `docs/INSUMOS.md`, sección 5).
- Residencia por defecto: `dp` y `mun` son el departamento y el municipio de residencia del fallecido o de la madre. La ocurrencia va en `dp_oc` y `mun_oc`.
- Las variables armonizadas (`dp`, `mun`, `sexo`, `g`, `g1`, `area`, `cb`, `cie`) tienen el mismo significado en todos los años. Las demás quedan con los códigos que el DANE publica en cada año, convertidos a entero (nulo si el archivo no trae la variable o el valor no es un número). Esos códigos cambian entre periodos, sobre todo en 2008; cada artículo documenta la armonización que necesita. Los diccionarios del DANE están en la pestaña «Diccionario de Datos» de cada catálogo: `https://microdatos.dane.gov.co/index.php/catalog/<catálogo>/data-dictionary`.
- Municipio: código DANE de cinco cifras (departamento × 1000 + municipio). Si el archivo trae el municipio con tres cifras se le antepone el departamento; si falta el municipio o el departamento, `mun = 0` (y `mun_oc = 0`).

## 2. Defunciones no fetales, 1979-2025

`ext/def_<año>.parquet` (47 archivos, 9.109.285 filas) tiene las 24 columnas de abajo. `defunciones_eevv.parquet` tiene las 12 primeras, con los 47 años apilados en orden.

| Columna | Tipo | Qué es | Códigos |
|---|---|---|---|
| `anio` | Int16 | año de la defunción | |
| `dp` | Int16 | departamento de residencia | código DANE; nulo si «sin información» (código 01) o vacío; en 1980-1981 el código viejo 83 de Caquetá pasa a 18; 75 = exterior |
| `mun` | Int32 | municipio de residencia | cinco cifras; 0 si no se sabe o si `dp` es nulo |
| `sexo` | Int8 | sexo | 1 hombre, 2 mujer, 0 indeterminado |
| `g` | Int8 | grupo de edad | 0 menor de 1 año, 1 de 1 a 4, 2 de 5 a 9, …, 19 de 90 a 94, 20 de 95 y más; −1 edad desconocida. En 1979-2007 el grupo 18 es «85 y más» y no hay 19 ni 20 |
| `g1` | Int8 | tramo de los menores de un año | 0 de 0 a 6 días, 1 de 7 a 27 días, 2 de 28 días a 11 meses; nulo para un año o más. Antes de 1998 el tramo 1 es de 7 a 29 días |
| `area` | Int8 | área de residencia | 1 cabecera, 2 centro poblado, 3 rural disperso, 0 sin dato (antes de 1992 siempre 0) |
| `cb` | Utf8 | causa básica | código de cuatro caracteres sin punto, en mayúscula (CIE-9 hasta 1996, CIE-10 desde 1997) |
| `cie` | Int8 | revisión de la clasificación | 9 hasta 1996, 10 desde 1997 |
| `etnia` | Int8 | pertenencia étnica (`idpertet`) | códigos del DANE; desde 2008 |
| `reg` | Int8 | régimen de seguridad social (`seg_social`) | códigos del DANE; desde 1998 |
| `c667` | Int16 | subgrupo de la lista 6/67 asignado por el DANE (`causa_667`) | 2008-2011 y 2014-2025 |
| `dp_oc` | Int16 | departamento de ocurrencia (`cod_dpto`) | código DANE |
| `mun_oc` | Int32 | municipio de ocurrencia (`cod_munic`) | cinco cifras; 0 si falta |
| `mes` | Int64 | mes de la defunción | 1 a 12 |
| `sit_defun` | Int64 | sitio de la defunción | códigos del DANE |
| `asis_med` | Int64 | asistencia médica | códigos del DANE; desde 1998 |
| `idprofcer` | Int64 | profesión de quien certifica | códigos del DANE; desde 2008 |
| `muerteporo` | Int64 | «la ocupación pudo ser causa o estar asociada con la defunción» | no es la manera de muerte; desde 2008 |
| `nivel_edu` | Int64 | nivel educativo del fallecido | códigos del DANE; desde 1998 |
| `est_civil` | Int64 | estado civil | códigos del DANE |
| `emb_fal` | Int64 | embarazo en mujeres fallecidas | códigos del DANE; desde 1998 |
| `edad_madre` | Int64 | edad de la madre (defunciones de menores de un año) | desde 1998 |
| `peso_nac` | Int64 | peso al nacer (defunciones de menores de un año) | desde 1998 |

Correspondencia de grupos de edad del archivo (`gru_ed1`) a `g`:

| Periodo | Esquema del DANE | Menores de 1 año | 1 a 4 | 5 a 9 … 80 a 84 | Edades mayores | Desconocida |
|---|---|---|---|---|---|---|
| 1979-1997 | antiguo (etiquetas DDI) | 01-05 | 06-07 | 08 … 23 | 24 = 85 y más (`g` 18) | 25 |
| 1998-2007 | viejo (decodificado cruzando con `gru_ed2` y con 2008) | 1-6 | 7-8 | 9 … 24 | 25 = 85 y más (`g` 18) | 26 |
| 2008-2025 | nuevo | 0-6 | 7-8 | 9 … 24 | 25 = 85 a 89, 26 = 90 a 94, 27 y 28 = 95 y más (`g` 18, 19, 20) | 29 |

Cualquier código fuera de estos mapas toma `g = −1`.

## 3. Nacidos vivos, 1998-2025

`ext/nac_<año>.parquet` (28 archivos, 18.450.346 filas), 28 columnas.

| Columna | Tipo | Qué es | Códigos |
|---|---|---|---|
| `anio` | Int16 | año del nacimiento | |
| `dp` | Int16 | departamento de residencia de la madre | código DANE; nulo si 00, 01 o vacío; 75 = exterior (cuenta en el total, en ningún departamento) |
| `mun` | Int32 | municipio de residencia de la madre | cinco cifras; 0 si falta |
| `area` | Int8 | área de residencia | 1 cabecera, 2 centro poblado, 3 rural disperso, 0 sin dato |
| `sexo` | Int8 | sexo del nacido | 1, 2; 0 sin dato |
| `edad_madre` | Int64 | edad de la madre | grupos quinquenales del DANE (códigos) |
| `peso_nac` | Int64 | peso al nacer | grupos de peso del DANE (códigos) |
| `t_ges` | Int64 | tiempo de gestación | grupos del DANE (códigos) |
| `numconsul` | Int64 | número de consultas prenatales | número |
| `tipo_parto` | Int64 | tipo de parto | códigos del DANE |
| `mul_parto` | Int64 | multiplicidad | códigos del DANE |
| `sit_parto` | Int64 | sitio del parto | códigos del DANE |
| `aten_par` | Int64 | quién atendió el parto | códigos del DANE |
| `reg` | Int64 | régimen de seguridad social de la madre (`seg_social`) | códigos del DANE |
| `etnia` | Int64 | pertenencia étnica (`idpertet`) | 2008-2011 y 2014-2025 |
| `t_ges_cie` | Int64 | gestación agrupada como la CIE (`t_ges_agru_cie`) | 3 = 28 a 36 semanas, 4 = 37 a 41; 2008-2011, 2014-2019, 2021-2025 |
| `pais_madre` | Int64 | país de nacimiento de la madre (`codpaisnacmad`) | 2024-2025 |
| `n_hijosv` | Int64 | hijos nacidos vivos de la madre, contando este | número |
| `dp_oc` | Int16 | departamento de ocurrencia del parto | código DANE |
| `mun_oc` | Int32 | municipio de ocurrencia del parto | cinco cifras; 0 si falta |
| `mes` | Int64 | mes del nacimiento | 1 a 12 |
| `edad_padre` | Int64 | edad del padre | años o grupos, según el año |
| `niv_edum` | Int64 | nivel educativo de la madre | códigos del DANE |
| `niv_edup` | Int64 | nivel educativo del padre | códigos del DANE |
| `est_civm` | Int64 | estado civil de la madre | códigos del DANE |
| `n_emb` | Int64 | número de embarazos | número |
| `codpres` | Int64 | país de residencia de la madre | 170 = Colombia |
| `idclasadmi` | Int64 | clase de institución del parto | desde 2008 |

En 2012 y 2013 se lee la versión en texto del catálogo 377, que no trae `idpertet` ni `t_ges_agru_cie`.

## 4. Población departamental, 1981-2025

`poblacion_eevv.parquet`, 548.228 filas. Solo las filas de área (cabecera y resto); su suma por departamento coincide con la fila «Total» del DANE (diferencia máxima: 0 personas).

| Columna | Tipo | Qué es |
|---|---|---|
| `anio` | Int16 | año |
| `dp` | Int16 | departamento (código DANE); 0 = total nacional, solo en 1981-1984 |
| `area` | Int8 | 1 cabecera, 2 centros poblados y rural disperso |
| `sexo` | Int8 | 1 hombres, 2 mujeres |
| `edad` | Int8 | edad simple 0 a 100 (100 = 100 y más) |
| `pob` | Float64 | personas |

Fuentes por periodo: 1981-1984 serie nacional 1950-2017; 1985-1992, 1993-2004 y 2005-2017 retroproyecciones departamentales; 2018-2025 proyecciones departamentales 2018-2050 (actualización de julio de 2025).

## 5. Población municipal, 1985-2025

`mun_pob_edad.parquet`, 11.870.580 filas.

| Columna | Tipo | Qué es |
|---|---|---|
| `dp` | Utf8 | departamento, dos cifras |
| `mpio` | Utf8 | municipio, cinco cifras |
| `ano` | Int32 | año |
| `area` | Utf8 | «Cabecera Municipal», «Centros Poblados y Rural Disperso» o «Total» |
| `edad` | Int16 | edad simple 0 a 85 (85 = 85 y más) |
| `pob` | Float64 | personas (hombres más mujeres) |

Fuentes por periodo: 1985-1994, 1995-2004 y 2005-2017 retroproyecciones municipales; 2018-2025 proyecciones municipales 2018-2042 (actualización de julio de 2025). La suma municipal del área «Total» coincide cada año con la departamental (diferencia relativa máxima: 0).

## 6. Años en que el archivo original trae cada variable

Sale de `pruebas/columnas_esperadas.json`, que la prueba de columnas compara con los archivos en cada corrida.

| Variable del DANE | Defunciones | Nacimientos |
|---|---|---|
| `codptore`, `codmunre`, `sexo`, `cod_dpto`, `cod_munic`, `mes` | 1979-2025 | 1998-2025 |
| `gru_ed1`, `c_bas1`, `sit_defun`, `est_civil` | 1979-2025 | |
| `area_res` | 1992-2025 | 1998-2025 |
| `seg_social`, `asis_med`, `nivel_edu`, `emb_fal`, `edad_madre`, `peso_nac` | 1998-2025 | `seg_social`, `edad_madre`, `peso_nac`: 1998-2025 |
| `idpertet` | 2008-2025 | 2008-2011, 2014-2025 |
| `causa_667` | 2008-2011, 2014-2025 | |
| `idprofcer`, `muerteporo` | 2008-2025 | |
| `t_ges`, `numconsul`, `tipo_parto`, `mul_parto`, `sit_parto`, `aten_par`, `n_hijosv`, `edad_padre`, `niv_edum`, `niv_edup`, `est_civm`, `n_emb`, `codpres` | | 1998-2025 |
| `t_ges_agru_cie` | | 2008-2011, 2014-2019, 2021-2025 |
| `idclasadmi` | | 2008-2025 |
| `codpaisnacmad` | | 2024-2025 |
