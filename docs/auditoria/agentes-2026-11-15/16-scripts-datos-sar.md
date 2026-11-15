# Agente 16: Scripts de Datos y SAR

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

## Audit Report: `scripts/datos/*` and `scripts/sar/*` (wt_audit20, commit `20bec48`)

### Confirmed Findings

1. **[High] Windows `UnicodeDecodeError` crash and silent UTF-8 mojibake in `descargar_hidrologia.py`**
   - **File:Line (Symbol):**
     - `scripts/datos/descargar_hidrologia.py:95, 97` (`Descargas.archivo`)
     - `scripts/datos/descargar_hidrologia.py:107` (`Descargas.json`)
     - `scripts/datos/descargar_hidrologia.py:247, 265` (`main`)
   - **What happens & why it is a bug:** `json_escribir` (line 66) writes UTF-8 JSON (`ensure_ascii=False`), and ArcGIS/SINAPRED responses downloaded by `Descargas.archivo` are UTF-8 JSON containing Spanish text. However, `read_text()` is called without `encoding='utf-8'` on lines 95, 97, 107, 247, and 265. On Windows (`cp1252`), reading UTF-8 text containing bytes undefined in `cp1252` (`0x81`, `0x8d`, `0x8f`, `0x90`, `0x9d`) crashes with `UnicodeDecodeError`, and re-reading `procedencia.json` on `--solo` runs silently produces mojibake.
   - **Verification/Repro evidence:**
     - `Path('data/hidrologia/sinapred_catalogo.json').read_text()` (populated from ArcGIS item JSON via `d.json(...)` at line 219) crashed with: `UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d in position 12117: character maps to <undefined>` (UTF-8 bytes `b'\xe2\x80\x9d'` = `\u201d`).
     - `Path('data/hidrologia/procedencia.json').read_text()` (line 247) differed from `read_text(encoding='utf-8')`, corrupting `'as hidrogr\xe1ficas'` into `'as hidrogr\xc3\xa1ficas'`.

2. **[Medium] Unclosed file handles on `swot_observaciones.csv` (and missing `encoding='utf-8'` in SAR scripts)**
   - **File:Line (Symbol):**
     - `scripts/sar/opera_demostracion.py:124` (`main`)
     - `scripts/sar/modelo_dualpol.py:156` (`main`)
     - `scripts/sar/rcm_procesar.py:210` (`main`)
   - **What happens & why it is a bug:** All three scripts open `swot_observaciones.csv` inline via `.open(...)` inside `csv.DictReader(...)` without a `with` statement, leaking the file descriptor until garbage collection. Additionally, `opera_demostracion.py` (lines 88, 116, 124, 130), `calibrar_optica.py` (lines 45, 133), `modelo_dualpol.py` (lines 154, 156, 169), and `agua_superficial.ipynb` (cell `process`, lines 11 and 20) omit `encoding='utf-8'` on text reads/writes (currently latent because `sar_dominios.geojson`, `cocibolca_naturalearth.geojson`, and `swot_observaciones.csv` are ASCII-only).
   - **Verification/Repro evidence:** Directly observed in source and confirmed via `ast` scan across all `.py` files under `scripts/datos` and `scripts/sar`.

3. **[Low] `agua_superficial.ipynb` cell `run-opera` fails with `NameError` if executed standalone**
   - **File:Line (Symbol):** `scripts/sar/agua_superficial.ipynb` (cell index 3, `id: "run-opera"`)
   - **What happens & why it is a bug:** Cell `run-opera` uses `os.environ`, `sys.executable`, and `root` without importing `os`/`sys` or resolving `root`, assuming cell `process` (index 1) was executed first.
   - **Verification/Repro evidence:** Executing cell 3 sequentially after cell 1 succeeded; executing cell 3 in a fresh namespace (`exec(cell3_src, {})`) raised `NameError: name 'os' is not defined`.

4. **[Low] `comparar` in `verificar_clima.py` does not guard `b` against `bool`**
   - **File:Line (Symbol):** `scripts/datos/verificar_clima.py:56-57` (`comparar`)
   - **What happens & why it is a bug:** `if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):` only excludes `bool` for `a`. Since `bool` subclasses `int`, `comparar(1, True)` evaluates `math.isclose(1, True)` as `True` instead of reporting a type/value mismatch.
   - **Verification/Repro evidence:** Directly observed in `verificar_clima.py:56-57`.

5. **[Low] Inaccurate unused-stripe fraction in `calibrar_optica.py` metadata**
   - **File:Line (Symbol):** `scripts/sar/calibrar_optica.py:128` (`main`)
   - **What happens & why it is a bug:** Lines 41–42 define `train_stripe = ((col//50)%4 == 0)` and `test_stripe = ((col//50)%4 == 2)`, leaving 2 of 4 modulo-4 stripes (`1` and `3`, i.e., **1/2**) unused, whereas line 128 writes `'spatial_split':'5 km column stripes: train 0 mod4, test2 mod4; 1/3 unused'` (also reflected in `data/recursos/csa/sar_validacion_optica.json:6`).
   - **Verification/Repro evidence:** Directly observed in `scripts/sar/calibrar_optica.py:41-42, 128`.

---

### Clean Components
- `scripts/datos/comun.py`, `extraer_series.py`, `generar_clima.py`, `generar_lugares.py`, `geometrias.py`, `preparar_oni.py`, `sensibilidad_geometria.py`: No defects found after line-by-line review and diagnostic checks (note: `shapefile`/`pyshp` is an optional hydrology extraction dependency documented in `scripts/datos/requirements-hidrologia.txt` and not installed in this environment).
- `scripts/sar/dswx_s1_cierre.py`: No defects found (`shapely.transform(lake, transform, interleaved=False)` verified working on Shapely 2.2.0 against `data/recursos/csa/cocibolca_naturalearth.geojson`).

---

### Files Inspected
- `scripts/datos/`: `comun.py`, `descargar_hidrologia.py`, `extraer_series.py`, `generar_clima.py`, `generar_lugares.py`, `geometrias.py`, `preparar_oni.py`, `sensibilidad_geometria.py`, `tendencia.py`, `verificar_clima.py`, `README.md`, `requirements*.txt`
- `scripts/sar/`: `agua_superficial.ipynb`, `calibrar_optica.py`, `dswx_s1_cierre.py`, `modelo_dualpol.py`, `opera_demostracion.py`, `rcm_procesar.py`, `requirements.txt`
- Related modules/outputs read for path/schema/repro verification: `backend/clima_nic/hidrologia.py`, `backend/clima_nic/fuentes/sar_agua.py`, `backend/clima_nic/fuentes/earthdata.py`, `data/hidrologia/procedencia.json`, `data/hidrologia/ineter_catalogo.json`, `data/hidrologia/sinapred_catalogo.json`, `data/lugares_mundo.json`, `data/recursos/csa/{swot_observaciones.csv,sar_fuentes.json,sar_dominios.geojson,rcm_fuentes.json,rcm_superficie.csv,rcm_vs_swot.csv,sar_superficie.csv,sar_superficie_calibrada.csv,sar_dualpol_superficie.csv,sar_validacion_optica.json,sar_dualpol_validacion.json,comparacion_swot_sar.csv,comparacion_swot_sar_dualpol.csv,dswx_s1_serie_corta.csv,dswx_s1_cierre.json}`

### Checks Run
- `python -m py_compile` on all 15 `.py` files (10 in `scripts/datos/`, 5 in `scripts/sar/`): **15/15 passed**.
- Import check across all 15 `.py` modules: **15/15 imported cleanly** (`IMPORT_OK`).
- `python scripts/datos/verificar_clima.py`: **88/88 checks passed** (exit code 0).
- `extraer_series.preparar_malla` + `sensibilidad_geometria` `buffer(±0.05)` on `data/dominios.geojson` with synthetic 0.1° global grid: **passed** (all geometries non-empty; expected cell counts produced).
- `rcm_procesar.a_malla_6933` with synthetic GeoTIFF + 4 GCPs: **passed** (`(1002, 769)` EPSG:6933 output).
- `dswx_s1_cierre` `shapely.transform(..., interleaved=False)` on `data/recursos/csa/cocibolca_naturalearth.geojson`: **passed**.
- `scripts/sar/agua_superficial.ipynb` JSON parse (`nbformat` 4.5, 6 cells), code-cell syntax compile (`2/2` passed), cell 1 execution on synthetic EPSG:6933 GeoTIFF (`passed`), cell 3 sequential (`passed`) vs standalone (`NameError: name 'os' is not defined`).
- Windows `cp1252` default-encoding repro on `data/hidrologia/{procedencia,ineter_catalogo,sinapred_catalogo}.json`: reproduced mojibake on `procedencia.json`/`ineter_catalogo.json` and `UnicodeDecodeError` at byte `0x9d` on `sinapred_catalogo.json`.
- `git status` in `wt_audit20`: clean (`nothing to commit, working tree clean`).
