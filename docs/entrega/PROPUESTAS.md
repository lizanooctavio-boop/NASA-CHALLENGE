# Propuestas de cambios fuera de `docs/entrega/`

> **Propósito:** De acuerdo con las reglas de trabajo, no se ha modificado ningún archivo existente del código, datos ni documentación previa fuera de `docs/entrega/`. Este documento recopila las acciones concretas propuestas para que las personas responsables de cada módulo las apliquen antes del cierre oficial (**domingo `15-11-2026` a las `23:59`, hora de Managua `UTC−6`**).

---

## 1. Prioridad crítica (bloqueantes de admisión, elegibilidad o puntuación)

### P-00 — Consulta obligatoria al *Local Lead* de Managua antes de marcar `Confirm All Work is Original`
- **Responsable:** Representante / líder del equipo en la sede **Managua**.
- **Problema comprobado:** El historial Git registra `54` commits previos a la apertura del evento (`f5fad37` el `2026-11-11 22:34:36 -0600`; `15` el `11-11`, `15` el `12-11` y `24` el `13-11`, más el visor previo `SICC-952`), mientras las *Participant FAQs* indican *"Teams are not allowed to begin working on the challenges prior to the hackathon"* y el envío exige marcar **`Confirm All Work is Original`**.
- **Acción propuesta:**
  1. Enviar hoy mismo al *Local Lead* de Managua la consulta transparente preparada en `docs/entrega/REQUISITOS_ENTREGA_2026.md` §4 (sin minimizar ni ocultar fechas ni editar el historial Git).
  2. Documentar su respuesta por escrito y seleccionar en consecuencia la **Opción A** o la **Opción B** de `docs/entrega/FORMULARIO_PROYECTO_EN.md` §8 (y actualizar `README.md` antes del envío).

### P-01 — Visibilidad pública del repositorio y auditoría de secretos
- **Responsable:** Propietario del repositorio (`lizanooctavio-boop/NASA-CHALLENGE`).
- **Problema comprobado (`13-11-2026`):** `https://github.com/lizanooctavio-boop/NASA-CHALLENGE` y su endpoint en la API de GitHub devuelven **HTTP `404`** sin autenticación (repositorio **privado**). Si permanece privado tras el `15-11` a las `23:59`, el proyecto no podrá evaluarse.
- **Cambio propuesto:**
  1. Revisar historial, archivos ignorados y ramas activas para confirmar ausencia de credenciales (`.netrc`, tokens Earthdata/NOAA/EODMS, rutas locales sensibles o PII).
  2. Cambiar el repositorio a **Public** en GitHub y confirmar acceso HTTPS limpio (regla FortiGuard).
  3. Rellenar los enlaces públicos definitivos en el formulario de entrega y en el guion o diapositivas finales.

### P-02 — Crear `LICENSE` OSI en la raíz y separar licencias de datos/servicios externos
- **Responsable:** Equipo completo / propietario del repositorio.
- **Problema comprobado:** No existe archivo `LICENSE` en la raíz de `origin/codex/verificacion-entrega` ni de `origin/codex/recursos-interfaz`, y coexisten recursos con condiciones distintas:
  - El módulo SAR adaptado conserva `scripts/sar/LICENSE-CSA.txt` (**MIT** con cláusula de no respaldo publicitario por la CSA).
  - **CRU TS 4.10** se distribuye bajo **ODbL / DbCL** (*Share-Alike* para derivados redistribuidos).
  - **RainViewer API** restringe el nivel gratuito a **uso personal y educativo** con enlace obligatorio.
  - **Open-Meteo** limita el nivel gratuito a **uso no comercial** (aunque ECMWF IFS subyacente sea `CC BY 4.0`).
  - **CSA RCM (`Order #3787605`)** sigue pendiente de lectura íntegra de EULA (EODMS devolvió `403`).
- **Cambio propuesto:**
  1. Añadir `LICENSE` OSI en la raíz (recomendado **Apache License 2.0**, alineado con el estándar por defecto de los *Terms* de Space Apps, o **MIT** compatible con `LICENSE-CSA.txt`).
  2. Declarar expresamente en `README.md` y en el formulario que la licencia OSI cubre el código propio, mientras los datos de entrada y APIs externas conservan las licencias de sus proveedores.
  3. Evaluar si se deshabilita por defecto o se aísla **RainViewer** (y la nota no comercial de **Open-Meteo**) para evitar fricciones con requisitos OSI sin restricciones.

### P-03 — Integrar los PRs abiertos y regenerar `data/recursos_integrados.json`
- **Responsable:** Integración de interfaz (`PR #10`, `origin/codex/recursos-interfaz`) junto con responsables de `PR #7`, `PR #9` y `PR #12`.
- **Problema comprobado (`13-11-2026`):** En GitHub constan `11` PRs abiertos (`#1`, `#2`, `#3`, `#4`, `#5`, `#7`, `#8` [borrador], `#9`, `#10`, `#12` [borrador], `#13` [borrador]). En `origin/codex/recursos-interfaz` (`91ede22`), `data/recursos_integrados.json` contiene actualmente **solo las `12` investigaciones base de Nicaragua y `contrastes = []`** porque aún no se han fusionado `PR #7` (Canadá/SWOT/OPERA/RCM), `PR #9` (contrastes y nuevas series `AIRS3STM`, `OMNO2d`, `IMERG OPeNDAP`, `OBPG`, `CRU/GPCC/NOAA`) ni `PR #12` (GLDAS/AppEEARS).
- **Cambio propuesto:**
  1. Revisar y fusionar `PR #7`, `PR #9`, `PR #12` y `PR #10` (más los PRs complementarios aprobados) en una rama unificada de publicación.
  2. Verificar en `backend/clima_nic/recursos.py` el mapeo completo de las series incorporadas en `5d64ab9` (`clorofila_pacifico_fonseca`, `airs_tas_nic`, `omi_no2_managua`, `omi_no2_rural`, `giovanni_imerg_*`) y de los nuevos contrastes antes de regenerar.
  3. Ejecutar desde `backend/` el comando CLI real verificado en `backend/clima_nic/__main__.py`:
     - `python -m clima_nic recursos`
  4. Ejecutar `pytest` completo tras fusionar y validar en navegador que `Tropics vs. prairies` (`nicaragua_vs_praderas`) y **Cross-checks** (`GLDAS` vs `MERRA-2`, `GISTEMP` vs `POWER/AIRS`, `SWOT` vs `G-REALM`, `MODIS CHL` Fonseca vs Pacífico abierto) se muestran en vivo antes de grabar el demo o capturar pantallas.

---

## 2. Prioridad alta (coherencia científica y accesibilidad)

### P-04 — Corregir cifras antiguas de CMIP6 en `docs/auditoria.md` y documentar la diferencia de NDVI (`-0.0432` vs. `-0.0438`)
- **Responsable:** Responsable de análisis estadístico / documentación técnica.
- **Problema comprobado:**
  1. En `origin/codex/verificacion-entrega:docs/auditoria.md` **línea `47`** figuran valores antiguos de `NEX-GDDP-CMIP6` para Nicaragua (**`+1,55 / +1,96 °C`** y lluvia **`+0,9 % / −4,3 %`**), mientras el archivo vigente `data/fenomenos_nicaragua.json` arroja medianas de **`+1,399 °C` (`ssp245`) / `+1,980 °C` (`ssp585`)** y precipitación **`−5,446 %` (`ssp245`) / `−10,488 %` (`ssp585`)**.
  2. La muestra puntual `MOD13Q1` (`2000–2024`) en sitio `Central` figura como **`-0.0432` NDVI/década** en `origin/codex/recursos-interfaz:data/recursos_integrados.json`, frente a **`-0.0438`** en `origin/codex/recursos-tierra-v2:data/recursos/tierra/tabla_analisis.md:20` y `docs/reto/recursos/tierra.md:179`.
- **Cambio propuesto:**
  - Actualizar `docs/auditoria.md` línea `47` con los valores exactos vigentes de `data/fenomenos_nicaragua.json` (`+1,399 / +1,980 °C` y `−5,446 % / −10,488 %`) para evitar contradicciones si los jueces revisan el informe de auditoría.
  - Unificar o explicar en nota metodológica la pequeña diferencia (`-0.0432` vs. `-0.0438`) según el recálculo exacto en `recursos.py` (`tendencia_robusta`), manteniendo explícita la salvedad de muestra puntual sin máscara regional.

### P-05 — Aplicar mejoras rápidas de accesibilidad antes de grabar el demo (`REVISION_ACCESIBILIDAD.md`)
- **Responsable:** Responsable de interfaz (`PR #10`, `origin/codex/recursos-interfaz`).
- **Archivos implicados:** `index.html`, `app/estilos.css`, `app/investigar.js`, `app/shell.js`.
- **Cambio propuesto (priorizando las 4 incidencias Altas + vista móvil a `390 px`):**
  1. **`A-01` (Contraste en `.vista.ventana`):** Aplicar `background: rgba(14, 20, 34, .88);` en `.vista.ventana` y elevar `--tenue` al menos a `#b7c5d4` (`app/estilos.css:1,75,303`).
  2. **`A-03` y `A-04` (Foco y *roving tabindex*):** En `app/investigar.js:35-41`, aplicar `tabindex` rotativo (`0` activo, `-1` resto) más `Home`/`End` sin destruir nodos si el grupo no cambia; en `pasoDemo()` (`app/investigar.js:154-176`), restaurar foco al titular del paso o al botón iniciador al pulsar *Finish*.
  3. **`A-07` (Gráficas `Chart.js`):** Añadir `role="img"`, resumen estadístico completo en `aria-label` (pendiente, IC 95 %, `p` y veredicto) y `<details><table>` accesible bajo `<canvas id="inv-serie">` (`index.html:71`, `app/investigar.js:111,137`).
  4. **`A-11` (Móvil `390 px`):** Habilitar `flex-wrap: wrap` o indicador visible en `nav` (`app/estilos.css:156`) para que *Learn* y *Sources* no queden ocultos y asegurar objetivos táctiles de `44×44 px`.
  *(Detalle completo de `A-01` a `A-12` con líneas exactas en `docs/entrega/REVISION_ACCESIBILIDAD.md`.)*

### P-06 — Actualizar `README.md` raíz para jueces internacionales
- **Responsable:** Responsable de repositorio / documentación.
- **Problema comprobado:** El `README.md` actual (`origin/main` solo contiene `README.md`; `origin/codex/verificacion-entrega` está en español) necesita portada en inglés orientada a jueces internacionales, enlace a `LICENSE` y nota explícita del trabajo previo (`SICC-952` y commits `11–13-11-2026`) y uso de SI.
- **Cambio propuesto:** Incorporar al inicio de `README.md` un resumen ejecutivo en inglés (*Project Overview, Quick Start, Statistical Methodology, Sources & Licenses, SI Disclosure & Pre-Event Infrastructure Notice*), enlazar `LICENSE` y mantener los textos de entrega coherentes con la decisión acordada en `P-00`.

---

## 3. Prioridad media (colas en curso y verificaciones manuales del equipo)

### P-07 — Procesar tareas pendientes (`AppEEARS` y `CSA RCM`) solo si completan antes del cierre
- **Responsable:** Responsables de `PR #12` (Tierra / AppEEARS) y `PR #7` (CSA / SAR).
- **Situación actual (`13-11-2026`):**
  - `160` tareas en AppEEARS (`SPL4SMGP.008`, `MOD11A2.061`, `MOD16A2GF.061`, `MOD13A3.061`, `MCD12Q1.061`) siguen en `0` completadas (`158 Pending`, `2 Processing`).
  - Pedido EODMS `RCM` (`#3787605`, escenas `5616847` y `5600935`) sigue en `SUBMITTED`, con acceso de documentación/EULA bloqueado (`403/404`).
- **Cambio propuesto:**
  - Si completan antes de la tarde del `15-11`, validar QA, revisar la EULA exacta de EODMS antes de redistribuir cualquier derivado `RCM` y regenerar con `python -m clima_nic recursos`.
  - Si no completan a tiempo, mantener intactas las etiquetas `pendiente` y `NO_VALIDADA` sin rellenar valores estimados ni ocultar colas.

### P-08 — Completar inspecciones humanas pendientes y decisiones finales del equipo
- **Responsable:** Todo el equipo en Managua.
- **Pendientes no automatizables:**
  1. **Elegibilidad y sede:** Confirmar edades de todos los participantes (reglas `< 18` años en sede y exclusión absoluta de nombres reconocibles, voces e imagen de menores en la entrega), cuenta y registro unificado en la sede **Managua**.
  2. **Demo único y publicación:** Elegir vídeo `<= 30 s` O presentación `<= 7` diapositivas, confirmar si hay voz/visuales SI (aplicar **marca de agua visible** y metadatos), prohibir logotipos NASA/CSA/NOAA, comprobar URLs públicas aptas para **FortiGuard** y pulsar **Submit for Judging** antes del **domingo `15-11-2026` a las `23:59` (`UTC−6`)**.
  3. **Verificaciones manuales restantes `[VERIFICAR]`:**
     - Abrir manualmente el artículo #7 en Medium (`HTTP 403` Cloudflare en descarga automática) para completar `LECTURA_MEDIUM.md`.
     - Comprobar en las páginas oficiales de los proveedores los datos marcados `[VERIFICAR]` en `FUENTES_Y_LICENCIAS.md` (cita completa Hansen et al. 2010 en GISTEMP, DOI de `GPCC v2025`, URL/DOI canónico de `NOAA GSOM 1.0`, DOI actual de `NASA POWER`, texto literal de atribución conjunta CNES en `SWOT`).
     - Decidir título único definitivo (`Earth Trend Detective` vs. `Earth System Trend Detective`).
