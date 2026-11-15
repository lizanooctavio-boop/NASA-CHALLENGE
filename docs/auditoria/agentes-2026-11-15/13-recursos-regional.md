# Agente 13: Recursos y Regionales

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

## Audit Report: `recursos.py` & Regional Investigation Modules

Repo checked: `wt_audit20` (clean read-only audit; `git status -s` empty).

### Confirmed Findings

1. **[High] Soil moisture contrast unit truncated from `m³/m³` to `m³`**
   - **File:Line (Symbol):** `backend/clima_nic/recursos.py:486` (and same `.split("/")[0]` pattern at `:447`) in `_contraste`
   - **What happens & why:** `_contraste` computes `"unidad": nuestra.get("unidad", "").split("/")[0]`. For `giovanni_gldas_sm0_10_caja_sicc` in `data/recursos/contraste/resumen_contrastes.json`, `serie_nuestra.unidad` is `"m³/m³/década"`. Splitting on the first `"/"` truncates it to `"m³"` (cubic meters) instead of `"m³/m³"` (volumetric soil moisture), causing a unit mismatch with its target investigation `humedad_gldas_0_10_caja_sicc` (`"m³/m³"`) and rendering wrong units in `app/investigar.js:196`.
   - **Verification:** Observed in `data/recursos_integrados.json` and via `recursos._contraste`: `giovanni_gldas_sm0_10_caja_sicc -> unidad: 'm³'` vs investigation `humedad_gldas_0_10_caja_sicc -> 'm³/m³'`.

2. **[Medium] Negative zero (`-0.0`) emitted in 18 numeric fields of `recursos.construir()` / `data/recursos_integrados.json`**
   - **File:Line (Symbol):** `backend/clima_nic/recursos.py:283-284` (`_r`), used by `tendencia_compacta` (`:287-305`), `_investigacion` (`:308-316`), and `_contraste` (`:485`).
   - **What happens & why:** `_r(v, n=4)` returns `round(float(v), n)` without normalizing `-0.0` (e.g., `+ 0.0`). `recursos_americas.py:85-92` works around this with `_limpiar_cero_negativo`, but `recursos.py`, `recursos_asia_oceania.py`, and `recursos_europa_africa.py` do not. Additionally, `frase_en` in `resumen_contrastes.json` preserves `-0 mm/yr` / `-0.0 mm/yr` in `opendap_imerg_caja_sicc` and `giovanni_imerg_caja_sicc`.
   - **Verification:** `repr(recursos._r(-1e-6))` returned `-0.0`; walking `recursos.construir()` found 18 `-0.0` floats across 9 investigations (`humedad_gldas_0_10_caja_sicc`, `humedad_gldas_0_10_punto_caribe`, `humedad_gldas_10_40_punto_caribe`, `meses_calidos_mar_caribe_nic`, `ciclones_tormentas_NIC`, `ciclones_huracanes_NIC`, `ciclones_tormentas_NIC_1851`, `canicula_duracion_NIC`, `canicula_intensidad_central`) and 2 contrastes (`opendap_imerg_caja_sicc`, `giovanni_imerg_caja_sicc`).

3. **[Medium] `TypeError` crash when no years satisfy hardcoded post-2001 / post-1981 date cutoffs**
   - **File:Line (Symbol):** `backend/clima_nic/recursos.py:728-729` (`_hallazgos` -> `notas_lluvia`) and `:891-892` (`_hallazgos`, PSMSL block)
   - **What happens & why:** Both slice `[(a, v) for a, v in ... if a >= 2001]` / `if a >= 1981` and immediately call `tendencia_compacta(*zip(*...), unidad)` without checking for an empty slice. An empty slice unpacks zero arguments, causing `tendencia_compacta` to raise `TypeError` (e.g., any pre-2001 CHIRPS series or historical PSMSL tide gauge ending before 1981).
   - **Verification:** Reproduced via `recursos.construir()` in `TemporaryDirectory` for `chirps_only_pre2001` and `psmsl_only_pre1981`: both raised `TypeError: tendencia_compacta() missing 2 required positional arguments: 'valores' and 'unidad'`.

4. **[Medium] Unhandled crashes and empty-series emissions on empty/filtered-empty CSVs**
   - **File:Line (Symbol):**
     - `backend/clima_nic/recursos.py:818,833` (`_hallazgos`, `gistemp_bandas.csv`): `IndexError` on `filas[0]['anio']`.
     - `backend/clima_nic/recursos.py:907` (`_hallazgos`, `ibtracs_cerca_nicaragua.csv`): `ValueError: max() iterable argument is empty`.
     - `backend/clima_nic/recursos.py:1047,1056-1057` (`_mundo`, `grace_csr_mensual.csv`): `ValueError` on `max(...)`, or `ZeroDivisionError`/`IndexError` if `anios` is empty.
     - `backend/clima_nic/recursos.py:1123` (`_mundo`, `gfed5_area_quemada_mensual.csv`): `ValueError` on `max(zip(valores, anios))`.
     - `backend/clima_nic/recursos.py:1164` (`_mundo`, `gsw_lagos_nicaragua_anual.csv`): `ValueError` on `max(...)` when empty or no rows pass `fraccion_observada >= 0.8`.
     - `backend/clima_nic/recursos_americas.py:108-131` (`americas`, `colorado_lees_ferry_anual.csv`): `IndexError` / `ZeroDivisionError` when empty or missing pre-1963 rows.
     - `backend/clima_nic/recursos_europa_africa.py:163` (`_lluvia_africa`, `cru_africa_mensual.csv`): `IndexError` on `anios[0]`.
     - `backend/clima_nic/recursos_europa_africa.py:180` (`_grace_oriente`, `grace_oriente_medio_mensual.csv`): `ValueError` on `max(...)`.
     - `backend/clima_nic/recursos_europa_africa.py:89-115` (`_mediterraneo`) & `:135-153` (`_lluvia_africa`): emit investigations with `tiempos: []`, `valores: []` when CSVs are empty/filtered out.
   - **Verification:** Reproduced each crash and empty-series emission (`empty_csv_hallazgos/oisst_mediterraneo_anual.csv` returned `invs=14` instead of `12`) in `TemporaryDirectory` runs.

5. **[Medium] `_anuales_mensuales` and `_estacional` accept `"NaN"`/`"inf"`, and `_estacional` does not deduplicate months**
   - **File:Line (Symbol):** `backend/clima_nic/recursos.py:971-982` (`_anuales_mensuales`) and `backend/clima_nic/recursos_europa_africa.py:118-124` (`_estacional`)
   - **What happens & why:** Both only check `not in ("", "nan")`, allowing `"NaN"` / `"inf"` through `float(...)` into annual/seasonal averages (`math.isfinite` is not checked). Additionally, `_estacional` appends directly to `por[year]` and checks `len(v) == len(meses)` without deduplicating by month, so a duplicate month with another month missing passes as a complete season.
   - **Verification:** `recursos._anuales_mensuales` returned `{2020: nan}` for `"NaN"` and `{2020: inf}` for `"inf"`; `recursos_europa_africa._estacional` returned `{2020: 60.0}` for two March rows and no April row.

6. **[Medium] Hardcoded `a < ultimo` in GRACE drops complete final years and emits false partial-year note**
   - **File:Line (Symbol):** `backend/clima_nic/recursos.py:1047-1070` (`_mundo`) and `backend/clima_nic/recursos_europa_africa.py:180-189` (`_grace_oriente`)
   - **What happens & why:** Both unconditionally exclude `ultimo = max(year)` via `a < ultimo` regardless of month count, and `recursos.py:1068` always prints `"{ultimo} so far ({len(parcial)} months): ... the wettest months are still missing."` even when all 12 months are present. (If `ultimo` has 9–11 months it is partial, but checking completeness via `< 12` instead of `a < ultimo` avoids dropping future 12-month years.)
   - **Verification:** Reproduced with a synthetic 3-year complete GRACE CSV (`2022–2024`, 12 months/year): `2024` was omitted (`tiempos: [2022, 2023]`) and `nota[0]` reported `"2024 so far (12 months): +1.0 cm; the wettest months are still missing."`.

7. **[Low] Minor robustness gaps: discarded `lugares_extra` for Canada/Tierra contrastes and unguarded `swot_mensual.csv` lake ID**
   - **File:Line (Symbol):** `backend/clima_nic/recursos.py:1258-1261` (`construir`), `:565-574` (`_csa`), `:1281` (`construir`)
   - **What happens & why:** `construir` discards `lugares_extra` (`_`) from `contrastes_canada.json` and `contrastes_tierra.json`, and `_csa` does not check `lago in LUGARES` for `swot_mensual.csv`, raising `KeyError` at `todos[k]` (`:1281`) on an unknown lake ID.
   - **Verification:** Reproduced `KeyError: 'lago_desconocido'` with a synthetic `swot_mensual.csv`.

---

### Clean Areas Verified
- **Duplicate IDs / Missing `LUGARES` / Categories / Resource IDs on live data:** In `recursos.construir()` (217 investigations, 33 contrastes, 89 `lugares`), there are 0 duplicate investigation IDs, 0 duplicate contrast IDs, 0 missing `LUGARES`, 0 invalid categories, and 0 unknown resource IDs (`1..13` all `en_uso`).
- **Citations & text:** All `ESTUDIOS` entries in all 4 modules match `Published check: ... doi:10.`. No Spanish leaks found in published strings.

### Files Inspected
- `backend/clima_nic/recursos.py`
- `backend/clima_nic/recursos_americas.py`
- `backend/clima_nic/recursos_asia_oceania.py`
- `backend/clima_nic/recursos_europa_africa.py`
- Supporting files inspected: `backend/clima_nic/estadistica/tendencia_robusta.py`, `backend/clima_nic/rutas.py`, `backend/clima_nic/api.py`, `backend/clima_nic/__main__.py`, `app/investigar.js`, `data/recursos/contraste/resumen_contrastes.json`, `data/recursos/csa/contrastes_canada.json`, `data/recursos/csa/swot_mensual.csv`, `data/recursos/hallazgos/fuentes.json`, `data/recursos/hallazgos/grace_csr_mensual.csv`, `data/recursos/tierra/{contrastes_tierra.json,series_appeears_nicaragua_anual.json,series_appeears_nicaragua_mensual.json,series_gldas_anual.json,series_gldas_punto_anual.json}`, and `tests/test_recursos_*.py`.

### Checks Run
- `python -m py_compile backend/clima_nic/recursos.py backend/clima_nic/recursos_americas.py backend/clima_nic/recursos_asia_oceania.py backend/clima_nic/recursos_europa_africa.py` — **passed (exit 0)**.
- `python -m pytest -q tests/test_recursos_americas.py tests/test_recursos_asia_oceania.py tests/test_recursos_contraste.py tests/test_recursos_csa.py tests/test_recursos_europa_africa.py tests/test_recursos_interfaz.py tests/test_recursos_tierra.py` — **177 passed** in 116.80s. (Note: bare `pytest -q` without `python -m` failed collection due to `ModuleNotFoundError: No module named 'backend'`.)
- Inline Python diagnostics & `TemporaryDirectory` edge-input runs on `recursos.construir()`, `americas()`, `asia_oceania()`, `europa_africa()`, `_anuales_mensuales()`, and `_estacional()` — confirmed all 7 findings above with zero disk modifications.
