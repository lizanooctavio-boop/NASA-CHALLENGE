# Agente 08: Hidrologia Frontend

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

### Hydrology / Watersheds Frontend Audit (`app/hidrologia.js`, `src/hidrologia-datos.js`)

Audited `app/hidrologia.js` and `src/hidrologia-datos.js` (plus supporting `index.html`, `app/config.js`, `app/shell.js`, `data/hidrologia/*`, `tests/test_hidrologia.py`) in `wt_audit20` (read-only, no files modified).

---

### Confirmed Findings

1. **[Medium] Leaflet `L.Canvas` renderer, `<canvas>` DOM, and map event listener leak on watershed / SINAPRED reloads**
   - **Location**: `app/hidrologia.js:53-54` (`pintarCuencas`), `app/hidrologia.js:117` (`mostrarSinapred`), `app/hidrologia.js:97, 105, 140, 147` (`cuencas?.remove()`, `referencia?.remove()`)
   - **What happens & why it is a bug**: `pintarCuencas()` passes a new `L.canvas({padding:.3})` on every load (and `mostrarSinapred()` passes a new `L.canvas()`). Leaflet adds that `L.Canvas` renderer directly to `mapa`, appending a `<canvas>` to `.leaflet-overlay-pane` and registering `moveend`/`zoom`/`viewreset` listeners on `mapa`. Calling `cuencas?.remove()` or `referencia?.remove()` removes the `L.GeoJSON` layer and its paths, **not** the `L.Canvas` renderer layer, leaking canvases and listeners on every region/level switch, SINAPRED load, or hide action.
   - **Verification/Repro evidence**: Verified in headless Edge against `index.html`:
     - After initial `nic` load: `2` `L.Canvas` layers, `2` `<canvas>` elements, `10` `moveend` listeners, `5` `zoom` listeners.
     - After 5 additional region switches (`af`, `na`, `sa`, `eu`, `nic`): `7` `L.Canvas` layers, `7` `<canvas>` elements, `15` `moveend` listeners, `10` `zoom` listeners.
     - After clicking `#hid-ocultar` ("Hide watersheds"): still `7` `L.Canvas` layers, `7` `<canvas>` elements, `15` `moveend` listeners, `10` `zoom` listeners.

2. **[Medium] Unbounded `cache` retains every decompressed `.geojson.gz` `FeatureCollection` in memory**
   - **Location**: `app/hidrologia.js:22, 34` (`cache`, `datos`), `app/hidrologia.js:60, 64` (`cargarCuencas`)
   - **What happens & why it is a bug**: `datos(url)` inserts every fetched/decompressed `FeatureCollection` into `const cache = new Map()` and never evicts resolved entries. As noted in `app/hidrologia.js:60`, the 9 level-6 HydroBASINS datasets contain 16,397 polygons (~1.5 GB browser memory; 127.4 MB raw JSON across the 9 level-6 `.geojson.gz` files, 135.45 MB across all 19 `.gz` files). Switching across several level-6 regions pins all parsed GeoJSON objects permanently in `cache`.
   - **Verification/Repro evidence**: Inspected `app/hidrologia.js:22, 34` and measured uncompressed sizes of `data/hidrologia/*.gz` (`135.45 MB` total raw JSON).

3. **[Medium] Auto-refresh `setInterval` forces 2D map view and resets viewport every 5 minutes**
   - **Location**: `app/hidrologia.js:152` (`setInterval`), `app/hidrologia.js:92, 94` (`cargarEstaciones`)
   - **What happens & why it is a bug**: When `#hid-auto` is checked, `setInterval` calls `cargarEstaciones(true)` every 300s. `cargarEstaciones()` unconditionally calls `await window.SICC_vista.cambiar('mapa')` and `mapa.fitBounds(puntos.getBounds(), {maxZoom:8, padding:[20,20]})`, even when `window.SICC_CONFIG.hidrologia_api` is `null` (static deploy), even if the user switched back to the 3D Globe, and even if the user was zoomed into a specific watershed.

4. **[Medium] Unhandled `TypeError` when any GeoJSON feature has `properties: null`**
   - **Location**: `src/hidrologia-datos.js:4` (`codigo`), `5-9` (`filasCSV`), `10-15` (`fecha`), `16-22` (`antiguedad`), `23` (`buscar`); `app/hidrologia.js:37-38, 46` (`atributos`, `detalle`, `buscar`)
   - **What happens & why it is a bug**: RFC 7946 §3.2 allows `feature.properties` to be `null`. None of these helpers guard against `null` `properties`, crashing CSV export, search, tooltip/popup building, and timestamp inspection if an upstream WFS/ArcGIS layer emits a feature with `"properties": null`.
   - **Verification/Repro evidence**: Reproduced in Node: `codigo(null)`, `filasCSV([{properties:null}])`, `fecha(null)`, `antiguedad(null)`, and `buscar([{properties:null}], "a")` all threw `TypeError`.

5. **[Low] `opciones()` is not invoked on startup, leaving invalid detail levels (`4`, `6`) enabled for Nicaragua**
   - **Location**: `app/hidrologia.js:75, 139` (`opciones`), `index.html:127-128` (`#hid-region`, `#hid-nivel`)
   - **What happens & why it is a bug**: `opciones()` is only registered on `$('hid-region').onchange`, so on initial page load `#hid-region` is `'nic'` while `<option value="4">` and `<option value="6">` in `#hid-nivel` remain enabled (`disabled: false`), even though `cargarCuencas()` ignores `#hid-nivel` for `nic`.
   - **Verification/Repro evidence**: Observed in headless Edge: `Initial #hid-nivel options: [{'v': '4', 'd': False, 's': False}, {'v': '6', 'd': False, 's': False}, {'v': '7', 'd': False, 's': True}]`.

6. **[Low] Watershed search results and `#hid-detalle` remain active/stale after hiding or switching regions**
   - **Location**: `app/hidrologia.js:45-48` (`buscar`), `38-44` (`detalle`), `58` (`pintarCuencas`), `140` (`#hid-ocultar`)
   - **What happens & why it is a bug**: `#hid-ocultar` removes `cuencas` and sets `visible = false` without clearing `fc`, `#hid-resultados`, or `#hid-detalle`. Clicking a result in `#hid-resultados` while hidden still executes `mapa.fitBounds(encontrado.getBounds(), ...)` and styles a detached layer. Switching regions refreshes `#hid-resultados` but leaves the prior region's `#hid-detalle` visible.
   - **Verification/Repro evidence**: Observed in headless Edge after clicking `#hid-ocultar`: searching `9519581` returned `1` result and clicking it populated `#hid-detalle` and zoomed the map to the hidden layer.

7. **[Low] `pintarCuencas()` reads `$('hid-region').value` from the DOM instead of the captured region `r`**
   - **Location**: `app/hidrologia.js:55` (`pintarCuencas`), `app/hidrologia.js:61-67` (`cargarCuencas`)
   - **What happens & why it is a bug**: `cargarCuencas()` awaits network fetch and `SICC_vista.cambiar('mapa')`, then calls `pintarCuencas()`, which reads `$('hid-region').value` live from the DOM for the attribution string. Changing `#hid-region` mid-load assigns the wrong attribution to the loaded `fc`.

8. **[Low] Minor edge cases in `fechaResumen()`, `filasCSV()`, and `json()` `.gz` check**
   - **Location**: `app/hidrologia.js:76` (`fechaResumen`), `app/hidrologia.js:27-31` (`json`), `src/hidrologia-datos.js:7` (`filasCSV`)
   - **What happens & why it is a bug**:
     - `fechaResumen()` counts `'Older than 48 hours'` and `'unknown'`, omitting `'Future timestamp: check source'` from the `#hid-estaciones-estado` summary even though `data/hidrologia/ineter_nivel_rio.geojson` contains 2 stations with future timestamps (`Embalse Las Canoas` `'2028-05-24T08:00:00Z'`, `Sisin` `'2027-10-26T08:00:00Z'`; marker popups do still show the warning).
     - `json()` checks `typeof DecompressionStream === 'undefined'` before checking gzip magic bytes (`b[0] !== 31 || b[1] !== 139`), which would fail unnecessarily if a CDN already decompressed `.gz` via `Content-Encoding: gzip` on a browser without `DecompressionStream`.
     - `filasCSV()` escapes `^[=+@\-\t\r]` on strings, omitting leading `\n`.

---

### Checked & Clean Areas
- **Pfafstetter code preservation & search**: `codigo()` and `buscar()` preserve leading zeros (`'0012'`), handle 3/6/7-digit Nicaragua codes and 4/6/10-digit HydroBASINS IDs accurately; note `buscar()` intentionally searches `codigo_completo`, `cuencas`, and `HYBAS_ID` (does not search `codigo_componentes` on the 44 discrepant features).
- **CSV formula injection & quoting**: `filasCSV()` prefixes `=`, `+`, `@`, `-`, `\t`, `\r` on string cells and header keys with `'`, doubles internal `"`, and keeps numeric negatives (`-2`) unprefixed.
- **Station timestamps & timezones**: `fecha()` and `antiguedad()` handle ISO UTC (`Z`), explicit numeric offsets (`[+-]HH:MM`), invalid dates (`Number.isFinite(ms)`), future timestamps, and timezone-less `fechaformato`/`horaformato` strings without misinterpreting local time as UTC.
- **INETER WFS static fallback**: When `window.SICC_CONFIG.hidrologia_api` is `null` (static Render deploy), clicking `#hid-actualizar` cleanly loads `data/hidrologia/ineter_<id>.geojson` and displays `'Live gateway not configured; dated snapshot · retrieved ...'`.
- **XSS**: All station/watershed/SINAPRED DOM rendering (`el`, `texto`, `atributos`, `detalle`, `buscar`, `rotular` via `L.divIcon` with `HTMLElement`, `bindTooltip`, `bindPopup`) uses `textContent` and DOM element creation; no `innerHTML` sinks found.

---

### Files Inspected & Checks Run
- **Files inspected**: `app/hidrologia.js`, `src/hidrologia-datos.js`, `app/config.js`, `app/shell.js`, `app/globo.js`, `app/fenomenos.js`, `app/estilos.css`, `index.html`, `backend/clima_nic/hidrologia.py`, `backend/clima_nic/api.py`, `scripts/datos/descargar_hidrologia.py`, `scripts/preparar_render.mjs`, `scripts/preparar_render.sh`, `scripts/servir-local.mjs`, `tests/test_hidrologia.py`, `tests/test_e2e_navegador.py`, `tests/e2e/hidrologia_navegador.py`, `data/hidrologia/fuentes_y_limites.md`, `data/hidrologia/*.json`, `data/hidrologia/*.geojson`, `data/hidrologia/*.geojson.gz`.
- **Checks run**:
  - `node --check app/hidrologia.js` -> exit `0`
  - `node --check src/hidrologia-datos.js` -> exit `0`
  - `python -m pytest tests/test_hidrologia.py -q` -> `18 passed, 1 warning in 92.86s`
  - Custom Node edge-case tests on `src/hidrologia-datos.js` -> verified `codigo`, `filasCSV`, `fecha`, `antiguedad`, `buscar`, and `null`-properties `TypeError`s.
  - Headless Microsoft Edge Playwright probes against read-only local HTTP server (`index.html`) -> verified initial `#hid-nivel` option states, `L.Canvas`/`<canvas>`/listener leaks across loads & hide, hidden search/detail behavior, all 4 station layers, static fallback on `#hid-actualizar`, and 150 rendered `<span>` labels.
