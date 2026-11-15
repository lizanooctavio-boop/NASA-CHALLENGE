# Agente 02: Shell y Maquetacion

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

Audit of `app/shell.js`, `app/estilos.css`, and cross-checked DOM selectors in `index.html` (checkout `wt_audit20`, commit `20bec48`) is complete. All findings below were directly observed in code and verified with Playwright (MS Edge headless) / Node checks.

### Confirmed Findings

1. **[High] Mobile landscape header `flex-wrap: nowrap` crushes `.acciones` off-screen and overlaps controls with `.buscador-envoltura`**
   - **File:Line (Symbol)**: `app/estilos.css:196,199` (`@media(max-height:500px) and (max-width:1000px)` -> `header`, `.acciones`) interacting with `app/buscador.css:45` (`.buscador-envoltura{flex:1 1 100%;max-width:none;order:3}`).
   - **What happens & why**: `header` and `.acciones` force `flex-wrap: nowrap` while `.buscador-envoltura` has `flex: 1 1 100%; order: 3`. Because `.acciones` has `flex: 1; min-width: 0; justify-content: flex-end`, `.buscador-envoltura` consumes the row and pushes `#indicador-datos`, `.interruptor`, and `#solomapa` off the left side or behind the search box.
   - **Verification**:
     - `667x375`: `#indicador-datos` at `left: -129.05, right: -3.14`; `#solomapa` at `left: 2.86`; `page.click('#solomapa')` timed out (`element is outside of the viewport`).
     - `844x390`: `#indicador-datos` at `left: -127.72, right: -1.81`.
     - `667x375` with `solo-mapa` active: `.buscador-envoltura` (`left: 25..582.17`) overlaps `#vista-globo` (`19..97.6`), `#indicador-datos` (`178.25..200.25`), and `#solomapa` (`184.25..274.36`).

2. **[High] Desktop/compact sidebar (`aside`) overflows vertically with no scroll container, making bottom nav tabs unreachable**
   - **File:Line (Symbol)**: `app/estilos.css:4,30,165-179` (`body`, `aside`, `body.menu-plegado`) and `app/shell.js:124` (`plegarMenu`).
   - **What happens & why**: `aside` is `position: fixed; inset: 14px auto 14px 14px;` with no `overflow-y: auto` while `body` has `overflow: hidden`. With 11 nav buttons (`index.html:32-41` + `Help` from `app/ayuda.js:136-143`), `.sub`, and `.pie`, content exceeds `aside` height on common laptop/short desktop viewports and spills past the bottom of the viewport with no way to scroll.
   - **Verification**:
     - `1280x720` (`menuPlegado: false`): `aside` `clientHeight: 690`, `scrollHeight: 758`; `.pie` extends to `bottom: 722.64` (past viewport).
     - `1366x650` (`menuPlegado: false`): `aside` `clientHeight: 620`, `scrollHeight: 758`; `Sources` button (`[data-tab="fuentes"]`) is at `y: 609.25..654.25` (overflows viewport).
     - `1024x550` (`menuPlegado: true`): `aside` `clientHeight: 520`, `scrollHeight: 602`; both `Help` (`y: 524..568`) and `Sources` (`y: 573..617`) are completely below the `550px` viewport.

3. **[High] `hashchange` listener forces view back to 3D Globe on non-`#map` hashes, breaking "Skip to main content" in 2D Map mode**
   - **File:Line (Symbol)**: `app/shell.js:213` (`addEventListener('hashchange', ...)`) and `index.html:19` (`.saltar-contenido`).
   - **What happens & why**: `addEventListener('hashchange', () => cambiarVista(location.hash === '#map' ? 'mapa' : 'globo'))` treats any hash other than `#map` as a command to switch to `'globo'`. Activating `<a href="#contenido-principal" class="saltar-contenido">` while in 2D Map mode changes `location.hash` to `#contenido-principal` and switches the app out of the 2D Map back to the 3D Globe.
   - **Verification**: In `1280x720` Playwright test after switching to 2D Map (`['mapa', 'modo-mapa', '']`), focusing `.saltar-contenido` and pressing `Enter` changed state to `['globo', 'en-transicion modo-globo', '#contenido-principal']`.

4. **[Medium] `main { z-index: 4 }` traps `header` popups (`#indicador-detalle`, `.buscador-lista`) below `#controles-mapa` (`z-index: 6`)**
   - **File:Line (Symbol)**: `app/estilos.css:62,79,80,250` (`main`, `header`, `#indicador-detalle`, `#controles-mapa`) and `app/buscador.css:12` (`.buscador-lista`).
   - **What happens & why**: `main` establishes a stacking context with `z-index: 4`, so `header` (`z-index: 10`), `#indicador-detalle` (`z-index: 30`), and `.buscador-lista` (`z-index: 30`) cannot paint above `#controles-mapa` (`z-index: 6`).
   - **Verification**: At `667x375` in `solo-mapa` mode, `#buscador-lista` spans `y: 61..381` and `#linea-tiempo` spans `y: 242.83..315` (`x: 341.5..661`); `document.elementFromPoint(381.5, 257.83)` returns `#lt-play` (`ltContainsTop: true, listaContainsTop: false`).

5. **[Medium] Unchecked optional DOM elements in `app/shell.js` throw uncaught `TypeError`s on startup**
   - **File:Line (Symbol)**: `app/shell.js:99` (`[data-descarga="punto"]`), `106` (`$('controles-mapa')`), `119` (`$('plegar-menu')`), `137` (`#barra-capas .ventana-cuerpo`), `138` (`linea-tiempo`, `leyenda-campo`, `barra-capas`, `header`), `146-147,193-194` (`$('vista-globo')`, `$('vista-mapa')`) — inconsistent with null guards on lines `97,105,130,134,136,150-152`.
   - **What happens & why**: When any of these elements is absent, `shell.js` throws `TypeError` during initialization (and lines `99`/`106` abort before `iniciarMapa()` at line `113`).
   - **Verification**: Playwright HTML route tests removing each element reproduced uncaught `pageerror`s:
     - `#controles-mapa`: `Failed to execute 'observe' on 'ResizeObserver': parameter 1 is not of type 'Element'.`
     - `#plegar-menu`: `Cannot read properties of null (reading 'setAttribute')`
     - `#linea-tiempo`: `Failed to execute 'observe' on 'ResizeObserver': parameter 1 is not of type 'Element'.`
     - `#vista-globo`: `Cannot set properties of null (setting 'onclick')`
     - `#barra-capas .ventana-cuerpo`: `Cannot read properties of null (reading 'addEventListener')`

6. **[Medium] Double-clicking `.ventana-barra` skips `sicc:paneles`, and hiding a panel via `.punto.rojo` drops keyboard focus to `<body>`**
   - **File:Line (Symbol)**: `app/shell.js:112` (`barra.ondblclick`) vs `111` (`boton('ambar', ...)`), and `app/shell.js:102` (`soloMapa`).
   - **What happens & why**: `barra.ondblclick` toggles `.minimizada` without dispatching `sicc:paneles`, leaving `globo.js:desplazar()` and `tendencias.js` unnotified. Separately, calling `soloMapa(true)` from inside a panel (`.punto.rojo`) sets `.vista { display: none }` (`app/estilos.css:101`) without moving focus, dropping `document.activeElement` to `BODY`.
   - **Verification**: In `1280x720` Playwright test, dispatching `dblclick` on `#meteorologia .ventana-barra` set `.minimizada` (`minAfterDbl: true`) with `0` `sicc:paneles` events (`countAfterBtn: 1`). Pressing `Enter` on `#meteorologia .punto.rojo` left `document.activeElement` at `BODY`.

7. **[Medium] Global `Escape` handler in `shell.js` closes `#error` without stopping sibling `document` `keydown` handlers**
   - **File:Line (Symbol)**: `app/shell.js:14` (`document.addEventListener('keydown', ...)`) vs `app/campo.js:124` and `app/reticula.js:55`.
   - **What happens & why**: `shell.js:14` calls `e.preventDefault()` but not `e.stopImmediatePropagation()`. When `#error` and `#indicador-detalle` are both open, a single `Escape` closes both simultaneously and lets `campo.js:124` steal focus to `#indicador-datos`.
   - **Verification**: Verified in `1280x720` Playwright test (`before: {errHidden: false, detHidden: false}` -> single `Escape` -> `after: {errHidden: true, detHidden: true}`).

8. **[Low] Dead CSS selectors in `app/estilos.css` targeting missing/removed DOM IDs**
   - **File:Line (Symbol)**: `app/estilos.css:139` (`#mapaestado`, `#campo-estado`, `#grillaestado`), `142-143,310` (`#aviso-cerrar`), `150` (`#vivo-estado`), `174,184,277,287,290` (`#aviso-publico`), `241,248,249,255,282` (`#estado-meteo-mapa`), `302` (`body.aviso-encima`), `338` (`#regiones`).
   - **What happens & why**: None of these IDs exist in `index.html` or any JS file under `app/` or `src/`. (Line `280` also reserves a `'estado'` grid-template area for `#estado-meteo-mapa`, and line `287` gates header width on `:not(:has(#aviso-publico:not([hidden])))`).

---

### Files Inspected & Checks Run
- **Files inspected**: `app/shell.js`, `app/estilos.css`, `index.html` (plus cross-checks against `app/ayuda.js`, `app/ayuda.css`, `app/buscador.js`, `app/buscador.css`, `app/inicio.js`, `app/inicio.css`, `app/reticula.js`, `app/reticula.css`, `app/campo.js`, `app/espacio.js`, `app/globo.js`, `app/tutorial.js`).
- **Checks run**:
  - `node --check app/shell.js`: exited `0`.
  - `git status --short`: clean (no modified/untracked files).
  - Node selector cross-check (`app/shell.js` `$()` IDs vs `index.html`): 22/22 IDs present in `index.html`; `app/estilos.css` selector scan found 8 missing IDs listed in Finding 8.
  - Headless MS Edge Playwright checks across `1280x720`, `1366x650`, `1024x550`, `800x600`, `375x667`, `667x375`, `844x390`, `560x360` reproducing all runtime/layout/keyboard findings above.
