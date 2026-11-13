# CSA resources — integration and evidence

Branch: `codex/recursos-csa`. Verification date: 2026-11-12.

## Canadian region: ready for agent 1

`data/regiones_canada.geojson` already existed on this branch and has been reproduced against the official AAFC source. Use feature/property ID **CAN_prairies**. Its actual latitude bounds are 48.9949–54.245° N. The National Ecological Framework v2.2 Prairies ecozone is dissolved and simplified with topology preservation at 0.01°, made valid and rounded to 0.0001°. EPSG:6933 area changes from 467,029.4 to 467,127.9 km² (+0.021%); 4,058 coordinates become 605. This is an analysis geometry, not a fine-scale official boundary.

Source: [Geo.ca discovery](https://geo.ca/home/?keys=Terrestrial%20Ecozones%20of%20Canada), [AAFC dataset](https://open.canada.ca/data/en/dataset/7ad7ea01-eb23-4824-bccc-66adb7c5bdf8), [official GeoJSON](https://agriculture.canada.ca/atlas/data_donnees/nationalEcologicalFramework/data_donnees/geoJSON/ez/nef_ca_ter_ecozone_v2_2.geojson). Contains information licensed under the [Open Government Licence – Canada](https://open.canada.ca/en/open-government-licence-canada). Attribution and original SHA-256 are embedded in the feature.

Being south of 60° N establishes coverage eligibility, **not measured IMERG quality**. Snow, frozen surfaces, retrieval uncertainty and monthly completeness must be evaluated before claiming good precipitation quality here.

## Canadian climate series

`python data/recursos/csa/canada.py` downloads and reads the existing GISTEMP adapter, calls the existing area-weighted mesh routine on the Canadian polygon and uses the existing annual aggregator and trend engine. The adapters themselves are unchanged. The wrapper bypasses `Gistemp.recortar`, which hardcodes a Nicaragua window. Output: `data/recursos/csa/canada_gistemp.json`, role `tendencia`; raw NetCDF SHA-256 in `gistemp_fuente.json`.

For 2001–2024 (24 annual values), GISTEMP 250 km gives Sen +0.1751 °C/decade, 95% CI [−0.5684, +0.7535]; modified Mann–Kendall p=0.6374, insufficient evidence. This describes this region and period only. Years require at least ten valid months, as in the existing adapter; spatial missing values are renormalized, not filled. A separate spatial-coverage sensitivity assessment remains necessary.

**IMERG is blocked, not calculated.** No Earthdata credentials are configured in this environment. In addition, `Imerg.leer` has a Nicaragua-only BBOX and cannot read Canadian cells as-is. Do not use its Nicaragua result for Canada. Resolution requires authenticated Canadian HDF5 acquisition and a separate regional reader/wrapper, without editing the read-only adapter. No Canadian rainfall trend is published. NDVI and LST belong to agent 1.

## SWOT and the longer lake record

[CSA SWOT mission](https://www.asc-csa.gc.ca/eng/satellites/swot/) explains the mission and Canada's instrument contribution. [Hydrocron](https://podaac.github.io/hydrocron/overview/) requires a verified PLD identifier from the lake database or LakeSP shapefile. Public Hydrocron access was tested with NASA's documented example ID **6350036102** (HTTP 200). **That example is not Cocibolca or Xolotlán and none of its values is used as a Nicaragua observation.** `acceso.json` records the exact query.

Both target PLD IDs remain unresolved (`LAKE_IDS` explicitly contains null). Hence there is no real SWOT time series for these lakes in this PR. `descargar_swot` and `NivelLagos.descargar(lake_id=...)` support explicit verified IDs and JSON-wrapped CSV. Parsing drops `no_data`, missing dates, nonfinite heights and SWOT fill magnitudes; original quality flags and uncertainties remain for scientific screening. A returned numeric record is not automatically a high-quality observation. Role: `demostracion_registro_corto`.

**Required intervention:** obtain Cocibolca and Xolotlán PLD IDs from PLD/LakeSP, verify geometry/name and product version, then run Hydrocron from 2023 and review quality flags. Do not substitute G-REALM target IDs.

G-REALM catalog and archive responded HTTP 200. Target **000351 Nicaragua** at 11.792° N, 85.714° W is Cocibolca. `cocibolca_grealm.txt` retains the original product header; `cocibolca_grealm.csv` contains **1,332 valid heights, 1992-10-02–2026-11-07**, from column 15 (EGM2008 metres). Archive URL and SHA-256 are in `grealm_fuente.json`. [NASA GSFC catalog](https://earth.gsfc.nasa.gov/gwm/lake/Index). The compatible `leer_grealm` API still returns dates and heights and now handles the 16-column GSFC format without parsing numeric headers as observations. No datum alignment to SWOT or INETER is assumed. No Xolotlán G-REALM series has been verified.

## RCM / Sentinel-1 and reproducible SAR notebook

[CSA RCM resource](https://donnees-data.asc-csa.gc.ca/en/dataset/rcm) and [EODMS](https://www.eodms-sgdot.nrcan-rncan.gc.ca/index-en.html) are the intended sources. An initial hand-built query was invalid (HTTP 400), **not evidence of absent scenes**. Retrying with `py-eodms-rapi`, collection `RCMImageProducts` and intersecting AOI −86,10.5,−83.5,12.7, returned an authentication error. `rcm_busqueda.json` is empty because that search failed, not because coverage is absent. Retry with a valid EODMS account before deciding RCM availability.

As a fallback discovery step, ASF public search found ten Sentinel-1 GRD_HD scenes intersecting that AOI in 2023, saved in `sentinel1_catalogo.geojson`; exact query in `acceso.json`. These are catalogue footprints, not processed water observations. Earthdata-authenticated image download and calibration remain pending. No claim is made that all scenes cover Cocibolca, Los Guatuzos and the San Juan River completely.

`scripts/sar/agua_superficial.ipynb` adapts raster/CRS/masked-array handling from [CSA's Python SAR tutorial](https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial), Option 2, BC Wildfire raster plot. Copyright CSA 2022; MIT license copied in `scripts/sar/LICENSE-CSA.txt`. The water threshold is our extension, not a classifier supplied or validated by CSA. The notebook requires a manifest of real calibrated, terrain-corrected sigma0 dB GeoTIFFs, EPSG:6933, clipped to the same AOI. It writes masks (255 no-data) and area/valid-area km² per date using affine pixel determinants. See notebook for preprocessing and parameter requirements. It executes without fabricating observations when imagery is absent. Role: `demostracion_registro_corto`.

Threshold −17 dB is illustrative: validate sensitivity and outlines, hold polarization/orbit/incidence/AOI constant and inspect shadow, wind and flooded vegetation. Tests use tiny synthetic rasters only to check units and masking; they are never published as observations.

## Height versus surface area on common dates

**No common measured dates are available:** target SWOT IDs and calibrated SAR rasters are missing. No correlation or paired table can yet be calculated. `sar_agua.fechas_comunes` joins exact ISO calendar dates only; it does not interpolate or relabel SWOT's own area as independent SAR area. Compare the same lake footprint and report acquisition times, vertical datum, WSE uncertainties, radar polarization and valid spatial coverage before interpreting a relation.

SWOT observations since 2023 and a short radar sample cannot establish a robust climatic trend. A longer record can improve power and might make a persistent change statistically significant, as the challenge suggests; that outcome is not guaranteed. Seasonality, autocorrelation, sensor changes, missing coverage and nonclimatic hydrological influences remain relevant even with more observations.

## Guided questions — copy for integration

### Vegetation & ecosystems

Satellite observations can help identify changes in forest condition, land cover and habitat. Ask whether a greenness change persists across years and whether it coincides with disturbance or land-use change. Compare regional vegetation indicators with moisture and temperature, while keeping association separate from a causal explanation. [CSA ecosystem monitoring](https://www.asc-csa.gc.ca/eng/satellites/everyday-lives/monitoring-and-protecting-our-ecosystems-from-space.asp).

### Water bodies

Satellite radar can map water extent, while SWOT measures water-surface elevation. Ask whether a lake's height and mapped area change together on comparable dates. Changes can reflect seasonal inflows, evaporation and water management, so a short record should be presented as a demonstration rather than a climatic trend. [CSA ecosystem monitoring](https://www.asc-csa.gc.ca/eng/satellites/everyday-lives/monitoring-and-protecting-our-ecosystems-from-space.asp).
