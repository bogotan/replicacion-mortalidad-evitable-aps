# Revisión de árbitro simulada y respuestas

Árbitro: otra instancia de Claude (Anthropic), la misma herramienta usada para preparar el artículo, a la que se pidió actuar como árbitro sin acceso a la conversación en que se escribió; no es una revisión por pares externa. 5 de noviembre de 2026. Dictamen completo en `docs/dictamen_arbitro.md`. Recalculó con código propio las tasas nacional, por sexo, de 1998, 2014 y 2025, las de Chocó, Guainía y Bogotá, los conteos 18/6 y 19/11 y las correlaciones; ninguna diferencia superó 0,5 %. Cotejó con el PDF de la ADRES las cifras usadas.

Veredicto: artículo, revisión mayor; columna, revisión menor. Bloqueante para ambos: los marcadores [confirmar] (dependen del autor).

## Contenido

1. Objeciones y respuestas
2. Errores puntuales corregidos
3. Lo que queda pendiente

## 1. Objeciones y respuestas

| # | Objeción | Respuesta | Dónde |
|---|---|---|---|
| 1 | La REH usa la distribución por edad de *pacientes* (tabla 4 de la ADRES), con 5 bandas, y la supone igual en todos los departamentos | Se dice en Métodos y en las limitaciones. Nueva sensibilidad con la razón cruda de hospitalización: el ordenamiento del cociente RME/REH casi no cambia (Spearman 0,978) y los tres mayores siguen siendo Guainía, Vichada y Chocó | `sensibilidad.py:reh_cruda()`; Métodos, Resultados, Discusión |
| 2 | IC de Poisson con 33 departamentos: casi todos «significativos», señal de sobredispersión | Nuevo ajuste cuasi-Poisson (gráfico de embudo): factor de dispersión 79,0 en las tasas y 86,2 en el cociente. Con esos límites solo Bogotá queda por debajo del país en la tasa, y solo Huila y Bogotá en el cociente; ninguno por encima. Los conteos 18/6 y 19/11 se presentan como descriptivos de intervalos que solo recogen el azar | `sensibilidad.py:sobredispersion()`; Métodos, Resultados, Discusión, cuadro S1 |
| 3 | Lenguaje causal y circular («es mayor donde se hospitaliza poco»; «dos diagnósticos que piden intervenciones distintas») | Reescrito: «la hospitalización evitable de un departamento no predice su mortalidad evitable»; «dos hipótesis que conviene investigar por separado»; se agrega que el diseño ecológico no permite atribuir el patrón | Resumen, Discusión, Conclusiones; columna |
| 4 | «Estancamiento desde 2014» sin análisis formal; ¿es propio de las CSAA? | Nuevo CPA por regresión log-lineal: −4,46 % anual en 1998–2014 y −0,14 % (−0,64 a 0,37) en 2014–2025 sin 2020–2021. La mortalidad general antes de los 75 también se estancó (−0,29 %; −0,75 a 0,17): se dice. El repunte infeccioso se concentra en neumonías bacterianas (1,12 a 3,24) e infecciones urinarias (1,52 a 2,58), con la hipótesis de cambios de codificación. No se hizo joinpoint; el CPA por tramos predefinidos basta para lo que afirma el texto | `sensibilidad.py:tendencia()`, `grupos()`; Resultados, Discusión |
| 5 | «La misma lista» es inexacto (la ADRES usa 20 grupos y una ampliación del 0,46 %); 35 % frente a 3 % compara una tasa cruda de todas las edades con una estandarizada de menores de 75 | Se describe la lista de la ADRES con la ampliación (cifra del informe). Se agrega la tasa cruda de mortalidad de todas las edades, que subió 4 % (115,65 a 119,84) | Métodos, Resultados; columna |

## 2. Errores puntuales corregidos

- «del régimen contributivo y del subsidiado»: no está en la fuente. Se quitó del artículo y de la columna; la limitación habla de cobertura poblacional distinta.
- «cuadros» de la ADRES: el informe los llama tablas.
- Columna: «hasta 19 grupos» pasó a 20 grupos de la ADRES y versión oficial de 19; se quitó «bastante más» y los conteos 19/11; «las muertes tendrían que haber bajado» pasó a «se esperaría que bajaran»; «los RIPS cambiaron de cobertura» pasó a la advertencia de la propia ADRES (pág. 55 del informe; la ampliación de 0,46 %, pág. 70); la entradilla ya no usa la forma «no es donde»; se glosaron ADRES, DANE, EPOC, RIPS y UGPP.
- Referencia 2: es una publicación anticipada en línea sin volumen ni páginas; se indica así.

## 3. Lo que queda pendiente

- El [confirmar] de la declaración de uso de IA depende del autor. El conflicto de intereses quedó resuelto el 5 de noviembre: el autor lideró el equipo que elaboró el informe de la ADRES, y así se declara.
- La referencia 5 enlaza a la copia del informe alojada en consultorsalud.com; si la ADRES lo publica en su sitio, cambiar la URL.
- La referencia 13 es una transcripción secundaria de la Portaria 221; si se consigue el texto en el Diário Oficial da União, citarlo.
- La vista del tablero dice «por encima del país con un intervalo que no lo toca» con la advertencia de que el intervalo solo mide el azar; conviene agregar la nota de sobredispersión en la próxima versión del tablero.

## 4. Ampliación del 6 de noviembre: territorios y municipios

A pedido del autor se agregó el análisis territorial y municipal del informe HECSAP (tablas 6, 8, 9, 10 y 12) frente a la mortalidad municipal (`src/aps_evitable/municipal.py`, idéntico byte a byte al `scripts/43b_aps_municipal.py` del repositorio EEVV). En el manuscrito: un párrafo en Métodos, uno en Resultados, dos frases en la Discusión, una limitación y el cuadro suplementario S2; referencia nueva de Marshall (1991). El cuerpo quedó en 3 489 palabras y el resumen en 250. Se señalan en la nota técnica y en el tablero dos inconsistencias del informe (la tabla 6 suma 1 090 municipios y el texto dice 1 091; la definición del O/E en el anexo A mide composición, aunque la sección 6.3 hable de tamaño poblacional).

Árbitro simulado de la ampliación (otra instancia de Claude) (6 de noviembre; `docs/dictamen_arbitro_municipal.md`): recalculó desde `municipal_csaa.parquet` los conteos, la clasificación y el suavizado de Marshall (diferencia 0,000 municipio por municipio) y cotejó las tablas 6, 8, 9, 10 y 12 con el PDF (sin diferencias). Pidió revisión menor. Cambios: se advierte la menor potencia de la mortalidad (unas 59 muertes por municipio en tres años frente a unas 670 hospitalizaciones al año); «no anticipa» pasó a «no se asoció», con el IC de la correlación (−0,41 a 0,35); la definición del O/E de la ADRES se atribuye a su anexo; la clasificación de los diez de cada extremo dice que usa la razón suavizada; se cita el 48,9 % de 1 091 del texto de la ADRES; se agregó la omisión municipal; y en el tablero y el cuadro S2, con 1 a 4 muertes ya no se publican las esperadas ni las razones (se despejaba el número), solo la clase.
