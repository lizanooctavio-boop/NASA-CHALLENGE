# NASA Space Apps Challenge 2026 — Project Submission Form

> **Idioma del formulario:** Inglés obligatorio (*Project Submission Guide*).  
> **Estructura de este archivo:** La **Parte 1** contiene únicamente texto limpio en inglés listo para copiar y pegar en la plataforma (sin nombres de ramas, hashes de commits, rutas internas de carpetas ni notas de coordinación). Todas las acciones, enlaces y confirmaciones pendientes del equipo se encuentran aparte en la **Parte 2 (`Pendiente del equipo`)**.

---

## Parte 1: Bloques limpios listos para pegar (English)

### 1. Project Name
**Earth Trend Detective**

### 2. Tagline
An open statistical detective platform that cross-checks NASA and partner Earth observations to reveal what is changing, where, by how much, and why datasets sometimes disagree.

### 3. High-Level Project Summary
Environmental shifts rarely announce themselves through a single clean curve—short satellite records, changing weather-station density, El Niño cycles, and reanalysis jumps can easily mimic or mask real climate change. **Earth Trend Detective** pairs a conservative multi-method trend engine with an interactive web application (**Investigate**, **Learn**, and **Sources**) anchored on two sharply contrasting domains: tropical Central America centered on **Nicaragua** (~119,900 km²) and the continental **Canadian Prairies** ecozone (~467,128 km²).

Instead of stopping at one naive p-value, every series is evaluated across complementary linear and non-parametric estimators to produce three statistical trend verdicts—***Trend detected***, ***Not enough evidence of a trend*** (which never means "no change"), and ***Methods disagree***—guarded by explicit data-sufficiency rules (***Not enough data for a trend test*** / ***Record too short for a trend test*** for records under 10 years, and ***Not validated*** for uncalibrated radar flood thresholds) alongside independent **Cross-checks**. Across 1981–2024, NASA GISTEMP v4 detects robust surface warming in Nicaragua (+0.294 °C/decade, 95% CI `[0.217, 0.374]`, Mann–Kendall p < 0.001), whereas 2001–2024 GPM IMERG rainfall returns *Not enough evidence of a trend* alongside strong ENSO modulation (r = −0.561 in June–November). Cross-checking turns conflicting measurements into scientific clues: NASA POWER diverges sharply from GISTEMP and IMERG with abrupt reanalysis steps, GLDAS Noah v2.1 surface soil moisture diverges from MERRA-2 wetness indices (`r = 0.025` nationally), Aura OMI tropospheric NO₂ declines similarly over urban Managua and a rural control box, and open-Pacific chlorophyll contrasts sharpen interpretation of turbid Gulf of Fonseca waters.

### 4. How Our Project Addresses the Challenge ("Be an Earth System Trend Detective!")

#### What is changing (and what does not show enough evidence yet)?
- **Surface Air Temperature**: Using NASA GISTEMP v4 (1981–2024, 44 years), annual temperature anomalies in Nicaragua increased significantly at **+0.294 °C/decade** (Theil–Sen slope, 95% CI `[+0.217, +0.374]`, Pettitt step change detected in 2003, p < 0.001). Over the common satellite window (2001–2024), Nicaragua warmed at **+0.398 °C/decade** (95% CI `[+0.210, +0.537]`, modified Mann–Kendall p < 0.001). Over the exact same 2001–2024 period, the **Canadian Prairies** span −0.289 °C to +2.675 °C (mean +1.152 °C) with a Sen slope of **+0.175 °C/decade** (95% CI `[−0.568, +0.754]`, modified MK p = 0.637)—yielding ***Not enough evidence of a trend*** because mid-latitude year-to-year variability overwhelms a 24-year window (not proof of zero warming). As a third free-troposphere/surface cross-check over 2003–2024, NASA **AIRS v7** (`AIRS3STM`) tracks GISTEMP (`r = 0.924`) and NASA POWER (`r = 0.817`) closely in interannual swings and yields an annual Sen slope of **+0.126 °C/decade** (*Trend detected*, MK p = 0.010), roughly one-third of GISTEMP's +0.381 °C/decade over 2003–2024; however, raw monthly AIRS OLS (+0.137 °C/decade, p = 0.073) and monthly Theil–Sen (95% CI `[−0.012, +0.250]`) do not cross significance, so AIRS supports the warming sign and year-to-year timing rather than GISTEMP's warming rate.
- **Precipitation, ENSO Coupling & Area-Average Verification**: In NASA GPM IMERG Final V07B (2001–2024), Nicaragua averages 2,094.1 mm/year with a negative Sen slope (−64.9 mm/decade, 95% CI `[−233.2, +98.3]`, MK p = 0.442), and a southwest Nicaragua study box (~66,500 km²) averages 2,230.9 mm/year at −28.7 mm/decade (MK p = 0.785)—both returning ***Not enough evidence of a trend***. June–November rainfall correlates strongly with NOAA CPC Oceanic Niño Index (`r = −0.561` nationally, `r = −0.591` in the southwest box, n = 24). By contrast, Costa Rica over 2001–2024 returns ***Methods disagree***: OLS estimates −201.2 mm/decade (p = 0.028), whereas Theil–Sen estimates −168.4 mm/decade (95% CI `[−369.5, +20.8]`, MK p = 0.097). Independent GES DISC Cloud OPeNDAP area-averaging reproduces the southwest study box virtually identically (`r = 1.000`, −28.7 vs. −28.7 mm/decade) and agrees closely over Nicaragua (`r = 0.999`, −52.3 vs. −64.9 mm/decade; −25.0 mm/year mean offset from including interior lake cells).
- **Dataset Disagreements as First-Class Evidence**:
  - **GPCC v2025 vs. CRU TS 4.10 vs. IMERG**: GPCC closely mirrors IMERG over Nicaragua (−79.2 mm/decade, `r = 0.94` because gauge inputs inform IMERG calibration), whereas CRU TS 4.10 diverges (−21.3 mm/decade, `r = 0.63`) as active Nicaraguan gauge density drops from 3.7 to 1.8 stations after 2015, and local GHCN-Daily precipitation records halt around 1989–1991.
  - **NASA POWER / MERRA-2 Divergence**: Over 1981–2024 in Nicaragua, NASA POWER precipitation climbs artificially (+329.0 mm/decade) around an abrupt 2005 Pettitt break (+819.9 mm, p < 0.001), while surface temperature shows a negative slope (−0.105 °C/decade, Pettitt break in 1999, p = 0.008)—exposing reanalysis inhomogeneity rather than physical cooling.
  - **Soil Moisture (GLDAS v2.1 vs. MERRA-2 `GWETTOP`)**: Across 30 GES DISC Cloud OPeNDAP series (GLDAS-2.1 Noah 0.25° monthly, water-balance closure residual 0.7–2.6%), top-layer soil moisture (0–10 cm, m³/m³) shows a negative slope across Nicaragua (−0.0071 m³/m³/decade, *Methods disagree*, MK p = 0.050), statistically clear drying in **Central Nicaragua** (−0.0090 m³/m³/decade, *Trend detected* over 2001–2024, MK p = 0.040, Pettitt step change in 2013, p = 0.026) and the **Canadian Prairies** (−0.0139 m³/m³/decade, 95% CI `[−0.0232, −0.0029]`, MK p = 0.008, Pettitt step in 2015, p = 0.011). Crucially, Central Nicaragua's verdict weakens to ***Methods disagree*** when 2001–2002 are excluded (−0.0086 m³/m³/decade, MK p = 0.042) and carries an explicit AGRMET forcing-transition caveat (2008+/post-2011), whereas the Canadian Prairies drying verdict persists without 2001–2002. Over Nicaragua, MERRA-2 surface wetness (`GWETTOP`, a dimensionless 0–1 index over 0–5 cm plotted as standardized anomalies due to differing depth and units) trends positive (+0.048/decade nationally, +0.063/decade Central, *Trend detected*) with near-zero annual correlation against GLDAS (`r = 0.025` nationally, `r = 0.075` Central; `r = −0.034` to `+0.355` across all Nicaraguan regions and depths).
  - **Urban vs. Rural Tropospheric NO₂ (`Aura OMI OMNO2d v003`, 2005–2024)**: Column NO₂ over urban Managua (mean 0.745 × 10¹⁵ molecules/cm², 1.52× the rural Chontales control box at 0.490 × 10¹⁵) yields −0.043 × 10¹⁵ molecules/cm²/decade (*Trend detected*, MK p = 0.035), yet rural Chontales shows virtually the same decline (−0.049 × 10¹⁵/decade, *Methods disagree*, MK p = 0.056; `r = 0.366`). Because both urban and rural boxes drift downward at nearly identical rates, satellite NO₂ alone cannot isolate a Managua-specific emission change from regional background drift, cloud screening, or sensor row-anomaly effects.
  - **Coastal Chlorophyll-a Trap (MODIS-Aqua R2022.0, 2003–2024)**: Applying naive monthly OLS to Gulf of Fonseca chlorophyll-a reproduces an apparently dramatic upward trend (+1.21 mg/m³/decade, p < 0.001, matching the NASA NTRS monthly coastal approach by Acker et al., 2009), yet deseasonalizing to annual means reduces the signal to *Methods disagree* (+0.679 mg/m³/decade, MK p = 0.080)—and Gulf mean chlorophyll (7.02 mg/m³) fails the 1 mg/m³ Case-1 optical water threshold. Evaluating an adjacent **open Pacific** box (100% of 144 pixels <= 1 mg/m³, mean 0.436 mg/m³) gives −0.060 mg/m³/decade (MK p = 0.128, *Not enough evidence*), which is **consistent with** inner-Gulf optical turbidity and sediment interference rather than true phytoplankton trend acceleration. Three Caribbean river mouths stay below 0.92 mg/m³ (Coco and Grande de Matagalpa: *Not enough evidence*; Escondido/Bluefields: *Methods disagree* at +0.095, MK p = 0.071).
- **Lakes, Radar Water Extent, Vegetation & Projections**:
  - **Lake Altimetry**: NASA/USDA G-REALM altimetry for Lake Cocibolca (1993–2025 full years) measures +0.11 m/decade (`[−0.01, +0.23]`, *Not enough evidence*). SWOT Hydrocron (2023–present, ~41 overlapping months) correlates closely with G-REALM (`r = 0.990`, −0.437 m offset) and is strictly guarded as ***Record too short for a trend test***.
  - **SAR Water Mapping**: 75 OPERA RTC-S1 bursts and 37 OPERA DSWx-S1 tiles over Lakes Cocibolca and Xolotlán (2,585.25 km² common water extent = 33.05% of Lake Cocibolca) carry a hard ***Not validated*** (`NO_VALIDADA`) tag until independent field validation and queued CSA RADARSAT Constellation Mission (RCM) scenes complete processing.
  - **Vegetation Exploratory Sample & Pending Queues**: A single-site MODIS (`MOD13Q1 C6.1`, 2000–2024) sample in Central Nicaragua shows −0.0432 NDVI/decade (MK p < 0.001), explicitly caveated as a localized single-site signal lacking a regional unchanged-land-cover mask while 160 regional AppEEARS jobs (MODIS C6.1 + SMAP L4) remain queued without fabricated placeholder numbers.
  - **Climate Projections (NASA NEX-GDDP-CMIP6 v2.0, 2041–2060 vs. 1995–2014, 6 GCMs)**: Nicaragua 20-year median warming reaches **+1.399 °C** under SSP2-4.5 (+1.073 to +1.735 °C) and **+1.980 °C** under SSP5-8.5 (+1.255 to +2.134 °C, 6/6 models warmer), alongside median annual precipitation changes of **−5.45%** (SSP2-4.5) and **−10.49%** (SSP5-8.5, 6/6 models drier), with explicit warning that ENSO swings continue above and below long-term averages.

### 5. Benefits & Impact
- **Replaces False Certainty with Evidence Discipline**: Prevents analysts, journalists, educators, and planners from mistaking seasonal autocorrelation, short sensor lifetimes, gauge dropouts, or assimilation jumps for verified climate trends.
- **Makes *"Not Significant"* Constructive**: Clearly separates statistical power limits (*Not enough evidence of a trend*) from claims of safety or zero change—vital in regions where station records have gaps and ENSO creates multi-year precipitation swings.
- **Accessible Pedagogy**: The interactive **Learn** section transforms statistical safeguards (Theil–Sen vs. OLS, autocorrelation inflation, Type II error, Pettitt step breaks, Benjamini–Hochberg false discovery control) into short visual lessons tied to real regional examples.
- **Scalable Detective Pattern**: Pairing tropical Central America against the continental Canadian Prairies (`r = 0.830` precipitation and `r = 0.961` temperature agreement between satellite/gridded records and 3 Saskatchewan NOAA GSOM stations) demonstrates a reproducible verification workflow applicable to any watershed or ecozone.

### 6. Detailed Project Description — How It Works
1. **Multi-Source Ingestion & Transparent Queues**: Automated Python clients pull verified satellite, reanalysis, station, altimetry, and projection records via NASA Earthdata/GES DISC OPeNDAP, ORNL DAAC, PO.DAAC Hydrocron, ASF Search, NASA POWER, NOAA NCEI/CPC, NOAA PSL GPCC, UEA CRU, and NRCan EODMS. Boundaries come from Natural Earth 10m polygons and AAFC/Geo.ca Terrestrial Ecozones of Canada (~467,128 km² Canadian Prairies). Queued jobs (160 AppEEARS requests and 2 queued CSA RCM scenes) are tracked by status without inventing results.
2. **Multi-Method Trend Engine**: Each continuous annual series (>= 10 years) passes through:
   - Ordinary Least Squares (OLS) with AR(1)-adjusted effective degrees of freedom (Santer et al., 2000);
   - OLS with Newey–West HAC standard errors;
   - Non-parametric Theil–Sen slope with 95% confidence intervals (`scipy.stats.theilslopes`), verified under ±3-year window shifts and leave-one-year-out checks;
   - Classic and Hamed–Rao (1998) modified Mann–Kendall rank test;
   - Descriptive Pettitt (1979) change-point detection to flag step inhomogeneities;
   - Spatial Benjamini–Hochberg FDR (`q = 0.10`) over 57 Nicaraguan extreme-index grid cells (57/57 cells pass FDR for total precipitation and R95p; 52/57 for Rx1day; 43/57 for mean maximum temperature and warm days TX90p; 26/57 for mean minimum temperature).
3. **Interactive Web Platform**:
   - **Investigate**: Guided Topic -> Place -> Variable selector, automated verdict card, interactive Chart.js plots, side-by-side Cross-checks, guided tours (*Nicaragua vs. Canadian Prairies*), and one-click CSV/JSON downloads with citation metadata.
   - **Learn & Sources**: Plain-English statistical guides alongside versioned source provenance, operational caveats, and license disclosures.
   - **3D Globe to 2D Map**: Three.js WebGL sphere transitioning seamlessly into Leaflet 2D layers with NASA GIBS imagery, ENSO phase, NHC cyclones, and live meteorological overlays.

### 7. Tools, Coding Languages, Hardware & Libraries
- **Languages & Runtime**: Python 3, Vanilla JavaScript (ES Modules), HTML5, CSS3, Node.js helper build utilities.
- **Backend & Science Libraries**: `numpy`, `scipy`, `shapely`, `pyproj`, `h5py`, `rasterio`, `requests`, `httpx`, `fastapi`, `uvicorn`, `pytest`, `earthaccess`, `asf-search`, `scikit-learn`.
- **Frontend Libraries**: `Three.js` (`0.160.0`), `Leaflet` (`1.9.4`), `Chart.js` (`4.4.1`).
- **Hardware & Infrastructure**: Standard developer laptops/workstations and public Earth-observation cloud APIs (NASA Earthdata / GES DISC Cloud OPeNDAP / PO.DAAC Hydrocron / AppEEARS); no specialized local hardware required.

### 8. Use of Super Intelligence (SI) & Development Timeline Disclosure

#### Use of Super Intelligence (SI) Tools
Our team directed the scientific framing, challenge hypotheses, statistical acceptance rules, dataset vetting, and final review, while utilizing Super Intelligence (SI) software assistants—**Claude Code (Opus)**, **Codex**, **Claude Opus**, and **Gemini**—for Python data-ingestion modules, statistical test scaffolding, frontend JavaScript/CSS implementation, accessibility auditing, and English/Spanish documentation drafting. All quantitative results shown in the application and submission were verified against executed code and primary data portals; neither the web interface nor our demo visuals include NASA, CSA, or NOAA agency logos or mission badges.

#### Development Timeline & Prior Work Disclosure — Option A (Full Pre-Event History Transparently Declared — recommended pending Local Lead confirmation)
Part of our weather viewer layer builds upon the team's prior open-weather web interface (`SICC-952`), and the main code development, statistical engine, multi-source ingestion scripts, and submission documentation in our project repository were developed prior to opening day between November 11 and November 13, 2026 (UTC−6, 54 commits across 5 team contributors), prior to hackathon-weekend refinement, integration, and verification on November 14–15, 2026. We are disclosing this exact timeline to the Managua Local Lead and in this submission to preserve complete transparency with respect to Space Apps pre-event and originality rules.

#### Development Timeline & Prior Work Disclosure — Option B (Use ONLY if Local Lead instructs scoping prior work as baseline open tooling + hackathon-only delta)
This submission distinguishes cleanly between pre-existing components—our prior open-weather base interface (`SICC-952`) and foundational data and statistical utilities initiated on November 11–13, 2026—and the Space Apps challenge integration, verification, user-facing *Investigate / Learn / Sources* synthesis, and demo package completed during the Managua hackathon on November 14–15, 2026, in accordance with guidance from our Local Event Lead.

### 9. NASA Data (With Citations & DOIs)
- **GPM IMERG Final Run V07B (`GPM_3IMERGM` v07, `GPM_3IMERGDF` v07)** via GES DISC & Cloud OPeNDAP — Huffman et al. (2023), DOI `10.5067/GPM/IMERG/3B-MONTH/07`, DOI `10.5067/GPM/IMERGDF/DAY/07`.
- **GISTEMP Surface Temperature Analysis v4** — NASA GISS, https://data.giss.nasa.gov/gistemp/; Lenssen et al. (2024), DOI `10.1029/2023JD040179` (citing the GISTEMP Hansen et al., 2010 baseline on portal).
- **AIRS/Aqua L3 Monthly Standard Physical Retrieval (`AIRS3STM v7.0`)** — NASA GES DISC, DOI `10.5067/UBENJB9D3T2H`.
- **OMI/Aura Nitrogen Dioxide Cloud-Screened Column (`OMNO2d v003`)** — NASA GES DISC, DOI `10.5067/Aura/OMI/DATA3007`.
- **GLDAS Noah Land Surface Model v2.1 (`GLDAS_NOAH025_M 2.1`)** via GES DISC Cloud OPeNDAP — Beaudoing & Rodell (2020), DOI `10.5067/SXAVCZFAQLNO`.
- **MERRA-2 (`v5.12.4`: `M2TMNXLND`, `M2IMNPASM`, `M2TMNXOCN`)** — NASA GMAO / GES DISC, DOIs `10.5067/8S35XF81C28F`, `10.5067/2E096JV59PK7`, `10.5067/4IASLIDL8EEC`.
- **NASA POWER (`v10` docs / Daily API `v2.10.3`)** — NASA LaRC, https://power.larc.nasa.gov/docs/.
- **MODIS Collection 6.1 (`MOD13Q1.061` via ORNL DAAC REST; queued AppEEARS: `MOD11A2.061`, `MOD16A2GF.061`, `MOD13A3.061`, `MCD12Q1.061`)** — NASA LP DAAC / ORNL DAAC, DOIs `10.5067/MODIS/MOD13Q1.061`, `10.5067/MODIS/MOD11A2.061`, `10.5067/MODIS/MOD16A2GF.061`, `10.5067/MODIS/MOD13A3.061`, `10.5067/MODIS/MCD12Q1.061`.
- **SMAP Level 4 (`SPL4SMGP v008` in AppEEARS queue; `v007` adapter)** — NASA NSIDC DAAC, DOI `10.5067/T5RUATAQREF8`.
- **GRACE/GRACE-FO Mascon CRI (`RL06.3 V4`, code adapter)** — NASA JPL / PO.DAAC, Wiese et al. (2019), DOI `10.5067/TEMSC-3JC634`.
- **OBPG MODIS-Aqua L3m Chlorophyll-a (`R2022.0`)** — NASA OB.DAAC, DOI `10.5067/AQUA/MODIS/L3M/CHL/2022`.
- **G-REALM Global Reservoir & Lake Monitoring (Lake Cocibolca `000351`)** — NASA GSFC / USDA, https://earth.gsfc.nasa.gov/gwm/lake/Index.
- **SWOT L2 HR LakeSP (`v2.0`, Ver C via PO.DAAC Hydrocron)** — NASA JPL / CNES / PO.DAAC, DOI `10.5067/SWOT-LAKESP-2.0`.
- **OPERA RTC-S1 (`V1`) & OPERA DSWx-S1 (`V1`)** — NASA JPL / ASF DAAC & PO.DAAC, DOIs `10.5067/SNWG/OPERA_L2_RTC-S1_V1`, `10.5067/OPDSWS1-L3V1`.
- **NEX-GDDP-CMIP6 (`v2.0`)** — NASA NCCS, Thrasher et al. (2022), DOI `10.1038/s41597-022-01393-4`; dataset DOI `10.7917/OFSG3345`.
- **NASA NTRS Technical Report `20090042747`** — Acker, McMahon, Shen, Hearty, and Casey (2009), *Time-Series Analysis of Remotely-Sensed SeaWiFS Chlorophyll in River-Influenced Coastal Regions*, *EARSeL eProceedings* 8(2), https://ntrs.nasa.gov/api/citations/20090042747.
- **NASA GIBS WMTS & NASA SVS CGI Moon Kit (`4720`)** — NASA EOSDIS / GSFC, https://svs.gsfc.nasa.gov/4720.

### 10. Space Agency Partner Data & Other Resources
- **Canadian Space Agency (CSA)**: RADARSAT Constellation Mission (`RCM`, Public Good EODMS Order `#3787605` — queued, zero raw imagery redistributed) and CSA Synthetic Aperture Radar Python Tutorial (MIT License, https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial).
- **Agriculture and Agri-Food Canada (AAFC / Geo.ca)**: Terrestrial Ecozones of Canada (`CAN_prairies`, ~467,128 km²), licensed under Open Government Licence – Canada (http://geo.ca/).
- **Climatic Research Unit (UEA)**: `CRU TS 4.10` (`ODbL / DbCL`); Harris et al. (2020), DOI `10.1038/s41597-020-0453-3`.
- **DWD / NOAA PSL**: `GPCC Full Data Monthly v2025` (`0.50°`), https://psl.noaa.gov/data/gridded/data.gpcc.html.
- **NOAA NCEI & CPC**: `GHCN-Daily v3` (DOIs `10.7289/V5D21VHZ`, `10.1175/JTECH-D-11-00103.1`), `GSOM v1.0` (3 Saskatchewan stations), and `CPC ONI v5`.
- **Natural Earth**: `10m` country boundary vectors (Public Domain, https://www.naturalearthdata.com/about/terms-of-use/).
- **Statsig**: Allon Korem (August 7, 2025), *A Comprehensive Guide to Statistical Significance*, https://www.statsig.com/perspectives/a-comprehensive-guide-to-statistical-significance.
- **SINAPRED (Nicaragua)**: Institutional event reference links and brief factual dates/summaries (`sinapred.gob.ni`; original bulletins not mirrored).
- **External Weather Map Layers**: Open-Meteo / ECMWF IFS `0.25°` (DOI `10.21957/open-data`, CC BY 4.0; Open-Meteo free-tier non-commercial terms) and RainViewer API (personal/educational radar display terms with attribution).

---

## Parte 2: Pendiente del equipo (NO pegar en la plataforma)

- **`[DECISIÓN DEL EQUIPO]` — Título unificado:** Confirmar si el título oficial en la plataforma y en todas las piezas será **`Earth Trend Detective`** (`index.html`) o **`Earth System Trend Detective`**.
- **`[DECISIÓN DEL EQUIPO]` — Trabajo previo al evento (§8):** Consultar al *Local Lead* de Managua antes de marcar **`Confirm All Work is Original`** (ver plantilla en `REQUISITOS_ENTREGA_2026.md` §4). Pegar **Option A** u **Option B** según lo acordado por escrito con la sede, nunca ambas a la vez.
- **`[DECISIÓN DEL EQUIPO]` — Licencia raíz del proyecto:** Añadir `LICENSE` OSI (`Apache-2.0` o `MIT`) en la raíz del repositorio y documentar la separación respecto a datos derivados (`CRU ODbL`, `RainViewer`, `Open-Meteo`; ver `PROPUESTAS.md`).
- **`[CONFIRMAR]` — Declaración SI de audio/visuales (§8):** Si el vídeo de 30 s o las diapositivas usan locución sintética (p. ej. ElevenLabs) o imágenes generadas por IA, añadir al párrafo de *Use of Super Intelligence* la frase exacta indicando la herramienta y confirmar la **marca de agua visible** y metadatos (ver `DECLARACION_SI.md` §4b). Si se graba 100 % con pantalla real y voz humana mayor de 18 años, añadir: *"Demo captures and human narration contain no SI-generated imagery, video, or synthetic voice."*
- **`[CONFIRMAR]` — Menores de edad (`< 18` años):** Confirmar si todos los autores/participantes son mayores de 18 años y que no aparezcan nombres reconocibles, voces ni rostros de menores en ningún enlace enviado.
- **`[VERIFICAR]` — Cita completa Hansen et al. (2010):** Si el formulario exige referencia bibliográfica completa además del DOI de Lenssen et al. (2024), copiar la cita literal de Hansen et al. (2010) directamente desde https://data.giss.nasa.gov/gistemp/.
- **`[ENLACE]` — Repositorio público en GitHub:** Hacer público el repositorio (previa auditoría de secretos) y pegar su URL HTTPS directa (`https://github.com/lizanooctavio-boop/NASA-CHALLENGE`).
- **`[ENLACE]` — Demo interactiva pública:** Desplegar la rama unificada tras fusionar PRs abiertos y probar la URL pública en una red externa sin inicio de sesión (regla FortiGuard).
- **`[ENLACE]` — Demo oficial (`<= 30 s` vídeo O `<= 7` diapositivas PDF/deck):** Subir el enlace público único seleccionado antes del **domingo `15-11-2026` a las `23:59` (Managua `UTC−6`)**.
