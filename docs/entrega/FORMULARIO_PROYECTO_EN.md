# NASA Space Apps Challenge 2026 — Project Submission Form Draft

> **Language**: English (required by Space Apps 2026 submission rules).  
> **Review status**: Ready-to-paste draft grounded exclusively in repository measurements across `codex/verificacion-entrega`, `codex/recursos-interfaz`, `codex/recursos-csa-rcm`, `codex/recursos-contraste`, and `codex/recursos-tierra-v2` as of `2026-11-13`. Fields marked `[ENLACE]`, `[CONFIRMAR]`, or `[VERIFICAR]` must be completed by the team before clicking **Submit for Judging** (deadline: Sunday `2026-11-15` at `23:59` Managua local time).

---

## 1. Project Name
**Earth Trend Detective** *(subtitle optional: Multi-Source Climate Evidence for Nicaragua & Canadian Prairies)* `[CONFIRMAR]`

## 2. Tagline
*An open statistical detective board that cross-checks NASA and partner Earth observations to test what is changing, where, by how much, and when datasets disagree.* `[CONFIRMAR]`

## 3. High-Level Project Summary
Environmental shifts rarely announce themselves through a single clean curve—short records, shifting station networks, and reanalysis artifacts can easily mimic or hide real change. **Earth System Trend Detective** pairs a rigorous time-series statistical backend with an interactive web interface (**Investigate**, **Learn**, and **Sources**) anchored on two contrasting domains: tropical Mesoamerica centered on **Nicaragua** (~119,900 km²) and the continental **Canadian Prairies** ecozone (467,128 km²).

Instead of stopping at raw slopes, our tool enforces a strict five-verdict system—including ***"Not enough evidence of a trend"*** (which never means "no change"), ***"Methods disagree"***, ***"Cross-check discrepancy"***, and ***"Pending / unvalidated"***. Across 1981–2024, NASA GISTEMP v4 detects robust surface warming in Nicaragua (+0.2939 °C/decade, `[0.2169, 0.3741]`), while 2001–2024 GPM IMERG rainfall lacks enough evidence for a monotonic regional trend and shows strong ENSO coupling (`r = -0.561` in June–November). Cross-checking exposes critical surprises: NASA POWER diverges sharply from GISTEMP and IMERG (`2005` jump), and GLDAS Noah v2.1 detects top-layer drying in Central Nicaragua (`-0.0090 m³/m³/decade`) and the Canadian Prairies (`-0.0139 m³/m³/decade`) where MERRA-2 soil moisture rises instead. Future CMIP6 projections (NEX-GDDP-CMIP6 v2.0, 2041–2060) and open workflows make every limitation inspectable.

---

## 4. How Our Project Addresses the Challenge ("Be an Earth System Trend Detective!")

### What is changing (and what does *not* show enough evidence yet)?
- **Surface Air Temperature**: Using NASA GISTEMP v4 (`1981–2024`, 44 years), annual temperature anomalies in Nicaragua increased significantly at **+0.2939 °C/decade** (Theil–Sen slope, 95% CI `[0.2169, 0.3741]`, Pettitt change point in `2003`, `p = 0.0`). In the common satellite era (`2001–2024`), Nicaragua warmed at **+0.3977 °C/decade** (`[0.2099, 0.5370]`, modified Mann–Kendall `p = 0.0001`), whereas the **Canadian Prairies** show wide year-to-year swings (`-0.29 °C` to `+2.68 °C`, mean `+1.152 °C`) and a Sen slope of **+0.1751 °C/decade** (`[-0.5684, +0.7535]`, modified MK `p = 0.6374`)—classified honestly as **"Not enough evidence of a trend"** (which does *not* prove absence of warming, given high interannual variance over 24 years).
- **Precipitation & ENSO Modulation**: In GPM IMERG V07B (`2001–2024`), Nicaragua averages `2,094.1 mm/year` with a negative Sen slope (`-64.923 mm/decade`, `[-233.240, 98.283]`, MK `p = 0.4419`) and the `caja_sicc` sub-box (~66,500 km², 62% Nicaragua) shows `-28.705 mm/decade` (MK `p = 0.785`): both return **Not enough evidence of a trend**. Strong El Niño–Southern Oscillation variability drives June–November rainfall (`r = -0.561` for Nicaragua, `r = -0.591` for `caja_sicc` vs. NOAA ONI, `n = 24`). In contrast, Costa Rica displays **Methods disagree**: OLS detects `-201.224 mm/decade` (`p = 0.028`, HAC CI `[-332.359, -70.089]`), while non-parametric Sen/MK gives `-168.3861 mm/decade` (`[-369.4922, +20.814]`, `p = 0.0965`).
- **Dataset Cross-Checks as First-Class Findings**:
  - **GPCC v2025 vs. CRU TS 4.10 vs. IMERG**: GPCC closely tracks IMERG in Nicaragua (`-79.2 mm/decade`, `r = 0.94`, partly sharing gauge inputs), whereas CRU TS 4.10 diverges (`-21.3 mm/decade`, `r = 0.63`) as underlying stations drop from `3.7` to `1.8` after `2015`.
  - **NASA POWER / MERRA-2 Divergence**: On Nicaragua (`1981–2024`), POWER yields `+329.0 mm/decade` with an abrupt Pettitt jump in `2005` (`+819.9 mm`, `p = 0.0`) and a slight cooling slope (`-0.1051 °C/decade`, Pettitt `1999`, `p = 0.0077`)—contradicting GISTEMP's `+0.2939 °C/decade` warming and flagging reanalysis inhomogeneity rather than real cooling.
  - **Soil Moisture (GLDAS v2.1 vs. MERRA-2)**: Across 30 cloud OPeNDAP series (`GLDAS_NOAH025_M 2.1`, water-balance closure residual `0.7–2.6%`), top-layer soil moisture (`0–10 cm`) declines significantly in **Central Nicaragua** (`-0.0090 m³/m³/decade`) and the **Canadian Prairies** (`-0.0139 m³/m³/decade`, Pettitt shift `2011–2013`, flagged with an AGRMET forcing-change caveat), while national Nicaragua sits at **Methods disagree** (`-0.0071 m³/m³/decade`). Meanwhile, MERRA-2 `GWETTOP`/`GWETROOT` shows opposite positive trends (`+0.048/decade` in Nicaragua, `r = -0.03 to 0.36` vs. GLDAS).
- **Lakes, Coastal Water & Pending Tasks**:
  - **Lake Cocibolca Water Level**: G-REALM altimetry (`000351`, full years `1993–2025`) measures `+0.11 m/decade` (`[-0.01, +0.23]`, *Not enough evidence*); SWOT Hydrocron (`41` months) shows tight correlation (`r = 0.99`, `-0.437 m` datum offset) and is labeled strictly as a **short-record demonstration** (`demostracion_registro_corto`).
  - **Coastal Chlorophyll-a (MODIS-Aqua, 2003–2024)**: Gulf of Fonseca registers `Methods disagree` (`+0.68`, MK `p = 0.08`, vs. raw monthly OLS `+1.21`, `p = 0.0007` per the NASA NTRS coastal methodology) and fails the `<= 1 mg/m³` optical threshold (`7.0 mg/m³`); three Caribbean river mouths stay below `0.92 mg/m³` with *Not enough evidence*.
  - **Transparent Incomplete Queues**: MODIS single-point NDVI (`MOD13Q1`, Central `-0.0432` in UI summary / `-0.0438` in table `[CONFIRMAR unificación]`), 37 OPERA DSWx-S1 (`2,585.25 km²` common water extent, `33.05%` of Lake Cocibolca) and 75 OPERA RTC-S1 bursts remain tagged `NO_VALIDADA`; 2 CSA RCM Public Good scenes (`Order #3787605`) remain queued (`SUBMITTED`); and `160` AppEEARS tasks (SMAP L4 & MODIS C6.1) currently sit at `0` completed (`158` Pending, `2` Processing).
- **Near-Term Projections (NEX-GDDP-CMIP6 v2.0, 2041–2060 vs. 1995–2014, 6 GCMs)**:
  - Nicaragua median warming reaches **+1.399 °C** under `ssp245` (`+1.073 to +1.735 °C`, `6/6` models warmer) and **+1.980 °C** under `ssp585` (`+1.255 to +2.134 °C`, `6/6` warmer), alongside median annual rainfall shifts of **-5.446%** (`ssp245`) and **-10.488%** (`ssp585`).

---

## 5. Benefits & Impact
- **Separates signal from statistical illusion**: Protects analysts, local planners, and students from treating short records, autocorrelation, or dataset jumps as confirmed long-term climate trends.
- **Actionable uncertainty framing**: Explicitly preserves the distinction between *Not enough evidence of a trend* (insufficient statistical power or high variability) and *no change*, and flags reanalysis/station-drop discrepancies directly in the interface.
- **Educational transferability**: The **Learn** tab turns abstract concepts (Sen vs. OLS, autocorrelation inflation of false positives, Pettitt change-points, spatial FDR `q = 0.10`, and why 40-month SWOT series are calibration—not trend—records) into interactive intuition.
- **Regional contrast beyond local anecdotes**: Contrasting tropical ENSO-sensitive watersheds in Nicaragua against continental agricultural plains in the Canadian Prairies (`r = 0.830` precipitation and `r = 0.961` temperature correlation against 3 Saskatchewan GSOM stations) demonstrates generalizable detective methodology without making operational hazard claims on unvalidated SAR products.

---

## 6. Detailed Project Description — How It Works
1. **Data Acquisition & Regional Aggregation (`scripts/datos/`, `scripts/sar/`)**:
   - Python extractors retrieve official satellite, reanalysis, altimetry, ecozone, and station time series via NASA GES DISC (`OPeNDAP` / `earthaccess`), ORNL DAAC REST, NASA POWER, PO.DAAC Hydrocron, ASF Search (`OPERA RTC-S1` / `DSWx-S1`), NCEI, PSL, UEA CRU, and EODMS (`RCM` queue).
   - Regional clipping uses exact polygons (`Natural Earth 10m` for Central America; `AAFC/Geo.ca` Terrestrial Ecozones for `CAN_prairies`, `467,128 km²`).
2. **Statistical Trend Engine (`backend/clima_nic/estadistica/`)**:
   - Every continuous series runs through multiple complementary estimators instead of one p-value threshold:
     - **OLS** with autocorrelation-adjusted effective degrees of freedom;
     - **Newey–West HAC** heteroskedasticity- and autocorrelation-consistent standard errors;
     - **Theil–Sen** median slope with bootstrap confidence intervals;
     - **Classic & Hamed–Rao Modified Mann–Kendall** tests accounting for serial persistence;
     - **Pettitt Change-Point Test** to spot abrupt inhomogeneities (such as station drops or assimilation shifts);
     - **Spatial Benjamini–Hochberg FDR (`q = 0.10`)** across gridded climate extremes (`prcptot 57/57`, `rx1day 52`, `r95p 57`, `tmax_media 43/44`, `tmin_media 26/29`, `tx90p 43`).
   - Built-in automated test suite (`pytest`) validates every statistical verdict path.
3. **Interactive Web Interface (`index.html`, `app/investigar.js`, `src/`, `data/`)**:
   - **Investigate**: Region vs. contrast workspace (`Nicaragua vs. Canadian Prairies` and subregions) with synchronized trend plots, confidence bounds, Pettitt markers, and side-by-side cross-check verdicts.
   - **Learn**: Plain-language visual explainers on statistical validity, dataset caveats, and common pitfalls (no hype, no false certainty).
   - **Sources**: Structured registry tracing dataset versions, coverage windows, verification status (`verificado`, `demostracion_registro_corto`, `NO_VALIDADA`, `pendiente`), and DOIs/terms of use.

---

## 7. Tools, Coding Languages, Hardware & Libraries
- **Programming Languages & Architecture**: Python 3 (`scripts/datos/`, `scripts/sar/`, `backend/clima_nic/`), FastAPI + Uvicorn (local analytical API), Vanilla JavaScript + HTML5 + CSS3 (static frontend, zero heavy framework lock-in), Node.js helper scripts (`scripts/preparar_render.mjs`, `scripts/preparar_meteo.mjs`).
- **Python Libraries**: `numpy`, `scipy`, `shapely`, `pyproj`, `h5py`, `requests`, `rasterio`, `fastapi`, `uvicorn`, `httpx`, `pytest`, `earthaccess`, `asf-search`, `scikit-learn`.
- **Frontend Libraries**: `Three.js` (`three@0.160.0` WebGL globe), `Leaflet` (`1.9.4` interactive spatial maps), `Chart.js` (`4.4.1` time-series & diagnostic plots).
- **Hardware**: Standard team laptops / local workstations + NASA Earthdata Cloud / GES DISC OPeNDAP and AppEEARS cloud processing queues (no custom proprietary hardware required).

---

## 8. Use of Super Intelligence (SI / AI Tools) & Prior Work Disclosure

### Use of Super Intelligence (SI)
In accordance with NASA Space Apps 2026 transparency rules, our team discloses all AI assistance used across the hackathon:
- **Tools used**: `Claude Code (Opus)`, `Codex`, `Claude Opus`, and `Gemini` (`[CONFIRMAR]` exact platform versions and whether any AI-generated audio/video voiceover or visual asset is used in the final demo).
- **Role in the project**: Code scaffolding, Python/JS refactoring, statistical edge-case verification, documentation drafting, accessibility auditing, and bilingual translation/editing.
- **Human ownership**: Concept origination, challenge strategy, regional and contrast hypotheses, dataset selection, statistical validation standards, and all final design/scientific decisions belong exclusively to the human team.
- **Demo SI compliance rule**: Any AI-generated visual or voice content (if included in the final video/slides, e.g., TTS narration or generated imagery) will display a clear **visible watermark**, be explicitly declared in this form, and keep attribution in exported file metadata. Zero NASA/CSA/NOAA emblems or logos are generated or inserted.

### Pre-Event Work Disclosure (Participant FAQs Compliance)
- Portions of the underlying weather viewer infrastructure build upon the team's prior open-weather interface (`SICC-952`, `[CONFIRMAR]` original scope and license), and initial repository commits occurred slightly prior to opening day (`2026-11-11` to `2026-11-13` UTC-6, starting at commit `f5fad37` on `2026-11-11T22:34:36-06:00`). All Space Apps–specific multi-dataset integration (`GLDAS`, `OPERA`, `SWOT`, `G-REALM`, `Canadian Prairies` cross-check), statistical detective verdict engine, **Investigate / Learn / Sources** workflow, and documentation package were developed and documented for this challenge; prior components are transparently noted here and in `docs/entrega/REQUISITOS_ENTREGA_2026.md`. `[CONFIRMAR]`

---

## 9. NASA Data (With Citations & DOIs)
- **GPM IMERG Final Run V07B (`GPM_3IMERGM` `07` / `GPM_3IMERGDF` `07`)** — NASA GES DISC; Huffman et al. (2023), DOI `10.5067/GPM/IMERG/3B-MONTH/07`, `10.5067/GPM/IMERGDF/DAY/07`.
- **GISTEMP Surface Temperature Analysis `v4`** — NASA GISS; Lenssen et al. (2024), DOI `10.1029/2023JD040179`, https://data.giss.nasa.gov/gistemp/ (`[VERIFICAR]` Hansen et al. 2010 citation text).
- **GLDAS Noah Land Surface Model `2.1` (`GLDAS_NOAH025_M 2.1`)** — NASA GES DISC; Beaudoing & Rodell (2020), DOI `10.5067/SXAVCZFAQLNO`.
- **MERRA-2 (`5.12.4`: `M2TMNXOCN`, `M2IMNPASM`, `M2TMNXLND`)** — NASA GMAO / GES DISC; DOIs `10.5067/4IASLIDL8EEC`, `10.5067/2E096JV59PK7`, `10.5067/8S35XF81C28F`.
- **NASA POWER (`v10` docs / Daily API `v2.10.3`)** — NASA LaRC; https://power.larc.nasa.gov/docs/.
- **MODIS Collection `6.1` (`MOD13Q1.061` via ORNL DAAC REST; queued AppEEARS: `MOD11A2.061`, `MOD16A2GF.061`, `MOD13A3.061`, `MCD12Q1.061`)** — NASA LP DAAC / ORNL DAAC; DOIs `10.5067/MODIS/MOD13Q1.061`, `10.5067/MODIS/MOD11A2.061`, `10.5067/MODIS/MOD16A2GF.061`, `10.5067/MODIS/MOD13A3.061`, `10.5067/MODIS/MCD12Q1.061`.
- **SMAP Level 4 (`SPL4SMGP v008` in AppEEARS queue; `v007` adapter)** — NASA NSIDC DAAC; DOI `10.5067/T5RUATAQREF8`.
- **GRACE/GRACE-FO Mascon CRI (`RL06.3 V4`, code adapter)** — NASA JPL / PO.DAAC; Wiese et al. (2019), DOI `10.5067/TEMSC-3JC634`.
- **OBPG MODIS-Aqua L3m Chlorophyll-a (`2022.0`)** — NASA OB.DAAC; DOI `10.5067/AQUA/MODIS/L3M/CHL/2022`.
- **G-REALM Global Reservoir & Lake Monitoring (Lake Cocibolca `000351`)** — NASA GSFC / USDA; https://earth.gsfc.nasa.gov/gwm/lake/Index.
- **SWOT L2 HR LakeSP (`2.0`, Ver `C`, via PO.DAAC Hydrocron)** — NASA JPL / CNES / PO.DAAC; DOI `10.5067/SWOT-LAKESP-2.0`.
- **OPERA RTC-S1 (`OPERA_L2_RTC-S1_V1`) & OPERA DSWx-S1 (`OPERA_L3_DSWX-S1_V1`)** — NASA JPL / ASF DAAC & PO.DAAC; DOIs `10.5067/SNWG/OPERA_L2_RTC-S1_V1`, `10.5067/OPDSWS1-L3V1`.
- **NEX-GDDP-CMIP6 (`v2.0`)** — NASA NCCS; Thrasher et al., DOI `10.1038/s41597-022-01393-4`, dataset DOI `10.7917/OFSG3345`.
- **NASA NTRS Technical Report `20090042747`** (*Time-Series Analysis of Remotely-Sensed SeaWiFS Chlorophyll in River-Influenced Coastal Regions*, *EARSeL eProceedings* 8(2), 2009) — https://ntrs.nasa.gov/api/citations/20090042747 (`[VERIFICAR]` exact author list from PDF).
- **NASA GIBS WMTS & NASA SVS CGI Moon Kit (`4720`)** — NASA EOSDIS / GSFC (visual globe base layers).

---

## 10. Space Agency Partner Data & Other Resources
- **Canadian Space Agency (CSA)**: RADARSAT Constellation Mission (`RCM`, Public Good EODMS Order `#3787605` — queued `SUBMITTED`, EULA pending review, zero raw scenes stored) and **CSA SAR Python Tutorial** (MIT License in `scripts/sar/LICENSE-CSA.txt`).
- **Agriculture and Agri-Food Canada (AAFC / Geo.ca)**: Terrestrial Ecozones of Canada (`CAN_prairies`, 467,128 km²), Open Government Licence - Canada.
- **Climatic Research Unit (UEA)**: `CRU TS 4.10` (`ODbL / DbCL`); Harris et al. (2020), DOI `10.1038/s41597-020-0453-3`.
- **DWD / NOAA PSL**: `GPCC Full Data Monthly v2025` (`0.50°`), https://psl.noaa.gov/data/gridded/data.gpcc.html.
- **NOAA NCEI & CPC**: `GHCN-Daily v3` (DOI `10.7289/V5D21VHZ`, `10.1175/JTECH-D-11-00103.1`), `GSOM 1.0` (`3` Saskatchewan stations), and `CPC ONI v5`.
- **Natural Earth**: `10m` country boundary vectors (Public Domain, https://www.naturalearthdata.com/about/terms-of-use/).
- **Statsig**: Statistical reference on multiple testing / FDR control (https://statsig.com/terms).
- **SINAPRED (Nicaragua)**: Links & factual summaries of 4 public event bulletins for event cross-checks (`sinapred.gob.ni`, no redistribution license verified; originals excluded).
- **Legacy/External Weather Layers**: Open-Meteo / ECMWF IFS `0.25°` (DOI `10.21957/open-data`, `CC BY 4.0`; Open-Meteo non-commercial terms) and RainViewer API (personal/educational terms — `[CONFIRMAR]` retention vs. removal in `PROPUESTAS.md`).

---

## 11. Public Links (Checklist Before Submission)
- **Public GitHub Repository**: `[ENLACE]` *(currently returns HTTP `404` as private; must be switched to public and include root `LICENSE` after secret scan: `https://github.com/lizanooctavio-boop/NASA-CHALLENGE` `[CONFIRMAR]`)*
- **Live Interactive Demo URL** *(verify accessibility under corporate firewalls / FortiGuard & HTTPS without login)*: `[ENLACE]`
- **Project Demo (`<= 30 seconds` video OR `<= 7 slides` PDF/deck — pick one official format)**: `[ENLACE]` `[CONFIRMAR]`
- **Challenge Team & Local Event (Same Managua Site Verified for All Members)**: `[CONFIRMAR]`
