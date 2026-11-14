# NASA-CHALLENGE
Prototipo climático para NASA Space Apps 2026 (Earth System Trend Detective). Interfaz en inglés.

La demo abre en la pestaña **Rainfall trend** con Nicaragua seleccionada: la pregunta del reto, la variable, el período, la fuente, el selector de región y el resultado. La portada es una escena 3D (Three.js): la Tierra con NASA Blue Marble y luces nocturnas VIIRS, la Luna (LRO), el Sol y estrellas. Sobre ella están los paneles de cristal: tiempo con pronóstico puntual mundial, tendencia de lluvia anual GPM IMERG 2001–2024 en Nicaragua y su contexto, El Niño y ciclones, escenarios CMIP6 y descargas. El botón **Map** aplana el globo en proyección Mercator con América al centro y lo funde con el mapa Leaflet (mosaico Blue Marble de GIBS y capas meteorológicas). `visor/` redirige a `/#map`.

Estructura: `index.html`, `app/` (armazón, escena 3D, capas y fenómenos), `src/` (fuentes, paletas, estadística y tendencia), `assets/` (texturas NASA y Natural Earth), `data/` (resultados IMERG con su contrato).

Para preparar la versión estática, ejecutar `node scripts/preparar_render.mjs` y `node scripts/preparar_meteo.mjs`. Servir el resultado con `python -m http.server 8982 --directory public`. Render ejecuta ambos comandos desde `scripts/preparar_render.sh`.

Texturas: Blue Marble Next Generation y VIIRS Black Marble (NASA GIBS, dominio público); Luna: NASA SVS CGI Moon Kit (LRO). Campos meteorológicos ECMWF IFS (CC BY 4.0) vía la API de SICC-952 y Open-Meteo.
