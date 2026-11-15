# Agente 11: Motor Estadistico Backend

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

Audit complete for the Python statistical engine in `wt_audit20` (commit `20bec48`). No files in `C:\NASA-CHALLENGE` or `wt_audit20` were modified.

### Baseline Checks Run
- `python -m pytest tests/test_indicadores_nicaragua.py tests/test_backend_clima_nic.py tests/test_datos.py -q` -> **80 passed, 28 subtests passed** (1 deprecation warning in `starlette.testclient`).
- Diagnostic reproducers run in scratch scripts (`audit_repro.py`, `audit_repro2.py`, `audit_repro3.py`, `audit_repro4.py`).

### Confirmed Findings

#### 1. `backend/clima_nic/estadistica/modelo_estacional.py`
- **[High] `msess_loo` divides by zero / produces `NaN` or `-inf` when leverage `h_i = 1`, corrupting `evaluar` permutation p-values**
  - **Location**: `modelo_estacional.py:68-71` (`msess_loo`), `modelo_estacional.py:84-86` (`evaluar`)
  - **Bug**: `ecm = float(np.mean((e / (1 - h)) ** 2))` does not guard `1 - h <= 0` (e.g., `n == k + 1` or an indicator predictor giving `h_i == 1`). In `evaluar`, `msess_loo(rng.permutation(y), X) >= obs - 1e-12` evaluates `False` for `nan` and `-inf`, producing a bogus `p_permutacion_msess = 1 / (permutaciones + 1)`.
  - **Verified**:
    - `X = np.eye(4, 3)`, `y = [1, 2, 3, 4]`: `msess_loo` emits `RuntimeWarning: divide by zero` / `invalid value` and returns `nan`, while `validacion_cruzada(y, X, 1)["msess"] == -1.278125`; `evaluar(y, X, permutaciones=50)["p_permutacion_msess"] == 0.0196078431372549`.
    - `n = 10` with 1-hot column (`X[0, 0] = 1`): `msess_loo == -inf`, `validacion_cruzada == 0.008977`, `evaluar(..., permutaciones=50)["p_permutacion_msess"] == 0.0196078431372549`.

- **[High] `msess_loo` uses `np.linalg.qr(A)` on rank-deficient `X`, silently diverging from `validacion_cruzada(..., 1)`**
  - **Location**: `modelo_estacional.py:67-70` (`msess_loo`)
  - **Bug**: `np.linalg.qr(A)` returns a full-rank orthonormal `Q` even when `A` has constant or collinear columns, projecting `y` and inflating `h` along arbitrary floating-point noise directions instead of matching `np.linalg.lstsq` in `_ajustar`.
  - **Verified**:
    - Constant `X = np.ones((20, 1))`: `validacion_cruzada(y2, X_const, 1)["msess"] == 0.0`, `msess_loo(y2, X_const) == -0.294659158523392`.
    - Collinear `X` (2 identical random columns, `n=20`): `validacion_cruzada == -0.135225266506249`, `msess_loo == -0.22069900889440897`.

- **[Medium] `validacion_cruzada` returns `r = nan` on constant `y` and crashes with `IndexError` when `bloque >= n`**
  - **Location**: `modelo_estacional.py:56`, `modelo_estacional.py:44-53` (`validacion_cruzada`, `_tercil`)
  - **Bug**: Line 56 checks `if np.std(pred) > 0 else 0.0` without checking `np.std(y) > 0`, so constant `y` with non-constant `X` yields `np.corrcoef` division by zero (`r: nan`). When `bloque >= n` (e.g., `n=3, bloque=3`), `ent` is all `False`, `y[ent]` is empty, and `np.percentile` in `_tercil` raises `IndexError`.
  - **Verified**: `validacion_cruzada(np.full(20, 5.0), X_var, 1)["r"]` -> `nan` (and `pronostico(... )["habilidad_loo"]["r"]` -> `nan`); `validacion_cruzada([1,2,3], [[1],[2],[3]], bloque=3)` -> `IndexError: index -1 is out of bounds for axis 0 with size 0`.

---

#### 2. `backend/clima_nic/estadistica/indicadores.py`
- **[High] `ZeroDivisionError` in `ajustar_loglogistica` / `spei` when `6 * w1 - w0 - 6 * w2 == 0.0`**
  - **Location**: `indicadores.py:151` (`ajustar_loglogistica`), `indicadores.py:181-184` (`spei`)
  - **Bug**: `_pwm` returns Python `float`s, so zero denominator in `beta = (2 * w1 - w0) / (6 * w1 - w0 - 6 * w2)` raises `ZeroDivisionError` before `if not math.isfinite(beta)` (line 152) is reached. `spei` only catches `except ValueError:` for its normal-distribution fallback.
  - **Verified**: `ind.spei(np.zeros(180), np.tile(np.arange(1, 13), 15), 1)` crashes with `ZeroDivisionError: float division by zero`.

- **[Medium] Incomplete leap years (365 of 366 days) are treated as complete**
  - **Location**: `indicadores.py:238` (`indices_lluvia`), `287` (`indices_calor`), `348` (`canicula_anio`), `399` (`canicula`)
  - **Bug**: All four completeness checks test `< 365` instead of checking against 366 for leap years.
  - **Verified**: A 2020 series missing Dec 31 (`2020-01-01`..`2020-12-30`, 365 days) is accepted (`2020 in out == True`) by `indices_lluvia`, `indices_calor`, and `canicula`.

- **[Medium] Leap-year DOY shift in `canicula_ventana_fija` / `canicula_anio` and Jan 1 wraparound asymmetry in `umbral_diario`**
  - **Location**: `indicadores.py:269` (`umbral_diario`), `351-352` (`canicula_anio`), `381-385` (`canicula_ventana_fija`)
  - **Bug**: `canicula_ventana_fija` filters `doy` `196..227` documented as July 15–August 15, which becomes July 14–August 14 in leap years (same 1-day shift in `canicula_anio` `135..196` and `213..304`). `umbral_diario` wraps `((d - 1 + k) % 366) + 1`, so for `d = 1` (Jan 1) in non-leap years (`doy` 1..365), `doy = 364` (Dec 30) is excluded while `doy = 366` (leap-year Dec 31) is included.
  - **Verified**: `descomponer` on 2020 vs 2021 maps `doy 196..227` to `2020-07-14..2020-08-14` vs `2021-07-15..2021-08-15`.

- **[Medium] `indices_calor` silently treats `NaN` thresholds as `0%` exceedance and warns/`NaN` on all-NaN `tmed`**
  - **Location**: `indicadores.py:287, 291-292, 297` (`indices_calor`)
  - **Bug**: If `umbral_diario` has `NaN`s (`sel.sum() < 10`), `tx[sel] > ux[d]` is `False` for `NaN`, counting missing-threshold days as 0% exceedances. Also line 287 does not check `tm`, so all-NaN `tmed` triggers `RuntimeWarning: Mean of empty slice` and `"t2m_media": nan`.
  - **Verified**: 1-year base (`2001`) with all-NaN `tmed` returns `tx90p: 0.0, tn90p: 0.0, t2m_media: nan` with `RuntimeWarning`.

- **[Low] Edge cases in `canicula_anio`, `climatologia_diaria`, and `_spi_mes`**
  - `indicadores.py:353-354` (`canicula_anio`): `np.argmax(s[v1])` raises `ValueError: attempt to get argmax of an empty sequence` if `len >= 365` but `doy_anio` lacks days in `135..196` or `213..304` (verified).
  - `indicadores.py:323-326` (`climatologia_diaria`): when `ventana > 1`, a single `NaN` day in `clim` propagates to `ventana` days via `np.convolve` (verified: 1 missing day with `ventana=7` yields 7 `NaN`s).
  - `indicadores.py:94` (`_spi_mes`): `np.full_like(valores, np.nan)` truncates output to integer if `valores` is an integer array (verified; `spi()` itself is unaffected because `suma_movil` casts to `float`).

---

#### 3. `backend/clima_nic/estadistica/tendencia_robusta.py` & `scripts/datos/tendencia.py`
- **[High] `tendencia_robusta.analizar` does not sort `(anios, y, covariables)`, contradicting `tendencia.analizar_tendencia`**
  - **Location**: `tendencia_robusta.py:160-175` (`analizar`), `30-53` (`mann_kendall_modificado`), `72-84` (`pettitt`), `87-96` (`_hac`) vs `tendencia.py:160-162`
  - **Bug**: `tendencia.analizar_tendencia` sorts `anios` and `valores` chronologically; `tendencia_robusta.analizar` passes unsorted arrays to `mann_kendall_modificado`, `pettitt`, and `regresion_controlada._hac`.
  - **Verified**:
    - Reversed `[2024..2001]` series: `minimos_cuadrados.por_decada` stays `50.139`, while `mmk["z"]` flips from `6.2295` to `-6.2295`, `pettitt["anio_cambio"]` changes from `2013` to `2012`, and `veredicto` flips from `"tendencia_detectada"` to `"metodos_discrepan"`.
    - Randomly shuffled 20-year series with covariable: `mmk["z"]` changes from `4.6494` to `-0.0973` and `controlada_por_indices["ic_por_decada"]` changes from `[18.928, 22.976]` to `[19.4832, 22.4209]`.

- **[Medium] Missing-year (gap) handling mismatch between `tendencia.py` and `tendencia_robusta.py`**
  - **Location**: `tendencia_robusta.py:39-49` (`mann_kendall_modificado`), `87-96` (`_hac`) vs `tendencia.py:75-84, 107-118`
  - **Bug**: `tendencia.py` handles missing years via calendar-year lags (`_r1_calendario`, `_intervalo_hac` using `abs(x[:, None] - x[None, :])`). `tendencia_robusta.mann_kendall_modificado` ignores `anios` (detrending against `np.arange(n)` and computing rank autocorrelation by index lag) and `regresion_controlada._hac` uses positional lags `u[k:].T @ u[:-k]`.

- **[Medium] `_r1_calendario` in `tendencia.py` can exceed `1.0` on gapped series**
  - **Location**: `tendencia.py:84` (`_r1_calendario`)
  - **Bug**: Scaling the `pares` consecutive residual products by `(len(x) - 1) / pares / sce` (using total `sce` over all `n` observations rather than variance of the paired observations) allows `r1 > 1.0`, making `n_ef` negative and causing `analizar_tendencia` to abort with `"datos_insuficientes"`.
  - **Verified**: On a 30-year series with 5 consecutive pairs (`x_gap`, `y_gap`), `_r1_calendario` returned `2.16965503757462` and `analizar_tendencia` returned `estado: "datos_insuficientes"`.

- **[Medium] `regresion_controlada` returns `p_valor = 1.0` for exact fits (`se = 0`, `beta != 0`) and calls `_hac` before checking `gl <= 0`**
  - **Location**: `tendencia_robusta.py:110-113, 122, 126` (`regresion_controlada`)
  - **Bug**: Lines 122 & 126 return `p_valor = 1.0` when `se == 0` regardless of `beta != 0` (unlike `tendencia.py:100` which returns `0.0 if b != 0 else 1.0`). Line 110 calls `_hac` (which divides by `n - X.shape[1]`) before `if gl <= 0:` on line 112.
  - **Verified**: Exact linear fit `y3 = 4*(t3 - t3.mean()) + 2*c3` gives `por_decada: 40.0, r2: 1.0, p_valor: 1.0`, `cov p_valor: 1.0`; `gl == 0` emits `RuntimeWarning: divide by zero encountered in divide` on line 96 before raising `ValueError`.

- **[Low] `veredicto_robusto` checks rounded `theil_sen` CI bounds**
  - **Location**: `tendencia_robusta.py:69, 151` (`theil_sen`, `veredicto_robusto`)
  - **Bug**: `theil_sen` rounds `ic_por_decada` to 4 decimals before `veredicto_robusto` tests `> 0` / `< 0`, whereas `tendencia.py` tests unrounded bounds.
  - **Verified**: Tiny positive slope (`vals_b`) gives `tendencia.analizar_tendencia(...)["veredicto"] == "tendencia_detectada"` (`sen ic = [0.0, 0.0]`), while `tendencia_robusta.analizar(...)["veredicto"] == "metodos_discrepan"`.

---

#### 4. `backend/clima_nic/estadistica/fdr.py`
- **[Low] `benjamini_hochberg` counts `NaN`s in `m = len(p)`**
  - **Location**: `fdr.py:13-17` (`benjamini_hochberg`)
  - **Bug**: Any `NaN` in `p_valores` inflates `m`, tightening BH thresholds `q * i / m` for valid p-values. (Current callers in `productos.py` pass finite p-values.)
  - **Verified**: `benjamini_hochberg([0.04, np.nan, 0.9], q=0.10)` returns `([False, False, False], 0.0)` vs `([True, False], 0.04)` without `NaN`.

### Files Inspected
- `backend/clima_nic/estadistica/tendencia_robusta.py` (1–177)
- `backend/clima_nic/estadistica/modelo_estacional.py` (1–161)
- `backend/clima_nic/estadistica/fdr.py` (1–24)
- `backend/clima_nic/estadistica/indicadores.py` (1–404)
- `scripts/datos/tendencia.py` (1–267)
- Callers/tests reviewed for context: `backend/clima_nic/productos.py` (260–360), `backend/clima_nic/consulta.py` (1–168), `backend/clima_nic/fuentes/giovanni.py` (445–480), `backend/clima_nic/recursos.py` (1–200), `tests/test_indicadores_nicaragua.py` (1–336), `tests/test_datos.py` (1–390).

---

Correction to the `audit_repro4.py` (`task-66`) numbers in my previous report — the exact observed output from `task-66.log` for those three checks is:

1. **Shuffled 20-year input to `tendencia_robusta.analizar`** (`anios=2001..2020`, `rng=default_rng(123)`):
   - `sorted`: `veredicto="tendencia_detectada"`, `minimos_cuadrados["por_decada"]=20.379`, `mmk["z"]=4.5746`, `pettitt["anio_cambio"]=2013`, `controlada_por_indices["ic_por_decada"]=[18.0409, 21.8424]`
   - `shuffled`: `veredicto="metodos_discrepan"`, `minimos_cuadrados["por_decada"]=20.379`, `mmk["z"]=1.7195`, `pettitt["anio_cambio"]=2011`, `controlada_por_indices["ic_por_decada"]=[18.092, 21.7912]`
2. **`regresion_controlada` exact zero-residual fit** (`t3=[2001..2004]`, `c3=[1,-1,-1,1]`, `y3=4*(t3-mean)+2*c3`):
   - `{'por_decada': 40.0, 'ic_por_decada': [40.0, 40.0], 'p_valor': 1.0, 'r2': 1.0, 'rezago_hac': 1, 'covariables': {'c': {'coeficiente': 2.0, 'ic': [2.0, 2.0], 'p_valor': 1.0}}}`
3. **`climatologia_diaria(..., ventana=7)` NaN propagation**:
   - `NaNs in climatologia_diaria(ventana=7) from 1 missing day (excl idx 0 & 366): 7`

All other figures in the previous message were directly observed in `task-10`, `task-35`, `task-49`, `task-54`, and `task-57`.
