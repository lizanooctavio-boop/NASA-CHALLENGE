# Earth System Trend Detective — Project Description & Official 2026 Submission Requirements

## Part 1. Official NASA Space Apps Challenge 2026 Submission & Judging Requirements

**Sources consulted (`spaceappschallenge.org`):**
- **Project Submission Guide:** <https://www.spaceappschallenge.org/resources/project-submission-guide/>
- **Judging & Awards Guide:** <https://www.spaceappschallenge.org/resources/judging-awards-guide/>
- **Participant FAQs:** <https://www.spaceappschallenge.org/resources/participant-faqs/>
- **Legal & Terms and Conditions:** <https://www.spaceappschallenge.org/legal/>
- **Challenge Statement ("Be an Earth System Trend Detective!"):** <https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/>

### 1.1 Project Submission Form Fields & Rules
All project submission form fields on `spaceappschallenge.org` must be completed **in English** before clicking **"Submit for Judging"** prior to the Local Event deadline (`Sunday, November 15, 2026, at 11:59 p.m.` local time of the registered Local Event — Managua, `UTC−6`):

| Form Field / Requirement | Official Rule (`spaceappschallenge.org`) | Status / Note |
| :--- | :--- | :--- |
| **Project Name** | Short, descriptive title of the project. | **Earth System Trend Detective** |
| **High-Level Project Summary** | Concise overview of what the team built and why it matters. | Provided in Section 2.1 below. |
| **Link to Project Demo** | Publicly accessible URL (no logins, permissions, or paywalls) to **either** a `<= 30-second video` **or** a `<= 7-slide presentation`. | Choose one format; see `docs/entrega/GUION_DEMO.md`. |
| **Link to Final Project** | Publicly accessible URL to the live interactive application and/or open-source code repository (`github.com`). | Live demo: <https://sicc952.onrender.com> · Repo: <https://github.com/lizanooctavio-boop/NASA-CHALLENGE> |
| **Detailed Project Description** | Explanation of what the solution does, how it works, how it responds to the challenge objectives, and what benefits it provides. | Provided in Sections 2.2–2.6 below. |
| **Space Agency Data** | Explicit list and citations of all NASA and Space Agency Partner datasets, APIs, and resources used (required for Global Judging eligibility). | All **13** official challenge resources and additional NASA/CSA/NOAA datasets listed in Section 2.5 and `README.md`. |
| **Other Data, Tools, Coding Languages & Hardware** | All third-party datasets, software libraries, programming languages, and hardware used. | Listed in Section 2.6 and `README.md`. |
| **Use of Artificial Intelligence (AI) / Super Intelligence (SI)** | Mandatory disclosure explaining which AI/SI tools were used, how they were used, and how outputs were verified. | Full disclosure in `docs/entrega/AI_USE.md`. |
| **Mandatory Submission Checkboxes** | Teams must check **`Terms and Conditions`** and **`Confirm All Work is Original`** before clicking **Submit for Judging**. | Open-source licensing (OSI-approved license; defaults to `Apache 2.0` if unspecified per Space Apps Terms). |

### 1.2 Demo Format Limits (Video vs. Slide Deck)
The Project Submission Guide specifies that teams must provide **one** of two demo formats hosted on a publicly accessible external link (avoiding URL shorteners that corporate firewalls such as FortiGuard may block):
1. **Option A — Video Demo (`<= 30 seconds`):**
   - Maximum length of **30 seconds**.
   - Spoken narration may be in any language, but **English subtitles are mandatory** (English audio + burned-in English captions recommended).
2. **Option B — Slide Deck (`<= 7 slides`):**
   - Maximum of **7 slides total** (including title and introduction slides).
   - Must be written **entirely in English**.

### 1.3 Official Global Judging Criteria
According to the Judging & Awards Guide, every eligible project (responding to an official challenge statement, integrating at least one NASA or Space Agency Partner resource, and providing working public links) is scored from **1 to 5** (*Very Poor* = 1 to *Excellent* = 5) across five criteria:
1. **Impact:** How much impact (quality and quantity) can this project have? Does it solve a big problem or a small problem, and how clearly does it benefit its target users?
2. **Creativity:** How creative or innovative is the approach? Is the project novel and something that has not been attempted in this way before?
3. **Validity:** Is the solution scientifically and technically sound? Does it interpret Earth science data and statistical evidence accurately, and can it work in the real world?
4. **Relevance:** Is this project responsive to the specific challenge for which it was submitted (*"Be an Earth System Trend Detective!"*)? Is it a complete response to the challenge objectives?
5. **Presentation:** How well did the team communicate their project? Were they effective in telling the story of the project: the challenge, the solution, and why this project is important?

### 1.4 Official AI / Super Intelligence (SI) Policy
- **Permitted with Mandatory Disclosure:** Participants may use AI/SI tools (LLMs, code assistants, media generators), provided the submission clearly discloses which tools were used and how they contributed.
- **Watermarking & Metadata:** Any AI-generated visual or audio assets in the project or demo must carry a visible watermark/label and appropriate file metadata.
- **Strict Prohibition on Agency Logos:** Neither AI-generated assets nor project materials may include or modify official NASA branding, logos (*meatball* or *worm*), mission insignias, or agency flags. Attribution to NASA, CSA, and NOAA must be textual only.
- **What is not published on `spaceappschallenge.org`:** Exact character limits per text box in the live web portal (which vary slightly by browser/edition, typically ~300–500 characters for the short summary and several thousand characters for detailed fields) and local judging schedule hours are managed inside each authenticated Local Event team dashboard rather than on the public static guide pages.

---

## Part 2. Project Description — Earth System Trend Detective

### 2.1 High-Level Summary
**Earth System Trend Detective** is an open, interactive climate-diagnostics web application built for the 2026 NASA Space Apps Challenge (**"Be an Earth System Trend Detective!"**). Starting from an interactive 3D WebGL globe that unfolds into a 2D map, users investigate **202 observed Earth-system time series** across **74 locations** worldwide and **8 thematic categories** (*Rain*, *Temperature*, *Vegetation & ecosystems*, *Water bodies*, *Air quality*, *Coast & ocean*, *Hurricanes*, and *Ice*), integrating all **13 official challenge resources** plus **33 independent cross-checks**.

Instead of relying on a single regression line that can be fooled by El Niño cycles, outlier years, autocorrelation, or sensor changes, every series with at least 10 years of observations is evaluated simultaneously by **four statistical estimators**—**Theil–Sen slope**, **modified Mann–Kendall with Hamed–Rao autocorrelation correction**, **AR(1)-adjusted Ordinary Least Squares (OLS)**, and **Newey–West HAC least squares**—to issue one of three transparent verdicts: **`Trend detected`** (`66` series), **`Not enough evidence of a trend`** (`83` series), or **`Methods disagree`** (`48` series), while guarding short satellite records (`5` series) as **`Record too short for a trend test`**.

### 2.2 What the App Does, Who It Is For, and the Challenge It Answers
The challenge **"Be an Earth System Trend Detective!"** asks for a tool that lets users select Earth science variables from satellites, ground networks, and models, visualize their evolution over time, and answer four core questions:
1. **What** is changing?
2. **Where** is it changing?
3. **How much** is it changing?
4. **Whether** those changes are statistically **"significant."**

**Target Audience:** High-school and university students, educators, science journalists, and regional environmental planners who need plain-English definitions of physical variables alongside rigorous statistical guardrails.

**How the Interface Guides the User:**
- **3D Globe & 2D Map (`#globe` / `#map`):** A `Three.js` 3D Earth with NASA GIBS Blue Marble and VIIRS Black Marble textures that transitions smoothly into a `Leaflet` 2D map with satellite, radar, and regional polygon layers.
- **`Investigate` (`#investigar`):** Guided three-step selector (**Topic / Category → Location → Variable**), an immediate **Verdict Card** (*How much per decade* via Theil–Sen with 95% CI, *How sure* via modified Mann–Kendall $p$-value, and *Least squares* slope with 95% CI), an interactive time-series chart with the Theil–Sen trend line, **Published checks** with Crossref-verified DOIs, side-by-side **Cross-checks** (`33` series pairs), **3 Guided Tours**, and one-click **CSV / JSON export**.
- **`Learn` (`#aprender`):** Interactive visual explanations of why months are not independent, why confidence intervals matter, why *"Not enough evidence"* never means *"no change,"* how Pettitt change-point tests catch artificial reanalysis jumps, and how Benjamini–Hochberg False Discovery Rate (`FDR`) prevents false positives across maps.
- **`Sources` (`#fuentes`):** Live status of all **13 challenge resources** (`13/13` active in use) and direct links to every primary dataset.
- **Nicaragua Deep-Dive Tabs (`Rainfall trend`, `Climate indicators`, `El Niño & cyclones`, `Climate scenarios`):** Detailed national and subregional diagnostics for Nicaragua (`Pacific lowlands`, `Central highlands`, `Caribbean coast`, and `Southwest study box`), comparing NASA GPM IMERG, GISTEMP v4, MODIS NDVI, GLDAS-2.1, MERRA-2/POWER, and 6-model NASA NEX-GDDP-CMIP6 projections (`2041–2060`).

### 2.3 Exact Public Demo Figures (From `data/recursos_integrados.json`)
All counts below are computed directly from the versioned public dataset (`data/recursos_integrados.json`, verified by `python -m pytest -q`):

| Metric in Public Demo | Exact Count | Breakdown in Screen Interface |
| :--- | :---: | :--- |
| **Total Investigations (`investigaciones`)** | **202** | `Water bodies` (**64**), `Rain` (**53**), `Ice` (**31**), `Coast & ocean` (**21**), `Temperature` (**14**), `Vegetation & ecosystems` (**10**), `Hurricanes` (**7**), `Air quality` (**2**) |
| **Locations (`lugares`)** | **74** | Central America & Nicaragua, North & South America, Caribbean, Europe, Africa, Middle East, Arctic, Antarctic, and Global latitude bands |
| **Verdict: `Trend detected`** | **66** | All parametric and non-parametric 95% CIs exclude zero with the same sign and modified Mann–Kendall $p < 0.05$ |
| **Verdict: `Not enough evidence of a trend`** | **83** | Confidence intervals include zero and modified Mann–Kendall $p \ge 0.05$ over the observed window |
| **Verdict: `Methods disagree`** | **48** | Parametric (OLS / Newey–West HAC) and non-parametric (Theil–Sen / modified Mann–Kendall) tests reach different conclusions at the 5% level |
| **Guardrail: `Record too short for a trend test`** | **5** | Series with `< 10` years (`SWOT` monthly lake elevation for Lakes Cocibolca and Xolotlán, `OPERA DSWx-S1` radar water scenes, and monthly `SMAP L4` soil moisture) |
| **Cross-Checks (`contrastes`)** | **33** | Independent dataset comparisons (e.g., IMERG vs. CRU TS 4.10, GPCC, Giovanni, OPeNDAP, and NOAA stations; GLDAS vs. MERRA-2; SWOT vs. G-REALM) and method comparisons |
| **Guided Tours (`demostraciones`)** | **3** | *Has Nicaragua's rainfall changed?*, *Same total, different rain?*, and *Tropics vs. prairies: is warming the same everywhere?* |
| **Official Challenge Resources (`recursos`)** | **13 / 13** | All 13 NASA, NOAA, CSA, KNMI, Medium, and Statsig challenge resources integrated (`estado: "en_uso"`) |

#### Representative Series Visible in the Public Demo
- **Mediterranean Marine Heatwaves & Warming (`1982–2025`, NOAA OISST v2.1):**
  - *Mediterranean sea surface temperature* (`mediterraneo_sst`): **`+0.372 °C/decade`** (Theil–Sen 95% CI `[+0.315, +0.435]`, OLS `+0.368 °C/decade`, modified Mann–Kendall $p < 0.001$) → **`Trend detected`**.
  - *Days in a Mediterranean marine heatwave* (`mediterraneo_olas_calor`): **`+22.60 days/decade`** (Theil–Sen 95% CI `[+6.15, +35.00]`, OLS `+40.37 days/decade`, modified Mann–Kendall $p = 0.005$) → **`Trend detected`**.
- **North Atlantic Hurricane Rapid Intensification (`1980–2024`, NOAA IBTrACS v04r01):**
  - *North Atlantic rapid intensification steps* (`huracanes_rapida_intensificacion_na_pasos`, 6-hour intervals with $\ge 30\text{ kt}$ gain in $24\text{ h}$): Theil–Sen **`+2.105 steps/decade`** (95% CI `[0.000, +4.444]`), modified Mann–Kendall $p = 0.064$, AR(1)-adjusted OLS `+2.354 steps/decade` (95% CI `[-0.215, +4.924]`, $p = 0.071$), whereas Newey–West HAC 95% CI `[+0.168, +4.541]` excludes zero → **`Methods disagree`**.
- **Tree Cover Loss in Nicaragua (`2001–2024`, Landsat 30 m / Hansen Global Forest Change v1.12):**
  - *Nicaragua national total* (`bosque_perdida_NIC`): **`20,231 km²`** of tree cover lost over 2001–2024 (**26%** of the `78,049 km²` of year-2000 forest; peak loss `2,149 km²` in 2010). Theil–Sen slope is **`+255.8 km²/decade`** (95% CI `[+11.5, +570.2]`) and HAC CI is `[+114.3, +482.0]`, while AR(1)-adjusted OLS (`+298.2 km²/decade`, 95% CI `[-8.1, +604.4]`, $p = 0.056$) and modified Mann–Kendall ($p = 0.069$) narrowly cross 5% → **`Methods disagree`**.
  - *Caribbean coast* (`bosque_perdida_caribe`): **`16,105 km²`** lost (**33%** of `48,118 km²` in 2000; Theil–Sen **`+253.3 km²/decade`**, 95% CI `[+50.1, +470.5]`, MK $p = 0.019$, OLS $p = 0.060$) → **`Methods disagree`**.
  - *Pacific lowlands* (`bosque_perdida_pacifico`): **`581 km²`** lost (**7%** of `7,824 km²` in 2000; Theil–Sen **`-14.2 km²/decade`**, 95% CI `[-20.6, -7.5]`, MK $p = 0.001$) → **`Trend detected`**.
- **Additional Global Benchmarks:**
  - *Colorado River at Lees Ferry (`1922–2025`, USGS 09380000):* **`-0.412 km³/decade`** (95% CI `[-0.652, -0.199]`, MK $p = 0.003$) → **`Trend detected`** over the full record, vs. **`-0.052 km³/decade`** ($p = 0.595$) → **`Not enough evidence of a trend`** since Glen Canyon Dam regulation began in 1963.
  - *Arctic Permafrost at Deadhorse, Alaska (`1978–2016`, GTN-P / PANGAEA):* **`+0.833 °C/decade`** at 20 m depth ($p < 0.001$) → **`Trend detected`**.
  - *Lake Superior Ice Cover at Bayfield (`1858–2019`, NSIDC G01377):* **`-3.19 days/decade`** ($p < 0.001$) → **`Trend detected`**.
  - *Central European Glaciers (`2000–2023`, GlaMBIE Region 11):* **`-0.48 m w.e./decade`** in annual mass balance ($p = 0.027$) → **`Trend detected`**.
  - *Sahel Rainy-Season Rainfall (`1981–2025`, CHIRPS v2.0 & CRU TS 4.10):* **`+19.5 mm/decade`** (CHIRPS) and **`+24.3 mm/decade`** (CRU), both $p < 0.001$ → **`Trend detected`** (reflecting partial recovery from the 1980s drought).

### 2.4 How the Statistical Verdict Engine Works
Implemented in `scripts/datos/tendencia.py` and `backend/clima_nic/estadistica/tendencia_robusta.py`, the trend engine enforces strict statistical hygiene on every annual series $(t_i, y_i)$ with $n \ge 10$ valid years:

1. **Theil–Sen Non-Parametric Estimator (Sen, 1968):**
   - Computes the median of all pairwise slopes $b_{\text{Sen}} = \text{median}\{(y_j - y_i)/(t_j - t_i) : i < j\}$ expressed per decade ($\times 10$), together with its exact rank-based 95% confidence interval (`scipy.stats.theilslopes`).
   - Resistant to up to ~29% corrupted or extreme outlier years (such as Hurricane Mitch or a single extreme El Niño).

2. **Modified Mann–Kendall Test with Hamed–Rao (1998) Autocorrelation Correction:**
   - Evaluates the Mann–Kendall $S$ statistic and tie-adjusted variance $V(S)$.
   - Removes the Theil–Sen trend, converts residuals to ranks, and computes lag-$k$ rank autocorrelations $r_k$. For all lags significant at the 5% level ($|r_k| > 1.96/\sqrt{n}$), it applies the Hamed & Rao (1998) variance inflation factor:
     $$\frac{V^*(S)}{V(S)} = \max\left(1,\; 1 + \frac{2}{n(n-1)(n-2)} \sum_{k \in \mathcal{L}} (n-k)(n-k-1)(n-k-2)\,r_k\right)$$
   - The correction factor is bounded below by $1.0$, ensuring positive autocorrelation never inflates the effective sample size or produces false-positive $p$-values.

3. **Ordinary Least Squares (OLS) with AR(1) Effective Degrees of Freedom (Santer et al., 2000):**
   - Fits $y_t = \alpha + \beta t + \varepsilon_t$ and estimates lag-1 residual autocorrelation $r_1$. When $r_1 > 0$, effective sample size is reduced to $n_{\text{eff}} = n \frac{1 - r_1}{1 + r_1}$, widening the $t$-distribution 95% confidence interval accordingly.

4. **Ordinary Least Squares with Newey–West (1987) HAC Standard Errors:**
   - Computes heteroskedasticity and autocorrelation consistent (HAC) covariance using a Bartlett kernel up to lag $L = \lfloor 4(n/100)^{2/9} \rfloor$, providing a parametric 95% confidence interval robust to serial correlation and changing variance.

5. **Consensus Verdict Rule:**
   - **`Trend detected` (`tendencia_detectada`):** All three 95% confidence intervals (Theil–Sen, AR(1)-adjusted OLS, and Newey–West HAC) exclude zero with the **same sign**, **and** the Hamed–Rao modified Mann–Kendall test has $p < 0.05$.
   - **`Not enough evidence of a trend` (`evidencia_insuficiente`):** None of the estimators reject the null hypothesis of zero slope at the 95% confidence level.
   - **`Methods disagree` (`metodos_discrepan`):** At least one estimator's 95% confidence interval or Mann–Kendall test indicates a significant slope while another estimator's 95% confidence interval crosses zero.
   - **`Record too short for a trend test` (`demostracion_registro_corto`):** Applied automatically when a dataset has fewer than 10 annual values (e.g., SWOT satellite altimetry launched in 2022–2023).

### 2.5 Why "Not Enough Evidence of a Trend" Does Not Mean "No Change"
A central pedagogical goal of **Earth System Trend Detective**—highlighted both in the verdict cards and in the **Learn** tab—is preventing the classic statistical fallacy of interpreting $p \ge 0.05$ as proof of stability:
- **Signal-to-Noise Ratio & Internal Variability:** Whether a trend test crosses $p < 0.05$ depends on the ratio between the decadal slope, the year-to-year standard deviation $\sigma$, and the record length $n$ (Santer et al., 2011, `doi:10.1029/2011JD016263`).
- **Example 1 — Tropics vs. Canadian Prairies Temperature (`2001–2024`):** Over the same 24-year window, Nicaragua's air temperature has low interannual variance and shows a clear warming verdict (`+0.40 °C/decade`, 95% CI `[+0.21, +0.54]`, $p < 0.001$, `Trend detected`). In the **Canadian Prairies**, year-to-year swings exceed several degrees Celsius; a positive slope of `+0.18 °C/decade` has a 95% confidence interval of `[-0.57, +0.75] °C/decade` ($p = 0.637$), yielding `Not enough evidence of a trend`. That wide interval includes both cooling and rapid warming of $+0.75\text{ °C/decade}$—meaning 24 noisy years cannot yet pin down the rate, not that the Prairies are immune to warming.
- **Example 2 — Nicaragua Rainfall & El Niño (`2001–2024` vs. `1981–2025`):** Over 2001–2024, NASA GPM IMERG annual rainfall in Nicaragua has a negative slope (`-64.9 mm/decade`, 95% CI `[-233.2, +98.3]`, $p = 0.442$), returning `Not enough evidence of a trend` because El Niño and La Niña (NOAA ONI) drive large year-to-year swings (~31% of variance in CHIRPS). Removing the linear ENSO component or extending the window back to 1981 with CHIRPS narrows the uncertainty and reveals how window length and natural oscillations shape trend detection.
