# Agente 19: Integracion Cross-Module, A11y y Responsive

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

# Frontend Integration, Accessibility, Responsive Layout & i18n Audit (`wt_audit20` @ `20bec48`)

Read-only audit completed. No files were created, modified, or committed.

---

## Confirmed Findings

### 1. [High] Un-guarded Leaflet (`L` / `mapa`) crashes when Leaflet CDN fails to load
- **Files**: `app/hidrologia.js:22` (`etiquetas = L.layerGroup()`), `app/hidrologia.js:150` (`mapa.on('moveend',rotular)`), `app/shell.js:155,197-202` (`cambiarVista`, `marcar`, `window.SICC_vista.irA`).
- **What happens & why it is a bug**: `index.html:11` and Leaflet script load from `unpkg.com`. `app/shell.js:45` (`iniciarMapa`) guards `if(mapa||!window.L)return;`, leaving global `mapa` `undefined` when Leaflet fails to load (offline, blocked CDN, SRI failure). However:
  - `app/hidrologia.js:22` unconditionally executes `L.layerGroup()` at IIFE initialization, throwing `ReferenceError: L is not defined` before `mapa.on(...)` or `window.SICC_hidrologia` is registered.
  - `window.SICC_vista.marcar` (`app/shell.js:197-200`) calls `L.circleMarker(...).addTo(mapa)` unconditionally.
  - `window.SICC_vista.irA` (`app/shell.js:202`) calls `await cambiarVista('mapa'); mapa.setView([lat,lon],z)` even though `cambiarVista` (`app/shell.js:155`) returns early when `!mapa`.
- **Verification**: Playwright probe fulfilling `**unpkg.com/**` with HTTP 404 observed `pageerror`: `'L is not defined'`, `window.SICC_vista.irA(0, 0, 4)` -> `TypeError: Cannot read properties of undefined (reading 'setView')`, `window.SICC_vista.marcar(0, 0, 'Test')` -> `ReferenceError: L is not defined`.

### 2. [High] Mobile landscape header overflow pushes all primary action controls off-screen (`negative X`)
- **Files**: `app/estilos.css:196,199` (`@media(max-height:500px) and (max-width:1000px)` -> `header`, `.acciones`), `app/buscador.css:44-45` (`@media(max-width:700px),(max-height:500px) and (max-width:1000px)` -> `.buscador-envoltura`).
- **What happens & why it is a bug**: In mobile landscape (`max-height:500px` and `max-width:1000px`), `app/estilos.css:196,199` sets `header { flex-wrap: nowrap }` and `.acciones { flex: 1; min-width: 0; justify-content: flex-end; flex-wrap: nowrap }`, while `app/buscador.css:45` sets `.buscador-envoltura { flex: 1 1 100%; order: 3 }`. Because `header` cannot wrap, the 100%-basis search wrapper crushes `.acciones` to `width: 0`, pushing `#vista-globo`, `#vista-mapa`, `#indicador-datos`, `#solomapa`, and `#menu-tour` to negative X coordinates outside the viewport.
- **Verification**: Playwright viewport check at `740x360` observed `.buscador-envoltura` (`l: 92, r: 719, w: 627`), `.acciones` (`l: 82, r: 82, w: 0`), `#vista-globo` (`l: -408, r: -329`), `#vista-mapa` (`l: -329, r: -258`), `#indicador-datos` (`l: -248, r: -122`), `#solomapa` (`l: -116, r: -37`), `#menu-tour` (`l: -31, r: 82`).

### 3. [High] Help `"Show me"` leaves layer controls hidden (`display: none`) on mobile viewports
- **Files**: `app/ayuda.js:116` (`mostrar(enlace)`), `app/estilos.css:248` (`@media(max-width:700px),(max-height:500px) and (max-width:1000px)` -> `body:not(.solo-mapa) #controles-mapa>:not(#estado-meteo-mapa){display:none}`).
- **What happens & why it is a bug**: On mobile viewports (`<= 700px` wide or landscape `<= 500px` high), `#barra-capas` and all `.solo-mapa-capas` controls (`#chk-sat`, `#chk-imerg`, `#chk-sst`, `#chk-aod`, `#chk-tormentas`, etc.) are hidden with `display: none` unless `body.solo-mapa` is active. `mostrar()` in `app/ayuda.js:116` switches to 2D map (`window.SICC_vista?.cambiar('mapa')`) when `el.closest('.solo-mapa-capas')` matches, but never enables `soloMapa(true)` (or exposes `#barra-capas`). Consequently `scrollIntoView()` and `.focus()` silently no-op on a `display: none` control, leaving focus inside `#ayuda` and nothing highlighted.
- **Verification**: Playwright check at `390x844` triggering Help `"Show me"` on `chk-sat` observed `{'modo': 'mapa', 'soloMapa': False, 'ayudaHidden': False, 'barraCapasDisplay': 'none', 'satRect': {'w': 0, 'h': 0}, 'activeId': 'ayuda-buscar'}`.

### 4. [Medium] `hashchange` listener forces 2D Map view back to 3D Globe on skip-link / fragment navigation
- **Files**: `app/shell.js:213` (`addEventListener('hashchange',...)`), `index.html:19,46` (`a.saltar-contenido` -> `#contenido-principal`).
- **What happens & why it is a bug**: `app/shell.js:213` runs `cambiarVista(location.hash==='#map'?'mapa':'globo')` on every `hashchange`. Activating the keyboard skip link `"Skip to main content"` (`#contenido-principal`)—or any fragment link other than `#map`—while in 2D Map mode changes `location.hash` to `#contenido-principal` and immediately switches the application back to 3D Globe mode.
- **Verification**: Playwright check (`1366x768`) entered Map mode (`modo: 'mapa'`, `hash: ''`), waited for transition end, pressed `Enter` on `a.saltar-contenido`, and observed `after`: `{'modo': 'globo', 'hash': '#contenido-principal', 'active': 'contenido-principal'}`.

### 5. [Medium] Investigate `"What does this mean?"` / `"Open the explanation"` drops keyboard focus to `BODY`
- **Files**: `app/investigar.js:146` (`'What does this mean?'` link), `app/investigar.js:249` (`'Open the explanation'` button), `app/investigar.js:259` (`aprender(ancla)`).
- **What happens & why it is a bug**: Both controls call `aprender(ancla)` (`app/investigar.js:259`), which hides `#investigar` via `tab('aprender')` and scrolls/highlights `<article id="aprender-...">`. Because `aprender()` neither adds `tabindex="-1"` nor moves focus into the target `<article>` or `#aprender` heading, hiding `#investigar` causes `document.activeElement` to fall back to `document.body` (WCAG 2.4.3 Focus Order).
- **Verification**: Playwright check clicking `"What does this mean?"` observed `document.activeElement`: `BODY#`.

### 6. [Medium] Grid Guide dialog `#reticula-guia` lets `Tab` escape to `BODY` while open
- **Files**: `app/reticula.js:30-31,45,47,54-56` (`guia`, `pintarGuia`, `cerrarGuia`, `ayuda.onclick`).
- **What happens & why it is a bug**: `#reticula-guia` (`role="dialog"`, `tabIndex=-1`) is appended to `document.body` and focused on open, but only handles `Escape` and outside `pointerdown`. Because its sole focusable child is the `Close` button and there is no `Tab`/`Shift+Tab` wrapping or focus-out close handler, pressing `Tab` from `Close` moves focus to `BODY`/background page while the dialog remains visible (`hidden === false`).
- **Verification**: Playwright check (`open=reticula-guia`) observed `tab1=BUTTON:Close`, `tab2=BODY#`, `hidden=false`.

### 7. [Medium] Tablet touch targets `< 44px` on geographic grid controls (`36px`)
- **Files**: `app/reticula.css:4,8` (`.reticula-controles button,.reticula-controles select{min-height:36px}`, `.reticula-controles .reticula-ayuda{width:36px}`) vs `app/estilos.css:309` (`@media(pointer:coarse){ button:not(.punto),a.boton,select,...{min-height:44px} }`).
- **What happens & why it is a bug**: `app/reticula.css` is linked after `app/estilos.css` (`index.html:12-13`), so `.reticula-controles button,.reticula-controles select` overrides the `44px` coarse-pointer rule on tablet viewports wider than `700px` (above `reticula.css:17`), rendering `#reticula-toggle`, `#reticula-unidades`, and `#reticula-ayuda` at `36px` height (and `36x36` for `#reticula-ayuda`).
- **Verification**: Playwright check at `768x1024` (`has_touch=True`) measured `#reticula-toggle` (`144x36`), `#reticula-unidades` (`104x36`), `#reticula-ayuda` (`36x36`).

### 8. [Medium] Bilingual & WCAG 3.1.2 (`lang`) mismatches in Help Spanish mode & English fallback strings
- **Files**:
  - `app/ayuda.js:31-35,198-202,215` (`TXT.es`, `textos`, `itemPregunta`): In Spanish mode (`idioma === 'es'`), `TXT.es.tour` (`'Start the tour'`), `TXT.es.mostrar` (`'Show me'`), and `TXT.es.reintentar` (`'Retry'`) remain untranslated in English. Furthermore, `textos()` sets `lang="es"` only on `titulo`, `intro`, and `lista` (`app/ayuda.js:202`), leaving Spanish UI text in `etiquetaBuscar` (`'Buscar en la ayuda'`), `entrada.placeholder`, and `linea` (`#ayuda-estado`) inheriting `lang="en"` from `<html lang="en">`.
  - `app/config.js:6` (`base_atribucion: 'Mapa base: Natural Earth (dominio público)'`) and `src/contrato.js:137` (`unidades: meta.unidades || 'mm/año'`): Spanish fallback strings in an English (`<html lang="en">`) UI.
- **Verification**: Playwright check in Help Spanish mode observed `{'tourText': 'Start the tour', 'tourLang': None, 'idiomaAria': 'Show questions in English', 'idiomaLang': 'en', 'mostrarTexts': [{'t': 'Show me', 'lang': 'en'}, {'t': 'Show me', 'lang': 'en'}]}`.

### 9. [Medium] Invalid ARIA `role="listbox"` child button & missing `role="presentation"` on error item in Buscador
- **Files**: `app/buscador.js:49-51,155-169,256` (`#buscador-lista`, `renderizarOpciones`, `actualizarSugerencias`).
- **What happens & why it is a bug**: `#buscador-lista` has `role="listbox"`. When a country is expanded, `renderizarOpciones` inserts `<li role="presentation">` containing `<button class="buscador-volver">Back</button>` inside the `listbox`, which violates ARIA `listbox` ownership rules (an interactive `button` inside `listbox` is invalid and unreachable via the listbox's arrow-key handler). Additionally, `actualizarSugerencias` (`app/buscador.js:256`) creates `<li class="buscador-vacio">Place directory could not be loaded.</li>` without `role="presentation"` (unlike line 174).

### 10. [Medium] Indistinguishable duplicate button accessible names (`9x "Show map"`, `4x "Show"`)
- **Files**: `app/hidrologia.js:131` (`filtrarCatalogo`), `index.html:171-174` (`#fenomenos` `"More layers"`).
- **What happens & why it is a bug**: `filtrarCatalogo` renders 9 SINAPRED catalog rows each with `<button type="button">Show map</button>` without `aria-label` or `aria-describedby` linking the button to its layer name. Similarly, `index.html:171-174` renders 4 `"More layers"` rows each with `<button type="button" class="mini">Show</button>` with no distinct accessible name.
- **Verification**: Playwright inspection of `#hid-catalogo` confirmed 9 buttons with `{'text': 'Show map', 'aria': None}`.

### 11. [Low] Double `requestSubmit()` on 3D globe point selection (`void elegirPunto ?? fallback`)
- **Files**: `app/globo.js:62-64` (`iniciar`), `app/shell.js:60` (`elegirPunto`).
- **What happens & why it is a bug**: `elegirPunto(lat, lon)` returns `undefined`, so `window.elegirPunto?.(lat, lon) ?? (function () { ... $('consulta-punto').requestSubmit(); })()` always evaluates the fallback IIFE too, invoking `$('consulta-punto').requestSubmit()` twice per globe click.

---

## Clean Areas Verified
- **JS Syntax**: All 25 non-module JS files (`app/*.js`, `src/*.js`) passed `node --check`.
- **HTML/Dynamic ID uniqueness**: `index.html` and JS-created IDs have 0 duplicates / collisions.
- **Help/Resource Data Integrity**: `tests/test_ayuda.py` and `tests/test_interfaz.py` passed (`13 passed, 12 subtests passed`); all 100 `enlace` targets in `data/ayuda_preguntas.json`, `app/inicio.js` demo IDs, and all 9 `sinapred_catalogo.json` layers (`NOMBRES_SINAPRED`) matched cleanly.
- **GeoJSON English Labels**: All non-lake features in `assets/mundo.geojson` (`tipo !== 'lago'`) have `nombre_en` populated (`non-lake missing nombre_en: []`).
- **Color Contrast (WCAG 2.2 AA)**: 18 sampled CSS foreground/background pairs across `estilos.css`, `ayuda.css`, `buscador.css`, `inicio.css`, and `reticula.css` all measured `>= 5.26:1` (passing `4.5:1`).

---

## Files Inspected
- `index.html`
- `app/ayuda.js`, `app/buscador.js`, `app/campo.js`, `app/config.js`, `app/coordenadas.js`, `app/espacio.js`, `app/fenomenos.js`, `app/globo.js`, `app/graficas-meteo.js`, `app/hidrologia.js`, `app/indicadores.js`, `app/inicio.js`, `app/investigar.js`, `app/reticula.js`, `app/shell.js`, `app/soporte-meteo.js`, `app/teselas-globo.js`, `app/teselas-geometria.mjs`, `app/tutorial.js`
- `app/estilos.css`, `app/ayuda.css`, `app/buscador.css`, `app/inicio.css`, `app/reticula.css`
- `src/contrato.js`, `src/fuentes-meteo.js`, `src/globo-meteo.js`, `src/graficas.js`, `src/hidrologia-datos.js`, `src/meteo-paletas.js`, `src/tendencias.js`
- `tests/test_ayuda.py`, `tests/test_interfaz.py`, `tests/interfaz_normalizada.cjs`, `tests/test_e2e_navegador.py`, `tests/test_recursos_interfaz.py`, `tests/e2e/sonda.js`
- `assets/mundo.geojson`, `data/dominios.geojson`

## Checks Run
- `node --check` on all 25 JS files in `app/*.js` and `src/*.js`: **25/25 passed**.
- `python -m pytest tests/test_ayuda.py tests/test_interfaz.py -q`: **13 passed, 12 subtests passed in 0.37s**.
- GeoJSON `nombre_en` check on `assets/mundo.geojson` (`652` features) and `data/dominios.geojson` (`5` features): **0 non-lake `mundo.geojson` features missing `nombre_en`**.
- Headless Microsoft Edge Playwright probes across `1366x768`, `768x1024` (`has_touch=True`), `390x844`, `360x740`, `740x360`, and blocked `unpkg.com` (`404`): reproduced Findings #1–#8 and #10 above.
