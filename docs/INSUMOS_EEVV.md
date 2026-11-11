# Insumos de Estadísticas Vitales (EEVV) y población

Fichas de los 79 insumos crudos que usa el paquete, sus términos de uso, lo que se hace con cada uno y su validación contra cifras publicadas por el propio DANE. La lista completa, con la huella SHA-256 entera, está en `data/raw/MANIFIESTO.csv`.

## Contenido

1. Productor y cita
2. Términos de uso y decisión sobre la redistribución
3. Fichas por producto
4. Transformaciones
5. Validación año por año
6. Archivos y huellas (tablas A y B)

## 1. Productor y cita

Todos los insumos son del Departamento Administrativo Nacional de Estadística (DANE). Cita exigida por el DANE: «Fuente: Departamento Administrativo Nacional de Estadística: www.dane.gov.co».

## 2. Términos de uso y decisión sobre la redistribución

**Microdatos del Archivo Nacional de Datos (ANDA).** Cada catálogo de Estadísticas Vitales en `microdatos.dane.gov.co` tiene una sección «Acceso a los datos» con el mismo texto (consultada el 29 de octubre de 2026 en los catálogos 366, 732 y 878, en la página `catalog/<n>/study-description`):

> «El acceso a los microdatos anonimizados de uso público es de carácter gratuito y estará disponible en la página Web del DANE.»

> «Se autoriza el uso de la información contenida en esta portal, siempre y cuando se haga la siguiente cita textual: "Fuente: Departamento Administrativo Nacional de Estadística: www.dane.gov.co". Queda en cambio prohibida la copia o reproducción de los datos en cualquier medio electrónico (redes, bases de datos, cd rom, diskettes) que permita la disponibilidad de esta información a múltiples usuarios sin el previo visto bueno del DANE por medio escrito.»

La misma sección cita la reserva estadística (Ley 79 de 1993, artículo 5). La API del portal marca el acceso como directo (`data_access_type: direct`, consultado en el catálogo 732) y, el 29 de octubre de 2026, los 91 recursos de descarga de los 17 catálogos respondieron con el archivo, sin registro, formulario ni aceptación de términos. El script `00_descargar_microdatos.py` se detiene y explica el paso manual si eso cambia.

**Portal www.dane.gov.co** (proyecciones de población y estimaciones del cambio demográfico). Términos y condiciones, consultados el 29 de octubre de 2026 en `https://www.dane.gov.co/index.php/terminos-y-condiciones`:

> «El DANE pone este material a disposición de los usuarios en forma individual, como licencia de usuario final […]»

> «Se autoriza el uso, aprovechamiento, transformación y análisis de la información contenida en esta portal, siempre y cuando se haga la siguiente cita textual: "Fuente: Departamento Administrativo Nacional de Estadística: www.dane.gov.co".»

**Decisión.**

| Qué | ¿Se redistribuye? | Por qué |
|---|---|---|
| Zips de microdatos (65 archivos) | No | Los términos del ANDA prohíben ponerlos a disposición de múltiples usuarios sin visto bueno escrito del DANE. Un repositorio público lo haría. Se bajan con `00_descargar_microdatos.py` y se verifican por su huella. |
| `ext/def_<año>`, `ext/nac_<año>`, `defunciones_eevv.parquet` | No | Son el mismo microdato, registro por registro, con otras columnas. La prohibición los alcanza. Se reconstruyen con los scripts 01 a 03 en unos 3 minutos. |
| Proyecciones de población y estimaciones en .xlsx (14 archivos) | No | El portal las entrega como licencia de usuario final individual; además dos pasan de 50 MB. Se bajan y verifican igual que los microdatos. |
| `poblacion_eevv.parquet`, `mun_pob_edad.parquet` | Sí, con la cita del DANE | Son agregados transformados, y los términos del portal autorizan la transformación con cita. No contienen registros individuales. |
| Agregados que publiquen los artículos (conteos por municipio y año, tasas) | Sí, con la cita del DANE | Son «resúmenes numéricos» en el sentido de la Ley 79 de 1993; las celdas menores de 5 en cruces sensibles se suprimen según el estándar de los repositorios. |

Esta lectura es conservadora. Si el DANE da un visto bueno escrito para redistribuir los microdatos, basta con cambiar la columna `redistribuye` del manifiesto y el `.gitignore`.

## 3. Fichas por producto

### 3.1 Defunciones no fetales 1979-1997

- **Origen:** DANE, Estadísticas Vitales, catálogos ANDA 396 (1979-1991), 397 (1992-1996) y 398 (1997). Un zip por año, `Defun<año>.zip`.
- **Archivo:** un .sav por zip. Filas usadas: todas. Columnas: residencia (`codptore`, `codmunre`), `sexo`, `gru_ed1`, `c_bas1` (CIE-9 hasta 1996), `area_res` (desde 1992), ocurrencia, `mes`, `sit_defun`, `est_civil`.
- **Términos:** ANDA (sección 2). No se redistribuye.
- **Transformación:** `eevv_insumos.defunciones` (esquema «antiguo» de edad), script 02.
- **Validación:** total anual contra la tabla de defunciones por grupos de edad y lista de 56 grupos de causas del DANE (`/files/investigaciones/poblacion/defunciones/lista_56grupos-causas/defun<año>.xls`). Coincide en los 19 años (tabla C).

### 3.2 Nacimientos y defunciones 1998-2007

- **Origen:** catálogo 366 (EEVV 1998-2007). Archivos `Nacimientos <año>.zip` (2006 y 2007 con guion bajo) y `Defunciones <año>.zip` (2000, 2003, 2004 y 2006 con dos espacios, como los nombra el DANE).
- **Archivo:** nacimientos en texto separado por tabulador; defunciones en .sav sin etiquetas de valor.
- **Transformación:** scripts 02 (esquema «viejo» de edad) y 03.
- **Validación:** cuadro 1 de nacimientos y cuadro 1 de defunciones de cada año. Coinciden los 20 totales. El cuadro de defunciones de 2004 está marcado como preliminar (`CUADRO1_2004P.xls`, el único publicado) y aun así coincide.

### 3.3 Nacimientos y defunciones 2008-2019

- **Origen:** catálogos 375 (2008-2011), 377 (2012-2013), 420 (2014), 475 (2015), 519 (2016), 652 (2017-2018) y 696 (2019). En el portal todos se llaman `Defunciones.zip` y `Nacimientos.zip` (o `Nacidos.zip`); aquí se guardan con el prefijo `cat<n>_<años>_` para que no se pisen.
- **Archivo:** CSV dentro de un zip anual dentro del zip del catálogo; en 2012-2013, .sav (defunciones) y texto con tabulador (nacimientos, versión «txt» del catálogo 377).
- **Transformación:** scripts 02 y 03 (esquema «nuevo» de edad).
- **Validación:** cuadro 1 de cada año hasta 2015 y boletín técnico de septiembre de 2026 para 2016-2019. Coinciden los 24 totales.

### 3.4 Nacimientos y defunciones 2020-2025

- **Origen:** catálogos 732 (2020), 775 (2021), 807 (2022), 876 (2023), 878 (2024) y 915 (2025). Un zip por año y tipo, con el mismo dato en .csv, .dta y .sav.
- **Archivo:** nacimientos, el .csv; defunciones, el .dta (en 2021, que no trae .dta sino .stata, el .sav), como en el repositorio EEVV. Los cinco zips de defunciones 2020-2024 no estaban en `eevv-repo/data/raw/` (allí se habían borrado tras extraerlos); se bajaron el 29 de octubre de 2026 y dieron exactamente las mismas bases.
- **Transformación:** script 01 (lee 21 columnas del .dta/.sav a `data/interim/eevv/def_<año>.parquet`) y scripts 02 y 03.
- **Validación:** boletín técnico «Estadísticas Vitales, año 2025 y año corrido 2026pr» del 24 de septiembre de 2026 (gráficos 2 y 8, cifras definitivas 2016-2025). Coinciden los 12 totales.

### 3.5 Proyecciones de población (base CNPV 2018)

- **Origen:** `https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/` (carpetas Nacional, Departamental y Municipal), página «Proyecciones de población» del DANE. Las versiones de 2018 en adelante son la actualización publicada en julio de 2025 (archivos con fecha de modificación del 8 de agosto de 2025 en el servidor).
- **Archivos:** serie nacional por área, sexo y edad 1950-2017; retroproyecciones departamentales 1985-1992, 1993-2004 y 2005-2017; proyección departamental 2018-2050; retroproyecciones municipales 1985-1994, 1995-2004 y 2005-2017; proyección municipal 2018-2042 (en el portal `PPED-AreaSexoEdadMun-2018-2042_VP.xlsx`; aquí `Mun-edad-2018-2042.xlsx`, el nombre que usan los artículos). Todos se bajaron de nuevo el 29 de octubre de 2026 y tienen la misma huella que la copia del repositorio EEVV.
- **Transformación:** script 04. Departamental: filas de área (cabecera y resto), edad simple 0-100. Municipal: hombres más mujeres, edad simple hasta 85 y más.
- **Validación:** el total de cada año contra el total nacional que el DANE publica en archivos aparte (`PPED-AreaNac-1950-2017.xlsx` y `PPED-AreaNac-2018-2070.xlsx`, guardados en `data/raw/poblacion/referencia/`). Coinciden los 45 años departamentales y los 41 municipales, con diferencia 0 (tabla D). Controles internos: cabecera más resto igual al total departamental (diferencia máxima 0 personas), suma departamental 1985-1992 igual a la serie nacional, suma municipal igual a la departamental cada año.

### 3.6 Archivos que los artículos leen directo

- `poblacion/dane_mor/DCD-Mor-EstSexNal-Dep-1985-2017_VP.xlsx` y `DCD-Mor-EstSexNal-Reg-2018-2070_VP.xlsx`: tasas de mortalidad por sexo y edad simple de las estimaciones del cambio demográfico (`https://www.dane.gov.co/files/censo2018/cambio-demografico/`). Los lee A1 para la completitud del registro.
- `poblacion/Mun-2020-2035.xlsx`: proyección municipal por área 2020-2035 de la actualización posCOVID-19 anterior a la de julio de 2025 (fecha interna del archivo: 17 de marzo de 2023). Lo lee A4. **Ya no está en el portal del DANE** y no se encontró su URL; el manifiesto guarda su huella y el script de descarga pide copiarlo a mano.

## 4. Transformaciones

| Script | Lee | Escribe |
|---|---|---|
| `00_descargar_microdatos.py` | `MANIFIESTO.csv` | `data/raw/…` (y verifica huellas) |
| `01_extraer.py` | zips de defunciones 2020-2025 | `data/interim/eevv/def_<año>.parquet` |
| `02_base_defunciones.py` | zips de defunciones 1979-2019 e intermedios 2020-2025 | `ext/def_<año>.parquet`, `defunciones_eevv.parquet` |
| `03_base_nacimientos.py` | zips de nacimientos 1998-2025 | `ext/nac_<año>.parquet` |
| `04_poblacion.py` | proyecciones departamentales y municipales | `poblacion_eevv.parquet`, `mun_pob_edad.parquet` |

La armonización (grupos de edad, residencia, causa) es la del repositorio EEVV, copiada sin cambios; `docs/REPLICACION.md` lista lo que sí cambió en la lectura.

## 5. Validación año por año

`pruebas/test_insumos_eevv.py` corre estas comparaciones y falla si alguna se aparta de la tolerancia:

- **Registros:** tolerancia 0. Los cuadros y el boletín del DANE se tabulan del mismo archivo definitivo que publica el ANDA, así que una diferencia de un solo registro indicaría otra versión del archivo.
- **Población:** tolerancia 1 persona por año. Los totales publicados son enteros y las bases suman enteros guardados como decimales; 1 persona solo cubre el error de coma flotante.

Las cifras del DANE de cada año, con el documento y la URL, están en `pruebas/totales_publicados_dane.csv`. Resultado de la corrida del 29 de octubre de 2026: **los 47 años de defunciones, los 28 de nacimientos y los 45 de población coinciden exactamente**.


### Tabla C. Registros por año frente a lo publicado por el DANE

| Año | Defunciones no fetales: base | DANE | Diferencia | Nacidos vivos: base | DANE | Diferencia | Fuente de la cifra del DANE |
|---|---|---|---|---|---|---|---|
| 1979 | 110.400 | 110.400 | 0 | | |  | lista de 56 grupos del DANE |
| 1980 | 125.573 | 125.573 | 0 | | |  | lista de 56 grupos del DANE |
| 1981 | 139.505 | 139.505 | 0 | | |  | lista de 56 grupos del DANE |
| 1982 | 137.678 | 137.678 | 0 | | |  | lista de 56 grupos del DANE |
| 1983 | 140.292 | 140.292 | 0 | | |  | lista de 56 grupos del DANE |
| 1984 | 137.189 | 137.189 | 0 | | |  | lista de 56 grupos del DANE |
| 1985 | 153.947 | 153.947 | 0 | | |  | lista de 56 grupos del DANE |
| 1986 | 146.346 | 146.346 | 0 | | |  | lista de 56 grupos del DANE |
| 1987 | 151.957 | 151.957 | 0 | | |  | lista de 56 grupos del DANE |
| 1988 | 153.067 | 153.067 | 0 | | |  | lista de 56 grupos del DANE |
| 1989 | 154.694 | 154.694 | 0 | | |  | lista de 56 grupos del DANE |
| 1990 | 154.685 | 154.685 | 0 | | |  | lista de 56 grupos del DANE |
| 1991 | 163.692 | 163.692 | 0 | | |  | lista de 56 grupos del DANE |
| 1992 | 167.743 | 167.743 | 0 | | |  | lista de 56 grupos del DANE |
| 1993 | 168.647 | 168.647 | 0 | | |  | lista de 56 grupos del DANE |
| 1994 | 168.568 | 168.568 | 0 | | |  | lista de 56 grupos del DANE |
| 1995 | 169.896 | 169.896 | 0 | | |  | lista de 56 grupos del DANE |
| 1996 | 173.506 | 173.506 | 0 | | |  | lista de 56 grupos del DANE |
| 1997 | 170.753 | 170.753 | 0 | | |  | lista de 56 grupos del DANE |
| 1998 | 175.363 | 175.363 | 0 | 720.984 | 720.984 | 0 | cuadro 1 definitivo |
| 1999 | 183.553 | 183.553 | 0 | 746.194 | 746.194 | 0 | cuadro 1 definitivo |
| 2000 | 187.432 | 187.432 | 0 | 752.834 | 752.834 | 0 | cuadro 1 definitivo |
| 2001 | 191.513 | 191.513 | 0 | 724.319 | 724.319 | 0 | cuadro 1 definitivo |
| 2002 | 192.262 | 192.262 | 0 | 700.455 | 700.455 | 0 | cuadro 1 definitivo |
| 2003 | 192.121 | 192.121 | 0 | 710.702 | 710.702 | 0 | cuadro 1 definitivo |
| 2004 | 188.933 | 188.933 | 0 | 723.099 | 723.099 | 0 | cuadro 1 definitivo; defunciones: cuadro 1 de 2004 marcado como preliminar |
| 2005 | 189.022 | 189.022 | 0 | 719.968 | 719.968 | 0 | cuadro 1 definitivo |
| 2006 | 192.814 | 192.814 | 0 | 714.450 | 714.450 | 0 | cuadro 1 definitivo |
| 2007 | 193.936 | 193.936 | 0 | 709.253 | 709.253 | 0 | cuadro 1 definitivo |
| 2008 | 196.943 | 196.943 | 0 | 715.453 | 715.453 | 0 | cuadro 1 definitivo |
| 2009 | 196.933 | 196.933 | 0 | 699.775 | 699.775 | 0 | cuadro 1 definitivo |
| 2010 | 200.524 | 200.524 | 0 | 654.627 | 654.627 | 0 | cuadro 1 definitivo |
| 2011 | 195.823 | 195.823 | 0 | 665.499 | 665.499 | 0 | cuadro 1 definitivo |
| 2012 | 199.756 | 199.756 | 0 | 676.835 | 676.835 | 0 | cuadro 1 definitivo |
| 2013 | 203.071 | 203.071 | 0 | 658.835 | 658.835 | 0 | cuadro 1 definitivo |
| 2014 | 210.051 | 210.051 | 0 | 669.137 | 669.137 | 0 | cuadro 1 definitivo |
| 2015 | 219.472 | 219.472 | 0 | 660.999 | 660.999 | 0 | cuadro 1 definitivo |
| 2016 | 223.078 | 223.078 | 0 | 647.521 | 647.521 | 0 | boletín técnico sep. 2026 |
| 2017 | 227.624 | 227.624 | 0 | 656.704 | 656.704 | 0 | boletín técnico sep. 2026 |
| 2018 | 236.932 | 236.932 | 0 | 649.115 | 649.115 | 0 | boletín técnico sep. 2026 |
| 2019 | 244.355 | 244.355 | 0 | 642.660 | 642.660 | 0 | boletín técnico sep. 2026 |
| 2020 | 300.853 | 300.853 | 0 | 629.402 | 629.402 | 0 | boletín técnico sep. 2026 |
| 2021 | 363.089 | 363.089 | 0 | 616.914 | 616.914 | 0 | boletín técnico sep. 2026 |
| 2022 | 287.251 | 287.251 | 0 | 573.625 | 573.625 | 0 | boletín técnico sep. 2026 |
| 2023 | 268.411 | 268.411 | 0 | 515.549 | 515.549 | 0 | boletín técnico sep. 2026 |
| 2024 | 275.778 | 275.778 | 0 | 453.901 | 453.901 | 0 | boletín técnico sep. 2026 |
| 2025 | 284.254 | 284.254 | 0 | 441.537 | 441.537 | 0 | boletín técnico sep. 2026 |

### Tabla D. Población total por año frente al total nacional publicado por el DANE

| Año | DANE, total nacional | `poblacion_eevv` | Diferencia | `mun_pob_edad` (área Total) | Diferencia |
|---|---|---|---|---|---|
| 1981 | 28.212.667 | 28.212.667 | 0 | |  |
| 1982 | 28.748.586 | 28.748.586 | 0 | |  |
| 1983 | 29.289.744 | 29.289.744 | 0 | |  |
| 1984 | 29.842.691 | 29.842.691 | 0 | |  |
| 1985 | 30.419.892 | 30.419.892 | 0 | 30.419.892 | 0 |
| 1986 | 30.980.812 | 30.980.812 | 0 | 30.980.812 | 0 |
| 1987 | 31.550.132 | 31.550.132 | 0 | 31.550.132 | 0 |
| 1988 | 32.124.173 | 32.124.173 | 0 | 32.124.173 | 0 |
| 1989 | 32.697.847 | 32.697.847 | 0 | 32.697.847 | 0 |
| 1990 | 33.268.154 | 33.268.154 | 0 | 33.268.154 | 0 |
| 1991 | 33.840.991 | 33.840.991 | 0 | 33.840.991 | 0 |
| 1992 | 34.425.915 | 34.425.915 | 0 | 34.425.915 | 0 |
| 1993 | 35.032.308 | 35.032.308 | 0 | 35.032.308 | 0 |
| 1994 | 35.629.174 | 35.629.174 | 0 | 35.629.174 | 0 |
| 1995 | 36.229.830 | 36.229.830 | 0 | 36.229.830 | 0 |
| 1996 | 36.830.574 | 36.830.574 | 0 | 36.830.574 | 0 |
| 1997 | 37.426.532 | 37.426.532 | 0 | 37.426.532 | 0 |
| 1998 | 38.012.359 | 38.012.359 | 0 | 38.012.359 | 0 |
| 1999 | 38.585.016 | 38.585.016 | 0 | 38.585.016 | 0 |
| 2000 | 39.140.080 | 39.140.080 | 0 | 39.140.080 | 0 |
| 2001 | 39.674.811 | 39.674.811 | 0 | 39.674.811 | 0 |
| 2002 | 40.190.679 | 40.190.679 | 0 | 40.190.679 | 0 |
| 2003 | 40.693.254 | 40.693.254 | 0 | 40.693.254 | 0 |
| 2004 | 41.188.093 | 41.188.093 | 0 | 41.188.093 | 0 |
| 2005 | 41.671.878 | 41.671.878 | 0 | 41.671.878 | 0 |
| 2006 | 42.170.126 | 42.170.126 | 0 | 42.170.126 | 0 |
| 2007 | 42.658.630 | 42.658.630 | 0 | 42.658.630 | 0 |
| 2008 | 43.134.017 | 43.134.017 | 0 | 43.134.017 | 0 |
| 2009 | 43.608.630 | 43.608.630 | 0 | 43.608.630 | 0 |
| 2010 | 44.086.292 | 44.086.292 | 0 | 44.086.292 | 0 |
| 2011 | 44.553.416 | 44.553.416 | 0 | 44.553.416 | 0 |
| 2012 | 45.001.571 | 45.001.571 | 0 | 45.001.571 | 0 |
| 2013 | 45.434.942 | 45.434.942 | 0 | 45.434.942 | 0 |
| 2014 | 45.866.010 | 45.866.010 | 0 | 45.866.010 | 0 |
| 2015 | 46.313.898 | 46.313.898 | 0 | 46.313.898 | 0 |
| 2016 | 46.830.116 | 46.830.116 | 0 | 46.830.116 | 0 |
| 2017 | 47.419.200 | 47.419.200 | 0 | 47.419.200 | 0 |
| 2018 | 48.258.494 | 48.258.494 | 0 | 48.258.494 | 0 |
| 2019 | 49.266.526 | 49.266.526 | 0 | 49.266.526 | 0 |
| 2020 | 50.390.790 | 50.390.790 | 0 | 50.390.790 | 0 |
| 2021 | 51.115.637 | 51.115.637 | 0 | 51.115.637 | 0 |
| 2022 | 51.643.565 | 51.643.565 | 0 | 51.643.565 | 0 |
| 2023 | 52.117.067 | 52.117.067 | 0 | 52.117.067 | 0 |
| 2024 | 52.613.753 | 52.613.753 | 0 | 52.613.753 | 0 |
| 2025 | 53.057.212 | 53.057.212 | 0 | 53.057.212 | 0 |

## 6. Archivos y huellas

La huella completa de cada archivo está en `data/raw/MANIFIESTO.csv`; aquí van los primeros 16 caracteres. «Descargado» es la fecha de la copia cuya huella se registró (la fecha de modificación del archivo en el repositorio EEVV, o el 29 de octubre de 2026 para los que se bajaron en esta sesión). Todos los enlaces de la tabla A son de descarga directa del ANDA.

### Tabla A. Microdatos de Estadísticas Vitales

| Archivo en `data/raw/` | Catálogo ANDA | Años | Tamaño (MB) | SHA-256 (primeros 16) | Descargado | Lo lee |
|---|---|---|---|---|---|---|
| `antiguos/Defun1979.zip` | [396](https://microdatos.dane.gov.co/index.php/catalog/396/download/6344) | def. 1979 | 2,0 | `9e9b9dd95f4335a2` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1980.zip` | [396](https://microdatos.dane.gov.co/index.php/catalog/396/download/6345) | def. 1980 | 2,3 | `0801b3edefdabade` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1981.zip` | [396](https://microdatos.dane.gov.co/index.php/catalog/396/download/6346) | def. 1981 | 2,5 | `0382e5edafb614e3` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1982.zip` | [396](https://microdatos.dane.gov.co/index.php/catalog/396/download/6347) | def. 1982 | 2,2 | `5c28499f612ff494` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1983.zip` | [396](https://microdatos.dane.gov.co/index.php/catalog/396/download/6348) | def. 1983 | 2,3 | `68e7fb08d382b51f` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1984.zip` | [396](https://microdatos.dane.gov.co/index.php/catalog/396/download/6349) | def. 1984 | 2,6 | `77ac4bc19b131be3` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1985.zip` | [396](https://microdatos.dane.gov.co/index.php/catalog/396/download/6350) | def. 1985 | 2,9 | `09b1610fcec9908e` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1986.zip` | [396](https://microdatos.dane.gov.co/index.php/catalog/396/download/6351) | def. 1986 | 2,7 | `2bfbe46a5b48949a` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1987.zip` | [396](https://microdatos.dane.gov.co/index.php/catalog/396/download/6352) | def. 1987 | 2,8 | `ff19f3d8f5320543` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1988.zip` | [396](https://microdatos.dane.gov.co/index.php/catalog/396/download/6353) | def. 1988 | 2,8 | `0c0f2f41ecd385cd` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1989.zip` | [396](https://microdatos.dane.gov.co/index.php/catalog/396/download/6354) | def. 1989 | 2,8 | `81d54aa4103803c4` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1990.zip` | [396](https://microdatos.dane.gov.co/index.php/catalog/396/download/6355) | def. 1990 | 2,8 | `262ba0f78088a441` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1991.zip` | [396](https://microdatos.dane.gov.co/index.php/catalog/396/download/6356) | def. 1991 | 2,9 | `b9dc185ed66c4535` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1992.zip` | [397](https://microdatos.dane.gov.co/index.php/catalog/397/download/6360) | def. 1992 | 4,0 | `c4bf9d902eac539b` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1993.zip` | [397](https://microdatos.dane.gov.co/index.php/catalog/397/download/6361) | def. 1993 | 4,0 | `40b33deb35c1a739` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1994.zip` | [397](https://microdatos.dane.gov.co/index.php/catalog/397/download/6362) | def. 1994 | 4,0 | `738ac9a252192bbb` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1995.zip` | [397](https://microdatos.dane.gov.co/index.php/catalog/397/download/6363) | def. 1995 | 4,0 | `f7f3ea722c6b6716` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1996.zip` | [397](https://microdatos.dane.gov.co/index.php/catalog/397/download/6364) | def. 1996 | 4,0 | `803af17ccf864cc9` | 2026-10-21 | 02_base_defunciones.py |
| `antiguos/Defun1997.zip` | [398](https://microdatos.dane.gov.co/index.php/catalog/398/download/6367) | def. 1997 | 4,0 | `d953a0878bbeea86` | 2026-10-21 | 02_base_defunciones.py |
| `Defunciones  2000.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5604) | def. 2000 | 9,3 | `52fab640ddb6664e` | 2026-09-26 | 02_base_defunciones.py |
| `Defunciones  2003.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5610) | def. 2003 | 9,3 | `6569f6fc21e86a5e` | 2026-09-26 | 02_base_defunciones.py |
| `Defunciones  2004.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5612) | def. 2004 | 9,6 | `24c96585d135f8ad` | 2026-09-26 | 02_base_defunciones.py |
| `Defunciones  2006.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5616) | def. 2006 | 9,9 | `b3a82e553b62e0b0` | 2026-09-26 | 02_base_defunciones.py |
| `Defunciones 1998.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5600) | def. 1998 | 6,7 | `3e473e7ce205a363` | 2026-09-26 | 02_base_defunciones.py |
| `Defunciones 1999.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5602) | def. 1999 | 8,6 | `9312255f1e0cc405` | 2026-09-26 | 02_base_defunciones.py |
| `Defunciones 2001.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5606) | def. 2001 | 9,8 | `21bae5dacde826ae` | 2026-09-26 | 02_base_defunciones.py |
| `Defunciones 2002.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5608) | def. 2002 | 9,3 | `ab3aa31758132533` | 2026-09-26 | 02_base_defunciones.py |
| `Defunciones 2005.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5614) | def. 2005 | 9,6 | `b7f57baaf25603bf` | 2026-09-26 | 02_base_defunciones.py |
| `Defunciones 2007.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5618) | def. 2007 | 10,4 | `feb6daf266a501a9` | 2026-09-26 | 02_base_defunciones.py |
| `Nacimientos 1998.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5599) | nac. 1998 | 24,6 | `f33a8b9eea7573bb` | 2026-10-21 | 03_base_nacimientos.py |
| `Nacimientos 1999.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5601) | nac. 1999 | 26,0 | `cc87820fb97315d0` | 2026-10-21 | 03_base_nacimientos.py |
| `Nacimientos 2000.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5603) | nac. 2000 | 26,7 | `fabbf515707bf2d5` | 2026-10-21 | 03_base_nacimientos.py |
| `Nacimientos 2001.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5605) | nac. 2001 | 26,4 | `59077dd5254572a8` | 2026-10-21 | 03_base_nacimientos.py |
| `Nacimientos 2002.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5607) | nac. 2002 | 25,5 | `2466b78de9713f4b` | 2026-10-21 | 03_base_nacimientos.py |
| `Nacimientos 2003.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5609) | nac. 2003 | 25,9 | `96727e39b137b8e0` | 2026-10-21 | 03_base_nacimientos.py |
| `Nacimientos 2004.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5611) | nac. 2004 | 26,2 | `8e271df8459adeb3` | 2026-10-21 | 03_base_nacimientos.py |
| `Nacimientos 2005.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5613) | nac. 2005 | 25,9 | `cff18f23753d9ce5` | 2026-10-21 | 03_base_nacimientos.py |
| `Nacimientos_2006.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5615) | nac. 2006 | 26,0 | `92077d39a1499d36` | 2026-10-21 | 03_base_nacimientos.py |
| `Nacimientos_2007.zip` | [366](https://microdatos.dane.gov.co/index.php/catalog/366/download/5617) | nac. 2007 | 25,9 | `a86e0a68c7de84e1` | 2026-10-21 | 03_base_nacimientos.py |
| `cat375_2008-2011_Defunciones.zip` | [375](https://microdatos.dane.gov.co/index.php/catalog/375/download/21417) | def. 2008-2011 | 86,4 | `c453d83d9b9cc7b9` | 2026-09-26 | 02_base_defunciones.py |
| `cat375_2008-2011_Nacidos.zip` | [375](https://microdatos.dane.gov.co/index.php/catalog/375/download/21415) | nac. 2008-2011 | 192,3 | `b6af620fdd501cee` | 2026-10-21 | 03_base_nacimientos.py |
| `cat377_2012-2013_Defunciones.zip` | [377](https://microdatos.dane.gov.co/index.php/catalog/377/download/5821) | def. 2012-2013 | 28,7 | `255cdbb50eb25f4d` | 2026-09-26 | 02_base_defunciones.py |
| `cat377_2012-2013_Nacidos_vivos_txt.zip` | [377](https://microdatos.dane.gov.co/index.php/catalog/377/download/5824) | nac. 2012-2013 | 44,0 | `82bd5cfca0d2657f` | 2026-10-21 | 03_base_nacimientos.py |
| `cat420_2014_Defunciones.zip` | [420](https://microdatos.dane.gov.co/index.php/catalog/420/download/21433) | def. 2014 | 24,7 | `22e7afbbc40065c5` | 2026-09-26 | 02_base_defunciones.py |
| `cat420_2014_Nacimientos.zip` | [420](https://microdatos.dane.gov.co/index.php/catalog/420/download/21435) | nac. 2014 | 44,2 | `e0cfb573d50451bc` | 2026-10-21 | 03_base_nacimientos.py |
| `cat475_2015_Defunciones.zip` | [475](https://microdatos.dane.gov.co/index.php/catalog/475/download/21430) | def. 2015 | 25,5 | `d10275e70865f44a` | 2026-09-26 | 02_base_defunciones.py |
| `cat475_2015_Nacimientos.zip` | [475](https://microdatos.dane.gov.co/index.php/catalog/475/download/21432) | nac. 2015 | 47,9 | `31373cd31f3205c2` | 2026-10-21 | 03_base_nacimientos.py |
| `cat519_2016_Defunciones.zip` | [519](https://microdatos.dane.gov.co/index.php/catalog/519/download/21427) | def. 2016 | 26,3 | `5586e353c61f00a9` | 2026-09-26 | 02_base_defunciones.py |
| `cat519_2016_Nacimientos.zip` | [519](https://microdatos.dane.gov.co/index.php/catalog/519/download/21429) | nac. 2016 | 51,9 | `ec806ca477bf6710` | 2026-10-21 | 03_base_nacimientos.py |
| `cat652_2017-2018_Defunciones.zip` | [652](https://microdatos.dane.gov.co/index.php/catalog/652/download/21421) | def. 2017-2018 | 54,0 | `dc38796d1d139e48` | 2026-09-26 | 02_base_defunciones.py |
| `cat652_2017-2018_Nacimientos.zip` | [652](https://microdatos.dane.gov.co/index.php/catalog/652/download/21423) | nac. 2017-2018 | 106,1 | `9e739653b83512bf` | 2026-10-21 | 03_base_nacimientos.py |
| `cat696_2019_Defunciones.zip` | [696](https://microdatos.dane.gov.co/index.php/catalog/696/download/21424) | def. 2019 | 32,6 | `fd59a4f366a3aafe` | 2026-09-26 | 02_base_defunciones.py |
| `cat696_2019_Nacimientos.zip` | [696](https://microdatos.dane.gov.co/index.php/catalog/696/download/21426) | nac. 2019 | 52,4 | `ec26f89f25489f19` | 2026-10-21 | 03_base_nacimientos.py |
| `cat732_2020_nac2020.zip` | [732](https://microdatos.dane.gov.co/index.php/catalog/732/download/21085) | nac. 2020 | 48,0 | `baa6532d7c7017b1` | 2026-10-21 | 03_base_nacimientos.py |
| `cat732_2020_nofetal2020.zip` | [732](https://microdatos.dane.gov.co/index.php/catalog/732/download/21082) | def. 2020 | 41,2 | `7e5f295eb70b3e22` | 2026-10-29 | 01_extraer.py y 02_base_defunciones.py |
| `cat775_2021_nacimientos2021.zip` | [775](https://microdatos.dane.gov.co/index.php/catalog/775/download/22160) | nac. 2021 | 46,3 | `2a5e1222daed3cd4` | 2026-10-21 | 03_base_nacimientos.py |
| `cat775_2021_nofetal2021.zip` | [775](https://microdatos.dane.gov.co/index.php/catalog/775/download/22162) | def. 2021 | 52,8 | `3ba80df7ce073eaa` | 2026-10-29 | 01_extraer.py y 02_base_defunciones.py |
| `cat807_2022_nac2022.zip` | [807](https://microdatos.dane.gov.co/index.php/catalog/807/download/23133) | nac. 2022 | 41,2 | `c6ca0d6e20fbb8fa` | 2026-10-21 | 03_base_nacimientos.py |
| `cat807_2022_nofetal2022.zip` | [807](https://microdatos.dane.gov.co/index.php/catalog/807/download/23132) | def. 2022 | 35,5 | `093f119965ef5aa4` | 2026-10-29 | 01_extraer.py y 02_base_defunciones.py |
| `cat876_2023_BD_EEVV_Nacimientos_2023.zip` | [876](https://microdatos.dane.gov.co/index.php/catalog/876/download/24250) | nac. 2023 | 34,2 | `a7c60978bf515ee6` | 2026-10-21 | 03_base_nacimientos.py |
| `cat876_2023_BD_EEVV_Defuncionesnofetales_2023.zip` | [876](https://microdatos.dane.gov.co/index.php/catalog/876/download/24249) | def. 2023 | 31,6 | `252a052580485a02` | 2026-10-29 | 01_extraer.py y 02_base_defunciones.py |
| `cat878_2024_BD_EEVV_Nacimientos_2024.zip` | [878](https://microdatos.dane.gov.co/index.php/catalog/878/download/24461) | nac. 2024 | 29,3 | `b98fcffe3c820a2d` | 2026-10-21 | 03_base_nacimientos.py |
| `cat878_2024_BD_EEVV_Defuncionesnofetales_2024.zip` | [878](https://microdatos.dane.gov.co/index.php/catalog/878/download/24462) | def. 2024 | 32,1 | `fc1948ddc27e70d7` | 2026-10-29 | 01_extraer.py y 02_base_defunciones.py |
| `BD-EEVV-Nacimientos-2025.zip` | [915](https://microdatos.dane.gov.co/index.php/catalog/915/download/24798) | nac. 2025 | 28,3 | `4a2414236842cbcd` | 2026-10-21 | 03_base_nacimientos.py |
| `cat915_2025_Defunciones.zip` | [915](https://microdatos.dane.gov.co/index.php/catalog/915/download/24800) | def. 2025 | 32,8 | `7c2772f92a012762` | 2026-10-20 | 01_extraer.py y 02_base_defunciones.py |

### Tabla B. Proyecciones de población y estimaciones demográficas

| Archivo en `data/raw/` | Producto | Tamaño (MB) | SHA-256 (primeros 16) | Descargado | Lo lee |
|---|---|---|---|---|---|
| `poblacion/PPED-AreaSexoEdadNac-1950-2017.xlsx` | nacional por área, sexo y edad 1950-2017 ([enlace](https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Nacional/PPED-AreaSexoEdadNac-1950-2017.xlsx)) | 0,5 | `fba186716ef94a10` | 2026-09-26 | 04_poblacion.py (1981-1984 y control 1985-1992) |
| `poblacion/dane_dep/DCD-area-sexo-edad-proypoblacion-dep-1985-1992.xlsx` | departamental por área, sexo y edad 1985-1992 ([enlace](https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Departamental/DCD-area-sexo-edad-proypoblacion-dep-1985-1992.xlsx)) | 1,5 | `aca9f6784d0aa2d4` | 2026-10-21 | 04_poblacion.py |
| `poblacion/dane_dep/DCD-area-sexo-edad-proypoblacion-dep-1993-2004.xlsx` | departamental por área, sexo y edad 1993-2004 ([enlace](https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Departamental/DCD-area-sexo-edad-proypoblacion-dep-1993-2004.xlsx)) | 2,2 | `2261e567fcf6bae5` | 2026-10-20 | 04_poblacion.py |
| `poblacion/dane_dep/DCD-area-sexo-edad-proypoblacion-dep-2005-2017_VP.xlsx` | departamental por área, sexo y edad 2005-2017 ([enlace](https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Departamental/DCD-area-sexo-edad-proypoblacion-dep-2005-2017_VP.xlsx)) | 2,4 | `ed08be6f708a5040` | 2026-10-20 | 04_poblacion.py |
| `poblacion/dane_dep/PPED-AreaSexoEdadDep-2018-2050_VP.xlsx` | departamental por área, sexo y edad 2018-2050 (actualización de julio de 2025) ([enlace](https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Departamental/PPED-AreaSexoEdadDep-2018-2050_VP.xlsx)) | 6,6 | `ba42efa193e9d194` | 2026-10-20 | 04_poblacion.py |
| `poblacion/dane_mun/DCD-area-sexo-edad-proypoblacion-Mun-1985-1994.xlsx` | municipal por área, sexo y edad 1985-1994 ([enlace](https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Municipal/DCD-area-sexo-edad-proypoblacion-Mun-1985-1994.xlsx)) | 41,2 | `6abac1fcaa9d37c3` | 2026-10-21 | 04_poblacion.py |
| `poblacion/dane_mun/DCD-area-sexo-edad-proypoblacion-Mun-1995-2004.xlsx` | municipal por área, sexo y edad 1995-2004 ([enlace](https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Municipal/DCD-area-sexo-edad-proypoblacion-Mun-1995-2004.xlsx)) | 42,8 | `728612eeae0dfdc3` | 2026-10-21 | 04_poblacion.py; A1 (61) lo lee directo |
| `poblacion/dane_mun/DCD-area-sexo-edad-proypoblacion-Mun-2005-2017_VP.xlsx` | municipal por área, sexo y edad 2005-2017 ([enlace](https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Municipal/DCD-area-sexo-edad-proypoblacion-Mun-2005-2017_VP.xlsx)) | 56,0 | `f804eb4408d2714c` | 2026-10-21 | 04_poblacion.py; A1 (61) lo lee directo |
| `poblacion/Mun-edad-2018-2042.xlsx` | municipal por área, sexo y edad 2018-2042 (actualización de julio de 2025; publicado como PPED-AreaSexoEdadMun-2018-2042_VP.xlsx) ([enlace](https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Municipal/PPED-AreaSexoEdadMun-2018-2042_VP.xlsx)) | 131,6 | `7e461635315664d4` | 2026-09-26 | 04_poblacion.py; A1 (61) y A4 (64) lo leen directo |
| `poblacion/Mun-2020-2035.xlsx` | municipal por área 2020-2035, actualización posCOVID-19 anterior (fecha interna 17 de marzo de 2023); ya no está en el portal del DANE (sin URL pública) | 1,9 | `4a696919048712ba` | 2026-09-26 | A4 (64) lo lee directo |
| `poblacion/dane_mor/DCD-Mor-EstSexNal-Dep-1985-2017_VP.xlsx` | estimaciones del cambio demográfico: tasas de mortalidad por sexo y edad simple, departamental 1985-2017 ([enlace](https://www.dane.gov.co/files/censo2018/cambio-demografico/DCD-Mor-EstSexNal-Dep-1985-2017_VP.xlsx)) | 1,8 | `5499df5a46d403fd` | 2026-10-20 | A1 (61, vía 35_completitud) lo lee directo |
| `poblacion/dane_mor/DCD-Mor-EstSexNal-Reg-2018-2070_VP.xlsx` | estimaciones del cambio demográfico: tasas de mortalidad por sexo y edad simple, nacional y regional 2018-2070 ([enlace](https://www.dane.gov.co/files/censo2018/cambio-demografico/DCD-Mor-EstSexNal-Reg-2018-2070_VP.xlsx)) | 2,2 | `f6ac96c4fdefa4a3` | 2026-10-20 | A1 (61, vía 35_completitud) lo lee directo |
| `poblacion/referencia/PPED-AreaNac-1950-2017.xlsx` | total nacional por área (950-2017.) ([enlace](https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Nacional/PPED-AreaNac-1950-2017.xlsx)) | 0,0 | `43cccbd8c33e3085` | 2026-10-29 | pruebas/test_insumos_eevv.py (total nacional publicado) |
| `poblacion/referencia/PPED-AreaNac-2018-2070.xlsx` | total nacional por área (018-2070.) ([enlace](https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Nacional/PPED-AreaNac-2018-2070.xlsx)) | 0,1 | `957239f522f79ada` | 2026-10-29 | pruebas/test_insumos_eevv.py (total nacional publicado) |

