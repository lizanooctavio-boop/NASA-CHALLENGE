# Validación local: idiomas, experiencia de usuario y endurecimiento

Base revisada: `0c7184c` de `origin/codex/demo-render`. Rama local: `codex/frontend-ux-seguridad-local`. No se han creado commits, PR ni despliegues de esta implementación.

## Cómo probar

La copia de trabajo se sirve en <http://127.0.0.1:8996/#investigar>. Desde su raíz, para reconstruir y arrancar de nuevo:

```powershell
node scripts/preparar_render.mjs
node scripts/servir-local.mjs
```

El servidor solo escucha en `127.0.0.1`. No ejecutes un segundo servidor si ya responde ese puerto. Las capas meteorológicas de esta validación utilizan una instantánea local preexistente: su fecha se muestra en pantalla y, cuando corresponde, el aviso «Pronóstico caducado». No se descargó una corrida nueva. Mapas, librerías de terceros y consultas puntuales requieren sus proveedores habituales; no se promete funcionamiento completamente desconectado.

## Cambios implementados

- Selector English/Español con botones nativos, estado `aria-pressed`, foco visible y preferencia local validada. Inglés inicial y respaldo cuando no hay traducción. Almacenamiento opcional y sin llamadas a servicios de traducción.
- Actualización del idioma del documento, formatos regionales, ayuda y etiquetas de gráficas. Se conservan la investigación seleccionada, el mapa, la capa y la hora. Los CSV conservan los datos y su contrato original.
- Catálogo local de 1358 mensajes: incluye los 664 campos `*_en` de los recursos integrados, 298 notas únicas, 33 contrastes, 83 títulos y 97 definiciones. También contiene las 100 preguntas y respuestas de ayuda, Terra y las secciones explicativas. Se conservan nombres originales de referencias, marcas, DOI, autores, cifras y unidades cuando corresponde.
- Enlaces directos a secciones y navegación atrás/adelante; rutas desconocidas no se interpretan como selectores arbitrarios.
- Controles de idioma visibles en móvil y horizontal, botones táctiles de 44 px, menú lateral desplazable y ajustes para textos largos y movimiento reducido.
- Getter de almacenamiento protegido dentro de `try/catch`, para evitar cortar el arranque cuando el navegador lo bloquea.
- La instantánea meteorológica fuera de vigencia ya no se anuncia como actual ni etiqueta su última hora como «ahora». Se desactiva el botón Ahora cuando no hay una ventana vigente.
- Endurecimiento de texto en popups y etiquetas Leaflet, escape de metadatos en tooltips SVG y aceptación de enlaces de avisos únicamente con HTTPS. Son medidas preventivas; no equivalen a demostrar vulnerabilidades explotables en el despliegue.

## Skills aplicadas

Se obtuvieron copias locales de `ui-ux-pro-max` y `security-audit` en el directorio externo de skills de esta validación.

UI UX Pro Max orientó el uso de controles nativos con nombre y estado, foco no oculto, tamaños táctiles y reflujo del contenido. Se consultaron las guías concretas y se verificó su aplicación en navegador. Se conserva el sistema visual y el stack existentes: JavaScript, HTML/CSS, Leaflet, Chart.js y Three.js.

La revisión de seguridad es **parcial y estática**. El informe y sus límites están en `../audit-ux-seguridad/REPORT.md` respecto a la raíz de esta copia. No se ejecutaron pruebas ofensivas ni payloads contra la demo o proveedores. No se pudo acreditar el aislamiento completo exigido por la skill; además, sus validadores oficiales rechazan esta plataforma por falta de las garantías Windows no-follow/nonblocking. No se modificaron esas protecciones para obtener un pase. Las pruebas funcionales de desarrollo que siguen no son validación dinámica de seguridad.

## Comprobaciones ejecutadas

- `node --test tests/local-ux.test.cjs`: **8/8**, incluyendo ventana vigente, caché caducada, límite exacto de expiración, fechas inválidas y zona horaria.
- `python -m pytest tests/test_ayuda.py tests/test_interfaz.py tests/test_lugares_coordenadas.py tests/test_recursos_interfaz.py -q`: **33 passed, 12 subtests passed** con el entorno Python existente.
- `tests/validar-i18n-navegador.js` ejecutado en DevTools en la vista local: **15/15**, incluyendo ida/vuelta EN/ES, contenido dinámico, persistencia, preferencias no admitidas, selección y nodos del mapa conservados, ayuda sincronizada y CSV idéntico en ambos idiomas.
- Arranque con getter de `localStorage` que lanza `SecurityError`: inglés inicial, cambio a español, navegación y carga de Investigate correctos; sin errores JS en esa comprobación.
- Preferencia guardada no válida: regreso a inglés, sin bloquear el cambio posterior.
- Teclado: Tab desde English y Enter sobre Español cambian el idioma y conservan el foco en el botón activo.
- Recarga de `#investigar`, navegación a Aprender y vuelta mediante Atrás: sección y URL correctas.
- Resoluciones 360×740, 390×844, 768×1024, 1366×768, 1920×1080 y 844×390: sin desbordamiento horizontal y selector visible en el inicio de página. El primer pase encontró un desajuste horizontal en paisaje; se corrigió y se repitió ese caso con resultado correcto. Se probaron español e inglés y movimiento reducido en las vistas capturadas.
- Comprobación de sintaxis de los JavaScript modificados y reconstrucción estática correctas.

Las capturas English/Español de escritorio y móvil, y los resultados JSON de las comprobaciones del selector se guardan fuera del repositorio, en `../qa-local/`.

## Mantener traducciones

`app/locales/es.js` contiene pares de texto inglés/español; el texto inglés funciona como identificador estable. Para contenido nuevo usa `GnomonI18n.t('Message ID')` y agrega su traducción al catálogo. No insertes HTML desde una traducción ni traduzcas archivos fuente de datos o columnas de exportación.

`app/i18n.js` adapta el DOM heredado mediante nodos de texto y una lista limitada de atributos de presentación. Conserva los textos originales en WeakMaps para permitir volver a inglés. Su observador procesa solo nodos añadidos o modificados. Las nuevas pantallas deben preferir claves explícitas y los mensajes compuestos deben tener una plantilla revisada; no se utiliza traducción automática por sustitución arbitraria de palabras.

`GnomonI18n.missing()` permite revisar en memoria mensajes sin entrada; incluye nombres propios y metadatos que no necesariamente deban traducirse. No se envían esos textos fuera del navegador.

Para añadir un idioma se necesita su catálogo, inclusión explícita en los idiomas admitidos, opción accesible, locale y pruebas de ida/vuelta, respaldo y conservación de estado.

## Límites

La cobertura estática del catálogo no garantiza todos los mensajes que un proveedor pueda generar en el futuro. Un mensaje no reconocido usa inglés como respaldo. Los títulos originales de publicaciones, nombres propios, códigos y atribuciones pueden conservarse en su idioma de origen.

La revisión visual y el teclado se probaron en Chromium. No se certifica WCAG AA, Safari/Firefox ni lectores de pantalla reales con estas comprobaciones. La auditoría completa de seguridad sigue pendiente de un entorno compatible con el aislamiento y los validadores de la skill.
