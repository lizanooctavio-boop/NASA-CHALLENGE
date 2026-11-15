# Agente 12: Productos, Proyecciones, Agro, Actualizar y Regiones

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

Audit complete on `wt_audit20` (`20bec48`). Here are the verified findings, files inspected, and checks run.

### Confirmed Findings

1. **[High] Hardcoded 2024 year limits silently drop 2025+ observations (including existing 2025 GISTEMP data)**
   - **Location**: `backend/clima_nic/productos.py:410-413, 423, 435` (`construir`), plus `productos.py:83` (`PROCEDENCIA_MAPAS`)
   - **What happens & why it is a bug**: `imerg_anual` and `imerg_jjason` iterate `for a in range(2001, 2025)`, `gis_anual` filters `1981 <= a <= 2024`, and `ndvi` filters `a <= 2024`. Once data extends past 2024 (as happens with `actualizar --descargar`, which sets `fin = date.today().year - 1` = `2025`), 2025+ years are silently dropped and `PROCEDENCIA_MAPAS["fuente"]` remains hardcoded as `1981–2024`.
   - **Verification**: `data/fenomenos/gistemp_nicaragua.csv` already contains 12/12 finite months for `2025` (mean `1.3609166666666666` for `NIC`), yet `2025 in gis_anual_actual` is `False` and `data/fenomenos_nicaragua.json` stops at `2024` for `temperatura_gistemp` in all 5 regions.

2. **[High] `KeyError` on incomplete years/months in IMERG aggregation**
   - **Location**: `backend/clima_nic/productos.py:410-413` (`construir`)
   - **What happens & why it is a bug**: `sum(v[(a, m)] for m in range(1, 13))` and `sum(v[(a, m)] for m in JUN_NOV)` unconditionally index `v[(a, m)]` for every `a in range(2001, 2025)`. Any missing month or incomplete year in `data/serie_mensual.csv` for `NIC` or `caja_sicc` crashes `construir()` with `KeyError`.
   - **Verification**: Reproducer with `imerg_m = {"NIC": {(2001, m): 100.0 for m in range(1, 13)}}` raised `KeyError((2002, 1))`.

3. **[High] Division by zero (`ZeroDivisionError`) and `NaN` leakage in CMIP6 scenarios**
   - **Location**: `backend/clima_nic/proyecciones.py:76-84` (`escenarios`)
   - **What happens & why it is a bug**: For `variable == "pr"`, `d = (cf / ch - 1) * 100` divides by `ch` without checking `ch == 0`, and `sesgo_modelos_historico` computes `(ch / obs - 1) * 100` without checking `obs == 0`. Both `ch` and `obs` are Python `float`s from `climatologia()`, so `0.0` triggers `ZeroDivisionError`. If `observado` has no complete years in `hist` (`n_obs == 0`), `obs` is `nan` and `escenarios()` returns `observado_historico: nan` and `sesgo_modelos_historico: {mo: nan}`.
   - **Verification**:
     - `ch == 0.0` -> `ZeroDivisionError('float division by zero')`
     - `obs == 0.0` -> `ZeroDivisionError('float division by zero')`
     - Empty `observado` -> `observado_historico: nan`, `sesgo: {'M1': nan}`, `json.dumps(..., allow_nan=False)` raised `ValueError('Out of range float values are not JSON compliant: nan')`.

4. **[High] Unhandled `KeyError`/`IndexError`/`ValueError` on short or empty IMERG overlap**
   - **Location**: `backend/clima_nic/productos.py:449-459` (`construir`) and `productos.py:348-359` (`modelo_estacional`)
   - **What happens & why it is a bug**: Unlike the GISTEMP comparison (`if len(comunes) >= 15:` at line 468), the IMERG comparison does not check `len(comunes)` or `tp["veredicto"]`: with `< 10` common years `tr.analizar` omits `"theil_sen"` and `tp["theil_sen"]["por_decada"]` raises `KeyError`, and with `0` common years `comunes[0]` raises `IndexError`. Similarly, `modelo_estacional` skips `grilla` entries when `len(anios) < 15` (line 315) but runs `me.evaluar` unconditionally for `principales` (lines 338-359), crashing on empty overlap.
   - **Verification**: `tr.analizar([2020, 2021, 2022], ...)` followed by `tp["theil_sen"]["por_decada"]` raised `KeyError('theil_sen')`; `productos.modelo_estacional(obj, idx, permutaciones=10, imerg={"NIC": {2030: 1000.0}})` raised `ValueError: cannot reshape array of size 0 into shape (0,newaxis)` at `productos.py:357` -> `modelo_estacional.py:78`.

5. **[Medium] Stale GISTEMP cache in `actualizar(descargar=True)` prevents updating GISTEMP**
   - **Location**: `backend/clima_nic/actualizar.py:60-67` (`actualizar`) -> `backend/clima_nic/fuentes/gistemp.py:38-44` (`Gistemp.descargar`) -> `backend/clima_nic/fuentes/base.py:94-98` (`descargar_url`)
   - **What happens & why it is a bug**: `Gistemp.descargar()` downloads to a fixed unversioned path (`gistemp250_GHCNv4.nc.gz`) and decompresses only `if not nc.exists():`. Because `descargar_url` returns immediately if `destino.exists() and destino.stat().st_size > 0`, running `actualizar --descargar` after the initial download never fetches new GISTEMP releases or refreshes `.nc`. (Also note: `actualizar` defaults `tierra=None` when `--tierra` is omitted, silently skipping land-masking in `power.escribir_derivados` (`power.py:323-324`) vs. the versioned dataset.)
   - **Verification**: With pre-existing `gistemp250_GHCNv4.nc.gz` and `.nc`, `base.descargar_url("https://example.invalid/gistemp250_GHCNv4.nc.gz", gz)` returned the cached path without network access (`True`) and preserved `b'old-nc-content'`.

6. **[Medium] `actualizar.registrar` can write invalid JSON (`NaN`) to `data/historial/corridas.jsonl`**
   - **Location**: `backend/clima_nic/actualizar.py:53-54` (`registrar`) and `backend/clima_nic/productos.py:556-560` (`escribir`)
   - **What happens & why it is a bug**: `productos.escribir()` cleans only the copy serialized to `fenomenos_nicaragua.json` (`_limpio(r)` with `allow_nan=False`), returning the uncleaned `r`. `actualizar()` passes that uncleaned `resultado` to `registrar()`, which writes `json.dumps(registro, ensure_ascii=False)` without `allow_nan=False` or sanitization. Any `NaN`/`Inf` in `msess` writes non-standard `NaN` into `corridas.jsonl`.
   - **Verification**: Passing `msess=float("nan")` to `actualizar.registrar` wrote `{"habilidad": {"NIC|test": NaN}, ...}`, failing strict JSON decoding (`ValueError('NaN')`).

7. **[Medium] Missing/partial months in 1995–2014 POWER daily data become `0.0` mm in CMIP6 `obs_pr`**
   - **Location**: `backend/clima_nic/productos.py:498-502` (`construir`)
   - **What happens & why it is a bug**: `obs_pr[(a, m)] = float(d["prectotcorr"][sel].sum())` and `obs_t[(a, m)] = float(d["t2m"][sel].mean())` do not check that `sel` is non-empty or has a full month. If a month in `1995–2014` is missing (`sel` empty), `.sum()` silently records `0.0` mm instead of `NaN` (biasing the observed historical climatology down in `proyecciones.escenarios`), while `.mean()` produces `nan` with a `Mean of empty slice` warning.
   - **Verification**: Evaluating on a January-only slice with `sel_feb = (anio == 1995) & (mes == 2)` yielded `obs_pr = 0.0` and `obs_t = nan` (with `RuntimeWarning`).

8. **[Medium] `grados_dia` does not cap `tmin` at `techo`, exceeding `techo - base` when `tmin > techo`**
   - **Location**: `backend/clima_nic/agro.py:58-63` (`grados_dia`)
   - **What happens & why it is a bug**: `tx = np.minimum(tmax, techo)` caps `tmax` at `techo`, and `tn = np.maximum(tmin, base)` floors `tmin` at `base`, but `tmin` is not capped at `techo`. When `tmin > techo`, daily GDD exceeds the ceiling `techo - base`.
   - **Verification**: `agro.grados_dia(f_2001, 35.0, 32.0, base=10.0, techo=30.0)` returned `7665.0` (`21.0` °C·day/day instead of `20.0`).

9. **[Medium] `eto_penman_monteith` raises `TypeError` when `elevacion_m` is a Python sequence**
   - **Location**: `backend/clima_nic/agro.py:29-38` (`eto_penman_monteith`)
   - **What happens & why it is a bug**: `elevacion_m` is passed to `presion_por_elevacion` (which wraps `np.asarray(z, float)`), but line 38 computes `2e-5 * elevacion_m` directly without `np.asarray(elevacion_m, float)`. Passing a list/tuple raises `TypeError`. (Also, `tmed == -273` or `-237.3` causes division by zero at lines 44 and 34.)
   - **Verification**: `agro.eto_penman_monteith([30, 31], [20, 21], [70, 75], [20, 19], [2, 2], 12.5, [100, 101], [100, 200])` raised `TypeError("can't multiply sequence by non-int of type 'float'")`.

10. **[Medium] `std == 0` in `analizar_variable` and `NaN` in `leer_oceano` CLLJ baseline**
    - **Location**: `backend/clima_nic/productos.py:247-251` (`analizar_variable`) and `productos.py:131` (`leer_oceano`)
    - **What happens & why it is a bug**:
      - When `len(anios) >= 10` and `valores` is constant (`std == 0`), `tr.analizar` returns `veredicto: "datos_insuficientes"`, yet `analizar_variable` still runs `regresion_controlada` and `np.corrcoef(c, valores)[0, 1]`, producing `nan` in `correlacion_moduladores` (converted to `None` only when `escribir()` calls `_limpio`).
      - `leer_oceano` computes `clim` with `np.mean` instead of `np.nanmean`; a single `NaN` in `cllj_u10m` within `1991–2020` makes `clim[m]` `nan`, poisoning `out["cllj"][(a, m)]` for all years in month `m`.
    - **Verification**: Constant-series call to `analizar_variable` returned `veredicto: datos_insuficientes` with `correlacion_moduladores: {'nino34': nan, ...}`; single missing `cllj_u10m` value at `(2000, 1)` made `oce["cllj"][(1991, 1)]` `nan`.

11. **[Low] `meses_sequia_spei3` includes incomplete 1981, and `pesos_malla` crashes on empty `regiones={}`**
    - **Location**: `backend/clima_nic/productos.py:186` (`series_region`) and `backend/clima_nic/regiones.py:110` (`pesos_malla`)
    - **What happens & why it is a bug**:
      - `sp3` has `NaN` (`None` in JSON) for `1981-01` and `1981-02` because 3-month SPEI requires 3 months, yet `s["meses_sequia_spei3"]` counts `np.sum(sp3[ma == a] <= -1)` for `1981` (`0.0` in `data/fenomenos_nicaragua.json`) over only 10 evaluated months instead of requiring 12 finite months.
      - `pesos_malla(..., regiones={})` evaluates `max(p.values())` on an empty dict, raising `ValueError`. (`regiones.cargar`, `regiones.construir`, and `regiones.media_ponderada` were clean.)
    - **Verification**: In `data/fenomenos_nicaragua.json`, `1981` `spei3` starts `[None, None, -0.343]` while `meses_sequia_spei3` includes `1981: 0.0`; `regiones.pesos_malla([12.0], [-86.0], 0.5, 0.625, regiones={})` raised `ValueError('max() iterable argument is empty')`.

### Files Inspected
- Target files: `backend/clima_nic/productos.py`, `backend/clima_nic/proyecciones.py`, `backend/clima_nic/agro.py`, `backend/clima_nic/actualizar.py`, `backend/clima_nic/regiones.py`
- Supporting context: `backend/clima_nic/__main__.py`, `backend/clima_nic/rutas.py`, `backend/clima_nic/consulta.py`, `backend/clima_nic/api.py`, `backend/clima_nic/estadistica/{indicadores,modelo_estacional,tendencia_robusta,fdr}.py`, `backend/clima_nic/fuentes/{__init__,base,power,gistemp}.py`, `scripts/datos/tendencia.py`, `tests/{test_backend_clima_nic,test_indicadores_nicaragua}.py`, `data/fenomenos/{gistemp_nicaragua,manifiesto_power}.csv`, `data/fenomenos/fuentes_power.json`, `data/historial/{habilidad.csv,corridas.jsonl}`

### Checks Run
- `python -m py_compile` on all 5 target files: **passed** (exit code 0).
- `python -m pytest tests/test_backend_clima_nic.py tests/test_indicadores_nicaragua.py -q`: **56 passed, 1 warning** (in 34.13s).
- Inline Python reproducers (`python -` in `wt_audit20`): verified every finding listed above against observed outputs and tracebacks. No files in `wt_audit20` were created, modified, or deleted.
