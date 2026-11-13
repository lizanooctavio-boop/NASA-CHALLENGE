# 7-Slide Presentation Deck Plan (`<= 7` Slides, English)

> **Idioma de la presentación:** Inglés obligatorio en todas las diapositivas, etiquetas, gráficos y notas del orador.  
> **Estructura de este archivo:** La **Parte 1** contiene únicamente el contenido limpio en inglés de las **7 diapositivas** (sin rutas internas del repositorio, nombres de ramas, hashes de commits ni marcadores `[...]`). La **Parte 2 (`Pendiente del equipo`)** recoge las comprobaciones de exportación, metadatos, marca, menores de edad y enlaces.

---

## Parte 1: Guion limpio de 7 diapositivas (English)

### Slide 1 — Title & Introduction

- **Slide Content:**
  - **Title:** **Earth Trend Detective**
  - **Subtitle:** *Separating Real Climate Signals from Variability and Cross-Source Noise — Nicaragua & the Canadian Prairies*
  - **Challenge:** NASA Space Apps 2026 — *Be an Earth System Trend Detective!*
  - **Event:** Managua Local Event
  - **Access:** Live Interactive Web App · Open-Source Code Repository
- **Suggested Visual:**
  - High-contrast capture of our 3D interactive globe centered on Central America paired with three clean verdict badges (`Trend detected` · `Not enough evidence of a trend` · `Methods disagree`). No NASA, CSA, or NOAA logos.
- **Speaker Notes:**
  - Stakeholders constantly ask whether rainfall, air temperature, soil moisture, or lakes are changing—yet a single satellite curve or naive regression can give the wrong answer. **Earth Trend Detective** tests *what* is changing, *where*, *by how much*, and *how sure we can be* using cross-checked NASA, NOAA, CSA, and global records.

---

### Slide 2 — Why Single Tests Fail & Our 4-Check Statistical Engine

- **Slide Content:**
  - **The Statistical Trap (Gulf of Fonseca Chlorophyll-a, 2003–2024):**
    - Naive monthly OLS across 264 raw months (Acker et al., 2009 monthly method): **`+1.21 mg/m³/decade`, `p < 0.001`** (`p = 0.0007`) — appears strongly significant!
    - Deseasonalized annual series + autocorrelation correction: **`+0.68 mg/m³/decade`, Modified Mann–Kendall `p = 0.080`** -> **`Methods disagree`** (and `7.02 mg/m³` mean exceeds the `<= 1 mg/m³` Case-1 water threshold).
    - Adjacent **Open Pacific control box** (`0.44 mg/m³`, `100%` of 144 pixels `<= 1 mg/m³`): **`−0.06 mg/m³/decade`, `p = 0.128`** -> **`Not enough evidence`** — consistent with inner-Gulf optical turbidity confounding rather than confirmed phytoplankton trend acceleration.
  - **Our 4-Check Trend Engine & 3 Verdicts:**
    1. **OLS with effective degrees of freedom** (`AR(1)`-adjusted, Santer et al., 2000)
    2. **OLS with Newey–West HAC errors**
    3. **Non-parametric Theil–Sen slope** (`95% CI`, verified with `±3-year` shifts & leave-one-year-out sensitivity)
    4. **Modified Mann–Kendall** (`Hamed & Rao, 1998`) + **Pettitt (1979) step-change detector** + **Benjamini–Hochberg FDR (`q = 0.10`)**
    - **Three Verdicts + Data Guards:** `Trend detected` · `Not enough evidence of a trend` *(never equals "no change")* · `Methods disagree`, plus **`Record too short for a trend test`** (`< 10 yrs`) and **`Not validated`** radar gate.
- **Suggested Visual:**
  - Side-by-side comparison card from the *Learn* section (`p = 0.0007` naive vs. `p = 0.080` adjusted) next to a simple 3-verdict decision funnel.
- **Speaker Notes:**
  - Explain how autocorrelated months and turbid waters inflate significance, and why *Learn* teaches users that *"Not enough evidence of a trend"* never means zero physical risk.

---

### Slide 3 — Core Demonstration: Nicaragua vs. Canadian Prairies (`2001–2024`)

- **Slide Content:**
  - **Guided Walkthrough:** **`Tropics vs. prairies`** in the **Investigate** tab compares the same `2001–2024` satellite/station era across two starkly different climates:
  - **Surface Air Temperature (`NASA GISTEMP v4`, 2001–2024):**
    - **Nicaragua (~119,900 km²):** **`+0.398 °C/decade`** (95% CI `+0.210 to +0.537`, MMK `p < 0.001`) -> **`Trend detected`** (full `1981–2024`: `+0.294 °C/decade`).
    - **Canadian Prairies (~467,128 km², AAFC ecozone):** **`+0.175 °C/decade`** (95% CI `−0.568 to +0.754`, MMK `p = 0.637`, annual range `−0.289 to +2.675 °C`) -> **`Not enough evidence of a trend`**. *Higher mid-latitude variance hides moderate slopes over 24 years.*
  - **Annual Rainfall (`NASA GPM IMERG Final V07B`, 2001–2024):**
    - **Nicaragua:** Mean `2,094.1 mm/yr`, Sen `−64.9 mm/decade` (MK `p = 0.442`) -> **`Not enough evidence`**, strongly modulated by ENSO (`r = −0.561` Jun–Nov vs. ONI). *(Contrast: Costa Rica returns `Methods disagree`: OLS `−201.2` vs. Sen `−168.4 mm/dec`.)*
    - **Canadian Prairies:** Mean `435.2 mm/yr`, Sen `−30.4 mm/decade` (May–Sep `−20.2 mm/dec`) -> **`Not enough evidence`**, verified against 3 NOAA GSOM Saskatchewan stations (`r = 0.830` rain, `r = 0.961` temp) and GES DISC Cloud OPeNDAP IMERG (`r = 1.000` in SW box, `r = 0.999` in Nicaragua).
- **Suggested Visual:**
  - Live **Investigate** capture showing Nicaragua (`Trend detected`, coral badge) paired with Canadian Prairies (`Not enough evidence`, neutral badge) plus annual IMERG vs. GSOM curves.
- **Speaker Notes:**
  - Contrast the two regions directly: identical statistical rules detect rapid warming in tropical Nicaragua while rightly flagging variance-dominated uncertainty in the Canadian Prairies.

---

### Slide 4 — Cross-Checks as Clues: When Datasets Diverge

- **Slide Content:**
  - **Principle:** *Disagreement across independent observations is a diagnostic clue, not an error to hide.*
  - **Temperature (`AIRS3STM v7.0` vs. `GISTEMP v4` & `POWER/MERRA-2`):**
    - `AIRS v7` (`2003–2024`, Nicaragua) tracks interannual swings (`r = 0.924` vs. GISTEMP) with `+0.126 °C/dec` annual Sen (`MK p = 0.010`), yet raw monthly OLS (`p = 0.073`) stays non-significant—supporting warming direction rather than GISTEMP's rate (`+0.381 °C/dec`). Meanwhile `NASA POWER` (`1981–2024`) shows `−0.105 °C/dec` across a `1999` Pettitt step break (`p = 0.008`).
  - **Surface Soil Moisture (`GLDAS-2.1 Noah` 0–10 cm vs. `MERRA-2 GWETTOP` 0–5 cm, `2001–2024`):**
    - `GLDAS-2.1` (Cloud OPeNDAP) shows drying in Central Nicaragua (`−0.0090 m³/m³/dec`, *Trend detected* full window, **drops to `Methods disagree` if 2001–2002 excluded**; `2013` Pettitt & AGRMET caveat) and Canadian Prairies (`−0.0139 m³/m³/dec`, `MK p = 0.008`, persistent). `MERRA-2 GWETTOP` (0–1 index) trends positive (`r = 0.025–0.075`).
  - **Rainfall Gauges & Urban Air Quality (`CRU / GPCC` & `OMI NO2`):**
    - `GPCC v2025` tracks IMERG (`r = 0.94`), while `CRU TS 4.10` diverges (`r = 0.63`) as active Nicaraguan gauges fall `3.7 -> 1.8` post-`2015`. Over `2005–2024`, `Aura OMI NO₂` drops nearly identically in Managua (`−0.043 × 10¹⁵/dec`) and rural Chontales (`−0.049 × 10¹⁵/dec`), showing regional declines cannot be isolated as an urban-only trend.
- **Suggested Visual:**
  - Two clean **Cross-checks** charts (`GLDAS` vs. `MERRA-2` standardized anomalies and `GISTEMP` vs. `POWER` with Pettitt break annotation).
- **Speaker Notes:**
  - Highlight why judges can trust our numbers: every divergence—gauge dropouts, assimilation jumps, forcing changes, or matching urban/rural drifts—is surfaced automatically instead of hidden.

---

### Slide 5 — Lakes, SAR Radar Demos, Vegetation & 2050 Projections

- **Slide Content:**
  - **Lake Altimetry (`Lakes Cocibolca & Xolotlán`):**
    - `G-REALM` (`1993–2025`): Lake Cocibolca `+0.11 m/decade` (`95% CI −0.01 to +0.23`) -> **`Not enough evidence`**.
    - `SWOT Hydrocron` (`41` months): tracks G-REALM closely (`r = 0.990`, `−0.437 m` offset) and is strictly guarded as **`Record too short for a trend test`**.
  - **Radar Surface-Water Demo (`OPERA RTC-S1` & `DSWx-S1`):**
    - `75` Sentinel-1 bursts and `37` DSWx-S1 tiles (`2,585.25 km²` common water = `33.05%` of Lake Cocibolca) stay tagged **`Not validated`** until independent ground truth and queued CSA `RCM` scenes (`Order #3787605`) finish processing.
  - **Exploratory Vegetation & 2050 Scenarios (`NASA NEX-GDDP-CMIP6 v2.0`, 6 GCMs, `2041–2060` vs. `1995–2014`):**
    - Central Nicaragua single-site `MOD13Q1` (`2000–2024`) shows `−0.0432 NDVI/decade` (`MK p < 0.001`), explicitly caveated as single-site exploratory data pending regional land-cover masks.
    - Mid-century warming medians: **`+1.40 °C`** (SSP2-4.5) and **`+1.98 °C`** (SSP5-8.5, `6/6` warmer); precipitation medians: **`−5.45%`** (SSP2-4.5) and **`−10.49%`** (SSP5-8.5, `6/6` drier).
- **Suggested Visual:**
  - Top: Lake Cocibolca `SWOT` vs. `G-REALM` tight overlay (`r = 0.990`). Bottom: `CMIP6` scenario summary strip paired with **`Record too short`** and **`Not validated`** honesty badges.
- **Speaker Notes:**
  - Emphasize disciplined scope: new sensors like SWOT and uncalibrated SAR masks are separated cleanly from multi-decade climate inferences.

---

### Slide 6 — Interactive Platform & Open Data Transparency

- **Slide Content:**
  - **Three Detective Workspaces + Spatial Globe/Map:**
    - **Investigate:** Step-by-step Topic -> Place -> Variable explorer, automated 3-verdict cards, interactive `Chart.js` series, side-by-side **Cross-checks**, guided tours, and 1-click **CSV / JSON** export with provenance metadata.
    - **Learn & Sources:** Visual explanations of confidence intervals, Type II error, autocorrelation, Pettitt breaks, and `57`-cell Benjamini–Hochberg FDR maps (`57/57` total rain & `r95p`; `52/57` `rx1day`; `43/57` `tmax_media` & `tx90p`; `26/57` `tmin_media`), plus dataset versions and licensing.
    - **3D Globe ⇄ 2D Map (`Three.js 0.160.0` + `Leaflet 1.9.4`):** NASA `GIBS` overlays, ENSO status, NHC cyclones, and live meteorological layers (`Open-Meteo` / `ECMWF IFS` & `RainViewer`).
  - **Honest Ingestion Queue Reporting:**
    - Automated download logs record blocked or pending feeds transparently without placeholder guesses: `160` regional `AppEEARS` tasks queued (`MODIS C6.1 + SMAP L4`), `CSA RCM Order #3787605` in queue, and retired Hydrology Data Rods replaced cleanly with `GES DISC Cloud OPeNDAP`.
- **Suggested Visual:**
  - Clean 3-panel screenshot mosaic of the web UI (**Investigate**, **Learn**, and **3D Globe -> 2D Map**) plus a concise Open Source Data -> Statistical Checks -> UI/CSV Export pipeline diagram.
- **Speaker Notes:**
  - Show judges that this is a live, verifiable software tool—anyone can read statistical assumptions, export CSV/JSON series, and inspect exactly which cloud endpoints are complete versus queued.

---

### Slide 7 — Impact, Roadmap, Citations & SI Disclosure

- **Slide Content:**
  - **Who Benefits:** Climate educators, science journalists, students, and local technical teams across Central America and Canada who need transparent verification rather than single-test overconfidence.
  - **Post-Hackathon Roadmap:**
    1. Ingest completed `160` AppEEARS regional MODIS/SMAP jobs and process `CSA RCM` scenes (`5600935`, `5616847`) with ground-truth SAR validation.
    2. Finalize unified production release and apply mobile responsive (`390 px`), contrast, and keyboard-focus accessibility improvements.
    3. Connect public `SINAPRED` historical context links under clear non-redistribution attribution rules.
  - **Credits, Open License & SI Transparency:**
    - **Data & Citations (Text Attribution Only):** NASA (`GPM IMERG V07B`, `GISTEMP v4`, `AIRS3STM v7.0`, `OMNO2d v003`, `MODIS C6.1`, `MERRA-2`, `POWER`, `GLDAS-2.1`, `OPERA`, `SWOT`, `OBPG`, `NEX-GDDP-CMIP6`, `G-REALM`, `GIBS`, `SVS 4720`, `NTRS 20090042747` Acker et al., 2009), NOAA (`GHCN-D`, `GSOM`, `CPC ONI`), CSA (`RCM`, `SAR Python Tutorial`), AAFC/Geo.ca (`OGL-Canada`), UEA `CRU TS 4.10` (`ODbL`), DWD/NOAA PSL `GPCC v2025`, `Natural Earth`, `Statsig` (Allon Korem, 2025), `Open-Meteo` (`ECMWF IFS`), `RainViewer`, `Three.js`, `Leaflet`, `Chart.js`.
    - **SI Assistance Disclosure:** Software development, statistical test scaffolding, accessibility auditing, and documentation were assisted by `Claude Code (Opus)`, `Codex`, `Claude Opus`, and `Gemini`; scientific direction, verdict rules, and final verification belong to the human team. Screen captures depict the real web UI with zero agency logos.
- **Suggested Visual:**
  - Clean structured credits matrix (zero NASA/CSA/NOAA emblems) paired with live Demo & Open-Source Repository URLs.

---

## Parte 2: Pendiente del equipo (NO pegar en las diapositivas)

- **`[DECISIÓN DEL EQUIPO]` — Elegir formato único de demo:** Confirmar entrega como **presentación `<= 7` diapositivas (PDF/enlace público)** O **vídeo `<= 30 s`**. No enviar dos demos si la guía pide uno.
- **`[DECISIÓN DEL EQUIPO]` — Título unificado:** Alinear **`Earth Trend Detective`** vs. **`Earth System Trend Detective`** en la Diapositiva 1.
- **`[DECISIÓN DEL EQUIPO]` — Licencia abierta del proyecto:** Añadir el nombre exacto de la licencia OSI elegida (`Apache-2.0` o `MIT`) al pie de la Diapositiva 7 y crear `LICENSE` en la raíz del repositorio antes de exportar.
- **`[CONFIRMAR]` — Estado real de la captura UI antes de hacer las capturas:** Para las capturas de las Diapositivas 3, 4 y 5, fusionar los PRs abiertos y ejecutar `python -m clima_nic recursos` en `backend/` (ver `PROPUESTAS.md`) de modo que **Canada**, **Cross-checks** y **SWOT/OPERA** se muestren directamente desde `data/recursos_integrados.json`.
- **`[CONFIRMAR]` — Regla de marca de agua SI y menores (`< 18` años):**
  - Verificar que ninguna persona `< 18` años aparezca en fotos/capturas/nombres reconocibles.
  - Si se inserta alguna ilustración generada por IA en las diapositivas, colocar una **marca de agua visible** sobre esa imagen y declararla en la Diapositiva 7 y en los metadatos del PDF (*Title / Author / Comments*). Si todas las visuales son capturas reales de la app y diagramas propios, consignarlo así en las propiedades del PDF.
- **`[ENLACE]` — Exportación y enlaces públicos (FortiGuard):** Exportar un único PDF de exactamente **7 páginas** o enlace público sin login ni acortadores, rellenar los enlaces reales en Diapositiva 1 y Diapositiva 7 y probarlos desde una red externa.
