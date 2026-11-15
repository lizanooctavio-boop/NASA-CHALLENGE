# Validación local: idiomas, experiencia de usuario y endurecimiento

La validación de Configuración usa `20bec48` de `origin/codex/demo-render` como base. La revisión estática de seguridad comenzó sobre `0c7184c`.

## Cómo probar

La copia de trabajo se sirve en <http://127.0.0.1:8996/#configuracion>. Desde la raíz del repositorio:

```powershell
node scripts/preparar_render.mjs
node scripts/servir-local.mjs
```

El servidor solo escucha en `127.0.0.1`. No ejecutes un segundo servidor si ya responde ese puerto. Las capas meteorológicas de esta validación utilizan una instantánea local preexistente: su fecha se muestra en pantalla y, cuando corresponde, el aviso «Pronóstico caducado». No se descargó una corrida nueva. Mapas, librerías de terceros y consultas puntuales requieren sus proveedores habituales; no se promete funcionamiento completamente desconectado.

## Cambios implementados

- **Configuración** en el menú lateral agrupa idioma y tema. Desde Ayuda, el acceso a idioma abre Configuración y enfoca la opción activa.
- Botones English/Español y Claro/Oscuro con estado `aria-pressed`, foco visible y preferencias locales validadas. La primera visita usa inglés y tema oscuro. Si el almacenamiento está bloqueado, ambas preferencias funcionan durante la sesión.
- El tema claro se aplica a menús, paneles, formularios y etiquetas de gráficas. El mapa y las escalas cromáticas científicas conservan su representación. En pantallas pequeñas las opciones se distribuyen debajo de su etiqueta.
- Actualización del idioma del documento, formatos regionales, ayuda y etiquetas de gráficas. Se conservan la investigación seleccionada, el mapa, la capa y la hora. Los CSV conservan los datos y su contrato original.
- El catálogo incluye los campos `*_en` de los recursos integrados, las preguntas frecuentes, el recorrido de Terra y la interfaz de Configuración. Se conservan las referencias originales y los valores científicos.
- Enlaces directos a secciones y navegación atrás/adelante; rutas desconocidas no se interpretan como selectores arbitrarios.
- Controles de idioma visibles en móvil y horizontal, botones táctiles de 44 px, menú lateral desplazable y ajustes para textos largos y movimiento reducido.
- Getter de almacenamiento protegido dentro de `try/catch`, para evitar cortar el arranque cuando el navegador lo bloquea.
- La instantánea meteorológica fuera de vigencia ya no se anuncia como actual ni etiqueta su última hora como «ahora». Se desactiva el botón Ahora cuando no hay una ventana vigente.
- Endurecimiento de texto en popups y etiquetas Leaflet, escape de metadatos en tooltips SVG y aceptación de enlaces de avisos únicamente con HTTPS. Son medidas preventivas; no equivalen a demostrar vulnerabilidades explotables en el despliegue.

## Skills aplicadas

Se obtuvieron copias locales de `ui-ux-pro-max` y `security-audit` en el directorio externo de skills de esta validación.

UI UX Pro Max orientó el uso de controles nativos con nombre y estado, foco no oculto, tamaños táctiles y reflujo del contenido. Se consultaron las guías concretas y se verificó su aplicación en navegador. Se conserva el sistema visual y el stack existentes: JavaScript, HTML/CSS, Leaflet, Chart.js y Three.js.

La revisión de seguridad fue **parcial y estática**. La skill exige aislamiento de ejecución y validadores compatibles. En Windows, los validadores informaron que las garantías de apertura de archivos sin seguir enlaces y en modo no bloqueante no estaban disponibles. [Informe de seguridad](INFORME_SEGURIDAD_FRONTEND.md)

## Comprobaciones ejecutadas

- `node --test tests/local-ux.test.cjs`: **8/8**, incluyendo ventana vigente, caché caducada, límite exacto de expiración, fechas inválidas y zona horaria.
- `python -m pytest tests/test_ayuda.py tests/test_interfaz.py tests/test_lugares_coordenadas.py tests/test_recursos_interfaz.py -q`: **33 passed, 12 subtests passed** con el entorno Python existente.
- `tests/validar-i18n-navegador.js`, ejecutado desde Investigate en Chromium: **19/19**. Cubre Configuración, los dos temas y su persistencia, el idioma en ambos sentidos, el estado del mapa, la ayuda y la igualdad del CSV en ambos idiomas.
- Arranque con getter de `localStorage` que lanza `SecurityError`: inglés inicial, cambio a español, navegación y carga de Investigate correctos; sin errores JS en esa comprobación.
- Preferencia guardada no válida: regreso a inglés, sin bloquear el cambio posterior.
- Teclado: Tab desde English y Enter sobre Español cambian el idioma y conservan el foco en el botón activo.
- Recarga de `#investigar`, navegación a Aprender y vuelta mediante Atrás: sección y URL correctas.
- Configuración se verificó a 360×740, 390×844, 768×1024, 1024×768, 1440×900 y 844×390, en español e inglés con los dos temas. Los cuatro controles midieron al menos 44 px de alto y quedaron dentro del ancho disponible.
- Comprobación de sintaxis de los JavaScript modificados y reconstrucción estática correctas.


## Mantener traducciones

`app/locales/es.js` contiene pares de texto inglés/español; el texto inglés funciona como identificador estable. Para contenido nuevo usa `GnomonI18n.t('Message ID')` y agrega su traducción al catálogo. No insertes HTML desde una traducción ni traduzcas archivos fuente de datos o columnas de exportación.

`app/i18n.js` adapta el DOM heredado mediante nodos de texto y una lista limitada de atributos de presentación. Conserva los textos originales en WeakMaps para permitir volver a inglés. Su observador procesa solo nodos añadidos o modificados. Las nuevas pantallas deben preferir claves explícitas y los mensajes compuestos deben tener una plantilla revisada; no se utiliza traducción automática por sustitución arbitraria de palabras.

`GnomonI18n.missing()` permite revisar en memoria mensajes sin entrada; incluye nombres propios y metadatos que no necesariamente deban traducirse. No se envían esos textos fuera del navegador.

Para añadir un idioma se necesita su catálogo, inclusión explícita en los idiomas admitidos, opción accesible, locale y pruebas de ida/vuelta, respaldo y conservación de estado.

## Límites

La cobertura estática del catálogo no garantiza todos los mensajes que un proveedor pueda generar en el futuro. Un mensaje no reconocido usa inglés como respaldo. Los títulos originales de publicaciones, nombres propios, códigos y atribuciones pueden conservarse en su idioma de origen.

La revisión visual y el teclado se probaron en Chromium. No se certifica WCAG AA, Safari/Firefox ni lectores de pantalla reales con estas comprobaciones. La auditoría completa de seguridad sigue pendiente de un entorno compatible con el aislamiento y los validadores de la skill.
