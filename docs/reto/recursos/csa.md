# CSA resources: verified state and reproduction

Branch: `codex/recursos-csa`. Verification: 2026-11-13. Originals, credentials and raster masks stay outside Git. NDVI/LST and UI integration belong to the other assigned areas.

| Requirement | State | Evidence |
|---|---|---|
| Canadian region | Delivered | `data/regiones_canada.geojson`, CAN_prairies; reproducible official source |
| SWOT + longer record | Delivered | 211 Cocibolca and 123 Xolotlán valid SWOT observations; 1,332 G-REALM observations |
| Radar | Real-data demonstration; classifier not validated | 75 ASF OPERA VV bursts, three dates, masks and candidate areas; RCM availability unresolved behind EODMS authentication |
| Canadian IMERG + GISTEMP | Calculated | 24 annual values each, 2001–2024; existing source adapters unchanged |
| Ecosystem guided questions | Written in English | Copy below, with CSA citation |
| SWOT–SAR common dates | Compared, scientifically inconclusive | Three exact calendar-day pairs on a fixed partial lake domain; no physical water-area trend claimed |

## 1. Prairies: Canadian region for agent 1

`CAN_prairies` is the AAFC National Ecological Framework v2.2 Prairies ecozone, 48.9949–54.245° N. Source: [Geo.ca discovery](https://geo.ca/home/?keys=Terrestrial%20Ecozones%20of%20Canada), [official dataset](https://open.canada.ca/data/en/dataset/7ad7ea01-eb23-4824-bccc-66adb7c5bdf8), [AAFC GeoJSON](https://agriculture.canada.ca/atlas/data_donnees/nationalEcologicalFramework/data_donnees/geoJSON/ez/nef_ca_ter_ecozone_v2_2.geojson). Contains information licensed under the [Open Government Licence – Canada](https://open.canada.ca/en/open-government-licence-canada). Full attribution and source SHA-256 are embedded in the feature.

Dissolve -> topology-preserving simplification at 0.01° -> make_valid -> precision 0.0001°. EPSG:6933 area changes from 467,029.4 to 467,127.9 km² (+0.021%); 4,058 coordinates become 605. Reproduction with `data/recursos/csa/construir_region_canada.py` matched the committed geometry properties. This is an analysis boundary, not a fine-scale official boundary.

## 2. Canadian climate, 2001–2024

`python data/recursos/csa/descargar_canada.py --destino ../imerg_canada` obtains all 288 monthly GPM_3IMERGM V07B HDF5 granules through CMR/GES DISC, then runs the Canadian reader. For existing originals: `python data/recursos/csa/canada.py --imerg-dir ../imerg_canada`. `imerg_consulta.json` stores source URLs; `canada_imerg.json` stores original hashes, monthly valid-area fractions, annual values and statistical results. Rates in mm/hr are multiplied by calendar-month hours before annual summation. Years require twelve valid months and each month >=95% valid polygon area. Coverage is calculated relative to the full polygon, not just the downloaded raster. Duplicate months and wrong rate units are rejected.

The 24 annual rainfall values have a mean of **435.17 mm/year**. Theil–Sen is **−30.4488 mm/decade**, 95% CI **[−84.4022, +13.4341]**; modified Mann–Kendall p=**0.1069**. Minimum monthly valid spatial coverage is **99.9966%**. Verdict: insufficient evidence of a trend.

Coverage is not equivalent to physical retrieval accuracy. The region lies within IMERG's latitude coverage, but snow/frozen-ground and cold-season precipitation uncertainty remain relevant. No station-based Canadian validation or warm-season sensitivity analysis has been completed; do not describe this result as proof that IMERG is unbiased here.

`python data/recursos/csa/canada.py` reproduces GISTEMP 250 km through the existing read/annual-aggregation adapters and shared area weights, bypassing only their Nicaragua-specific crop. `canada_gistemp.json` contains 24 annual values. Theil–Sen **+0.1751 °C/decade**, 95% CI **[−0.5684, +0.7535]**; modified Mann–Kendall p=**0.6374**. The temperature variable is anomaly relative to 1951–1980. At least ten valid months are required per year, as in the existing adapter. Spatial missing observations are renormalized; a spatial-coverage sensitivity assessment remains advisable. Raw NetCDF hash: `gistemp_fuente.json`.

Both climate outputs have role `tendencia`. `imerg.py` and `gistemp.py` are unchanged.

## 3. SWOT and G-REALM

[CSA SWOT](https://www.asc-csa.gc.ca/eng/satellites/swot/) describes the international mission and Canadian contribution. [Hydrocron](https://podaac.github.io/hydrocron/overview/) provides PLD-oriented LakeSP time series without login. Verified PLD IDs: **Cocibolca 7530096743**, **Xolotlán 7530093763**. Their LakeSP identification evidence, names, coordinates and product hashes are in `pld_lake_ids.json`. Both IDs were independently queried successfully with Hydrocron.

`lagos.py` builds Hydrocron requests, parses wrapped CSV, removes duplicates, fill/no_data records and quality_f >=2, and forms monthly means. Result: **211 valid Cocibolca observations**, July 2023–November 2026, and **123 Xolotlán observations**, August 2023–November 2026; 41 and 40 monthly values. Original responses, queries and hashes are versioned. Their role is **demostracion_registro_corto**, not climatic trend. The ten-year computational guard is a minimum guard, not a guarantee of adequate climatic inference.

All accepted SWOT records are partial observations (`partial_f=1`). SWOT area_total must not be interpreted as complete lake surface. WSE follows product quality conventions; a reported uncertainty of zero must not be interpreted as perfect precision.

[NASA GSFC G-REALM](https://earth.gsfc.nasa.gov/gwm/lake/Index), target **000351 Nicaragua**, supplies **1,332 valid Cocibolca heights, 1992-10-02–2026-11-07**. Source: `https://earth.gsfc.nasa.gov/gwm/zip/lake.10.tar.gz`; archive hash and extracts are retained. Column 15 is height in EGM2008 metres. Compatible `leer_grealm` returns dates/heights; `leer_grealm_gsfc` exposes mission detail. No Xolotlán G-REALM record was verified.

The 41 common monthly SWOT–G-REALM means yield r≈0.99 and SWOT−G-REALM bias≈−0.437 m (difference standard deviation≈0.073 m). Agreement supports cross-product consistency during this short common period; it does not independently prove long-term stability or establish the cause of the offset. Do not splice datums/products without a documented adjustment and uncertainty analysis.

## 4. Radar: real data and a failed fixed-threshold water interpretation

The [CSA RCM resource](https://donnees-data.asc-csa.gc.ca/en/dataset/rcm) points to EODMS. The initial hand-built query returned HTTP 400; retry through py-eodms-rapi/RCMImageProducts returned an authentication error. Neither result proves that open RCM scenes are absent. RCM availability remains unresolved. The demonstration explicitly uses **Sentinel-1 through ASF/Earthdata**, not RCM.

`python scripts/sar/opera_demostracion.py` downloads **75 OPERA_L2_RTC-S1_V1 VV bursts** on orbit T092 for **2024-03-04, 2024-04-21 and 2024-07-14**. Product URLs/hashes are in `sar_fuentes.json`. The [official OPERA guide](https://hyp3-docs.asf.alaska.edu/guides/opera_rtc_product_guide/) specifies gamma0 power, terrain-corrected, 30 m, without speckle filtering. Bursts are mosaicked without double counting, power is averaged to 100 m EPSG:6933, then converted with **10 log10**. Gamma0 is not relabelled as sigma0. Invalid/nonpositive power never becomes candidate water.

All dates are aligned to one grid. The common valid mask is fixed across dates; candidate water is tested at **−19/−17/−15 dB**. The common observed Cocibolca domain is **2,602.37 km²**, about **33.3%** of the 7,821.56 km² Natural Earth analysis polygon. No extrapolation to total lake area is performed. Natural Earth 10m lakes is public domain; the committed subset has Wikidata Q173862. Los Guatuzos and San Juan domains are explicitly named rectangular analytical windows, not official wetland/protected-area boundaries. Their common valid areas are 840.87 and 968.86 km².

`data/recursos/csa/sar_superficie.csv` has 27 candidate-area records. **These are low-backscatter classifications, not validated physical water extent.** On the same mapped lake domain, the −17 dB candidate fraction collapses on two dates despite the domain being a known lake. This is a quality-control failure of a universal threshold, not evidence that most of the lake dried up. Wind roughening, incidence, residual noise, mixed pixels and threshold choice are hypotheses to investigate, not established causal diagnoses. No climate trend or validated water-area change is published.

`backend/clima_nic/fuentes/sar_agua.py` also exposes the simpler calibrated sigma0-dB mask/area workflow for user-supplied GeoTIFFs. The real OPERA workflow keeps its different radiometry explicit. Original rasters, mosaics and masks remain in `../opera_rtc`, outside Git.

### CSA tutorial and notebook

`scripts/sar/agua_superficial.ipynb` adapts raster reading, CRS inspection and masked arrays from the [CSA Synthetic Aperture Radar Tutorial](https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial), Option 2 Python, BC Wildfire raster plot. Copyright Canadian Space Agency 2022; **MIT** license retained in `scripts/sar/LICENSE-CSA.txt`. Thresholding is a project extension, not a validated CSA water classifier. The notebook documents both input radiometries and runs the real OPERA workflow when `SAR_RUN_OPERA=1`. Without input/authorization it does not fabricate measurements.

## 5. Exact-calendar-day SWOT–SAR comparison

`sar_superficie.csv` and `comparacion_swot_sar.csv` use the same fixed partial lake domain. Same calendar day does not mean simultaneous acquisitions. Each radar acquisition time is encoded in the product IDs retained in the manifest.

| UTC day | SWOT WSE, EGM2008 m | Low-backscatter candidate area at −17 dB, km² | Fixed observed lake area, km² |
|---|---:|---:|---:|
| 2024-03-04 | 31.528 | 8.31 | 2602.37 |
| 2024-04-21 | 31.258 | 2267.65 | 2602.37 |
| 2024-07-14 | 31.713 | 171.02 | 2602.37 |

The lowest SWOT height coincides with the highest candidate area, while the candidate areas fail the known-lake sanity check. Therefore these data **do not validate a physical height–extent relation**. No correlation significance is claimed from three points. A validated classifier, broader spatial coverage and an independent shoreline reference are still required before publishing actual water-area changes.

SWOT since 2023 and three radar dates are short records. More observations might increase statistical power and make a persistent trend significant, as the challenge notes, but significance is not guaranteed. Longer records do not repair a biased or invalid classifier: seasonality, autocorrelation, sensor stability and hydrological management still require explicit treatment.

## 6. Guided questions — English copy

### Vegetation & ecosystems

Satellite observations can help identify changes in forest condition, land cover and habitat. Ask whether a greenness change persists across years and whether it coincides with disturbance or land-use change. Compare regional vegetation indicators with moisture and temperature, while keeping association separate from causal explanation. [CSA ecosystem monitoring](https://www.asc-csa.gc.ca/eng/satellites/everyday-lives/monitoring-and-protecting-our-ecosystems-from-space.asp).

### Water bodies

Satellite radar can map water extent, while SWOT measures water-surface elevation. Ask whether a lake's height and mapped area change together on comparable dates. Changes can reflect seasonal inflows, evaporation and water management, so a short record should be presented as a demonstration rather than a climatic trend. [CSA ecosystem monitoring](https://www.asc-csa.gc.ca/eng/satellites/everyday-lives/monitoring-and-protecting-our-ecosystems-from-space.asp).

## 7. Remaining scientific limits

Earthdata, GES DISC and ASF access now work. No credential is part of this PR. The remaining limitations are substantive: unresolved RCM availability, no validated SAR water classifier/independent shoreline, partial lake coverage and three same-day comparisons, plus Canadian winter-retrieval uncertainty and no station cross-check. These must not be presented as fully validated climatic water-area results. No merge, deployment or UI integration is included.


## Verification

`python -m pytest tests -q`: **111 passed, 1 skipped, 57 subtests passed**. Includes real-result consistency checks (24 Canadian years, 288 unique months, >=95% coverage; constant SAR domains and monotonic threshold sensitivity; three exact-day SWOT pairs), plus synthetic checks for units, leap years, missing months, fill values and power-to-dB conversion. Data acquisition and both processing scripts ran on real provider data. Existing imerg.py/gistemp.py are unchanged. Statistical significance and classifier validity are not inferred from software tests.
