# Guion de la demo (ES / EN)

> **Formato oficial sin confirmar.** Dos búsquedas web coinciden en: video de hasta 30 s con subtítulos en inglés, o hasta 7 diapositivas en inglés, alojado en un enlace público. Provienen de copias de la guía (no del sitio oficial) y no confirman el año. Verificar en spaceappschallenge.org antes de grabar (ver [checklist-entrega.md](checklist-entrega.md)).

## Preparación (una vez)
Ejecutar `node scripts/preparar_render.mjs` y `node scripts/servidor.mjs` (ver [reproduccion.md](reproduccion.md)) y abrir la demo en `http://localhost:8000/?region=caja_original#tendencias`.

## Una sola interacción: de la caja original a Nicaragua
El jurado empieza en la pestaña **Rainfall trend** en la caja original (`Original SICC box`), hace **un clic en «Nicaragua»** (botón de región o sobre el mapa) y ve actualizarse, sobre el mismo dominio, el mapa, la pendiente, la gráfica de la serie y las descargas.

| Antes del clic · Original SICC box | Después del clic · Nicaragua |
|---|---|
| −13,1 mm/década; IC 95 % [−170,7; 144,5] | −62,3 mm/década; IC 95 % [−210,8; 86,1] |
| Área ≈ 66 500 km² (62 % es Nicaragua, el resto lagos, mar y norte de Costa Rica) | Área ≈ 119 900 km², sin los lagos |
| Insufficient evidence (`evidencia_insuficiente`) | Insufficient evidence (`evidencia_insuficiente`) |

**Qué cambió:** la estimación puntual (de −13,1 a −62,3 mm/década) porque cambió el área promediada. **Qué se mantiene:** la conclusión estadística: con 24 años de datos IMERG no se detecta una tendencia lineal significativa, porque ambos intervalos de confianza al 95 % incluyen cero.

## Texto narrado (≈ 30 s)
**Español**
> «Mismos datos de lluvia de NASA, dos escalas. En la caja original de SICC, la estimación es de unos −13 milímetros por década y el intervalo cruza el cero. Con un clic pasamos a Nicaragua: la estimación cambia a −62, pero el intervalo sigue cruzando el cero. Cambió el número; se mantiene la conclusión: con 24 años no detectamos una tendencia de lluvia anual. Costa Rica muestra por qué importa el método: dos métodos ven descenso y uno no.»

**English**
> “Same NASA rainfall data, two scales. In the original SICC box the estimate is about −13 millimeters per decade, and the interval crosses zero. One click takes us to Nicaragua: the estimate changes to −62, yet the interval still crosses zero. The number changed; the conclusion holds: with 24 years we cannot detect an annual rainfall trend. Costa Rica shows why method matters: two methods see a decline, one does not.”

## Si hay más tiempo (recorrido por las demás pestañas)
| Paso | Español | English |
|---|---|---|
| **Costa Rica** (`Rainfall trend`) | «Aquí dos intervalos excluyen el cero y Theil–Sen no (p = 0,097): el resultado depende del método.» | “Here two intervals exclude zero and Theil–Sen does not (p = 0.097): the result depends on the method.” |
| **Climate indicators** (`#indicadores`) | «Al contrastar fuentes independientes (GISTEMP e IMERG) con MERRA-2, detectamos calentamiento de +0,29 °C por década en Nicaragua y evitamos el salto artificial del reanálisis en 2002–2005.» | “By contrasting independent sources (GISTEMP and IMERG) against MERRA-2, we detect +0.29 °C per decade of warming in Nicaragua while avoiding the reanalysis step jump in 2002–2005.” |
| **El Niño & cyclones** (`#fenomenos`) | «El índice ONI y los ciclones históricos se muestran con datos reales como contexto de variabilidad interanual.» | “The ONI index and historical cyclones are shown with real data as interannual variability context.” |
| **Climate scenarios** (`#proyecciones`) | «Para 2041–2060, el ensamble de 6 modelos de NASA NEX-GDDP-CMIP6 proyecta entre +1,36 y +1,68 °C y una canícula más larga.» | “For 2041–2060, the 6-model NASA NEX-GDDP-CMIP6 ensemble projects +1.36 to +1.68 °C and a longer midsummer drought.” |

## Notas
- Todas las cifras salen de `data/clima.json` y `data/fenomenos_nicaragua.json` y se comprueban con `pytest tests -q`.
- No decir «no hay cambio»: decir «no se detecta una tendencia de lluvia anual con esta ventana de 24 años y estos métodos».
- No presentar los tres países como tres resultados independientes ni la caja y Nicaragua como dos muestras distintas (se solapan).
- El límite de 30 s es ajustado para el texto narrado; si el formato final es video, usar el bloque principal y mostrar las pestañas en plano continuo.
