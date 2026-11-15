# Investigación de casos globales: Europa, África y Oriente Medio

Síntesis científica y guía de ingestión de datos para **Gnomon** (NASA Space Apps Challenge 2026), diseñada bajo el criterio estadístico del proyecto (`tendencia detectada`, `evidencia insuficiente` o `los métodos no coinciden`, evaluados conjuntamente mediante regresión lineal/HAC, Theil-Sen y Mann-Kendall modificado a un nivel base $\alpha = 0,05$). No duplica las series globales ya integradas en la aplicación (bandas latitudinales de GISTEMP, total mundial de GFED5 ni total mundial de GlaMBIE), sino que aporta desgloses regionales y casos hidroclimáticos, marinos, de vegetación, de aerosoles y de almacenamiento de agua propios de Europa, África y Oriente Medio.

---

## 1. Resumen

| caso | región | variable | periodo | tendencia publicada (con unidades por década) | veredicto esperado | confianza |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `europa_calor_extremo_tx90p` | Europa (occidental y central) | Frecuencia de días cálidos extremos (`TX90p`, %>P90 1961–1990) | 1950–2025 | `+0,33 °C/década` en extremos cálidos y frecuencia `>3×` en 1950–2018 (`TX90p`, Lorenz et al. 2019) | `tendencia detectada` | Alta |
| `mediterraneo_sst_olas_calor_marinas` | Mar Mediterráneo | Temperatura superficial del mar (`SST` media anual) y días de ola de calor marina | 1982–2025 | `~+0,41 °C/década` (1982–2018, Pisano et al. 2020); `+1,3 ± 0,25 eventos OCM/década` y `+3,6 ± 1,16 días/década` (Dayan et al. 2023); `+0,366 °C/década` (cálculo OISST 1982–2025) | `tendencia detectada` | Alta |
| `alpes_glaciares_glambie` | Europa central (Alpes y Pirineos, región 11 GlaMBIE) | Balance de masa glaciar específico (`m w.e./año`) y masa acumulada (`Gt`) | 2000–2024 | `-0,480 m w.e./año/década` (Sen 2001–2024 en tasa anual) y `-18,14 Gt/década` en masa acumulada; pérdida de `~39 %` del volumen regional en 2000–2023 (GlaMBIE Team 2025) | `tendencia detectada` (tasa específica y masa acumulada); `los métodos no coinciden` (flujo anual `Gt/año`) | Alta |
| `sahel_lluvia_recuperacion` | Sahel (África occidental y central) | Precipitación acumulada estacional JJAS (`mm/año`) | 1901–2025 (foco pos-1982) | Recuperación positiva parcial en el Sahel central y oriental pos-1983 (concentrada en septiembre y tormentas intensas; sin pendiente lineal única continental, Biasutti 2019) | `los métodos no coinciden` | Media |
| `sahel_ndvi_enverdecimiento` | Sahel central y occidental | `NDVI` medio anual de estación de crecimiento (`Jul–Oct`, adimensional) | 2000–2025 (MODIS) / 1981–2025 | Reverdecimiento generalizado 1982–2011 en zonas pastorales como Gourma (Malí), contrastado con declives agrícolas locales como Fakara (Níger); sin tasa lineal única regional (Dardel et al. 2014) | `los métodos no coinciden` | Media |
| `africa_oriental_lluvias_largas_cortas` | África oriental y Cuerno de África | Lluvia estacional MAM (Lluvias Largas) vs. OND (Lluvias Cortas) (`mm/temporada`) | 1981–2025 | MAM: `-6,5 a -29,5 mm/temporada/década`; OND: `+14,4 a +23,6 mm/temporada/década` desde mediados de 1980 (Palmer et al. 2023) | `los métodos no coinciden` | Media |
| `africa_austral_cabo_sequia` | Cabo Occidental, Sudáfrica | Lluvia acumulada invernal MJJAS (`mm/año`) | 1981–2025 | Probabilidad del episodio 2015–2017 triplicada (Otto et al. 2018) a `5–6×` mayor (Pascale et al. 2020) por el calentamiento; tendencia observada en series cortas atenuada por variabilidad | `evidencia insuficiente` | Baja-Media |
| `mar_caspio_nivel_altimetria` | Mar Caspio | Anomalía de nivel medio anual del mar/lago (`m`) | 1992–2025 | `-0,672 m/década` (`-6,72 cm/año`) en 1996–2015 (frente a `+1,274 m/década` en 1979–1995; Chen et al. 2017) | `tendencia detectada` (era pos-1995) | Alta |
| `lagos_chad_victoria_altimetria` | Lagos Victoria y Chad (África) | Nivel medio anual de superficie de agua (`m`) | 1992–2025 | Victoria: oscilaciones interanuales abruptas ligadas al ENSO/IOD (salto extremo 2019–2020, Khaki y Awange 2021); Chad: pérdida `>90 %` entre 1960 y 1980, luego estabilidad estacional pos-1990 en `~2400–2500 km²` (Pham-Duc et al. 2020) | `evidencia insuficiente` | Media |
| `sahara_sahel_polvo_aod` | Sahara y Sahel norte | Profundidad óptica de aerosoles de polvo a 550 nm (`DOD`/`DAOD`, adimensional) | 1980–2025 | Variaciones regionales y descenso reciente (2001–2018) en el norte de África/Sahel modulados por viento superficial y vegetación, con alta discrepancia entre sensores y reanálisis (Voss y Evan 2020; Song et al. 2021) | `los métodos no coinciden` | Media |
| `orientemedio_norte_africa_grace_tws` | Oriente Medio (Tigris-Éufrates y Arabia) | Almacenamiento total de agua terrestre (`TWS` en `cm` de agua equivalente) | 2002–2025 | Tigris-Éufrates: `-27,2 ± 0,6 cm LWE/década` (`-27,2 mm/año` TWS) y `-17,3 ± 2,1 cm LWE/década` en acuíferos 2003–2009 (Voss et al. 2013); Arabia/Oriente Medio: `~-61 Gt/década` (`6,1 Gt/año`, Rodell et al. 2018) | `tendencia detectada` | Alta |
| `mediterraneo_sabanas_africa_gfed5` | Sabanas africanas del norte vs. Europa mediterránea | Área quemada anual acumulada (`Mha/año` o `% área/año`) | 1997–2020 | Declive global de `-24,3 ± 8,8 %` en 1998–2015 (`~-13,5 %/década`) dominado por la fragmentación agrícola en sabanas africanas (Andela et al. 2017); Europa mediterránea con declive débil o no monótono por supresión y picos meteorológicos (Turco et al. 2016) | `tendencia detectada` (sabanas africanas) / `evidencia insuficiente` (Mediterráneo anual) | Alta (sabanas) / Media (Med) |

---

## 2. Fichas por caso

### Caso 1: Días cálidos extremos en Europa (`europa_calor_extremo_tx90p`)
- **ID sugerido:** `europa_calor_extremo_tx90p`
- **Título e interfaz en inglés:** **European Extreme Heat Days Frequency**
  *Counts how often summer maximum temperatures exceed the local historical 90th percentile across European land stations. It tracks how rapidly heatwaves like 2003, 2018, and 2022 have shifted from rare events to frequent occurrences.*
- **Lugar:** Europa central y occidental (`[48.5, 9.0]`; caja: `lat 36.0° a 60.0° N`, `lon -10.0° a 25.0° E`).
- **Variable, unidad y agregación:** Porcentaje o número anual de días con temperatura máxima diaria ($TX$) superior al percentil 90 móvil de la ventana de 5 días para el periodo base 1961–1990 (`TX90p`, en `% días` o `días/año`), promediado espacialmente con ponderación por $\cos(\text{lat})$.
- **Conjunto de datos:** **E-OBS** (ECA&D), versión **v34.0e** (`0.1°` regular, diario, `1950-01-01` al presente). Descarga directa NetCDF sin cuenta:
  - `https://knmi-ecad-assets-prd.s3.amazonaws.com/ensembles/data/Grid_0.1deg_reg_ensemble/tx_ens_mean_0.1deg_reg_v34.0e.nc`
  - Respaldo global precalculado de índices extremos sin cuenta: **HadEX3** (`1.25° × 1.875°`, `1901–2018`): `https://www.metoffice.gov.uk/hadobs/hadex3/data/HadEX3_TX90p_1901-2018_ADW_61-90_1.25x1.875deg.nc.gz`
- **Pasos para construir la serie anual:**
  1. Descargar `tx_ens_mean_0.1deg_reg_v34.0e.nc` y recortar a `lat [36, 60]`, `lon [-10, 25]`.
  2. Calcular en cada celda el umbral diario del percentil 90 de $TX$ sobre 1961–1990 (ventana centrada de 5 días).
  3. Contar por año calendario cuántos días superan ese umbral (exigiendo $\ge 90\,\%$ de días válidos anuales por celda).
  4. Promediar sobre celdas válidas ponderando por $\cos(\text{lat})$ para obtener `TX90p` en días/año (o verificar directamente con la variable `Ann` de `HadEX3_TX90p`).
  5. Evaluar tendencia sobre 1950–2025 y comparar con la subventana satelital 1980–2025.
- **Resultado publicado:** **Lorenz et al. (2019)** (*Geophysical Research Letters*, `doi:10.1029/2019GL082062`) demuestran que el 94 % de las estaciones ECA&D analizadas muestran calentamiento en los extremos cálidos estivales entre 1950 y 2018 (`+0,33 °C/década` de media, más rápido que la temperatura media de verano) y que el número de días de calor extremo en Europa se ha más que triplicado. **Vautard et al. (2023)** (`doi:10.1038/s41467-023-42143-3`) y **Fischer y Schär (2010)** (`doi:10.1038/ngeo866`) confirman que los modelos climáticos suelen subestimar este ritmo observado de calentamiento diurno extremo en Europa occidental.
- **Veredicto esperado:** **`tendencia detectada`**. Tanto MCO/HAC como Mann-Kendall modificado y Theil-Sen superan holgadamente el umbral $p < 0,05$ tras los veranos extremos de 2003, 2018, 2019 y 2022–2023.
- **Advertencias:** En E-OBS v34.0e la densidad de estaciones varía según el país y decrece en las últimas décadas o en regiones mediterráneas periféricas respecto a Europa central (**Cornes et al. 2018**, `doi:10.1029/2017JD028200`); los años 2003, 2018 y 2022 actúan como puntos de apalancamiento elevados, pero el rechazo nulo se sostiene incluso eliminando los últimos 3 años; la influencia directa del ENSO en el verano europeo es débil frente al patrón AMO/NAO y las retroalimentaciones de humedad del suelo.
- **Frase en inglés para la app:** `Published check: Across Europe, 94% of ECA&D stations warmed in summer heat extremes (+0.33 °C/decade on average) and extreme-heat days more than tripled over 1950–2018 (Lorenz et al. 2019, doi:10.1029/2019GL082062).`

---

### Caso 2: Calentamiento superficial y olas de calor marinas en el Mediterráneo (`mediterraneo_sst_olas_calor_marinas`)
- **ID sugerido:** `mediterraneo_sst_olas_calor_marinas`
- **Título e interfaz en inglés:** **Mediterranean Sea Surface Warming**
  *Measures annual average sea surface temperature and marine heatwave days across the Mediterranean basin. Because it is a semi-enclosed sea, surface waters warm much faster than the global ocean average.*
- **Lugar:** Cuenca del mar Mediterráneo (`[38.0, 15.0]`; caja: `lat 30.2° a 45.8° N`, `lon -5.5° a 36.2° E`, con máscara marina).
- **Variable, unidad y agregación:** Media anual ponderada por área de la temperatura superficial del mar (`SST` en `°C`), complementada con conteo anual de días en ola de calor marina (`MHW days`, episodios $\ge 5$ días por encima del percentil 90 climatológico de 1982–2011 según Hobday et al. 2016).
- **Conjunto de datos:** **NOAA OISST v2.1** (`0.25° × 0.25°`, diario/mensual, `1981-09` a `2026`). Sin cuenta:
  - API ERDDAP con recorte directo (PFEG/CoastWatch): `https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180`
  - Archivos mensuales consolidados (NOAA PSL, `2.25 GB` global): `https://downloads.psl.noaa.gov/Datasets/noaa.oisst.v2.highres/sst.mon.mean.nc`
  - Archivos diarios por fecha (NOAA NCEI): `https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/v2.1/access/avhrr/`
- **Pasos para construir la serie anual:**
  1. Consultar `ncdcOisst21Agg_LonPM180` (o descargar `sst.mon.mean.nc`) dentro de `[30.2, 45.8] N`, `[-5.5, 36.2] E` excluyendo mar Negro/Atlántico mediante máscara de cuenca.
  2. Para SST anual, promediar los 12 meses de cada año completo `1982–2025` ponderando por $\cos(\text{lat})$ en celdas oceánicas.
  3. Para MHW (si se usa OISST diario), definir por celda el percentil 90 estacional (ventana de 11 días en 1982–2011) y sumar días anuales en rachas $\ge 5$ días.
  4. Ejecutar `analizar(anios, sst_anual, "°C")` sobre 1982–2025.
- **Resultado publicado:** **Pisano et al. (2020)** (*Remote Sensing*, `doi:10.3390/rs12010132`) miden un calentamiento superficial medio de `~+0,041 ± 0,006 °C/año` (`~+0,41 °C/década`) en 1982–2018. **Dayan et al. (2023)** (*Frontiers in Marine Science*, `doi:10.3389/fmars.2023.1045138`) reportan aumentos en superficie de `+1,3 ± 0,25` eventos de ola de calor marina por década y `+3,6 ± 1,16` días de duración media por década (definición **Hobday et al. 2016**, `doi:10.1016/j.pocean.2015.12.014`). En nuestra ejecución directa de control sobre un muestreo mensual de `ncdcOisst21Agg_LonPM180` (1982–2025, `n = 44`), el motor estadístico del proyecto arrojó `Sen = +0,366 °C/década` (`IC 95 % [0,296, 0,437]`), `MCO = +0,359 °C/década`, `MK p < 0,0001`.
- **Veredicto esperado:** **`tendencia detectada`**. La señal térmica es monótona, físicamente robusta y con intervalo HAC ampliamente separado de cero.
- **Advertencias:** Cambio de sensores AVHRR en el paso NOAA-16/17/18/MetOp-A y fusión con boyas/buques desde 2007 en OISST v2.1 (**Huang et al. 2020**, `doi:10.25921/RE9P-PT57`); la definición de MHW sobre una climatología fija (1982–2011) hace que para 2022–2024 gran parte del verano supere el percentil 90 por desplazamiento de la media (**Darmaraki et al. 2024**, `doi:10.12681/mms.38392`); el ruido por latitud obliga a enmascarar estrictamente golfo de Vizcaya y mar Negro dentro de la caja rectangular.
- **Frase en inglés para la app:** `Published check: Mediterranean sea surface temperatures warmed at ~0.41 °C/decade over 1982–2018 (Pisano et al. 2020, doi:10.3390/rs12010132), alongside rising marine heatwave frequency (Dayan et al. 2023, doi:10.3389/fmars.2023.1045138).`

---

### Caso 3: Pérdida de masa glaciar en los Alpes y Europa central (`alpes_glaciares_glambie`)
- **ID sugerido:** `alpes_glaciares_glambie`
- **Título e interfaz en inglés:** **European Alps Glacier Mass Loss**
  *Tracks annual specific ice mass loss across glaciers in the European Alps and Central Europe using combined satellite and field measurements. It shows both yearly melt anomalies and accelerating ice shrinkage since 2000.*
- **Lugar:** Europa central — Alpes europeos y Pirineos (`[46.5, 10.5]`; región GlaMBIE 11; caja aproximada `lat 42.5° a 47.8° N`, `lon 0.0° a 16.5° E`).
- **Variable, unidad y agregación:** Balance de masa específico anual (`annual_mwe` en `m w.e./año`, tasa anual equivalente de agua) y cambio anual/acumulado de masa (`annual_gt` y `cum_gt` en `Gt`). Serie ya anualizada en año calendario (y disponible también en año hidrológico).
- **Conjunto de datos:** **WGMS GlaMBIE v1.0.0** (`10.5904/wgms-glambie-2024-07`), archivo `glambie_results_20240716/calendar_years/11_central_europe.csv` (`2000–2024`, agregado regional). Descarga directa ZIP sin cuenta:
  - `https://wgms.ch/downloads/GlaMBIE_Data_DOI_10.5904_wgms-glambie-2024-07.zip`
- **Pasos para construir la serie anual:**
  1. Descargar el archivo ZIP de GlaMBIE v1.0.0 y extraer `calendar_years/11_central_europe.csv`.
  2. Cargar las columnas `year` (2001–2024), `annual_mwe` (`m w.e.`) y `annual_gt` (`Gt`).
  3. Acumular `annual_gt` desde el año inicial para obtener `cum_gt` (pérdida total acumulada).
  4. Analizar tanto `annual_mwe` (aceleración de la tasa específica de fusión) como `cum_gt` con `analizar()` y registrar la divergencia con `annual_gt`.
- **Resultado publicado:** **GlaMBIE Team (2025)** (*Nature*, `doi:10.1038/s41586-024-08545-z`) documenta que Europa central registró la mayor pérdida relativa mundial entre 2000 y 2023, perdiendo cerca del `39 %` de su masa glaciar total. En nuestra verificación directa sobre `11_central_europe.csv` (años calendario `2001–2024`), la tasa específica media es `-1,062 m w.e./año` con tendencia significativa hacia balances más negativos (`MCO = -0,610 m w.e./año/década`, `IC [-1,126, -0,094]`, `p = 0,0234`; `Sen = -0,480 m w.e./año/década`, `MK p = 0,0273`), y la masa acumulada alcanza `-47,33 Gt` en 2024 (`Sen = -18,14 Gt/década`, `MK p < 0,0001`). En contraste, en `annual_gt` los métodos discrepan (`Sen = -0,757 Gt/año/década`, `MK p = 0,0500`) porque el área glaciar alpina se contrajo de `2140,6 km²` (2000) a `1693,2 km²` (2024).
- **Veredicto esperado:** **`tendencia detectada`** para `annual_mwe` y `cum_gt` en años calendario (`2001–2024`), pero **`los métodos no coinciden`** para la tasa anual absoluta `annual_gt` y **`evidencia insuficiente`** en `annual_gt` por año hidrológico (`MK p = 0,1574`).
- **Advertencias:** Alta sensibilidad a los tres años extremos recientes (2022–2024): al excluir `2022–2024` del balance calendario `annual_mwe`, la pendiente MCO cae a `-0,269 m w.e./año/década` (`IC [-0,662, +0,124]`, sin significancia); los primeros años combinan pocos glaciares in situ con altimetría/gravimetría satelital; los resultados en `Gt/año` subestiman la intensificación del derretimiento por pérdida de superficie glaciar.
- **Frase en inglés para la app:** `Published check: Central Europe (Alps) lost ~39% of its glacier mass during 2000–2023, the steepest relative decline globally (GlaMBIE Team 2025, doi:10.1038/s41586-024-08545-z; data doi:10.5904/wgms-glambie-2024-07).`

---

### Caso 4: Recuperación estacional de las lluvias en el Sahel (`sahel_lluvia_recuperacion`)
- **ID sugerido:** `sahel_lluvia_recuperacion`
- **Título e interfaz en inglés:** **Sahel Wet Season Rainfall Recovery**
  *Measures summer monsoon rainfall totals across the African Sahel from the 1970s–1980s droughts to the present. It distinguishes long-term secular drying from the partial post-1983 rainfall recovery driven by late-season storms.*
- **Lugar:** Franja del Sahel occidental y central (`[14.5, 2.0]`; caja: `lat 11.0° a 18.0° N`, `lon -16.0° a 20.0° E`, separando Sahel occidental `[-16, -5]` y central/oriental `[-5, 20]`).
- **Variable, unidad y agregación:** Suma anual de lluvia de la estación húmeda principal junio–septiembre (`JJAS`, en `mm/año`), promediada por área terrestre.
- **Conjunto de datos:** **GPCC Full Data Monthly v2022** (`0.25°`, `1891–2020`, DWD opendata, sin cuenta) y **CRU TS v4.10** (`0.5°`, `1901–2025`, UEA, sin cuenta), complementados para alta resolución desde 1981 con **CHIRPS v2.0** (`0.05°`, `1981–presente`, sin cuenta):
  - GPCC v2022 (`2011–2020`, análogo por décadas): `https://opendata.dwd.de/climate_environment/GPCC/full_data_monthly_v2022/025/full_data_monthly_v2022_2011_2020_025.nc.gz`
  - CRU TS v4.10: `https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/cruts.2604091129.v4.10/pre/cru_ts4.10.1901.2025.pre.dat.nc.gz`
  - CHIRPS v2.0 mensual: `https://data.chc.ucsb.edu/products/CHIRPS/v2.0/global_monthly/netcdf/chirps-v2.0.monthly.nc`
- **Pasos para construir la serie anual:**
  1. Descargar `cru_ts4.10.1901.2025.pre.dat.nc.gz` (y `chirps-v2.0.monthly.nc` para 1981–2025).
  2. Recortar a `lat [11, 18] N`, `lon [-16, 20] E` (y analizar por separado el subdominio occidental y el central/oriental).
  3. Sumar los meses junio–septiembre (`JJAS`) de cada año para obtener el total monzónico en `mm/año`.
  4. Calcular la media ponderada por $\cos(\text{lat})$ solo sobre celdas con datos en todo el periodo.
  5. Comparar los veredictos entre las ventanas `1901–2025`, `1950–2025` y `1983–2025`.
- **Resultado publicado:** **Biasutti (2019)** (*WIREs Climate Change*, `doi:10.1002/wcc.591`) y **Nicholson et al. (2018)** (*Global and Planetary Change*, `doi:10.1016/j.gloplacha.2017.12.014`) sintetizan que, tras las megasequías de 1970–1985, el Sahel muestra una recuperación parcial concentrada en la parte central y oriental y en el final de la temporada (septiembre), con tormentas más intensas y mayor intermitencia; en cambio, en la costa occidental (Senegal/Mauritania) la recuperación fue más tardía y débil, y los niveles acumulados rara vez igualan los máximos húmedos de 1950–1965.
- **Veredicto esperado:** **`los métodos no coinciden`** (alta sensibilidad a la ventana elegida: de tendencia positiva pos-1983 a tendencia nula o negativa si se inicia en 1950; además MCO y MK/Sen divergen cuando el quiebre abrupto en los años 1970–1980 domina la serie secular).
- **Advertencias:** La densidad de pluviómetros en CRU TS y GPCC cae drásticamente en el Sahel pos-1990 y CHIRPS/CRU pueden diferir en el oeste; la variabilidad multidecadal atlántica (AMO/gradiente SST interhemisférico) y el ENSO modulan los años secos; empezar en 1983–1984 (piso de la sequía) infla artificialmente la pendiente de «recuperación».
- **Frase en inglés para la app:** `Published check: Post-1980s Sahel rainfall shows a spatially uneven partial recovery—strongest in the central-eastern Sahel and late monsoon—driven by more intense storms (Biasutti 2019, doi:10.1002/wcc.591; Nicholson et al. 2018, doi:10.1016/j.gloplacha.2017.12.014).`

---

### Caso 5: Enverdecimiento satelital del Sahel frente a la lluvia (`sahel_ndvi_enverdecimiento`)
- **ID sugerido:** `sahel_ndvi_enverdecimiento`
- **Título e interfaz en inglés:** **Sahel Vegetation Greening Trends**
  *Tracks satellite vegetation greenness (NDVI) during the Sahel growing season against monsoon rainfall. It tests where landscape greening stems solely from wetter years or diverges due to land use and grazing pressures.*
- **Lugar:** Cinturón agro-pastoral del Sahel (`[14.5, 0.0]`; caja: `lat 12.0° a 17.5° N`, `lon -15.0° a 18.0° E`).
- **Variable, unidad y agregación:** Índice de vegetación de diferencia normalizada (`NDVI` adimensional, escala `0–1`), promediado anualmente sobre los meses de vegetación máxima (`julio–octubre`) y ponderado espacialmente por área.
- **Conjunto de datos:** **NASA MODIS `MOD13C2` v061** (`0.05°`, mensual, `2000-02` al presente). Requiere cuenta gratuita **NASA Earthdata Login**:
  - Catálogo protegido LPCLOUD (CMG mensual v061): `https://cmr.earthdata.nasa.gov/search/granules.json?short_name=MOD13C2&version=061` (acceso directo autenticado bajo `https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD13C2.061/...`).
  - Serie histórica desde 1981 sin cuenta en **NOAA NCEI NDVI CDR**: `https://www.ncei.noaa.gov/data/land-normalized-difference-vegetation-index/access/` (solo para contextualizar 1981–2013 AVHRR v5 `doi:10.7289/V5ZG6QH9`; no mezclar con VIIRS v1 `2014+` sin homogeneización).
- **Pasos para construir la serie anual:**
  1. Consultar los gránulos mensuales `MOD13C2.061` (meses `07, 08, 09, 10`, años `2000–2025`) vía CMR y autenticar con token Earthdata.
  2. Aplicar el factor de escala (`× 1e-4`), enmascarar con `CMG 0.05 Deg Monthly pixel reliability` (solo valores buenos `<= 1`) y recortar a `lat [12, 17.5] N`, `lon [-15, 18] E`.
  3. Promediar julio–octubre por año y por píxel, y luego promediar espacialmente (separando subregiones como Gourma/Malí vs. oeste de Níger).
  4. Contrastar los residuales NDVI–lluvia JJAS frente a CHIRPS/CRU usando `analizar()`.
- **Resultado publicado:** **Herrmann et al. (2005)** (*Global Environmental Change*, `doi:10.1016/j.gloenvcha.2005.08.004`) y **Olsson et al. (2005)** (`doi:10.1016/j.jaridenv.2005.03.008`) documentaron un reverdecimiento extendido del Sahel en `1982–2003` controlado principalmente por la lluvia, refutando una desertificación irreversible uniforme. **Dardel et al. (2014)** (*Remote Sensing of Environment*, `doi:10.1016/j.rse.2013.09.011`) validaron ese reverdecimiento en `1981–2011` en zonas pastorales (Gourma, Malí), pero demostraron tendencias negativas locales por presión agrícola y encostramiento del suelo (Fakara, Níger). **Tong et al. (2017)** (`doi:10.1016/j.rse.2017.01.030`) advierten sobre discontinuidades según sensores e índices.
- **Veredicto esperado:** **`los métodos no coinciden`**. En la ventana pos-2000 de un solo sensor (`MOD13C2.061`), la señal es heterogénea entre subregiones y oscila con la lluvia interanual; mezclar 1981–2013 AVHRR (`V5ZG6QH9`) con 2014+ VIIRS (`gakh-st76`) en el CDR de NOAA introduce un salto de calibración artificial de sensor.
- **Advertencias:** **Ruptura crítica AVHRR→VIIRS en 2013/2014** dentro del archivo CDR de NOAA NCEI (deriva orbital y cambio de ancho espectral); deriva de calibración de Terra MODIS en años tardíos respecto a Colección 6.1; nubes convectivas del monzón; heterogeneidad fuerte entre sabana pastoral y zonas de cultivo intensivo.
- **Frase en inglés para la app:** `Published check: Sahel satellite NDVI increased broadly after 1982 in response to rainfall recovery, though localized agricultural zones show browning and multi-sensor records require careful calibration (Herrmann et al. 2005, doi:10.1016/j.gloenvcha.2005.08.004; Dardel et al. 2014, doi:10.1016/j.rse.2013.09.011).`

---

### Caso 6: Paradoja estacional en África oriental: Lluvias Largas vs. Lluvias Cortas (`africa_oriental_lluvias_largas_cortas`)
- **ID sugerido:** `africa_oriental_lluvias_largas_cortas`
- **Título e interfaz en inglés:** **East Africa Contrasting Seasonal Rainfall**
  *Compares the drying trend in East Africa's Long Rains (March–May) against the wetting trend in its Short Rains (October–December). Analyzing annual totals hides these opposite seasonal behaviors.*
- **Lugar:** Cuerno de África y África oriental ecuatorial (`[2.0, 41.0]`; caja: `lat -4.0° S a 12.0° N`, `lon 33.0° a 51.0° E`).
- **Variable, unidad y agregación:** Dos series anuales paralelas de precipitación acumulada estacional (`mm/temporada`): **MAM** (marzo–mayo, Lluvias Largas) y **OND** (octubre–diciembre, Lluvias Cortas), promediadas espacialmente sobre tierra.
- **Conjunto de datos:** **CHIRPS v2.0** (UCSB CHC), mensual `0.05°`, `1981-01` al presente (y **v3.0** como contraste). Descarga directa sin cuenta:
  - `https://data.chc.ucsb.edu/products/CHIRPS/v2.0/global_monthly/netcdf/chirps-v2.0.monthly.nc`
  - Versión actualizada v3.0: `https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/global/netcdf/chirps-v3.0.monthly.nc`
- **Pasos para construir la serie anual:**
  1. Descargar `chirps-v2.0.monthly.nc` (o usar GPCC v2022 para contraste pluviométrico) y recortar a `lat [-4, 12]`, `lon [33, 51]` sobre tierra.
  2. Construir por separado la suma anual de `marzo + abril + mayo` (`MAM`) y de `octubre + noviembre + diciembre` (`OND`).
  3. Promediar cada temporada sobre las celdas terrestres válidas ponderando por $\cos(\text{lat})$.
  4. Evaluar ambas series por separado (y su suma anual) con `analizar()` usando el índice ENSO/IOD como covariable diagnóstica.
- **Resultado publicado:** **Wainwright et al. (2019)** (*npj Climate and Atmospheric Science*, `doi:10.1038/s41612-019-0091-7`) demostraron que el declive de las Lluvias Largas (`MAM`) desde mediados de los años 1980 hasta la década de 2010 se debe a un acortamiento de la estación (inicio más tardío y fin más temprano), mientras **Lyon y DeWitt (2012)** (`doi:10.1029/2011GL050337`) vincularon la caída pos-1998 con cambios en la SST del Pacífico tropical. En la revisión de **Palmer et al. (2023)** (*Nature Reviews Earth & Environment*, `doi:10.1038/s43017-023-00397-x`), las tendencias observadas desde mediados de 1980 oscilan entre **`-6,5` y `-29,5 mm/temporada/década`** en `MAM` y **`+14,4` a `+23,6 mm/temporada/década`** en `OND` (según producto y subdominio).
- **Veredicto esperado:** **`los métodos no coinciden`** (si se agrega el año completo, `MAM` y `OND` se cancelan parcialmente; incluso dentro de `MAM`, la recuperación húmeda posterior a 2018 en algunos años suaviza la pendiente de `1981–2025` respecto a `1985–2017`, mientras que `OND` está dominado por picos extremos del IOD positivo y ENSO como 1997, 2019 y 2023).
- **Advertencias:** Altísima sensibilidad al año de corte (`1983–2017` vs. `1981–2025`), fuerte influencia del Dipolo del Índico (IOD) y del ENSO en OND, y escasez severa de estaciones en Somalia y sur de Etiopía que hace divergir a GPCC/CRU frente a productos satelitales infrarrojos como CHIRPS (**Funk et al. 2015**, `doi:10.1038/sdata.2015.66`).
- **Frase en inglés para la app:** `Published check: Since the mid-1980s, East Africa shows opposing trends—drying in MAM Long Rains (-6.5 to -29.5 mm/season/decade) alongside wetting in OND Short Rains (+14.4 to +23.6 mm/season/decade)—creating the East African climate paradox (Palmer et al. 2023, doi:10.1038/s43017-023-00397-x; Wainwright et al. 2019, doi:10.1038/s41612-019-0091-7).`

---

### Caso 7: Sequía plurianual y riesgo en el Cabo Occidental, Sudáfrica (`africa_austral_cabo_sequia`)
- **ID sugerido:** `africa_austral_cabo_sequia`
- **Título e interfaz en inglés:** **Southwestern Cape Drought Rainfall Trends**
  *Examines winter rainy-season precipitation in South Africa's Western Cape, site of Cape Town's 2015–2018 Day Zero drought crisis. It tests why extreme drought risk can triple even when short rainfall series appear noisy.*
- **Lugar:** Suroeste de Sudáfrica — cuenca de suministro del Cabo Occidental (`[-33.6, 19.2]`; caja: `lat -34.6° a -31.8° S`, `lon 18.0° a 20.6° E`).
- **Variable, unidad y agregación:** Suma anual de lluvia invernal austral mayo–septiembre (`MJJAS`) y año hidrológico completo (`mm/año`), promediados espacialmente.
- **Conjunto de datos:** **CRU TS v4.10** (`0.5°`, `1901–2025`, sin cuenta) para largo plazo y **CHIRPS v2.0** (`0.05°`, `1981–presente`, sin cuenta) para detalle topográfico de captación:
  - CRU TS v4.10: `https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/cruts.2604091129.v4.10/pre/cru_ts4.10.1901.2025.pre.dat.nc.gz`
  - CHIRPS v2.0 mensual: `https://data.chc.ucsb.edu/products/CHIRPS/v2.0/global_monthly/netcdf/chirps-v2.0.monthly.nc`
- **Pasos para construir la serie anual:**
  1. Descargar `cru_ts4.10.1901.2025.pre.dat.nc.gz` y `chirps-v2.0.monthly.nc`.
  2. Recortar a la región de lluvias invernales del Cabo Occidental (`lat [-34.6, -31.8]`, `lon [18.0, 20.6]`), sin mezclar con el interior de lluvias estivales.
  3. Sumar los meses de mayo a septiembre (`MJJAS`) de cada año para evitar contaminación de tormentas estivales aisladas.
  4. Promediar con peso de área terrestre para obtener una serie `mm/año`.
  5. Evaluar `1901–2025` (CRU) frente a `1981–2025` (CHIRPS) con `analizar()`.
- **Resultado publicado:** **Otto et al. (2018)** (*Environmental Research Letters*, `doi:10.1088/1748-9326/aae9f9`) demostraron mediante observaciones y modelos que el cambio climático antropogénico triplicó (`~3×`) la probabilidad de una sequía meteorológica como la de Ciudad del Cabo de `2015–2017`; **Pascale et al. (2020)** (*PNAS*, `doi:10.1073/pnas.2009144117`) estimaron un incremento de `5 a 6×` en la probabilidad de déficits equivalentes respecto a inicios del siglo XX debido al desplazamiento hacia los polos de las trayectorias de tormentas del hemisferio sur, proyectando déficits crecientes por década a lo largo del siglo XXI.
- **Veredicto esperado:** **`evidencia insuficiente`** en una prueba lineal simple sobre los ~45 años de CHIRPS (`1981–2025`) debido a la gran varianza interanual y la recuperación húmeda posterior a 2018/2023; la señal de desecación es física y de largo plazo en atribución multi-siglo/ensamble, no necesariamente un rechazo $p < 0,05$ en 4 décadas cortas.
- **Advertencias:** **Error geográfico común**: en 2023–2024 hubo una grave sequía en el interior austral de África (Zambia, Zimbabue, Malaui), pero esa zona es de lluvias de verano (DJF) dominadas por El Niño (**Kimutai et al. 2024**, `doi:10.25561/110770`, donde El Niño duplicó el riesgo pero la tendencia histórica DJF es neutra/positiva), régimen distinto al invierno mediterráneo del Cabo Occidental; además, la topografía de las montañas del Cabo reduce la precisión de rejillas gruesas de `0.5°`.
- **Frase en inglés para la app:** `Published check: Anthropogenic warming made Cape Town's 2015–2017 drought ~3 times (Otto et al. 2018, doi:10.1088/1748-9326/aae9f9) to 5–6 times more likely (Pascale et al. 2020, doi:10.1073/pnas.2009144117), although short 40-year rainfall series remain noisy.`

---

### Caso 8: Descenso del nivel del mar Caspio por altimetría satelital (`mar_caspio_nivel_altimetria`)
- **ID sugerido:** `mar_caspio_nivel_altimetria`
- **Título e interfaz en inglés:** **Caspian Sea Water Level Decline**
  *Tracks multi-decade changes in the surface elevation of the Caspian Sea—the world's largest inland water body—from satellite radar altimetry. Falling levels since 1995 highlight rising basin evaporation under warming.*
- **Lugar:** Mar Caspio (`[41.5, 50.5]`; caja: `lat 36.5° a 47.0° N`, `lon 46.5° a 54.5° E`).
- **Variable, unidad y agregación:** Altura superficial media anual respecto al geoide EGM2008 / anomalía de nivel del agua (`m`), promediada anualmente desde pases de 10 días.
- **Conjunto de datos:** **NASA GSFC Global Water Monitor (G-REALM)**, archivo `lake.10.tar.gz`, serie **`lake000270.10d.2.txt`** (`10 días`, `septiembre de 1992` al presente, idéntica arquitectura de archivo que la ya implementada en el backend del proyecto). Descarga directa sin cuenta:
  - Archivo consolidado GSFC G-REALM: `https://earth.gsfc.nasa.gov/gwm/zip/lake.10.tar.gz`
  - Tabla maestra de metadatos: `https://earth.gsfc.nasa.gov/gwm/html/WATER-MONITOR.LakesReservoirs.10day.xlsx`
- **Pasos para construir la serie anual:**
  1. Descargar `lake.10.tar.gz` y extraer el archivo ASCII de 16 columnas `lake000270.10d.2.txt`.
  2. Filtrar filas inválidas (valores centinela negativos/NaN o errores de rastreo) y conservar fecha decimal (`YYYY.frac`) y altura ajustada EGM2008 (`m`).
  3. Agrupar por año calendario `1993–2025` exigiendo al menos ~18 pasadas válidas/año y calcular la media anual.
  4. Ejecutar `analizar(anios, altura_media, "m")` sobre `1995–2025` y comparar con la ventana `1993–2025`.
- **Resultado publicado:** **Chen et al. (2017)** (*Geophysical Research Letters*, `doi:10.1002/2017GL073958`) reportaron un ascenso rápido de `+12,74 cm/año` (`+1,274 m/década`) entre `1979 y 1995`, seguido de un descenso sostenido de **`-6,72 cm/año`** (**`-0,672 m/década`**) entre `1996 y 2015` impulsado principalmente por el aumento de la evaporación superficial sobre el lago al subir la temperatura del aire. **Prange et al. (2020)** (*Communications Earth & Environment*, `doi:10.1038/s43247-020-00075-6`) confirman que el descenso continuado domina las proyecciones del siglo XXI por evaporación neta.
- **Veredicto esperado:** **`tendencia detectada`** (descenso claro en toda la era altimétrica pos-1995 con concordancia de MCO, Sen y Mann-Kendall modificado).
- **Advertencias:** Los propios metadatos de NASA GSFC GWM marcan el Caspio (`000270`) con banderas de *Winter ice* (hielo invernal en el Caspio norte somero), *Anthropogenic effects* (desvíos históricos del Volga y bahía de Kara-Bogaz-Gol) y *Potential seiche/wind effects*; en el siglo XX existió un quiebre opuesto de ascenso entre 1978 y 1995, por lo que una serie más larga pre-satelital (mareógrafos de Bakú/Makhachkala) muestra un comportamiento no lineal.
- **Frase en inglés para la app:** `Published check: Satellite altimetry reveals a sustained Caspian Sea level drop of -0.672 m/decade over 1996–2015 driven by warming-enhanced evaporation after an earlier 1979–1995 rise (Chen et al. 2017, doi:10.1002/2017GL073958).`

---

### Caso 9: Nivel altimétrico y dinámica no lineal de los lagos Victoria y Chad (`lagos_chad_victoria_altimetria`)
- **ID sugerido:** `lagos_chad_victoria_altimetria`
- **Título e interfaz en inglés:** **African Great Lakes Level Variability**
  *Monitors water level changes in Lake Victoria and Lake Chad using satellite radar altimetry. It illustrates why regulated outflows and strong Indian Ocean–ENSO swings produce abrupt jumps rather than simple linear trends.*
- **Lugar:** Lago Victoria (`[-1.0, 33.0]`, caja `lat -3.0° a 0.5°`, `lon 31.5° a 34.8° E`) y lago Chad (`[13.0, 14.0]`, caja `lat 12.4° a 14.4° N`, `lon 13.0° a 15.3° E`).
- **Variable, unidad y agregación:** Nivel medio anual de la superficie del agua (`m` respecto a EGM2008).
- **Conjunto de datos:** **NASA GSFC Global Water Monitor (G-REALM)**, archivo `lake.10.tar.gz`, series **`lake000314.10d.2.txt`** (Victoria) y **`lake000068.10d.2.txt`** (Chad), `septiembre de 1992` al presente, resolución temporal de 10 días. Descarga directa sin cuenta:
  - `https://earth.gsfc.nasa.gov/gwm/zip/lake.10.tar.gz`
  - Respaldo/contraste histórico altimétrico Hydroweb (**Crétaux et al. 2011**, `doi:10.1016/j.asr.2011.01.004`, requiere cuenta gratuita Theia en `https://hydroweb.next.theia-land.fr`).
- **Pasos para construir la serie anual:**
  1. Descargar `lake.10.tar.gz` y extraer `lake000314.10d.2.txt` (Victoria) y `lake000068.10d.2.txt` (Chad).
  2. Depurar lecturas faltantes o de calidad comprometida señaladas en la cabecera G-REALM.
  3. Promediar todas las pasadas válidas de cada año calendario completo (`1993–2025`) para cada lago.
  4. Analizar ambas series por separado con `analizar()` e inspeccionar puntos de cambio mediante `pettitt`.
- **Resultado publicado:** Para el **lago Victoria**, **Khaki y Awange (2021)** (*Sensors*, `doi:10.3390/s21134304`) documentan la subida rápida histórica de `2019–2020` asociada a lluvias extremas del Dipolo del Índico y **Olaka et al. (2019)** (`doi:10.3390/w11071449`) relacionan los cambios de nivel con variabilidad ENSO/IOD y regulación en la presa de Nalubaale/Owen Falls. Para el **lago Chad**, **Pham-Duc et al. (2020)** (*Scientific Reports*, `doi:10.1038/s41598-020-62417-w`) muestran que tras colapsar en `>90 %` respecto a sus `~25 000 km²` de los años 1960, su superficie abierta satelital se ha mantenido relativamente estable con fuertes ciclos estacionales alrededor de `~2400–2500 km²` en las últimas décadas (**Mahmood et al. 2019**, `doi:10.1038/s41598-019-42811-9`).
- **Veredicto esperado:** **`evidencia insuficiente`** (en la ventana pos-1992 de G-REALM: Victoria presenta ciclos plurianuales y el salto de 2019–2020 tras la caída de 2004–2006; Chad fluctúa estacionalmente tras su colapso previo a 1985, sin tendencia lineal monótona continua desde 1992).
- **Advertencias:** Banderas explícitas en la tabla oficial de NASA GSFC GWM: Victoria (`000314`) lleva **`Regulated water levels`** (descarga hidroeléctrica regulada en Jinja), y Chad (`000068`) lleva **`Anthropogenic effects`**, **`Shallow waters`**, **`Complex region`** y **`Data capture compromised (J1)`** (retrodispersión sobre humedales y vegetación flotante en cuenca somera, por lo que altimetría de radar solo muestrea una subcuenca del lago y debe contrastarse con extensión superficial como JRC Global Surface Water, **Pekel et al. 2016**, `doi:10.1038/nature20584`).
- **Frase en inglés para la app:** `Published check: Satellite records show Lake Victoria exhibits abrupt ENSO/IOD-driven jumps (Khaki & Awange 2021, doi:10.3390/s21134304) while Lake Chad stabilized seasonally after its 1960s–1980s collapse (Pham-Duc et al. 2020, doi:10.1038/s41598-020-62417-w).`

---

### Caso 10: Polvo mineral del Sahara y profundidad óptica de aerosoles en el norte de África (`sahara_sahel_polvo_aod`)
- **ID sugerido:** `sahara_sahel_polvo_aod`
- **Título e interfaz en inglés:** **Saharan Dust Optical Depth Trends**
  *Evaluates multi-decadal changes in mineral dust aerosol optical depth across North Africa and the Sahel. Comparing reanalysis dust fields with satellite retrievals exposes how wind and vegetation shifts affect atmospheric dust.*
- **Lugar:** Sahara occidental/central y Sahel norte (`[18.0, 2.0]`; caja: `lat 12.0° a 28.0° N`, `lon -17.0° a 25.0° E`).
- **Variable, unidad y agregación:** Profundidad óptica de extinción por polvo mineral a 550 nm (`DUEXTTAU`, adimensional), media anual (y subanálisis pico abril–julio).
- **Conjunto de datos:** **NASA MERRA-2 `M2TMNXAER`** (GMAO), versión **5.12.4**, `0.5° × 0.625°`, mensual, `1980-01` al presente (`doi:10.5067/FH9A0MLJPC7N`). Requiere cuenta gratuita **NASA Earthdata Login**:
  - Directorio GES DISC (archivos `.nc4` por año/mes): `https://data.gesdisc.earthdata.nasa.gov/data/MERRA2_MONTHLY/M2TMNXAER.5.12.4/`
  - Patrón de archivo: `MERRA2_400.tavgM_2d_aer_Nx.<YYYYMM>.nc4` (también disponible vía OPeNDAP `C1276812866-GES_DISC`).
- **Pasos para construir la serie anual:**
  1. Descargar mediante token Earthdata la variable `DUEXTTAU` de `M2TMNXAER.5.12.4` dentro de `lat [12, 28] N`, `lon [-17, 25] E` para `1980–2025`.
  2. Promediar mensualmente por celda y calcular la media anual (`12 meses`) y de primavera-verano (`MAMJJA`).
  3. Obtener el promedio espacial ponderado por $\cos(\text{lat})$.
  4. Comparar la tendencia de `1980–2025` con la ventana satelital homogénea MODIS/MISR `2001–2025` mediante `analizar()`.
- **Resultado publicado:** **Voss y Evan (2020)** (*Journal of Applied Meteorology and Climatology*, `doi:10.1175/JAMC-D-19-0194.1`) desarrollaron una climatología satelital específica de profundidad óptica de polvo (`DAOD`), seguida por **Song et al. (2021)** (*Atmospheric Chemistry and Physics*, `doi:10.5194/acp-21-13369-2021`, `2° × 5°`, `2007–2019` con CALIOP+MODIS). La síntesis de **Kok et al. (2023)** (*Nature Reviews Earth & Environment*, `doi:10.1038/s43017-022-00379-5`) destaca que la carga de polvo en el norte de África descendió desde los máximos de las sequías sahelianas de 1970–1980 hacia las décadas de 2000–2010 conforme aumentaron la vegetación en el Sahel y cambiaron los vientos superficiales, pero subraya grandes discrepancias entre productos de `AOD` total, `DAOD` satelital puro y reanálisis como MERRA-2 (**Gelaro et al. 2017**, `doi:10.1175/JCLI-D-16-0758.1`).
- **Veredicto esperado:** **`los métodos no coinciden`**. En MERRA-2, la introducción de asimilación de MODIS Terra (`2000`), Aqua (`2002`) y AERONET altera los saltos entre la era pre-2000 y pos-2002; además la pendiente cambia de signo o pierde significancia entre `1980–2025`, `2001–2018` y `2007–2019`, y el `AOD` total mezcla polvo mineral con aerosoles de quema de biomasa del Sahel/África central.
- **Advertencias:** **Discontinuidad de asimilación en MERRA-2 alrededor de 2000–2002** al incorporar MODIS y MISR; sobre desiertos muy brillantes las recuperaciones ópticas requieren algoritmos específicos (*Deep Blue*); fuerte variabilidad estacional e interanual ligada a la Oscilación Multidecadal del Atlántico (AMO) y el Saharan Heat Low.
- **Frase en inglés para la app:** `Published check: Satellite dust optical depth over North Africa declined after the 1980s drought peak alongside Sahel greening, though reanalysis and multi-sensor trends diverge across periods (Voss & Evan 2020, doi:10.1175/JAMC-D-19-0194.1; Kok et al. 2023, doi:10.1038/s43017-022-00379-5).`

---

### Caso 11: Agotamiento de agua terrestre y acuíferos en Oriente Medio (`orientemedio_norte_africa_grace_tws`)
- **ID sugerido:** `orientemedio_norte_africa_grace_tws`
- **Título e interfaz en inglés:** **Middle East Groundwater Depletion Trends**
  *Measures monthly changes in total terrestrial water storage across the Tigris–Euphrates basin and Arabian Peninsula from NASA GRACE gravity satellites. Persistent downward trends reflect unsustainable groundwater extraction amplified by drought.*
- **Lugar:** Cuencas del Tigris-Éufrates y centro-norte de la península Arábiga (`[31.0, 44.0]`; caja: `lat 20.0° a 39.0° N`, `lon 35.0° a 55.0° E`, separando subregión Tigris-Éufrates `[29, 39] N, [38, 50] E` y Arabia `[20, 30] N, [38, 52] E`).
- **Variable, unidad y agregación:** Anomalía media anual de almacenamiento total de agua terrestre (`lwe_thickness`, en `cm` de espesor de agua equivalente respecto a 2004–2009), agregada por promedio anual ponderado por área terrestre.
- **Conjunto de datos:** **CSR GRACE / GRACE-FO Mascon Solutions**, versión **RL06.03** (`0.25°` rejilla de salida / `~300 km` resolución nativa geodésica, mensual, `abril de 2002` al presente). Descarga directa NetCDF sin cuenta:
  - `https://download.csr.utexas.edu/outgoing/grace/RL0603_mascons/CSR_GRACE_GRACE-FO_RL0603_Mascons_all-corrections.nc`
- **Pasos para construir la serie anual:**
  1. Descargar `CSR_GRACE_GRACE-FO_RL0603_Mascons_all-corrections.nc` y cargar `lwe_thickness`.
  2. Aplicar máscara terrestre de CSR (evitando derrame sobre golfo Pérsico y mar Rojo) en la caja de cuenca Tigris-Éufrates `[29, 39] N`, `[38, 50] E`.
  3. Promediar los meses disponibles por año calendario `2002–2025` (omitiendo años con `< 7` meses válidos como `2017–2018` durante el relevo GRACE→GRACE-FO).
  4. Calcular la serie ponderada por $\cos(\text{lat})$ en `cm` y ejecutar `analizar()`.
- **Resultado publicado:** **Voss et al. (2013)** (*Water Resources Research*, `doi:10.1002/wrcr.20078`) cuantificaron en el norte y centro de Oriente Medio (Tigris-Éufrates y oeste de Irán) una pérdida de `TWS` de **`-27,2 ± 0,6 mm/año`** (`-27,2 cm/década` en el periodo `2003–2009`, volumen total `~143,6 km³`), impulsada en su mayoría por agotamiento de aguas subterráneas de `-17,3 ± 2,1 mm/año`. **Rodell et al. (2018)** (*Nature*, `doi:10.1038/s41586-018-0123-1`) y **Scanlon et al. (2018)** (`doi:10.1073/pnas.1704665115`) confirmaron entre 2002 y 2016 que Arabia Saudita y Oriente Medio pierden almacenamiento subterráneo fósil de manera persistente (`~6,1 Gt/año` o `~61 Gt/década` en Arabia Saudita según Rodell et al., 2018) bajo riego intensivo y sequías recurrentes.
- **Veredicto esperado:** **`tendencia detectada`**. La caída sostenida a lo largo de más de 20 años supera ampliamente el ruido estacional y la incertidumbre de mascon tanto en Tigris-Éufrates como en Arabia.
- **Advertencias:** **Brecha instrumental de 11 meses** entre julio de 2017 y mayo de 2018 entre GRACE y GRACE-FO (no interpolar linealmente años vacíos para no sesgar errores estándar); la señal combina bombeo antrópico de acuíferos fósiles con sequía climática (especialmente desde 2007); el tamaño nativo de los mascons (`~3°`) suaviza gradientes en bordes costeros estrechos como la costa del Levante o el mar Caspio (**Scanlon et al. 2021**, `doi:10.1088/1748-9326/ac16ff`).
- **Frase en inglés para la app:** `Published check: GRACE observations show steep freshwater loss across the Tigris–Euphrates basin (-27.2 mm/yr TWS over 2003–2009, Voss et al. 2013, doi:10.1002/wrcr.20078) and persistent Arabian aquifer depletion (Rodell et al. 2018, doi:10.1038/s41586-018-0123-1).`

---

### Caso 12: Área quemada en sabanas africanas frente a Europa mediterránea (`mediterraneo_sabanas_africa_gfed5`)
- **ID sugerido:** `mediterraneo_sabanas_africa_gfed5`
- **Título e interfaz en inglés:** **Mediterranean vs African Savanna Fire**
  *Compares regional burned-area trends in Africa's fire-prone savannas against Mediterranean Europe using GFED5. It reveals how cropland expansion drives falling savanna fire totals globally, even as Mediterranean fire weather worsens.*
- **Lugar:** Sabanas africanas del hemisferio norte (`[9.5, 16.0]`; caja `lat 4.0° a 14.5° N`, `lon -16.0° a 36.0° E`) comparadas con Europa mediterránea (`[40.0, 7.0]`; caja `lat 36.0° a 44.5° N`, `lon -9.5° a 26.5° E`).
- **Variable, unidad y agregación:** Área quemada acumulada anual (`Mha/año`, suma de los 12 meses de la fracción/área quemada mensual multiplicada por área de celda), evaluada de forma separada en ambos subdominios.
- **Conjunto de datos:** **GFED5 Burned Area** (**Chen et al. 2023**, `0.25° × 0.25°`, mensual, `1997–2020`). Descarga directa ZIP sin cuenta:
  - Archivo de área quemada (`BA.zip`, 264,8 MB, Zenodo `10.5281/zenodo.7668423`): `https://zenodo.org/records/7668424/files/BA.zip?download=1`
- **Pasos para construir la serie anual:**
  1. Descargar `BA.zip` y leer los archivos NetCDF mensuales de `1997–2020` (o `2001–2020` de era MODIS uniforme).
  2. Recortar dos subregiones independientes: cinturón de sabana norte-ecuatorial africana (`lat [4, 14.5] N`, `lon [-16, 36] E`) y cuenca europea mediterránea (`lat [36, 44.5] N`, `lon [-9.5, 26.5] E`, solo tierra).
  3. Sumar el área quemada mensual sobre las celdas de cada región para obtener `Mha/año`.
  4. Analizar ambas series por separado en `analizar()` (en `2001–2020` y en `1997–2020`).
- **Resultado publicado:** **Andela et al. (2017)** (*Science*, `doi:10.1126/science.aal4108`) demostraron que el área quemada mundial disminuyó en **`-24,3 ± 8,8 %`** entre `1998 y 2015` (concentrada en sabanas y pastizales de África, que aportan `~70 %` de la superficie quemada del planeta, donde la expansión agrícola fragmenta el combustible; véase también **Andela y van der Werf 2014**, `doi:10.1038/nclimate2313`). En contraste, para Europa mediterránea **Turco et al. (2016)** (`doi:10.1371/journal.pone.0150663`) y **Jones et al. (2022)** (*Reviews of Geophysics*, `doi:10.1029/2020RG000726`) explican que la mayor aridez e intensidad del peligro meteorológico de incendio compiten con la supresión activa y los cambios rurales, produciendo picos agudos en años extremos (2003, 2007, 2017) sin un aumento monótono simple del área quemada en todas las subcuencas.
- **Veredicto esperado:** **`tendencia detectada`** a la baja en sabanas africanas del norte (`2001–2020`), frente a **`evidencia insuficiente`** en Europa mediterránea (alta varianza dominada por veranos puntuales extremos y políticas de supresión).
- **Advertencias:** **Discontinuidad 1997–2000 vs. 2001–2020 en GFED5** (**Chen et al. 2023**, `doi:10.5194/essd-15-5227-2023`): antes de 2001 se reconstruye desde AVHRR/ATSR/VIRS y desde 2001 integra MODIS + corrección de pequeños incendios mediante Landsat/Sentinel-2, por lo que para tendencias robustas debe priorizarse `2001–2020`; el archivo GFED5 público llega hasta 2020 y aún no refleja la campaña extrema mediterránea de 2022–2023 en esa serie.
- **Frase en inglés para la app:** `Published check: Global burned area fell by 24.3 ± 8.8% over 1998–2015 largely due to agricultural fragmentation in African savannas (Andela et al. 2017, doi:10.1126/science.aal4108), whereas Mediterranean totals reflect competing suppression and extreme fire weather (Jones et al. 2022, doi:10.1029/2020RG000726).`

---

## 3. Contradicciones y matices

1. **«África y el Mediterráneo arden más» vs. la caída del área quemada en GFED5:** El mensaje popular asocia cualquier ola de calor o incendio extremo en Grecia, España o Argelia con un aumento lineal del área quemada total. Sin embargo, África representa alrededor del `70 %` del área quemada mundial y allí el fuego anual ha bajado por fragmentación agrícola y pastoreo (**Andela et al. 2017**, `doi:10.1126/science.aal4108`), mientras que en Europa mediterránea los grandes años catastróficos conviven con una fuerte reducción del número promedio de igniciones y mayor inversión en extinción (**Turco et al. 2016**, `doi:10.1371/journal.pone.0150663`). El indicador que sube de forma casi universal es el **riesgo meteorológico de incendio** (*fire weather*), no necesariamente el área total quemada año tras año (**Jones et al. 2022**, `doi:10.1029/2020RG000726`).
2. **La «paradoja de África oriental» y la reversión reciente pos-2018:** Entre 1998 y 2017 numerosos estudios y simulaciones climáticas mostraron que los modelos CMIP proyectaban lluvias más húmedas en `MAM`, mientras las observaciones mostraban secamiento. El desglose estacional (**Wainwright et al. 2019**, `doi:10.1038/s41612-019-0091-7`; **Palmer et al. 2023**, `doi:10.1038/s43017-023-00397-x`) demuestra que los promedios anuales ocultan señales estacionales de signo contrario y que añadir los años recientes de `MAM` húmedo (como 2018–2020) o el super-IOD de `OND` (2019, 2023) altera el veredicto de Mann-Kendall según el año final.
3. **¿El Sahel «volvió a la normalidad» o «se volvió verde por la lluvia»?** Aunque la lluvia JJAS se recuperó parcialmente después de 1983, esa recuperación no restaura el patrón estacionario de 1950–1965: ocurre con precipitaciones extremas más intensas y desplazadas hacia el final de la estación (**Biasutti 2019**, `doi:10.1002/wcc.591`). En paralelo, el reverdecimiento satelital (`NDVI`) no equivale a recuperación ecológica uniforme: **Dardel et al. (2014)** (`doi:10.1016/j.rse.2013.09.011`) documentaron reverdecimiento en sabanas pastorales junto a degradación localizada en tierras de cultivo intensivo, y la serie NOAA CDR sufre una ruptura de sensor entre AVHRR (`1981–2013`) y VIIRS (`2014+`).
4. **Lago Chad «casi seco ahora mismo» vs. altimetría/área pos-1990:** El colapso histórico del lago Chad (`~25 000 km²` en los 1960 a `~2400 km²`) ocurrió antes de la era altimétrica moderna de TOPEX/Jason (que inicia en 1992). En el periodo `1992–2025` no existe una tendencia descendente lineal sostenida, sino oscilaciones estacionales e interanuales (**Pham-Duc et al. 2020**, `doi:10.1038/s41598-020-62417-w`), además de fuertes interferencias de vegetación y aguas someras en altimetría radar (bandera de G-REALM en `lake000068`).
5. **Cuenca del Congo: ¿oscurecimiento y secamiento continuos o escasez de estaciones?** **Zhou et al. (2014)** (`doi:10.1038/nature13265`) reportaron un oscurecimiento (*browning*) multi-anual del bosque del Congo en 2000–2012 atribuido a un secamiento de abril–junio. Sin embargo, **Nicholson et al. (2018)** (`doi:10.1175/JHM-D-18-0015.1` y `doi:10.1016/j.gloplacha.2017.12.014`) advirtieron que la red de pluviómetros en el interior del Congo colapsó después de 1980–1990, haciendo que los productos reticulados globales interpolen tendencias artificiales o diverjan fuertemente entre sí.
6. **Secamiento invernal de Ciudad del Cabo (2015–2018) vs. sequía estival de 2024 en África austral:** Ambas se mencionan juntas bajo «África austral», pero responden a dinámicas opuestas: la crisis de Ciudad del Cabo afectó una zona de lluvias invernales (`MJJAS`) cuya probabilidad crece con el calentamiento antropogénico (**Otto et al. 2018**, `doi:10.1088/1748-9326/aae9f9`), mientras la sequía de 2023–2024 en Zambia/Zimbabue/Malaui afectó el régimen estival (`DJF`), duplicado en probabilidad por El Niño y sin tendencia negativa histórica en la lluvia total DJF (**Kimutai et al. 2024**, `doi:10.25561/110770`).

---

## 4. Descartados

- **Altimetría fluvial y lacustre de la misión SWOT (Hydrocron, NASA PO.DAAC):** Aunque dispone de acceso abierto sin cuenta mediante API (`SWOT_L2_HR_LakeSP_prior 2.0`), las observaciones científicas regulares comenzaron en julio de 2023 (`< 4 años` al 2026), muy por debajo del mínimo de 10–20 años necesario para evaluar tendencias climáticas estadísticamente válidas.
- **Lluvias locales observadas en la cuenca del Congo (`1990–2025`) como serie primaria de pluviómetros:** Descartada como ficha independiente de tendencia pluviométrica fiable porque la pérdida casi total de estaciones sinópticas activas en la República Democrática del Congo tras los años 1980 invalida la homogeneidad temporal de rejillas de estación pura (**Nicholson et al. 2018**, `doi:10.1175/JHM-D-18-0015.1`). Se incorpora en la sección de matices como advertencia metodológica.
- **Olas de calor marinas subsuperficiales del Mediterráneo y productos operativos de Copernicus CMEMS como serie base anónima:** Aunque **Dayan et al. (2023)** (`doi:10.3389/fmars.2023.1045138`) muestran que las OCM subsuperficiales difieren en vertical de la superficie, los reanálisis oceánicos tridimensionales y los productos de Copernicus Marine Service requieren registro y cuenta/API específicos (motivo por el que el caso 2 emplea **NOAA OISST v2.1** de acceso directo abierto sin cuenta, citando los matices verticales).
- **Superficie total del mar de Aral en G-REALM de forma aislada:** Su desecación responde abrumadoramente al desvío masivo de los ríos Amu Daria y Sir Daria para irrigación desde la década de 1960 más que a una señal climática atmosférica limpia posterior a 1992, y la fragmentación en múltiples lóbulos desborda la pista única de altimetría `10d`.
- **Series continuas homogéneas de polvo mineral con CALIOP (`2006–2023`):** La misión lidar espacial CALIPSO concluyó operaciones en 2023 tras 17 años (excelente para perfiles verticales y climatologías como **Song et al. 2021**, `doi:10.5194/acp-21-13369-2021`, pero sin continuidad hacia el futuro para una app pensada para actualizarse año con año sin cambio de instrumento).

---

## 5. Bibliografía

Todas las referencias y DOIs de esta sección fueron verificados directamente frente a Crossref o DataCite el **14 de noviembre de 2026** (`2026-11-14`).

1. Andela, N., & van der Werf, G. R. (2014). Recent trends in African fires driven by cropland expansion and El Niño to La Niña transition. *Nature Climate Change*, 4, 791–795. `doi:10.1038/nclimate2313` (comprobado `2026-11-14`).
2. Andela, N., Morton, D. C., Giglio, L., Chen, Y., van der Werf, G. R., Kasibhatla, P. S., et al. (2017). A human-driven decline in global burned area. *Science*, 356(6345), 1356–1362. `doi:10.1126/science.aal4108` (comprobado `2026-11-14`).
3. Biasutti, M. (2019). Rainfall trends in the African Sahel: Characteristics, processes, and causes. *WIREs Climate Change*, 10(4), e591. `doi:10.1002/wcc.591` (comprobado `2026-11-14`).
4. Chen, J. L., Pekker, T., Wilson, C. R., Tapley, B. D., Kostianoy, A. G., Cretaux, J.-F., & Safarov, E. S. (2017). Long-term Caspian Sea level change. *Geophysical Research Letters*, 44(13), 6993–7001. `doi:10.1002/2017GL073958` (comprobado `2026-11-14`).
5. Chen, Y., Hall, J., van Wees, D., Andela, N., Hantson, S., Giglio, L., et al. (2023). Multi-decadal trends and variability in burned area from the fifth version of the Global Fire Emissions Database (GFED5). *Earth System Science Data*, 15, 5227–5259. `doi:10.5194/essd-15-5227-2023` (comprobado `2026-11-14`).
6. Chen, Y., et al. (2023). *GFED5 Burned Area (BA) Monthly Dataset* [Dataset]. Zenodo. `doi:10.5281/zenodo.7668423` (comprobado `2026-11-14`).
7. Cornes, R. C., van der Schrier, G., van den Besselaar, E. J. M., & Jones, P. D. (2018). An Ensemble Version of the E-OBS Temperature and Precipitation Data Sets. *Journal of Geophysical Research: Atmospheres*, 123(17), 9391–9409. `doi:10.1029/2017JD028200` (comprobado `2026-11-14`).
8. Crétaux, J.-F., Jelinski, W., Calmant, S., Kouraev, A., Vuglinski, V., Bergé-Nguyen, M., et al. (2011). SOLS: A lake database to monitor in the Near Real Time water level and storage variations from remote sensing data. *Advances in Space Research*, 47(9), 1497–1507. `doi:10.1016/j.asr.2011.01.004` (comprobado `2026-11-14`).
9. Dardel, C., Kergoat, L., Hiernaux, P., Mougin, E., Grippa, M., & Tucker, C. J. (2014). Re-greening Sahel: 30 years of remote sensing data and field observations (Mali, Niger). *Remote Sensing of Environment*, 140, 350–364. `doi:10.1016/j.rse.2013.09.011` (comprobado `2026-11-14`).
10. Darmaraki, S., Denaxa, D., Theodorou, I., Llasses, J., Jordà, G., Somot, S., et al. (2024). Marine Heatwaves in the Mediterranean Sea: A Literature Review. *Mediterranean Marine Science*, 25(3), 586–620. `doi:10.12681/mms.38392` (comprobado `2026-11-14`).
11. Dayan, H., McAdam, R., Juza, M., Masina, S., & Speich, S. (2023). Marine heat waves in the Mediterranean Sea: An assessment from the surface to the subsurface to meet national needs. *Frontiers in Marine Science*, 10, 1045138. `doi:10.3389/fmars.2023.1045138` (comprobado `2026-11-14`).
12. Didan, K. (2021). *MODIS/Terra Vegetation Indices Monthly L3 Global 0.05Deg CMG V061* [Dataset]. NASA EOSDIS LP DAAC. `doi:10.5067/MODIS/MOD13C2.061` (comprobado `2026-11-14`).
13. Fischer, E. M., & Schär, C. (2010). Consistent geographical patterns of changes in high-impact European heatwaves. *Nature Geoscience*, 3, 398–403. `doi:10.1038/ngeo866` (comprobado `2026-11-14`).
14. Funk, C., Peterson, P., Landsfeld, M., Pedreros, D., Verdin, J., Shukla, S., et al. (2015). The climate hazards infrared precipitation with stations—a new environmental record for monitoring extremes. *Scientific Data*, 2, 150066. `doi:10.1038/sdata.2015.66` (comprobado `2026-11-14`).
15. Gelaro, R., McCarty, W., Suárez, M. J., Todling, R., Molod, A., Takacs, L., et al. (2017). The Modern-Era Retrospective Analysis for Research and Applications, Version 2 (MERRA-2). *Journal of Climate*, 30(14), 5419–5454. `doi:10.1175/JCLI-D-16-0758.1` (comprobado `2026-11-14`).
16. The GlaMBIE Team. (2025). Community estimate of global glacier mass changes from 2000 to 2023. *Nature*. `doi:10.1038/s41586-024-08545-z` (comprobado `2026-11-14`).
17. Global Modeling and Assimilation Office (GMAO). (2015). *MERRA-2 tavgM_2d_aer_Nx: 2d, Monthly mean, Time-averaged, Single-Level, Assimilation, Aerosol Diagnostics V5.12.4* [Dataset]. GES DISC. `doi:10.5067/FH9A0MLJPC7N` (comprobado `2026-11-14`).
18. Harris, I., Osborn, T. J., Jones, P., & Lister, D. (2020). Version 4 of the CRU TS monthly high-resolution gridded multivariate climate dataset. *Scientific Data*, 7, 109. `doi:10.1038/s41597-020-0453-3` (comprobado `2026-11-14`).
19. Herrmann, S. M., Anyamba, A., & Tucker, C. J. (2005). Recent trends in vegetation dynamics in the African Sahel and their relationship to climate. *Global Environmental Change*, 15(4), 394–404. `doi:10.1016/j.gloenvcha.2005.08.004` (comprobado `2026-11-14`).
20. Hobday, A. J., Alexander, L. V., Perkins, S. E., Smale, D. A., Straub, S. C., Oliver, E. C. J., et al. (2016). A hierarchical approach to defining marine heatwaves. *Progress in Oceanography*, 141, 227–238. `doi:10.1016/j.pocean.2015.12.014` (comprobado `2026-11-14`).
21. Huang, B., Liu, C., Banzon, V., Freeman, E., Graham, G., Hankins, B., et al. (2020). *NOAA 0.25-degree Daily Optimum Interpolation Sea Surface Temperature (OISST), Version 2.1* [Dataset]. NOAA NCEI. `doi:10.25921/RE9P-PT57` (comprobado `2026-11-14`).
22. Jones, M. W., Abatzoglou, J. T., Veraverbeke, S., Andela, N., Lasslop, G., Forkel, M., et al. (2022). Global and Regional Trends and Drivers of Fire Under Climate Change. *Reviews of Geophysics*, 60(3), e2020RG000726. `doi:10.1029/2020RG000726` (comprobado `2026-11-14`).
23. Khaki, M., & Awange, J. (2021). The 2019–2020 Rise in Lake Victoria Monitored from Space: Exploiting the State-of-the-Art GRACE-FO and the Newly Released ERA-5 Reanalysis Products. *Sensors*, 21(13), 4304. `doi:10.3390/s21134304` (comprobado `2026-11-14`).
24. Kimutai, J., Zachariah, M., Nhantumbo, B., Nkemelang, T., Jain, S., Pinto, I., et al. (2024). *El Niño key driver of drought in highly vulnerable Southern African countries*. World Weather Attribution / Imperial College London. `doi:10.25561/110770` (comprobado `2026-11-14`).
25. Kok, J. F., Storelvmo, T., Karydis, V. A., Adebiyi, A. A., Mahowald, N. M., Evan, A. T., et al. (2023). Mineral dust aerosol impacts on global climate and climate change. *Nature Reviews Earth & Environment*, 4, 71–86. `doi:10.1038/s43017-022-00379-5` (comprobado `2026-11-14`).
26. Lorenz, R., Stalhandske, Z., & Fischer, E. M. (2019). Detection of a Climate Change Signal in Extreme Heat, Heat Stress, and Cold Waves in Europe From Observations. *Geophysical Research Letters*, 46(14), 8363–8374. `doi:10.1029/2019GL082062` (comprobado `2026-11-14`).
27. Lyon, B., & DeWitt, D. G. (2012). A recent and abrupt decline in the East African long rains. *Geophysical Research Letters*, 39(2), L02702. `doi:10.1029/2011GL050337` (comprobado `2026-11-14`).
28. Mahmood, R., Jia, S., & Zhu, W. (2019). Analysis of climate variability, trends, and prediction in the most active parts of the Lake Chad basin, Africa. *Scientific Reports*, 9, 6317. `doi:10.1038/s41598-019-42811-9` (comprobado `2026-11-14`).
29. Nicholson, S. E., Funk, C., & Fink, A. H. (2018). Rainfall over the African continent from the 19th through the 21st century. *Global and Planetary Change*, 165, 114–127. `doi:10.1016/j.gloplacha.2017.12.014` (comprobado `2026-11-14`).
30. Nicholson, S. E., Klotter, D., Zhou, L., Hua, W., Russell, J., & Dezfuli, A. K. (2018). New Rainfall Datasets for the Congo Basin and Surrounding Regions. *Journal of Hydrometeorology*, 19(8), 1379–1396. `doi:10.1175/JHM-D-18-0015.1` (comprobado `2026-11-14`).
31. Olaka, L. A., Ogutu, J. O., Said, M. Y., & Oludhe, C. (2019). Projected Climatic and Hydrologic Changes to Lake Victoria Basin Rivers under Three RCP Emission Scenarios for 2015–2100 and Impacts on the Water Sector. *Water*, 11(7), 1449. `doi:10.3390/w11071449` (comprobado `2026-11-14`).
32. Olsson, L., Eklundh, L., & Ardö, J. (2005). A recent greening of the Sahel—trends, patterns and potential causes. *Journal of Arid Environments*, 63(3), 556–566. `doi:10.1016/j.jaridenv.2005.03.008` (comprobado `2026-11-14`).
33. Otto, F. E. L., Wolski, P., Lehner, F., Tebaldi, C., van Oldenborgh, G. J., Hogesteeger, S., et al. (2018). Anthropogenic influence on the drivers of the Western Cape drought 2015–2017. *Environmental Research Letters*, 13(12), 124010. `doi:10.1088/1748-9326/aae9f9` (comprobado `2026-11-14`).
34. Palmer, P. I., Wainwright, C. M., Dong, B., Maidment, R. I., Brönnimann, S., & Black, E. (2023). Drivers and impacts of Eastern African rainfall variability. *Nature Reviews Earth & Environment*, 4, 254–270. `doi:10.1038/s43017-023-00397-x` (comprobado `2026-11-14`).
35. Pascale, S., Kapnick, S. B., Delworth, T. L., & Cooke, W. F. (2020). Increasing risk of another Cape Town "Day Zero" drought in the 21st century. *Proceedings of the National Academy of Sciences*, 117(47), 29495–29503. `doi:10.1073/pnas.2009144117` (comprobado `2026-11-14`).
36. Pekel, J.-F., Cottam, A., Gorelick, N., & Belward, A. S. (2016). High-resolution mapping of global surface water and its long-term changes. *Nature*, 540, 418–422. `doi:10.1038/nature20584` (comprobado `2026-11-14`).
37. Pham-Duc, B., Sylvestre, F., Papa, F., Frappart, F., Bouchez, C., & Crétaux, J.-F. (2020). The Lake Chad hydrology under current climate change. *Scientific Reports*, 10, 5498. `doi:10.1038/s41598-020-62417-w` (comprobado `2026-11-14`).
38. Pisano, A., Marullo, S., Artale, V., Falcini, F., Yang, C., Leonelli, F. E., et al. (2020). New Evidence of Mediterranean Climate Change and Variability from Sea Surface Temperature Observations. *Remote Sensing*, 12(1), 132. `doi:10.3390/rs12010132` (comprobado `2026-11-14`).
39. Prange, M., Wilke, T., & Wesselingh, F. P. (2020). The other side of sea level change. *Communications Earth & Environment*, 1, 69. `doi:10.1038/s43247-020-00075-6` (comprobado `2026-11-14`).
40. Rodell, M., Famiglietti, J. S., Wiese, D. N., Reager, J. T., Beaudoing, H. K., Landerer, F. W., & Lo, M.-H. (2018). Emerging trends in global freshwater availability. *Nature*, 557, 651–659. `doi:10.1038/s41586-018-0123-1` (comprobado `2026-11-14`).
41. Scanlon, B. R., Zhang, Z., Save, H., Sun, A. Y., Müller Schmied, H., van Beek, L. P. H., et al. (2018). Global models underestimate large decadal declining and rising water storage trends relative to GRACE satellite data. *Proceedings of the National Academy of Sciences*, 115(6), E1080–E1089. `doi:10.1073/pnas.1704665115` (comprobado `2026-11-14`).
42. Scanlon, B. R., Rateb, A., Anyamba, A., Kebede, S., MacDonald, A. M., Shamsudduha, M., et al. (2021). Linkages between GRACE water storage, hydrologic extremes, and climate teleconnections in major African aquifers. *Environmental Research Letters*, 17(1), 014046. `doi:10.1088/1748-9326/ac16ff` (comprobado `2026-11-14`).
43. Schneider, U., Hänsel, S., Finger, P., Rustemeier, E., & Ziese, M. (2022). *GPCC Full Data Monthly Version 2022 at 0.5°: Monthly Land-Surface Precipitation from Rain-Gauges built on GTS-based and Historical Data* [Dataset]. Deutscher Wetterdienst (DWD). `doi:10.5676/DWD_GPCC/FD_M_V2022_050` (comprobado `2026-11-14`).
44. Song, Q., Zhang, Z., Yu, H., Ginoux, P., & Shen, J. (2021). Global dust optical depth climatology derived from CALIOP and MODIS aerosol retrievals on decadal timescales: regional and interannual variability. *Atmospheric Chemistry and Physics*, 21, 13369–13395. `doi:10.5194/acp-21-13369-2021` (comprobado `2026-11-14`).
45. Tong, X., Brandt, M., Hiernaux, P., Herrmann, S. M., Tian, F., Prishchepov, A. V., & Fensholt, R. (2017). Revisiting the coupling between NDVI trends and cropland changes in the Sahel drylands: A case study in western Niger. *Remote Sensing of Environment*, 191, 286–296. `doi:10.1016/j.rse.2017.01.030` (comprobado `2026-11-14`).
46. Turco, M., Bedia, J., Di Liberto, F., Fiorucci, P., von Hardenberg, J., Koutsias, N., et al. (2016). Decreasing Fires in Mediterranean Europe. *PLOS ONE*, 11(3), e0150663. `doi:10.1371/journal.pone.0150663` (comprobado `2026-11-14`).
47. Vautard, R., Christidis, N., Ciavarella, A., Alvarez-Castro, C., Bellprat, O., Christiansen, B., et al. (2023). Heat extremes in Western Europe increasing faster than simulated due to atmospheric circulation trends. *Nature Communications*, 14, 6803. `doi:10.1038/s41467-023-42143-3` (comprobado `2026-11-14`).
48. Vermote, E., NOAA CDR Program. (2019). *NOAA Climate Data Record (CDR) of AVHRR Normalized Difference Vegetation Index (NDVI), Version 5* [Dataset]. NOAA NCEI. `doi:10.7289/V5ZG6QH9` (comprobado `2026-11-14`).
49. Vermote, E., NOAA CDR Program. (2022). *NOAA Climate Data Record (CDR) of VIIRS Normalized Difference Vegetation Index (NDVI), Version 1* [Dataset]. NOAA NCEI. `doi:10.25921/gakh-st76` (comprobado `2026-11-14`).
50. Voss, K. A., Famiglietti, J. S., Lo, M., de Linage, C., Rodell, M., & Swenson, S. C. (2013). Groundwater depletion in the Middle East from GRACE with implications for transboundary water management in the Tigris-Euphrates-Western Iran region. *Water Resources Research*, 49(2), 904–914. `doi:10.1002/wrcr.20078` (comprobado `2026-11-14`).
51. Voss, K. K., & Evan, A. T. (2020). A New Satellite-Based Global Climatology of Dust Aerosol Optical Depth. *Journal of Applied Meteorology and Climatology*, 59(1), 83–102. `doi:10.1175/JAMC-D-19-0194.1` (comprobado `2026-11-14`).
52. Wainwright, C. M., Marsham, J. H., Keane, R. J., Rowell, D. P., Finney, D. L., Black, E., & Allan, R. P. (2019). 'Eastern African Paradox' rainfall decline due to shorter not less intense Long Rains. *npj Climate and Atmospheric Science*, 2, 34. `doi:10.1038/s41612-019-0091-7` (comprobado `2026-11-14`).
53. World Glacier Monitoring Service (WGMS). (2024). *Glacier Mass Balance Intercomparison Exercise (GlaMBIE) Dataset 1.0.0* [Dataset]. WGMS. `doi:10.5904/wgms-glambie-2024-07` (comprobado `2026-11-14`).
54. Zhou, L., Tian, Y., Myneni, R. B., Ciais, P., Saatchi, S., Liu, Y. Y., et al. (2014). Widespread decline of Congo rainforest greenness in the past decade. *Nature*, 509, 86–90. `doi:10.1038/nature13265` (comprobado `2026-11-14`).
