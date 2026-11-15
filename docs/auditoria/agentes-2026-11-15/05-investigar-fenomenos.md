# Agente 05: Investigar, Fenomenos e Indicadores

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

# Audit Report: `app/investigar.js`, `app/fenomenos.js`, `app/indicadores.js`

Target checkout: `wt_audit20` (HEAD `20bec48`). Read-only audit; no files modified.

---

## Confirmed Findings

### High

1. **[High] Unhandled crashes on missing `tendencia`, `contrastes`, `fuente`, or `nuestra` fields**
   - **Locations:**
     - `app/investigar.js:121` (`resultado`): `VEREDICTO[t.veredicto]` when `x.tendencia` (`t`) is missing and `x.papel !== 'demostracion_registro_corto'` (despite `t?.veredicto` on line 122).
     - `app/investigar.js:182` (`contrastes`) & `app/investigar.js:269` (`fuentes`): `x.contrastes.map(...)` and `i.contrastes.includes(...)` when `contrastes` is missing/null (whereas `notas` is guarded via `x.notas||[]` on line 143).
     - `app/investigar.js:149` (`resultado`), `app/investigar.js:267` (`fuentes`), `app/investigar.js:283` (`#inv-csv`): `x.fuente.producto` / `i.fuente.producto` when `fuente` is missing/null.
     - `app/investigar.js:192` (`contrastes`): `x.tendencia.veredicto` / `x.tendencia.sen.por_decada` when `c.tipo === 'metodo'` and `x.tendencia` is missing.
     - `app/investigar.js:195` (`contrastes`): `c.nuestra.por_decada` when `c.tipo !== 'metodo'` and `c.nuestra` is missing (despite `c.nuestra?.valores` on line 199).
   - **What happens:** Throws `TypeError` and aborts rendering (or aborts `construir()` during load in `fuentes()`).
   - **Verification:** Reproduced in Node `vm` against mutated `data/recursos_integrados.json` deleting each of `tendencia`, `contrastes`, and `fuente` from `lluvia_NIC`:
     - `MISSING FIELD tendencia ERROR: Cannot read properties of undefined (reading 'veredicto')`
     - `MISSING FIELD contrastes ERROR: Cannot read properties of undefined (reading 'map')`
     - `MISSING FIELD fuente ERROR: Cannot read properties of undefined (reading 'producto')`
   - *(Note: in current `data/recursos_integrados.json`, all 217 investigations define `contrastes`, `notas`, `fuente`, and all 5 without `tendencia` have `papel: "demostracion_registro_corto"`.)*

2. **[High] `L.marker` throws on partial cyclone coordinates (`lat != null`, `lon == null`), breaking the whole storm list**
   - **Location:** `app/fenomenos.js:109` (`cargarTormentas`)
   - **What happens:** Line 112 guards `if(t.lat!=null&&t.lon!=null)`, but line 109 only checks `if(t.lat!=null)` before calling `L.marker([t.lat, t.lon], ...)`. If any active storm has `lat != null` and `lon == null`, `L.marker` throws inside `d.activas.forEach(...)`, jumping to `catch` and replacing `#lista-tormentas` with `"Cyclone data unavailable."`.
   - **Verification:** Reproduced in Node `vm` with `activas: [{ nombre: 'TestStorm', categoria: 'Tormenta tropical', viento_kt: 45, presion_hpa: 1000, lat: 15.0, lon: null }]`; output: `Storm list with lon=null: Cyclone data unavailable.`.

3. **[High] Silent fetch failure in `verMapa()` / `mapaRegiones()` breaks "Regions on the map"**
   - **Location:** `app/indicadores.js:171, 194-198` (`mapaRegiones`, `verMapa`, `#ind-ver-mapa`)
   - **What happens:** Neither `fetch('data/regiones_nicaragua.geojson')` checks `r.ok` before `r.json()`, and both `.catch(()=>{})` handlers silently swallow errors. In `verMapa()`, the fetch runs *before* `window.SICC_vista.cambiar('mapa')`, so if `data/regiones_nicaragua.geojson` fails (HTTP 404/500 or network error), clicking `"Regions on the map"` does nothing at all (never switches to the map and displays no error message).
   - **Verification:** Reproduced in Node `vm` with 404 for `data/regiones_nicaragua.geojson`: `ind-ver-mapa with 404 geojson -> switchedToMap: false` with zero error notification.

---

### Medium

4. **[Medium] Negative-zero formatting (`−0.000`, `−0.0`) on real data & `null`/`NaN` coercion in `num()`/`signo()`**
   - **Locations:** `app/investigar.js:7-8` (`num`, `signo`), `app/indicadores.js:7-8` (`num`, `signo`), `app/fenomenos.js:6` (`dec`)
   - **What happens:** `signo` inspects `v < 0` on the unrounded number before formatting `Math.abs(v)` to `d` decimals, so `-0.5e-d < v < 0` renders `"−0.000"` / `"−0.0"`. Additionally, `num(null, d)` coerces `null` to `"0.00"`, `num(undefined, d)` / `signo(NaN, d)` outputs `"NaN"`, and `fenomenos.js:6` `dec(NaN, n)` / `dec("", n)` outputs `"NaN"` / `"0.0"` (and `"-0.0"` for `-0.04`).
   - **Verification:** Confirmed on real `data/recursos_integrados.json` entries in Node `vm`:
     - `humedad_gldas_0_10_caribe` (`sen.ic[1] = -0.0002`, `d = 3`) -> `"95% CI −0.012 to −0.000 · Theil–Sen"`
     - `escorrentia_subterranea_gldas_CAN_prairies` (`sen.ic[1] = -0.0046`, `d = 1`) -> `"95% CI −0.8 to −0.0 · Theil–Sen"`

5. **[Medium] Contrast unit and precision mismatch for `giovanni_gldas_sm0_10_caja_sicc`**
   - **Location:** `app/investigar.js:194-196, 208` (`contrastes`) & `data/recursos_integrados.json` (`giovanni_gldas_sm0_10_caja_sicc`)
   - **What happens:** Investigation `humedad_gldas_0_10_caja_sicc` has `unidad: "m³/m³"`, whereas contrast `giovanni_gldas_sm0_10_caja_sicc` has `unidad: "m³"` and `diferencia_media: 0` (produced by `backend/clima_nic/recursos.py:486` splitting `"m³/m³/década"` on `"/"` and rounding to 2 decimals) while `frase_en` states `+0.001 m³/m³`. In `contrastes()`, lines 194–195 display the two slopes in `m³/m³/decade`, while line 196 uses `c.unidad || u` (`"m³"`, `dec("m³") = 2`) and renders `"mean difference 0.00 m³"`, and line 208 sets the chart y-axis title to `"m³"`.
   - **Verification:** Reproduced in Node `vm` on `humedad_gldas_0_10_caja_sicc`:
     `−0.004 m³/m³/decade | ... | Agreement | r = 1.00 | mean difference 0.00 m³ | ... mean difference +0.001 m³/m³`

6. **[Medium] Orphaned GIBS tile layer remains stuck on `mapa` if unchecked or errored during refresh**
   - **Location:** `app/fenomenos.js:50, 57-63` (`capaGibs`)
   - **What happens:** On refresh, `viejo = vivo[k]` is kept on `mapa` until `vivo[k].once('load', () => mapa.removeLayer(viejo))` fires. If the user unchecks `#chk-k` (line 50), or `vigilarTeselas`'s `alFallo` fires on `tileerror` (line 59), or `catch` runs (line 63) before the new `vivo[k]` finishes loading, `vivo[k]` is removed and set to `null`, leaving `viejo` permanently on `mapa` with no reference left to remove it.
   - **Verification:** Reproduced in Node `vm` (`chk-imerg` checked -> refreshed -> unchecked before `'load'`): `Layers remaining on map after uncheck (BUG if > 0): 1`.

7. **[Medium] `cargarEnos()` misreports `"ENSO phase: Neutral"` when `oni_actual` is `null`/`undefined`/`NaN`**
   - **Location:** `app/fenomenos.js:131-133` (`cargarEnos`)
   - **What happens:** `fase = d.oni_actual >= .5 ? 'El Niño' : d.oni_actual <= -.5 ? 'La Niña' : 'Neutral'` falls through to `'Neutral'` when `d.oni_actual` is `null`/`undefined`/`NaN`, presenting a false `"Neutral"` phase alongside `"ONI: — °C"`.
   - **Verification:** Reproduced in Node `vm` with `oni_actual: null`:
     `ENSO cards with oni_actual=null: ENSO phase | Neutral | NOAA ONI thresholds | ONI | — °C | NOAA CPC`.

8. **[Medium] Unfiltered `null` values in `indicadores.js` trend line / anomaly calculation & unsafe `r_anual` assumption**
   - **Location:** `app/indicadores.js:94, 115, 130` (`resultado`, `contraste`)
   - **What happens:**
     - Line 94 (`vals.map((y,i)=>y-b*anios[i])`) does not filter `null` values (unlike `investigar.js:167`), so a `null` becomes `0 - b*anios[i]` and corrupts the median intercept `a0`.
     - Line 115 (`anomalia`) does not guard against `null`/`undefined`, missing years (`indexOf(a) === -1`), or empty `anios` (`0/0 = NaN`).
     - Line 130 (`if(c.r_anual!==undefined)`) unconditionally formats `c.media_imerg_mm` and `c.media_power_mm` with unit `mm`, which produces `"Mean NaN vs. NaN mm"` if `r_anual` is ever provided on a temperature comparison (or `"r = 0.00"` if `r_anual === null`). *(Current `data/fenomenos_nicaragua.json` has no nulls in the 4 active variables and only sets `r_anual` on rainfall comparisons.)*

9. **[Medium] Mobile "Regions on the map" / "Show" buttons leave panels covering the map**
   - **Location:** `app/indicadores.js:194-198` (`verMapa`), `app/fenomenos.js:86-90` (`[data-activar]`)
   - **What happens:** Unlike `app/investigar.js:280` (which calls `window.SICC_vista.soloMapa?.(true)` on compact/mobile viewports so the map is revealed), neither `indicadores.js` nor `fenomenos.js` hides the full-screen panel on mobile when switching to the map.

---

### Low

10. **[Low] Double relational operator `"p = < 0.001"` in method contrast card**
    - **Location:** `app/investigar.js:191` (`contrastes`)
    - **What happens:** ``p = ${c.externa.p_valor<0.001?'< 0.001':num(c.externa.p_valor,3)}`` renders `"p = < 0.001 · significant at 5%"` (inconsistent with `"p < 0.001"` on line 131).
    - **Verification:** Reproduced in Node `vm` on real `data/recursos_integrados.json` case `clorofila_golfo_fonseca` (`clorofila_golfo_fonseca_metodo`, `p_valor: 0.0007`): `"p = < 0.001 · significant at 5%"`.

11. **[Low] Short-record branch renders `"Infinity–-Infinity"` if all values are `null`, and fails to filter `undefined`/`NaN`**
    - **Location:** `app/investigar.js:134, 139` (`resultado`)
    - **What happens:** `vals = x.valores.filter(v => v !== null)` keeps `undefined`/`NaN`; if `vals.length === 0`, `Math.min(...[])` / `Math.max(...[])` produces `"Infinity–-Infinity"`.

12. **[Low] Hardcoded `"°C/decade"` unit in `pasoDemo()` comparison cards & missing `DECIMALES` entries**
    - **Locations:** `app/investigar.js:240` (`pasoDemo`), `app/investigar.js:9` (`DECIMALES`)
    - **What happens:** Line 240 hardcodes `°C/decade` and `2` decimals for `dm.comparacion` instead of deriving from `y.unidad` and `dec(y.unidad)` (currently safe only because `nicaragua_vs_praderas` compares temperature series). `DECIMALES` omits 7 units present in `data/recursos_integrados.json` (`'m³/m³'`, `'10¹⁵ molecules/cm²'`, `'%'`, `'km³'`, `'steps'`, `'m w.e.'`, `'10²² J'`), falling back to `2` decimals (e.g., integer `'steps'` formatted with 2/3 decimals).

13. **[Low] Missing URL scheme validation on external JSON links (`r.url`, `t.aviso_url`)**
    - **Locations:** `app/investigar.js:262` (`fuentes`), `app/fenomenos.js:111` (`cargarTormentas`)
    - **What happens:** Unlike `app/investigar.js:272` (`/^https?:/.test(u)`), these assign `a.href` directly from JSON without verifying `http:`/`https:`. *(No XSS via `innerHTML` from JSON or URL params was found in any of the three files.)*

---

## Clean / Verified Areas
- **XSS / `innerHTML`:** All `innerHTML` writes in the 3 files (`investigar.js:118`, `indicadores.js:83`, `fenomenos.js:109`) use hardcoded SVG/HTML templates and safe enum tokens; all JSON text is rendered via `textContent` (`nodo()`). No URL parameter parsing exists in these files.
- **Cross-tab links & data integrity in current JSONs:**
  - `app/inicio.js:17` shortcut (`costa`, `mediterraneo`, `mediterraneo_olas_calor`) resolves cleanly in `data/recursos_integrados.json`.
  - All 89 `lugares` have valid `[lat, lon]` (`[-90,90]`, `[-180,180]`) and `zoom` (`1–18`); all 217 `investigaciones` reference valid `categoria` and `lugar`; all 33 `contrastes` and all `demostraciones` steps/anchors exist in `index.html` and `data/recursos_integrados.json`.
  - `data/regiones_nicaragua.geojson` contains valid features and `bbox` for `NIC`, `pacifico`, `central`, `caribe`.
- **Verdict / color mapping:** `investigar.js:116-117` and `indicadores.js:79-82` match CSS rules `.veredicto.aumento` (`#ffb3a8`), `.veredicto.disminucion` (`#9cc4ff`), `.veredicto.insuficiente` (`var(--tenue)`) in `app/estilos.css:415, 437` (note: positive trend = warm red and negative trend = cool blue across all variables, unlike `src/tendencias.js` which uses teal/peach/amber).

---

## Files Inspected & Checks Run
- **Inspected:** `app/investigar.js`, `app/fenomenos.js`, `app/indicadores.js`, `index.html`, `app/shell.js`, `app/estilos.css`, `app/inicio.js`, `app/graficas-meteo.js`, `src/fuentes-meteo.js`, `src/tendencias.js`, `src/graficas.js`, `scripts/preparar_meteo.mjs`, `backend/clima_nic/api.py`, `backend/clima_nic/recursos.py` (selected lines), `tests/test_recursos_interfaz.py`, `tests/test_e2e_navegador.py`.
- **Checks run:**
  - `node --check app/investigar.js`, `node --check app/fenomenos.js`, `node --check app/indicadores.js`: **PASS** (`SYNTAX_OK`, exit 0).
  - Node schema & rendering audits against `data/recursos_integrados.json` (217 investigations, 89 places, 33 contrasts, 3 demos, 13 resources), `data/fenomenos_nicaragua.json` (5 regions, 7 independent comparisons, seasonal model, CMIP6 scenarios), and `data/regiones_nicaragua.geojson`: **PASS** (surfaced negative-zero slopes, `p = < 0.001`, `giovanni_gldas_sm0_10_caja_sicc` unit mismatch, and missing `DECIMALES` units).
  - Node `vm` reproducers for `investigar.js`, `fenomenos.js`, and `indicadores.js`: **PASS** (reproduced all reported crashes, formatting defects, orphaned tile layer, `Neutral` on `null` ONI, and silent 404 failure in `verMapa()`).
