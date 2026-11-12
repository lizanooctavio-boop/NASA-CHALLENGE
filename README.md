# NASA-CHALLENGE
Prototipo climático de Nicaragua y su contexto regional para NASA Space Apps.

La portada muestra el campo mundial ECMWF IFS en un globo y las tendencias históricas de precipitación GPM IMERG (2001–2024). El visor 2D conserva las capas, la línea de tiempo regional, ENOS, ciclones, gráficas y proyecciones de temperatura y precipitación del visor SICC-952.

Para preparar la versión estática, ejecutar `node scripts/preparar_render.mjs` y `node scripts/preparar_meteo.mjs`. Servir el resultado con `python -m http.server 8982 --directory public`. Render ejecuta ambos comandos desde `scripts/preparar_render.sh`.

La compilación guarda corridas y archivos climáticos de la API pública de SICC-952. Las capas indican la fecha de la corrida y de la hora válida. Las consultas puntuales a Open-Meteo y las imágenes externas conservan su propia disponibilidad y hora. Los resultados históricos IMERG se empaquetan desde `data/` con su contrato.
