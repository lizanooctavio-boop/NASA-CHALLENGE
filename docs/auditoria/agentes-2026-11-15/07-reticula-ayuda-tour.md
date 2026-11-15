# Agente 07: Reticula, Ayuda, Tutorial e Inicio

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

Audit of graticule/orientation, help modal, onboarding/welcome, and guided tour in `wt_audit20` (HEAD `20bec48`) complete. All checks were read-only; working tree remains clean.

### Confirmed Findings

1. **[Medium] "Show me" fails to un-minimize minimized tab panels when targeting a tab ID**
   - **Location:** `app/ayuda.js:111-112` (`mostrar`)
   - **What happens:** When `enlace` matches a tab ID (e.g., `investigar`, `tendencias`, `indicadores`, `hidrologia`, `fenomenos`, `escenarios`, `exportar`, `aprender`, `fuentes`, `meteorologia` — 28 entries in `data/ayuda_preguntas.json`), `mostrar` enters the `if(boton&&el?.classList.contains('vista'))` branch, calls `irAPestana(enlace)`, and reassigns `el` to `.ventana-cuerpo h2, .ventana-cuerpo h3, .ventana-cuerpo`. Unlike the `else if(el)` branch (`app/ayuda.js:117`), line 112 never removes `.minimizada` (`.ventana.minimizada .ventana-cuerpo{display:none}` in `app/estilos.css:100`). As a result, `el` remains `display: none`, failing to scroll, highlight, or focus.
   - **Verification:** Headless Edge (`SICC_ayuda.mostrar('tendencias')` with `.minimizada` set): `{"tendenciasHidden": false, "minimizada": true, "h2Rect": {"width": 0, "height": 0}, "activeTag": "BODY"}`.

2. **[Medium] "Show me" targets hidden elements on mobile (`#barra-capas`, `#linea-tiempo`, `#plegar-menu`) and unpopulated/hidden `#inv-contrastes`**
   - **Location:** `app/ayuda.js:113-125` (`mostrar`), `data/ayuda_preguntas.json`
   - **What happens:**
     - On mobile (`max-width: 700px` or `max-height: 500px and max-width: 1000px`), `app/estilos.css:248` hides `#barra-capas` and `#linea-tiempo` (`display: none`) while `body:not(.solo-mapa)` is active, and `app/estilos.css:189` hides `#plegar-menu` (`display: none`). Calling `mostrar` for any of the 12 questions linking to `barra-capas`, `linea-tiempo`, `chk-particulas`, `chk-sat`, `chk-imerg`, `chk-sst`, `chk-aod`, `chk-radar`, `chk-tormentas`, or `plegar-menu` does not toggle `soloMapa(true)`, leaving the target `0x0` (`display: none`).
     - Question `investigar-05` links to `inv-contrastes` (`<article id="inv-contrastes" hidden>` in `index.html:87`), which is hidden until `app/investigar.js` asynchronously loads `data/recursos_integrados.json` and selects an investigation with `contrastes.length > 0`. `mostrar('inv-contrastes')` only waits 60ms (`app/ayuda.js:120`) and does not switch to a contrast-bearing investigation, so if data hasn't finished loading or an investigation without cross-checks (e.g., `ciclones`) is active, `#inv-contrastes` remains `hidden: true` (`0x0`).
   - **Verification:** Headless Edge at `375x667`: `SICC_ayuda.mostrar('chk-imerg')` -> `{"soloMapa": false, "barraCapasDisplay": "none", "imergRect": {"width": 0, "height": 0}, "activeId": "ayuda-buscar"}`. Desktop `SICC_ayuda.mostrar('inv-contrastes')` after selecting `ciclones` -> `{"hidden": true, "rect": {"width": 0, "height": 0}, "activeId": ""}`.

3. **[Medium] First-visit Terra invitation becomes invisible when the active panel is minimized**
   - **Location:** `app/tutorial.js:157-164` (`colocarInvitacion`)
   - **What happens:** `colocarInvitacion()` finds the active `.vista` using `!v.hidden && visible(v)` and resolves `dentro = vista.querySelector('.ventana-cuerpo') || vista`. When the open panel has `.minimizada`, the `.vista` itself is still visible via `.ventana-barra`, so `visible(vista)` is `true`, and `colocarInvitacion()` prepends `.tour-invitacion` inside `.ventana-cuerpo` (`display: none`), hiding the invitation completely instead of floating it on `document.body`.
   - **Verification:** Headless Edge (`#meteorologia.minimizada` + `SICC_tutorial.invitar()`): `{"parent": "ventana-cuerpo", "display": "none", "w": 0, "h": 0}`.

4. **[Medium] Focus drops to `<body>` when the guided tour is started from the first-visit invitation and then closed**
   - **Location:** `app/tutorial.js:37-42,131-135,147` (`iniciar`, `cerrar`, `invitar`)
   - **What happens:** `iniciar()` calls `cerrarInvitacion(false)` on line 38 *before* capturing `previo = document.activeElement` on line 40. When started via the `Start` button inside `.tour-invitacion` (`line 147`), `cerrarInvitacion(false)` removes `invitacion` from the DOM (`line 169`), resetting `document.activeElement` to `document.body`. Line 40 captures `previo = document.body`. On `cerrar()` (`line 134`), `document.body.isConnected` is `true`, so `document.body.focus()` executes (a no-op on non-focusable `<body>`) instead of focusing `#contenido-principal` or `#menu-tour`.
   - **Verification:** Headless Edge: clicked `.tour-invitacion .tour-principal`, pressed `Escape` -> `document.activeElement` became `BODY#`.

5. **[Medium] Async load race on tour steps 5–7 highlights a 0px-tall `#inv-demos` and leaves `.tour-foco` stale**
   - **Location:** `app/tutorial.js:12,27-29,55-73,98-117` (`visible`, `PASOS`, `objetivo`, `ir`, `recolocar`)
   - **What happens:** Steps 5–7 (`#inv-categorias`, `#inv-veredicto`, `#inv-demos`) invoke `irAPestana('investigar')`, triggering an async `fetch('data/recursos_integrados.json')` in `app/investigar.js:54,286`. `ir(n)` only awaits two `requestAnimationFrame`s (`line 70`) and never calls `recolocar()` once `investigar.js` populates the DOM. Additionally, before load completes, `<div id="inv-demos" class="demos"></div>` has `height: 0` (no `min-height` in CSS), yet `visible(el)` (`el.getClientRects().length > 0`, `line 12`) returns `true` for a 0px-height block/flex container, so `objetivo()` does not fall back to `respaldo: '#investigar'` and highlights a 12px-tall empty line.
   - **Verification:** Headless Edge with `recursos_integrados.json` delayed 1.5s: on Step 7, `demosChildren: 0`, `demosRect.height: 0`, `focoStyle: {"top": "778.094px", "height": "12px", "hidden": false}`.

6. **[Medium] Guided tour Step 4 ("Layers") target `#barra-capas` is `display: none` on mobile**
   - **Location:** `app/tutorial.js:26` (`PASOS[3]`)
   - **What happens:** Step 4 targets `#barra-capas` with no `respaldo` and no `antes` hook. On mobile (`max-width: 700px` or `max-height: 500px and max-width: 1000px`), `app/estilos.css:248` hides `#barra-capas` (`display: none`) whenever `body:not(.solo-mapa)` is active (which is true during the tour). `objetivo(PASOS[3])` returns `null`, hiding the spotlight while telling mobile users to use Layers.
   - **Verification:** Headless Edge at `375x667`, Step 4: `{"stepTitle": "Layers", "barraCapasDisplay": "none", "barraCapasRect": {"width": 0, "height": 0}, "focoHidden": true}`.

7. **[Medium] Header `#menu-tour` stays enabled and fails silently into hidden `#ayuda-estado` if `app/tutorial.js` fails to load or is still loading**
   - **Location:** `app/ayuda.js:128,147,258-259` (`iniciarTour`, `crearBotonMenu`)
   - **What happens:** `s.onerror` (`line 259`) disables `#ayuda-tour` (inside `#ayuda`) with hardcoded `TXT.en.sinTour`, but does not disable `#menu-tour` in `header` (`line 147`). Clicking `#menu-tour` invokes `iniciarTour()` (`line 128`), which writes the error message to `#ayuda-estado` inside the hidden `#ayuda` panel, giving no visible or accessible error feedback on any other tab.
   - **Verification:** Headless Edge with `app/tutorial.js` aborted: clicking `#menu-tour` -> `{"menuTourDisabled": false, "ayudaTourDisabled": true, "ayudaEstado": "The guided tour is not available right now.", "ayudaHidden": true}`.

8. **[Low] `.capas-seccion` headings wrap onto multiple lines inside the mobile horizontal Layers strip**
   - **Location:** `app/inicio.js:28-33`, `app/inicio.css:5-6`
   - **What happens:** `app/inicio.js` injects `<div class="capas-seccion">Map grid</div>` and `<div class="capas-seccion">Weather layer</div>` into `#barra-capas .ventana-cuerpo`. On mobile (`app/estilos.css:256-260`), `.capas-mapa .ventana-cuerpo` becomes a 72px-tall `flex-direction: row` scrolling strip and hides `<hr>`, but `.capas-seccion` lacks `flex: none; white-space: nowrap` or mobile hiding, causing both labels to wrap tightly inside the strip.
   - **Verification:** Headless Edge at `375x667` (`solo-mapa`): `Map grid` rendered at `28.8x52px`, `Weather layer` at `55.3x44px` inside `barHeight: 72px`.

9. **[Low] Landscape mobile header pushes `#menu-tour` (and `.acciones` controls) offscreen left**
   - **Location:** `app/ayuda.css:67` (`#menu-tour`), interacting with `app/estilos.css:196-199` and `app/buscador.css:45`
   - **What happens:** In the landscape mobile media query (`max-height: 500px and max-width: 1000px`), `header` and `.acciones` have `flex-wrap: nowrap`, `.buscador-envoltura` has `flex: 1 1 100%; order: 3`, and `#menu-tour` has `flex: none` inside `.acciones`. This pushes `.acciones` off the left edge of the viewport.
   - **Verification:** Headless Edge at `667x375`: `#menu-tour` rendered at `x: -18.70` (partially offscreen left and overlapping `#titulo` at `x: 21..84.66`), and `#interruptor`/`#indicador-datos`/`#solomapa` at `x: -399..-24`.

10. **[Low] WCAG 2.5.3 Label in Name mismatch on `#reticula-toggle`**
    - **Location:** `app/reticula.js:22,57`
    - **What happens:** `#reticula-toggle` sets `aria-label="Geographic grid"` (`line 22`) while updating visible `textContent` to `"Show grid"` / `"Hide grid"` (`line 57`), so the accessible name does not contain the visible text label.

### Clean Areas Verified
- **Syntax & unit checks:** `node --check` passed on `app/reticula.js`, `app/ayuda.js`, `app/inicio.js`, and `app/tutorial.js` (exit 0). `python -m pytest tests/test_ayuda.py -v` passed 7/7 tests.
- **Resource/image paths & `ayuda_preguntas.json` IDs:** All 100 questions in `data/ayuda_preguntas.json` map to existing IDs in `index.html` (54) or `app/ayuda.js` (2: `ayuda-tour`, `ayuda-idioma`), and `app/inicio.js` example `{categoria:'costa',lugar:'mediterraneo',investigacion:'mediterraneo_olas_calor'}` exists and resolves cleanly in `data/recursos_integrados.json`. No broken image/capture paths were found in the 7 audited files.
- **Graticule (`app/reticula.js`, `app/reticula.css`):** Aside from finding #10, 2D/3D canvas rendering, coordinate wrapping/formatting, `#reticula-guia` Escape/pointerdown dismissal, and positioning avoidance of `#barra-capas`, `#controles-mapa`, and `#panel-coordenadas` worked without errors in headless Edge (`TEST_L_RETICULA`, `TEST_M_GUIA_1024`, `TEST_M_GUIA_MOB`).
- **Tour keyboard trap (`app/tutorial.js:118-130`):** `Tab`, `Shift+Tab`, and `Escape` inside `.tour-tarjeta` trapped focus and closed the tour cleanly in headless Edge (`TEST_N_TOUR_KEYS`).

### Files Inspected & Checks Run
- **Files inspected:** `app/reticula.js`, `app/reticula.css`, `app/ayuda.js`, `app/ayuda.css`, `app/inicio.js`, `app/inicio.css`, `app/tutorial.js`, `index.html`, `data/ayuda_preguntas.json`, `data/recursos_integrados.json`, `app/shell.js`, `app/estilos.css`, `app/buscador.js`, `app/buscador.css`, `app/coordenadas.js`, `app/espacio.js`, `app/investigar.js`, `app/globo.js`, `app/campo.js`, `app/hidrologia.js`, `tests/test_ayuda.py`.
- **Checks run:**
  - `node --check app/reticula.js; node --check app/ayuda.js; node --check app/inicio.js; node --check app/tutorial.js` -> exited 0 (all valid).
  - `python -m pytest tests/test_ayuda.py -v` -> 7 passed in 0.60s.
  - Inline Node scripts verifying `data/ayuda_preguntas.json` `enlace` targets against `index.html`, `mediterraneo_olas_calor` in `data/recursos_integrados.json`, and U+0300–U+036F diacritic regex codepoints in `app/ayuda.js:39`.
  - Headless Edge (Playwright) probes against read-only local HTTP server (`1280x800`, `1024x768`, `375x667`, `667x375`) verifying all reported DOM/focus/async/layout defects with 0 uncaught page errors.
  - `git status -s` -> clean (no files modified or created in `wt_audit20`).
