# Agente 17: Datos y Generadores

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

## Read-Only Audit Report: `data/` & `data/recursos/**/*.py` (`wt_audit20` @ `20bec48`)

### Confirmed Findings

1. **[Medium] Missing daily CHIRPS values silently zeroed into dry days before ETCCDI rain indices**
   - **Location**: [`main`](file:///data/recursos/hallazgos/generar_hallazgos.py#L78-L86) (`data/recursos/hallazgos/generar_hallazgos.py:78-86`)
   - **What happens & why**: Line 79 permits grid cells with up to 1% `NaN` values (`if np.isnan(s).mean() > 0.01: continue`), then line 84 passes `np.nan_to_num(s)` to `ind.indices_lluvia(fechas, np.nan_to_num(s), BASE)`. However, [`indices_lluvia`](file:///backend/clima_nic/estadistica/indicadores.py#L229-L239) explicitly rejects incomplete years containing `NaN` (`if len(x) < 365 or not np.all(np.isfinite(x)): continue`). Converting `NaN` to `0.0` bypasses this guard and turns missing days into `0.0 mm` dry days, inflating `cdd`/`cdd_may_oct` and breaking `cwd`.
   - **Verification/Repro**: Inline reproducer against `clima_nic.estadistica.indicadores.indices_lluvia` on a 2-year daily array with 3 `NaN`s in 2000 returned `[2001]` for raw `s`, vs `[2000, 2001]` with `cdd_2000: 3` for `np.nan_to_num(s)`.

2. **[Medium] Duplicate Giovanni job execution, ignored `max_espera`, and asymmetric AIRS blocked-contrast check**
   - **Location**: [`generar_contrastes.py`](file:///data/recursos/contraste/generar_contrastes.py#L611-L619) (`data/recursos/contraste/generar_contrastes.py:611-619`) and [`contrastes_bloqueados`](file:///data/recursos/contraste/generar_contrastes.py#L1430-L1435) (`:1430`)
   - **What happens & why**:
     - At lines 611–619, `gv.ejecutar(op, url0, espera=5, max_espera=max_espera)` executes `pend[0]`, discards `(ids, urls)` (`_, urls`), and then `for k in list(pend):` executes `pend[0]` a second time while hardcoding `max_espera=300` instead of `max_espera`.
     - At line 1430 (`contrastes_bloqueados`), blocked status for `airs_tas_nic` only checks `(OPENDAP_CSV / "airs_tas_a_nic.csv").exists()`, whereas [`contrastes_estaciones`](file:///data/recursos/contraste/generar_contrastes.py#L1245-L1246) requires both `airs_tas_a_nic.csv` and `airs_tas_d_nic.csv`. If `_a_` exists without `_d_`, `airs_tas_nic` is omitted from both generated and blocked contrasts.

3. **[Medium] Literal `nan` values written to output CSVs & uninformative zero-fraction lake scaling**
   - **Location**: [`lagos`](file:///data/recursos/hallazgos/generar_landsat.py#L109-L112) (`data/recursos/hallazgos/generar_landsat.py:109-112`) -> [`gsw_lagos_nicaragua_anual.csv`](file:///data/recursos/hallazgos/gsw_lagos_nicaragua_anual.csv#L6-L13) (`:6,11-13,40,44,48,51`); [`acidificacion`](file:///data/recursos/hallazgos/generar_mundo.py#L107-L108) (`data/recursos/hallazgos/generar_mundo.py:107-108`) -> [`oceansoda_caribe_mensual.csv`](file:///data/recursos/hallazgos/oceansoda_caribe_mensual.csv#L2) (`:2,518`)
   - **What happens & why**:
     - `generar_landsat.py:111-112` writes `nan` into `gsw_lagos_nicaragua_anual.csv` when `v.any()` is False (6 rows: `cocibolca` 1988, 1995; `xolotlan` 1984, 1988, 1992, 1995) and scales tiny `<0.0005` observed fractions into bogus lake areas (`cocibolca,1993,841.79,0.0,7942.9`; `1994,1922.95,0.0,7942.9`).
     - `generar_mundo.py:107-108` divides by `peso.sum((1, 2))` when zero cells are valid, emitting `nan,nan` for `1982-01` in both `mar_caribe_nic` and `mar_caribe` (`oceansoda_caribe_mensual.csv` lines 2 and 518).
     - Note: [`backend/clima_nic/recursos.py`](file:///backend/clima_nic/recursos.py#L971-L982) (`_anuales_mensuales:977` and `:1160-1161`) explicitly filters out `"nan"` and `fraccion_observada < 0.8`, preventing corruption of `data/recursos_integrados.json`.

4. **[Low] Unhandled empty-`anual` `ValueError` and `NaN` propagation in `generar_americas.py`**
   - **Location**: [`_media_espacial_erddap_mensual`](file:///data/recursos/hallazgos/generar_americas.py#L295-L300) (`data/recursos/hallazgos/generar_americas.py:299`) and [`_series_cru_pre`](file:///data/recursos/hallazgos/generar_americas.py#L338-L343) (`:338-343`)
   - **What happens & why**: Line 299 evaluates `max(anual)` unconditionally, crashing with `ValueError: max() iterable argument is empty` if no complete 12-month year exists. Lines 338–343 append `np.nan` when `den == 0` and sum `doce` directly via `float(sum(doce))`, propagating `nan` rather than omitting incomplete years.
   - **Verification/Repro**: Calling `ga._media_espacial_erddap_mensual` on a CSV with only Feb–May 2024 raised `ValueError: max() iterable argument is empty`.

5. **[Low] Duplicate feature IDs/station codes and future timestamps in INETER river-level snapshot**
   - **Location**: [`ineter_nivel_rio.geojson`](file:///data/hidrologia/ineter_nivel_rio.geojson#L1) (`data/hidrologia/ineter_nivel_rio.geojson`)
   - **What happens & why**: Among the 37 features, `Nivel_Rio.12` (`codigo: "490101"`, Auas Tingni) appears twice (indices 28 and 34: `nivelrio: 1.4` at `2026-11-15T02:15:00Z` vs `null` at `null`), and `Nivel_Rio.14` (`codigo: "490201"`, Sisin) appears twice (indices 32 and 36: `nivelrio: 0` at `2026-11-15T01:15:00Z` vs `1.75` at `"2027-10-26T08:00:00Z"`). Additionally, `Nivel_Rio.14` (`"2027-10-26T08:00:00Z"`) and `Nivel_Rio.36` (`codigo: "690506"`, `"2028-05-24T08:00:00Z"`) carry future observation dates. Note: this is verbatim upstream WFS data and [`src/hidrologia-datos.js`](file:///src/hidrologia-datos.js#L16-L22) (`antiguedad:20`) intentionally surfaces `'Future timestamp: check source'`.

6. **[Low] `json.dumps` without `allow_nan=False` when writing `canada_gistemp.json`**
   - **Location**: [`main`](file:///data/recursos/csa/canada.py#L109) (`data/recursos/csa/canada.py:109`)
   - **What happens & why**: Unlike `lluvia_canada` (`:90`), `main` serializes `canada_gistemp.json` without `allow_nan=False`. (The committed `canada_gistemp.json` is currently valid strict JSON.)

---

### Clean Areas Verified (No Defects Found)
- **`data/clima.json`, `data/dominios.geojson`, `data/serie_mensual.csv`**: All 5 domains complete with no `None`/non-finite floats; `mapa_base_sha256` matches `dominios.geojson` `fuente_mapa_sha256` (`816eba5cb8fb968703b69f4e1d72bf9775f22b49f9f422cac55709c5c09d6f9f`); `serie_mensual_sha256` matches `data/serie_mensual.csv` (`06054f6e2d9896000c92669496f37dde241f83f742c1bd3873294230e6e444a2`).
- **`data/fenomenos_nicaragua.json` & `data/fenomenos/*.csv`**: All 11 `integridad_sha256` hashes match; `celdas_power.csv` (`57` rows) matches `fuentes_power.json` (`celdas: 57`); all 9 CSVs in `data/fenomenos/` have zero malformed rows or `nan`/`inf` strings; `indices_climaticos`, `mapas_tendencia`, `comparaciones_independientes`, `modelo_estacional`, `escenarios_cmip6` contain no non-finite/empty numeric issues.
- **`data/recursos_integrados.json` & `data/recursos/**/*.json`**: Strict JSON with zero `NaN`/`Infinity`; the 7 series containing `null` (`humedad_smap_superficial_NIC` 1/58, `mar_aral_superficie_agua` 6/36, `nivel_mar_auckland_ii` 3/95, `nivel_mar_betio` 1/31, `nivel_mar_funafuti_b` 4/32, `nivel_mar_manila` 4/30, `yangtze_lluvia_extrema_verano` 2/45) are intentional gaps handled by [`app/investigar.js`](file:///app/investigar.js#L134-L168).
- **`data/recursos/csa/rcm_vs_swot.csv`**: Confirmed header-only (`1` line) is expected per [`scripts/sar/rcm_procesar.py`](file:///scripts/sar/rcm_procesar.py#L210-L232), [`swot_observaciones.csv`](file:///data/recursos/csa/swot_observaciones.csv#L1-L5), and [`docs/reto/recursos/csa.md`](file:///docs/reto/recursos/csa.md#L239) (0 SWOT passes within ±2 days of the 2023-08-16 / 2023-08-22 RCM scenes).
- **`data/hidrologia/*.geojson.gz` & catalogs**: All 19 `.geojson.gz` files parsed cleanly with `empty_geom=0, bad_coord=0`; `nicaragua_pfafstetter` (`2337`), `ineter_catalogo` (`402`), and `sinapred_catalogo` (`2` keys, `layers` populated) match `procedencia.json`.
- **`data/ayuda_preguntas.json` & `data/historial/corridas.jsonl`**: 100 unique FAQ items with all bilingual fields; `corridas.jsonl` (1 line) valid strict JSON.

---

### Files Inspected & Checks Run
- **Inspected**: `data/contrato.md`, `data/ayuda_preguntas.json`, `data/hidrologia/procedencia.json`, `data/hidrologia/fuentes_y_limites.md`, `data/recursos/hallazgos/generar_hallazgos.py`, `generar_americas.py`, `generar_europa_africa.py`, `generar_asia_oceania.py`, `generar_landsat.py`, `generar_mundo.py`, `generar_oceano.py`, `gsw_lagos_nicaragua_anual.csv`, `oceansoda_caribe_mensual.csv`, `chirps_acumulado_parcial.csv`, `data/recursos/contraste/generar_contrastes.py`, `data/recursos/csa/canada.py`, `noaa_canada.py`, `rcm_fuentes.json`, `swot_observaciones.csv`, `app/hidrologia.js`, `app/investigar.js`, `app/fenomenos.js`, `src/hidrologia-datos.js`, `backend/clima_nic/recursos.py`, `recursos_americas.py`, `recursos_asia_oceania.py`, `estadistica/indicadores.py`, `fuentes/giovanni.py`, `scripts/datos/descargar_hidrologia.py`, `scripts/sar/rcm_procesar.py`, `docs/reto/recursos/csa.md`, `tests/test_datos.py`, `tests/test_hidrologia.py`.
- **Checks run**:
  - `py_compile` across all `data/**/*.py`: `15 files, errors=0`.
  - Strict JSON/GeoJSON/GZip validation & empty/null checks across `fenomenos_nicaragua.json`, `clima.json`, `dominios.geojson`, `ayuda_preguntas.json`, `corridas.jsonl`, `recursos_integrados.json`, all `data/recursos/**/*.json`, and all 19 `data/hidrologia/*.geojson.gz` files (`0` JSON/coordinate errors).
  - SHA-256 verification for `clima.json` (`serie_mensual_sha256`, `mapa_base_sha256`) and `fenomenos_nicaragua.json` (all 11 hashes matched).
  - CSV structural & `nan`/`inf` scan across all 9 `data/fenomenos/*.csv` (`bad=0`) and flagged `data/recursos/` CSVs.
  - Inline reproducers for `generar_hallazgos.py:84` (`indices_lluvia` `NaN` masking) and `generar_americas.py:299` (`ValueError: max() iterable argument is empty`).
  - `python -m pytest tests/test_datos.py tests/test_hidrologia.py tests/test_lugares_coordenadas.py tests/test_recursos_asia_oceania.py -q`: `80 passed, 1 warning, 28 subtests passed` in `116.77s`.
