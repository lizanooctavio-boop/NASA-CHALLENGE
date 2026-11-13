# Contrastes externos de las series del proyecto

Este documento corresponde al agente 2 (contrastes). Las cifras salen de `data/recursos/contraste/resumen_contrastes.json`, que genera
`data/recursos/contraste/generar_contrastes.py`. Las consultas se hicieron el 12 y el 13 de noviembre de 2026.

Cada contraste tiene un **papel**:

- **contraste**: otra fuente o método mide lo mismo que una serie nuestra. Sirve para saber cuánto se puede confiar en esa serie.
- **tendencia**: variable nueva, sin serie propia previa. Se analiza con los mismos métodos.

El panel «Cross-checks» usa el campo `frase_en` de cada entrada.

## 1. Métodos comunes

- **Tendencia.** Usa los métodos del backend, sin copiarlos: `clima_nic.fuentes.giovanni.veredicto_serie` llama a `tendencia_robusta.analizar`.
  - El veredicto del contrato 1.0.0 (`tendencia.py`) usa mínimos cuadrados con grados de libertad ajustados por AR(1), HAC de Newey–West y Theil–Sen. Hay tendencia cuando los tres intervalos del 95 % excluyen el cero con el mismo signo y p < 0,05.
  - El veredicto robusto exige además Mann–Kendall modificado (Hamed y Rao).
  - La pendiente que se informa es la de **Sen por década**.
  - Con las series de IMERG de `data/clima.json` se reproducen exactamente su pendiente MCO y su veredicto. Lo comprueba `test_imerg_nuestra_coincide_con_clima_json`.
- **Comparación.** Se hace en los años comunes:
  - `diferencia.media` = externa − nuestra (media anual);
  - `r` = Pearson entre totales o medias anuales;
  - `diferencia_pendiente` = Sen externa − Sen nuestra.
- **Regiones de lluvia.** Para las mallas (CRU, GPCC) se usan los mismos polígonos de `data/dominios.geojson` y la misma ponderación por área de intersección (EPSG:6933) que `recortar_malla`.
- **Reproducibilidad.** `series_anuales.csv` guarda la entrada exacta de cada cálculo de tendencia. Las pruebas recalculan con ella los veredictos y las pendientes.

## 2. Resumen de cifras

| id | papel | período | nuestra (Sen/década, veredicto) | externa (Sen/década, veredicto) | dif. media | r |
|---|---|---|---|---|---|---|
| cru_caja_sicc | contraste | 2001–2024 | IMERG −28,7 mm, ev. insuficiente | CRU TS 4.10 +6,7 mm, ev. insuficiente | +209 mm | 0,71 |
| cru_nic | contraste | 2001–2024 | IMERG −64,9 mm, ev. insuficiente | CRU TS 4.10 −21,3 mm, ev. insuficiente | +210 mm | 0,63 |
| gpcc_caja_sicc | contraste | 2001–2024 | IMERG −28,7 mm, ev. insuficiente | GPCC −15,9 mm, ev. insuficiente | +127 mm | 0,81 |
| gpcc_nic | contraste | 2001–2024 | IMERG −64,9 mm, ev. insuficiente | GPCC −79,2 mm, ev. insuficiente | −47 mm | 0,94 |
| noaa_managua_tavg | contraste | 2001–2024 | POWER/MERRA-2 +0,01 °C, ev. insuficiente | estación +0,04 °C, ev. insuficiente | +0,1 °C | 0,80 |
| noaa_juigalpa_tavg | contraste | 2001–2024 | POWER/MERRA-2 +0,06 °C, ev. insuficiente | estación +0,21 °C, ev. insuficiente | +1,7 °C | 0,70 |
| noaa_tegucigalpa_tavg | contraste | 2001–2024 | POWER/MERRA-2 −0,06 °C, ev. insuficiente | estación −0,03 °C, ev. insuficiente | −0,6 °C | 0,55 |
| noaa_tegucigalpa_lluvia_vs_imerg_hnd | contraste | 2001–2024 | IMERG HND −41,2 mm, ev. insuficiente | GSOM: 5 años completos, sin tendencia | −788 mm | 0,77 (anual, n=5); 0,73 (mensual, n=150) |
| noaa_estaciones_nic_lluvia | contraste | 1981–1991 | POWER, no aplica | GSOM, no aplica | mediana −1 092 mm | mediana 0,22 |
| clorofila_golfo_fonseca | tendencia | 2003–2024 | Sen +0,68 mg m⁻³, **métodos discrepan** (MK p = 0,08) | OLS NTRS +1,21 mg m⁻³, p(F) = 0,0007 | — | — |
| clorofila_rio_coco | tendencia | 2003–2024 | +0,01, ev. insuficiente | OLS +0,05, p = 0,26 | — | — |
| clorofila_rio_grande_matagalpa | tendencia | 2003–2024 | +0,03, ev. insuficiente | OLS +0,04, p = 0,39 | — | — |
| clorofila_rio_escondido_bluefields | tendencia | 2003–2024 | +0,10, **métodos discrepan** (MK p = 0,07) | OLS +0,10, p = 0,13 | — | — |
| giovanni_imerg_caja_sicc | contraste | 2001–2024 | — | **bloqueado** | | |
| giovanni_imerg_nic | contraste | 2001–2024 | — | **bloqueado** | | |
| noaa_tegucigalpa_lluvia_vs_imerg_caja | contraste | 2001–2024 | — | **bloqueado** | | |
| airs_tas_nic | tendencia | 2003–2024 | — | **bloqueado** | | |
| omi_no2_managua | tendencia | 2005–2024 | — | **bloqueado** | | |

En la tabla, «ev. insuficiente» significa evidencia insuficiente. En todas las filas el veredicto robusto coincide con el del contrato.

## 3. Lluvia: caja SICC y Nicaragua frente a IMERG

### 3.1 Giovanni (IMERG, papel contraste): BLOQUEADO

Los datos de GES DISC están bloqueados. Esto afecta a Giovanni y también a la descarga de IMERG, AIRS y OMI.

- La causa es Earthdata Login: la aplicación «NASA GESDISC DATA ARCHIVE» (`client_id=e2WVk8Pw6weeLUKZYOxvTQ`) no está autorizada en la cuenta.
- URS responde *«Pre authorization required for this application»* y redirige (302) con `error=access_denied`.
- Giovanni deja constancia en su linaje: *«Giovanni now requires a login for data access»*. El flujo `ArAvTs` falla.
- El `.netrc` es válido: los metadatos de OPeNDAP responden 200. Esta autorización es también la causa del «401» anotado en `docs/modelos/REVISION_MODELOS_NICARAGUA.md` §7 b.
- **Para desbloquear**, el titular de la cuenta debe pulsar «Authorize» en <https://urs.earthdata.nasa.gov/approve_app?client_id=e2WVk8Pw6weeLUKZYOxvTQ>. Después basta con `python data/recursos/contraste/generar_contrastes.py giovanni resumen`.

**Token EDL.** No había ningún token EDL en el entorno ni en la cuenta. La API nueva (`api.giovanni.earthdata.nasa.gov`, Bearer) exige uno y no se creó: crear una clave en la cuenta requiere permiso del titular.

Peticiones registradas en `bloqueos.json` (12-11-2026):

- Caja: `https://giovanni.gsfc.nasa.gov/giovanni/daac-bin/service_manager.pl?service=ArAvTs&starttime=2001-01-01T00%3A00%3A00Z&endtime=2024-12-31T23%3A59%3A59Z&data=GPM_3IMERGM_07_precipitation&bbox=-86.5%2C10.7%2C-83.6%2C12.6&portal=GIOVANNI&format=json`
- País: la misma petición con `shape=state_dept_countries_2017%2Fshp_163`. En Giovanni, Nicaragua es `shp_163` y Honduras `shp_97` (catálogo `daac-bin/getProvisionedShapefiles.py`).

**Diferencias esperables cuando se ejecute.** Sirven para interpretar el resultado:

1. **Máscara.** Giovanni con `bbox` promedia las celdas cuyo centro cae en la caja. Nuestra caja pondera por la fracción exacta de cada celda de 0,1° dentro del rectángulo, así que solo cambia el borde: menos de 1 % del área.
   Con `shape` Giovanni usa el contorno del Departamento de Estado de EE. UU. (2017). Es un polígono de país que previsiblemente incluye los lagos Cocibolca y Xolotlán; hay que comprobarlo con el CSV. Nuestro NIC los resta. Sobre los lagos llueve menos que en la vertiente caribe, así que se espera una diferencia de unas decenas de mm/año.
2. **Ponderación.** Giovanni pondera por cos(latitud); nosotros, por el área de intersección en EPSG:6933. Entre 10,7 y 12,6° N el cos(lat) varía un 0,7 %. Según `clima.json` (`comprobacion_pesos_caja`), cambiar de pesos esféricos a pesos de igual área mueve el total anual de la caja como máximo 0,016 mm. La diferencia de ponderación es, por tanto, despreciable frente a la de máscara.
3. **Versión.** Ambas usan GPM_3IMERGM V07B. Si Giovanni sirviera aún V07A en algún mes, se vería como un salto.
4. **Unidades.** Giovanni devuelve la tasa media en mm/h. Se convierte con horas del mes × tasa (`giovanni.mensual_tasa_a_anual`), igual que en `clima.json`. Usar 730 h fijas o mm/día × 30 introduce errores de hasta un 3 % por mes.

### 3.2 KNMI Climate Explorer: BLOQUEADO

KNMI Climate Explorer (<https://climexp.knmi.nl/start.cgi>, 12-11-2026) pide al visitante «verify that I am human», un control antibots que no se automatiza. Python, además, rechaza su cadena de certificados.

Se usó la descarga directa equivalente de los mismos conjuntos que ofrece KNMI y se calculó la correlación en local.

### 3.3 CRU TS 4.10 (principal) y GPCC (secundario)

**CRU TS 4.10 (UEA)**

- Versión `cruts.2604091129.v4.10`, cobertura 1901–2025, consultada el 12-11-2026.
- URL: <https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/cruts.2604091129.v4.10/pre/>
- Diferencias con IMERG:
  - CRU tiene más lluvia: +209 mm/año en la caja y +210 en NIC, un 9 % aproximadamente.
  - La correlación es moderada: r = 0,71 en la caja y 0,63 en NIC.
  - Las pendientes de Sen son menos negativas: +7 y −21 mm/década, frente a −29 y −65 de IMERG.
  - **El veredicto coincide: evidencia insuficiente en los dos.**
- **Atención: menos estaciones desde 2015.** La variable `stn` de CRU muestra que las estaciones que influyen en cada celda bajan a la mitad desde 2015:
  - caja: de 4,3 (2001–2014) a 2,1 (2015–2024);
  - NIC: de 3,7 a 1,8.
  
  Con pocas estaciones, CRU vuelve hacia su climatología. Eso amortigua la variabilidad y lleva la pendiente hacia cero, y explica en parte por qué la r baja y por qué la pendiente de CRU es menos negativa. Por eso CRU sirve para contrastar el nivel y la sensibilidad a ENOS, no para refutar una tendencia.

**GPCC (copia de NOAA PSL)**

- URL: <https://psl.noaa.gov/thredds/dodsC/Datasets/gpcc/full_v2025/precip.mon.total.0.50x0.50.v2025.nc>
- Los atributos del archivo se contradicen:
  - `version = v2025`;
  - `title = "…Version 2018…"`;
  - `history = "Created 10/2026 based on V2022 data obtained via opendap"`.
- La serie llega hasta 2026-08, de modo que los últimos años son, con toda probabilidad, producto de monitoreo y no la reanálisis «Full».
- **No es independiente de IMERG**: IMERG Final se calibra mes a mes con el análisis de pluviómetros de GPCC. Eso explica r = 0,94 en NIC.
- Diferencias con IMERG:
  - caja: +127 mm, r = 0,81;
  - NIC: −47 mm, r = 0,94;
  - pendientes de Sen: −16 y −79 mm/década;
  - veredicto: evidencia insuficiente en los dos.

**Niño 3.4, junio a noviembre** (ONI medio jun–nov de `clima.json`, 24 temporadas, correlación descriptiva)

| región | IMERG | CRU | GPCC |
|---|---|---|---|
| caja | −0,59 | −0,46 | −0,57 |
| NIC | −0,56 | −0,47 | −0,64 |

Las tres fuentes dan el mismo signo y una magnitud parecida: los años de El Niño son más secos en la temporada de lluvias.

## 4. Estaciones NOAA (GSOM y GHCN-Daily, papel contraste)

### 4.1 Acceso

- **CDO v2 bloqueado por falta de token.** `NOAA_CDO_TOKEN` no existe en el entorno. La petición `https://www.ncei.noaa.gov/cdo-web/api/v2/stations?datasetid=GSOM&extent=10.7%2C-89.4%2C16.5%2C-83.1&limit=1000` responde **HTTP 400** (12-11-2026).
- **Vía alternativa sin token.** Se usaron el buscador y el Access Data Service v1 de NCEI, que sirven los mismos conjuntos (`global-summary-of-the-month` y `daily-summaries`).

Estaciones encontradas (bbox de Nicaragua y Honduras):

| id | nombre | GSOM | GHCN-Daily |
|---|---|---|---|
| NUM00078741 | Managua International | 1982–2003 | 1942–2025 |
| NU000069034 | Juigalpa | 1979–2002 | 1973–2025 |
| HO000078720 | Tegucigalpa | 1957–2025 | 1957–2025 |
| NU000055002 | Hacienda San Francisco | 1979–1991 | 1979–1991 |
| NU000055029 | Guasimón | 1979–1991 | 1979–1991 |
| NU000055016 | San Dionisio | 1979–1991 | 1979–1991 |

### 4.2 Qué sirve para 2001–2024

**Lluvia: las estaciones de Nicaragua terminan antes de 2001 y NO sirven para la tendencia de lluvia 2001–2024.**

- Sus últimos años completos son de 1989 a 1991.
- Los últimos meses con dato son octubre de 2003 en Managua y octubre de 2002 en Juigalpa. Entre 2001 y 2024 solo hay 6 y 2 meses de lluvia, respectivamente.

**Temperatura: una excepción que conviene corregir en las notas del proyecto.** GHCN-Daily sí trae temperatura media diaria (TAVG, de mensajes SYNOP) casi completa en 2001–2024 para Managua y Juigalpa: 23 años completos de 24. Se usó como contraste de temperatura, con dos cautelas:

- son series sin homogeneizar;
- un mes vale con al menos 20 días y un año, con los 12 meses.

### 4.3 Temperatura

Se compara con la celda de NASA POWER (MERRA-2) más cercana y con GISTEMP v4 (región NIC, anomalías).

**Managua** (celda a 18 km)

- r = 0,80 con POWER; 0,76 en 1981–2024.
- La estación está 0,1 °C más cálida.
- Tendencias: estación +0,04 °C/década, POWER +0,01. Las dos dan evidencia insuficiente.

**Juigalpa** (celda a 30 km)

- r = 0,70.
- La estación está 1,7 °C más cálida que la celda. La diferencia no se explica por la elevación (90 m frente a 131 m); probablemente es efecto del emplazamiento o del sesgo frío de MERRA-2 en el interior.
- Tendencias: +0,21 frente a +0,06 °C/década. Evidencia insuficiente (MK p = 0,10).

**Tegucigalpa** (la celda más cercana de la malla POWER del proyecto está a 37 km, a 933 m)

- r = 0,55.
- La estación está 0,6 °C más fría.
- Tendencias: −0,03 frente a −0,06 °C/década. Evidencia insuficiente.

**GISTEMP** (región NIC)

- Correlación de anomalías con las estaciones: r = 0,60 (Managua), 0,83 (Juigalpa) y 0,57 (Tegucigalpa).
- Pendiente 2001–2024: +0,40 °C/década, con **tendencia detectada**.
- Ni las estaciones ni la celda POWER detectan ese calentamiento en 24 años. La diferencia de pendiente entre estación y GISTEMP va de −0,19 a −0,43 °C/década.
- Hipótesis: GISTEMP usa GHCN mensual v4 **homogeneizado** y, con radio de 250 km, mezcla estaciones de países vecinos. El TAVG de GHCN-Daily es crudo, sin ajustes por cambios de instrumento o emplazamiento. Habría que revisarlo con AIRS (bloqueado, §5.2).

### 4.4 Lluvia de Tegucigalpa

**Frente a IMERG Honduras** (`clima.json`):

- Solo hay 5 años GSOM con los 12 meses, así que no se compara la tendencia.
- En los 150 meses comunes: r = 0,73 mensual y 0,57 en anomalías.
- La estación recibe el 55 % de la lluvia media nacional. Es un problema de representatividad (valle a 1 007 m, a sotavento), no un sesgo de IMERG.

**Frente a IMERG en una caja pequeña** (13,95–14,25° N; 87,35–87,05° O): bloqueado por Giovanni/GES DISC (§3.1).

### 4.5 Lluvia de las estaciones de Nicaragua en la década de 1980

Frente a la celda POWER más cercana:

- r va de 0,08 (Guasimón) a 0,38 (Hacienda San Francisco); mediana 0,22.
- Las estaciones de montaña reciben 700–1 800 mm más que la celda (Hacienda San Francisco, 790 m; Guasimón).

Es una validación débil, útil solo para mostrar que POWER suaviza la lluvia orográfica. No se usa para tendencias.

## 5. Variables nuevas (papel tendencia)

### 5.1 OMI NO₂ troposférico sobre Managua: BLOQUEADO

- Producto: OMNO2d v003, `ColumnAmountNO2TropCloudScreened` (fracción de nubes < 30 %), 2005–2024.
- **Caja urbana:** 12,05–12,20° N; 86,35–86,15° O.
  - Cubre el casco urbano, el aeropuerto internacional (12,14° N; 86,17° O) y la orilla sur del lago Xolotlán, al norte.
  - Con celdas de 0,25° toca 2 celdas, con centros en 12,125° N, 86,375° O y 86,125° O. La resolución de OMNO2d no permite una caja menor.
- **Caja rural de fondo:** 12,35–12,50° N; 85,10–84,90° O, en zona ganadera de Chontales.
  - Mismo tamaño y misma latitud.
  - Está a unos 130 km al este, sin ciudades grandes y fuera del eje Managua–Granada–Masaya.
  - La ubicación es una elección razonada, no un fondo validado: conviene revisar el mapa de NO₂ medio cuando se desbloquee.
- Bloqueado igual que §3.1. Las peticiones están en `bloqueos.json`.
- El OPeNDAP de la nube devuelve **403** («Failed to read the DMR++ from S3») y el de `acdisc` en sitio devuelve **410** (retirado). Por eso no hay vía alternativa con subconjuntos, y descargar los ~7 300 archivos diarios completos supondría decenas de GB.

### 5.2 AIRS, temperatura del aire en superficie: BLOQUEADO

- Producto: AIRS3STM v7, `SurfAirTemp_A` y `_D`, promedio de los nodos ascendente y descendente; Nicaragua con `shp_163`; 2003–2024.
- Comparación prevista con GISTEMP y MERRA-2 de `data/fenomenos/`: anomalías, r y diferencia de pendiente.
- Bloqueado igual que §3.1. Por OPeNDAP: 403 en la nube y 410 en `acdisc`.

### 5.3 Clorofila-a, MODIS-Aqua (OB.DAAC)

**Datos**

- Producto: `AQUA_MODIS.*.L3m.MO.CHL.chlor_a.4km.nc`, reprocesamiento R2022.0, consultado el 12 y 13-11-2026.
- Se descargaron los 264 archivos mensuales de 2003 a 2024 desde `oceandata.sci.gsfc.nasa.gov/getfile/` (58 MB cada uno). Cada archivo se recortó y se borró.
- Por qué no se usaron otras vías:
  - el OPeNDAP de OB.DAAC respondió 429;
  - ERDDAP `erdMH1chlamday` respondió 503;
  - el bucket de la nube exige aceptar las EULA de MERIS/Sentinel en el perfil.

**Promedio por caja**

- Igual que en Giovanni: media con peso cos(lat) de los píxeles válidos cuyo centro cae en la caja.
- Un mes vale si tiene al menos el 20 % del máximo de píxeles válidos de esa caja; las nubes vacían muchos meses en el Caribe.

**Cajas** (0,5° × 0,5°, del lado del mar)

| caja | límites |
|---|---|
| Río Coco | 14,75–15,25° N; 83,15–82,65° O |
| Río Grande de Matagalpa | 12,65–13,15° N; 83,5–83,0° O |
| Río Escondido / bahía de Bluefields | 11,75–12,25° N; 83,68–83,18° O |
| Golfo de Fonseca | 12,9–13,5° N; 87,9–87,3° O (incluye tierra, que es NaN) |

**SeaWiFS: no se usó.** Por eso no hay empalme con MODIS: no se validó el solape 2003–2010.

## 6. Artículo NTRS 20090042747 y su aplicación a la clorofila

### 6.1 Procedimiento del artículo

Acker, McMahon, Shen, Hearty y Casey, *Time-Series Analysis of Remotely-Sensed SeaWiFS Chlorophyll in River-Influenced Coastal Regions* (EARSeL eProceedings; NTRS 20090042747). Resumen hecho tras leer el PDF completo (27 páginas, descargado el 13-11-2026).

**Datos y cajas (sección Methods)**

- SeaWiFS L3 mensual (9 km, malla de igual área) de enero de 1998 a diciembre de 2007, a través de Giovanni.
- Diez zonas de nueve ríos: Amazonas, Congo, Eel, Ganges, Guadalquivir, Misisipi este y oeste, Orinoco, Perla y Po.
- Cada zona es una caja de 0,5° × 0,5° tan cerca de la boca como sea posible, **pero con clorofila media de toda la serie ≤ 1 mg m⁻³**. Así se reduce la influencia de la turbidez y del CDOM, que SeaWiFS no separa bien de la clorofila. Por eso algunas cajas quedan a cientos de kilómetros de la boca (el Congo, a 1 100 km).
- Giovanni promedia aritméticamente, sin ponderar, los valores de la caja.

**Prueba**

- Regresión lineal por mínimos cuadrados sobre la serie mensual completa, en Excel.
- Significancia por ANOVA: «significance F» < 0,05, es decir, nivel del 95 %. La prueba F evalúa el modelo lineal.
- El R² mide el ajuste. Son muy bajos (0,0006–0,079), y los autores lo atribuyen a la variabilidad entre meses y a episodios como crecidas.

**Desestacionalización**

Siguen a Gregg et al. (2005) en tres pasos:

1. restar a cada mes la media de su mes calendario;
2. promediar las anomalías de cada año;
3. aplicar una regresión a esas anomalías anuales.

**Regresión robusta y otros análisis**

- Por la sensibilidad a los valores atípicos, repiten el ajuste con regresión lineal robusta (ROBUST_LINEFIT de la biblioteca de astronomía de IDL). La pendiente robusta suele ser menor, sobre todo cuando hay episodios extremos al principio o al final (Misisipi oeste: −0,0043 → −0,0005).
- En el río Eel separan además la serie en invierno (noviembre–abril) y verano (mayo–octubre).

**Lo que no hace**

- No corrige la autocorrelación serial ni el ciclo estacional en la prueba F.
- No estima cuántos años hacen falta para detectar una tendencia.
- Los propios autores la presentan como una demostración sencilla con Excel.

**Resultados**

- Los ríos poco intervenidos (Amazonas, Congo, Orinoco) no dan tendencia significativa.
- Ganges y Misisipi este y oeste dan tendencias negativas significativas.
- El Eel da una positiva (p = 0,035).
- El Perla da +, aunque con p = 0,068.

### 6.2 Aplicación (`ntrs_clorofila` + `veredicto_serie`)

Se calcularon cuatro cosas:

1. OLS mensual cruda con F de ANOVA;
2. Theil–Sen mensual (la regresión robusta);
3. anomalías por mes calendario promediadas por año, exigiendo al menos 9 meses;
4. sobre esa serie anual desestacionalizada, nuestro veredicto: tres intervalos y Mann–Kendall modificado por autocorrelación.

| caja | OLS mensual (/década) | p(F) | R² | Theil–Sen mensual (IC 95 %) | Sen anual | MK p | veredicto nuestro | ¿coinciden? |
|---|---|---|---|---|---|---|---|---|
| Golfo de Fonseca | +1,21 | 0,0007 | 0,043 | +0,75 (0,32 a 1,17) | +0,68 | 0,08 | métodos discrepan | **No** |
| Río Coco | +0,05 | 0,26 | 0,005 | +0,01 (−0,04 a 0,06) | +0,01 | 0,78 | evidencia insuficiente | Sí |
| Río Grande de Matagalpa | +0,04 | 0,39 | 0,003 | +0,03 (−0,03 a 0,10) | +0,03 | 0,65 | evidencia insuficiente | Sí |
| Río Escondido / Bluefields | +0,10 | 0,13 | 0,009 | +0,07 (−0,02 a 0,17) | +0,10 | 0,07 | métodos discrepan | Sí, ninguno es significativo al 5 % |

Unidades: mg m⁻³ por década.

**Dónde coinciden.** En las tres desembocaduras caribeñas ningún método detecta una tendencia, y la OLS de Acker y nuestro Mann–Kendall coinciden.

**Dónde discrepan.** En el golfo de Fonseca, la OLS cruda declara una tendencia «significativa» (p = 0,0007), aunque explica solo el 4 % de la varianza. Theil–Sen mensual también excluye el cero. En cambio, al tratar la serie como 22 valores anuales y corregir la autocorrelación, Mann–Kendall da p = 0,08 y el veredicto queda en «métodos discrepan».

**Por qué.** La OLS sobre 264 meses trata como independientes meses que no lo son: autocorrelación y ciclo estacional. Eso infla los grados de libertad, que es justo la limitación que el artículo reconoce.

**Lectura.** Hay un indicio de aumento de la clorofila en Fonseca, pero con estos datos no llega a tendencia detectada.

**Criterio de ≤ 1 mg m⁻³ del artículo.** Media mensual de toda la serie en cada caja:

| caja | media (mg m⁻³) | ¿cumple? |
|---|---|---|
| Río Coco | 0,84 | sí |
| Río Grande de Matagalpa | 0,75 | sí |
| Río Escondido / Bluefields | 0,92 | sí |
| Golfo de Fonseca | 7,0 (mediana 5,9) | **no** |

La caja de Fonseca no cumple el criterio. Está dentro de aguas someras y turbias, donde el algoritmo OCx confunde sedimento y CDOM con clorofila. Su tendencia no debe leerse como eutrofización sin antes repetirla en una caja más afuera, en el Pacífico abierto, que cumpla el criterio.

**Otras diferencias de método con el artículo** (ninguna cambia la conclusión):

- usamos MODIS de 4 km y no SeaWiFS de 9 km;
- ponderamos por cos(lat), aunque en 0,5° la diferencia con la media aritmética es despreciable;
- como regresión robusta usamos Theil–Sen y no ROBUST_LINEFIT de IDL; las dos reducen el efecto de los valores atípicos.

## 7. Bloqueos

| clave | URL de la petición | código | fecha | motivo |
|---|---|---|---|---|
| giovanni_imerg_caja_sicc, giovanni_imerg_nic, giovanni_imerg_tegucigalpa, giovanni_airs_tas_a_nic, giovanni_airs_tas_d_nic, giovanni_omi_no2_managua, giovanni_omi_no2_rural | ver `bloqueos.json` (service_manager.pl, ArAvTs) | 302 → `access_denied` | 12-11-2026 | aplicación GES DISC sin autorizar en Earthdata (§3.1) |
| knmi_climate_explorer | <https://climexp.knmi.nl/start.cgi?id=someone@somewhere> | 200, página de verificación | 12-11-2026 | control «verify that I am human»; se usaron CRU y GPCC |
| noaa_cdo_v2 | <https://www.ncei.noaa.gov/cdo-web/api/v2/stations?datasetid=GSOM&extent=10.7%2C-89.4%2C16.5%2C-83.1&limit=1000> | 400 | 12-11-2026 | falta `NOAA_CDO_TOKEN`; se usó NCEI v1 |

## 8. Archivos

**Código**

- `backend/clima_nic/fuentes/giovanni.py`:
  - cliente de Giovanni (inicio de sesión OAuth, `service_manager`, sondeo, lector de CSV);
  - abridor Earthdata con Basic preventivo solo hacia URS;
  - parser DAP2 ASCII y promedio cos(lat);
  - conversión de mm/h a mm;
  - comparación con los métodos del backend.
- `backend/clima_nic/fuentes/noaa_cdo.py`: CDO v2 (token leído del entorno), buscador y Access Data Service v1 de NCEI, y parsers.
- `data/recursos/contraste/generar_contrastes.py`: pasos `noaa`, `knmi`, `cru`, `gpcc`, `giovanni`, `clorofila` y `resumen`.

**Datos** en `data/recursos/contraste/`:

- `resumen_contrastes.json`, `series_anuales.csv`, `bloqueos.json` y `consultas.json`;
- `lluvia_mensual_externa_{cru,gpcc}.csv` y `cru_estaciones_mensual.csv`;
- `clorofila_modis_mensual.csv`;
- `noaa/gsom_estaciones.csv`, `noaa/estaciones_mensual.csv` y `noaa/estaciones_ncei.csv`.

Los archivos crudos (CRU, GHCN-Daily y MODIS) quedan en `backend/.cache/contraste/`, fuera de git.

**Pruebas:** `tests/test_recursos_contraste.py`. Comprueban:

- la forma del resumen;
- que no haya secretos;
- que los veredictos y las pendientes coincidan con un recálculo desde los CSV;
- los parsers, sin red.

Ningún archivo contiene credenciales. El `.netrc` se lee en memoria y los tokens solo desde variables de entorno.
