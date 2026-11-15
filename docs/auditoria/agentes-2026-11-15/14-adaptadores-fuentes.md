# Agente 14: Adaptadores de Fuentes NASA

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

## Audit Report: `backend/clima_nic/fuentes` (checkout `wt_audit20`, HEAD `20bec48`)

### Checks Run (all read-only, `git status --short` clean)
1. `python -m py_compile` on all 19 files in `backend/clima_nic/fuentes/*.py`: **PASSED** (exit code 0, 19/19 compiled).
2. `python -B -m pytest tests/test_backend_clima_nic.py tests/test_gldas_mensual.py tests/test_recursos_tierra.py tests/test_recursos_contraste.py tests/test_recursos_csa.py -q`: **117 passed**, 1 Starlette deprecation warning in `105.39s`.
3. Targeted inline Python (`python -B -c`) verification reproducers on pure parsers, NetCDF/HDF5 readers, unit conversions, and edge cases.

---

### Confirmed Findings

#### High Severity

1. **[High] `Smap.leer` crashes on every HDF5 file due to invalid 2D `h5py` fancy indexing**
   - **Location**: `backend/clima_nic/fuentes/smap.py:65` (`Smap.leer`)
   - **What happens & why**: `d = f["Geophysical_Data"][variable][np.ix_(filas, cols)].astype(float)` passes the 2D index tuple returned by `np.ix_` directly to an `h5py.Dataset` before loading it into NumPy. `h5py` only supports 1D sequences in fancy indexing and unconditionally raises `TypeError`. (Lines 61 & 66 index already-materialized NumPy arrays `lat`, `lon`, so only line 65 crashes.)
   - **Verification**: Synthetic HDF5 reproducer failed with: `Smap.leer FAILED: TypeError Only 1D arrays allowed for fancy indexing`.

2. **[High] `parsear_hyrax_ascii` flattens 3D+ arrays into 2D, breaking `media_caja_coslat`**
   - **Location**: `backend/clima_nic/fuentes/giovanni.py:345-359` (`parsear_hyrax_ascii`)
   - **What happens & why**: Multi-indexed lines like `precipitation[0][0], ...`, `precipitation[1][0], ...` do not match `r"\[(\d+)\]"`, so every row is appended flatly into `filas_ord[nombre]` and converted to a 2D array of shape `(N_time * N_lat, N_lon)` instead of `(N_time, N_lat, N_lon)`. When `N_time > 1`, passing the result to `media_caja_coslat` fails on the `lat` boolean mask.
   - **Verification**: Reproducer with `(time=2, lat=2, lon=2)` yielded `hyrax 3D shape: (4, 2)` and crashed in `media_caja_coslat`: `IndexError: boolean index did not match indexed array along axis 0; size of axis is 4 but size of corresponding boolean axis is 2`.

3. **[High] `GraceFo.leer` ignores `_FillValue`, silently corrupting regional means**
   - **Location**: `backend/clima_nic/fuentes/grace.py:37-47` (`GraceFo.leer`)
   - **What happens & why**: `d = f["lwe_thickness"][:][:, ilat][:, :, ilon].astype(float)` never checks or masks `_FillValue` (nor `scale_factor`/`add_offset` attributes). Any fill values (e.g. `-99999.0` or `1e20`) pass straight into `recortar_malla` as valid cm of water thickness.
   - **Verification**: Synthetic HDF5/NetCDF4 reproducer with `_FillValue = -99999.0` returned `grace _FillValue preserved as: -99999.0`.

4. **[High] `NexGddp.recortar` subtracts `273.15` from non-temperature variables (`hurs`, `rsds`, `sfcWind`) and `NexGddp.agregar` raises `KeyError`**
   - **Location**: `backend/clima_nic/fuentes/nex_gddp.py:38-39, 114-119, 129-134` (`NexGddp.recortar`, `NexGddp.agregar`)
   - **What happens & why**: `NexGddp.variables` declares `pr`, `tas`, `tasmax`, `tasmin`, `hurs` (`%`), `rsds` (`W m⁻²`), and `sfcWind` (`m/s`), but `recortar()` only branches on `if variable == "pr": ... else: np.mean(...) - 273.15`. Calling `recortar` with `hurs`, `rsds`, or `sfcWind` corrupts units by subtracting `273.15`. Furthermore, `agregar()` looks up `VARIABLES[variable]` where `VARIABLES = {"pr": "mm/mes", "tas": "°C"}` (line 29), raising `KeyError` for any of the other 5 declared variables.
   - **Verification**: Reproducer on synthetic 365-day NetCDF3 with `hurs = 80.0` returned `nex_gddp hurs (80%) Jan result: -193.14999999999998`.

---

#### Medium Severity

5. **[Medium] `Gistemp.leer` NetCDF-4 branch crashes on 1D attribute arrays; `descargar` lacks atomic `.nc` write**
   - **Location**: `backend/clima_nic/fuentes/gistemp.py:41-43, 54-56, 65-66` (`Gistemp.descargar`, `Gistemp.leer`)
   - **What happens & why**: In the `h5py` (NetCDF-4) branch, `float(v.attrs.get("scale_factor", 1.0))` raises `TypeError` under NumPy 2.5.3 when `scale_factor` is a 1-element array `np.array([0.01])` (unlike `merra2.py:60` which uses `np.ravel(...)[0]`). Neither branch applies `add_offset` if present. Also, `descargar()` writes uncompressed output directly to `nc` rather than `.parcial` + `replace()`, leaving a corrupt partial file permanently cached if decompression is interrupted.
   - **Verification**: Reproducer with `h5py` dataset and `scale_factor = np.array([0.01], dtype='float32')` failed with: `Gistemp.leer nc4 FAILED: TypeError only 0-dimensional arrays can be converted to Python scalars`.

6. **[Medium] `AppEEARS.terminadas` hardcodes `(2001, 2024)`, rejecting valid tasks from other year ranges**
   - **Location**: `backend/clima_nic/fuentes/appeears.py:271-272, 580-584` (`AppEEARS.terminadas`, `main`)
   - **What happens & why**: `terminadas()` builds its geometry lookup via `self.plan(2001, 2024, geojson, productos)`, and CLI `procesar-terminadas` ignores `--inicio` and `--fin`. Any 5-year MODIS task submitted with a different start/end year (e.g., `2010–2024`) has different `(desde, hasta)` keys and fails with `ValueError`.
   - **Verification**: Reproducer with `plan(2010, 2024, productos=['MOD13A3.061'])` failed with: `appeears.terminadas(2010..2024) FAILED: ValueError Tarea tid-1 sin geometría en el plan: ('NIC', 'MOD13A3.061', '2010-01-01', '2014-12-31')`.

7. **[Medium] `AppEEARS.api` does not retry network/timeout errors and `bajar_bundle` races on `autenticar()`**
   - **Location**: `backend/clima_nic/fuentes/appeears.py:109-127, 231-236` (`AppEEARS.api`, `AppEEARS.bajar_bundle`)
   - **What happens & why**: `api()` only catches `urllib.error.HTTPError` (retrying 429/503), so transient `URLError`, `TimeoutError`, or `ConnectionError` during large multi-thousand-file bundle downloads (`hilos=8`) abort without retry. Also `float(e.headers.get("Retry-After") or 0)` throws `ValueError` if a server returns an HTTP-date. In `bajar_bundle(task_id, hilos=8)`, if `self._token` is not yet populated, all worker threads concurrently invoke `self.autenticar()` and mutate `self._token` without synchronization.

8. **[Medium] `Smap.descargar` temporal format mismatch and `earthdata.granulos` silent 10,000-granule truncation**
   - **Location**: `backend/clima_nic/fuentes/smap.py:53` (`Smap.descargar`); `backend/clima_nic/fuentes/earthdata.py:51-68` (`granulos`)
   - **What happens & why**: All other `Adaptador.descargar(inicio, fin)` implementations (`power`, `imerg`, `merra2`, `modis`, `grace`, `nex_gddp`, `appeears`, `gldas_datarods`) accept integer years and append `-01-01T00:00:00Z` / `-12-31T23:59:59Z`. `Smap.descargar` uses `f"{inicio}T00:00:00Z"`, producing invalid CMR temporal queries (`2016T00:00:00Z`) if called with integer years. Additionally, `earthdata.granulos` defaults to `max_paginas=50` (`page_size=200` → 10,000 granules max) and silently stops returning results beyond page 50—truncating 3-hourly SMAP queries > 3.4 years and daily IMERG queries > 27.4 years.

9. **[Medium] `Imerg.agregar` labels `mm/h` (or `mm/day`) rates as `"mm"` when `recortar` is called with default `horas=None`**
   - **Location**: `backend/clima_nic/fuentes/imerg.py:53-66` (`Imerg.recortar`, `Imerg.agregar`)
   - **What happens & why**: `Imerg.recortar()` defaults to `horas=None`, returning raw `mm/h` (monthly) or `mm/day` (daily) rates, while `Imerg.agregar()` unconditionally creates `SerieRegional(..., "precipitation", "mm", ...)`.
   - **Verification**: Reproducer on synthetic `0.5 mm/h` IMERG HDF5 returned `Imerg default agregar: mm [0.5]`.

10. **[Medium] Retry/backoff defects in `gldas_mensual.descargar_mes` and `GldasDatarods.descargar`**
    - **Location**: `backend/clima_nic/fuentes/gldas_mensual.py:116-131` (`descargar_mes`); `backend/clima_nic/fuentes/gldas_datarods.py:145-152` (`GldasDatarods.descargar`)
    - **What happens & why**: `descargar_mes` catches `Exception` and retries 6 times with **zero delay** (`time.sleep` is absent), hammering OPeNDAP immediately on 429/503 and retrying permanent 401/403/404 errors 6 times. Conversely, `GldasDatarods.descargar` has **no retries at all** on HTTP 429/5xx or `URLError`/`TimeoutError` across 360 sequential requests.

11. **[Medium] `power.indices_oceanicos` wipes entire AMO series on a single `NaN`; `Power.campo_caja` crashes on empty features**
    - **Location**: `backend/clima_nic/fuentes/power.py:186, 229-234` (`Power.campo_caja`, `indices_oceanicos`)
    - **What happens & why**: For `amo`, `np.polyfit(t, an, 1)` is called on the full array without masking `NaN`s, turning all 360 months to `NaN` if even 1 month is missing. In `Power.campo_caja`, an empty `features` list raises `StopIteration` on `next(iter(puntos.values()))`.
    - **Verification**: Reproducer with 1 `NaN` month produced `AMO all NaN count: 360 of 360`; empty `features` raised `Power.campo_caja empty FAILED: StopIteration`.

---

#### Low Severity

12. **[Low] `parsear_dap2_ascii` silently returns an unshaped 1D array on truncated responses**
    - **Location**: `backend/clima_nic/fuentes/giovanni.py:268-269` (`parsear_dap2_ascii`)
    - **What happens & why**: `plano.reshape(forma) if forma and np.prod(forma) == plano.size else plano` silently returns a 1D array when elements are missing instead of raising `ValueError`.
    - **Verification**: Truncated `(1, 2, 3)` fixture returned `dap2 truncated shape: (3,)`.

13. **[Low] Unhandled `netrc.NetrcParseError` in `giovanni.iniciar_sesion`, `appeears.autenticar`, and `gldas_datarods.autenticar`**
    - **Location**: `backend/clima_nic/fuentes/giovanni.py:59, 87, 127`; `backend/clima_nic/fuentes/appeears.py:89`; `backend/clima_nic/fuentes/gldas_datarods.py:108`
    - **What happens & why**: Unlike `earthdata.hay_credenciales()`, these call `netrc.netrc(...)` without catching `netrc.NetrcParseError`, leaking a raw parse exception instead of `RequiereEarthdata` or `(None, motivo)`.

14. **[Low] `url_hydrocron` end-of-day cutoff and `NivelLagos.descargar` zero-byte cache check**
    - **Location**: `backend/clima_nic/fuentes/lagos.py:127, 245` (`url_hydrocron`, `NivelLagos.descargar`)
    - **What happens & why**: `url_hydrocron` sets `end_time=f"{fin}T00:00:00Z"` (excluding observations on `fin` after midnight UTC), and `NivelLagos.descargar` checks `if destino.exists():` without `st_size > 0` for the G-REALM text cache.

15. **[Low] `Merra2.recortar` and `Smap.recortar` fail with `AttributeError` if string paths are passed**
    - **Location**: `backend/clima_nic/fuentes/merra2.py:73` (`Merra2.recortar`); `backend/clima_nic/fuentes/smap.py:76` (`Smap.recortar`)
    - **What happens & why**: Both access `p.stem` / `p.name` assuming `Path` objects, whereas `Power.leer_punto`, `AppEEARS.inventario`, `NivelLagos.recortar`, and `GldasDatarods.recortar` wrap entries with `Path(...)`.

---

### Clean / Verified Components
- **`backend/clima_nic/fuentes/__init__.py`**: Registry (`REGISTRO`), `obtener`, and `catalogo` match all 9 registered `Adaptador` subclasses cleanly.
- **`backend/clima_nic/fuentes/base.py`**: Atomic `.parcial` + `replace()` download, `recortar_malla` (0–360° lon normalization, `NaN` weight renormalization), `a_mensual`, and `a_anual` passed inspection and tests.
- **`backend/clima_nic/fuentes/knmi.py`**: Header unit parsing (`mm/day`, `mm/month`, etc.), `-999` fill rejection, 3-column and 13-column parsing, and 12-month completeness checks in `anual` are clean and pass tests.
- **`backend/clima_nic/fuentes/sar_agua.py`**: `potencia_a_db`, `caracteristicas_dualpol`, `calibrar_umbral`, `evaluar_mascara`, `mascara_agua`, and `procesar` (EPSG:6933 enforcement and nodata=255 masking) are clean and pass all unit tests.
- **`backend/clima_nic/fuentes/noaa_cdo.py`**: Token handling (env-only, never logged/returned), URL encoding, CSV/JSON parsing, and daily/monthly aggregation are clean and pass all tests (note: `noaa_cdo.descargar` has no retry loop on transient HTTP errors).
- **`earthdata.abridor()` thread safety**: Inspected `urllib.request.HTTPBasicAuthHandler` and `HTTPPasswordMgr` in Python 3.13.4; no shared mutable `retried` counter exists on `HTTPBasicAuthHandler`, and `CookieJar` uses an `RLock`.

### Files Inspected
All 19 requested files in `backend/clima_nic/fuentes/`: `__init__.py`, `base.py`, `earthdata.py`, `power.py`, `gistemp.py`, `noaa_cdo.py`, `imerg.py`, `merra2.py`, `modis.py`, `smap.py`, `grace.py`, `nex_gddp.py`, `lagos.py`, `appeears.py`, `giovanni.py`, `knmi.py`, `sar_agua.py`, `gldas_mensual.py`, `gldas_datarods.py` (plus supporting `regiones.py`, `rutas.py`, `agro.py`, `estadistica/indicadores.py`, `productos.py`, `recursos.py`, and the 5 corresponding pytest suites).
