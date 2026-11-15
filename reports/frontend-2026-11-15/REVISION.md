# Revisión del frontend — 15 de noviembre de 2026

Revisión local del commit c5c1e02, en http://127.0.0.1:8996/. No se modificó el código de la aplicación durante la auditoría. Evidencias en esta carpeta; sondas reproducibles en su carpeta superior.

Nota de publicación: este informe se incorpora sobre main 2ad3c58 en una rama de documentación. Los hallazgos describen c5c1e02; no se ha comprobado si cambios posteriores los resolvieron. Los JSON y las capturas conservan los resultados originales.

Para reproducir: usar una copia de c5c1e02, copiar allí los dos scripts de `reports/`, disponer de Playwright y Chrome, e iniciar la aplicación con `INICIAR-APP.cmd`. Ejecutar `node reports/auditoria-frontend-2026-11-15.cjs` y `node reports/sonda-estado-frontend.cjs`. Playwright debe resolverse mediante la instalación local o `NODE_PATH`; las sondas no requieren rutas personales. La primera prueba usa el servidor local en el puerto 8996; la segunda simula servicios y reloj. Ambas sobrescriben sus resultados, por lo que conviene ejecutarlas en una copia de trabajo.

## Fallos, por prioridad

### P1 — La capa 3D mezcla datos antiguos con la corrida nueva

Ubicación: `app/globo.js:8–18`, `app/globo.js:25–40`.

La caché usa variable y paso, pero no la fecha de corrida. Al actualizarse los metadatos, `campo.js` limpia su caché 2D; `globo.js` conserva la suya. Se puede mostrar la hora de una corrida nueva sobre la textura y el viento de la anterior.

Reproducción aislada ejecutando el módulo real con servicios simulados: emitir `sicc:campo`, cambiar la corrida y emitirlo otra vez. Solo se hacen las dos peticiones originales; la segunda textura recibe metadatos nuevos y datos antiguos. Evidencia: `estado.json`, clave `globeCache`.

Corrección propuesta: compartir el proveedor de datos entre 2D/3D o incluir corrida en la clave y validar `corrida_utc` antes de pintar. Probar además respuestas tardías de una corrida anterior.

### P1 — «Now» puede identificar una hora antigua

Ubicación: `app/campo.js:31`, `app/campo.js:169–177`, `app/campo.js:198–199`.

La disponibilidad mundial solo comprueba que la corrida haya empezado. `indiceAhora()` devuelve el último índice cuando todas las horas están vencidas; `relativa()` lo etiqueta como `now` sin verificar la distancia temporal. El indicador también considera disponible esa malla.

Reproducción aislada de las funciones originales: serie del 1 de noviembre, reloj del 15 de noviembre; devuelve índice 1 y etiqueta `now`. Evidencia: `estado.json`, clave `expiredClock`. No se cargó una malla operativa para esta prueba.

Corrección propuesta: verificar el intervalo cubierto y distinguir archivo histórico de pronóstico vigente. Fuera de cobertura, deshabilitar «Now» y retirar su marcador; conservar fecha absoluta y antigüedad si se permite explorar el archivo.

### P2 — Sin WebGL no hay entrada automática al mapa

Ubicación: `app/espacio.js:16`, `app/shell.js:137–139`.

Chrome con los contextos WebGL desactivados: entrar en `/#map`, esperar más de cuatro segundos. Resultado: `Error creating WebGL context`, modo `globo`, mapa con `visibility:hidden`. El enlace depende de `espacio:listo`, evento que no llega si falla el constructor.

Corrección propuesta: capturar el fallo de inicialización, activar Leaflet, explicar la limitación y deshabilitar Globe. Procesar `#map` sin depender del éxito del 3D.

Evidencia: `resultados.json` y `no-webgl.png`. El resto de los paneles puede seguir funcionando; no es un bloqueo total de la aplicación.

### P2 — Un fallo transitorio deja Investigate sin reintento

Ubicación: `app/investigar.js:29–31`. Patrón equivalente en `app/indicadores.js:28`.

Interceptar únicamente la primera petición de `recursos_integrados.json` con 503; volver a Weather y abrir Investigate otra vez. Solo se hace una petición y el panel sigue vacío: `carga ??=` conserva la promesa rechazada. Learn y Sources comparten esa carga.

Corrección propuesta: limpiar la promesa tras el rechazo, mostrar un estado de error dentro del panel y un botón «Retry»; deshabilitar acciones que requieren datos. La reproducción en navegador cubre Investigate; la extensión a indicadores se identifica por inspección del mismo patrón.

Evidencia: `resultados.json`, clave `retry`.

## Mejoras para entender y usar el producto

1. **Entrada por una pregunta.** Ofrecer «¿Está cambiando la lluvia en Nicaragua?» al inicio, con acceso a Investigate. Hoy la entrada Weather presenta coordenadas y un pronóstico, y no hace evidente el objetivo de detectar tendencias.
2. **Separar tres horizontes temporales.** Identificar de forma persistente «Tiempo: próximas 48 horas», «Clima observado: período de cada serie» y «Escenarios: futuro condicionado por emisiones». Indicar en cada resultado región, variable, fuente, período y método.
3. **Conclusión antes del detalle estadístico.** Reutilizar Learn y los ejemplos guiados existentes. Explicar junto al resultado qué significa evidencia insuficiente y que no demuestra ausencia de cambio. Diferenciar claramente las pendientes Theil–Sen y mínimos cuadrados al navegar entre vistas, sin alterar cifras.
4. **Móvil: hacer visible el objeto que se pide pulsar.** A 375 × 800, navegación, cabecera y formulario ocupan casi toda la pantalla. Proponer una entrada con mapa visible y ficha plegable; añadir búsqueda de lugar y un ejemplo con Nicaragua. El texto «Click anywhere on the globe» tiene poca utilidad cuando el globo queda detrás de los paneles.
5. **Estado de datos por función.** En local se muestra «No model data», aunque los históricos de Investigate cargan. Aclarar que falta la malla meteorológica y mostrar por separado el estado del pronóstico puntual y de las series históricas. El README ya documenta la ausencia de mallas locales; no se clasifica esa ausencia como bug.
6. **Controles reconocibles.** Los tres puntos de color de cada ventana podrían acompañarse de etiquetas o ayudas visibles; dar una pista de desplazamiento al menú horizontal móvil. Añadir foco visible al canvas 3D, que ahora tiene `outline:none`.
7. **Datos históricos de ENOS.** Cuando se usa el CSV de respaldo hasta 2024, mostrar «Historical ONI» y su período junto a la fase, evitando una lectura de estado actual. La tarjeta ya incluye la temporada, pero la diferencia entre respaldo histórico y actualización operativa necesita mayor prominencia.

## Mapa del código para mantenimiento

| Archivo | Responsabilidad |
|---|---|
| `index.html`, `app/estilos.css` | Estructura, paneles y adaptación a pantalla |
| `app/shell.js` | Navegación, Leaflet, consulta puntual y transición de vistas |
| `app/espacio.js`, `app/teselas-globo.js` | Escena 3D, cámara y detalle satelital |
| `app/campo.js` | Mallas meteorológicas, reloj y capas 2D |
| `app/globo.js` | Adaptación de las capas meteorológicas a la escena 3D |
| `src/fuentes-meteo.js` | Enrutamiento a archivos estáticos y Open-Meteo |
| `src/tendencias.js` | Resultado histórico IMERG |
| `app/indicadores.js`, `app/investigar.js` | Indicadores y recorrido de investigación |
| `scripts/preparar_render.mjs` | Construcción de la carpeta public |

Conviene documentar los eventos `sicc:*`, su emisor, su carga útil y consumidores. El estado duplicado de datos y cachés entre módulos ya produce el primer fallo. Añadir un comando documentado para pruebas y dependencias: las sondas actuales requieren localizar Playwright fuera del proyecto.

## Comprobaciones y límites

- Compilación local correcta; repositorio del frontend sin cambios al terminar.
- Chrome real, sin errores JavaScript en el recorrido normal de las siete pestañas visitadas.
- Capturas revisadas: 1440 × 900, 375 × 800 y 768 × 800; también capturado 1280 × 800. No se encontró desbordamiento horizontal de la página en las tres anchuras de la sonda.
- Tres pruebas de geometría y seis de interfaz existentes correctas.
- Dos fallos reproducidos en navegador y dos con sondas aisladas del código original.
- No se auditó el despliegue público, la validez científica del conjunto completo, todos los botones/descargas, lectores de pantalla ni rendimiento en dispositivos físicos. Los servicios externos y la disponibilidad de mallas no equivalen a una prueba integral de la meteorología.
- Prioridad propuesta: corregir coherencia temporal y caché; añadir recuperación de errores; después mejorar entrada y móvil. Conservar las pruebas de regresión de esos cuatro casos.
