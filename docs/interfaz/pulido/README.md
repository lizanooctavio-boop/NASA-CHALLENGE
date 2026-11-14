# Pulido de la interfaz: pestaña «Rainfall trend»

Rama `codex/pulido-interfaz`, creada sobre `codex/recursos-interfaz` (PR #10). No cambia el contrato de datos (`data/clima.json` 1.0.0), los cálculos ni el contenido de las descargas.

## Cambios

1. **Primera pantalla.** La demo abre en «Rainfall trend» con Nicaragua seleccionada. Muestra la pregunta del reto, una ficha con la variable (lluvia anual, mm/año), el período (2001–2024, 24 años), la fuente (NASA GPM IMERG Final V07B) y el área con su superficie, el selector de región y el veredicto. La pregunta y la ficha cambian con la región. La pestaña pasa al primer lugar del menú.
2. **Comparación de intervalos.** La comparación va justo después del veredicto, en una escala común en mm/década y con la línea del cero rotulada en todos los anchos («0 = no change»). Cada intervalo lleva el rótulo «LS» o «TS», además de la forma y el trazo, para no depender del color. Una frase explica por qué un intervalo que cruza el cero deja evidencia insuficiente. En Costa Rica, el veredicto dice qué métodos excluyen el cero y cuáles lo incluyen. Debajo hay una tabla desplegable, «Figures as text», con las cifras de las cuatro áreas.
3. **Mapa, gráfica y descarga.** En el mapa 2D se dibujan las cuatro áreas. La elegida aparece resaltada, con su nombre y su veredicto, y un clic sobre un área la selecciona. El botón «Show area on the map» encuadra la región. Si no queda hueco junto al panel, a 800 px o en el móvil, oculta los paneles. El título de la serie y la cabecera del CSV anual (`# Area: …`) nombran la misma área.
4. **Panel sin solapes.** En las pestañas de análisis se ocultan la barra de capas, la línea de tiempo y el indicador meteorológico, y el panel gana ancho. «Weather» y «El Niño & cyclones» los conservan. En «Rainfall trend», un clic en el globo ya no abre el pronóstico. También se corrigió el doble envío que hacía cada clic en el globo en `app/globo.js`.
5. **Accesibilidad y estados.** La cifra principal tiene una lectura para lectores de pantalla («minus 62.3 mm/decade»). La gráfica comparativa incluye en su descripción el veredicto y el intervalo de cada área. El detalle de los tres métodos es desplegable. Mientras se cargan los datos se muestra un estado de carga, y si fallan aparece un mensaje de error con un botón «Try again». Si una gráfica no se puede dibujar, se muestran sus cifras en una tabla.

## Comprobaciones

- Capturas a 390, 800 y 1440 px con los datos reales de `data/clima.json`, servidos desde `public/` (`node scripts/preparar_render.mjs`) en Chrome sin interfaz. Las capturas `antes_*` corresponden al commit 91ede22 y las `despues_*` a esta rama. A 1440 px solo hay captura previa de la portada.
- Estados simulados en el navegador: el JSON responde 503 (aparece el error con «Try again»); Honduras con 7 años válidos (aparece «Missing data» y su fila «no trend available»); SVG desactivado (se abre la tabla de cifras y la serie anual aparece como tabla).
- Teclado: las flechas recorren el selector (Nicaragua → Costa Rica), y solo un botón queda con `tabindex=0`. La pregunta se actualiza con la región. El foco visible depende de la regla `:focus-visible` existente.
- `python -m unittest tests.test_e2e_navegador tests.test_interfaz`: 13 pruebas correctas. `tests/test_recursos_interfaz.py` necesita `pytest`, que no está instalado en este equipo.

## Pendiente

- Probar el recorrido con lector de pantalla real (NVDA o VoiceOver) y medir el contraste con una herramienta. Solo se revisaron los colores a ojo.
- En el móvil, la barra superior y el menú ocupan unos 300 px antes del panel. El veredicto queda visible, pero la cifra principal aparece al desplazar.
- Las capas meteorológicas siguen activas en el mapa 2D si el usuario las enciende desde «Weather» y vuelve a la tendencia.
- Coordinar con Astral antes de fusionar: los cambios tocan `index.html`, `app/estilos.css`, `app/shell.js`, `app/globo.js`, `src/tendencias.js`, `src/graficas.js` y `src/contrato.js` (solo se conserva `area_km2` al normalizar).
- El despliegue queda a decisión de Octavio.
