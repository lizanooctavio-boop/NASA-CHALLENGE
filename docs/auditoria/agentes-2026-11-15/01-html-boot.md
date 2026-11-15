# Agente 01: HTML y Arranque

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

# Audit Report: Entry HTML, Boot Sequence, Config, Assets & Launcher

Repository audited: `.` (HEAD `20bec48`). Read-only audit; `git status --short` clean.

---

## Confirmed Findings

### 1. [High] Missing error/load fallback for Three.js / `app/espacio.js` leaves app stuck on `Loading 3D Earth…`
- **File:Line (Symbol):** `index.html:18, 23, 281`, `app/espacio.js:4`, `app/shell.js:204-212`, `app/estilos.css:12`
- **What happens & why it is a bug:** `index.html:18` initializes `<body class="modo-globo cargando">`, which displays `#carga-globo` (`Loading 3D Earth…`) while `body.cargando:not(.modo-mapa)` is present (`app/estilos.css:12`). `app/espacio.js:4` statically imports `https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.min.js` (also without Subresource Integrity, unlike the `leaflet`, `chart.js`, and `proj4` CDN tags in `index.html:11, 258, 259, 278`). Unlike `app/reticula.js` (`index.html:282`), `<script type="module" src="app/espacio.js">` (`index.html:281`) has no `onerror` handler, and `app/shell.js:204-212` only removes `cargando` on `espacio:listo` / `espacio:error` / `window.Espacio` (with a 1200 ms fallback that only triggers when `location.hash === '#map'`). If the Three.js CDN fetch fails or is blocked, `app/espacio.js` never executes, neither event fires, and the default `#globe` view stays permanently stuck on the black `#01030a` screen with the `Loading 3D Earth…` spinner.
- **Verification/Repro evidence:** Direct inspection of `index.html:18, 23, 281`, `app/espacio.js:4`, `app/estilos.css:12`, and `app/shell.js:204-212`.

### 2. [Medium] `#map` / `visor/index.html` boot race cancels `aMapa()` transition and runs `intro()` on a hidden/paused globe
- **File:Line (Symbol):** `app/espacio.js:574-576` (boot tail), `app/espacio.js:346-375` (`animar`), `app/espacio.js:379-390` (`intro`), `app/espacio.js:393-412` (`aMapa`), `app/shell.js:203-212` (`salidaHash`), `visor/index.html:6, 10`
- **What happens & why it is a bug:** `visor/index.html` redirects to `../#map`. When `app/espacio.js` finishes loading textures (when `prefers-reduced-motion` is not `reduce`), line 574 synchronously dispatches `espacio:listo`. `app/shell.js:204` handles `espacio:listo` by calling `salidaHash()` → `cambiarVista('mapa')` → `window.Espacio.aMapa(...)` → `animar(1900, ...)` (when textures load before the 1200 ms timeout on `shell.js:212`). Immediately after `dispatchEvent` returns, `app/espacio.js:576` unconditionally executes `else intro()`, which calls `animar(3600, ...)`. Inside `animar()` (lines 347-348), starting `intro()` cancels `aMapa()`'s `requestAnimationFrame` and invokes `previa(false)` before frame 1, resolving `aMapa()` early with `false` (`estado.morph === 0`, `estado.dist === 30`) and leaving `intro()`'s 3.6 s animation loop running behind `#mapa` even after `shell.js:177` calls `window.Espacio.pausar(true)` (which only pauses `bucle()`, not `animar()`). If textures take > 1200 ms, `shell.js:212` already switched `modo` to `'mapa'`, `espacio:listo` calls `pausar(true)`, and line 576 still launches `intro()`.
- **Verification/Repro evidence:** Reproduced `animar()` cancellation sequence via `node -`:
  `after intro(): animando: true animId: 2`
  `aMapa resolved: false morph: 0 dist: 30 animId: 2`

### 3. [Medium] Unconditional `L.layerGroup()` in `app/hidrologia.js` throws `ReferenceError` if Leaflet CDN fails
- **File:Line (Symbol):** `app/hidrologia.js:22`, `index.html:258, 276`
- **What happens & why it is a bug:** While `app/shell.js:45`, `app/campo.js:11`, `app/fenomenos.js:8`, `app/indicadores.js:165`, and `app/reticula.js:33` guard against `window.L` / `mapa` being absent when `https://unpkg.com/leaflet@1.9.4/dist/leaflet.js` fails to load, `app/hidrologia.js:22` calls `etiquetas=L.layerGroup()` unconditionally during top-level IIFE execution. If Leaflet fails to load (offline, CDN outage, or SRI mismatch), `hidrologia.js` throws an uncaught `ReferenceError` before registering any Watersheds panel handlers (lines 137-153).
- **Verification/Repro evidence:** Reproduced via `node -` running `app/hidrologia.js` in a `vm` context without `L`:
  `hidrologia crash: ReferenceError: L is not defined`

### 4. [Medium] `Espacio.reticula()` omits reduced-motion redraw, breaking 3D grid toggle under `prefers-reduced-motion: reduce`
- **File:Line (Symbol):** `app/espacio.js:530-536` (`Espacio.reticula`) vs `app/espacio.js:306, 327, 552, 554, 563, 565`
- **What happens & why it is a bug:** Under `prefers-reduced-motion: reduce` (`reducido === true`), `bucle()` does not schedule frames (`arrancar()` line 327 draws once and returns; `bucle()` line 306 returns early). Every other `window.Espacio` setter (`meteo` line 552, `opacidad` line 554, `viento` line 563, `desplazar` line 565) calls `if (reducido) dibujar();`. `Espacio.reticula(lienzo)` (line 535) only checks `if (estado.pausado) dibujar();` and omits `|| reducido`. Because `estado.pausado` is `false` on the 3D globe, toggling the geographic grid (`#reticula-toggle`) or switching units (`#reticula-unidades`) updates `uniformes.uReticula.value` without redrawing the canvas.
- **Verification/Repro evidence:** Verified all `window.Espacio` methods in `app/espacio.js:529-573`; only `reticula(lienzo)` at line 535 checks `if (estado.pausado)` instead of `if (estado.pausado || reducido)` (or `if (reducido)`).

### 5. [Medium] ARIA & HTML validity defects in `index.html` (`#mapa` missing `role`; reference `<a>` elements missing `href`)
- **File:Line (Symbol):** `index.html:22`, `index.html:152-153`
- **What happens & why it is a bug:**
  - `index.html:22`: `<div id="mapa" aria-label="2D weather map" aria-hidden="true"></div>` places `aria-label` on a generic `<div>` with no `role`. Once `shell.js:151` removes `aria-hidden` and Leaflet makes `#mapa` keyboard-focusable (`tabindex="0"`), `#mapa` exposes a focusable container with an `aria-label` and no ARIA role.
  - `index.html:152-153`: `<a id="hid-referencia-fuente" target="_blank" rel="noopener">` and `<a id="hid-referencia-leyenda" target="_blank" rel="noopener">` omit `href` in initial HTML (only populated later in `app/hidrologia.js:102-103, 119` after clicking "Show reference map"), rendering styled cyan (`#hidrologia a`) placeholder links that are neither keyboard-focusable nor clickable until then.
- **Verification/Repro evidence:** Confirmed via Python `HTMLParser` audit of `index.html`:
  `L22: <div id="mapa"> has aria-label/labelledby without role`
  `L152: <a id="hid-referencia-fuente"> missing href attribute`
  `L153: <a id="hid-referencia-leyenda"> missing href attribute`

### 6. [Low] Unused configuration keys in `app/config.js` (`publico`, `teselas`)
- **File:Line (Symbol):** `app/config.js:1-7` (`window.SICC_CONFIG`)
- **What happens & why it is a bug:** `SICC_CONFIG.publico` (line 2) and `SICC_CONFIG.teselas` (`{ base, base_atribucion, etiquetas }`, line 6) are never read anywhere in `app/` or `src/`. Only `window.SICC_CONFIG.hidrologia_api` is read (`app/hidrologia.js:88`); 2D tile sources and attributions are hardcoded in `app/shell.js:49-56`.
- **Verification/Repro evidence:** Repository-wide search confirmed only `app/hidrologia.js:88` (and `tests/e2e/hidrologia_navegador.py:63`) accesses `SICC_CONFIG`, exclusively via `.hidrologia_api`.

---

## Clean / Verified Components (No Defects Found)
- **`INICIAR-APP.cmd`** & **`scripts/iniciar-local.ps1`**: Verified `scripts/iniciar-local.ps1`, `scripts/preparar_render.mjs`, and `scripts/servir-local.mjs` exist and all files copied by `preparar_render.mjs` exist in the checkout. (Note: `public/clima-base/` is intentionally absent after `preparar_render.mjs` without `preparar_meteo.mjs`, and `app/shell.js:239-250` intercepts clicks on `/clima-base/*.csv` downloads to display a clear error instead of a 404 page.)
- **`visor/index.html`**: Valid HTML5, static redirect (`../#map`) with no XSS vector; target `#map` hash is handled by `app/shell.js:203-213` (aside from Finding 2 in `app/espacio.js`).
- **DOM IDs & Local Asset/Script Paths in `index.html` and `app/espacio.js`**: All 5 CSS files, 24 JS/MJS files, 3 textures (`assets/texturas/tierra-dia.jpg`, `tierra-noche.jpg`, `luna.jpg`), and `data/hidrologia/fuentes_y_limites.md`, `procedencia.json`, `data/fenomenos_nicaragua.json` exist on disk. Automated scan across all `app/*.js`, `app/*.mjs`, and `src/*.js` found zero missing DOM IDs.
- **XSS in inline scripts/templates**: `index.html:282` (`onerror`) uses static `textContent`; `visor/index.html:10` uses a static string; `app/ayuda.js`, `app/buscador.js`, `app/hidrologia.js`, `app/investigar.js`, `app/indicadores.js`, and `app/tutorial.js` use `textContent` / `createElement` or static SVG templates.

---

## Files Inspected & Checks Run
- **Files inspected:** `index.html`, `visor/index.html`, `app/config.js`, `app/espacio.js`, `INICIAR-APP.cmd`, `scripts/iniciar-local.ps1`, `scripts/preparar_render.mjs`, `scripts/preparar_meteo.mjs`, `scripts/servir-local.mjs`, `app/teselas-globo.js`, `app/teselas-geometria.mjs`, `app/shell.js`, `app/globo.js`, `app/inicio.js`, `app/reticula.js`, `app/ayuda.js`, `app/tutorial.js`, `app/buscador.js`, `app/coordenadas.js`, `app/campo.js`, `app/soporte-meteo.js`, `app/graficas-meteo.js`, `app/fenomenos.js`, `app/indicadores.js`, `app/investigar.js`, `app/hidrologia.js`, `src/fuentes-meteo.js`, `src/graficas.js`, `src/tendencias.js`, `app/estilos.css`, `app/ayuda.css`, `app/inicio.css`, `app/reticula.css`, `app/buscador.css`, `README.md`, `tests/test_interfaz.py`, `tests/interfaz_normalizada.cjs`, `tests/globo-detalle.cjs`, `tests/test_e2e_navegador.py`, `tests/test_ayuda.py`, `tests/teselas-geometria.test.mjs`.
- **Checks run:**
  - `node --check` on `app/config.js`, `app/espacio.js`, and all 22 other frontend `.js`/`.mjs` files: **24/24 passed (exit 0)**.
  - `node --test tests/teselas-geometria.test.mjs`: **3/3 passed**.
  - `python -m unittest tests/test_interfaz.py`: **6/6 passed**.
  - `python -m pytest -q tests/test_ayuda.py tests/test_interfaz.py`: **13 passed, 12 subtests passed**.
  - Python path & DOM ID verification scripts: all local CSS/JS/texture/data paths (except `/clima-base/*.csv` as noted) exist; 0 missing DOM IDs referenced by JS.
  - Python `HTMLParser` ARIA/HTML check on `index.html`: caught L22 `#mapa` missing role, L152–153 missing `href`, L32–41 nav `<button>` missing explicit `type="button"` (minor).
  - Node `vm` reproducer for `app/hidrologia.js` without `L`: confirmed `ReferenceError: L is not defined`.
  - Node reproducer for `app/espacio.js` `animar()` race on `#map`: confirmed `aMapa resolved: false morph: 0 dist: 30 animId: 2`.
  - `git status --short`: clean (no modifications).
