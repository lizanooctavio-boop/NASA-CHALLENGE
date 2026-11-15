# Agente 09: JS Compartido (Estadistica, Graficas, Contrato)

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

Audit complete for `src/contrato.js`, `src/estadistica.js`, `src/graficas.js`, and `src/tendencias.js` in `wt_audit20` (HEAD `20bec48`). No files were modified.

### Confirmed Findings

1. **[High] Unescaped HTML in SVG tooltips (XSS sink)**
   - **Location**: `src/graficas.js:38-40` (`mostrarTip`), `src/graficas.js:153` (`dibujarSerie` -> `mostrar`), `src/graficas.js:223` (`dibujarComparacion`), and dead helper `src/graficas.js:77-81` (`resumenCorto`).
   - **What happens**: `mostrarTip(html, ...)` assigns `t.innerHTML = html`. `dibujarSerie` concatenates `meta.unidades` raw into `html`, and `dibujarComparacion` concatenates `r.nombre` and `meta.unidades_pendiente` raw into `html`, despite `escapar()` existing at `src/graficas.js:234-236` (and being used by `src/tendencias.js`). Note: on the live page `src/tendencias.js:170-172` overwrites `r.nombre` (for known IDs) and `meta.unidades`/`unidades_pendiente`, mitigating the default `clima.json` flow, but `SofGraficas` directly exposes the sink for any dynamic/external data.
   - **Evidence**: Node `vm` reproducer with `nombre: '<img src=x onerror=alert(1)>'`, `unidades: '<svg onload=alert(2)>'`, `unidades_pendiente: '<b onmouseover=alert(3)>mm/dec</b>'` produced unescaped `<svg ...>` and `<img ...>` in `#tooltip.innerHTML`.

2. **[High] 10x unit mismatch (`mm/yr` vs `mm/decade`) when browser fallback computes trends**
   - **Location**: `src/contrato.js:47-59` (`desdeClima`), `src/contrato.js:91-109` (`normalizar`), `src/tendencias.js:172`.
   - **What happens**: When `r.tendencias` is missing (including via `desdeClima` if `t.controles` is omitted, e.g. `inferencia_no_disponible` or `datos_insuficientes`), `normalizar` calls `E.analizar(serie, nivel)`, which returns slopes in **units/year** (`mm/yr`). However, `desdeClima` sets `meta.unidades_pendiente = meta.unidad_pendiente` (`'mm/década'`), and `src/tendencias.js:172` unconditionally sets `estado.datos.meta.unidades_pendiente = 'mm/decade'`. If one or more regions fall back to browser calculation, slopes are labeled as `mm/decade` despite being 10x smaller (`mm/yr`), and `dibujarComparacion` (`src/graficas.js:185`) plots `mm/yr` alongside JSON-provided `mm/decade` intervals on the same axis.
   - **Evidence**: Node `vm` reproducer modifying `NIC` in `data/clima.json` to `estado: 'inferencia_no_disponible'` (12 gapped years, no `controles`) yielded `nicaragua` `origen: 'computed in the browser'`, `mco.pendiente: 5` (mm/yr, should be 50 mm/decade) under `unidades_pendiente: 'mm/década'`, alongside `caja_original` (`-13.132`), `honduras` (`-35.005`), `costa_rica` (`-201.224`).

3. **[High] Unhandled `TypeError` crashes in `colorMapa` and unknown `veredicto_fuente`**
   - **Location**: `src/graficas.js:58-69` (`claseDivergente`, `colorMapa`), `src/contrato.js:102-106` (`normalizar`), `src/graficas.js:205-207` (`dibujarComparacion`), `src/tendencias.js:73-78` (`pintarVeredicto`).
   - **What happens**:
     - `claseDivergente(v, maxAbs)` returns `null` when `v` is `null`/`undefined`/`NaN`/`Infinity`, and `colorMapa` unconditionally calls `.slice(4, -1)` on its return value.
     - `normalizar` maps `r.veredicto_fuente` through a 3-key lookup object without fallback; any unknown string sets `analisis.veredicto.estado = undefined`, causing `ESTADOS[estado].etiqueta`/`.clase` in `dibujarComparacion` and `pintarVeredicto` to throw.
   - **Evidence**: Node `vm` reproducers threw `TypeError: Cannot read properties of null (reading 'slice')` for `colorMapa({analisis:{veredicto:{estado:'aumento'},sen:{pendiente:NaN}}}, ...)` and `TypeError: Cannot read properties of undefined (reading 'etiqueta')` for `veredicto_fuente: 'nuevo_estado_desconocido'`.

4. **[High] Silent wrong `p = 0` on constant series, `NaN` corruption on duplicate `x`, and zero-division in `pearson`**
   - **Location**: `src/estadistica.js:92-106` (`mco`), `src/estadistica.js:109-147` (`sen`), `src/estadistica.js:175-183` (`pearson`), `src/graficas.js:185-231` (`dibujarComparacion`).
   - **What happens**:
     - `mco` line 104 uses `p: se > 0 ? pBilateralT(b / se, gl) : 0`. On a constant `y` series (`b === 0, se === 0`), it returns **`p: 0`** instead of `1` (whereas `scripts/datos/tendencia.py:100` uses `0.0 if b != 0 else 1.0` and line 166 rejects constant series as `datos_insuficientes`).
     - When all `x[i]` are identical (`sxx === 0`, `pend.length === 0`), `mco` returns `NaN` for `pendiente`, `intercepto`, `ic_inf`, `ic_sup` and `p: 0`, while `sen` returns `NaN` for `pendiente`/`intercepto` and `undefined` for `ic_inf`/`ic_sup`. Propagated into `dibujarComparacion`, `vals` contains `undefined`, turning `lo`, `hi`, and all `X(v)` coordinates (including the zero line) into `NaN`.
     - `pearson(a, b)` computes `sab / Math.sqrt(saa * sbb)` without checking `saa === 0`, `sbb === 0`, or `a.length !== b.length`, returning `{ r: NaN, n, p: NaN }`.
   - **Evidence**: Node `estadistica.js` reproducers confirmed `constant` -> `mco.p: 0`; `dupX` (10 points at `anio: 2020`) -> `mco` all `NaN`/`p:0`, `sen` `ic_inf/ic_sup: undefined`, and `dibujarComparacion` emitted `x1: 'NaN'` on MCO, Sen, and `.cero` lines; `pearson([1,1,1,1], [1,2,3,4])` and `pearson([1,2,3,4], [1,2])` -> `{ r: NaN, n: 4, p: NaN }`.

5. **[High] Unsorted input corrupts Mann-Kendall `S` and `p` in `src/estadistica.js`**
   - **Location**: `src/estadistica.js:79-87` (`paresValidos`), `src/estadistica.js:109-147` (`sen`), `src/estadistica.js:168-173` (`analizar`).
   - **What happens**: `sen(x, y, nivel)` accumulates `S += d > 0 ? 1 : d < 0 ? -1 : 0` over array indices `i < j`, assuming `x` is sorted ascending. Neither `paresValidos`, `sen`, nor `analizar` sorts by `x` (unlike `contrato.js:90` and `tendencia.py:160-162`).
   - **Evidence**: Node reproducer with the same 10 `(anio, valor)` points shuffled vs sorted by `anio`: `sen.pendiente` (`-3.5714`) and CI (`[-5, -3]`) matched, but `sen.p` was **`0.999999999`** (shuffled) vs **`0.004208`** (sorted).

6. **[Medium] Numerical and decision-rule divergences vs `scripts/datos/tendencia.py` and `backend/clima_nic/estadistica/tendencia_robusta.py`**
   - **Location**: `src/estadistica.js:92-166` vs `scripts/datos/tendencia.py:87-202` and `backend/clima_nic/estadistica/tendencia_robusta.py:30-69, 146-157`.
   - **What happens**:
     - **Autocorrelation & HAC & verdict**: `estadistica.js` uses unadjusted `gl = n - 2` (documented in comment at line 8), omits Newey-West HAC, and decides verdicts using only unadjusted MCO + Theil-Sen CIs, whereas `tendencia.py` uses Santer et al. (2000) lag-1 effective `n_ef` + HAC + `p < 1 - nivel`, and `tendencia_robusta.py` adds Hamed & Rao (1998) modified Mann-Kendall. On `data/clima.json` `CRI`: JS MCO gives CI `[-369.316, -33.132], p = 0.0212` vs `tendencia.py` `[-378.357, -24.091], p = 0.0280`.
     - **Theil-Sen CI & Mann-Kendall continuity correction**: `estadistica.js:129, 137-139` applies `±1` continuity correction to `S` and `Math.round((N ± C)/2)` integer indexing, whereas `tendencia.py:193-194` and `tendencia_robusta.py:66-69` use `scipy.stats.theilslopes` (interpolated CI) and `scipy.stats.kendalltau` (uncorrected `S`). On `data/clima.json`: `NIC` MK `p = 0.4419` (JS) vs `0.4461` (PY); `caja_sicc` Theil-Sen CI `[-184.427, 188.864]` (JS) vs `[-184.428, 188.865]` (PY).
     - **Constant / gapped series**: `tendencia.py:166-186` returns `datos_insuficientes` (`serie_constante`) or `inferencia_no_disponible` (`< 5` consecutive calendar pairs), whereas `estadistica.js` still computes slopes/verdicts.
     - **Ties in `x`**: `sen` (`src/estadistica.js:115, 128`) skips `x[j] === x[i]` from `pend` (`N < n*(n-1)/2`) without adjusting `varS` or `n` for `x`-ties.

7. **[Medium] SVG zero-range division by zero (`a0 === a1`) and unguarded `undefined`/`NaN` values in `dibujarSerie`**
   - **Location**: `src/graficas.js:89, 101-103, 130`.
   - **What happens**:
     - When `meta.periodo[0] === meta.periodo[1]` (`a0 === a1`), `X(a) = m.l + (a - a0) / (a1 - a0) * (W - m.l - m.r)` computes `0 / 0 = NaN`, emitting `cx="NaN"`, `x="NaN"`, and `d="MNaN,..."` on SVG elements.
     - `validos` (`line 89`) and path building (`line 130`) only check `p.valor !== null` instead of `isFinite(p.valor)`; an `undefined` or `NaN` value yields `ymin = ymax = NaN` and `cy="NaN"` across all points.
   - **Evidence**: Verified both cases in Node `vm` (`cx: 'NaN'`, `d: 'MNaN,141.0'` for `[2024, 2024]`; `cy: 'NaN'` for `valor: undefined`).

8. **[Low/Medium] Global `isFinite` coerces `""`, `" "`, `false`, `true`, `[]` to numbers**
   - **Location**: `src/estadistica.js:82` (`paresValidos`), `src/contrato.js:89, 126` (`normalizar`).
   - **What happens**: `isFinite('')` and `isFinite(false)` return `true` in JS, converting empty strings/booleans into `0` instead of skipping/nulling them.
   - **Evidence**: Verified in Node: `E.paresValidos` converted `{anio:2002, valor:''}` and `{anio:2003, valor:false}` into `y: 0`.

9. **[Low] Minor null-safety & CSV quoting issues**
   - **Location**: `src/contrato.js:62` (`desdeClima`), `src/tendencias.js:134` (`csvPendientes`).
   - **What happens**: `desdeClima` accesses `clima.superposicion.nota` without guarding missing `superposicion`; `csvPendientes` wraps `r.nombre` in `"..."` without escaping internal quotes.

---

### Files Inspected
- `src/contrato.js` (lines 1-163)
- `src/estadistica.js` (lines 1-192)
- `src/graficas.js` (lines 1-244)
- `src/tendencias.js` (lines 1-190)
- `scripts/datos/tendencia.py` (lines 1-267)
- `backend/clima_nic/estadistica/tendencia_robusta.py` (lines 1-177)
- `index.html` (lines 75-287), `data/contrato.md` (lines 1-198), `data/clima.json` (lines 1-120), `tests/interfaz_normalizada.cjs` (lines 1-28), `tests/test_interfaz.py` (lines 1-75), `tests/test_datos.py` (lines 1-210)

### Checks Run
- `node --check src/contrato.js`, `src/estadistica.js`, `src/graficas.js`, `src/tendencias.js`: all 4 passed (exit 0).
- `python -m unittest tests/test_interfaz.py -v`: 6/6 tests passed (0.925s).
- Node `estadistica.js` edge-case suite (empty, `null`, `len<10`, constant, duplicate `x`, `NaN`/`""`/`false`, unsorted `x`, `pearson` edge cases, exact linear): exit 0; reproduced findings #4, #5, #8.
- Node vs `data/clima.json` & Python (`tendencia.py`, `tendencia_robusta.py`) comparison on `clima.json` and synthetic tied/constant/gapped series: exit 0; reproduced finding #6.
- Node `vm` DOM-mock reproducers on `contrato.js` + `graficas.js` (XSS, `a0===a1`, `valor: undefined`, `colorMapa(NaN)`, unknown `veredicto_fuente`, `dupX` propagation, missing `controles` unit mismatch): exit 0; reproduced findings #1, #2, #3, #4, #7.
