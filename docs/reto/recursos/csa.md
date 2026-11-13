# Recursos CSA y caso de contraste canadiense

Agente 3 · CSA · rama `codex/recursos-csa` (base `codex/verificacion-entrega`) · 13-11-2026.
Cubre los recursos #10 (Geo.ca) y #11 (SWOT) del [plan de integración](../PLAN_INTEGRACION_RECURSOS.md). Los recursos #9, #12 y #13 quedan en «Pendiente».

| Recurso | Estado | Salida | Prueba |
|---|---|---|---|
| #10 Geo.ca — región canadiense | Hecho | `data/regiones_canada.geojson` | `tests/test_recursos_csa.py::RegionCanada` |
| #11 SWOT — nivel de lagos | Hecho (Hydrocron) | `backend/clima_nic/fuentes/lagos.py`, `data/recursos/csa/` | `tests/test_recursos_csa.py::Hydrocron` |
| #9 RCM | Pendiente | — | — |
| #12 Monitoring and protecting our ecosystem from space | Pendiente | — | — |
| #13 Tutorial SAR | Pendiente | — | — |

## 1. Región de contraste: ecozona Prairies (Canadá)

**Elección.** Ecozona terrestre «Prairies» / «Prairies» (ECOZONE_ID 10) del National Ecological Framework for Canada. Es la ecozona agrícola de las praderas (Alberta, Saskatchewan y Manitoba). Está entera al sur de 60° N y su régimen de lluvia (semiárido continental con máximo en junio) contrasta con el de Nicaragua, que es tropical y monzónico.

**Fuente.**
- Conjunto: *Terrestrial Ecozones of Canada*, National Ecological Framework for Canada v2.2, Agriculture and Agri-Food Canada (AAFC). Ficha en el Portal de Gobierno Abierto, la misma que indexa Geo.ca: <https://open.canada.ca/data/en/dataset/7ad7ea01-eb23-4824-bccc-66adb7c5bdf8>. Búsqueda en Geo.ca: <https://geo.ca/home/?keys=Terrestrial%20Ecozones%20of%20Canada>.
- Archivo descargado el 12-11-2026: <https://agriculture.canada.ca/atlas/data_donnees/nationalEcologicalFramework/data_donnees/geoJSON/ez/nef_ca_ter_ecozone_v2_2.geojson> (4,7 MB, EPSG:4326). Su SHA-256 queda en las propiedades (`fuente.sha256_descarga`). El archivo original no se versiona.
- Licencia: **Open Government Licence – Canada** (<https://open.canada.ca/en/open-government-licence-canada>). Atribución exigida: «Contains information licensed under the Open Government Licence – Canada.» Está incluida en `licencia.atribucion` y debe aparecer en la pestaña *Sources* de la interfaz.

**Procesado** (`data/recursos/csa/construir_region_canada.py`, reproducible):
1. Selección de los polígonos con `ECOZONE_NAME_EN == "Prairies"` y disolución en una geometría (`shapely.union_all` + `make_valid`).
2. `shapely.simplify(tolerancia=0,01°, preserve_topology=True)`, `make_valid` y precisión de 1e-4°.
3. Áreas en EPSG:6933 (igual área), la misma proyección que `clima_nic.rutas.proyectar_6933`.

| Cifra | Valor |
|---|---|
| Geometría | `Polygon` válido, sin huecos |
| bbox (O, S, E, N) | −114,612; 48,995; −96,608; 54,245 |
| Área original | 467 029,4 km² |
| Área simplificada | 467 127,9 km² (+0,021 %) |
| Vértices | 4 058 → 605 |
| Tamaño del archivo | 13,4 KB |

**Esquema.** Las propiedades siguen el de `data/dominios.geojson` (`id`, `nombre`, `tipo`, `rol`, `bbox`, `area_km2`), con `id = "CAN_prairies"`, `tipo = "ecozona"` y `rol = "contraste"`. Además incluyen `fuente`, `licencia`, `simplificacion`, `area_km2_original`, `diferencia_area_pct`, vértices, `crs` y `fecha_descarga`.

### Calidad de IMERG sobre la región

- **Cobertura.** El punto más septentrional está en 54,245° N. Toda la región queda dentro de la franja de 60° S a 60° N, donde IMERG combina de forma completa microondas pasivas, IR geoestacionario y la calibración mensual con pluviómetros GPCC (en la versión Final).
- **Invierno.** Entre noviembre y marzo el suelo nevado o helado degrada la estimación por microondas pasivas sobre tierra: la superficie fría y la nieve se confunden con la dispersión de la precipitación sólida, y muchas estimaciones se descartan o se marcan como de baja calidad. En esos meses IMERG Final depende más del IR, de la propagación morfológica y de la corrección con GPCC. La precipitación sólida, además, se mide peor en los pluviómetros por el subcaptado por viento.
- **Recomendación.** Comparar Nicaragua y Prairies en la **estación cálida (mayo–septiembre)**, que concentra la mayor parte de la lluvia anual de las praderas. Si se usa el año completo, anotar la limitación invernal en la tarjeta de la variable. Es razonable revisar también la variable `precipitationQualityIndex` de IMERG en los meses de invierno.

## 2. SWOT: nivel de Cocibolca y Xolotlán

### lake_id de la Prior Lake Database (PLD)

| Lago | lake_id | Nombre en la PLD | Área de referencia PLD | Centroide PLD |
|---|---|---|---|---|
| Cocibolca (lago de Nicaragua) | **7530096743** | LAGO DE NICARAGUA;NICARAGUA | 7 807,8 km² | 11,535° N, 85,396° O |
| Xolotlán (lago de Managua) | **7530093763** | MANAGUA | 1 079,7 km² | 12,326° N, 86,334° O |

**Cómo se encontraron.** Con `earthaccess` y el `_netrc` de Earthdata (PO.DAAC no devolvió 401) se buscó el producto `SWOT_L2_HR_LakeSP_prior_2.0` sobre 11,0–12,5° N, 86,5–85,0° O y se descargó una pasada: `SWOT_L2_HR_LakeSP_Prior_027_522_NA_20250201T075737_20250201T081233_PIC2_01` (80 MB). Se leyeron los polígonos del grano dentro de 10,8–13° N, 87–84,5° O y se tomó para cada lago el polígono que contiene el punto de referencia, o el más cercano a él. Después se confirmó con `lake_name` y `p_ref_area`. El polígono de Cocibolca de esa pasada es parcial (`partial_f = 1`, 3 491 de 7 808 km²) y queda a 0,03° del punto 11,6° N 85,4° O; el nombre y el centroide de la PLD lo confirman. La evidencia está en `data/recursos/csa/pld_lake_ids.json` (nombre del grano, URL y SHA-256).

**Formato.** El `lake_id` tiene 10 dígitos: continente (7 = Norteamérica y Centroamérica), cuenca Pfafstetter, número de lago y tipo en el último dígito. `clima_nic.fuentes.lagos.es_lake_id` lo valida.

### Cliente Hydrocron (`backend/clima_nic/fuentes/lagos.py`)

- Petición: `GET https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries?feature=PriorLake&feature_id=<lake_id>&start_time=2023-07-26T00:00:00Z&end_time=<fin>T00:00:00Z&output=csv&fields=lake_id,time_str,wse,wse_u,area_total,quality_f,partial_f,dark_frac,ice_clim_f,xovr_cal_q,cycle_id,pass_id`. Sin cuenta: la API respondió 200.
- `leer_hydrocron`: acepta el sobre JSON (`results.csv`) o el CSV y quita duplicados exactos. Hydrocron repite la fila cuando un lago cae en dos granos de la misma pasada.
- `filtrar_hydrocron`: descarta las pasadas sin observación (`time_str = no_data`, `wse = -999999999999`) y las de `quality_f > 1`. Se aceptan 0 (bueno) y 1 (sospechoso); se excluyen 2 (degradado) y 3 (malo). Con `calidad_max=0` el filtro es estricto.
- `mensual_hydrocron`: media mensual de `wse`. `tendencia_si_suficiente` solo calcula pendiente con 10 años o más; si no, devuelve el motivo.
- `NivelLagos.descargar(..., fuente="swot", lago="cocibolca"|"xolotlan")` usa la misma petición dentro del adaptador registrado (`lagos`).
- Se conserva G-REALM: `leer_grealm` lee el formato antiguo y el formato GSFC de 16 columnas (altura EGM2008), y `leer_grealm_gsfc` devuelve el detalle por misión. El objetivo de Cocibolca es el **000351** (de la rama `codex/modelos-climaticos-nicaragua`, PR #4).
- Regenerar: `cd backend && python -m clima_nic.fuentes.lagos swot --fin 2026-11-13 --grealm lake000351.10d.2.txt`.

### Resultados (consulta del 13-11-2026)

Archivos en `data/recursos/csa/`: respuestas crudas `hydrocron_<lake_id>_<lago>.json`, `consultas_hydrocron.json` (URL, fecha UTC, SHA-256, resumen), `swot_observaciones.csv` (observaciones válidas), `swot_mensual.csv` y `comparacion_cocibolca_grealm_swot.csv`.

| | Cocibolca (7530096743) | Xolotlán (7530093763) |
|---|---|---|
| Filas recibidas (sin duplicados) | 223 | 224 |
| Pasadas sin observación (relleno) | 9 | 98 |
| Descartadas por calidad (`quality_f` ≥ 2) | 3 | 3 |
| Observaciones válidas (`quality_f` 0 / 1) | 211 (197 / 14) | 123 (107 / 16) |
| Periodo | 28-07-2023 a 05-11-2026 | 05-08-2023 a 06-11-2026 |
| Meses con dato | 41 | 40 |
| `wse` media (EGM2008) | 32,06 m | 40,03 m |
| `wse` mínima / máxima | 31,00 / 33,06 m | 38,68 / 41,54 m |
| Media mensual mínima / máxima | 31,10 m (05-2024) / 32,98 m (12-2024) | 38,75 m (05-2024) / 41,45 m (12-2024) |
| Tendencia | No se calcula: 3,3 años < 10 | No se calcula: 3,2 años < 10 |

Todas las observaciones válidas son parciales (`partial_f = 1`): la franja de SWOT (2 × 50 km) no cubre de una vez el lago entero. La `wse` sigue siendo válida como nivel del lago, pero `area_total` es solo la parte observada y **no** sirve como superficie del lago.

**Comparación con G-REALM en Cocibolca** (`comparacion_cocibolca_grealm_swot.csv`). Se usa la media mensual de la altura EGM2008 de G-REALM, objetivo 000351. El archivo `lake.10.tar.gz` de NASA GSFC se descargó el 13-11-2026 y se guardó el extracto `grealm_lake000351.10d.2.txt` (1 332 observaciones válidas, última del 07-11-2026). Se compara con la media mensual de SWOT en los meses comunes:

| Cifra | Valor |
|---|---|
| Meses comunes | 41 (07-2023 a 11-2026) |
| Correlación de Pearson | 0,99 |
| Sesgo medio (SWOT − G-REALM) | −0,437 m |
| Desviación típica de la diferencia | 0,073 m |
| RMSD | 0,443 m |

Las dos series siguen el mismo ciclo: mínimo en mayo–junio, máximo en diciembre y la subida de 2024 tras la sequía de El Niño 2023. Difieren en un desplazamiento casi constante de unos 44 cm. Ese desplazamiento es del tipo esperado entre productos de altimetría con procesados distintos: G-REALM mide un solo punto de cruce de su pasada de referencia (Jason-2) y SWOT promedia la parte observada del lago, y cada uno aplica sus propias correcciones geofísicas. La causa exacta no se ha investigado. Sin el desplazamiento, el error es de unos 7 cm, del orden de la precisión de ambos sistemas. Conclusión: SWOT **valida** la serie de G-REALM que usa el proyecto en el periodo común. Para empalmar las dos series habría que restar el sesgo medio y documentarlo.

Las cotas también son coherentes con la referencia de INETER del análisis geocientífico (Cocibolca 32,91 m y Xolotlán 42,73 m en octubre de 2010). En octubre de 2025, SWOT da 32,69 m en Cocibolca y 40,74 m en Xolotlán; Xolotlán queda unos 2,0 m por debajo de su cota de 2010. Esa diferencia de Xolotlán es compatible con los descensos de 2014–2016 que el análisis señala, pero no se ha validado con datos de INETER.

**Papel en el producto.** SWOT empieza en julio de 2023: unos 3,3 años no bastan para la tendencia 2001–2024 y no se presenta como tendencia. Su papel es de **contraste y validación**: confirma de forma independiente el nivel de G-REALM en Cocibolca durante el periodo común y aporta la única serie satelital de Xolotlán, que no está en G-REALM. Es el mismo caso de «registro corto» del enunciado: con una serie más larga, el mismo método podría llegar a ser concluyente.

## 3. Pendiente

### RCM (#9)
Pendiente: Angel enviará la tarea.

### Tutorial SAR en Python (#13)
Pendiente: Angel enviará la tarea. La carpeta reservada es `scripts/sar/`.

### Geo.ca (#10), ampliaciones
Pendiente: la región ya está (sección 1). Si se piden otras capas o regiones de Geo.ca, se añadirán aquí.

### Monitoring and protecting our ecosystem from space (#12)
Pendiente: Angel enviará la tarea.


## Supplement: Canadian climate, SAR and guided questions

## Canadian climate series

`python data/recursos/csa/canada.py` downloads and reads the existing GISTEMP adapter, calls the existing area-weighted mesh routine on the Canadian polygon and uses the existing annual aggregator and trend engine. The adapters themselves are unchanged. The wrapper bypasses `Gistemp.recortar`, which hardcodes a Nicaragua window. Output: `data/recursos/csa/canada_gistemp.json`, role `tendencia`; raw NetCDF SHA-256 in `gistemp_fuente.json`.

For 2001–2024 (24 annual values), GISTEMP 250 km gives Sen +0.1751 °C/decade, 95% CI [−0.5684, +0.7535]; modified Mann–Kendall p=0.6374, insufficient evidence. This describes this region and period only. Years require at least ten valid months, as in the existing adapter; spatial missing values are renormalized, not filled. A separate spatial-coverage sensitivity assessment remains necessary.

**IMERG is blocked, not calculated.** No Earthdata credentials are configured in this environment. In addition, `Imerg.leer` has a Nicaragua-only BBOX and cannot read Canadian cells as-is. Do not use its Nicaragua result for Canada. Resolution requires authenticated Canadian HDF5 acquisition and a separate regional reader/wrapper, without editing the read-only adapter. No Canadian rainfall trend is published. NDVI and LST belong to agent 1.

## RCM / Sentinel-1 and reproducible SAR notebook

[CSA RCM resource](https://donnees-data.asc-csa.gc.ca/en/dataset/rcm) and [EODMS](https://www.eodms-sgdot.nrcan-rncan.gc.ca/index-en.html) are the intended sources. An initial hand-built query was invalid (HTTP 400), **not evidence of absent scenes**. Retrying with `py-eodms-rapi`, collection `RCMImageProducts` and intersecting AOI −86,10.5,−83.5,12.7, returned an authentication error. `rcm_busqueda.json` is empty because that search failed, not because coverage is absent. Retry with a valid EODMS account before deciding RCM availability.

As a fallback discovery step, ASF public search found ten Sentinel-1 GRD_HD scenes intersecting that AOI in 2023, saved in `sentinel1_catalogo.geojson`; exact query in `acceso.json`. These are catalogue footprints, not processed water observations. Earthdata-authenticated image download and calibration remain pending. No claim is made that all scenes cover Cocibolca, Los Guatuzos and the San Juan River completely.

`scripts/sar/agua_superficial.ipynb` adapts raster/CRS/masked-array handling from [CSA's Python SAR tutorial](https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial), Option 2, BC Wildfire raster plot. Copyright CSA 2022; MIT license copied in `scripts/sar/LICENSE-CSA.txt`. The water threshold is our extension, not a classifier supplied or validated by CSA. The notebook requires a manifest of real calibrated, terrain-corrected sigma0 dB GeoTIFFs, EPSG:6933, clipped to the same AOI. It writes masks (255 no-data) and area/valid-area km² per date using affine pixel determinants. See notebook for preprocessing and parameter requirements. It executes without fabricating observations when imagery is absent. Role: `demostracion_registro_corto`.

Threshold −17 dB is illustrative: validate sensitivity and outlines, hold polarization/orbit/incidence/AOI constant and inspect shadow, wind and flooded vegetation. Tests use tiny synthetic rasters only to check units and masking; they are never published as observations.

## Height versus surface area on common dates

**No common SWOT–SAR measured dates are available:** calibrated SAR rasters are missing. No correlation or paired table can yet be calculated. `sar_agua.fechas_comunes` joins exact ISO calendar dates only; it does not interpolate or relabel SWOT's own area as independent SAR area. Compare the same lake footprint and report acquisition times, vertical datum, WSE uncertainties, radar polarization and valid spatial coverage before interpreting a relation.

SWOT observations since 2023 and a short radar sample cannot establish a robust climatic trend. A longer record can improve power and might make a persistent change statistically significant, as the challenge suggests; that outcome is not guaranteed. Seasonality, autocorrelation, sensor changes, missing coverage and nonclimatic hydrological influences remain relevant even with more observations.

## Guided questions — copy for integration

### Vegetation & ecosystems

Satellite observations can help identify changes in forest condition, land cover and habitat. Ask whether a greenness change persists across years and whether it coincides with disturbance or land-use change. Compare regional vegetation indicators with moisture and temperature, while keeping association separate from a causal explanation. [CSA ecosystem monitoring](https://www.asc-csa.gc.ca/eng/satellites/everyday-lives/monitoring-and-protecting-our-ecosystems-from-space.asp).

### Water bodies

Satellite radar can map water extent, while SWOT measures water-surface elevation. Ask whether a lake's height and mapped area change together on comparable dates. Changes can reflect seasonal inflows, evaporation and water management, so a short record should be presented as a demonstration rather than a climatic trend. [CSA ecosystem monitoring](https://www.asc-csa.gc.ca/eng/satellites/everyday-lives/monitoring-and-protecting-our-ecosystems-from-space.asp).
