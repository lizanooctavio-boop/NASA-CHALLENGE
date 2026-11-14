# Zoom satelital del globo — 2026-11-14

Base: `bfa011f`, versión de Claude con Esri World Imagery en Leaflet. Rama de implementación: `codex/globo-detalle-progresivo`.

La esfera usaba una sola textura global y no solicitaba imágenes adicionales al acercarse. Se conserva Three.js y la transición original hacia Leaflet; se añade un árbol de teselas Web Mercator del mismo servicio satelital que ya utiliza el mapa 2D.

## Comportamiento

- Selección por tamaño proyectado en pantalla, campo de visión y horizonte; hasta nivel 17. El límite real de detalle depende de la cobertura del proveedor.
- Descarga únicamente de la vista y sus ancestros; seis solicitudes concurrentes, cancelación al salir de la vista, tiempo máximo por solicitud y reintento diferido ante errores.
- Máximo de 150 hojas visibles y 280 teselas necesarias, caché de 320 entradas con liberación de texturas, geometrías y bitmaps. Al terminar la carga se dibuja solo el detalle necesario.
- Los ancestros y Blue Marble sirven de respaldo durante la carga o ante una interrupción de red. Los polos fuera de Web Mercator conservan la textura NASA.
- El shader mantiene iluminación, luces nocturnas, meteorología y viento. Se descarta explícitamente la cara posterior y se dibujan niveles de menor a mayor detalle sin comparar profundidades coincidentes, evitando parpadeos a escala local.
- Zoom proporcional a la altura sobre la superficie, plano de recorte cercano adaptable, arrastre y teclado proporcionales a la escala. La rotación automática se detiene al acercarse. Altura mínima aproximada: 1,27 km sobre la esfera unitaria escalada a la Tierra.
- Atribución satelital visible en modo 3D; la interfaz sigue en inglés.

## Verificación

`node --test tests/teselas-geometria.test.mjs`: tres pruebas de coordenadas, jerarquía, antimeridiano, polos, límites de zoom y escala de arrastre.

`python -m unittest discover -s tests -p test_interfaz.py`: seis pruebas de correspondencia entre los datos y la interfaz.

`node scripts/preparar_render.mjs`: compila los módulos y recursos en `public/`.

`tests/globo-detalle.cjs` usa Playwright y Chrome con WebGL real. Verifica descargas satelitales, aumento del nivel de detalle, límites de recursos, rueda/arrastre, ausencia de errores JS/WebGL y cambio de mapa a globo. Produce capturas regionales, urbanas, esfera, pérdida de proveedor y viewport móvil en `reports/globo-detalle/` (no versionadas). La capa azul de la captura meteorológica es un estímulo de prueba del shader, no un dato científico ni un producto publicado.

Para ejecutar la prueba, Playwright debe estar disponible en Node; puede utilizarse `NODE_PATH` del runtime local de Codex sin agregar dependencias de producción.

Resultado final: 357 respuestas satelitales correctas; nivel 9 en vista regional y 16 en Managua. En la captura urbana se dibujaron 48 teselas, con 144 entradas en caché. Ningún error JavaScript ni de shaders/WebGL. Capturas regional, urbana, esfera y viewport de 390 × 844 revisadas visualmente. Las nueve pruebas de geometría e interfaz pasaron. El ensayo meteorológico comprueba la composición gráfica mediante una textura de prueba, no la disponibilidad de datos meteorológicos en vivo.

## Alcance

Mejora de imágenes sobre una esfera: no añade elevaciones reales, edificios 3D ni imágenes satelitales en vivo. No altera datos científicos ni implementa la actualización de pronósticos. El entorno estático local carece de la malla meteorológica generada durante el despliegue, por lo que muestra «No forecast data». No se ha publicado en Render.
