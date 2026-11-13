# Propuestas de cambios fuera de `docs/entrega/`

> **Propósito:** De acuerdo con las instrucciones de entrega, no se ha modificado ningún archivo existente fuera de `docs/entrega/`. Este documento recopila las acciones concretas sugeridas sobre el código, los datos, la documentación previa y la configuración del repositorio para que la persona responsable de cada área decida y aplique los cambios antes del **domingo 15-11-2026 a las 23:59 (hora de Managua)**.

---

## 1. Prioridad crítica (bloqueantes de admisión o puntuación)

### P-01 — Visibilidad pública del repositorio y revisión de secretos
- **Responsable:** Propietario del repositorio (`lizanooctavio-boop/NASA-CHALLENGE`).
- **Problema comprobado (`13-11-2026`):** Tanto la API como la web pública de GitHub (`https://github.com/lizanooctavio-boop/NASA-CHALLENGE`) devuelven **HTTP `404`** (repositorio privado). Además, las guías exigen que todo enlace de código y demo sea público y sin inicio de sesión durante el periodo de evaluación.
- **Cambio propuesto:**
  1. Revisar el historial y archivos temporales para confirmar que no hay credenciales (`.netrc`, tokens Earthdata/NOAA/EODMS, rutas locales sensibles o claves personales).
  2. Cambiar la visibilidad del repositorio a **Public** en GitHub.
  3. Anotar el enlace público definitivo en `docs/entrega/FORMULARIO_PROYECTO_EN.md`, `DEMO_VIDEO_30S_EN.md` y `DEMO_DIAPOSITIVAS_EN.md`.

### P-02 — Crear archivo `LICENSE` en la raíz y delimitar código vs. datos
- **Responsable:** Equipo completo / propietario del repositorio.
- **Problema comprobado:** No existe archivo `LICENSE` en la raíz (`origin/codex/verificacion-entrega` ni `origin/codex/recursos-interfaz`), mientras que existen dependencias y fuentes con condiciones distintas:
  - El tutorial SAR adaptado conserva `scripts/sar/LICENSE-CSA.txt` (**MIT** con cláusula de no respaldo publicitario por la CSA).
  - Los datos de **CRU TS 4.10** usan **ODbL / DbCL** (cláusula *Share-Alike* para bases de datos redistribuidas).
  - La API **RainViewer** (si sigue integrada en capas del visor) restringe su uso gratuito a ámbito **personal y educativo**.
  - **Open-Meteo** en nivel gratuito aplica restricción **no comercial** (aunque ECMWF IFS es `CC BY 4.0`).
- **Cambio propuesto:**
  1. Decidir licencia abierta estándar para el **código fuente del repositorio** (recomendado: **Apache License 2.0**, coherente con la licencia por defecto de los términos de Space Apps, o **MIT** compatible con `scripts/sar/LICENSE-CSA.txt`) y crear `LICENSE` en la raíz.
  2. Separar explícitamente en `README.md` y `LICENSE`: *"El código original está bajo `<Apache-2.0 / MIT>`; los conjuntos científicos de entrada y APIs externas conservan las licencias de sus proveedores (`NASA ESDIS`, `OGL-Canada`, `ODbL CRU`, `CSA`, etc.)"*.
  3. Decidir sobre **RainViewer API** y **Open-Meteo**: o bien desactivar/retirar llamadas de RainViewer si entran en conflicto con la licencia abierta del producto, o documentar expresamente que las capas heredadas de tiempo real consumen servicios externos de uso no comercial sin redistribución de su caché.

### P-03 — Integrar los PRs en paralelo y regenerar `data/recursos_integrados.json`
- **Responsable:** Integración / Agente 4 (`PR #10`) junto con responsables de `PR #7`, `PR #9` y `PR #12`.
- **Problema comprobado (`origin/codex/recursos-interfaz`):** Sin la fusión previa de `PR #7` (Canadá, SWOT, radar), `PR #9` (contrastes CRU/GPCC/NOAA/OBPG) y `PR #12` (GLDAS/AppEEARS), el JSON que alimenta **Investigate** (`data/recursos_integrados.json`) contiene actualmente solo **12 elementos base** y **`contrastes = []`** en lugar de las **20 investigaciones y 12 contrastes** completos descritos en el plan y necesarios para grabar la demo (`Nicaragua vs. Canadian Prairies` + discrepancias cruzadas).
- **Cambio propuesto:**
  1. Revisar y fusionar `PR #7`, `PR #9`, `PR #12` y `PR #10` en la rama candidata de despliegue público.
  2. Ejecutar el comando integrador de backend (`python -m clima_nic recursos` `[CONFIRMAR]` punto de entrada vigente tras fusionar PRs) y verificar que `data/recursos_integrados.json` incluye `nicaragua_vs_praderas`, contrastes `GLDAS` vs `MERRA-2`, `CRU`/`GPCC`/`POWER` y `G-REALM`/`SWOT`.
  3. Ejecutar la suite completa de pruebas (`pytest`) y validar manualmente en navegador la ruta de `DEMO_VIDEO_30S_EN.md` antes de grabar.

---

## 2. Prioridad alta (rigor científico, coherencia documental y accesibilidad)

### P-04 — Corregir cifras desactualizadas en `docs/auditoria.md` y unificar el NDVI de `MOD13Q1`
- **Responsable:** Responsable de documentación técnica / estadísticas.
- **Problema comprobado:**
  1. En `docs/auditoria.md` (línea `47`, rama `origin/codex/verificacion-entrega`) figuran cifras antiguas de `NEX-GDDP-CMIP6` para Nicaragua (`+1,55 / +1,96 °C` y lluvia `+0,9 % / −4,3 %`), mientras que el archivo actual `data/fenomenos_nicaragua.json` arroja medianas de **+1,399 °C (`ssp245`) / +1,980 °C (`ssp585`)** y lluvia **−5,446 % (`ssp245`) / −10,488 % (`ssp585`)**.
  2. La muestra puntual `MOD13Q1` en `Central` figura como `-0.0432` en la salida actual del JSON de interfaz y `-0.0438` en documentos previos de análisis (`tabla_analisis.md`).
- **Cambio propuesto:**
  - Regenerar o actualizar `docs/auditoria.md` línea `47` para reflejar los valores exactos de `data/fenomenos_nicaragua.json` (`+1,399 / +1,980 °C` y `−5,446 % / −10,488 %`).
  - Confirmar cuál es la fuente canónica del cálculo NDVI de muestra (`-0.0432` vs `-0.0438`) y añadir nota explícita hasta que se procesen las tareas regionales completas de `AppEEARS`.

### P-05 — Aplicar mejoras rápidas de accesibilidad antes de grabar el demo (`REVISION_ACCESIBILIDAD.md`)
- **Responsable:** Responsable de interfaz (`PR #10`, `origin/codex/recursos-interfaz`).
- **Archivo(s):** `index.html`, `app/estilos.css`, `app/investigar.js`, `app/shell.js`.
- **Cambio propuesto (priorizando las 4 incidencias **Altas** + adaptación móvil a `390 px`):**
  1. **`A-01` (Contraste en `.vista.ventana`):** Aplicar fondo `rgba(14, 20, 34, .88)` en `.vista.ventana` y elevar `--tenue` al menos a `#b7c5d4` (`app/estilos.css:1,75,303`) para evitar caídas por debajo de `4.5:1` cuando el globo iluminado o nubes pasan detrás del panel.
  2. **`A-03` y `A-04` (Foco y *roving tabindex*):** En `app/investigar.js:35-41` implementar `tabindex` rotativo (`0` en el radio activo, `-1` en los demás) con `Home`/`End` sin destruir el foco; en `pasoDemo()` (`app/investigar.js:154-176`) devolver el foco al encabezado del paso o al botón iniciador al pulsar *Finish*.
  3. **`A-07` (Gráficas `Chart.js`):** Añadir `role="img"`, resumen estadístico completo en `aria-label` (pendiente Theil–Sen, IC 95 %, `p` y veredicto) y tabla desplegable accesible (`<details><table>`) bajo `<canvas id="inv-serie">` (`index.html:71`, `app/investigar.js:111,137`).
  4. **`A-11` (Vista móvil `390 px`):** Permitir `flex-wrap: wrap` o indicador visible en `nav` (`app/estilos.css:156`) para que *Learn* y *Sources* sean visibles sin descubrir un scroll oculto, y asegurar áreas táctiles mínimas de `44×44 px`.
  *(El resto de incidencias `A-02`, `A-05`, `A-06`, `A-08`, `A-09`, `A-10`, `A-12` se detallan con línea exacta en `docs/entrega/REVISION_ACCESIBILIDAD.md`.)*

### P-06 — Actualizar `README.md` de la raíz para jueces internacionales
- **Responsable:** Responsable de documentación / repositorio.
- **Problema comprobado:** El `README.md` actual está centrado en la estructura interna en español y menciona `SICC-952` sin incluir todavía una portada bilingüe/en inglés con: descripción ejecutiva en inglés, guía reproducible rápida (`pytest`, regeneración de datos, servicio estático), tabla resumen de citas/licencias y aviso explícito de uso de **Super Intelligence (SI)** y trabajo previo (`SICC-952`, commits `11–13-11-2026`).
- **Cambio propuesto:** Añadir en la cabecera de `README.md` un bloque completo en inglés (*Project Overview, Quick Start, Methodology Summary, Data Attribution & Licenses, SI Disclosure & Prior Infrastructure Note*) y enlazar a `LICENSE` una vez creado.

---

## 3. Prioridad media (calidad científica post-cola y mantenimiento)

### P-07 — Procesar tareas pendientes (`AppEEARS` y `CSA RCM`) cuando completen los servidores
- **Responsable:** Agente 1 (`PR #12` — Tierra) y Agente 3 (`PR #7` — CSA/SAR).
- **Situación actual:**
  - `160` tareas en AppEEARS (`SPL4SMGP.008`, `MOD11A2.061`, `MOD16A2GF.061`, `MOD13A3.061`, `MCD12Q1.061`) siguen en `0` completadas (`158 Pending`, `2 Processing`).
  - Pedido EODMS `RCM` (`#3787605`, escenas `5616847` y `5600935`) sigue en estado `SUBMITTED`, y la página de términos EODMS devolvió `403`.
- **Cambio propuesto:**
  - Si completan **antes del domingo 15-11 a las 18:00 CST**, descargar resultados, verificar QA (`MODIS`/`SMAP`), leer la EULA exacta del pedido EODMS antes de subir cualquier derivado de `RCM` y re-ejecutar el pipeline integrador.
  - Si **no completan antes del cierre**, mantener explícitamente el estado `pendiente` / `NO_VALIDADA` sin rellenar valores artificiales ni cambiar las etiquetas de honestidad en la interfaz ni en el formulario.

### P-08 — Completar enlaces, comprobaciones manuales `[VERIFICAR]` y decisiones del equipo
- **Responsable:** Todo el equipo en Managua.
- **Lista de decisiones e inspecciones pendientes (no delegables):**
  1. **Sede y cuentas:** Confirmar que todos los miembros están registrados, verificados y dentro del mismo equipo en la **sede de Managua** (y resolver autorizaciones si hubiera menores de `< 18` años).
  2. **Formato del demo y publicación:** Elegir entre vídeo `<= 30 s` (`DEMO_VIDEO_30S_EN.md`) o `<= 7` diapositivas (`DEMO_DIAPOSITIVAS_EN.md`), generar el entregable **sin logotipos de NASA/CSA/NOAA**, aplicar **marca de agua visible + metadatos** si lleva voz/medios SI (p. ej. ElevenLabs) y verificar el `[ENLACE]` público desde una red sin sesión y considerando filtros **FortiGuard** (sin acortadores).
  3. **Inspecciones manuales `[VERIFICAR]`:**
     - Abrir manualmente el recurso #7 en Medium (`403` automático) para confirmar la lista literal de pruebas de su autor y completar `LECTURA_MEDIUM.md`.
     - Consultar el PDF de NASA NTRS `20090042747` para añadir los apellidos de autores omitidos en la API JSON (`authors: []`).
     - Verificar en el portal DWD/NOAA PSL el DOI exacto de `GPCC Full Data Monthly v2025`, la cita oficial de `NOAA GSOM 1.0` / `POWER`, y la atribución conjunta exacta NASA/CNES para `SWOT`.
     - Resolver el conflicto visual de nombre final del proyecto (`Earth Trend Detective` `[CONFIRMAR]`) y completar el envío pulsando **Submit for Judging** antes del **domingo 15-11-2026 a las 23:59 (UTC−6)**.
