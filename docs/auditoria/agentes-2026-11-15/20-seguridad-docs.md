# Agente 20: Seguridad y Exactitud Documental

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

## Security, Supply-Chain, and Documentation Audit Report (`wt_audit20`, commit `20bec48`)

Read-only audit completed with zero modifications to `wt_audit20` or `C:\NASA-CHALLENGE` (`git status --short` is clean).

---

### Confirmed Findings

#### 1. [Medium] Browser E2E test suite errors on all 7 tests due to unguarded polling fallback
- **File:Line (Symbol):** `tests/test_e2e_navegador.py:81-113` (`RecorridoEnNavegador.setUpClass`), `tests/e2e/sonda.js:23-27,130-143` (`esperarTodo`, `correr`)
- **What happens & why it is a bug:** `tests/e2e/sonda.js:138` exits `esperarTodo()` and unconditionally invokes `correr()` once `++intentos > 50` (~10.5s after inline `<script>` parsing) even when `tendOk && indOk && enosOk && invOk` are still false (e.g., while headless Edge is downloading external CDN `<script defer>` tags in `index.html:11,258,259,278` before `src/tendencias.js` populates `#botones-region`). `correr()` then calls `b.click()` at `tests/e2e/sonda.js:27` while `b = document.querySelector('#botones-region button[data-region="' + id + '"]')` is `null`, aborting `setUpClass` and failing all 7 tests in `RecorridoEnNavegador`.
- **Verification/Repro evidence:**
  - `python -B -m pytest -q`: `303 passed, 3 warnings, 7 errors, 40 subtests passed in 409.25s (0:06:49)`
  - `python -B -m pytest tests/test_e2e_navegador.py -v`: `7 errors in 82.59s (0:01:22)` — all 7 fail at `tests/test_e2e_navegador.py:112` with `AssertionError: Error en sonda JS: ERROR TypeError: Cannot read properties of null (reading 'click') at http://127.0.0.1:<port>/__e2e.html:312:9`.

#### 2. [Medium] Unvalidated remote URL scheme assigned to `a.href` in cyclone list
- **File:Line (Symbol):** `app/fenomenos.js:98-119` (`cargarTormentas`, line `111`)
- **What happens & why it is a bug:** `app/fenomenos.js:101,111` assigns `a.href = t.aviso_url` directly from `/api/tormentas` (`public/clima-base/tormentas.json`, fetched from `https://sicc952.onrender.com/api/tormentas` by `scripts/preparar_meteo.mjs:4,60`) without checking `/^https?:/` (unlike `app/investigar.js:272`, which checks `if(/^https?:/.test(u)&&!u.includes('{'))`). If the upstream feed is compromised or returns a `javascript:` / `data:` URI, clicking "NHC advisory" executes script in the app origin.
- **Verification/Repro evidence:** Direct inspection of `app/fenomenos.js:101,111` vs `app/investigar.js:272`.

#### 3. [Medium] `Three.js` ESM imported from CDN without Subresource Integrity (SRI)
- **File:Line (Symbol):** `app/espacio.js:4`, `app/teselas-globo.js:1` (compare `index.html:11,258,259,278`)
- **What happens & why it is a bug:** While `index.html` pins SRI hashes (`integrity="sha384-..." crossorigin="anonymous"`) for Leaflet 1.9.4, Chart.js 4.4.1, and proj4js 2.9.2, `app/espacio.js:4` and `app/teselas-globo.js:1` load `https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.min.js` via ES module `import` with no `<script type="importmap">` `integrity` verification or local vendored copy.
- **Verification/Repro evidence:** Direct inspection of `app/espacio.js:4`, `app/teselas-globo.js:1`, and `index.html:11,258,259,278`.

#### 4. [Medium] Unescaped `innerHTML` tooltip interpolation and missing CSV formula-injection escaping
- **File:Line (Symbol):** `src/graficas.js:38-46,153,223-224` (`mostrarTip`, `dibujarSerie`, `dibujarComparacion`); CSV builders `src/tendencias.js:131-138` (`csvPendientes`), `app/shell.js:90-96` (`csvPunto`), `app/investigar.js:282-283`, `app/indicadores.js:203-204`
- **What happens & why it is a bug:**
  - `src/graficas.js:40` sets `t.innerHTML = html` where `dibujarComparacion` (`line 223`) interpolates `r.nombre` and `dibujarSerie` (`line 153`) interpolates `meta.unidades` without calling `escapar()` (`lines 234-236`), even though `src/tendencias.js:38,77,80` uses `G.escapar(...)`. (Currently populated from `NOMBRES` / static `data/clima.json`.)
  - `src/tendencias.js:134-135`, `app/shell.js:93-94`, `app/investigar.js:283`, and `app/indicadores.js:204` construct CSV cells without neutralizing leading `=`, `+`, `-`, `@`, `\t`, `\r` formula prefixes or doubling quotes (`src/tendencias.js:134` wraps `r.nombre` in `"` without escaping internal quotes; `app/shell.js:94` includes remote Open-Meteo `cols` and `pronostico.fuente`; `app/investigar.js:283` and `app/indicadores.js:204` include `x.fuente.producto`/`v.fuente`).
- **Verification/Repro evidence:** Direct inspection of the listed lines in `src/graficas.js`, `src/tendencias.js`, `app/shell.js`, `app/investigar.js`, and `app/indicadores.js`.

#### 5. [Medium] Documented URL hashes, `?region=caja_original` query parameter, and `#proyecciones` tab ID do not match the app
- **File:Line (Symbol):** `README.md:42-53`, `docs/reproduccion.md:14,16-19`, `docs/guion.md:6,30-32`, `docs/prueba-persona-ajena.md:6` vs `app/shell.js:22-23,203,212-213` (`salidaHash`, `hashchange`), `index.html:38,178`, `src/tendencias.js:11`
- **What happens & why it is a bug:**
  - `README.md:44-53` documents deep-link URL hashes for 10 views (`#globe`, `#map`, `#investigar`, `#aprender`, `#fuentes`, `#tendencias`, `#indicadores`, `#fenomenos`, `#proyecciones`, `#hidrologia`, `#exportar`). In `app/shell.js:203,212-213`, only `#map` is handled; any other hash switches the 3D/2D view to `'globo'` and never invokes `tab()`.
  - `docs/reproduccion.md:14`, `docs/guion.md:6`, and `docs/prueba-persona-ajena.md:6` instruct opening `http://localhost:8000/?region=caja_original#tendencias`. Searching all `app/*.js` and `src/*.js` confirms `location.search` and `region=` are never parsed (`src/tendencias.js:11` hardcodes `sel: 'nicaragua'`).
  - `README.md:51`, `docs/reproduccion.md:19`, and `docs/guion.md:32` cite `#proyecciones`, whereas the actual tab/section ID in `index.html:38,178` is `escenarios` (`data-tab="escenarios"`, `<section id="escenarios">`).
- **Verification/Repro evidence:** Direct inspection of `app/shell.js:22-23,203,212-213`, `index.html:38,178`, `src/tendencias.js:11`, the cited docs, and search over `app/` and `src/`.

#### 6. [Medium] Non-existent script `scripts/servidor.mjs`, wrong port, and obsolete branch names in reproduction docs
- **File:Line (Symbol):** `docs/reproduccion.md:6,13-14`, `docs/guion.md:6`, `docs/prueba-persona-ajena.md:6` vs `scripts/servir-local.mjs:27`
- **What happens & why it is a bug:** `docs/reproduccion.md:13` and `docs/guion.md:6` instruct running `node scripts/servidor.mjs` and visiting `http://localhost:8000/`. `scripts/servidor.mjs` does not exist; the actual script is `scripts/servir-local.mjs`, which serves on `http://127.0.0.1:8996/`. `docs/reproduccion.md:6` also tells users to check out `codex/verificacion-v2` or `codex/demo-render`.
- **Verification/Repro evidence:** Direct inspection of `docs/reproduccion.md:6,13-14`, `docs/guion.md:6`, `docs/prueba-persona-ajena.md:6`, and `scripts/servir-local.mjs:27`.

#### 7. [Medium] Stale/contradictory IMERG Theil–Sen and Mann–Kendall statistics in docs vs `data/clima.json`
- **File:Line (Symbol):** `docs/reproduccion.md:47-50,52`, `docs/auditoria.md:33-38`, `docs/estado-verificacion.md:11` vs `data/clima.json` (`dominios[*].tendencia.controles`)
- **What happens & why it is a bug:** On `20bec48`, `data/clima.json` reports:
  - `caja_sicc`: Theil–Sen `-28.705` (`[-184.428, 188.865]`), MK `p = 0.7873`, HAC `[-119.373, 93.11]`
  - `NIC`: Theil–Sen `-64.923` (`[-233.24, 98.283]`), MK `p = 0.4461`, HAC `[-144.58, 19.916]`
  - `HND`: Theil–Sen `-41.197` (`[-191.751, 122.339]`), MK `p = 0.6062`, HAC `[-142.091, 72.081]`
  - `CRI`: Theil–Sen `-168.386` (`[-369.492, 20.815]`), MK `p = 0.0968`, HAC `[-332.359, -70.089]`
  - `docs/reproduccion.md:47-50,52` prints outdated Theil–Sen (`-7,9`, `-70,5`, `-51,3`, `-181,4`) and MK `p` (`0,8622`, `0,3586`, `0,5350`, `0,0970`).
  - `docs/auditoria.md:35-36,38` prints outdated `HND` Theil–Sen (`-26,574`) and `CRI` Theil–Sen (`-210,275`, MK `p = 0,0972`), and `docs/estado-verificacion.md:11` also cites `p = 0,0972`.
- **Verification/Repro evidence:** Verified by inspecting `data/clima.json` in Python and reading the three markdown files.

#### 8. [Low] Minor numerical drift in delivery docs and stale status/count notes in supporting docs
- **File:Line (Symbol):**
  - `docs/entrega/PROJECT_DESCRIPTION.md:103-104` & `docs/entrega/AI_USE.md:50` vs `data/recursos_integrados.json`
  - `backend/README.md:39`, `docs/auditoria.md:92,110`, `docs/reto/CUMPLIMIENTO.md:44`, `docs/criterios.md:9`, `docs/reproduccion.md:18`
- **What happens & why it is a bug:**
  - `PROJECT_DESCRIPTION.md:103` cites `+0.833 °C/decade` and `AI_USE.md:50` cites `+0.8333 °C/decade` for Deadhorse permafrost, whereas `data/recursos_integrados.json` (`canada_alaska_permafrost_magt_deadhorse`) has `sen.por_decada = 0.8342` (`+0.834`). `PROJECT_DESCRIPTION.md:104` cites `-3.19 days/decade` and `AI_USE.md:50` cites `-3.1915 days/decade` for Lake Superior ice at Bayfield, whereas `data/recursos_integrados.json` (`norteamerica_hielo_lagos_bayfield`) has `sen.por_decada = -3.1944` (`-3.194`).
  - Stale notes: `backend/README.md:39` (`fuentes/lagos.py`: `sin datos todavía`), `docs/auditoria.md:92` (`Sin datos todavía: Giovanni, AppEEARS, GLDAS, KNMI, RCM y SAR`), and `docs/reto/CUMPLIMIENTO.md:44` (`Cumplido para 6 de 13`) are outdated since `13/13` challenge resources are now `en_uso` in `data/recursos_integrados.json`. Test counts in `docs/criterios.md:9` (`50 pruebas`) and `docs/auditoria.md:110` (`88 pruebas`) are outdated vs the 310 tests collected by `pytest`. `docs/reproduccion.md:18` describes `#fenomenos` as `historial de ciclones HURDAT2/IBTrACS`, whereas `app/fenomenos.js:98-119` displays live NHC cyclones (`/api/tormentas`) and IBTrACS is in `Investigate`.
- **Verification/Repro evidence:** Direct comparison against `data/recursos_integrados.json`, `app/fenomenos.js:98-119`, and `pytest` output.

#### 9. [Low] Dependency & plaintext HTTP notes (`requirements.txt`, `Geo.ca`)
- **File:Line (Symbol):** `backend/requirements.txt:1-14` vs `backend/clima_nic/hidrologia.py:11`; `backend/clima_nic/recursos.py:173` & `README.md:107,146`
- **What happens & why it is a bug:** `backend/requirements.txt` uses unpinned `>=` ranges and puts `requests>=2.31` under `# Opcionales` (`line 8`), even though `backend/clima_nic/hidrologia.py:11` imports `requests` unconditionally at top level (meanwhile `scripts/sar/requirements.txt` uses exact pins matching the local environment). Additionally, `backend/clima_nic/recursos.py:173` and `README.md:107,146` use plaintext `http://geo.ca/` for the Geo.ca link.
- **Verification/Repro evidence:** Direct inspection of `backend/requirements.txt`, `backend/clima_nic/hidrologia.py:11`, `scripts/sar/requirements.txt`, `README.md:107,146`, and code scan output.

---

### Clean Areas Verified (No Defects Found)
- **README counts (`README.md:20,30-36,54`):** Exactly match `data/recursos_integrados.json` (`217` investigations: `79` `tendencia_detectada`, `85` `evidencia_insuficiente`, `48` `metodos_discrepan`, `5` `demostracion_registro_corto`; `89` places; `8` categories; `33` cross-checks; `3` tours; `13/13` `en_uso` resources) and `data/ayuda_preguntas.json` (`100` FAQs). `docs/reto/CUMPLIMIENTO.md:9` (`40 variables`) matches `len(productos.VARIABLES) == 40`.
- **Static server path traversal (`scripts/servir-local.mjs:16-18`):** Guards resolved path against `public/` root (`relative.startsWith('..') || path.isAbsolute(relative)` -> HTTP `403`).
- **Backend API & SSRF (`backend/clima_nic/api.py`, `hidrologia.py`):** INETER WFS proxy restricts `capa` to the fixed `OBSERVACIONES` allowlist (`404` otherwise); `CORSMiddleware` is explicitly read-only (`allow_methods=["GET"]`, default `allow_credentials=False`, intentional per `api.py:1`).
- **Dangerous sinks & leaks:** Repo-wide scan across `backend/`, `scripts/`, `data/recursos/`, `app/`, `src/`, `tests/` found zero `pickle.load`, `yaml.load`, `shell=True`, `verify=False`, or leaked credentials.

---

### Files Inspected (in this session)
`README.md`, `index.html`, `backend/README.md`, `backend/requirements.txt`, `backend/clima_nic/__main__.py`, `backend/clima_nic/actualizar.py`, `backend/clima_nic/api.py`, `backend/clima_nic/hidrologia.py`, `backend/clima_nic/productos.py`, `backend/clima_nic/fuentes/power.py`, `backend/clima_nic/fuentes/gistemp.py`, `app/espacio.js`, `app/teselas-globo.js`, `app/shell.js`, `app/fenomenos.js`, `app/investigar.js`, `app/indicadores.js`, `src/fuentes-meteo.js`, `src/contrato.js`, `src/graficas.js`, `src/tendencias.js`, `scripts/servir-local.mjs`, `scripts/preparar_render.mjs`, `scripts/preparar_meteo.mjs`, `scripts/datos/verificar_clima.py`, `scripts/datos/requirements.txt`, `scripts/datos/requirements-extraccion.txt`, `scripts/datos/requirements-hidrologia.txt`, `scripts/sar/requirements.txt`, `docs/reproduccion.md`, `docs/guion.md`, `docs/auditoria.md`, `docs/estado-verificacion.md`, `docs/criterios.md`, `docs/checklist-entrega.md`, `docs/prueba-persona-ajena.md`, `docs/reto/CUMPLIMIENTO.md`, `docs/entrega/PROJECT_DESCRIPTION.md`, `docs/entrega/AI_USE.md`, `docs/entrega/GUION_DEMO.md`, `tests/test_e2e_navegador.py`, `tests/e2e/sonda.js`.

### Checks Run (exact observed results)
- `node --check` (all `.js`/`.mjs`/`.cjs` in `app/`, `src/`, `scripts/`, `tests/`): **34 files checked, 0 failures**.
- `py_compile` (all `.py` in `backend/`, `scripts/`, `tests/`, `data/recursos/`): **87 files checked, 0 failures**.
- `python -B scripts/datos/verificar_clima.py`: **88 de 88 comprobaciones correctas** (exit code `0`).
- `python -B -m pytest -q`: **303 passed, 3 warnings, 7 errors, 40 subtests passed in 409.25s** (exit code `1`; all 7 errors in `tests/test_e2e_navegador.py::RecorridoEnNavegador`).
- `python -B -m pytest tests/test_e2e_navegador.py -v`: **7 errors in 82.59s** (exit code `1`).
- `git status --short`: **clean (no output, exit code `0`)**.
