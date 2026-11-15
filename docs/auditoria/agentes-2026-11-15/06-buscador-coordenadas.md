# Agente 06: Buscador y Coordenadas

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

Audit completed for `app/buscador.js`, `app/buscador.css`, `app/coordenadas.js`, `data/lugares_mundo.json`, and their integration with `index.html`, `app/shell.js`, and `app/estilos.css`.

### Confirmed Findings

1. **[High] Unchecked `proj4` calls & `Infinity`/`NaN` output in Nicaragua UTM 16N (`EPSG:32616`)**
   - **Location**: `app/coordenadas.js:130-138` (`formatear` case `'epsg32616'`); also `app/coordenadas.js:43-59` (`aUtm`) and `121-129` (`epsg3857`).
   - **Issue**: `proj4('EPSG:4326', PROJ_32616, [l, lat])` has no `try/catch` and no `Number.isFinite` check on `[e, n]`. Selecting `Nicaragua · UTM 16N (EPSG:32616)` and hovering/clicking near `±90°` from Zone 16's central meridian (`87°W`, i.e., `3°E` and `177°W`) hits the Transverse Mercator singularity, producing `"Infinity E, Infinity N m"` (or `"NaN"`/uncaught exception if `proj4` throws).
   - **Evidence**: Validated all 3,333 cities in `data/lugares_mundo.json` with `pyproj`: 62 cities (e.g., Benin `Cotonou`/`Porto-Novo`, Cameroon `Douala`/`Limbe` near `3°E`) returned `(inf, inf)` for `+proj=utm +zone=16`. Node reproducer of `app/coordenadas.js` returned `{ texto: 'Infinity E, Infinity N m', nota: 'Note: point is outside UTM 16N (90°W–84°W, N)' }`.
   - *Note on CDN failure*: When `proj4` fails to load (`typeof proj4 !== 'function'`), `app/coordenadas.js` does **not** crash — it returns `'Projection library unavailable'` for `utm`/`mgrs`/`epsg3857`/`epsg32616`, and `wgs84_*` modes continue working (verified in Node).

2. **[High] Mobile `#panel-coordenadas` clipped inside 72px/56px `#barra-capas` bar & inaccessible outside `solo-mapa`**
   - **Location**: `app/coordenadas.js:194-212`, `app/buscador.css:50-58` vs `app/estilos.css:92, 247-248, 256-260, 284`.
   - **Issue**: `coordenadas.js` prepends both `label.coords-opcion` and `#panel-coordenadas.coords-en-capas` into `#barra-capas .ventana-cuerpo`. On mobile (`<=700px` width or `<=500px` height & `<=1000px` width), `estilos.css:256-260, 284` turns `#barra-capas` into a bottom horizontal bar with fixed `height: calc(72px + env(safe-area-inset-bottom,0px))` (`56px` in landscape), `flex-direction: row; overflow-x: auto` on `.ventana-cuerpo`, and `overflow: hidden` on `.ventana` (`estilos.css:92`). Expanding `Coords ▸` opens `#coords-cuerpo` vertically inside that 72px/56px bar, clipping `<select>`, `Copy`, and the coordinate readout. Outside `solo-mapa` on mobile (`estilos.css:248`), `#controles-mapa > :not(#estado-meteo-mapa)` is `display: none`, hiding both the checkbox and panel.

3. **[Medium] `<input id="buscador-lugar">` capped at `140px` width by `estilos.css`**
   - **Location**: `app/buscador.css:3-7` (`.buscador-envoltura`, `.buscador-entrada`) vs `app/estilos.css:129-130` (`input{max-width:140px}`).
   - **Issue**: `app/estilos.css` (loaded before `app/buscador.css` in `index.html:12,14`) sets `input { max-width: 140px }`. `.buscador-entrada` overrides `min-width: 0` and sets `width: 100%`, but does not override `max-width`, capping the `<input>` at `140px` inside the `340px` desktop / full-width mobile `.buscador-envoltura` and truncating placeholder/selected place text.

4. **[Medium] Combobox keyboard, focus, and ARIA defects in `app/buscador.js`**
   - **Location**: `app/buscador.js:127-132` (`cerrarLista`), `216-237` (`elegirCiudad`), `255-260` (`actualizarSugerencias`), `265-272` (`focus`), `278-300` (`keydown`), `310-312` (`document` `click`).
   - **Issues (all verified in Node DOM harness)**:
     - **No `focusout`/`blur` closing**: Only `document.click` closes `#buscador-lista`; pressing `Tab` out of the combobox leaves `#buscador-lista` open (`aria-expanded="true"`) while focus moves elsewhere.
     - **Re-focusing after selecting a city shows "No matching countries or cities."**: `elegirCiudad` (`line 219`) sets `input.value = "${ciudad.nombre}, ${pais.nombre}"` (e.g., `"Managua, Nicaragua"`). Re-focusing triggers `actualizarSugerencias()` -> `buscar("Managua, Nicaragua")`, which matches 0 items because `indice` only indexes single names (`"managua"`, `"nicaragua"`).
     - **Stale `paisExpandido` hijacks view on `focus`**: `cerrarLista()` does not reset `paisExpandido = null`. After expanding a country and clicking outside to close, re-focusing the input runs `abrirPais(paisExpandido)`, switching back to 2D map (`SICC_vista.cambiar('mapa')`) and re-running `mapa.fitBounds(...)`.
     - **Fetch error `<li>` ARIA & `Escape` on `Back` button**: On `cargarDatos()` failure (`line 256`), the error `<li class="buscador-vacio">` lacks `role="presentation"` inside `role="listbox"` (unlike `line 174`) and doesn't clear `opcionesActuales`. `keydown` is only on `input`, so `Escape` while focused on `.buscador-volver` (`Back`) does not close the list.

5. **[Medium] Polar MGRS (`aMgrs`) uses ad-hoc 24-letter modulo placeholder instead of UPS MGRS grid letters**
   - **Location**: `app/coordenadas.js:66-73` (`aMgrs`).
   - **Issue**: For `lat < -80` or `lat > 84`, `aMgrs` indexes `'ABCDEFGHJKLMNPQRSTUVWXYZ'` via `Math.floor(e / 100000) % 24` and `Math.floor(n / 100000) % 24` for both poles. At `Amundsen–Scott South Pole Station` (`-90, 176.994`, `e=2000000, n=2000000`), index `20 % 24` produces `"B WW 00000 00000"` instead of standard UPS MGRS square letters (and uses 24 letters for North UPS `Y`/`Z`).

6. **[Medium] `gms()` emits `60.0"` seconds on rounding without carry**
   - **Location**: `app/coordenadas.js:84-92` (`gms`).
   - **Issue**: `((mf - m) * 60).toFixed(1)` rounds `>= 59.95` to `"60.0"` without carrying into minutes/degrees. Verified in Node: `gms(12.99999, 'N', 'S')` outputs `12° 59' 60.0" N`; `gms(12.01666, 'N', 'S')` outputs `12° 00' 60.0" N`.

7. **[Medium] Diacritics/Latin normalization gaps & invisible `U+200E` in `data/lugares_mundo.json`**
   - **Location**: `app/buscador.js:8` (`normalizar`), `data/lugares_mundo.json`.
   - **Issue**: NFD decomposition + `[\u0300-\u036f]` leaves non-decomposable Latin letters (`ł`, `ø`, `æ`, `đ`, `ð`, `ı`) and en-dash `–` (`U+2013` in `Amundsen–Scott South Pole Station`) unnormalized. Verified in Node: `buscar('lodz')`, `buscar('wroclaw')`, `buscar('tromso')`, `buscar('kobenhavn')`, `buscar('diyarbakir')`, `buscar('nam dinh')` all return `[]`. Additionally, `data/lugares_mundo.json` has a trailing invisible `U+200E` (LEFT-TO-RIGHT MARK) on `"Granada\u200e"` (both Nicaragua and Spain), causing `"granada\u200e" !== "granada"` (skipping the `+1000` exact-match bonus) and leaving `U+200E` in `input.value`.

8. **[Low] `zonaUtm` applies Norway/Svalbard exceptions to unwrapped `lon`**
   - **Location**: `app/coordenadas.js:23-34` (`zonaUtm`).
   - **Issue**: `zonaUtm` wraps `lon` for the base zone calculation but checks raw `lon` in the Norway/Svalbard overrides. `aUtm` wraps first, so this affects direct callers of `window.SICC_coordenadas.zonaUtm` (verified in Node: `zonaUtm(60, 5)` -> `32`, `zonaUtm(60, 365)` -> `31`).

---
### Files Inspected & Checks Run
- **Files inspected**: `app/buscador.js`, `app/buscador.css`, `app/coordenadas.js`, `app/shell.js`, `app/estilos.css`, `app/globo.js`, `app/inicio.js`, `app/reticula.js` (lines 1–45), `index.html`, `tests/test_lugares_coordenadas.py`, and `data/lugares_mundo.json` (programmatically).
- **Checks run**:
  - `node --check app/buscador.js` & `node --check app/coordenadas.js`: passed (exit 0).
  - `python -m pytest tests/test_lugares_coordenadas.py`: 4 passed in 20.01s.
  - Node `data/lugares_mundo.json` schema/content scan: 236 countries, 3,333 cities, 0 invalid coords/bboxes, 17 countries with 0 cities, 28 city names with non-ASCII chars remaining after NFD normalization (including 2× `"Granada\u200e"`).
  - Python `pyproj` validation across all 3,333 cities & polar/antimeridian/3857/32616 points: 0 UTM/UPS column errors, 62 cities returning `(inf, inf)` under `EPSG:32616`.
  - Node VM harnesses for `app/coordenadas.js` (with and without `proj4`) and `app/buscador.js` (error state, `paisExpandido` re-focus, city re-focus, normalization).
