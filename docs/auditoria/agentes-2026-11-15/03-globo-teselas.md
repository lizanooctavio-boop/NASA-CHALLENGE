# Agente 03: Globo 3D y Teselas

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

## Audit Summary: 3D WebGL Globe, Progressive Satellite Tiles & 2D Fallback

Worktree audited (read-only, `git status` clean): `.` (`20bec48`).

### Confirmed Findings

1. **[High] Progressive satellite tiles fail to render after download and skip LOD updates under `prefers-reduced-motion: reduce`**
   - **Location**: `app/teselas-globo.js:122-125, 137, 174` (`crearTeselas`, `pump`, `update`); `app/espacio.js:306, 327` (`bucle`, `arrancar`).
   - **Bug**: Under `prefers-reduced-motion: reduce`, `espacio.js` disables `bucle()` and only calls `dibujar()` synchronously on user input (`wheel`, `pointermove`, `keydown`). When `teselas.update()` queues async tile fetches, `install()` (`teselas-globo.js:122`) has no callback to request a render, so newly downloaded tiles never appear until another user input event occurs. In addition, `teselas-globo.js:174` applies a 350ms fade-in (`(now - v.born) / 350`) regardless of `prefers-reduced-motion`, and `teselas-globo.js:137` throttles `select()` by `180ms` (`now - last > 180`), causing rapid zoom/pan inputs within 180ms to skip `select()`/`pump()` on the final pose with no loop to retry later.
   - **Verification**: Playwright (`msedge`, `reduced_motion='reduce'`): zooming in with wheel events (`dist = 1.1066`, `cached = 146`, `visible = 12`, `active = 6`) and waiting 1.2s with no input left `visible = 12, cached = 146, active = 6` frozen; a single tiny wheel (`deltaY = -10`) immediately jumped `visible` from `12` to `35` and `cached` to `181` (`active = 0`). Three rapid `Equal` keypresses (<180ms) similarly left `visible = 5, cached = 5, active = 6` frozen after 1.2s, jumping to `visible = 50, cached = 68` on the next keypress.

2. **[High] 3D→2D mode switch (`aMapa`) drifts off-center (`desp`) during the post-animation cross-fade window**
   - **Location**: `app/espacio.js:309-319, 393-412` (`bucle`, `aMapa`); `app/shell.js:172-177` (`cambiarVista`).
   - **Bug**: `aMapa()` animates `estado.desp` to `0` and `estado.morph` to `1` so the flattened Mercator mesh aligns with Leaflet. Once `aMapa()` resolves, `estado.animando` becomes `false`, and `shell.js:176` waits `520ms` before calling `window.Espacio.pausar(true)` (`shell.js:177`). During those 520ms on desktop (`>= 1000px` with `despObjetivo > 0`), `bucle()` is still active and runs `estado.desp += (estado.despObjetivo - estado.desp) * Math.min(1, dt * 5)` (`app/espacio.js:318`), sliding the flattened globe off-center away from Leaflet before pausing.
   - **Verification**: Playwright (`msedge`, `1280x800`): switching to Map produced `window.Espacio.estado()` with `morph: 1, pausado: true, desp: 265.6876269374999, despObjetivo: 288.15` instead of `desp: 0`.

3. **[High] Missing WebGL context-loss recovery and CDN-failure 2D fallback**
   - **Location**: `app/espacio.js:16-24, 304-324` (`renderer`, `bucle`); `app/shell.js:204-212`; `index.html:281`.
   - **Bug**:
     - `#espacio` has no `webglcontextlost` or `webglcontextrestored` handlers. If WebGL context is lost after startup, `bucle()` and `teselas.update()` keep running (fetching tiles), `espacio:error` never fires, `#vista-globo` stays enabled, and the user is left on a blank black canvas instead of falling back to 2D.
     - If `three.module.min.js` (CDN) fails to load, neither `espacio:listo` nor `espacio:error` fires, leaving `<body class="modo-globo cargando">` stuck indefinitely showing `"Loading 3D Earth…"` (`#carga-globo` `display: flex`) with `#mapa` hidden (`visibility: hidden`).
     - When `new THREE.WebGLRenderer(...)` fails (`espacio.js:19-24`), it dispatches `espacio:error` (activating the 2D map) but re-throws `e` (`throw e;` at line 23), producing an uncaught module error.
   - **Verification**: Playwright (`msedge`):
     - `WEBGL_lose_context`: `lostFired: True, defaultPrevented: True`, `modo: 'globo'`, `globeDisabled: False`.
     - Aborting `three.module.min.js`: `modo: 'globo'`, `bodyClasses: 'modo-globo cargando'`, `spinnerVisible: 'flex'`, `globeBtnDisabled: False`.
     - Mocking `getContext('webgl*')` → `null`: 2D fallback activated (`modo: 'mapa'`, `globeBtnDisabled: True`) with uncaught `pageerror: Error creating WebGL context.`.

4. **[Medium] Opaque child-tile fade-in mixes over Blue Marble (`uDia`) instead of the visible parent tile**
   - **Location**: `app/teselas-globo.js:19-24, 89-97, 158-175` (`fragment`, `install`, `update`); `app/espacio.js:157, 178`.
   - **Bug**: `update()` keeps a parent tile visible for 350ms while a newly installed child tile fades in (`if (fading || now - v.born >= 350) break;`), with `renderOrder = t.z`. However, `install()` creates an opaque `ShaderMaterial` (`transparent` not enabled; fragment shader outputs `alpha = 1.0`), and line 23 blends `uTesela` against `dia` (the low-resolution NASA Blue Marble `uDia` texture) rather than the framebuffer/parent tile. For 350ms after installation, the child mesh overwrites the crisp parent tile underneath with `(1 - uDetalle) * BlueMarble + uDetalle * childTile`, briefly flashing low-res Blue Marble over loaded high-res imagery.

5. **[Medium] Geographic grid (`E.reticula`) is not drawn on the 3D globe under `prefers-reduced-motion: reduce`**
   - **Location**: `app/espacio.js:530-536` (`Espacio.reticula`).
   - **Bug**: `reticula()` only checks `if (estado.pausado) dibujar();` instead of `if (estado.pausado || reducido) dibujar();` (unlike `meteo`, `opacidad`, `viento`, and `desplazar` on lines 552–565). Because `bucle()` is disabled when `reducido === true` and `estado.pausado === false`, toggling the grid does not render on the 3D globe until the next camera interaction.
   - **Verification**: Playwright (`msedge`, `reduced_motion='reduce'`): clicking `#reticula-toggle` invoked `window.Espacio.reticula` (`retCalls: 1, pausado: False`) with `drawsAfterRet: 0` across subsequent animation frames.

6. **[Medium] Compact/mobile `#espacio` CSS height diverges from renderer aspect and click raycasting**
   - **Location**: `app/estilos.css:409`; `app/espacio.js:261-267, 444, 468, 511` (`tamano`, `gradosPorPixel`, `elegir`); `app/teselas-geometria.mjs:22-23` (`dragDegrees`).
   - **Bug**: On `@media(max-width:700px),(max-height:500px) and (max-width:1000px)`, CSS sets `#espacio{height:calc(100dvh - var(--alto-controles-mapa,0px))}`, while `tamano()` sizes the WebGL buffer and `camara.aspect` to `innerWidth`/`innerHeight`, and `elegir()` computes NDC Y from `e.clientY / innerHeight` rather than `canvas.getBoundingClientRect()`. When `--alto-controles-mapa > 0`, the globe is vertically squished and pointer picking is vertically offset. Additionally, `dragDegrees(distance, height)` divides by `height` without a `> 0` guard (`dragDegrees(4.9, 0)` → `Infinity`).

7. **[Low] `src/globo-meteo.js` `muestreador` throws `TypeError` on null `meta` or `< 2` grid dimensions**
   - **Location**: `src/globo-meteo.js:5-19` (`muestreador`, `textura`).
   - **Bug**: Line 6 checks `!matriz || !meta.latitudes?.length || !meta.longitudes?.length`, which throws `TypeError` if `meta` is null/undefined, and for a 1×1 grid computes `dy = NaN` and `i = -1` (`matriz[-1]` → `TypeError`). Valid multi-point ECMWF grids (and `app/globo.js:32` checking `!meta`) work as expected.
   - **Verification**: Node `vm` check: `null meta` threw `TypeError: Cannot read properties of null (reading 'latitudes')`, `1x1` threw `TypeError: Cannot read properties of undefined (reading 'NaN')`, valid `2x2` returned `1080x540` canvas.

### Clean Areas Noted
- `app/globo.js` run-staleness checks (`corrida_utc`), request superseding (`turno`), `Promise.allSettled` handling, and `src/globo-meteo.js` equirectangular canvas-to-WebGL UV orientation (`lat = +90°` → `y = 0` → `uv.y = 1.0`) match `app/espacio.js` shaders.
- `app/teselas-globo.js` `evict()` properly disposes `geometry`, `material`, `texture`, and closes `ImageBitmap` (`bitmap.close()`), and aborts/closes bitmaps if disabled before installation.
- `app/teselas-geometria.mjs` pure geometry (`bounds`, `point`, `tileAt`, `zoomDistance`) passes all existing tests.

### Files Inspected & Checks Run
- **Files inspected**: `app/globo.js`, `app/teselas-globo.js`, `app/teselas-geometria.mjs`, `src/globo-meteo.js`, `app/espacio.js`, `app/shell.js`, `app/campo.js`, `app/reticula.js`, `app/estilos.css`, `index.html`, `src/meteo-paletas.js`, `src/fuentes-meteo.js`, `app/soporte-meteo.js`, `app/config.js`, `tests/teselas-geometria.test.mjs`, `tests/globo-detalle.cjs`, `scripts/preparar_render.mjs`, `scripts/preparar_meteo.mjs`.
- **Checks run**:
  - `node --check` on `app/globo.js`, `app/teselas-globo.js`, `app/teselas-geometria.mjs`, `src/globo-meteo.js`, `app/espacio.js`, `app/shell.js` → all exited `0`.
  - `node tests/teselas-geometria.test.mjs` → `3/3` passed (`0` failed).
  - `node tests/interfaz_normalizada.cjs` and `python -m pytest tests/test_interfaz.py -q` → `6 passed, 12 subtests passed`.
  - Node ESM/VM probes for `teselas-geometria.mjs` and `src/globo-meteo.js` edge cases, plus headless Playwright (`msedge` + SwiftShader) probes reproducing the reduced-motion, `aMapa` `desp`, WebGL context-loss / CDN failure, and `reticula` issues above.
  - `git status -s` → clean (no files modified).
