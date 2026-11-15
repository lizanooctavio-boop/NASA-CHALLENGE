# Auditoría de usabilidad y claridad (Agente A)

- **Rama:** `codex/audit-usabilidad`
- **Alcance:** recorrido de usuario nuevo (sin formación estadística) sobre la primera pantalla, las 5 preguntas clave y la claridad de los veredictos, `What does this mean?` y `Learn`.

## Recorrido de las 5 preguntas

| Pregunta | Ruta y clics | Dónde dudó un usuario nuevo | Qué se entendió mal o faltó |
|---|---|---|---|
| 1. ¿Ha cambiado la lluvia en Nicaragua? | 1 clic (`Investigate`, ya abre en `Rainfall` → `Nicaragua`) o 1 clic (`Rainfall trend`) | Existen dos pestañas (`Investigate` y `Rainfall trend`) con la misma pregunta sin explicar la diferencia entre ambas. | Un usuario que entra por `Weather` (pestaña inicial) no ve ninguna pista de que el análisis de tendencias está en `Investigate`. |
| 2. ¿Se calienta el Mediterráneo? | 3 clics (`Investigate` → `Temperature` → `Mediterranean`) | En `Temperature` hay decenas de lugares mezclados sin filtro regional. | El veredicto dice *Trend detected*, pero la relación entre `Theil–Sen`, `Least squares` y `p < 0.001` requiere leer `Learn`. |
| 3. ¿Cuánto bosque ha perdido Nicaragua? | 4 clics (`Investigate` → `Vegetation` → `Nicaragua` → `Tree cover loss` / variable correspondiente) | No es obvio que «bosque» está bajo la categoría `Vegetation` hasta pulsarla. | Si el usuario solo mira `How much per decade`, puede confundir pérdida acumulada con tasa por década. |
| 4. ¿Qué significa «Methods disagree»? | 2–4 clics hasta un caso con desacuerdo + clic en `What does this mean?` (o ir a `Learn`) | `What does this mean?` es un enlace pequeño al pie de la definición, visualmente discreto. | Sin abrir `Learn`, no queda claro que «Methods disagree» significa que el resultado depende del método y por eso **no** se confirma tendencia. |
| 5. ¿De dónde salen los datos? | 1 clic (`Sources`) | Claro en el menú lateral. | Falta contexto rápido en `Investigate` sobre la diferencia entre fuentes primarias y `Cross-checks`. |

## Prueba de los 10 segundos (primera pantalla)

Al cargar la app, el usuario aterriza en `Weather` (`Point forecast` con `Latitude`/`Longitude` y un globo 3D). No hay ningún texto introductorio que explique qué es *Earth System Trend Detective* ni que invite a abrir `Investigate` para explorar las 217 investigaciones con veredicto estadístico. En 10 segundos parece una app de pronóstico meteorológico.

## Claridad de veredictos y «Learn»

- El artículo `#aprender-no-significativo` (*"Not significant" is not "no change"*) explica bien el concepto en `Learn`, pero en la tarjeta de resultado de `Investigate` el titular `Not enough evidence of a trend` no incluye una frase inmediata en lenguaje llano, por lo que un no experto tiende a leerlo como «no hubo cambio».

## Hallazgos

| ID | Gravedad | Dónde | Qué pasa | Cómo reproducirlo | Propuesta |
|---|---|---|---|---|---|
| A-01 | **bloqueante** | `index.html` (`#meteorologia`, cabecera/subtítulo) | La primera pantalla (`Weather`) no explica qué es *Earth System Trend Detective* ni guía al usuario hacia `Investigate`. | Abrir `/` y observar durante 10 s sin hacer clic. | Añadir un bloque de bienvenida claro en `#meteorologia` explicando el propósito de la app y qué hacer en `Weather` vs. `Investigate`. |
| A-02 | **alta** | `app/investigar.js` (`resultado()`), `app/estilos.css` | Los veredictos (`Not enough evidence of a trend`, `Methods disagree`, etc.) no muestran una frase llana inmediata bajo el título y el enlace `What does this mean?` pasa desapercibido. | Abrir `Investigate` en `Annual rainfall · Nicaragua` (`Not enough evidence of a trend`). | Añadir una línea breve de lectura en lenguaje llano bajo el veredicto y dar mejor jerarquía visual al enlace `What does this mean?`. |
| A-03 | **alta** | `index.html` (`#investigar`, `#tendencias`, `#indicadores`) | La diferencia de alcance entre `Investigate` (global, 8 temas), `Rainfall trend` (Nicaragua IMERG) y `Climate indicators` (Nicaragua por región) no se aclara en los subtítulos. | Alternar entre `Investigate`, `Rainfall trend` y `Climate indicators`. | Precisar los textos introductorios de las tres pestañas para evitar confusión al buscar lluvia en Nicaragua. |
| A-04 | **alta** | `index.html` (`#aprender`), `app/estilos.css` | Jerarquía visual plana entre veredicto, tarjetas estadísticas y definiciones; `Learn` no tiene guía rápida inicial para saltar a `Methods disagree` o `Not enough evidence`. | Abrir `Investigate` y `Learn` en escritorio (`1366×768`). | Reforzar tamaño/contraste de `.veredicto .estado`, `.tarjeta strong` y `.paso` en `app/estilos.css`, y añadir un índice breve en `#aprender .intro`. |
| A-05 | media | `app/investigar.js` (`#inv-lugares`) | En categorías con muchos lugares (`Temperature`, `Water`), los botones forman una lista larga sin agrupación o búsqueda. | Abrir `Investigate` → `Temperature`. | *(Propuesta)* Añadir filtro rápido o agrupación por continente/región en `Investigate`. |
| A-06 | baja | `index.html` / `app/investigar.js` (`#fuentes`) | La lista de datasets en `Sources` es larga y no permite filtrar por categoría o región. | Abrir la pestaña `Sources`. | *(Propuesta)* Agrupar `Datasets in this app` por categoría temática. |

## Capturas de referencia

- `docs/auditoria/img/usabilidad-01.png` a `docs/auditoria/img/usabilidad-06.png`.
