# Revisión local de seguridad — parcial e incompleta

## Alcance y estado

Perfil solicitado: `standard`, acotado al frontend, sus datos publicados, empaquetado y servidor local. Revisión de referencia: `0c7184c` de NASA-CHALLENGE/Gnomon. Las modificaciones de UX/idioma posteriores del worktree no se presentan como parte de esa revisión inmutable.

Se realizaron las cuatro tareas de reconocimiento independientes previstas por la skill: producto/stack, principales/controles, entradas/sinks y ejecución/despliegue. Se inspeccionaron fuentes sin red y sin ejecutar código del target para probar explotación. No hay ledger previo compatible disponible.

**El flujo completo no ha terminado.** No se ejecutaron las oleadas de hunters, críticos de cobertura ni verificadores de candidatos. No se valida una cobertura completa ni una ausencia de vulnerabilidades. `findings.json` es una lista vacía y las once unidades del ledger permanecen `deferred`; no se transforman las observaciones de reconocimiento en vulnerabilidades confirmadas.

Dos bloqueos concretos impiden afirmar cumplimiento de la skill:

1. El API de herramientas no acredita el sandbox exigido: red externa deshabilitada con namespace de loopback privado, entorno vacío/allowlist, target y toolchain solo lectura, scratch exclusivo y todos los límites de recursos/tiempo. No se ejecutó target para generar evidencia de seguridad.
2. Los dos validadores oficiales se invocaron sin modificar sus controles y fallaron en Windows con **`OS no-follow and nonblocking input protection is unavailable`**. No se desactivaron sus protecciones. La sintaxis JSON puede inspeccionarse con herramientas de confianza, pero eso no equivale a pasar los validadores oficiales.

El registro local del análisis conserva el estado `incomplete` y su motivo. Este documento es la copia del informe incluida con los cambios del frontend. Los artefactos de trabajo de la auditoría se conservan localmente.

## Resultado y postura observada

No se confirma ninguna vulnerabilidad. La aplicación es un visor de datos públicos y no se encontró una frontera de cuenta/tenant que justifique añadir autenticación a sus funciones públicas. Se observaron rutas cuyo endurecimiento es razonable, pero falta demostrar un actor de menor confianza con control de entrada y un resultado perjudicial sobre otra sesión. No se asigna severidad a esas rutas.

| Observación de fuentes | Ubicación de referencia | Clasificación y recomendación |
|---|---|---|
| Textos de nombres y categorías de ciclones se interpolan en cadenas para Leaflet. | `app/fenomenos.js:96`, `:101`, `:105`, `:109` | Endurecimiento: crear nodos con `textContent` para los popups. El snapshot se obtiene de una ruta estática compilada; no se acreditó control por atacante. |
| URL de aviso de ciclones se asigna desde datos. | `app/fenomenos.js:111` | Endurecimiento: permitir únicamente URL HTTPS válidas antes de crear un enlace; conservar `noopener`/`noreferrer`. No se demostró un URL de atacante publicado. |
| Tooltips de gráficas concatenan nombres/unidades mantenidos sin el escape que ya existe. | `src/graficas.js:153`, `:223`, `:234` | Endurecimiento: aplicar `escapar` a los campos de texto o usar nodos. No hay ruta demostrada desde búsqueda o fragmento de URL hasta esos metadatos. |
| Rótulos de países y nombres de investigaciones se entregan a Leaflet como HTML. | `app/shell.js:199`, `:216` | Endurecimiento: entregar `HTMLElement` con `textContent`, siguiendo el patrón de hidrología. Los datos proceden de assets/versionado. |
| Helper de preferencias resuelve `localStorage` como valor por defecto de parámetro antes del `try`. | `app/shell.js:115` | Bug de resiliencia/UX, no vulnerabilidad: resolver el almacenamiento dentro del `try` para sobrevivir a `SecurityError`. |
| Scripts externos HTTPS con versiones fijas, sin integridad visible. | `index.html:257`, `:258`, `:277`; `app/espacio.js:4` | Dependencia de confianza en CDN. Inventariar/vendorear o añadir integridad compatible puede mejorar defensa; no es una vulnerabilidad por sí sola. |

## Patrones positivos

- Búsqueda y sugerencias usan texto DOM, no interpretan la consulta como HTML (`app/buscador.js:20`, `:112`, `:179`).
- El fragmento de URL solo selecciona modos predefinidos (`app/shell.js:202`, `:206`).
- Coordenadas finitas y límites geográficos en el adaptador, con destino fijo de pronóstico (`src/fuentes-meteo.js:13–26`).
- Recursos meteorológicos locales seleccionados mediante allowlists (`src/fuentes-meteo.js:5–7`, `:78–82`).
- Popups hidrológicos construidos con nodos de texto (`app/hidrologia.js:23`, `:57`, `:80`).
- CSV de hidrología entrecomilla y neutraliza prefijos de fórmula en strings (`src/hidrologia-datos.js:5–8`).
- El build publica archivos de datos específicos; no copia cachés/credenciales de todo el repositorio (`scripts/preparar_render.mjs:9–31`).
- Servidor local enlazado a loopback, GET/HEAD y confinamiento léxico (`scripts/servir-local.mjs:15–27`). Esto no acredita confinamiento frente a symlinks ni controles efectivos de Render.

## Cobertura y siguientes pasos

Ledger: 11 unidades `deferred`, 0 `covered`, 0 `candidate`, 0 hallazgos confirmados. Backend científico completo, identidad del proveedor, infraestructura real y políticas efectivas de Render quedan fuera de la cobertura de reconocimiento. No se ejecutó crítico final de cobertura; no hay declaración de pase limpio.

Para terminar la auditoría: proporcionar el sandbox requerido y APIs de archivos compatibles (por ejemplo en entorno Linux aislado que cumpla todos los controles), validar el ledger, ejecutar las oleadas de búsqueda y críticas, y someter cada candidato a validación y verificación independientes. Usar nombres, URLs y datos ficticios en un origen local; detener cada prueba en el mínimo efecto. No convertir la mera ausencia de CSP/SRI ni la posibilidad de modificar todo el repositorio en un hallazgo.

Las pruebas de experiencia de usuario que el agente principal realice para la vista local se documentan por separado; no sustituyen pruebas de explotación ni el procedimiento completo de esta skill.

## Apéndice: revisión estática de las correcciones locales

Se volvió a leer el diff local de `app/shell.js`, `app/fenomenos.js`, `src/graficas.js`, `index.html` y el nuevo `app/i18n.js`, sin ejecutarlo. Esta lectura posterior no cambia el `source_ref` del reconocimiento ni transforma el run en completo.

- El acceso al getter `window.localStorage` está ahora dentro del `try` del helper de preferencias.
- Nombres de investigaciones, países y ciclones pasan por nodos `span` con `textContent`; Leaflet recibe esos elementos o factories que los crean.
- Avisos de ciclones requieren URL absoluta con protocolo HTTPS y enlaces nuevos usan `noopener noreferrer`.
- Campos de unidades y nombres en los tooltips señalados pasan por `escapar` antes de formar HTML.
- El nuevo módulo de idioma solo modifica texto y atributos de presentación/accesibilidad enumerados (`aria-label`, `title`, `placeholder`, `alt`, `aria-valuetext`). No introduce `innerHTML`, evaluación de código ni escritura de `href`/`src`/`style` desde traducciones. No realiza solicitudes de traducción externas. Acepta únicamente preferencias `en`/`es`, y captura fallos del almacenamiento.

Estas son mejoras de superficie y resiliencia revisadas por fuente. No se han sometido a payloads ni se certifica que eliminen todas las vías de inyección de la aplicación. Ninguna se presenta como reparación de una vulnerabilidad confirmada por este run.

## Configuración de idioma y tema

El tema usa el almacenamiento local con una lista cerrada de dos valores (`light`, `dark`). El único valor aplicado al documento es uno de esos identificadores, que selecciona reglas CSS incluidas en la aplicación. Los mensajes de cambio se escriben como texto. Configuración reutiliza el motor de idioma existente, y el enlace de Ayuda activa la ruta local `#configuracion`.

La rama de integración parte de `20bec48`. Conserva la comprobación de integridad de los recursos CDN que la base añadió después del reconocimiento inicial. El informe original describe el estado de `0c7184c`. [Guía de validación](VALIDACION_UX_LOCAL.md)
