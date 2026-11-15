# Earth System Trend Detective

**2026 NASA International Space Apps Challenge — "Be an Earth System Trend Detective!"**

- **Live Public Demo:** <https://nasa-challenge-q6cx.onrender.com/>
- **Challenge Page:** <https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/>
- **Submission Package Docs:**
  - [Project Description & Official 2026 Requirements](docs/entrega/PROJECT_DESCRIPTION.md)
  - [AI / Super Intelligence (SI) Disclosure & Verification](docs/entrega/AI_USE.md)
  - [30-Second Video & 7-Slide Demo Script (EN / ES)](docs/entrega/GUION_DEMO.md)

---

## 1. What It Does

**Earth System Trend Detective** is an interactive climate-diagnostics platform that answers the four questions of the challenge—**what** is changing, **where** it is changing, **how much** it is changing, and **whether** those changes are statistically **significant**—across **217 observed Earth-system time series**, **89 locations** worldwide, **8 thematic categories**, **33 independent cross-checks**, and all **13 official challenge resources**.

Every series with at least 10 annual observations is tested simultaneously by **four statistical estimators**:
1. **Theil–Sen non-parametric slope** with 95% confidence interval (`scipy.stats.theilslopes`), resistant to extreme outlier years.
2. **Modified Mann–Kendall test with Hamed & Rao (1998) autocorrelation correction**, preventing positive serial correlation from inflating false positives.
3. **Ordinary Least Squares (OLS)** with AR(1)-adjusted effective degrees of freedom (Santer et al., 2000).
4. **Ordinary Least Squares with Newey–West (1987) HAC** 95% confidence intervals.

### Verdicts Displayed in the Public Demo (`data/recursos_integrados.json`)

| Verdict / Guardrail on Screen | Series Count | Statistical Criterion |
| :--- | :---: | :--- |
| **`Trend detected`** (`tendencia_detectada`) | **79** | All 95% confidence intervals (Theil–Sen, AR(1)-OLS, and Newey–West HAC) exclude zero with the same sign **and** Hamed–Rao modified Mann–Kendall $p < 0.05$. |
| **`Not enough evidence of a trend`** (`evidencia_insuficiente`) | **85** | Confidence intervals include zero and modified Mann–Kendall $p \ge 0.05$ over the observed window. *(Explicitly explained in the UI as a signal-to-noise or record-length limit, **never** "no change".)* |
| **`Methods disagree`** (`metodos_discrepan`) | **48** | Parametric (OLS / HAC) and non-parametric (Theil–Sen / Mann–Kendall) tests reach different conclusions at the 5% threshold, alerting users to outliers, step changes, or borderline autocorrelation. |
| **`Record too short for a trend test`** (`demostracion_registro_corto`) | **5** | Series with `< 10` years of observations (e.g., `SWOT` satellite lake altimetry since 2023 and `OPERA DSWx-S1` radar water scenes) are plotted descriptively without a trend test. |
| **Total Investigations** | **217** | Across **89** locations, **8** categories, **33** cross-checks, **3** guided tours, and **13/13** active challenge resources. |

---

## 2. Visual Overview & Application Views

| View / Tab | URL Hash | What Judges See |
| :--- | :---: | :--- |
| **3D Globe & 2D Map** | `#globe` / `#map` | Interactive `Three.js` 3D Earth (`assets/texturas/tierra-dia.jpg`, `assets/texturas/tierra-noche.jpg`, `assets/texturas/luna.jpg` from NASA GIBS & LRO) that unfolds into a 2D `Leaflet` map with NASA GIBS satellite layers, radar overlays, and regional polygons. |
| **`Investigate`** | `#investigar` | Topic → Place → Variable selector (`217` series), Verdict Card (*How much per decade*, *How sure*, *Least squares*), interactive `Chart.js` plot with Theil–Sen trend line, Crossref-verified *Published check* notes, **33 Cross-checks**, **3 Guided tours**, and 1-click **CSV / JSON export**. |
| **`Learn`** | `#aprender` | Visual, plain-English guides explaining why *"Not enough evidence"* $\neq$ *"no change"*, why monthly data are autocorrelated, how Theil–Sen resists outliers, how Pettitt (1979) detects reanalysis step jumps, and how Benjamini–Hochberg FDR (`q = 0.10`) controls false positives across maps. |
| **`Sources`** | `#fuentes` | Live usage status of all **13 official challenge resources** (`13/13` active) plus direct links to every primary dataset. |
| **`Rainfall trend`** | `#tendencias` | Interactive map and series comparison across Nicaragua (`119,900 km²`), Southwest SICC study box (`66,500 km²`), Honduras, and Costa Rica using NASA GPM IMERG V07B (`2001–2024`). |
| **`Climate indicators`** | `#indicadores` | Multi-variable regional diagnostics for Nicaragua (`Pacific lowlands`, `Central highlands`, `Caribbean coast`), contrasting NASA GISTEMP v4 (`+0.294 °C/decade`, $p < 0.001$) and IMERG against MERRA-2/POWER step inhomogeneities (`docs/reto/recursos/evidencia_tierra/`). |
| **`El Niño & cyclones`** | `#fenomenos` | NOAA CPC Oceanic Niño Index (`ONI`) coupling with rainy-season precipitation and historical tropical cyclone tracks (NOAA IBTrACS v04r01). |
| **`Climate scenarios`** | `#proyecciones` | 6-model NASA NEX-GDDP-CMIP6 (`v2.0`) projections for `2041–2060` vs. `1995–2014` under SSP2-4.5 and SSP5-8.5. |
| **`Watersheds`** | `#hidrologia` | Nicaragua's INETER/SINAPRED Pfafstetter basins and HydroBASINS for the world, with source attribution and original downloads. |
| **`Data downloads`** | `#exportar` | CSV / JSON exports of every series with its source, period and verdict. |
| **`Help`** | Left menu | 100 searchable questions and answers (English / Spanish) and an 11-step guided tour of the app. |

---

## 3. How to Run Locally & Verify

### Prerequisites
- **Node.js** ($\ge 18$)
- **Python** ($\ge 3.11$) with `numpy`, `scipy`, `shapely`, `pyproj`, `h5py`, `rasterio`, `fastapi`, `uvicorn`, `httpx`, and `pytest` (`pip install -r backend/requirements.txt`).

### Quick Start on Windows
Run **`INICIAR-APP.cmd`**: it builds the interface, starts a local server and opens `http://127.0.0.1:8996/` (requires Node.js, and internet for the map tiles). Do not open `index.html` directly: browsers block its modules and data reads under `file://`. The local view does not include the weather grids generated during deployment.

### Build Static Bundle & Run Locally
```bash
# 1. Build the static bundle into public/ (verifies contract and copies assets/data)
node scripts/preparar_render.mjs

# 2. (Optional) Refresh live meteorological snapshot from the forecast service
node scripts/preparar_meteo.mjs

# 3. Serve the static web application locally on http://localhost:8982
python -m http.server 8982 --directory public
```

### Run the Automated Test Suite
```bash
# Run all unit, statistical, cryptographic provenance, and browser E2E tests
python -m pytest -q
```

### Regenerate the Integrated Resource Registry (Offline, Zero Network Calls)
```bash
cd backend && python -m clima_nic recursos
```

---

## 4. Data Sources, Links & Licenses

### 4.1 Official NASA Space Apps Challenge Resources (`13 / 13` Integrated)

| # | Challenge Resource | Agency / Provider | Direct URL | How It Is Used in the App |
| :---: | :--- | :--- | :--- | :--- |
| 1 | **Giovanni** | NASA GES DISC | <https://giovanni.gsfc.nasa.gov/> | Area-averaged NASA time series and sample-point hydrology cross-checks. |
| 2 | **Hydrology Time Series** | NASA GES DISC | <https://disc.gsfc.nasa.gov/information/tools?title=Hydrology%20Time%20Series> | GLDAS-2.1 Noah land-model hydrology series (`docs/reto/recursos/tierra.md`). |
| 3 | **AppEEARS** | NASA LP DAAC | <https://appeears.earthdatacloud.nasa.gov/> | Regional soil moisture from NASA SMAP Level 4 (`SPL4SMGP.008`) and MODIS land subsets. |
| 4 | **Climate Data Online (CDO)** | NOAA NCEI | <https://www.ncei.noaa.gov/cdo-web/> | Weather-station records (`GHCN-Daily` and `GSOM`) in Nicaragua, Honduras, and the Canadian Prairies. |
| 5 | **SeaWiFS Coastal Chlorophyll Time-Series Report (`NTRS 20090042747`)** | NASA NTRS (Acker et al., 2009) | <https://ntrs.nasa.gov/api/citations/20090042747/downloads/20090042747.pdf> | Methodological benchmark for coastal chlorophyll-a time series in river-influenced waters. |
| 6 | **KNMI Climate Explorer** | KNMI | <https://climexp.knmi.nl/> | Independent gridded rainfall cross-checks (`CHIRPS v2.0`, `CRU TS 4.10`, `GPCC`). |
| 7 | **Statistical test methods to detect trends in time series data** | Medium (Kriss, S.) | <https://medium.com/@snp.kriss/statistical-test-methods-to-detect-trends-in-time-series-data-b361a0ec530b> | Reference for seasonal Mann–Kendall and unit-root explanations in the `Learn` tab. |
| 8 | **A Comprehensive Guide to Statistical Significance** | Statsig (Korem, A., 2025) | <https://www.statsig.com/perspectives/a-comprehensive-guide-to-statistical-significance> | Plain-language framing of $p$-values, confidence intervals, and Type II errors in `Learn`. |
| 9 | **RADARSAT Constellation Mission (RCM) — Data** | Canadian Space Agency (CSA) | <https://donnees-data.asc-csa.gc.ca/en/dataset/rcm> | SAR water-extent workflow and RCM ScanSAR scene integration (`docs/reto/recursos/csa.md`). |
| 10 | **Geo.ca** | Government of Canada | <http://geo.ca/> | Boundary of the **Canadian Prairies** terrestrial ecozone (`467,128 km²`) used as a high-latitude contrast region. |
| 11 | **SWOT Mission — Information** | CSA / NASA / CNES | <https://www.asc-csa.gc.ca/eng/satellites/swot/> | SWOT L2 HR LakeSP water-surface elevation for Lakes Cocibolca and Xolotlán cross-checked against G-REALM. |
| 12 | **Monitoring and protecting our ecosystem from space** | Canadian Space Agency (CSA) | <https://www.asc-csa.gc.ca/eng/satellites/everyday-lives/monitoring-and-protecting-our-ecosystems-from-space.asp> | Framing of the *Vegetation & ecosystems* and *Water bodies* categories. |
| 13 | **Synthetic Aperture Radar Python Tutorial** | Canadian Space Agency (CSA) | <https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial> | Open-source workflow (MIT License) adapted to map lake surface water from radar imagery (`OPERA DSWx-S1`). |

### 4.2 Complete Dataset Inventory, DOIs & Licenses

| Dataset / Product | Provider | URL / DOI | License / Terms of Use |
| :--- | :--- | :--- | :--- |
| **NASA GPM IMERG Final Run V07B (`GPM_3IMERGM_07`)** | NASA GES DISC | <https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07> | NASA Open Data Policy (Public Domain / CC0-equivalent with attribution) |
| **NASA GISS Surface Temperature Analysis (`GISTEMP v4`)** | NASA GISS | <https://data.giss.nasa.gov/gistemp/> · <https://doi.org/10.1029/2023JD040179> | NASA Open Data Policy (Public Domain with attribution) |
| **NASA GLDAS-2.1 Noah Land Surface Model (`GLDAS_NOAH025_M 2.1`)** | NASA GES DISC | <https://doi.org/10.5067/SXAVCZFAQLNO> | NASA Open Data Policy (Public Domain with attribution) |
| **NASA SMAP Level 4 Soil Moisture (`SPL4SMGP.008`)** | NASA NSIDC DAAC / AppEEARS | <https://doi.org/10.5067/T5RUATAQREF8> | NASA Open Data Policy (Public Domain with attribution) |
| **NASA MODIS Vegetation Indices (`MOD13Q1.061` / `MOD13C2.061`)** | NASA LP DAAC / ORNL DAAC | <https://doi.org/10.5067/MODIS/MOD13Q1.061> | NASA Open Data Policy (Public Domain with attribution) |
| **NASA MODIS-Aqua L3m Chlorophyll-a (`R2022.0`)** | NASA OB.DAAC (OBPG) | <https://doi.org/10.5067/AQUA/MODIS/L3M/CHL/2022> | NASA Open Data Policy (Public Domain with attribution) |
| **NASA Aura OMI Tropospheric $\text{NO}_2$ (`OMNO2d v003`) & Aqua AIRS (`AIRS3STM v7.0`)** | NASA GES DISC | <https://doi.org/10.5067/Aura/OMI/DATA3007> · <https://doi.org/10.5067/UBENJB9D3T2H> | NASA Open Data Policy (Public Domain with attribution) |
| **NASA/CNES SWOT L2 HR LakeSP (`v2.0` via PO.DAAC Hydrocron)** | NASA PO.DAAC / CNES / CSA | <https://doi.org/10.5067/SWOT-LAKESP-2.0> | NASA PO.DAAC Open Data Policy |
| **NASA OPERA DSWx-S1 (`V1`) & RTC-S1 (`V1`)** | NASA JPL / PO.DAAC / ASF DAAC | <https://podaac.jpl.nasa.gov/dataset/OPERA_L3_DSWX-S1_V1> | NASA Open Data Policy (contains modified Copernicus Sentinel-1 data) |
| **NASA GSFC / USDA G-REALM Satellite Radar Altimetry** | NASA GSFC / USDA FAS | <https://earth.gsfc.nasa.gov/gwm/lake/Index> | US Government Open Data (Public Domain with attribution) |
| **NASA POWER / GMAO MERRA-2 (`v5.12.4`)** | NASA LaRC / GMAO | <https://power.larc.nasa.gov/> · <https://doi.org/10.5067/8S35XF81C28F> | NASA Open Data Policy |
| **NASA NEX-GDDP-CMIP6 (`v2.0`)** | NASA NCCS | <https://doi.org/10.1038/s41597-022-01393-4> | Creative Commons Attribution 4.0 (`CC BY 4.0`) |
| **NASA GIBS WMTS & SVS CGI Moon Kit (`4720`)** | NASA EOSDIS / GSFC | <https://gibs.earthdata.nasa.gov/> · <https://svs.gsfc.nasa.gov/4720> | NASA Public Domain |
| **GRACE / GRACE-FO Mascons (`CSR RL06.03`)** | UT Austin CSR / NASA | <https://www2.csr.utexas.edu/grace/RL06_mascons.html> | Open scientific use with citation |
| **Hansen Global Forest Change `v1.12` (Landsat 30 m, 2000–2024)** | UMD GLAD / NASA / USGS | <https://glad.earthengine.app/view/global-forest-change> · <https://doi.org/10.1126/science.1244693> | Creative Commons Attribution 4.0 (`CC BY 4.0`) |
| **JRC Global Surface Water (Landsat 30 m, 1984–2021)** | European Commission JRC | <https://global-surface-water.appspot.com/> · <https://doi.org/10.1038/nature20584> | European Commission Reuse Policy (`CC BY 4.0` equivalent, free & open) |
| **NOAA OISST `v2.1` Daily $0.25^\circ$ & ERSST `v5` Monthly $2^\circ$** | NOAA NCEI / CoastWatch | <https://www.ncei.noaa.gov/products/optimum-interpolation-sst> · <https://www.ncei.noaa.gov/products/extended-reconstructed-sst> | US Government Work (Public Domain) |
| **NOAA IBTrACS `v04r01` Tropical Cyclone Best-Track Archive** | NOAA NCEI | <https://www.ncei.noaa.gov/products/international-best-track-archive> · <https://doi.org/10.25921/82ty-9e16> | US Government Work (Public Domain with citation) |
| **NOAA GHCN-Daily, GSOM & CPC Oceanic Niño Index (`ONI`)** | NOAA NCEI / CPC | <https://www.ncei.noaa.gov/cdo-web/> · <https://www.cpc.ncep.noaa.gov/> | US Government Work (Public Domain) |
| **NOAA Coral Reef Watch `v3.1` & OceanSODA-ETHZ `v2025`** | NOAA NESDIS / NCEI | <https://coralreefwatch.noaa.gov/> · <https://www.ncei.noaa.gov/data/oceans/ncei/ocads/data/0220059/> | US Government Work / Open Ocean Data with citation |
| **NSIDC Sea Ice Index `v4` (`G02135`) & Lake Ice Phenology (`G01377`)** | NOAA@NSIDC | <https://nsidc.org/data/g02135> · <https://noaadata.apps.nsidc.org/NOAA/G01377/> | NSIDC Open Data Policy (Public Domain / free use with attribution) |
| **USGS NWIS Streamflow (`09380000` Colorado River at Lees Ferry)** | US Geological Survey | <https://waterservices.usgs.gov/> | US Government Work (Public Domain) |
| **USDA NRCS SNOTEL Snowpack Network (`AWDB REST API v1`)** | USDA NRCS NWCC | <https://wcc.sc.egov.usda.gov/awdbRestApi/swagger-ui/index.html> | US Government Work (Public Domain) |
| **CHIRPS `v2.0` Precipitation ($0.05^\circ$ / $0.25^\circ$)** | UCSB Climate Hazards Center | <https://www.chc.ucsb.edu/data/chirps> · <https://doi.org/10.1038/sdata.2015.66> | Public Domain / Creative Commons (`CC BY 4.0` equivalent, free for all uses) |
| **CRU TS `v4.10` Gridded Precipitation ($0.5^\circ$, 1901–2025)** | Climatic Research Unit (UEA) | <https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/> · <https://doi.org/10.1038/s41597-020-0453-3> | Open Database License (`ODbL v1.0`) |
| **GPCC Full Data Monthly `v2025` ($0.5^\circ$ via NOAA PSL)** | DWD / NOAA PSL | <https://psl.noaa.gov/data/gridded/data.gpcc.html> | DWD GeoNutzV / Open scientific attribution |
| **GlaMBIE `1.0.0` Glacier Mass Balance (2000–2023)** | WGMS / GlaMBIE Consortium | <https://doi.org/10.5904/wgms-glambie-2024-07> · <https://doi.org/10.1038/s41586-024-08545-z> | Creative Commons Attribution 4.0 (`CC BY 4.0`) |
| **GTN-P Permafrost Borehole Temperatures (`PANGAEA.930669`)** | GTN-P / PANGAEA | <https://doi.org/10.1594/PANGAEA.930669> | Creative Commons Attribution 4.0 (`CC BY 4.0`) |
| **GFED5 Global Burned Area (MODIS Era, 2001–2020)** | GFED / Zenodo | <https://doi.org/10.5281/zenodo.7668424> | Creative Commons Attribution 4.0 (`CC BY 4.0`) |
| **PSMSL Revised Local Reference Tide-Gauge Records** | Permanent Service for Mean Sea Level | <https://psmsl.org/> | Open scientific use with attribution |
| **AAFC Terrestrial Ecozones of Canada (`Geo.ca`)** | Government of Canada | <http://geo.ca/> | Open Government Licence – Canada (`OGL-Canada v2.0`) |
| **Natural Earth 1:10m / 1:50m Cultural Vectors** | Natural Earth | <https://www.naturalearthdata.com/> | Public Domain (`CC0`) |
| **ECMWF IFS Open Forecast & Open-Meteo (Live Context Overlay)** | ECMWF / Open-Meteo | <https://doi.org/10.21957/open-data> | `CC BY 4.0` (ECMWF); Open-Meteo free non-commercial API terms |

---

### 4.3 Watersheds and national hydrology

The **Watersheds** map includes Nicaragua's published INETER/SINAPRED Pfafstetter vectors (2021 edition), complete source codes, and HydroBASINS levels 4 and 6 for all nine source regions. It provides original level-12 downloads, station readings with observation dates, and INETER/SINAPRED climate and natural-hazard catalogues. Reference maps and dated readings are kept distinct from detected climate trends.

See [sources, reproducible downloads, API refresh configuration and limitations](data/hidrologia/fuentes_y_limites.md). A static installation displays dated station snapshots; live station requests require the optional `clima_nic` read-only API. Source data retain their own licenses and are not relicensed under Apache 2.0.

## 5. Repository Structure

- `index.html`, `app/`, `src/`, `assets/`: Frontend web application (`Three.js` 3D globe, `Leaflet` 2D map, `Chart.js` time-series diagnostics, `Investigate`, `Watersheds`, `Learn`, `Help`, and `Sources` tabs).
- `backend/clima_nic/`: Python statistical engine (`estadistica/tendencia_robusta.py`, `estadistica/fdr.py`, `estadistica/indicadores.py`), dataset integrators (`recursos.py`, `recursos_americas.py`, `recursos_europa_africa.py`, `recursos_asia_oceania.py`), and FastAPI service (`api.py`).
- `data/`: Versioned JSON and compact CSV time series (`recursos_integrados.json`, `clima.json`, `fenomenos_nicaragua.json`, and `data/recursos/`), verified by SHA-256 hashes.
- `scripts/`: Build scripts (`preparar_render.mjs`, `preparar_meteo.mjs`), core trend contract (`scripts/datos/tendencia.py`), and SAR water-extent calibration (`scripts/sar/`).
- `tests/`: Automated test suite (unit, statistical, provenance and browser tests).
- `docs/`: Technical documentation, audit logs, and Space Apps submission package (`docs/entrega/`).

---

## 6. Team Credits, Prior Work & AI Disclosure

- **Team (Managua, Nicaragua — NASA Space Apps Challenge 2026):**
  - **Octavio Lizano** (`lizanooctavio-boop`) — Architecture, statistical engine, global/Nicaragua integration, and 3D/2D interface.
  - **Benjamin** (`benjaminhr8687`) — Americas & Caribbean observational series, SAR water-extent workflows, place search and coordinate systems, and submission package.
  - **Astral** (`AstralPiolinXD`) — Europe, Africa & Middle East observational series, in-app help and guided tour, audit verification, and data quality control.
  - **Manuel Paniagua** (`Manuel Paniagua`) — Land-surface hydrology (`GLDAS-2.1`, `AppEEARS`, `SMAP`) and regional diagnostics.
  - **Javi** (`JAVITHEARKHI`) — Asia, Oceania & ocean observational series, Watersheds map, geographic grid, and historical event context.
- **Prior Work Disclosure:** The 3D/2D meteorological base viewer and southwest Nicaragua bounding box (`caja_sicc`) adapt foundational components from the team's prior project `SICC-952` (documented in `data/contrato.md` Section 5). All statistical trend engines, multi-method verdicts, 217 regional/global climate investigations, 33 cross-checks, and educational modules were built specifically for `Earth System Trend Detective`.
- **AI / Super Intelligence (SI) Disclosure:** Developed with assistance from **Claude Code (Opus)**, **OpenAI Codex**, and **Google Gemini (Antigravity)** under human scientific direction and verified by the full automated test suite, independent series recalculations, and Crossref API DOI checks. Full details in [`docs/entrega/AI_USE.md`](docs/entrega/AI_USE.md).
- **License:** Original source code is released under the **Apache License 2.0** ([`LICENSE`](LICENSE), copyright notice in [`NOTICE`](NOTICE)); adapted CSA SAR tutorial scripts in `scripts/sar/` retain their original **MIT License** (`scripts/sar/LICENSE-CSA.txt`), and third-party datasets follow their respective open data licenses listed in Section 4.2.
