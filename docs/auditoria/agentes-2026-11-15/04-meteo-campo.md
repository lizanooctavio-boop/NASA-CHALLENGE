# Agente 04: Meteo en Vivo y Campo

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

## Audit Report: Live Meteo Fetching, Field Rendering, Caching, Charts, and Palettes

**Target checkout:** `.` (read-only audit, no files modified).

### Files Inspected
- `app/campo.js` (291 lines)
- `app/graficas-meteo.js` (97 lines)
- `app/soporte-meteo.js` (12 lines)
- `src/fuentes-meteo.js` (87 lines)
- `src/meteo-paletas.js` (25 lines)
- Cross-checked callers/contracts in `app/shell.js`, `app/globo.js`, `app/fenomenos.js`, `src/globo-meteo.js`, `scripts/preparar_meteo.mjs`, `index.html`.

### Checks Run
- `node --check` on all 5 files: **5/5 passed** (exit code `0`).
- Node (`node -e` via `vm`) unit & integration reproducers on `src/meteo-paletas.js`, `app/soporte-meteo.js`, `src/fuentes-meteo.js`, `app/graficas-meteo.js`, and `app/campo.js`: all confirmed findings below were directly reproduced.

---

### Confirmed Findings

#### 1. [High] Stale in-flight `pidiendo` lock leaves global weather field blank after a model run update
- **Location:** `app/campo.js:43-44` (`pedirGlobal`), `app/campo.js:270,279` (`cargarGlobal`)
- **What happens & why it is a bug:**
  `cacheG` and `pidiendo` are keyed only by `varGlobal(v) + '|' + paso` (without `corrida_utc`). When `cargarGlobal()` receives a new run (`GM?.corrida_utc !== d.corrida_utc`), it clears `cacheG`, updates `GM = d`, and calls `reiniciar(true)` in `finally`. If a `pedirGlobal()` fetch for the previous run was still in flight, `pidiendo[k]` remains `true`, so `pintarCampo()` / `campoPantalla()` inside `reiniciar(true)` immediately returns at `if (paso===null||cacheG[k]||pidiendo[k]) return;` without requesting the new run's tile. When the old request later resolves, `GM?.corrida_utc === corrida` is `false`, so `pedirGlobal()` discards the old data, deletes `pidiendo[k]`, and never re-fetches or calls `reiniciar(true)`. The layer stays blank for that variable/step until the user pans, zooms, or changes hours.
- **Verification/Repro evidence:**
  In Node harness (`task-68`, Repro 1), `cargarGlobal()` switched from `oldRun` to `newRun` while `/api/global?var=temperatura_c&paso=0` was pending; `oldRun` then resolved. Observed `globalCalls`:
  `['/api/global?var=temperatura_c&paso=0', '/api/global?var=viento&paso=0', '/api/global?var=viento&paso=0']`, `tempCallsCount: 1` (`temperatura_c` was never fetched for `newRun`).

#### 2. [High] Missing or empty coordinates coerce to `0, 0` instead of returning HTTP 400 in `/api/tiempo`
- **Location:** `src/fuentes-meteo.js:12-16` (`punto`)
- **What happens & why it is a bug:**
  `punto(q)` parses `const lat = Number(q.get('lat')), lon = Number(q.get('lon'))` without checking whether `q.get('lat')` / `q.get('lon')` are `null`, `""`, or whitespace. In JavaScript, `Number(null) === 0`, `Number("") === 0`, and `Number("   ") === 0`, all of which pass `!Number.isFinite(lat + lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180` and silently fetch the Open-Meteo forecast for `(0, 0)` (Null Island) instead of returning `400 { error: 'Invalid coordinates.' }`.
- **Verification/Repro evidence:**
  Node reproducer (`src/fuentes-meteo.js` with mocked `fetch`):
  - `FuentesMeteo.fetch('/api/tiempo')` -> `status: 200`, fetched `https://api.open-meteo.com/v1/forecast?latitude=0&longitude=0&...`
  - `FuentesMeteo.fetch('/api/tiempo?lat=&lon=   ')` -> `status: 200`, fetched `https://api.open-meteo.com/v1/forecast?latitude=0&longitude=0&...`

#### 3. [High] Unhandled `SyntaxError` and untimed body read in `punto()` on non-JSON 200 OK upstream response
- **Location:** `src/fuentes-meteo.js:35-38` (`punto`)
- **What happens & why it is a bug:**
  `const datos = await r.json()` is outside the `try { ... } catch (e)` block and runs after `finally { if (temporizador) clearTimeout(temporizador); }` has already cleared the 12s abort timer. If Open-Meteo or an intercepting proxy/portal returns HTTP 200 with HTML or truncated/invalid JSON, `punto()` rejects with a raw `SyntaxError` instead of returning a structured error `Response` (defeating `leerJSON()` in `app/shell.js:16,21`, which expects a `Response` and exposes the raw `SyntaxError` message in the UI error banner).
- **Verification/Repro evidence:**
  Node reproducer mocking a 200 OK HTML response from `https://api.open-meteo.com/...`:
  `FuentesMeteo.fetch('/api/tiempo?lat=12&lon=-86')` threw unhandled `SyntaxError: Unexpected token '<', "<html>502 "... is not valid JSON`.

#### 4. [High] Unhandled `TypeError` crashes and `Invalid Date` labels in `graficas-meteo.js` chart listeners
- **Location:** `app/graficas-meteo.js:45,48-50` (`sicc:enos` listener), `app/graficas-meteo.js:64-67` (`sicc:pronostico` listener)
- **What happens & why it is a bug:**
  1. In the `sicc:enos` handler (`line 45`), `d.oni_local.filter(x => x.oni !== null)` does not filter out `undefined`, `NaN`, or non-numeric strings. If `f.length > 0` while `extremos(...)` returns `null`, line 50 reads `rOni[0]` and `rOni[1]` unguarded (unlike `r34` on line 57), crashing with `TypeError`.
  2. In the `sicc:pronostico` handler (`line 67`), `h.time.map(t => new Date(t + 'Z')...)` throws `TypeError` if `p.horas` is an object missing `time` (e.g. `{}`), leaves the empty chart container visible if `h.time` is `[]`, and blindly appends `'Z'` without checking if `t` already ends with `'Z'` or an offset (unlike `SICC_soporte.utc`), producing `Invalid Date` chart x-axis labels if ISO timestamps include `'Z'`.
- **Verification/Repro evidence:**
  Node reproducers (`task-57`, `task-62`):
  - Dispatching `sicc:enos` with `{ oni_local: [{ anio: 2024, mes: 1, oni: undefined }] }` threw `TypeError: Cannot read properties of null (reading '0')`.
  - Dispatching `sicc:pronostico` with `{ lat: 12, lon: -86, horas: {} }` threw `TypeError: Cannot read properties of undefined (reading 'map')`.
  - Dispatching `sicc:pronostico` with `{ lat: 12, lon: -86, horas: { time: ['2026-11-15T12:00Z'], temperature_2m: [25], precipitation: [0], wind_gusts_10m: [5] } }` produced `chart labels with Z timestamp: [ 'Invalid Date' ]`.

#### 5. [Medium] `estatico()` draws zero wind streamlines under `prefers-reduced-motion: reduce` when global wind loads after metadata
- **Location:** `app/campo.js:85-86,96,134-135` (`nueva`, `sembrar`, `estatico`, `reiniciar`)
- **What happens & why it is a bug:**
  When `cargarGlobal()` finishes before `/api/global?var=viento` arrives, `reiniciar(true)` builds `FV` (with `ok` all zeros outside `G`) and calls `sembrar()`. Every `nueva(k)` call fails `vel(x, y)` and initializes `px[k] = -1`. When `pedirGlobal('viento', pg)` resolves, it calls `reiniciar(true)`. Because `conservar && FV && hayCampo && N` is truthy, `reiniciar(true)` skips `sembrar()`. Under normal motion, `frame()` recovers on the next frame because `px[k] < 0` calls `nueva(k)`; however, when `reducido === true` (`prefers-reduced-motion: reduce`), `estatico()` runs instead, skips all `if (x < 0) continue;`, and draws an empty `Path2D` (zero streamlines) until the user pans/zooms or changes layers/toggles.
- **Verification/Repro evidence:**
  Node reproducer (`task-68`, Repro 3) with `matchMedia` matching `(prefers-reduced-motion: reduce)` and `global_meta` + `viento` resolving asynchronously:
  `estatico() Path2D ops counts: [ 0, 0, 0, 0 ]` (zero moveTo/lineTo ops even after wind data arrived).

#### 6. [Medium] `indicador()` reports `"No model data"` (`error`) when regional grid `G` is active and `global_meta` failed
- **Location:** `app/campo.js:107-115` (`indicador`)
- **What happens & why it is a bug:**
  `indicador()` only checks `mundialDisponible()` (`GM`) and `!globalListo`. If `/api/global_meta` fails (`GM === null`, `globalListo === true`) while `/api/campo_nicaragua` succeeds (`G !== null` and live), `indicador()` enters `else { nivel = 'error'; txt = 'No model data'; }` even though regional ECMWF IFS data is loaded, rendered on the map, and shown in `Shown` inside `#indicador-detalle`.
- **Verification/Repro evidence:**
  Node reproducer (`task-68`, Repro 2) with `/api/campo_nicaragua` returning 200 OK valid regional grid and `/api/global_meta` returning 404:
  Observed `indicador-datos.dataset.nivel === "error"` and `indicador-texto.textContent === "No model data"`.

#### 7. [Medium] `PaletasMeteo.color()` mishandles `null`, `NaN`/`undefined`, and unknown variable keys
- **Location:** `src/meteo-paletas.js:20-23` (`color`)
- **What happens & why it is a bug:**
  `color(v, x, E = ESCALAS[v], normalizado = false)` does not guard `!E` or `!Number.isFinite(x)`:
  - Passing `null` on any scale without `minimo` (all 6 scales except `precipitacion_mm`) coerces `null` to `0` in `x <= T[i][0]`, silently returning the `0`-value color (e.g., `[63, 196, 218, 1]` for `0 °C`, `[110, 40, 150, 1]` for `975 hPa`) instead of `null`.
  - Passing `NaN` or `undefined` falls through all comparisons and returns `undefined` instead of `null`.
  - Passing an unknown variable name (such as `'ninguna'`) leaves `E === undefined` and throws `TypeError: Cannot read properties of undefined (reading 'tramos')`.
- **Verification/Repro evidence:**
  Node reproducer (`task-51`):
  - `color('temperatura_c', null)` -> `[ 63, 196, 218, 1 ]` (same as `color('temperatura_c', 0)`)
  - `color('temperatura_c', NaN)` -> `undefined`
  - `color('ninguna', 10)` -> threw `TypeError: Cannot read properties of undefined (reading 'tramos')`

#### 8. [Low] Empty ONI CSV value coerces to `0` (`Neutral`) in `enosLocal()` fallback
- **Location:** `src/fuentes-meteo.js:53-56` (`enosLocal`)
- **What happens & why it is a bug:**
  `const [a, m, v] = l.split(','); return { anio: Number(a), mes: Number(m), oni: Number(v) };` followed by `.filter(x => Number.isFinite(x.oni))`. An empty `v` (e.g. `2024,12,`) converts via `Number('')` to `0`, which passes `Number.isFinite(0)` and creates a spurious `0.0` (`Neutral`) ONI observation.
- **Verification/Repro evidence:**
  Node reproducer with CSV `'anio,mes,oni\n2024,11,0.5\n2024,12,\n'`:
  Observed `oni_actual: 0`, `fase_actual: 'Neutral'`.

#### 9. [Low] `SICC_soporte.bilineal()` returns `NaN` when interpolation weights `a` or `b` are non-finite
- **Location:** `app/soporte-meteo.js:7-10` (`bilineal`)
- **What happens & why it is a bug:**
  `bilineal(q, a, b)` validates `q.some(x => !Number.isFinite(x))` and returns `null`, but does not validate `Number.isFinite(a) && Number.isFinite(b)`. If `a` or `b` is `NaN`/`undefined`, it returns `NaN` instead of `null`.
- **Verification/Repro evidence:**
  Node reproducer (`task-51`): `bilineal([10, 20, 30, 40], NaN, 0.5)` returned `NaN`.

#### 10. [Low] Regional wind speed computation coerces `null` components to `0` unlike global wind
- **Location:** `app/campo.js:26` (`campo`) vs `app/campo.js:39-40` (`campoG`)
- **What happens & why it is a bug:**
  In `campoG`, `viento_ms` checks `Number.isFinite(u) && Number.isFinite(v) ? Math.hypot(u, v) : null`. In `campo('viento_ms', h)` for the regional grid `G`, it computes `Math.hypot(u, V[i][j])` directly, so any `null` cell becomes `0` m/s rather than `null`. (Verified by inspection; `soporte.bilineal` on `u`/`v` individually would reject `null`, whereas `campo('viento_ms', h)` turns `null` into `0` before `bilineal` runs.)

---

### Note on Clean Areas Checked
- `app/soporte-meteo.js:3-6` (`utc`): correctly appends `'Z'` only when no `Z` or `[+-]HH:MM` offset is present; returns `NaN` on non-strings or empty strings.
- `app/campo.js:22,164` (`lon180`, `dirDe`): longitude wrapping around ±180° / dateline and meteorological wind-from direction (`atan2(-u, -v)`) are mathematically accurate.
- `app/campo.js:137-141,234-236,282,290`: no growing listener/timer/canvas leaks observed (`cT` and `cP` are singletons, `tmp` canvas is ephemeral and unattached, `reproducir` interval is cleared by `parar()`, `graficas[id]?.destroy()` cleans up Chart.js instances).
