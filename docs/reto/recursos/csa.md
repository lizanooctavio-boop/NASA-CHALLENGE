# Recursos CSA: estado verificado y reproducción

Rama: `codex/recursos-csa`. Verificación: 2026-11-13. Los originales, las credenciales y las máscaras ráster permanecen fuera de Git. NDVI/LST y la integración de la interfaz pertenecen a las otras áreas asignadas.

| Requisito | Estado | Evidencia |
|---|---|---|
| Región canadiense | Entregada | `data/regiones_canada.geojson`, CAN_prairies; fuente oficial reproducible |
| SWOT y registro largo | Entregados | 211 observaciones válidas de Cocibolca y 123 de Xolotlán; 1,332 observaciones G-REALM |
| Radar | Cerrado como demostración NO_VALIDADA | 75 ráfagas VV ASF OPERA y 37 productos DSWx-S1; series cortas, máscaras y áreas candidatas; RCM requiere cuenta EODMS del equipo |
| IMERG y GISTEMP de Canadá | Calculados y contrastados | 24 valores anuales y estacionales 2001–2024; red NOAA de tres estaciones con 20 años comunes; adaptadores existentes sin cambios |
| Preguntas guiadas de ecosistemas | Redactadas en inglés | Textos más abajo, con cita de CSA |
| Fechas comunes SWOT–SAR | Comparadas, sin conclusión física | Tres pares del mismo día sobre un dominio fijo parcial del lago; no se afirma una tendencia física de superficie de agua |

## 1. Prairies: región canadiense para el agente 1

`CAN_prairies` es la ecozona Prairies del National Ecological Framework v2.2 de AAFC, 48.9949–54.245° N. Fuentes: [búsqueda en Geo.ca](https://geo.ca/home/?keys=Terrestrial%20Ecozones%20of%20Canada), [conjunto oficial](https://open.canada.ca/data/en/dataset/7ad7ea01-eb23-4824-bccc-66adb7c5bdf8), [GeoJSON de AAFC](https://agriculture.canada.ca/atlas/data_donnees/nationalEcologicalFramework/data_donnees/geoJSON/ez/nef_ca_ter_ecozone_v2_2.geojson). Atribución conservada: «Contains information licensed under the [Open Government Licence – Canada](https://open.canada.ca/en/open-government-licence-canada).» La atribución completa y el SHA-256 de la fuente están en las propiedades del elemento.

Disolución -> simplificación conservando topología a 0.01° -> make_valid -> precisión de 0.0001°. El área EPSG:6933 pasa de 467,029.4 a 467,127.9 km² (+0.021%); 4,058 coordenadas pasan a 605. La reproducción con `data/recursos/csa/construir_region_canada.py` coincidió con las propiedades de la geometría versionada. Es un límite de análisis, no una frontera oficial a escala fina.

## 2. Clima canadiense, 2001–2024

`python data/recursos/csa/descargar_canada.py --destino ../imerg_canada` obtiene los 288 gránulos mensuales GPM_3IMERGM V07B HDF5 mediante CMR/GES DISC y ejecuta el lector canadiense. Para originales ya descargados: `python data/recursos/csa/canada.py --imerg-dir ../imerg_canada`. `imerg_consulta.json` guarda las URL; `canada_imerg.json` guarda los hashes de originales, fracciones mensuales de área válida, valores anuales y estadísticas. Se multiplican las tasas mm/hr por las horas reales del mes antes de sumar el año. Se exigen doce meses válidos por año y >=95% del área válida por mes. La cobertura se calcula sobre todo el polígono, no solo sobre el ráster descargado. Se rechazan meses duplicados y unidades incorrectas.

Los 24 valores anuales de lluvia tienen una media de **435.17 mm/año**. Theil–Sen: **−30.4488 mm/década**, IC 95% **[−84.4022, +13.4341]**; Mann–Kendall modificado p=**0.1069**. Cobertura espacial mensual mínima: **99.9966%**. Veredicto: evidencia insuficiente de tendencia.

La cobertura no equivale a exactitud física de la recuperación. La región está dentro de la cobertura latitudinal de IMERG, pero siguen siendo importantes la nieve, el suelo congelado y la incertidumbre de precipitación de la estación fría. En la revisión previa aún no se había completado la validación canadiense con estaciones ni la sensibilidad a la estación cálida; ese resultado no demostraba ausencia de sesgo. El cierre canadiense se documenta en las secciones finales.

`python data/recursos/csa/canada.py` reproduce GISTEMP 250 km mediante los adaptadores existentes de lectura/agregación anual y los pesos por área compartidos, evitando únicamente su recorte específico de Nicaragua. `canada_gistemp.json` contiene 24 valores anuales. Theil–Sen: **+0.1751 °C/década**, IC 95% **[−0.5684, +0.7535]**; Mann–Kendall modificado p=**0.6374**. La temperatura es anomalía respecto de 1951–1980. Se requieren al menos diez meses válidos por año, igual que en el adaptador existente. Se renormalizan las observaciones espaciales ausentes; sigue siendo aconsejable evaluar la sensibilidad a esa cobertura. Hash del NetCDF original: `gistemp_fuente.json`.

Ambas salidas climáticas tienen papel `tendencia`. `imerg.py` y `gistemp.py` no se modifican.

## 3. SWOT y G-REALM

[SWOT de CSA](https://www.asc-csa.gc.ca/eng/satellites/swot/) describe la misión internacional y la contribución canadiense. [Hydrocron](https://podaac.github.io/hydrocron/overview/) ofrece series LakeSP orientadas a PLD sin iniciar sesión. Identificadores PLD verificados: **Cocibolca 7530096743**, **Xolotlán 7530093763**. La evidencia de identificación LakeSP, nombres, coordenadas y hashes está en `pld_lake_ids.json`. Ambos identificadores se consultaron independientemente con éxito en Hydrocron.

`lagos.py` construye peticiones Hydrocron, analiza el CSV encapsulado, elimina duplicados, rellenos/registros no_data y quality_f >=2, y calcula medias mensuales. Resultado: **211 observaciones válidas de Cocibolca**, julio de 2023–noviembre de 2026, y **123 de Xolotlán**, agosto de 2023–noviembre de 2026; 41 y 40 valores mensuales. Respuestas originales, consultas y hashes están versionados. Su papel es **demostracion_registro_corto**, no tendencia climática. La guarda computacional de diez años es un mínimo, no una garantía de inferencia climática adecuada.

Todos los registros SWOT aceptados son observaciones parciales (`partial_f=1`). No debe interpretarse area_total de SWOT como superficie completa del lago. WSE sigue las convenciones de calidad del producto; una incertidumbre reportada de cero no representa precisión perfecta.

[NASA GSFC G-REALM](https://earth.gsfc.nasa.gov/gwm/lake/Index), objetivo **000351 Nicaragua**, aporta **1,332 alturas válidas de Cocibolca, 1992-10-02–2026-11-07**. Fuente: `https://earth.gsfc.nasa.gov/gwm/zip/lake.10.tar.gz`; se conservan el hash del archivo y el extracto canónico `grealm_lake000351.10d.2.txt`. La columna 15 es la altura en metros EGM2008. `leer_grealm` mantiene la devolución compatible de fechas/alturas; `leer_grealm_gsfc` expone el detalle por misión. No se verificó una serie G-REALM de Xolotlán.

Las 41 medias mensuales comunes SWOT–G-REALM dan r≈0.99 y sesgo SWOT−G-REALM≈−0.437 m (desviación típica de la diferencia≈0.073 m). La concordancia respalda la consistencia entre productos durante este período común corto; no prueba de forma independiente la estabilidad a largo plazo ni la causa del desplazamiento. No se deben empalmar datums/productos sin ajuste documentado y análisis de incertidumbre.

## 4. Radar: datos reales y fallo de interpretación con umbral fijo

El [recurso RCM de CSA](https://donnees-data.asc-csa.gc.ca/en/dataset/rcm) remite a EODMS. La primera consulta manual devolvió HTTP 400; el reintento con py-eodms-rapi/RCMImageProducts devolvió un error de autenticación. Ningún resultado prueba ausencia de escenas RCM abiertas. Su disponibilidad sigue sin resolverse. La demostración usa explícitamente **Sentinel-1 mediante ASF/Earthdata**, no RCM.

`python scripts/sar/opera_demostracion.py` descarga **75 ráfagas VV OPERA_L2_RTC-S1_V1** de la órbita T092 para **2024-03-04, 2024-04-21 y 2024-07-14**. URL/hashes de productos: `sar_fuentes.json`. La [guía oficial OPERA](https://hyp3-docs.asf.alaska.edu/guides/opera_rtc_product_guide/) especifica potencia gamma0, corregida por terreno, 30 m, sin filtro de moteado. Se ensamblan ráfagas sin doble conteo, se promedia la potencia a 100 m EPSG:6933 y se convierte con **10 log10**. No se cambia la etiqueta gamma0 por sigma0. La potencia inválida/no positiva nunca se convierte en agua candidata.

Se alinean todas las fechas a una malla. La máscara válida común se mantiene fija; se prueba agua candidata a **−19/−17/−15 dB**. El dominio observado común de Cocibolca es **2,602.37 km²**, aproximadamente **33.3%** del polígono de análisis Natural Earth de 7,821.56 km². No se extrapola al área total del lago. Natural Earth 10m lakes es de dominio público; el subconjunto versionado tiene Wikidata Q173862. Los dominios de Los Guatuzos y San Juan se identifican como ventanas rectangulares de análisis, no límites oficiales de humedales/áreas protegidas. Sus áreas válidas comunes son 840.87 y 968.86 km².

`data/recursos/csa/sar_superficie.csv` contiene 27 registros de área candidata. **Son clasificaciones de baja retrodispersión, no superficies físicas de agua validadas.** En el mismo dominio cartografiado del lago, la fracción candidata a −17 dB cae drásticamente en dos fechas. Es un fallo del control de calidad de un umbral universal, no evidencia de desecación de la mayor parte del lago. La rugosidad por viento, incidencia, ruido residual, píxeles mixtos y elección del umbral son hipótesis por investigar, no causas establecidas. No se publica una tendencia climática ni un cambio validado de superficie de agua.

`backend/clima_nic/fuentes/sar_agua.py` también expone el flujo más simple de máscara/área sigma0-dB calibrado para GeoTIFF aportados por el usuario. El flujo OPERA real mantiene explícita su radiometría diferente. Rásteres originales, mosaicos y máscaras permanecen en `../opera_rtc`, fuera de Git.

### Tutorial CSA y cuaderno

`scripts/sar/agua_superficial.ipynb` adapta lectura ráster, inspección del CRS y arreglos enmascarados del [Tutorial SAR de CSA](https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial), Option 2 Python, BC Wildfire raster plot. Copyright Canadian Space Agency 2022; licencia **MIT** conservada en `scripts/sar/LICENSE-CSA.txt`. El umbral es una extensión del proyecto, no un clasificador de agua validado por CSA. El cuaderno documenta ambas radiometrías y ejecuta OPERA real cuando `SAR_RUN_OPERA=1`. Sin datos/autorización no fabrica mediciones.

## 5. Comparación SWOT–SAR del mismo día calendario

`sar_superficie.csv` y `comparacion_swot_sar.csv` usan el mismo dominio parcial fijo del lago. Mismo día no significa adquisición simultánea. Las horas de adquisición radar están codificadas en los identificadores conservados en el manifiesto.

| Día UTC | WSE SWOT, metros EGM2008 | Área candidata de baja retrodispersión a −17 dB, km² | Área observada fija del lago, km² |
|---|---:|---:|---:|
| 2024-03-04 | 31.528 | 8.31 | 2602.37 |
| 2024-04-21 | 31.258 | 2267.65 | 2602.37 |
| 2024-07-14 | 31.713 | 171.02 | 2602.37 |

El menor nivel SWOT coincide con la mayor área candidata, y las áreas candidatas fallan la comprobación sobre el lago conocido. Por tanto, **no validan una relación física altura–superficie**. No se afirma significancia de correlación con tres puntos. Hacen falta un clasificador validado, cobertura más amplia y una referencia independiente de orilla antes de publicar cambios reales de superficie de agua.

SWOT desde 2023 y tres fechas radar son registros cortos. Más observaciones podrían aumentar la potencia estadística y volver significativa una tendencia persistente, como señala el reto, pero no se garantiza significancia. Un registro más largo no repara un clasificador sesgado o inválido: estacionalidad, autocorrelación, estabilidad del sensor y manejo hidrológico siguen requiriendo tratamiento explícito.

## 6. Guided questions — English copy

### Vegetation & ecosystems

Satellite observations can help identify changes in forest condition, land cover and habitat. Ask whether a greenness change persists across years and whether it coincides with disturbance or land-use change. Compare regional vegetation indicators with moisture and temperature, while keeping association separate from causal explanation. [CSA ecosystem monitoring](https://www.asc-csa.gc.ca/eng/satellites/everyday-lives/monitoring-and-protecting-our-ecosystems-from-space.asp).

### Water bodies

Satellite radar can map water extent, while SWOT measures water-surface elevation. Ask whether a lake's height and mapped area change together on comparable dates. Changes can reflect seasonal inflows, evaporation and water management, so a short record should be presented as a demonstration rather than a climatic trend. [CSA ecosystem monitoring](https://www.asc-csa.gc.ca/eng/satellites/everyday-lives/monitoring-and-protecting-our-ecosystems-from-space.asp).

## 7. Límites científicos restantes

Earthdata, GES DISC y ASF ya funcionan. No hay credenciales en el PR. Siguen siendo sustantivos la disponibilidad RCM no resuelta, la falta de clasificación SAR/orilla independiente validada, la cobertura parcial del lago y tres comparaciones del mismo día, y la incertidumbre invernal canadiense. La validación con estaciones se actualiza al cierre. Estos resultados no deben presentarse como superficies de agua climáticas plenamente validadas. No se incluye fusión, despliegue ni integración de interfaz.

## Verificación histórica

`python -m pytest tests -q`: **111 pruebas aprobadas, 1 omitida, 57 subpruebas aprobadas** en la primera entrega real. Incluye coherencia de resultados reales (24 años canadienses, 288 meses únicos, cobertura >=95%; dominios SAR constantes, sensibilidad monótona al umbral y tres pares SWOT del mismo día), y comprobaciones sintéticas de unidades, bisiestos, meses ausentes, rellenos y conversión potencia-dB. La adquisición y ambos scripts se ejecutaron con datos reales. `imerg.py`/`gistemp.py` no cambiaron. Las pruebas informáticas no demuestran significancia estadística ni validez del clasificador.

## 8. Intento de calibración óptica independiente: resultado y control de publicación

Reproducción: `python scripts/sar/calibrar_optica.py` después de la demostración RTC. Obtiene clasificaciones ópticas agua/tierra **OPERA_L3_DSWX-HLS_V1 B02_BWTR** de PO.DAAC, con desfase máximo de dos días. La colección descargada indica **PROVISIONAL** en las rutas: es evidencia óptica independiente, no verdad de campo. La [documentación DSWx de NASA JPL](https://www.jpl.nasa.gov/go/opera/products/dswx-product-suite/) describe las familias óptica y radar. Solo se usan clases binarias claras 0/1; se excluyen nubes, sombras, nieve, océano y rellenos. Se reproyectan máscaras categóricas por vecino más próximo, no por promedio.

El primer experimento eligió un mosaico más cercano por fecha; sus resultados favorables y desfavorables se conservan en `sar_validacion_optica_tile_unico.json` y `sar_superficie_calibrada_tile_unico.csv`. El segundo usa la observación **clara más cercana por píxel** dentro del mismo límite +/-2 días, conservando todas las fuentes. Mejora el tratamiento de nubes sin ampliar el tiempo ni tratar nubes como tierra. El agua/tierra puede cambiar en dos días y los productos ópticos también tienen errores.

La calibración elige por fecha un umbral inferior de retrodispersión que maximiza la **exactitud balanceada de entrenamiento**. Entrena en franjas de 5 km (0 módulo 4), evalúa en franjas 2 módulo 4 y no usa franjas 1 y 3. No optimiza umbrales con la evaluación, altura SWOT ni área deseada del lago. Son particiones espaciales dentro de cada fecha, no una demostración de transferencia temporal. Esta etapa no tenía una fecha externa reservada.

| Fecha radar | Umbral dB | F1 en evaluación reservada | Sensibilidad al agua | Sensibilidad a tierra | Control del clasificador |
|---|---:|---:|---:|---:|---|
| 2024-03-04 | -10.6 | 0.9344 | 0.9802 | 0.9648 | Superado |
| 2024-04-21 | -15.8 | 0.0222 | 0.0112 | 0.9999 | Fallido |
| 2024-07-14 | -8.0 | 0.7523 | 0.8390 | 0.9389 | Fallido |

Hay una mejora concreta en marzo, **no una solución general**. La calibración no se transfiere adecuadamente entre regiones espaciales en abril y julio. El área óptica clara común a las tres fechas dentro del dominio observado del lago es solo **0.02 km²** de 2,602.37 km². Muchas muestras en otras partes de la escena no compensan la ausencia de referencia del lago. No se valida una relación estacional o de superficie del lago completo.

`surface_quality_gate_passed` exige F1 y sensibilidades al agua/tierra >=0.90 **y** al menos 80% de referencia óptica clara común en el dominio. Es una regla conservadora necesaria, no un estándar universal de validación. `area_water_validated_km2` indica `NO_VALIDADA` con motivo explícito cuando falla. **Las nueve combinaciones fecha/dominio fallan actualmente el control de publicación.** Se conservan candidatos calibrados para diagnóstico sin convertirlos en mediciones validadas.

Las consultas CMR de OPERA_L3_DSWX-S1_V1 sobre esos tres días no devolvieron gránulos; ello no demuestra ausencia del producto en otras fechas. EODMS RCM necesita acceso propio; Earthdata no otorga autorización EODMS. La búsqueda ampliada de cierre se documenta al final.

### Alcance científico de la asignación CSA

Están entregados región canadiense, IMERG/GISTEMP, SWOT/G-REALM, demostración SAR reproducible con datos reales, textos ingleses y comparaciones del mismo día. La superficie física SAR seguía **parcial** antes del encargo de cierre. Validarla requiere referencia de orilla utilizable, evaluación espacial/temporal satisfactoria en fechas difíciles y mayor cobertura para afirmar área total del lago. Más longitud temporal no repara un clasificador ni una referencia ausente. No se infiere una tendencia climática ni relación altura–superficie fiable. El nuevo alcance permite cerrar el radar como demostración documentada.

Verificación tras calibración óptica: `python -m pytest tests -q` -> **114 aprobadas, 1 omitida, 57 subpruebas aprobadas**. Se comprobó que cambiar etiquetas reservadas no altera el umbral ajustado, que las métricas indefinidas no cuentan como éxito y que buenas métricas con referencia insuficiente no publican superficie validada.

## 9. Modelo dual, evaluación temporal y estados completos

Reproducción de la secuencia tras autenticar:

```text
python -m pip install -r scripts/sar/requirements.txt
python scripts/sar/opera_demostracion.py
python scripts/sar/calibrar_optica.py
python scripts/sar/modelo_dualpol.py
```

`requirements.txt` fija las versiones probadas; `entorno_reproduccion.json` las registra. `modelo_dualpol.py` obtiene **75 bandas VH correspondientes**, con URL y SHA-256, para las 75 adquisiciones VV originales: **75 adquisiciones de polarización dual / 150 rásteres de bandas**, no 150 observaciones independientes. Ensambla y alinea a la malla fija de 100 m; usa siete predictores radar: VV dB, VH dB, diferencia, medias y desviaciones locales sobre 300 m. Coordenadas, etiquetas ópticas, contorno, índice de fecha y SWOT no son predictores.

RandomForest de 80 árboles, profundidad 12, hoja mínima 30, semilla 8687 y pesos balanceados del remuestreo, entrenado con hasta 10,000 píxeles ópticos claros por clase/fecha. Se reservan las mismas franjas espaciales en cada fecha. Además de evaluar espacialmente el modelo combinado, se entrena con dos fechas y se evalúa la tercera (**leave-one-date-out**) sobre sus franjas reservadas. Los hiperparámetros se fijaron antes de estas pruebas. [Documentación del estimador](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html).

| Fecha | F1 espacial del modelo combinado | F1 dejando una fecha fuera |
|---|---:|---:|
| 2024-03-04 | 0.8720 | 0.5062 |
| 2024-04-21 | 0.1982 | 0.0467 |
| 2024-07-14 | 0.8724 | 0.8967 |

Las estimaciones duales del dominio fijo del lago son 2516.84, 2519.97 y 2515.06 km². Desaparece el salto extremo del umbral fijo, pero **estabilidad no demuestra exactitud**. Las evaluaciones espacial/temporal siguen siendo insuficientes. Julio mejora respecto del umbral VV calibrado, mientras que en marzo el umbral calibrado conserva mejor evaluación espacial; no se declara un método universalmente superior y se conservan los fallos.

`area_ambigua_prob_025_075_km2` cuenta píxeles con fracciones de votos del bosque entre 0.25 y 0.75. No son probabilidades calibradas ni un intervalo de confianza de superficie. `sar_dualpol_validacion.json` guarda métricas, parámetros, tamaños de entrenamiento, fechas excluidas y hashes VH. `comparacion_swot_sar_dualpol.csv` empareja estimaciones con SWOT e incluye inicio/fin de adquisición radar, haciendo explícita la falta de simultaneidad.

Cada fila de `sar_dualpol_superficie.csv` contiene estimación numérica, área observada, ambigüedad, cobertura, estado y motivo. Una superficie física no validada se indica como **NO_VALIDADA**, nunca celda vacía o cero inventado. Las nueve combinaciones permanecen estimadas/sin validar. El CSV del umbral calibrado usa la misma convención. Los null de parámetros sklearn son valores predeterminados documentados (p. ej. ausencia de límite), no mediciones omitidas.

`cumplimiento_csa.json` proporciona estado técnico/científico, evidencia, límite y próxima acción para **los seis requisitos originales**. Región/datos/textos/reproducción están entregados. La referencia actual no permite certificar las áreas; la integración de interfaz está fuera de los archivos de este agente.

Verificación tras modelo dual: `python -m pytest tests -q` -> **116 aprobadas, 1 omitida, 57 subpruebas aprobadas**. Incluye unidades/nodata, tablas sin celdas vacías, estados explícitos de área inválida y exclusión de cada fecha objetivo del entrenamiento temporal.


## 10. Cierre canadiense: estación cálida y estaciones NOAA

### 10.1 Mayo a septiembre, 2001–2024

Comando: `python data/recursos/csa/canada.py --imerg-dir ../imerg_canada --may-sep`. Se usan los mismos 288 HDF5, tasas mm/hr multiplicadas por horas reales y pesos EPSG:6933. Un año se admite únicamente con los **cinco meses mayo–septiembre válidos**, cada uno con cobertura >=95%; no se rellenan meses. Salida en el formato acordado: `canada_imerg_may_sep.json`, papel `tendencia`, unidad `mm/year` (total estacional de cada año).

Los 24 años completos tienen media **295.5445 mm**, pendiente Sen **−20.2015 mm/década**, IC 95% **[−62.2468; +23.2485]** y veredicto `evidencia_insuficiente`. El resultado estacional no sustituye ni modifica la serie anual.

### 10.2 Lector y selección NOAA

Se implementó `data/recursos/csa/noaa_canada.py` sin importar `noaa_cdo.py`. Reproducción: `python data/recursos/csa/noaa_canada.py --cache ../noaa_canada --gsom`. El inventario GHCN-Daily dio **96 candidatas** dentro del polígono con posibilidad temporal de 20 años entre 2001 y 2024, incluyendo estaciones terminadas antes de 2024. Se evaluaron datos, no solo fechas del inventario.

La prueba estricta GHCN-Daily, que exige todos los días válidos y elimina QFLAG no vacío, rellenos y MFLAG P (ausente presumido cero), no encontró tres registros que cumplieran 20 años completos de PRCP y temperatura. Por eso se utilizó **GSOM**, permitido por el encargo. Fuentes: [inventario GHCN-Daily](https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-inventory.txt), [metadatos de estaciones](https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt), [Access Data Service v1](https://www.ncei.noaa.gov/support/access-data-service-api-user-documentation), [documentación GSOM](https://www.ncei.noaa.gov/pub/data/cdo/documentation/gsom-gsoy_documentation.pdf).

En GSOM, **año completo significa doce resúmenes mensuales válidos publicados por NOAA** para PRCP y TAVG; no equivale a 365/366 días medidos. NOAA puede publicar un mes con hasta cinco días ausentes, bajo sus reglas y marcas. Se guardan esas marcas y se rechazan meses ausentes o con calidad PRCP inválida. No se imputó ningún día ni mes ni se empalmaron identificadores. Los CSV mensuales conservan `NA` para valores ausentes, que nunca entran en un año admitido.

La selección usa completitud y separación geográfica, sin mirar pendientes ni correlaciones. Se fija la misma red en todos los años comparados:

| Estación | Nombre | Latitud | Longitud | Años conjuntos GSOM completos 2001–2024 | Mínimo de observaciones por mes de referencia 1951–1980 |
|---|---|---:|---:|---:|---:|
| CAN04016322 | QU'APPELLE 1 | 50.5667 | -103.9833 | 23 | 18 |
| CAN04014040 | KIPLING | 50.2 | -102.7333 | 22 | 22 |
| CAN04013660 | KELLIHER | 51.2574 | -103.753 | 21 | 24 |

Comparten **20 años**: 2001, 2002, 2004–2010, 2012–2018, 2020–2022 y 2024. Se omiten 2003, 2011, 2019 y 2023: no se rellenan ni cambia la composición de la red. Todas están en Saskatchewan, dentro de Prairies; su media es un contraste de tres puntos, no una media areal de toda la ecozona ni una validación de sus tres provincias.

La temperatura anual es media de las doce TAVG mensuales. Para compararla con las anomalías GISTEMP se resta a cada estación su referencia **estimada de 1951–1980**, construida con las doce medias por mes calendario; el lector exige >=15 observaciones de referencia por mes y las estaciones elegidas tienen al menos 18, 22 y 24, respectivamente. No es una normal WMO completa de 30 años. La selección del período de referencia introduce incertidumbre en la diferencia media; no se resta temperatura absoluta a una anomalía ni se centra artificialmente ambas series en 2001–2024 para forzar sesgo cero.

Se conservan consultas, hashes, criterios y conteos en `noaa_canada_inventario.json` (cribado diario) y `noaa_canada_inventario_gsom.json` (selección mensual). `noaa_canada_mensual.csv` y `noaa_canada_estaciones_anuales.csv` permiten auditar meses y agregación; los originales completos permanecen fuera de Git. `noaa_canada_detalle.json` guarda tendencias completas y comparación estacional.

### 10.3 Contrastes en los 20 años comunes

Salidas de integración: **`contrastes_canada.json`**, esquema `nasa-challenge/contrastes`, versión `1.0.0`, identificadores exactos `noaa_canada_lluvia` y `noaa_canada_tavg`; fuentes y `frase_en` en inglés. **`contrastes_canada_series.csv`** tiene columnas `contraste,serie,anio,valor` y 80 filas (dos productos, dos series y 20 años). `serie` es `nuestra` o `externa`. La red externa es la media aritmética de las mismas tres estaciones en cada año.

| Variable | r de Pearson | Diferencia media estación − NASA | Sen NASA | Sen estaciones | Veredictos NASA / estaciones |
|---|---:|---:|---:|---:|---|
| Lluvia anual | 0.8301165 | +35.2508 mm | −30.4488 mm/década | −19.6833 mm/década | evidencia_insuficiente / evidencia_insuficiente |
| Temperatura, anomalía | 0.9607669 | +0.381660 °C | +0.1737 °C/década | +0.2396 °C/década | evidencia_insuficiente / evidencia_insuficiente |
| Lluvia mayo–septiembre | 0.8456622 | +16.06794 mm | −25.2676 mm/década | −29.7165 mm/década | evidencia_insuficiente / evidencia_insuficiente |

Las pendientes del contraste se recalculan sobre los mismos **20 años**, no se copian las de la serie NASA de 24 años. Por eso, por ejemplo, la temperatura NASA del contraste es +0.1737 y la completa +0.1751 °C/década. Los IC 95% de lluvia anual común son NASA [−91.0076; +27.2304] y estaciones [−107.4048; +63.6667] mm/década; los térmicos son [−0.6168; +0.7535] y [−0.4921; +1.1019] °C/década. Para mayo–septiembre común son [−73.5733; +27.1960] y [−99.3333; +48.8148] mm/década. El CSV estacional auxiliar es `noaa_canada_may_sep_series.csv`; sus estadísticas están en `noaa_canada_detalle.json`, sin añadir un tercer ID al formato de interfaz acordado.

### 10.4 Invierno, subcaptación y límites del contraste

Los pluviómetros pueden subcaptar nieve por el viento, y existen pérdidas por mojado/evaporación y diferencias de conversión de nieve a equivalente de agua. [Environment and Climate Change Canada](https://www.canada.ca/en/environment-climate-change/services/climate-change/science-research-data/climate-trends-variability/adjusted-homogenized-canadian-data/precipitation.html) documenta correcciones de esos efectos en sus productos ajustados. Aquí no se aplicó una corrección inventada a GSOM ni se asumió que el pluviómetro fuera verdad sin error.

En la estación cálida la correlación es 0.846 y la diferencia +16.07 mm; fuera de mayo–septiembre es **r=0.693008**, diferencia **+19.18287 mm**. Este último agregado es octubre–abril **del mismo año calendario**, no un invierno DJF continuo. La menor concordancia fuera de la estación cálida es compatible con mayores dificultades de medición/recuperación, pero no identifica su causa. El sesgo anual positivo de las estaciones no se atribuye solo a subcaptación: también influyen la selección espacial de tres estaciones y comparar puntos con la media de toda la ecozona.

GISTEMP utiliza estaciones y puede compartir insumos con las observaciones NOAA; IMERG Final incluye ajuste pluviométrico. Este es un contraste externo de productos y procesamiento, no una prueba de independencia total entre sensores ni una atribución causal del cambio climático. No hay tendencia significativa detectada en ninguna de las series comparadas en esta ventana.

## 11. Cierre acotado del radar y consulta opcional

La consulta CMR ampliada de `OPERA_L3_DSWX-S1_V1` sobre Cocibolca entre 2024 y 2026 devolvió **1437 coincidencias**; la URL, hora y respuesta están en `dswx_s1_busqueda_cierre.json`. El resultado corrige el alcance de la búsqueda anterior, limitada a tres días sin productos. Se usaron **37 productos oficiales** en tres fechas disponibles como **serie corta**, no como referencia independiente del modelo: comparte Sentinel-1 y otros insumos radar.

Comando reproducible: `python scripts/sar/dswx_s1_cierre.py`. Solo se admiten clases BWTR 0/1; se excluyen otras clases, rellenos y píxeles donde las clasificaciones superpuestas discrepan. Se usa vecino más próximo para categorías, malla EPSG:6933 de 100 m y máscara común fija, sin extrapolación. Fuente: [DSWx-S1 en PO.DAAC](https://podaac.jpl.nasa.gov/dataset/OPERA_L3_DSWX-S1_V1).

| Fecha | Productos | Píxeles conflictivos excluidos dentro del lago | Agua clasificada en dominio común, km² |
|---|---:|---:|---:|
| 2024-09-24 | 17 | 191 | 2486.81 |
| 2024-12-17 | 11 | 0 | 2488.28 |
| 2026-01-17 | 9 | 1 | 2489.03 |

El dominio válido común es **2585.25 km²**, cobertura **0.3305156** del polígono (~33.05%). Salidas: `dswx_s1_serie_corta.csv` y `dswx_s1_cierre.json`, con hashes y horas de adquisición. Se mantiene **NO_VALIDADA**, por falta de validación local independiente y cobertura parcial; no se calcula tendencia ni relación causal altura–área. El radar queda **cerrado como demostración documentada**, conforme al alcance de cierre. No se ajustó ningún clasificador adicional en este encargo. RCM solo se retomará si el equipo aporta una cuenta EODMS existente; no se creó ninguna.

Consulta opcional Xolotlán: [DAHITI identifica Managua con ID 194](https://dahiti.dgfi.tum.de/en/194/), pero la [API de descarga](https://dahiti.dgfi.tum.de/en/api/doc/v2/) requiere cuenta/clave. [Hydroweb.next](https://hydroweb.next.theia-land.fr/help) exige autenticación y clave API para descargar. Se detuvo la tarea según el encargo: **sin serie larga descargada, sin cuenta creada y sin inventar observaciones**. Detalle: `xolotlan_serie_larga_acceso.json`. SWOT de Xolotlán permanece disponible.

## 12. Cronología, preparación previa al evento y uso de IA

Este trabajo se declara como **preparación previa al evento**, según el contexto del equipo. Se utilizó **Codex/IA** para programación, traducción, búsqueda de fuentes y redacción; las cifras proceden de los archivos reales y cálculos reproducibles, no de generación de datos. El responsable debe conservar esta declaración en la entrega del evento. No se afirma trabajo humano manual ni validación de campo.

| Avance de este cierre (2026-11-13) | Hora UTC | Hora America/Mexico_City, UTC−06 |
|---|---|---|
| Inicio y lectura de las tres referencias del encargo | 08:24:09 | 02:24:09 |
| Traducción, deduplicación y cálculo canadiense registrados | 08:38:10 | 02:38:10 |
| Radar oficial y consulta opcional cerrados | 08:40:01 | 02:40:01 |
| Pruebas finales y preparación de publicación | 08:48:50 | 02:48:50 |

Cada avance tiene fecha/hora UTC y local en `avances_cierre.jsonl`. La traducción conservó enlaces, comandos y cifras anteriores; las preguntas guiadas siguen en inglés. La limpieza se completó dentro de 30 minutos. Se comprobó con `git grep` que el único nombre referenciado era `grealm_lake000351.10d.2.txt`; los dos TXT tenían SHA-256 **f0475a29fcdc50073853602807bdd8666d39c3b8f8ba16c11e6adde472c3b6d9**. Se conservó ese nombre canónico y se eliminó únicamente el duplicado `cocibolca_grealm.txt`; el CSV derivado no es un duplicado del TXT.

El verificador de esta base ejecuta **88/88 comprobaciones correctas**, frente a las 80/80 mencionadas en el encargo. Se conserva íntegro su código y el contrato; no se cambia el recuento para aparentar 80. Las pruebas finales del cierre constan en `pruebas_cierre.json`: **123 aprobadas, 57 subpruebas aprobadas, ninguna omitida**. Se instaló la dependencia opcional de la API para ejecutar también esa prueba. Se observó un aviso de obsolescencia externo de Starlette/httpx, sin fallos. Reproducción del entorno de prueba: `python -m pip install pytest fastapi httpx` y después `python -m pytest tests -q`. No se editan interfaz, `recursos.py` ni archivos de otros agentes, y no se fusiona el PR.
