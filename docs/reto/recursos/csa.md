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
