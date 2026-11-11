# Lista de verificación RECORD del artículo A5

Declaración RECORD (Benchimol et al., 2015), extensión de STROBE para datos de salud recogidos de forma rutinaria. Se indica dónde se cumple cada punto en `manuscrito/manuscrito.md`.

| Punto | Qué pide | Dónde |
|---|---|---|
| 1.1–1.3 Título y resumen | Tipo de datos, región y periodo; bases usadas | Título; Resumen («Métodos»: registros de defunción del DANE, informe de la ADRES) |
| 2–3 Introducción | Contexto y objetivos | Introducción, párrafos 1 a 4 |
| 4 Diseño | Diseño del estudio | Métodos, «Diseño» (ecológico, serie y corte) |
| 5 Ámbito | Periodo, lugares | Métodos, «Fuentes» (Colombia, 1998–2025, 33 departamentos) |
| 6.1 Población | Cómo se seleccionó; códigos | Métodos, «Clasificación» (menores de 75, causa básica, CIE-10); `config/lista_aps_icsap2008.csv` |
| 6.2 Validación de códigos | Estudios de validación de los códigos | Métodos, «Sensibilidad» (mal definidas, códigos poco específicos); Discusión, limitaciones 1 a 3 |
| 6.3 Enlace de bases | Enlace entre bases | No hay enlace individual; el cruce con la ADRES es ecológico por departamento (Métodos, «Hospitalizaciones y muertes») |
| 7 Variables | Definición de resultados | Métodos, «Medidas»; cuadro 1 (19 grupos); `docs/DICCIONARIO.md` |
| 8 Fuentes y medición | Fuentes de cada variable | Métodos, «Fuentes»; `docs/INSUMOS.md` |
| 9 Sesgos | Cómo se trataron | Sensibilidad; escenario de omisión; limitaciones |
| 10 Tamaño | — | Población completa (6 218 747 registros) |
| 12.1 Acceso a la base | Acceso de los autores a la base | Microdatos públicos del ANDA del DANE; informe público de la ADRES |
| 12.2 Limpieza | Métodos de limpieza | Reparto de edad desconocida (Métodos, «Fuentes»); exclusión de residentes en el exterior (`docs/INSUMOS.md`) |
| 12.3 Enlace | Métodos de enlace | No aplica |
| 13 Participantes | Flujo de registros | Resultados, primer párrafo; `docs/INSUMOS.md` |
| 14–17 Resultados | Datos descriptivos, resultados, otros análisis | Resultados; cuadros 1, 2 y S1; figuras 1 a 3 |
| 18–20 Discusión | Resultados clave, limitaciones, interpretación | Discusión |
| 19.1 Limitaciones de datos rutinarios | Datos no creados para la pregunta; errores de clasificación | Discusión, limitaciones 1 a 5 |
| 21 Generalización | — | Discusión, párrafo 3 |
| 22 Financiación | — | Declaraciones |
| 22.1 Acceso a protocolo, datos y código | — | Declaraciones, «Disponibilidad de datos y código»; este repositorio |
