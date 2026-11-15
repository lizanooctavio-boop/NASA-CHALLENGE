# Agente 10: Backend API, Consulta y CLI

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

Audit complete for `.` (read-only; `git status -s` clean).

### Confirmed Findings

1. **[High] CLI `--help`, `fuentes`, and `consultar` crash with `UnicodeEncodeError` on Windows `cp1252` consoles**
   - **File:Line (Symbol)**: `backend/clima_nic/__main__.py:5,7,20,51,72,75` (`main`)
   - **What happens & why it is a bug**: `__main__.py` does not configure UTF-8 stdout/stderr (e.g. `sys.stdout.reconfigure(encoding="utf-8")`), passes `__doc__` containing `→` (`\u2192`, lines 5 & 7) into `ArgumentParser(description=__doc__, ...)`, and prints `json.dumps(..., ensure_ascii=False, indent=2)` on `fuentes`, `actualizar`, and `consultar`. On Windows (`cp1252` default encoding), characters like `→` (`\u2192`) and `⁻` (`\u207b` in `MJ m⁻² día⁻¹` / `kg m⁻² s⁻¹`) raise `UnicodeEncodeError`.
   - **Verification/Repro evidence**:
     - `python -m clima_nic --help` -> rc=1: `UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 506: character maps to <undefined>`
     - `python -m clima_nic fuentes` -> rc=1: `UnicodeEncodeError: 'charmap' codec can't encode character '\u207b' in position 373: character maps to <undefined>`
     - `python -m clima_nic consultar --region NIC --variable radiacion_solar` -> rc=1: `UnicodeEncodeError: 'charmap' codec can't encode character '\u207b' in position 203: character maps to <undefined>`

2. **[High] HTTP 500 (and 300s cache poisoning) if INETER WFS JSON contains `NaN` or `Infinity`**
   - **File:Line (Symbol)**: `backend/clima_nic/hidrologia.py:37,52` (`obtener_observaciones`), `backend/clima_nic/api.py:94-96` (`observaciones_hidrologicas`)
   - **What happens & why it is a bug**: `obtener_observaciones` calls `r.json()`, whose default `json.loads` accepts non-standard `NaN`/`Infinity`, and stores `copy.deepcopy(d)` in `_CACHE` for 300s. When `observaciones_hidrologicas` returns `d`, FastAPI's `JSONResponse` serializes with `allow_nan=False` outside the endpoint's `try ... except (requests.RequestException, ValueError)` block, causing an unhandled `ValueError: Out of range float values are not JSON compliant` (HTTP 500) and poisoning `_CACHE` for 5 minutes.
   - **Verification/Repro evidence**:
     - Mocked `hidrologia.requests.get` returning `{'type': 'FeatureCollection', 'numberMatched': 1, 'features': [{'type': 'Feature', 'val': float('nan')}]}` and probed `GET /hidrologia/observaciones/nivel_rio` via `TestClient(app, raise_server_exceptions=False)` -> observed `500 Internal Server Error`.

3. **[Medium] `obtener_observaciones` skips `totalFeatures` completeness check when `numberMatched` is `null` or non-numeric**
   - **File:Line (Symbol)**: `backend/clima_nic/hidrologia.py:42-44` (`obtener_observaciones`)
   - **What happens & why it is a bug**: Line 42 writes `total = d.get('numberMatched', d.get('totalFeatures'))`. Because `dict.get` only uses the fallback when the key `'numberMatched'` is absent, a WFS payload with `"numberMatched": null` (or `"unknown"`) and `"totalFeatures": 5` yields `total = None`, failing `str(total).isdigit()` and bypassing the completeness check on line 43. Truncated station collections are thus returned as HTTP 200 and cached for 300s.
   - **Verification/Repro evidence**:
     - Mocked `hidrologia.requests.get` returning `{'type': 'FeatureCollection', 'numberMatched': None, 'totalFeatures': 5, 'features': [{'type': 'Feature'}]}` and probed `GET /hidrologia/observaciones/nivel_rio` -> observed `200` with the 1-feature incomplete payload instead of `502`.

4. **[Medium] Inconsistent region/missing-data validation in `/escenarios` and `/pronostico`**
   - **File:Line (Symbol)**: `backend/clima_nic/consulta.py:87-90` (`pronostico_estacional`), `backend/clima_nic/consulta.py:139-144` (`escenarios`), `backend/clima_nic/api.py:62-70` (`pronostico`, `escenarios`)
   - **What happens & why it is a bug**:
     - `escenarios(region, variable)` never calls `_region(region)` and does `cargar().get("escenarios_cmip6", {}).get(region, {})`, so an invalid region returns HTTP 200 `{"disponible": false, ...}` instead of HTTP 400 `ConsultaInvalida` (unlike `/variables`, `/tendencia`, `/consulta`).
     - `pronostico_estacional(region, anio, variable)` checks `if variable not in VARIABLES_ESTACIONALES:` before calling `cargar()` and `_region(region)`. Thus an invalid `region` paired with a non-seasonal `variable` returns HTTP 200 instead of 400, and when `data/fenomenos_nicaragua.json` is missing it returns HTTP 200 instead of 503.
   - **Verification/Repro evidence**:
     - `GET /escenarios?region=BAD&variable=lluvia_anual` -> `200 | {"disponible":false,"motivo":"Sin escenarios CMIP6 para lluvia_anual en BAD."}` (vs `400` on `/tendencia`).
     - With `consulta.ARCHIVO` set to a missing file: `GET /pronostico?region=NIC&anio=2024&variable=BAD` -> `200 | {"disponible":false,...}` (vs `503` on `/pronostico?region=NIC&anio=2024`).

5. **[Low] Shared mutable cached dict in `consulta.cargar()` and duplicate upstream fetches on cache miss in `hidrologia._CACHE`**
   - **File:Line (Symbol)**: `backend/clima_nic/consulta.py:26-34` (`_cargar`, `cargar`), `backend/clima_nic/hidrologia.py:27-53` (`obtener_observaciones`)
   - **What happens**: `consulta.cargar()` returns the `@lru_cache`-cached `dict` directly without copying, so any in-process Python caller mutating the returned dict mutates shared cached state across threads (`api.py` and `consulta.py` themselves do not mutate it). In `hidrologia.obtener_observaciones`, `_LOCK` is properly released during `requests.get` and `copy.deepcopy` protects `_CACHE` from caller mutation, though concurrent cache misses for the same layer can trigger duplicate upstream WFS requests.

6. **[Low] Minor CLI argument/error-handling gaps in `__main__.py`**
   - **File:Line (Symbol)**: `backend/clima_nic/__main__.py:35-46,70-79` (`main`)
   - **What happens**: `actualizar` subcommand does not expose the `fin` parameter of `actualizar.actualizar(..., fin=None)`; `consultar` does not catch `ConsultaInvalida` or `FileNotFoundError` (prints full traceback, rc=1); `api` hardcodes `host="127.0.0.1"` with no `--host` option.
   - **Verification/Repro evidence**: `python -m clima_nic consultar --region BAD --variable lluvia_anual` -> rc=1 with unhandled `clima_nic.consulta.ConsultaInvalida` traceback.

### Clean Areas Verified
- **`backend/clima_nic/rutas.py`**: Clean (`RAIZ`, `DATOS`, `CACHE`, `sha256`, `a_6933`, `proyectar_6933` verified; `a_6933` recreates `pyproj.Transformer.from_crs` per call, minor performance note only).
- **`consulta.py` vs `data/fenomenos_nicaragua.json`**: No mismatches found. All region IDs, variable keys, `mapas_tendencia`, `escenarios_cmip6`, `indices_climaticos.mensual`, and `modelo_estacional.principales` align cleanly; no `None` values exist in region variable series.
- **SSRF / Timeout in `hidrologia.py`**: `WFS` endpoint is hardcoded (`https://mapserveride.ineter.gob.ni/geoserver/ows`), `capa` is strictly allowlisted via `OBSERVACIONES`, `count=5000` and `timeout=(8, 25)` are enforced.

### Files Inspected
- `backend/clima_nic/api.py`, `backend/clima_nic/consulta.py`, `backend/clima_nic/hidrologia.py`, `backend/clima_nic/rutas.py`, `backend/clima_nic/__main__.py`
- Supporting files: `backend/clima_nic/__init__.py`, `backend/clima_nic/productos.py`, `backend/clima_nic/actualizar.py`, `backend/clima_nic/proyecciones.py`, `backend/clima_nic/regiones.py`, `backend/clima_nic/estadistica/modelo_estacional.py`, `backend/clima_nic/estadistica/tendencia_robusta.py`, `scripts/datos/tendencia.py`, `backend/clima_nic/fuentes/{__init__,base,earthdata,power,nex_gddp,gistemp,modis,imerg,merra2,smap,grace,lagos}.py`, `tests/{test_backend_clima_nic,test_hidrologia,test_datos}.py`, `data/fenomenos_nicaragua.json` (inspected keys/series).

### Checks Run
- `python -m py_compile backend/clima_nic/api.py backend/clima_nic/consulta.py backend/clima_nic/hidrologia.py backend/clima_nic/rutas.py backend/clima_nic/__main__.py` -> exit code 0.
- `python -m pytest tests/test_backend_clima_nic.py tests/test_hidrologia.py -q` -> **42 passed**, 1 warning in 53.30s.
- `TestClient(app, raise_server_exceptions=False)` probes:
  - Baseline endpoints (`/salud`, `/fuentes`, `/regiones`, `/variables`, `/tendencia`, `/pronostico`, `/escenarios`, `/consulta`, `/mapa`, `/hidrologia/observaciones/BAD`): all behaved as expected except `/escenarios?region=BAD` returning 200 instead of 400.
  - Exhaustive probe across all 5 regions x all variables in `fenomenos_nicaragua.json` (`/variables`, `/tendencia` full & subwindow, `/escenarios`, `/consulta`, plus all 6 `/mapa` keys): **0 errors**.
  - `pronostico` probe across 5 regions x 2 seasonal variables x 7 edge years (`1980, 1981, 2001, 2024, 2025, 0, -1`): **0 errors**.
  - All 10-year sliding windows across `canicula_inicio`, `canicula_intensidad`, `canicula_duracion`, `meses_sequia_spei3` in all 5 regions: **0 errors**.
  - Missing `fenomenos_nicaragua.json` probe: `/salud` -> 200 (`datos: false`), `/regiones`, `/variables`, `/tendencia`, `/pronostico` (valid var), `/escenarios`, `/consulta`, `/mapa` -> 503; `/pronostico?...&variable=BAD` -> 200.
  - Mocked `hidrologia.requests.get` edge probes: `numberMatched=None, totalFeatures=5, len=1` -> 200 (bug #3); `NaN` in JSON -> 500 (bug #2); 5000 features -> 502.
- CLI checks (`python -m clima_nic ...`):
  - `--help`, `fuentes`, `consultar --region NIC --variable radiacion_solar` -> failed with `UnicodeEncodeError` (bug #1).
  - `<subcommand> --help` for all 10 subcommands -> exit code 0.
  - `consultar --region NIC --variable lluvia_anual` and `lluvia_jun_nov --anio 2024` -> exit code 0.
  - `consultar --region BAD --variable lluvia_anual` -> exit code 1 with unhandled `ConsultaInvalida` traceback (bug #6).
- `git status -s` -> clean (no modified/untracked files).
