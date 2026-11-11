# Hospitalizaciones evitables de la ADRES (insumo del estudio 43)

**Documento.** ADRES, Innovación y Analítica (julio de 2026). *Hospitalizaciones evitables por condiciones sensibles a la Atención Primaria (HECSAP) en Colombia*. Publicado en https://consultorsalud.com/wp-content/uploads/2026/07/Hospitalizaciones_evitables_por_condiciones_sensibles_a_la_Atencion_Primaria.pdf (nota de prensa: https://consultorsalud.com/hospitalizaciones-evitables-dif-terri-aps-adres/).

**Copia transcrita.** La que entregó el autor el 5 de noviembre de 2026 (73 páginas; SHA-256 `9207d6f72cd1ec6b74b030f3ce658d91555dd0f03809299e4e4685432653481b`). Esa copia trae un comentario de revisión al margen en la página 54; no se verificó que sea idéntica a la publicada.

**Archivos (transcripción manual, verificada por `tests/verificar_aps.py`):**

| Archivo | De dónde sale | Verificación |
|---|---|---|
| `adres_hecsap_2025_departamentos.csv` | Cuadro 5 (págs. 22–24): hospitalizaciones totales y HECSAP, porcentaje, tasa por 10.000 y gasto por departamento de residencia, FEV-RIPS 2025 | El porcentaje de cada fila cuadra con sus conteos; las tasas implican la misma población del DANE 2025 del repositorio (diferencia < 0,5 %) |
| `adres_hecsap_2025_condiciones.csv` | Cuadro 2 (pág. 16): pacientes, hospitalizaciones y costo de las 20 condiciones; `grupo_csaa` las lleva a los 19 grupos de la Portaria 221 (inmunoprevenibles y «condiciones evitables» son el grupo 1) | Suman 748.212 hospitalizaciones y 8,36 billones, como el cuadro 1 |
| `adres_hecsap_2025_edad.csv` | Cuadro 4 (pág. 20): distribución por edad de los pacientes HECSAP del país | Suma 100,1 % (redondeo de la fuente) |
| `adres_hecsap_serie_nacional.csv` | Figura 6 (pág. 51), RIPS 2019–2024, y cuadro 1 (2025, FEV-RIPS) | Rótulos de la figura |

**Tablas territoriales y municipales (añadidas el 6 de noviembre de 2026; transcripción manual, verificada contra el texto del PDF por `tests/verificar_aps.py`):**

| Archivo | De dónde sale | Verificación |
|---|---|---|
| `adres_hecsap_2025_oe_departamentos.csv` | Tabla 6 (pág. 32): municipios por clase de la razón O/E (alta, esperada, baja) y O/E ponderado por departamento | Cada fila suma sus municipios; los porcentajes cuadran con los conteos (±0,05). La tabla suma 1.090 municipios; el texto dice 1.091 |
| `adres_hecsap_2025_oe_top_municipios.csv` | Tablas 8 y 9 (págs. 41 y 43): los diez municipios con O/E más alto y más bajo (n ≥ 30) | Cada O/E dentro de su intervalo |
| `adres_hecsap_2025_concentracion.csv` | Tabla 10 (págs. 47–48): municipio de mayor peso en las hospitalizaciones HECSAP de cada departamento | El peso cuadra con la tabla 5 salvo Chocó (67,0 frente a 65,8) y Guainía (77,5 frente a 75,6), que parecen usar otro total |
| `adres_hecsap_tendencias_2019_2024.csv` | Tabla 12 (pág. 72): tendencia 2019–2024 de ocho departamentos (Arauca y Risaralda sin datos) | Rótulos de la tabla |

**Qué mide el O/E municipal de la ADRES.** El anexo A (10.1.5) lo define como hospitalizaciones HECSAP observadas sobre el total de hospitalizaciones del municipio por la proporción nacional de HECSAP (19,5 %). Mide composición del uso hospitalario, no frecuencia por habitante, aunque el texto de la sección 6.3 hable de «tamaño poblacional». Por eso un municipio puede tener O/E bajo y una tasa por habitante alta (Armenia, Antioquia: O/E 0,178 y unas 339 hospitalizaciones HECSAP por 10.000 habitantes con la población del DANE).

**Inconsistencia de la fuente.** Las hospitalizaciones totales del cuadro 5 suman 4.402.548 entre departamentos; el cuadro 1 da 3.832.336 para el país (15 % menos). Las HECSAP sí cuadran (746.822 con residencia conocida frente a 748.212). Por eso no se usa el porcentaje HECSAP por departamento, solo los conteos y tasas HECSAP.

**Términos.** Documento público de una entidad estatal; se usan cifras agregadas con cita.
