# Dictamen del árbitro: A5 (RPSP) y columna 09 (CONSULTORSALUD)

*Dictamen producido por otra instancia de Claude (Anthropic), la misma herramienta usada para preparar el artículo, a la que se pidió actuar como árbitro. No es una revisión por pares externa.*

## Veredicto
- **Artículo: revisión mayor.** Las cifras se reproducen sin error. Los problemas están en tres sitios: cómo se construye la REH, la inferencia sobre 33 departamentos y un lenguaje que va más allá del diseño ecológico.
- **Columna: revisión menor.** Hay que corregir cómo describe la fuente de la ADRES y moderar dos frases.
- **Bloqueante para ambos textos:** quedan los marcadores [confirmar] en el conflicto de intereses y en la declaración de uso de IA.

## Recálculo (código propio en pandas desde conteos.parquet, poblacion.parquet y el estándar OCDE)
| Indicador | Texto | Recálculo |
|---|---|---|
| Nacional 2023–2025 | 53,41 (53,00–53,82) | 53,410 (53,000–53,822) |
| Hombres / mujeres | 67,28 / 41,68 | 67,280 / 41,684 |
| 1998 | 106,84 (105,31–108,39) | 106,837 (105,309–108,383) |
| 2014 / caída 1998–2014 | 55,22 / 48,3 % | 55,217 / 48,32 % |
| 2025 | 54,00 (53,30–54,71) | 54,001 (53,298–54,712) |
| Chocó / Guainía / Bogotá | 79,90 / 79,68 / 36,85 | 79,905 / 79,677 / 36,850 |
| Departamentos por encima / por debajo | 18 / 6 | 18 / 6 (9 sin diferencia) |
| Muertes CSAA por año; % de las <75 | 22 084; 15,4 % | 22 083,8; 15,39 % |
| Muertes <75 en el trienio | 430 370 | 430 489 (+0,03 %; mi reparto de la edad desconocida es otro) |
| RME/REH >1 / <1; rho REH–RME; rho hospitalización–TEE | 19 / 11; 0,119; −0,255 | 19 / 11; 0,119 (p=0,51); −0,255 (p=0,15) |

Ninguna diferencia supera el 0,5 %. Los puestos de Risaralda, Quindío y Caldas (2–4 frente a 7, 11 y 12) también cuadran.

**ADRES frente al PDF.** Todas estas cifras coinciden con el PDF: 748 212 (tabla 1 y resumen); 19,5 % (748 212/3 832 336); 20,2 % y 8,36 billones (8,36/41,45); Guainía 123, Huila 30 032 y Chocó 3 896 (tabla 5); las bandas de edad 27,6/16,7/16,1/25,7/14,0 (tabla 4); la serie 151,1 a 98,8, es decir −34,6 %; y diabetes 34 308, ECV 44 217 e IVU 128 304.

**Verificadores.** `pruebas/verificar_cifras.py`: 203 comprobaciones, todo coincide. pytest: 18 pasan. Verificador de la columna: todo coincide. Ojo: estos verificadores prueban que el texto coincide con las salidas del código. No prueban que el método sea válido.

## Objeciones
1. **REH con un perfil de edad que no corresponde (mayor).** La tabla 4 de la ADRES es la distribución de *pacientes*, no de hospitalizaciones, y la propia ADRES advierte que es «aproximada». La recurrencia se concentra en los mayores de 80 años (48,2 % de la recurrencia severa). Por eso las esperadas de los departamentos viejos quedan bajas, su REH sube y su RME/REH baja. Además la REH usa 5 bandas y la RME usa 19. El texto no lo trata.
   *Arreglo:* en Métodos, «…armadas con la distribución por edad de los pacientes (no de las hospitalizaciones) que publica la ADRES en cinco bandas, que la fuente califica de aproximada (5)». Añadir una sensibilidad con REH cruda y reportar el Spearman de RME/REH entre las dos versiones.
2. **IC de Poisson y comparaciones múltiples (mayor).** 30 de los 33 cocientes y 24 de las 33 tasas salen «significativos». Eso es la huella de la sobredispersión: el IC ignora la incertidumbre de las esperadas y la variación extra-Poisson, y no corrige las 33 comparaciones.
   *Arreglo:* gráfico de embudo con sobredispersión (Spiegelhalter, 2005), o presentar los conteos como descriptivos: «En 19 departamentos el cociente fue mayor que 1 (IC de Poisson, sin ajuste por sobredispersión ni por comparaciones múltiples)».
3. **Lenguaje causal y diagnóstico (mayor).** «Es mayor donde se hospitaliza poco para las muertes que ocurren» es circular, porque es la definición de RME/REH. La asociación cruda que hay detrás es débil y no significativa (rho −0,255, p=0,15). Lo mismo pasa con «dos diagnósticos que piden intervenciones distintas».
   *Arreglo:* en el resumen y las conclusiones, «La mortalidad y la hospitalización evitables casi no se correlacionaron entre departamentos; en 19 las muertes superaron lo que anticipaban sus hospitalizaciones». En política, «…plantea hipótesis distintas (acceso frente a resolutividad) que deben verificarse con datos individuales».
4. **«Dejó de bajar hace una década» sin un análisis de tendencia (mayor).** El corte en 2014 se eligió después de ver los datos.
   - Por mi cuenta: entre 2014 y 2025, sin 2020–2021, la pendiente es −0,14 %/año (p=0,55). La mortalidad por todas las causas antes de los 75 también se estancó (−0,29 %/año, p=0,18), y la proporción CSAA no cambió (16,4 % frente a 16,7 %). El estancamiento no es propio de las CSAA.
   - El bloque cardiometabólico siguió bajando (−1,7 %/año, p<0,001).
   - El repunte infeccioso viene de las neumonías bacterianas (1,12 → 3,24 entre 2011 y 2025) y de las IVU (1,52 → 2,58), lo que sugiere cambios de codificación (J15.9/J18.1 frente a J18.9; A41 frente a N39.0). Con todas las J12–J18, la tasa pasa de 61,9 a 60,9 entre 2014 y 2025: el estancamiento se sostiene.
   *Arreglo:* joinpoint o regresión de Poisson segmentada con el cambio porcentual anual (APC) y su IC; poner la mortalidad general <75 como contexto; y en Discusión: «el repunte se concentra en neumonías bacterianas e infecciones urinarias y puede reflejar en parte cambios de codificación».
5. **Lista y comparabilidad de las fuentes (menor).** La aplicación a defunciones está bien tratada (limitación 1). Pero «la misma lista» es inexacto: la ADRES usa 20 grupos (Alfradique, adaptada por Rodríguez-García) con una ampliación operativa que pesa 0,46 %. En Resultados, el contraste 35 % frente a 3 % compara una tasa cruda de todas las edades con una estandarizada de menores de 75.
   *Arreglo:* añadir «cuya ampliación operativa suma 0,46 % de las hospitalizaciones (5)» y comparar con la tasa cruda de todas las edades. El escenario de omisión y la distinción RIPS/FEV-RIPS están bien manejados.

## Errores puntuales de texto
- Introducción, «20,2 % del gasto hospitalario del régimen contributivo y del subsidiado»: la fuente dice «SGSSS» y «gasto hospitalario nacional». Escribir «del SGSSS registradas en FEV-RIPS». El mismo problema aparece en la limitación 4 («no los regímenes especiales», que no tiene fuente) y en la columna, párrafos 2 y 9.
- «cuadros 1 y 5» / «cuadro 4»: en el informe se llaman tablas. Corregir aquí y en FUENTE.md.
- Columna: «la lista que Brasil construyó en 2008 … hasta 19 grupos» describe mal lo que hizo la ADRES. Escribir «la lista brasileña (Alfradique et al., 2009) en 20 grupos, adaptada a Colombia».
- Columna: «se muere bastante más» sobra: en 5 de los 19 departamentos el cociente está entre 1,07 y 1,11. Quitar «bastante».
- Columna: «las muertes tendrían que haber bajado también» es demasiado fuerte (rezagos, otras edades). Escribir «se esperaría que las muertes también bajaran».
- Columna: «Los RIPS cambiaron de cobertura en esos años» no está en la fuente. Escribir «los RIPS tienen una cobertura distinta de la FEV-RIPS (ADRES, 2026)».
- Columna, entradilla: «donde menos se hospitaliza no es donde menos se muere» roza la paralela negativa y se apoya en una asociación no significativa. Escribir «entre departamentos, las dos cuentas casi no se relacionan».
- Siglas sin glosar en la columna: ADRES, DANE, EPOC, RIPS y UGPP. En el manuscrito están todas glosadas.
- Estilo: ninguno de los dos textos tiene rayas ni muletillas vetadas (verificado con grep). El tono con la ADRES es respetuoso.

## Cumplimiento de la revista
- Título: 15 palabras, en el límite.
- Resumen: 231 palabras (abstract 201), estructurado.
- Cuerpo (de la Introducción a las Conclusiones): 2 639 palabras, por debajo de 3 500.
- Cuadros y figuras: 2 + 3 = 5.
- Referencias: 18, en orden de aparición.
- Formato numérico: espacio de millares y coma decimal correctos.
- RECORD, disponibilidad de datos y declaración de IA: presentes, pero quedan los [confirmar].
- Vancouver:
  - ref. 2: le falta volumen y páginas.
  - ref. 5: el enlace es de consultorsalud.com; usar la URL oficial de la ADRES.
  - ref. 13: es una transcripción secundaria; citar la Portaria en el Diário Oficial da União.
- PDF anónimo: no aparecen el nombre, Sinergística ni el empleo en la ADRES; la ref. 18 está retirada. Solo queda el [confirmar] de la declaración de IA.
