# Contrastes externos de las series del proyecto

Este documento corresponde al agente 2 (contrastes). Las cifras salen de `data/recursos/contraste/resumen_contrastes.json`, que genera
`data/recursos/contraste/generar_contrastes.py`. Las consultas y análisis se hicieron el 12 y el 13 de noviembre de 2026 (trabajo previo al evento del 14–15 de noviembre; ver §9).

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
| clorofila_pacifico_fonseca | tendencia | 2003–2024 | Sen −0,06 mg m⁻³, ev. insuficiente (MK p = 0,13) | OLS NTRS −0,08 mg m⁻³, p(F) = 0,017 | — | — |
| opendap_imerg_caja_sicc | contraste | 2001–2024 | IMERG −28,7 mm, ev. insuficiente | GES DISC OPeNDAP (GPM_3IMERGM 07) −28,7 mm, ev. insuficiente | −0,0 mm | 1,00 |
| opendap_imerg_nic | contraste | 2001–2024 | IMERG −64,9 mm, ev. insuficiente | GES DISC OPeNDAP (GPM_3IMERGM 07) −52,3 mm, ev. insuficiente | −25,0 mm | 0,999 |
| noaa_tegucigalpa_lluvia_vs_imerg_caja | contraste | 2001–2024 | IMERG caja (OPeNDAP) +6,7 mm, ev. insuficiente | GSOM: 5 años completos, sin tendencia | −481 mm | 0,75 (anual, n=5); 0,87 (mensual, n=150) |
| airs_tas_nic | tendencia | 2003–2024 | Sen +0,13 °C, tendencia detectada (MK p = 0,010; **señal frágil**) | OLS +0,14 °C, no sig. p(F) = 0,073; Sen mensual −0,01 a +0,25 | — | r = 0,92 (GISTEMP); 0,82 (POWER) |
| omi_no2_managua | tendencia | 2005–2024 | Sen −0,043 × 10¹⁵, **tendencia detectada** (MK p = 0,035) | OLS −0,049 × 10¹⁵, p(F) = 0,011 | — | — |
| omi_no2_rural | tendencia | 2005–2024 | Sen −0,049 × 10¹⁵, **métodos discrepan** (MK p = 0,056) | OLS −0,050 × 10¹⁵, p(F) = 0,009 | — | r = 0,37 (urbano/rural) |
| clorofila_rio_coco | tendencia | 2003–2024 | +0,01, ev. insuficiente | OLS +0,05, p = 0,26 | — | — |
| clorofila_rio_grande_matagalpa | tendencia | 2003–2024 | +0,03, ev. insuficiente | OLS +0,04, p = 0,39 | — | — |
| clorofila_rio_escondido_bluefields | tendencia | 2003–2024 | +0,10, **métodos discrepan** (MK p = 0,07) | OLS +0,10, p = 0,13 | — | — |

En la tabla, «ev. insuficiente» significa evidencia insuficiente. En todas las filas el veredicto robusto coincide con el del contrato.

## 3. Lluvia: caja SICC y Nicaragua frente a IMERG

### 3.1 GES DISC OPeNDAP (IMERG, papel contraste): RESUELTO

- **Fuente real y bloqueo de Giovanni (13-11-2026).** Tras autorizar la aplicación «NASA GESDISC DATA ARCHIVE» (`client_id=e2WVk8Pw6weeLUKZYOxvTQ`), `giovanni.iniciar_sesion()` y las descargas en OPeNDAP pasaron a responder **HTTP 200**. Sin embargo, Giovanni no entregó series: el endpoint web `service_manager.pl` (`ArAvTs`) quedó detenido en cola (*«Request pending: 40 requests ahead of you...»* > 10 min) y `api.giovanni.earthdata.nasa.gov` devolvió **HTTP 403** sin `EARTHDATA_TOKEN` en el entorno. En su lugar, las series de IMERG se extrajeron directamente de **GES DISC Hyrax Cloud OPeNDAP** (`opendap.earthdata.nasa.gov`, producto **`GPM_3IMERGM 07`**, 288 meses de 2001–2024, consulta `2026-11-13`).

**Resultados observados frente a `data/clima.json`:**

- **Caja SICC (`opendap_imerg_caja_sicc`):** `r = 1,000`, diferencia media **`−0,0001 mm/año`**, Sen `−28,7` frente a `−28,7 mm/década` (`diferencia_pendiente = 0,0`), ambos **evidencia insuficiente** (MK p = 0,785). Muestra que la diferencia entre pesos EPSG:6933 frente a `cos(lat)` y el recorte de borde es despreciable.
- **Nicaragua (`opendap_imerg_nic`):** `r = 0,999`, diferencia media **`−25,0 mm/año`**, Sen `−52,3` (GES DISC OPeNDAP, con lagos) frente a `−64,9 mm/década` (`clima.json` sin lagos), ambos **evidencia insuficiente** (MK p = 0,60 frente a 0,44). Concuerda con el efecto esperado de máscara: incluir los lagos Cocibolca y Xolotlán reduce la media anual del dominio nacional en torno a 25 mm/año sin cambiar el veredicto.

**Token EDL.** No había ningún token EDL en el entorno ni en la cuenta (`api.giovanni.earthdata.nasa.gov` respondió HTTP 403), por lo que se autenticó directamente contra GES DISC Hyrax Cloud OPeNDAP con la sesión Earthdata ya autorizada.

**Comparación de método (explica exactamente los resultados anteriores):**

1. **Máscara.** La extracción en GES DISC OPeNDAP para la caja `bbox` promedia las celdas cuyo centro cae en la caja; `data/clima.json` pondera por la fracción exacta de cada celda de 0,1° dentro del rectángulo, de modo que solo difiere en el borde (< 1 % del área; `−0,0001 mm/año`, `r = 1,000`).
   Para `NIC`, la serie en GES DISC OPeNDAP se extrajo con el contorno nacional del Departamento de Estado de EE. UU. (2017) e incluye los lagos Cocibolca y Xolotlán, mientras que `clima.json` los resta. El resultado comprobado con los CSV (`data/recursos/contraste/opendap/imerg_nic.csv`) es **con lagos: `−25,0 mm/año` y `r = 0,999`** (Sen `−52,3` frente a `−64,9 mm/década`).
2. **Ponderación.** En GES DISC OPeNDAP aplicamos ponderación por `cos(latitud)` por centro de celda; `clima.json` usa el área de intersección en EPSG:6933. Entre 10,7 y 12,6° N el `cos(lat)` varía un 0,7 %. Según `clima.json` (`comprobacion_pesos_caja`), cambiar de pesos esféricos a pesos de igual área mueve el total anual de la caja como máximo 0,016 mm, despreciable frente al efecto de máscara.
3. **Versión.** Ambas series usan `GPM_3IMERGM 07` (V07B).
4. **Unidades.** `GPM_3IMERGM 07` entrega la tasa media en mm/h (`precipitation`). Se convierte con horas del mes × tasa (`giovanni.mensual_tasa_a_anual`), igual que en `clima.json`. Usar 730 h fijas o mm/día × 30 introduciría errores de hasta un 3 % por mes.

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
- **Lectura matizada frente a AIRS (§5.2):** la tendencia de AIRS (2003–2024) es **frágil**: el veredicto anual da «tendencia detectada» (`+0,13 °C/década`, MK `p = 0,010`), pero la regresión mensual cruda da `p(F) = 0,073` (`+0,14 °C/década`, no significativa) y el IC 95 % de Theil–Sen mensual va de `−0,01` a `+0,25 °C/década`. AIRS coincide con GISTEMP en el signo y en la variabilidad interanual (`r = 0,92`), pero con una tasa de un tercio (`+0,13` frente a `+0,38 °C/década` en 2003–2024; más cerca de POWER `+0,22` y Juigalpa `+0,21`). Por tanto, **la magnitud de GISTEMP no queda respaldada**, y además deben considerarse limitaciones de estabilidad instrumental y deriva orbital de AIRS a largo plazo (§5.2).

### 4.4 Lluvia de Tegucigalpa

**Frente a IMERG Honduras** (`clima.json`):

- Solo hay 5 años GSOM con los 12 meses, así que no se compara la tendencia.
- En los 150 meses comunes: r = 0,73 mensual y 0,57 en anomalías.
- La estación recibe el 55 % de la lluvia media nacional. Es un problema de representatividad (valle a 1 007 m, a sotavento), no un sesgo de IMERG.

**Frente a IMERG en una caja pequeña** (13,95–14,25° N; 87,35–87,05° O; 2001–2024): completado vía OPeNDAP. En 150 meses comunes, `r = 0,87` mensual (`r = 0,74` en anomalías mensuales; `r = 0,75` anual en 5 años completos), superior al contraste contra todo Honduras (`0,73` y `0,57`). La estación recibe el **64 %** de la lluvia de su caja de 0,3° en GES DISC OPeNDAP (`GPM_3IMERGM 07`, `−481 mm/año`), resultado coherente con la diferencia de representatividad punto-celda y una posible sombra orográfica local en el valle de Tegucigalpa (Sen en la caja: `+6,7 mm/década`, evidencia insuficiente).

### 4.5 Lluvia de las estaciones de Nicaragua en la década de 1980

Frente a la celda POWER más cercana:

- r va de 0,08 (Guasimón) a 0,38 (Hacienda San Francisco); mediana 0,22.
- Las estaciones de montaña reciben 700–1 800 mm más que la celda (Hacienda San Francisco, 790 m; Guasimón).

Es una validación débil, útil solo para mostrar que POWER suaviza la lluvia orográfica. No se usa para tendencias.

## 5. Variables nuevas (papel tendencia)

### 5.1 OMI NO₂ troposférico urbano y rural (Managua y Chontales): GES DISC OPeNDAP

- Producto: **`OMNO2d 003`** (`ColumnAmountNO2TropCloudScreened`, fracción de nubes < 30 %), 2005–2024 (`240` meses, `7 282` gránulos diarios desde **GES DISC Hyrax Cloud OPeNDAP**, CMR `OMNO2d.003`, consulta `2026-11-13`).
- Como las cajas caen entre centros de celdas de 0,25°, se usó ponderación exacta por área de intersección (`regiones.pesos_malla`) sobre las dos celdas que cubre cada caja (`180,6 km²` cada celda):
  - **Caja urbana (Managua):** 12,05–12,20° N; 86,35–86,15° O (centros en 12,125° N; 86,375° y 86,125° O). Cubre el casco urbano, el aeropuerto internacional y la orilla sur del Xolotlán. `4 863` días válidos (mediana `20` días/mes), media `0,745 × 10¹⁵ molec cm⁻²`.
  - **Caja rural de fondo (Chontales):** 12,35–12,50° N; 85,10–84,90° O (centros en 12,375° N; 85,125° y 84,875° O), ~130 km al este en zona ganadera fuera del eje Managua–Granada–Masaya. `3 558` días válidos (mediana `15` días/mes), media `0,490 × 10¹⁵ molec cm⁻²`.
- **Tendencias 2005–2024:**
  - **Managua:** Theil–Sen anual `−0,043 × 10¹⁵ molec cm⁻²/década` (**tendencia detectada**, MK p = 0,035); OLS mensual `−0,049 × 10¹⁵` (p = 0,011). Ambos métodos coinciden.
  - **Chontales rural:** Theil–Sen anual `−0,049 × 10¹⁵ molec cm⁻²/década` (MK p = 0,056, **métodos discrepan**); OLS mensual `−0,050 × 10¹⁵` (p = 0,009).
- **Lectura del contraste urbano–rural:** Managua presenta en promedio **1,52×** más NO₂ troposférico que Chontales (`+0,255 × 10¹⁵ molec cm⁻²`, `r_anual = 0,37`), resultado coherente con una carga urbana más alta sobre Managua. Sin embargo, ambas cajas descienden casi al mismo ritmo (`~−0,04` a `−0,05 × 10¹⁵/década`), por lo que la pendiente negativa temporal no debe atribuirse únicamente a emisiones locales de Managua sin descartar deriva regional, cambios de nubosidad o la *row anomaly* de OMI.

### 5.2 AIRS, temperatura del aire en superficie: GES DISC OPeNDAP y tercera opinión

- Producto: **`AIRS3STM 7.0`** (`AIRS3STM v7`), promedio de los pasos ascendente (`SurfAirTemp_A`, ~13:30) y descendente (`SurfAirTemp_D`, ~01:30), ponderado por área sobre el polígono NIC sin lagos (`265` meses de 2002-12 a 2024-12 desde **GES DISC Hyrax Cloud OPeNDAP**, CMR `AIRS3STM.7.0`, consulta `2026-11-13`).
- **Tendencia frágil de AIRS sobre Nicaragua (2003–2024):** climatología `25,35 °C`. Sobre la serie anual (22 años), el veredicto es **«tendencia detectada»** (Theil–Sen `+0,13 °C/década`, `+0,1261`, MK `p = 0,010` —exacto `0,0095`—). Sin embargo, la tendencia se presenta como **frágil**: la regresión OLS sobre los meses da `p(F) = 0,073` (`+0,14 °C/década`, no significativa al 5 %) y el IC 95 % de Theil–Sen mensual abarca de `−0,01` a `+0,25 °C/década` (`+0,12 °C/década` puntual), cruzando el cero.
- **Tercera opinión en la discrepancia GISTEMP frente a POWER/estaciones (ventana común 2003–2024, 22 años):**
  - AIRS sigue de cerca las anomalías interanuales tanto de **GISTEMP** (`r = 0,92`) como de **NASA POWER/MERRA-2** (`r = 0,82`, con sesgo de POWER de `+0,53 °C`).
  - **Conclusión:** **AIRS coincide con GISTEMP en el signo y en la variabilidad interanual (`r = 0,92`), pero con una tasa de un tercio (`+0,13` frente a `+0,38 °C/década` en 2003–2024). La magnitud de GISTEMP no queda respaldada**, y la propia significancia de AIRS depende del paso a medias anuales (`MK p = 0,010` frente a OLS mensual `p(F) = 0,073` e IC mensual `−0,01` a `+0,25`). Queda como hipótesis abierta si el radio de interpolación de 250 km de GISTEMP amplifica la pendiente sobre Nicaragua.
- **Limitaciones de estabilidad instrumental y muestreo a largo plazo (documentación oficial AIRS v7):**
  - *Producto solo IR y nubosidad:* la guía del producto Level 3 v7 (Baijun Tian et al., JPL, abril de 2020, v1.0, §1.1 p. 3 y §5.1 p. 31) indica que `AIRS3STM` utiliza la recuperación solo infrarroja (*AIRS-Only*) para conservar la continuidad tras el fallo de `AMSU-A2` (24 de septiembre de 2016), con menor rendimiento en zonas muy nubosas, y falla cuando la nubosidad supera el 70 %.
  - *Estabilidad radiométrica frente a deriva orbital:* *Overview of the AIRS Mission* (Heidar Th. Thrastarson et al., 2.ª ed., JPL/GES DISC, 6 de mayo de 2021, p. 10 y §2 p. 7) documenta que la deriva de las radiancias de ventana a 1231 cm⁻¹ se estimó en `< 0,2–0,3 mK/década` en 2002–2019 (Aumann et al., 2019), pero señala que Aqua mantuvo la órbita nominal hasta finales de 2022 y comenzó entonces a derivar hacia horas locales más tardías, afectando al muestreo diurno al final del período (`2023–2024`).
  - *Maniobra DSM de 2021:* el informe técnico sobre la maniobra de espacio profundo del 23 de septiembre de 2021 (Tao Wang y Qing Yue, JPL, 10 de diciembre de 2025, §1, §5.2.2 pp. 3–5 y 22–23; §6 y §8 pp. 31–38) describe un desplazamiento del plano focal (~1 µm) que provocó sesgo frío y discontinuidades en `SurfAirTemp` en compilaciones previas `v7.0.7.0` (sobre todo en pasos descendentes sobre tierra tropical) hasta el reprocesamiento `v7.0.9.3`/`v7.0.10.0`. Aunque nuestros gránulos `AIRS3STM.7.0` de 2024 en CMR ya corresponden a `v7.0.9.3`, cualquier deriva orbital o ajuste posmaniobra debe tratarse como limitación al interpretar pendientes débiles (`~0,1 °C/década`).

### 5.3 Clorofila-a, MODIS-Aqua (OB.DAAC)

**Datos**

- Producto: `AQUA_MODIS.*.L3m.MO.CHL.chlor_a.4km.nc`, reprocesamiento R2022.0, consultado el 12 y 13-11-2026.
- Se descargaron los 264 archivos mensuales de 2003 a 2024 desde `oceandata.sci.gsfc.nasa.gov/getfile/` (58 MB cada uno). Cada archivo se recortó y se borró.
- Por qué no se usaron otras vías:
  - el OPeNDAP de OB.DAAC respondió 429;
  - ERDDAP `erdMH1chlamday` respondió 503;
  - el bucket de la nube exige aceptar las EULA de MERIS/Sentinel en el perfil.

**Promedio por caja**

- Con el mismo criterio espacial que en nuestra extracción OPeNDAP: media con peso cos(lat) de los píxeles válidos cuyo centro cae en la caja.
- Un mes vale si tiene al menos el 20 % del máximo de píxeles válidos de esa caja; las nubes vacían muchos meses en el Caribe.

**Cajas** (0,5° × 0,5°, del lado del mar)

| caja | límites |
|---|---|
| Río Coco | 14,75–15,25° N; 83,15–82,65° O |
| Río Grande de Matagalpa | 12,65–13,15° N; 83,5–83,0° O |
| Río Escondido / bahía de Bluefields | 11,75–12,25° N; 83,68–83,18° O |
| Golfo de Fonseca | 12,9–13,5° N; 87,9–87,3° O (incluye tierra, que es NaN) |
| Pacífico abierto frente a Fonseca | 12,20–12,70° N; 88,30–87,80° O (100 % mar abierto, 144/144 píxeles) |

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
| Pacífico abierto frente a Fonseca | −0,08 | 0,017 | 0,021 | −0,05 (−0,09 a −0,02) | −0,06 | 0,13 | evidencia insuficiente | **No** |
| Río Coco | +0,05 | 0,26 | 0,005 | +0,01 (−0,04 a 0,06) | +0,01 | 0,78 | evidencia insuficiente | Sí |
| Río Grande de Matagalpa | +0,04 | 0,39 | 0,003 | +0,03 (−0,03 a 0,10) | +0,03 | 0,65 | evidencia insuficiente | Sí |
| Río Escondido / Bluefields | +0,10 | 0,13 | 0,009 | +0,07 (−0,02 a 0,17) | +0,10 | 0,07 | métodos discrepan | Sí, ninguno es significativo al 5 % |

Unidades: mg m⁻³ por década.

**Dónde coinciden.** En las tres desembocaduras caribeñas ningún método detecta una tendencia, y la OLS de Acker y nuestro Mann–Kendall coinciden.

**Dónde discrepan.** En el golfo de Fonseca, la OLS cruda declara una tendencia «significativa» (p = 0,0007), aunque explica solo el 4 % de la varianza. Theil–Sen mensual también excluye el cero. En cambio, al tratar la serie como 22 valores anuales y corregir la autocorrelación, Mann–Kendall da p = 0,08 y el veredicto queda en «métodos discrepan».

**Por qué.** La OLS sobre 264 meses trata como independientes meses que no lo son: autocorrelación y ciclo estacional. Eso infla los grados de libertad, que es justo la limitación que el artículo reconoce.

**Lectura.** Hay un indicio de aumento de la señal aparente de clorofila dentro del golfo de Fonseca, pero al corregir autocorrelación no llega a tendencia detectada; y en mar abierto fuera del golfo la pendiente se vuelve ligeramente negativa y no significativa en análisis anual.

**Criterio de ≤ 1 mg m⁻³ del artículo.** Media mensual de toda la serie en cada caja:

| caja | media (mg m⁻³) | ¿cumple? |
|---|---|---|
| Río Coco | 0,84 | sí |
| Río Grande de Matagalpa | 0,75 | sí |
| Río Escondido / Bluefields | 0,92 | sí |
| Golfo de Fonseca | 7,02 (mediana 5,9) | **no** |
| Pacífico abierto frente a Fonseca | 0,44 | **sí** |

La caja dentro del golfo (`7,02 mg m⁻³`) incumple el criterio de Acker et al. al caer en aguas someras y turbias donde el algoritmo OCx confunde sedimento y CDOM con clorofila. Al repetir el experimento en mar abierto frente a Fonseca (`12,20–12,70° N; 88,30–87,80° O`, media **`0,44 mg m⁻³`**, cumple ≤ 1 mg m⁻³ en el 100 % de los 144 píxeles), no aparece ningún aumento: OLS mensual `−0,08 mg m⁻³/década` (p = 0,017) y Theil–Sen anual `−0,06 mg m⁻³/década` (`evidencia insuficiente`, MK p = 0,13). Ese contraste es coherente con que la señal positiva observada dentro del golfo se deba a turbidez y aporte estuarino, y no a eutrofización en aguas abiertas.

**Otras diferencias de método con el artículo** (ninguna cambia la conclusión):

- usamos MODIS de 4 km y no SeaWiFS de 9 km;
- ponderamos por cos(lat), aunque en 0,5° la diferencia con la media aritmética es despreciable;
- como regresión robusta usamos Theil–Sen y no ROBUST_LINEFIT de IDL; las dos reducen el efecto de los valores atípicos.

## 7. Bloqueos

| clave | URL de la petición | código | fecha | motivo |
|---|---|---|---|---|
| giovanni_imerg_*, giovanni_airs_tas_*, giovanni_omi_no2_* | ver `bloqueos.json` (`service_manager.pl`, `ArAvTs`) | 200 (en espera) | 13-11-2026 | cola detenida (`40 requests ahead of you`) / respuesta vacía de sesión → **datos reales obtenidos de `GES DISC OPeNDAP`** (claves `opendap_*` en `consultas.json`) |
| giovanni_api_token | <https://api.giovanni.earthdata.nasa.gov/timeseries> | 403 | 13-11-2026 | sin `EARTHDATA_TOKEN` Bearer en el entorno → **suplido con Hyrax OPeNDAP** |
| knmi_climate_explorer | <https://climexp.knmi.nl/start.cgi?id=someone@somewhere> | 200, página de verificación | 12-11-2026 | control «verify that I am human»; se usaron CRU y GPCC |
| noaa_cdo_v2 | <https://www.ncei.noaa.gov/cdo-web/api/v2/stations?datasetid=GSOM&extent=10.7%2C-89.4%2C16.5%2C-83.1&limit=1000> | 400 | 12-11-2026 | falta `NOAA_CDO_TOKEN`; se usó NCEI v1 |

## 8. Archivos

**Código**

- `backend/clima_nic/fuentes/giovanni.py`:
  - cliente de Giovanni (inicio de sesión OAuth, `service_manager`, sondeo, lector de CSV y API Bearer opcional);
  - abridor y cliente HTTP `httpx` Earthdata (`sesion_urs_http`) con Basic preventivo solo hacia URS;
  - consulta CMR y parsers DAP2 / Hyrax Cloud ASCII (`parsear_hyrax_ascii`, `opendap_hyrax_ascii`), y promedio cos(lat);
  - conversión de mm/h a mm;
  - comparación con los métodos del backend.
- `backend/clima_nic/fuentes/noaa_cdo.py`: CDO v2 (token leído del entorno), buscador y Access Data Service v1 de NCEI, y parsers.
- `data/recursos/contraste/generar_contrastes.py`: pasos `noaa`, `knmi`, `cru`, `gpcc`, `giovanni`, `opendap`, `clorofila` y `resumen`.

**Datos** en `data/recursos/contraste/`:

- `resumen_contrastes.json`, `series_anuales.csv`, `bloqueos.json` y `consultas.json`;
- `lluvia_mensual_externa_{cru,gpcc}.csv` y `cru_estaciones_mensual.csv`;
- `clorofila_modis_mensual.csv`;
- `opendap/{imerg_caja_sicc,imerg_nic,imerg_tegucigalpa,airs_tas_a_nic,airs_tas_d_nic,omi_no2_managua,omi_no2_rural}.csv`;
- `noaa/gsom_estaciones.csv`, `noaa/estaciones_mensual.csv` y `noaa/estaciones_ncei.csv`.

Los archivos crudos y cacheados por año (CRU, GHCN-Daily, MODIS y OMI diario) quedan en `backend/.cache/contraste/`, fuera de git.

**Pruebas:** `tests/test_recursos_contraste.py`. Comprueban:

- la forma del resumen;
- que no haya secretos;
- que los veredictos y las pendientes coincidan con un recálculo desde los CSV;
- los parsers, sin red.

Ningún archivo contiene credenciales. El `.netrc` se lee en memoria y los tokens solo desde variables de entorno.

## 9. Registro cronológico y declaración de uso de IA

- **12-11-2026 (antes del evento del 14–15 de noviembre):** descarga y análisis de CRU TS 4.10, GPCC, estaciones NOAA NCEI v1 (GSOM y GHCN-Daily) y primeros 147 meses de MODIS; registro de bloqueos iniciales de Giovanni/GES DISC, KNMI y CDO v2.
- **13-11-2026 ~02:00–03:45 CST (antes del evento del 14–15 de noviembre):**
  - finalización de MODIS-Aqua (`264` meses) y lectura íntegra del artículo NTRS 20090042747;
  - selección y descarga de la caja de control en Pacífico abierto frente al golfo de Fonseca (`pacifico_fonseca`, 264 meses, `0,44 mg m⁻³`);
  - rebase de la rama `codex/recursos-contraste` sobre `origin/codex/verificacion-entrega`;
  - tras la autorización Earthdata de `NASA GESDISC DATA ARCHIVE`, verificación de bloqueo por cola en `ArAvTs` / HTTP 403 sin `EARTHDATA_TOKEN` y extracción equivalente completa vía GES DISC Hyrax OPeNDAP de IMERG (`288` meses), AIRS (`265` meses) y OMI (`7 282` días, 2005–2024); regeneración íntegra de `resumen_contrastes.json` y `series_anuales.csv` con `20/20` entradas en estado `ok`.
- **13-11-2026 (cierre y revisión previa al evento del 14–15 de noviembre):**
  - declaración explícita de la fuente real (`GES DISC OPeNDAP`, nombres cortos/versiones `GPM_3IMERGM 07`, `AIRS3STM 7.0`, `OMNO2d 003` y fecha `2026-11-13`), renombre de la carpeta `giovanni/` → `opendap/` e ids `opendap_*`, conservando el motivo de bloqueo de Giovanni en `bloqueos.json`;
  - migración de `sesion_urs_requests` a `sesion_urs_http` con `httpx.Client` en `giovanni.py` y limpieza de `import os` en `generar_contrastes.py`;
  - matización de AIRS (señal frágil: MK `p = 0,010` frente a OLS `p(F) = 0,073` e IC mensual `−0,01` a `+0,25`; magnitud de GISTEMP no respaldada; limitaciones con documentación oficial JPL de AIRS v7) y de conclusiones de Tegucigalpa, OMI urbano y Fonseca;
  - regeneración reproducible de `resumen_contrastes.json` / `series_anuales.csv` y verificación en rama e integrada con `pytest` y `scripts/datos/verificar_clima.py`.
- **Uso de IA:** trabajo asistido por agentes de programación basados en LLM (Codex en la fase del 12–13-11 y Antigravity en la finalización del 13-11) para la escritura del código en `giovanni.py`, `generar_contrastes.py`, pruebas y documentación. Todas las cifras publicadas provienen exclusivamente de descargas directas reales y cálculos locales reproducibles verificados con `pytest`.

## Giovanni en la nube (recurso 1), 13-11-2026

Servicio oficial «Area-Averaged Time Series» de Giovanni a través de Harmony, siguiendo el cuaderno de GES DISC `How_To_Access_the_Giovanni_Averaging_Service_Using_Python.ipynb` (repositorio `nasa/gesdisc-tutorials`, abril de 2026). Paso: `python data/recursos/contraste/generar_contrastes.py nube`. Necesita `earthaccess` y `harmony-py` y una cuenta Earthdata en el `.netrc`; el token se pide en cada ejecución y no se guarda. Antes de pedir datos se consulta la cuota mensual (`https://api.giovanni.earthdata.nasa.gov/quota`). Los CSV quedan tal como los devuelve Giovanni en `data/recursos/contraste/giovanni/`, y el identificador del trabajo de Harmony queda en `consultas.json`.

El servicio solo promedia sobre cajas: al pedir el polígono de Nicaragua responde que la operación requiere `spatialSubset`. Por eso se usa la caja SICC, que en `data/dominios.geojson` es exactamente una caja.

| Contraste | Variable de Giovanni | Resultado |
|---|---|---|
| `giovanni_imerg_caja_sicc` | `GPM_3IMERGM_07_precipitation` | r = 1,000 y diferencia media de 0,0 mm/año: Giovanni reproduce la serie anual de `data/clima.json` en los 24 años. |
| `giovanni_gldas_sm0_10_caja_sicc` | `GLDAS_NOAH025_M_2_1_SoilMoi0_10cm_inst` (kg m⁻² / 100 = m³/m³) | r = 1,000 tras corregir los meses repetidos de la serie OPeNDAP (ver `tierra.md`). Antes de la corrección daba r = 0,714. |

Este contraste detectó que el OPeNDAP en la nube había servido otro granulo para 14 meses de 2001–2003. Así, el recurso 1 cumple dos papeles: confirma con la herramienta oficial de NASA las cifras que muestra la aplicación y sirvió de control de calidad.
