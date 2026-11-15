# Mejorar la experiencia de usuario y la seguridad de NASA-CHALLENGE

Actúa como desarrollador senior especializado en frontend, experiencia de usuario, accesibilidad y seguridad de aplicaciones web.

Audita el proyecto, identifica problemas verificables e implementa correcciones. Utiliza obligatoriamente estas dos skills:

- `security-audit`: https://github.com/cloudflare/security-audit-skill
- `ui-ux-pro-max`: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill

Este encargo autoriza una auditoría de seguridad del alcance indicado, con informes, validación independiente mediante subagentes y correcciones verificadas.

## Contexto del proyecto

- Repositorio: https://github.com/lizanooctavio-boop/NASA-CHALLENGE
- Demo de referencia: https://nasa-challenge-q6cx.onrender.com/
- Rama base: `origin/codex/demo-render`.
- Rama de trabajo: `codex/frontend-ux-seguridad`.
- La aplicación permite explorar información meteorológica y tendencias climáticas mediante mapas, globo 3D, gráficas y descargas.

Lee README, `AGENTS.md` si existe y las instrucciones completas de ambas skills. Comprueba su disponibilidad antes de comenzar; no afirmes haberlas utilizado si no pudiste cargarlas.

Consulta los PR abiertos y los cambios recientes para evitar duplicar trabajo. Conserva los cambios locales existentes.

## Objetivo

Conseguir que una persona sin conocimientos técnicos pueda:

1. Entender para qué sirve la aplicación.
2. Encontrar una ubicación y una investigación.
3. Interpretar resultados, incertidumbre y fuentes.
4. Utilizar las funciones principales desde móvil o teclado.
5. Recuperarse de errores sin perder contexto.

Al mismo tiempo, identifica y corrige riesgos de seguridad demostrables en las superficies utilizadas por el frontend.

## Uso de las skills

### UI UX Pro Max

Usa obligatoriamente `ui-ux-pro-max` tanto para revisar como para diseñar e implementar los cambios de interfaz de usuario: navegación, componentes, accesibilidad, formularios, estados y visualización de datos. Incluye el selector de idioma y los ajustes de distribución necesarios para textos traducidos. No limites su uso a generar recomendaciones: aplica las guías pertinentes en el código y verifica el resultado en navegador.

- Detecta el stack real antes de elegir recomendaciones.
- Consulta las guías específicas para cada problema.
- Conserva las decisiones de diseño existentes que funcionen.
- Propón un sistema visual coherente cuando los problemas afecten a toda la aplicación.
- Comprueba que cada recomendación encaje con una herramienta científica y cartográfica.
- No conviertas la aplicación en una landing comercial ni añadas decoración que dificulte leer los datos.
- En el PR, explica qué guías de la skill aplicaste a cada cambio de interfaz relevante y aporta evidencia de su validación.

### Security Audit

Realiza la auditoría con perfil `standard`, limitada al frontend y sus fronteras de confianza.

Sigue su metodología, requisitos de aislamiento, validación independiente y formato de informes. Conserva los artefactos de auditoría fuera del repositorio.

Si el entorno no cumple los controles exigidos por la skill, continúa con la inspección de código permitida y documenta exactamente qué validaciones quedan bloqueadas. No sustituyas el aislamiento requerido por ejecución sin restricciones.

Separa la auditoría de la implementación: registra la revisión auditada antes de cambiar el código y vuelve a validar los hallazgos afectados después de corregirlos.

## Alcance de experiencia de usuario

### Navegación y orientación

Comprueba:

- Que la pantalla inicial explique la diferencia entre tiempo meteorológico y cambio climático.
- Que las secciones tengan nombres y estados activos comprensibles.
- Que los enlaces directos, la recarga y los botones atrás/adelante funcionen.
- Que el buscador permita seleccionar lugares sin ambigüedades.
- Que el recorrido de Terra pueda iniciarse, cerrarse y repetirse.
- Que cambiar de sección conserve el contexto cuando resulte útil.

### Paneles, mapas y controles

Revisa:

- Superposición entre menú, buscador, leyendas y paneles.
- Funcionamiento de cerrar, minimizar y ampliar.
- Cambio entre globo y mapa.
- Selección de capas, opacidad y reproducción temporal.
- Interacción táctil y alternativas al arrastre.
- Legibilidad sobre fondos cartográficos variables.
- Estado visible de los controles y respuesta a cada acción.

### Selector de idioma: español e inglés

Implementa un botón o selector visible y accesible que permita cambiar toda la interfaz entre **Español** y **English**, tanto en escritorio como en móvil. Este requisito es una funcionalidad nueva autorizada; no depende de encontrar un bug previo.

- Usa `ui-ux-pro-max` para definir su ubicación, presentación, estados e interacción, respetando los componentes y el estilo existentes.
- Identifica las opciones por su nombre de idioma; no dependas únicamente de banderas o iconos. Haz evidente la opción activa.
- Conserva inglés como idioma inicial cuando no haya una preferencia guardada. Recuerda la elección localmente y permite cambiarla en cualquier momento, sin iniciar sesión.
- El cambio debe ser inmediato y mantener la sección, ubicación, capas, variables y selección temporal actuales, sin reiniciar el mapa ni el globo.
- Traduce menús, botones, formularios, mensajes de carga/error/ausencia de datos, diálogos, ayudas, recorrido de Terra, leyendas, tooltips, etiquetas de gráficas, veredictos y nombres accesibles. Incluye contenido que se genere después del cambio.
- Centraliza las traducciones en diccionarios con claves estables. Reutiliza la infraestructura de internacionalización existente si la hay y evita condicionales de idioma dispersos.
- Actualiza el atributo `lang` del documento y utiliza el idioma elegido para formatos de fecha y número. Conserva valores científicos, unidades, identificadores y estructura de los archivos de datos; el formato de exportación debe seguir siendo compatible.
- Mantén nombres propios, referencias y títulos originales de fuentes cuando traducirlos pueda alterar su identificación. Conserva atribuciones y advertencias científicas en ambos idiomas.
- Si falta una traducción, usa inglés como respaldo y registra la clave durante la verificación; no muestres claves internas ni textos vacíos al usuario.
- Renderiza traducciones como texto mediante APIs seguras. No uses HTML sin sanear ni envíes contenido del usuario o datos privados a servicios externos de traducción.
- Maneja almacenamiento local bloqueado o no disponible sin impedir el cambio durante la sesión. Valida la preferencia guardada contra los idiomas admitidos.
- Comprueba teclado, foco, lector de pantalla y nombres accesibles en ambos idiomas. Evita que los textos más largos en español recorten controles o provoquen superposiciones.

Verifica al menos: primera visita, cambio EN → ES y ES → EN, persistencia tras recargar, actualización de contenido dinámico, almacenamiento no disponible y conservación del estado. Recorre las secciones principales en ambos idiomas y añade pruebas de las claves de traducción y de los flujos afectados. No presentes la traducción como completa si quedan textos visibles sin cubrir.

### Formularios y recuperación

- Valida coordenadas y otros campos con mensajes próximos al error.
- Distingue carga, ausencia de datos, fallo y éxito.
- Evita indicadores de carga indefinidos.
- Ofrece reintento sin borrar innecesariamente la selección.
- Evita que una respuesta antigua sobrescriba una consulta más reciente.
- Identifica datos caducados mediante fechas y mensajes claros.
- Evita errores silenciosos o detalles técnicos innecesarios en pantalla.

### Accesibilidad

Utiliza WCAG 2.2 AA como referencia y verifica manualmente los flujos principales:

- Uso por teclado y foco visible.
- Orden de navegación y foco al abrir o cerrar diálogos.
- Etiquetas accesibles y semántica de los controles.
- Contraste y ampliación del texto.
- Mensajes de estado accesibles.
- Alternativas a información transmitida solo mediante color.
- Respeto por las preferencias de movimiento reducido.

Las herramientas automáticas complementan la revisión manual; no certifican por sí solas la accesibilidad.

### Datos y confianza científica

Comprueba que cada gráfica o resultado permita reconocer:

- Variable y unidad.
- Ubicación y periodo.
- Fuente y fecha de actualización.
- Incertidumbre y datos faltantes.
- Diferencia entre observación, modelo, pronóstico y escenario.

Conserva los veredictos científicos existentes. “Evidencia insuficiente” no debe presentarse como “ausencia de cambio”.

### Diseño adaptable y rendimiento

Revisa móvil, tableta y escritorio, incluyendo anchuras de 360, 390, 768, 1366 y 1920 píxeles.

Busca desbordamientos, contenido recortado, controles inaccesibles y gráficas ilegibles. Comprueba también red lenta, redimensionado y cambios repetidos de sección.

Investiga consumo innecesario de recursos, listeners duplicados, animaciones activas fuera de pantalla y recreación de mapas o gráficas. Justifica las optimizaciones con mediciones.

## Alcance de seguridad

Traza la entrada de datos hasta su uso en el navegador. Examina especialmente:

### Contenido y entradas no confiables

- Parámetros de URL y fragmentos.
- Consultas del buscador y coordenadas.
- Respuestas de APIs y archivos de datos.
- Etiquetas, tooltips, leyendas, ventanas del mapa y mensajes.
- Construcción de HTML, enlaces y nombres de descarga.

Comprueba posibles inyecciones DOM, XSS y URLs peligrosas. Identifica el origen, las transformaciones y el punto de uso antes de confirmar un problema.

### Credenciales y privacidad

- Comprueba si el bundle, los archivos publicados o los logs exponen secretos.
- Revisa el uso de almacenamiento del navegador.
- Verifica si ubicaciones o datos del usuario se transmiten innecesariamente.
- Distingue identificadores públicos de credenciales privadas.
- No copies secretos reales a informes, capturas, pruebas o commits.

### Dependencias y recursos externos

- Revisa dependencias directas, CDN, scripts y recursos de terceros.
- Comprueba versiones, procedencia y avisos aplicables.
- Evalúa si una vulnerabilidad de dependencia alcanza una ruta utilizada.
- Evita presentar una alerta automática como explotación confirmada.

### Fronteras con el backend y el despliegue

Inspecciona únicamente lo necesario para entender:

- Acceso a endpoints utilizados por la interfaz.
- Validación del servidor frente a validación del cliente.
- Restricciones de origen y permisos, cuando correspondan.
- Tratamiento de errores y exposición de información.
- Políticas del navegador y compatibilidad con mapas, WebGL y recursos externos.

Si una corrección exige modificar backend o configuración de despliegue, documenta la dependencia y limita el cambio a lo necesario.

La ausencia de una cabecera o protección adicional no constituye por sí sola una vulnerabilidad: explica el impacto real o clasifícala como endurecimiento.

## Límites de las pruebas

- Usa la demo como referencia funcional.
- No ejecutes pruebas de explotación contra Render, NASA ni servicios de terceros.
- Reproduce los casos de seguridad con datos ficticios y en el entorno aislado exigido por la skill.
- No realices pruebas destructivas, de disponibilidad o de carga sobre infraestructura compartida.
- No añadas autenticación o restricciones que impidan el acceso legítimo a datos públicos sin una necesidad demostrada.
- No cambies datos, cálculos, unidades o resultados científicos para resolver problemas de interfaz.

## Priorización e implementación

Para cada problema registra:

- Identificador y categoría: UX, accesibilidad, bug o seguridad.
- Pantalla o archivo afectado.
- Pasos de reproducción.
- Resultado esperado y observado.
- Impacto y evidencia.
- Corrección propuesta y comprobación posterior.

Prioriza riesgos de seguridad confirmados y bloqueos de uso. Después aborda accesibilidad, errores frecuentes y mejoras visuales.

Implementa cambios pequeños y revisables. Reutiliza el código existente y evita dependencias nuevas sin justificación. No retrases correcciones importantes por ajustes cosméticos.

No etiquetes una sospecha como vulnerabilidad confirmada. Mantén separados los hallazgos demostrados, los pendientes de validación y las recomendaciones de endurecimiento.

## Validación y entrega

Entrega:

1. Resumen de los problemas corregidos y su impacto.
2. Evidencia visual del antes y después para cambios de interfaz.
3. Informe de seguridad y cobertura conforme a la skill.
4. Pruebas ejecutadas, resultados y entorno utilizado.
5. Limitaciones, riesgos residuales y validaciones pendientes.
6. Enlace al PR en borrador con los cambios verificados.

Incluye pruebas de regresión para bugs relevantes y correcciones de seguridad. Comprueba que las defensas añadidas no rompan la navegación, los mapas, las gráficas ni las descargas.

Incluye capturas comparables de escritorio y móvil en español e inglés, los resultados de las pruebas del selector y cualquier traducción pendiente. Documenta cómo añadir nuevas claves e idiomas al sistema de traducción.

No afirmes que la aplicación es completamente segura o accesible por haber superado una sola revisión.

Sube la rama y abre o actualiza un PR en borrador hacia `codex/demo-render`. No fusiones ni despliegues: esas acciones corresponden al responsable del repositorio.
