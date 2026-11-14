## 1. Resumen

| Caso | Región | Variable | Periodo | Tendencia publicada (unidades por década) | Veredicto esperado | Confianza |
|---|---|---|---|---|---|---|
| Días de ola de calor en Europa | Europa (Oeste y Centro) | Nº de días de ola de calor por verano | 1979–2020 | +0,61 días/década (media europea) | Tendencia detectada | Alta |
| SST y olas de calor marinas en el Mediterráneo | Mar Mediterráneo | Temperatura superficial del mar (SST) | 1982–2022 | +0,35 a +0,41 °C/década | Tendencia detectada | Alta |
| Pérdida de masa glaciar en los Alpes | Alpes (Europa central) | Masa glaciar (equivalente agua) | 2000–2023 | ≈ −39 % de masa en 23 años (≈ −17 %/década) | Tendencia detectada | Alta |
| Recuperación de lluvia en el Sahel | Sahel (África occidental) | Precipitación media | 1990–2024 | +0,17 mm/día/década | Tendencia detectada | Media-alta |
| «Paradoja» de las lluvias largas de África oriental | Cuerno de África | Precipitación MAM (marzo-mayo) | 1980–2024 | −0,33 a −0,42 mm/día/década (observado) | Los métodos no coinciden (observaciones secan; modelos GCM humedecen) | Media |
| Sequía de Ciudad del Cabo | Suroeste de Sudáfrica | Precipitación invernal y probabilidad de sequía plurianual | 2015–2024 | Probabilidad del déficit 2015-2017 multiplicada por 5–6 | Tendencia detectada (en riesgo); tendencia de lluvia anual: evidencia insuficiente | Media |
| Superficie del lago Chad | Cuenca del Chad | Área superficial (km²) | 2003–2022 | Estable en las dos últimas décadas; ligero descenso del pool norte | Evidencia insuficiente (sin tendencia clara) | Media |
| Nivel del lago Victoria | África oriental | Nivel del agua (m) | 1993–2016 | −0,005 m/año (≈ −0,05 m/década) | Tendencia detectada | Media |
| Nivel del mar Caspio | Asia central / Oriente Medio | Nivel del agua (cm) | 1996–2015 | ≈ −6,72 cm/año (≈ −67 cm/década) | Tendencia detectada | Alta |
| AOD de polvo del Sahara | Sahara central y occidental | AOD (aerosol optical depth) | 2001–2020 | Hasta +0,026 año⁻¹ (≈ +0,26/década) en el Sahara central | Tendencia detectada (espacialmente heterogénea) | Media |
| Aguas subterráneas en Oriente Medio y el norte de África | MENA (acuíferos transfronterizos) | Almacenamiento de agua subterránea (mm/año) | 2003–2021 | −3,62 ± 0,70 mm/año (≈ −36 mm/década) en el NWSAS | Tendencia detectada | Alta |
| Área quemada en el Mediterráneo | Mediterráneo occidental | Área quemada (ha) | 2001–2020 | Tendencia decreciente o no significativa según el producto; sin aumento consistente | Los métodos no coinciden (GFED5 vs. otros productos) | Baja-media |

---

## 2. Fichas por caso

### Caso 1: `europe_heatwave_days`

**Título en inglés:** *European Heatwave Days*  
**Definición:** Number of days per summer that exceed the local 90th percentile of daily maximum temperature, averaged over Europe. It measures how often extreme heat occurs.

**Lugar:** Europa occidental y central (coordenadas del centro: [48, 10]). Caja: lat 35–60, lon −10–30.

**Variable, unidad y agregación anual:** Número de días de ola de calor por año (conteo anual, media espacial sobre la región).

**Conjunto de datos:** ERA5 reanálisis, versión más reciente, resolución 0,25°, periodo 1979–presente. URL de descarga: https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels (requiere cuenta gratuita).

**Pasos para construir la serie anual:**
1. Descargar temperatura máxima diaria (o temperatura a 2 m) para junio-agosto.
2. Calcular el percentil 90 móvil (ventana de 11 días) para cada punto de rejilla y año.
3. Identificar días que superan ese percentil.
4. Contar días por año y promediar espacialmente sobre la caja.
5. Aplicar una regresión lineal robusta (Theil-Sen) para obtener la tendencia por década.

**Resultado publicado:** Aumento medio de +0,61 días de ola de calor por década en Europa, con tendencias 3–4 veces más rápidas que la media de las latitudes medias del hemisferio norte. DOI: 10.1038/s41467-022-31432-y.

**Veredicto esperado:** Tendencia detectada. La señal es robusta en múltiples reanálisis y está vinculada a cambios en la circulación atmosférica (doble jet).

**Advertencias:** La definición de ola de calor (percentil, ventana, duración mínima) afecta la magnitud. El periodo 1979–2020 incluye años con distinta cobertura satelital; se recomienda usar ERA5 a partir de 1979. El ENSO tiene influencia modesta en Europa.

**Nota para la app:** Published check: European heatwave days increased by ~0.61 days per decade (1979–2020) (DOI: 10.1038/s41467-022-31432-y).

---

### Caso 2: `mediterranean_sst_mhw`

**Título en inglés:** *Mediterranean Sea Surface Temperature*  
**Definición:** Average sea surface temperature and frequency of marine heatwaves in the Mediterranean Sea. Marine heatwaves are prolonged periods of anomalously warm water.

**Lugar:** Mar Mediterráneo (centro: [38, 18]). Caja: lat 30–46, lon −6–36.

**Variable, unidad y agregación anual:** SST media anual (°C) y número de días de ola de calor marina por año (conteo).

**Conjunto de datos:** Copernicus Marine Service, producto SST_MED_SST_L4_REP_OBSERVATIONS_010_021, resolución 0,05°, periodo 1982–presente. URL: https://data.marine.copernicus.eu/product/SST_MED_SST_L4_REP_OBSERVATIONS_010_021/description (cuenta gratuita).

**Pasos para construir la serie anual:**
1. Descargar SST diaria para el Mediterráneo.
2. Calcular la media anual espacial.
3. Definir olas de calor marinas con el percentil 90 estacional (ventana móvil de 11 días).
4. Contar días de MHW por año.
5. Estimar tendencias con Mann-Kendall y pendiente de Sen.

**Resultado publicado:** Calentamiento de la SST de +0,35 a +0,41 °C/década entre 1982 y 2022, con intensificación de las olas de calor marinas. DOI de referencia: 10.5194/sp-2024-4 (preprint); se recomienda citar también el producto Copernicus.

**Veredicto esperado:** Tendencia detectada. La señal de calentamiento es consistente en múltiples productos satelitales y se traduce en MHW más frecuentes e intensas.

**Advertencias:** La definición de MHW (baseline, percentil, duración mínima) cambia los resultados. La cuenca este (Adriático, Egeo, Levante) muestra tendencias más altas que la occidental. El periodo 1982–2022 es lo suficientemente largo, pero la cobertura satelital mejora después de 1990.

**Nota para la app:** Published check: Mediterranean SST warmed 0.35–0.41 °C per decade (1982–2022), with more frequent marine heatwaves (DOI: 10.5194/sp-2024-4).

---

### Caso 3: `alps_glacier_mass`

**Título en inglés:** *Alpine Glacier Mass Loss*  
**Definición:** Change in glacier ice mass in the European Alps, expressed as a percentage of the total mass or in metres of water equivalent. It reflects the response of glaciers to warming.

**Lugar:** Alpes (centro: [46, 10]). Caja: lat 44–48, lon 6–16.

**Variable, unidad y agregación anual:** Cambio de masa glaciar anual (m e.w. o Gt) agregado como tasa anual.

**Conjunto de datos:** GlaMBIE (Glacier Mass Balance Intercomparison Exercise), compilación comunitaria 2000–2023. Datos disponibles a través del repositorio del artículo (DOI: 10.1038/s41586-024-08545-z) y de las bases de datos de WGMS. Resolución variable según método; periodo 2000–2023.

**Pasos para construir la serie anual:**
1. Descargar las series de cambio de masa glaciar por región (Alpes) de GlaMBIE.
2. Filtrar la región «Central Europe» o «Alps».
3. Agregar las tasas anuales por década.
4. Calcular la pérdida acumulada y el porcentaje respecto a la masa inicial.
5. Estimar la tendencia lineal.

**Resultado publicado:** Los glaciares de los Alpes perdieron ≈39 % de su masa entre 2000 y 2023; la pérdida global fue del 5 % en el mismo periodo. DOI: 10.1038/s41586-024-08545-z.

**Veredicto esperado:** Tendencia detectada. La pérdida de masa es inequívoca y se acelera en la segunda mitad del periodo (2012–2023).

**Advertencias:** La masa glaciar se mide con métodos heterogéneos (altimetría, gravimetría, balance de masa in situ). GlaMBIE armoniza las diferencias, pero la incertidumbre regional es mayor que la global. El periodo 2000–2023 es corto para separar variabilidad decadal de tendencia, pero la señal es fuerte.

**Nota para la app:** Published check: Alpine glaciers lost ~39 % of their mass between 2000 and 2023 (DOI: 10.1038/s41586-024-08545-z).

---

### Caso 4: `sahel_rainfall_recovery`

**Título en inglés:** *Sahel Rainfall Recovery*  
**Definición:** Average rainfall over the Sahel region during the rainy season (June–September). It measures the partial recovery after the severe droughts of the 1970s and 1980s.

**Lugar:** Sahel (centro: [14, 0]). Caja: lat 10–18, lon −17–20.

**Variable, unidad y agregación anual:** Precipitación media estacional (mm/día o mm/año), agregada como media espacial.

**Conjunto de datos:** GPCC Full Data Monthly Product (versión más reciente), resolución 0,5° o 0,25°, periodo 1891–presente. URL: https://www.dwd.de/EN/ourservices/gpcc/gpcc.html (sin cuenta). También CHIRPS v2 para años recientes.

**Pasos para construir la serie anual:**
1. Descargar la precipitación mensual de GPCC para junio-septiembre.
2. Calcular el total estacional por año.
3. Promediar espacialmente sobre la caja del Sahel.
4. Calcular anomalías respecto a la media 1961–1990.
5. Ajustar una tendencia lineal para el periodo post-1990.

**Resultado publicado:** Tendencia positiva estadísticamente significativa de +0,17 mm/día/década desde 1990, tras las sequías de los 70 y 80. DOI: 10.1038/s43247-026-03474-3.

**Veredicto esperado:** Tendencia detectada (recuperación parcial). La señal es consistente en GPCC y CHIRPS, aunque no se ha recuperado completamente el nivel pre-1970.

**Advertencias:** La recuperación es parcial y modulada por la AMO y aerosoles antrópicos. La densidad de pluviómetros en el Sahel es baja; GPCC incorpora interpolación. El ENSO y la AMO explican parte de la variabilidad interanual.

**Nota para la app:** Published check: Sahel rainfall has increased by ~0.17 mm/day per decade since 1990, a partial recovery (DOI: 10.1038/s43247-026-03474-3).

---

### Caso 5: `east_africa_long_rains`

**Título en inglés:** *East African Long Rains*  
**Definición:** Total rainfall during the March–May “long rains” season in the Horn of Africa. It is the main rainy season for agriculture and water resources.

**Lugar:** Cuerno de África (centro: [5, 42]). Caja: lat −5–12, lon 30–52.

**Variable, unidad y agregación anual:** Precipitación total MAM (mm/día o mm/estación), media espacial.

**Conjunto de datos:** GPCC (versión más reciente) y CHIRPS v2. GPCC: 0,5°/0,25°, 1891–presente; CHIRPS: 0,05°, 1981–presente. URLs: https://www.dwd.de/EN/ourservices/gpcc/gpcc.html y https://data.chc.ucsb.edu/products/CHIRPS-2.0/ (sin cuenta).

**Pasos para construir la serie anual:**
1. Descargar precipitación mensual para marzo, abril y mayo.
2. Sumar los tres meses para obtener el total MAM.
3. Promediar espacialmente sobre la caja.
4. Calcular anomalías y tendencia (Theil-Sen).
5. Comparar con salidas de modelos CMIP6 para evaluar la «paradoja».

**Resultado publicado:** Las observaciones muestran una tendencia al secado de las lluvias largas de −0,33 a −0,42 mm/día/década, mientras que los modelos CMIP6 proyectan un humedecimiento (paradoja). DOI: 10.1175/JCLI-D-24-0225.1.

**Veredicto esperado:** Los métodos no coinciden. Las observaciones indican secado, pero los modelos no lo reproducen; la paradoja se reduce al prescribir SST observadas.

**Advertencias:** Fuerte influencia de La Niña y del Pacífico tropical. La sequía de cinco estaciones (2020–2023) es un evento extremo que puede sesgar tendencias cortas. La densidad de datos observacionales es limitada antes de 1980.

**Nota para la app:** Published check: Observed long rains show drying of −0.33 to −0.42 mm/day per decade, while CMIP6 models wet (DOI: 10.1175/JCLI-D-24-0225.1).

---

### Caso 6: `southern_africa_cape_town_drought`

**Título en inglés:** *Cape Town Drought Risk*  
**Definición:** Probability of multi-year winter rainfall deficits in southwestern South Africa, such as the 2015–2017 “Day Zero” drought. It measures the changing risk of severe drought.

**Lugar:** Suroeste de Sudáfrica (centro: [−34, 19]). Caja: lat −36–−30, lon 17–22.

**Variable, unidad y agregación anual:** Precipitación invernal (mayo-septiembre) y probabilidad de déficit de 3 años (adimensional).

**Conjunto de datos:** GPCC para observaciones; grandes ensambles SPEAR/FLOR (NOAA) para probabilidad. GPCC: 0,5°, 1891–presente; SPEAR: resolución variable, 1920–2100. URL de datos SPEAR: https://doi.org/10.25921/rwe5-fw03 (sin cuenta para algunos productos).

**Pasos para construir la serie anual:**
1. Calcular la precipitación total mayo-septiembre por año en GPCC.
2. Definir un déficit plurianual (p. ej., suma de 3 años por debajo del percentil 10).
3. Estimar la probabilidad empírica en observaciones.
4. Comparar con grandes ensambles históricos y futuros.
5. Calcular el factor de cambio de probabilidad.

**Resultado publicado:** El calentamiento antrópico aumentó la probabilidad del déficit 2015–2017 en un factor de 5–6; la probabilidad de un evento similar pasará de 0,7 % a 25 % en 2100 bajo SSP2-4.5. DOI: 10.1073/pnas.2009144117.

**Veredicto esperado:** Tendencia detectada en el riesgo de sequía. La tendencia de la lluvia anual por sí sola tiene evidencia insuficiente debido a la alta variabilidad interanual.

**Advertencias:** La región es pequeña; los modelos de baja resolución no capturan bien la orografía. El ENSO y el dipolo del Índico modulan la lluvia. El periodo 2015–2024 incluye el evento extremo, pero la tendencia de largo plazo es más incierta.

**Nota para la app:** Published check: Anthropogenic warming increased the likelihood of the 2015–2017 Cape Town rainfall deficit by a factor of 5–6 (DOI: 10.1073/pnas.2009144117).

---

### Caso 7: `lake_chad_surface_area`

**Título en inglés:** *Lake Chad Surface Area*  
**Definición:** Surface water extent of Lake Chad, a shallow lake in the Sahel that is highly sensitive to rainfall and human water use. It is not a simple shrinking story: the lake fluctuates strongly.

**Lugar:** Cuenca del Chad (centro: [13, 14]). Caja: lat 12–15, lon 13–16.

**Variable, unidad y agregación anual:** Área superficial media anual (km²).

**Conjunto de datos:** Series multi-satélite (MODIS, Landsat, altimetría). Producto de área de agua a partir de MODIS (p. ej., Copernicus C3S Lakes) o el conjunto de datos del estudio de referencia. Resolución 0,05°–0,25°, periodo 2003–2022. URL: https://cds.climate.copernicus.eu/ (cuenta).

**Pasos para construir la serie anual:**
1. Descargar máscaras de agua mensuales (MODIS o Landsat).
2. Calcular el área de agua por mes.
3. Promediar los meses para obtener el área anual.
4. Separar el pool norte y el pool sur si es posible.
5. Estimar la tendencia con Mann-Kendall.

**Resultado publicado:** La extensión del lago Chad se ha mantenido estable durante las dos últimas décadas, con un ligero descenso del pool norte. DOI: 10.1038/s41598-020-62417-w.

**Veredicto esperado:** Evidencia insuficiente para una tendencia monotónica. La narrativa popular de “el lago Chad desaparece” no se sostiene en las dos últimas décadas; el sistema es estacional y variable.

**Advertencias:** La superficie del lago depende de la estación y de la definición de “agua”. La cobertura satelital es buena desde 2000. La extracción de agua para riego y la variabilidad de la lluvia en la cuenca son factores clave.

**Nota para la app:** Published check: Lake Chad’s extent has remained stable over the last two decades, contradicting the “disappearing lake” narrative (DOI: 10.1038/s41598-020-62417-w).

---

### Caso 8: `lake_victoria_water_level`

**Título en inglés:** *Lake Victoria Water Level*  
**Definición:** Water level of Lake Victoria, Africa’s largest lake by area, which supports millions of people. It responds to rainfall, evaporation, and outflow regulation.

**Lugar:** Lago Victoria (centro: [−1, 33]). Caja: lat −3–0, lon 31–35.

**Variable, unidad y agregación anual:** Nivel medio anual del agua (m).

**Conjunto de datos:** Altimetría satelital multi-misión (p. ej., Copernicus, USDA Global Reservoir and Lake Monitor) y series del estudio de referencia. Resolución temporal mensual, periodo 1993–2016 (extensible con datos recientes). URL: https://www.pecad.fas.usda.gov/ (sin cuenta) o https://cds.climate.copernicus.eu/ (cuenta).

**Pasos para construir la serie anual:**
1. Descargar niveles de agua mensuales de altimetría.
2. Calcular la media anual.
3. Rellenar huecos con interpolación lineal si es necesario.
4. Estimar la tendencia lineal y la incertidumbre.
5. Comparar con la serie de precipitación de la cuenca.

**Resultado publicado:** El nivel del agua muestra una ligera disminución de −0,005 m/año (−0,05 m/década) entre 1993 y 2016. DOI: 10.1016/j.rse.2016.10.012.

**Veredicto esperado:** Tendencia detectada (descenso leve), pero la magnitud es pequeña y la variabilidad interanual es alta.

**Advertencias:** La construcción de presas y la regulación de la salida (presa de Owen Falls) afectan el nivel. La altimetría tiene errores de unos pocos centímetros. El periodo 1993–2016 puede no capturar tendencias más recientes.

**Nota para la app:** Published check: Lake Victoria’s water level declined slightly by ~0.05 m per decade (1993–2016) (DOI: 10.1016/j.rse.2016.10.012).

---

### Caso 9: `caspian_sea_level`

**Título en inglés:** *Caspian Sea Level*  
**Definición:** Water level of the Caspian Sea, the world’s largest inland water body. It is endorheic and highly sensitive to evaporation and river inflow.

**Lugar:** Mar Caspio (centro: [42, 51]). Caja: lat 36–47, lon 46–55.

**Variable, unidad y agregación anual:** Nivel medio anual del mar (cm).

**Conjunto de datos:** Altimetría satelital (Topex/Poseidon, Jason) y mareógrafos, compilados en el estudio de referencia. Resolución mensual, periodo 1996–2015 (extensible con datos de 2003–2024). URL: https://www.legos.omp.eu/ o https://cds.climate.copernicus.eu/ (cuenta para algunos productos).

**Pasos para construir la serie anual:**
1. Descargar la serie de nivel del mar de altimetría.
2. Promediar por año.
3. Calcular la tendencia para el periodo 1996–2015.
4. Comparar con la serie de evaporación y flujo de ríos.
5. Evaluar el cambio de régimen (aumento 1979–1995, descenso posterior).

**Resultado publicado:** Descenso de ≈ −6,72 cm/año entre 1996 y 2015, tras un aumento de ≈ +12,74 cm/año entre 1979 y 1995; el aumento de la evaporación explica la reversión. DOI: 10.1002/2017GL073958.

**Veredicto esperado:** Tendencia detectada (descenso fuerte y sostenido). Es uno de los casos más claros de cambio de nivel en la región.

**Advertencias:** El Caspio no tiene conexión con el océano; su nivel depende del balance entre precipitación, evaporación y flujo del Volga. La altimetría es fiable desde 1993. El cambio climático y la extracción de agua agravan el descenso.

**Nota para la app:** Published check: The Caspian Sea level dropped ~6.72 cm per year (1996–2015) after rising in the previous decades (DOI: 10.1002/2017GL073958).

---

### Caso 10: `sahara_dust_aod`

**Título en inglés:** *Sahara Dust Aerosol Optical Depth*  
**Definición:** Aerosol optical depth (AOD) from mineral dust over the Sahara. It measures how much sunlight is blocked by dust particles and affects radiation, clouds, and air quality.

**Lugar:** Sahara central y occidental (centro: [22, 5]). Caja: lat 15–30, lon −15–30.

**Variable, unidad y agregación anual:** AOD medio anual (adimensional) y AOD de polvo (DOD).

**Conjunto de datos:** MODIS Deep Blue AOD (producto MOD08_D3 o similar) y MERRA-2 reanálisis. MODIS: 1° o 0,1°, 2000–presente; MERRA-2: 0,5°×0,625°, 1980–presente. URLs: https://ladsweb.modaps.eosdis.nasa.gov/ (cuenta) y https://gmao.gsfc.nasa.gov/reanalysis/MERRA-2/ (sin cuenta).

**Pasos para construir la serie anual:**
1. Descargar AOD diario o mensual de MODIS para la caja.
2. Calcular la media mensual y luego anual.
3. Filtrar píxeles con nubes y calidad baja.
4. Calcular la tendencia espacial (por punto de rejilla) y la tendencia media regional.
5. Comparar MODIS con MERRA-2.

**Resultado publicado:** Tendencias positivas de AOD y DOD en el Sahara central (hasta +0,026 año⁻¹ ≈ +0,26/década) y en la península arábiga; tendencias negativas o neutras en el Sahara occidental. DOI: 10.5194/acp-24-2443-2024.

**Veredicto esperado:** Tendencia detectada, pero espacialmente heterogénea. No es una señal única para todo el Sahara.

**Advertencias:** Los cambios en los sensores MODIS (Terra vs. Aqua) y las actualizaciones de calibración pueden introducir saltos. La AOD depende de la humedad y del tamaño de las partículas. El ENSO y la AMO influyen en el transporte de polvo.

**Nota para la app:** Published check: Dust AOD increased in the central Sahara by up to ~0.26 per decade, with opposite trends in the western Sahara (DOI: 10.5194/acp-24-2443-2024).

---

### Caso 11: `mena_groundwater_grace`

**Título en inglés:** *MENA Groundwater Storage*  
**Definición:** Change in groundwater storage in the major transboundary aquifers of the Middle East and North Africa, derived from satellite gravity (GRACE). It indicates depletion or recharge.

**Lugar:** MENA (centro: [25, 20]). Caja: lat 15–40, lon −15–60 (acuíferos NSAS, NWSAS, Murzuk).

**Variable, unidad y agregación anual:** Anomalía de almacenamiento de agua subterránea (mm/año o km³/año), agregada como tendencia anual.

**Conjunto de datos:** GRACE y GRACE-FO mascons (p. ej., JPL, CSR, GFZ), resolución espacial ~300 km, periodo 2002–presente. URL: https://grace.jpl.nasa.gov/data/get-data/ (cuenta gratuita).

**Pasos para construir la serie anual:**
1. Descargar las anomalías de almacenamiento total de agua (TWS) de GRACE.
2. Restar la humedad del suelo y la nieve usando GLDAS.
3. Aislar la componente de agua subterránea (GWS).
4. Promediar sobre la caja del acuífero.
5. Ajustar una tendencia lineal y estimar la incertidumbre.

**Resultado publicado:** En el NWSAS, descenso de −3,62 ± 0,70 mm/año; en el NSAS, −1,28 ± 0,22 mm/año post-2009; en Murzuk, −2,41 ± 0,65 mm/año post-2010. DOI del capítulo: 10.1007/978-3-031-79122-2_2. Otra referencia: −8,8 mm/año en Irak y −6,0 mm/año en Siria (DOI: 10.1007/s10040-021-02448-3).

**Veredicto esperado:** Tendencia detectada (agotamiento). La señal es robusta en múltiples acuíferos y coincide con extracción humana y sequías.

**Advertencias:** GRACE tiene resolución espacial gruesa (~300 km) y no separa acuíferos individuales. La incertidumbre aumenta en regiones con datos limitados de GLDAS. El periodo 2002–presente incluye sequías severas y expansión agrícola.

**Nota para la app:** Published check: Groundwater storage in MENA aquifers declined by up to ~36 mm per decade (NWSAS, 2003–2021) (DOI: 10.1007/978-3-031-79122-2_2).

---

### Caso 12: `mediterranean_burned_area`

**Título en inglés:** *Mediterranean Burned Area*  
**Definición:** Annual area burned by wildfires in Mediterranean Europe. It measures fire activity, which is driven by heat, drought, and land management.

**Lugar:** Mediterráneo occidental (centro: [40, 0]). Caja: lat 36–45, lon −10–15.

**Variable, unidad y agregación anual:** Área quemada anual (ha).

**Conjunto de datos:** GFED5 (Global Fire Emissions Database v5), resolución 0,1°, periodo 1997–2022. URL: https://www.globalfiredata.org (SFTP con cuenta). Alternativa: FireCCI51 (2001–2020) y MCD64CMQ (2001–presente).

**Pasos para construir la serie anual:**
1. Descargar el área quemada mensual de GFED5 para la caja.
2. Sumar los meses para obtener el total anual.
3. Comparar con FireCCI51 y MCD64CMQ.
4. Calcular la tendencia con Mann-Kendall.
5. Evaluar la sensibilidad al producto.

**Resultado publicado:** Los análisis comparativos indican que el área quemada **no ha aumentado** en el Mediterráneo occidental en las últimas décadas; GFED5 muestra una tendencia decreciente, aunque con diferencias entre productos. DOI: 10.5194/essd-15-5227-2023.

**Veredicto esperado:** Los métodos no coinciden. La señal de tendencia es débil y depende del producto; no hay evidencia robusta de aumento.

**Advertencias:** Los productos de área quemada difieren en la detección de incendios pequeños. GFED5 incluye correcciones por incendios pequeños, pero la cobertura varía. El periodo 1997–2022 es relativamente corto para tendencias decenales. La variabilidad interanual es alta.

**Nota para la app:** Published check: Burned area in western Mediterranean Europe has not increased in recent decades; trends differ by product (DOI: 10.5194/essd-15-5227-2023).

---

## 3. Contradicciones y matices

- **Europa se calienta más rápido de lo que sugiere la temperatura media:** Las olas de calor aumentan 3–4 veces más rápido que la media de las latitudes medias del hemisferio norte, pero la temperatura media anual no muestra la misma aceleración. El mensaje popular “Europa se calienta como el resto del mundo” subestima el cambio en extremos.
- **El Sahel “se recupera”, pero no vuelve al estado pre-1970:** La lluvia ha aumentado desde 1990, pero la recuperación es parcial y la estación húmeda es más variable. La narrativa de “el Sahel se vuelve verde” debe matizarse: el verdor (NDVI) ha aumentado, pero no en todas partes y no siempre correlaciona con la lluvia.
- **La “paradoja” de África oriental no es una contradicción resuelta:** Las observaciones muestran secado de las lluvias largas, mientras que los modelos CMIP6 proyectan humedecimiento. La paradoja se reduce al prescribir SST observadas, lo que sugiere que los modelos no capturan bien la tendencia del Pacífico tropical.
- **El lago Chad no está desapareciendo en la actualidad:** La superficie se ha mantenido estable en las dos últimas décadas, con un ligero descenso del pool norte. La narrativa de “lago Chad desaparecido” se refiere a la contracción de los años 70-80, no a la tendencia reciente.
- **El Caspio no sube, baja:** El aumento de 1979–1995 se revirtió; desde 1996 el nivel desciende ≈ −6,72 cm/año. El mensaje popular de “el Caspio se recupera” está desactualizado.
- **El polvo del Sahara no aumenta en todas partes:** Hay tendencias positivas en el Sahara central y la península arábiga, pero negativas o neutras en el Sahara occidental. No se puede hablar de una tendencia única para todo el desierto.
- **Los incendios en el Mediterráneo no aumentan de forma consistente:** Los productos de área quemada discrepan; GFED5 muestra una tendencia decreciente, mientras que otros productos no detectan tendencia significativa. La percepción de “más incendios” puede estar influida por eventos extremos aislados.

---

## 4. Descartados

| Caso | Motivo de descarte |
|---|---|
| **Nivel del mar Caspio con datos de 2020–2024** | El periodo es demasiado corto (<10 años) para una tendencia climática robusta; además, los datos de altimetría recientes tienen menor cobertura. |
| **Incendios en la sabana africana (GFED5 por región)** | La señal de área quemada está dominada por prácticas agrícolas y de gestión del fuego, no solo por el clima; la atribución climática es confusa. |
| **NDVI del Sahel como caso independiente** | Se solapa con el caso de recuperación de lluvia; el verdor depende de la lluvia y de la gestión del suelo, y no aporta una tendencia climática distinta. |
| **Aguas subterráneas en el norte de África con GRACE a escala de acuífero individual** | La resolución de GRACE (~300 km) no permite separar acuíferos pequeños; se necesitan datos locales que no son públicos. |
| **Temperatura del Mediterráneo con boyas in situ** | La cobertura espacial es insuficiente para una serie anual regional; los datos satelitales son más adecuados y ya se usan en el caso 2. |
| **Olas de calor marinas en el Mediterráneo con definiciones alternativas** | La definición de MHW es metodológicamente sensible; se incluye dentro del caso 2 para evitar duplicidad. |
| **Nivel del lago Victoria después de 2016** | Los datos de altimetría recientes no están consolidados en un producto público único; se necesitaría una actualización que no está disponible con la misma calidad. |

---

## 5. Bibliografía

| Referencia | DOI | Fecha de comprobación |
|---|---|---|
| Rousi et al. (2022). Accelerated western European heatwave trends linked to more-persistent double jets over Eurasia. *Nature Communications*, 13, 3851. | 10.1038/s41467-022-31432-y | 2026-11-14 |
| Denaxa et al. (2024). Insights into sea surface temperature variability and the impact of long-term warming on marine heatwaves in the Mediterranean Sea. *State of the Planet* (preprint). | 10.5194/sp-2024-4 | 2026-11-14 |
| The GlaMBIE Team (2025). Community estimate of global glacier mass changes from 2000 to 2023. *Nature*, 639, 382–388. | 10.1038/s41586-024-08545-z | 2026-11-14 |
| Nnamchi & Fiedler (2026). Anthropogenic aerosols override greenhouse gases in Sahel climate change. *Communications Earth & Environment*. | 10.1038/s43247-026-03474-3 | 2026-11-14 |
| Schwarzwald & Seager (2024). Revisiting the “East African Paradox”: CMIP6 models also struggle to reproduce strong observed long rain drying trends. *Journal of Climate*, 37(24), 6641–6658. | 10.1175/JCLI-D-24-0225.1 | 2026-11-14 |
| Pascale et al. (2020). Increasing risk of another Cape Town “Day Zero” drought in the 21st century. *PNAS*, 117(47), 29495–29503. | 10.1073/pnas.2009144117 | 2026-11-14 |
| Pham-Duc et al. (2020). The Lake Chad hydrology under current climate change. *Scientific Reports*, 10, 5498. | 10.1038/s41598-020-62417-w | 2026-11-14 |
| Tong et al. (2016). Estimating water volume variations in Lake Victoria over the past 22 years using multi-mission altimetry and remotely sensed images. *Remote Sensing of Environment*, 187, 400–413. | 10.1016/j.rse.2016.10.012 | 2026-11-14 |
| Chen et al. (2017). Long-term Caspian Sea level change. *Geophysical Research Letters*, 44, 6993–7001. | 10.1002/2017GL073958 | 2026-11-14 |
| Rocha-Lima et al. (2024). Investigation of observed dust trends over the Middle East region in NASA GEOS model simulations. *Atmospheric Chemistry and Physics*, 24, 2443–2464. | 10.5194/acp-24-2443-2024 | 2026-11-14 |
| Groundwater Storage Variations in the MENA Transboundary Aquifer Systems Using GRACE: Response to Global Climate Change (2025). Springer chapter. | 10.1007/978-3-031-79122-2_2 | 2026-11-14 |
| Eltahan & Alahmadi (2019). Groundwater storage changes for 35 basins over MENA domain using GRACE during the period 2003–2017. *IOP Conf. Series: Earth and Environmental Science*, 384, 012127. | 10.1088/1755-1315/384/1/012127 | 2026-11-14 |
| Chen et al. (2023). Multi-decadal trends and variability in burned area from the fifth version of the Global Fire Emissions Database (GFED5). *Earth System Science Data*, 15, 5227–5259. | 10.5194/essd-15-5227-2023 | 2026-11-14 |
| Gaye (2026). Rainfall variability, vegetation dynamics, and the rainfall-NDVI relationship in the Sahel (1990–2022). *Environmental Research Communications*, 8, 061009. | 10.1088/2515-7620/ae7ceb | 2026-11-14 |