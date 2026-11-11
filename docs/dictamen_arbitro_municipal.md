# Dictamen del árbitro: análisis municipal (6 nov 2026)

*Dictamen producido por otra instancia de Claude (Anthropic), la misma herramienta usada para preparar el artículo, a la que se pidió actuar como árbitro. No es una revisión por pares externa.*

## Veredicto

Aceptable con revisiones menores. Cifras y transcripción exactas. Falta advertir la diferencia de potencia, quitar «anticipa» y hacer efectiva la supresión de 1 a 4 muertes.

## Recálculo

| Cifra | Recalculada = publicada |
|---|--:|
| Municipios / O ≥ 10 | 1 122 / 741 |
| Alta / baja, IC exacto | 138 (18,6 %) / 81 (10,9 %) |
| Marshall m; s²; a = b | 1,000; 0,1068; 9,36 |
| Alta / baja, bayesiano | 117 / 91 |
| p5–p95 suavizada (cruda) | 0,644–1,493 (0,364–1,762) |
| Concentración hosp./muertes/pob. | 54,3/46,5/42,3; 27 de 32 |
| Spearman departamental | −0,031 (IC 95 % −0,41 a 0,35) |

Por municipio, diferencia 0,000. `verificar_cifras.py`: 249 sin diferencias; `pytest`: 25 pasan.

## Transcripción

Tablas 6, 8, 9, 10 y 12: coinciden fila por fila con el PDF.

## Objeciones

1. **(d) Comparación de niveles. Moderada.** Con unas 58 muertes por municipio frente a unas 670 hospitalizaciones, el intervalo excluye 1 mucho menos en la mortalidad. Arreglo: añadir «con muchos menos eventos, el intervalo de la mortalidad excluye 1 con menos frecuencia; las dos proporciones no son comparables en nivel» y dar como principal la correlación entre las razones departamentales (−0,08).
2. **(b) Inferencia. Moderada.** Una ρ nula con intervalo de ±0,4 no demuestra ausencia de relación (texto 3).
3. **(a) Composición. Menor.** La sostienen el anexo 10.1.5 y Bogotá (15,2/19,5 = 0,78; tabla 6: 0,8). Pero con la tabla 5 no se reproducen Cundinamarca (0,88 frente a 1,7) ni San Andrés (0,45 frente a 1,9). Arreglo: «según su anexo (10.1.5)».
4. **(e) Omisión municipal. Moderada.** La limitación tercera es departamental. Añadir: «En municipios pequeños o periféricos, una razón baja puede reflejar omisión o residencia mal asignada en el certificado; ambas aumentarían el peso de la capital en las muertes, por lo que la brecha de concentración es conservadora».
5. **(f) Sexo. Menor.** Aceptable; mostrar en departamentos que el ajuste por sexo cambia poco.
6. **Confidencialidad. Moderada.** `aps_municipal_tablero.json` publica `top[].muertes_csaa75` (Supatá: 1). Además, O se despeja de `rme_eb` y `esperadas`: 0,536 × 19,36 − 9,36 ≈ 1. Arreglo: quitar ese conteo y publicar solo la clase cuando O esté entre 1 y 4.
7. **(c) Concentración.** Correcta.

## Errores de texto

1. Manuscrito, Resultados: «cuatro tuvieron mortalidad por debajo…». Ese conteo usa el intervalo bayesiano, no el exacto de los Métodos. Arreglo: «con la razón suavizada, cuatro…».
2. «el 49,0 % de 1 090». Arreglo: «el 49,0 % de los 1 090 de su tabla 6 (el texto dice 48,9 % de 1 091)».
3. Discusión: «tampoco anticipa dónde se muere más». Arreglo: «tampoco se asoció con la mortalidad municipal (Spearman −0,03; IC 95 % −0,41 a 0,35)».
4. Métodos: «mide composición del uso hospitalario, no frecuencia por habitante». Arreglo: «según su anexo (10.1.5), indica qué parte del uso hospitalario del municipio es evitable».
5. Nota 5c: «aunque la sección 6.3 hable de "tamaño poblacional"». Arreglo: «La sección 6.3 lo describe como ajustado por tamaño poblacional; la imprecisión es del equipo que redactó el informe, del que hizo parte el autor».
6. Nota 5c: «la razón baja viene de su total de hospitalizaciones, no de que hospitalicen poco». Arreglo: «su razón es baja porque su total de hospitalizaciones es alto, aunque hospitalicen por habitante más que el país».
7. Nota 5c: «lo que respalda la advertencia». Arreglo: «es compatible con la advertencia».
8. JS `seccionMunAps`: «no señala dónde se muere más». Arreglo: «no se asocia con la mortalidad». En `tablaTopMunAps`: «compara composición, no frecuencia» pasa a «mide composición del uso hospitalario».
