# Agente 18: Suite de Pruebas y Cobertura

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

## Audit Report: `tests/` Suite (`wt_audit20`, commit `20bec48`)

### Checks Run
- `python -m pytest -q`: **310 passed, 3 warnings, 274 subtests passed in 230.71s (0:03:50)** (0 skipped in this environment; all optional deps and data files were present).
- `node --test tests/teselas-geometria.test.mjs`: **3 passed, 0 failed** (duration ~1.92s).
- `node tests/globo-detalle.cjs`: **Failed (exit code 1)** — `Error: Cannot find module 'playwright'`.
- `node tests/interfaz_normalizada.cjs`: **Exited 0**, printed normalized JSON to stdout (helper script with no assertions; consumed by `tests/test_interfaz.py`).
- `python -m py_compile tests/e2e/hidrologia_navegador.py` & `python tests/e2e/hidrologia_navegador.py --help`: **Exited 0**.
- `node --check` on 18 JS modules (`app/*.js`, `app/teselas-geometria.mjs`, `src/*.js`): **Exited 0**.

---

### Confirmed Findings

1. **[High] `tests/globo-detalle.cjs` fails out of the box and has fragile environment/network assumptions**
   - `tests/globo-detalle.cjs:2,7,18,45,60-64`
   - **What happens & why**:
     - Line 2 calls `require('playwright')`, but the repository has no `package.json` or `node_modules`, causing immediate failure (`Error: Cannot find module 'playwright'`) unless `NODE_PATH` is manually supplied.
     - Line 7 serves `../public`, which does not exist in a clean checkout until `node scripts/preparar_render.mjs` is executed; running `globo-detalle.cjs` standalone serves 404s and times out after 45s waiting for `window.Espacio`.
     - Line 18 hardcodes `chromium.launch({channel:'chrome', ...})`, failing in headless environments with only Playwright Chromium or Edge.
     - Lines 45 and 60–64 require live internet access to ArcGIS `World_Imagery/MapServer/tile/` (`tiles.some(t => /\/tile\/1[4-7]\//.test(t.url) && t.status === 200)`), and lines 8–9, 77 write artifacts to `reports/globo-detalle/` inside the workspace without cleanup.
   - **Verification**: Executed `node tests/globo-detalle.cjs` -> exit code 1 (`Error: Cannot find module 'playwright'`).

2. **[Medium] `tests/test_e2e_navegador.py` uses Windows-only `taskkill`, leaves `public/` behind, and ignores uncaught JS errors**
   - `tests/test_e2e_navegador.py:82-83,105,114-117` (`RecorridoEnNavegador.setUpClass`), `tests/e2e/sonda.js:13-14,65,105,107,130-143`
   - **What happens & why**:
     - Line 116 runs `subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)` unconditionally when `proc.poll() is None`. Because headless Chrome stays running, on Linux/macOS this raises `FileNotFoundError` in `finally` and breaks the test.
     - Line 82 executes `node scripts/preparar_render.mjs`, generating `public/` in the repo root, and `finally`/`tearDownClass` only unlink `__e2e.html` (line 117), leaving the generated `public/` directory in the workspace. (Confirmed: `public/` was absent initially and present after `pytest` ran.)
     - Line 105 discards browser `stdout`/`stderr` (`DEVNULL`) and `tests/e2e/sonda.js` attaches no `window.onerror` or `unhandledrejection` listener, so uncaught exceptions in unrelated loaded modules (`espacio.js`, `buscador.js`, `coordenadas.js`, `ayuda.js`, `hidrologia.js`, etc.) pass silently.
     - `sonda.js` bypasses real UI clicks by dispatching `CustomEvent('sicc:pestana', ...)` (lines 13–14, 135), calling `window.SICC_investigar.elegir(...)` (line 105), and invoking `.onclick()` directly (lines 65, 107).

3. **[Medium] `tests/test_lugares_coordenadas.py` never executes `app/coordenadas.js` or `app/buscador.js` (masking an unwrapped-longitude UTM zone bug)**
   - `tests/test_lugares_coordenadas.py:48-57,94-117` (`TestCoordenadasYReferencia`), `app/coordenadas.js:23-34` (`zonaUtm`)
   - **What happens & why**:
     - `test_referencia_utm_y_mgrs_tres_puntos` only exercises Python's `pyproj.Transformer` and a test-local Python helper `_mgrs_referencia_utm()`, while `test_archivos_integrados_en_index_y_sintaxis_js` only checks `<script>` tags in `index.html` and runs `node --check` (silently skipped if `NODE is None` at line 115). Neither `app/coordenadas.js` nor `app/buscador.js` is ever executed.
     - In `app/coordenadas.js:26`, `zonaUtm(lat, lon)` computes `z` using `wrapLon(lon)` on line 24, but checks raw `lon` for the Norway/Svalbard exceptions on lines 26–32.
   - **Verification**: Running `app/coordenadas.js` in Node VM (`node -e`) produced `zonaUtm(60, 4.0) -> 32` vs `zonaUtm(60, 364.0) -> 31`.

4. **[Medium] `tests/test_interfaz.py` only tests the precomputed-JSON path, leaving `src/estadistica.js` completely untested**
   - `tests/test_interfaz.py:19,46` (`InterfazCoincideConLosDatos`), `tests/interfaz_normalizada.cjs:16,24`, `src/contrato.js:91-109` (`normalizar`)
   - **What happens & why**: `interfaz_normalizada.cjs` calls `C.desdeClima(clima, mapa)` which attaches precomputed `tendencias` to every region, so `normalizar()` always takes the `"provided in the JSON"` branch (`test_interfaz.py:46`). The browser-computed fallback in `src/contrato.js` and all functions in `src/estadistica.js` (`mco`, `sen`, `veredicto`, `analizar`, `pearson`, `cuantilT`, `pBilateralT`) have zero unit tests.

5. **[Medium] `tests/e2e/hidrologia_navegador.py` leaks its temp directory on failure and omits `encoding='utf-8'` on `read_text()`**
   - `tests/e2e/hidrologia_navegador.py:16,19,39,42,67-76,85`
   - **What happens & why**: `temporal.cleanup()` (line 85) is outside any `try...finally`, so any failed assertion (e.g. `assert not errores` at line 83) leaks the temp directory. Lines 19, 39, and 42 call `Path.read_text()` without `encoding='utf-8'`, relying on Windows locale encoding (`cp1252`). It is also excluded from `pytest` discovery and requires a separate HTTP server plus live internet access to INETER WMS and SINAPRED ArcGIS REST.

6. **[Low] `tests/test_backend_clima_nic.py` module-level `importorskip("shapely")` skips unrelated tests**
   - `tests/test_backend_clima_nic.py:26`
   - **What happens & why**: `shapely = pytest.importorskip("shapely")` at top-level skips all 24 tests in the file if `shapely` is absent, even pure-NumPy/stdlib tests (`test_benjamini_hochberg`, `test_ventana_predictor`, `test_serie_predictor_y_pronostico`, `test_escenarios_delta`, `test_penman_monteith_ejemplo_fao56`, `test_estadistica_casos_borde`, etc.) that do not require `shapely`.

7. **[Low] Inconsistent Node availability handling in `tests/test_hidrologia.py`**
   - `tests/test_hidrologia.py:180` (`test_utilidades_js_codigos_fechas_y_csv`)
   - **What happens & why**: Calls `subprocess.run(['node', '-e', ...])` directly without skipping if `node` is missing from `PATH`, unlike `test_interfaz.py:15`, `test_recursos_interfaz.py:217`, and `test_e2e_navegador.py:77` (and unlike `test_lugares_coordenadas.py:115`, which silently skips the check).

---

### Critical Untested Paths Observed
- **Frontend JS with no functional/runtime tests**: `src/estadistica.js`, `src/fuentes-meteo.js` (API/Open-Meteo & CSV ONI fallback), `src/globo-meteo.js`, `src/meteo-paletas.js`, `app/buscador.js`, `app/coordenadas.js`, `app/ayuda.js` (only regex-checked on `ayuda_preguntas.json` in `test_ayuda.py`), `app/tutorial.js` (only substring-checked in `test_ayuda.py`), `app/campo.js`, `app/globo.js`, `app/graficas-meteo.js`, `app/soporte-meteo.js`, `app/reticula.js`, `app/inicio.js`, `app/teselas-globo.js` (only covered by the broken `globo-detalle.cjs`), and `app/hidrologia.js` (only covered by the manual `tests/e2e/hidrologia_navegador.py`).
- **E2E gaps in `tests/test_e2e_navegador.py`**: `#meteorologia`, `#hidrologia`, and `#ayuda` tabs are never exercised.
- **Backend Python with no tests**: `backend/clima_nic/actualizar.py` (`registrar`, `actualizar`), `backend/clima_nic/__main__.py` (CLI dispatch), `backend/clima_nic/productos.py`, and FastAPI endpoints `/fuentes`, `/regiones`, `/variables`, `/escenarios`, `/consulta` plus `503` missing-data handling in `backend/clima_nic/api.py` (`test_consulta_y_api` in `test_backend_clima_nic.py:288-317` only hits `/salud`, `/tendencia`, `/pronostico`, `/mapa`).

---

### Files Inspected
- All files in `tests/`: `globo-detalle.cjs`, `interfaz_normalizada.cjs`, `teselas-geometria.test.mjs`, `test_ayuda.py`, `test_backend_clima_nic.py`, `test_datos.py`, `test_e2e_navegador.py`, `test_gldas_mensual.py`, `test_hidrologia.py`, `test_indicadores_nicaragua.py`, `test_interfaz.py`, `test_lugares_coordenadas.py`, `test_rcm_procesar.py`, `test_recursos_americas.py`, `test_recursos_asia_oceania.py`, `test_recursos_contraste.py`, `test_recursos_csa.py`, `test_recursos_europa_africa.py`, `test_recursos_interfaz.py`, `test_recursos_tierra.py`, `e2e/hidrologia_navegador.py`, `e2e/sonda.js`, `.gitignore`.
- Related source/config files cross-checked: `app/espacio.js`, `app/shell.js`, `app/coordenadas.js`, `app/buscador.js`, `app/indicadores.js`, `app/ayuda.js`, `app/hidrologia.js`, `app/config.js`, `src/contrato.js`, `src/estadistica.js`, `src/fuentes-meteo.js`, `backend/clima_nic/api.py`, `backend/clima_nic/actualizar.py`, `backend/clima_nic/__main__.py`, `scripts/preparar_render.mjs`, `.github/workflows/actualizar-pronostico.yml`, `.gitignore`.

*(Clean/well-structured components observed: `tests/teselas-geometria.test.mjs`, `tests/test_datos.py`, `tests/test_indicadores_nicaragua.py`, `tests/test_gldas_mensual.py`, `tests/test_rcm_procesar.py`, `tests/test_recursos_americas.py`, `tests/test_recursos_asia_oceania.py`, `tests/test_recursos_contraste.py`, `tests/test_recursos_csa.py`, `tests/test_recursos_europa_africa.py`, `tests/test_recursos_interfaz.py`, and `tests/test_recursos_tierra.py` ran cleanly and pass without defects in the executed paths.)*
