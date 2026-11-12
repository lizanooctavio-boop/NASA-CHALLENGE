# Revisión y mejora de los modelos climáticos de Nicaragua (solo datos NASA)

**Fecha:** 12 de noviembre de 2026 · **Rama:** `codex/modelos-climaticos-nicaragua` (desde `codex/datos-climaticos`) · **Estado:** exploratorio.
Requisitos del reto en [`docs/reto/REQUISITOS_NASA.md`](../reto/REQUISITOS_NASA.md); matriz de cumplimiento en [`docs/reto/CUMPLIMIENTO.md`](../reto/CUMPLIMIENTO.md); contexto científico en [`ANALISIS_GEOCIENTIFICO.md`](ANALISIS_GEOCIENTIFICO.md). Código en [`backend/`](../../backend/README.md); resultados completos en `data/fenomenos_nicaragua.json`.

## 1. Punto de partida

El pipeline de `codex/datos-climaticos` (contrato 1.0.0) analiza la lluvia anual IMERG Final V07B 2001–2024 en cinco dominios, con mínimos cuadrados, HAC y Theil–Sen. Nicaragua: −62 mm/década, IC 95 % de −211 a +86, sin tendencia detectada. ENOS: r ≈ −0,56 en junio–noviembre (descriptivo). No había temperatura, extremos, sequía, canícula, regiones internas ni predicción. El índice ENOS era el ONI de NOAA.

**Nada de eso se modificó**: `clima.json`, sus cifras de referencia y `verificar_clima.py` siguen igual (88/88 comprobaciones). Todo lo nuevo son archivos opcionales (contrato 1.1.0, §9).

## 2. Matriz dataset NASA → fenómeno

| Fenómeno | Dataset NASA | Resolución | Período | Acceso | Estado en esta corrida |
|---|---|---|---|---|---|
| Lluvia (referencia) | GPM IMERG Final V07 mensual | 0,1° · mensual | 1998-01 → (V07B; 324 gránulos 1998–2024 en CMR) | Earthdata | 2001–2024 en uso; 1998–2000 implementado, sin credenciales |
| Lluvia diaria, extremos | MERRA-2 PRECTOTCORR vía NASA POWER | 0,5° × 0,625° · diaria | 1981 → | sin cuenta | en uso, **con inhomogeneidad** (ver §4.1) |
| Temperatura media, máx., mín. | MERRA-2 T2M, T2M_MAX, T2M_MIN vía POWER | 0,5° × 0,625° · diaria | 1981 → | sin cuenta | en uso, **tendencia no fiable** (§4.2) |
| Temperatura observada | GISTEMP v4 (250 km) | 2° · mensual | 1880 → | sin cuenta | en uso 1981–2024 |
| Humedad del aire, radiación, viento | POWER RH2M, ALLSKY_SFC_SW_DWN (CERES/SRB), WS2M | 0,5° × 0,625° · diaria | 1981 → (radiación 1984 →) | sin cuenta | en uso |
| ETo, balance hídrico | Derivado: FAO-56 Penman–Monteith y Hargreaves | igual | 1984 → / 1981 → | — | en uso |
| Sequía (SPI, SPEI) | Derivado de lluvia y temperatura de POWER | igual | 1981 → | — | en uso |
| Canícula | Derivado de lluvia diaria de POWER | igual | 1981 → | — | en uso (definición fija y publicada) |
| Humedad del suelo (modelo) | MERRA-2 GWETROOT, GWETTOP | igual | 1981 → | sin cuenta | en uso |
| Humedad del suelo (satélite) | SMAP L4 SPL4SMGP | 9 km · 3 h | 2015-03 → | Earthdata | implementado, sin credenciales |
| Almacenamiento de agua | GRACE/GRACE-FO JPL mascons RL06.3 | 0,5° (efectiva ~3°) · mensual | 2002-04 → (hueco 2017–18) | Earthdata | implementado, sin credenciales |
| Vegetación | MODIS MOD13Q1 NDVI (ORNL DAAC) | 250 m · 16 días; 1 sitio de 3 × 3 km por región | 2000-02 → | sin cuenta | en uso (subconjunto) |
| Temperatura de superficie | MODIS MOD11A2 LST | 1 km · 8 días | 2000 → | sin cuenta | implementado, no descargado |
| ENOS (Niño 3.4) | TS de MERRA-2 sobre el mar vía POWER | 0,5° × 0,625° · mensual | 1981 → | sin cuenta | en uso; **sustituye al ONI de NOAA** |
| Atlántico (TNA, AMO), PDO | TS de MERRA-2 sobre el mar vía POWER (máscara de tierra Natural Earth) | igual | 1981 → | sin cuenta | en uso como moduladores |
| CLLJ | U a 10 m (POWER, aproximación) / U a 925 hPa (MERRA-2 M2IMNPASM) | igual | 1981 → / 1980 → | sin cuenta / Earthdata | aproximación en uso |
| Nivel de lagos | G-REALM (altimetría), SWOT | por lago | 1992 → / 2023 → | abierto / Earthdata | implementado, sin datos (G-REALM 503) |
| Ciclones tropicales | — | — | — | — | **no cubierto**: NASA no publica trayectorias; se ven solo por Rx1day/Rx5day |
| Escenarios futuros | NEX-GDDP-CMIP6 v2.0 (6 modelos) | 0,25° · diaria | 1950–2100 | sin cuenta (NCCS THREDDS) | en uso: histórico 1995–2014, SSP2-4.5 y SSP5-8.5 2041–2060 |
| Límites | Natural Earth (no NASA) | 1:50 m y 10 m | — | dominio público | en uso; SEDAC GPWv4 requeriría Earthdata y cambiaría las cifras del contrato |

Regiones: `NIC`, `pacifico` (18 190 km²), `central` (36 104 km², con el Corredor Seco del norte y centro), `caribe` (65 588 km²) y `caja_sicc`; las tres regiones suman exactamente la máscara NIC (`data/regiones_nicaragua.geojson`).

## 3. Qué cambió

1. **Fuentes 100 % NASA y registro más largo.** Niño 3.4 calculado con la TSM de MERRA-2 (r = 0,991 con el ONI de NOAA en 288 meses; RMSE 0,11 °C; misma categoría El Niño/La Niña/neutral en el 92 % de los meses). El ONI de NOAA queda solo como validación. Serie diaria 1981–2024 (44 años) de MERRA-2 vía POWER; IMERG desde 1998 listo para cuando haya cuenta Earthdata.
2. **Fenómenos.** 40 variables por región: lluvia, ETCCDI de lluvia (Rx1day, Rx5day, R95p, R10mm, R20mm, SDII, CDD, CWD, veranillos) y de calor (TX90p, TN90p, TXx, TNn, DTR), SPI/SPEI a 3, 6 y 12 meses, canícula (inicio, fin, duración, intensidad, déficit; objetiva y de ventana fija), ETo Penman–Monteith, balance P − ETo, grados-día, humedad, radiación, viento, humedad del suelo y NDVI.
3. **Tendencias robustas.** Sen con IC 95 %, Mann–Kendall modificado (Hamed y Rao), Pettitt, regresión con Niño 3.4 como covariable obligatoria en toda variable de lluvia (y TNA, AMO, PDO y CLLJ como moduladores), FDR (Benjamini–Hochberg, q = 0,10) en los mapas por celda, y **contraste obligatorio con una fuente independiente** (IMERG para lluvia, GISTEMP para temperatura) con advertencia automática cuando no coinciden.
4. **Predicción, separada de la detección.** Estacional 0–6 meses validado fuera de muestra (dejando 1 y 3 años fuera, MSESS frente a la climatología, permutaciones y FDR sobre 280 combinaciones); escenarios CMIP6 como rangos con corrección delta; nunca un año futuro como cifra determinista.
5. **Retroalimentación y API.** `python -m clima_nic actualizar` reingesta, recalibra y agrega la habilidad a `data/historial/`; consulta por CLI o FastAPI.

## 4. Resultados

### 4.1 Lluvia: el reanálisis no sirve para tendencias

| Región | MERRA-2 (POWER) 1981–2024, Sen mm/década [IC 95 %] | IMERG 2001–2024 | MERRA-2 en la misma ventana 2001–2024 |
|---|---|---|---|
| NIC | +329 [+231; +409], «detectada» | **−65 [−233; +98], evidencia insuficiente** | +313 [+55; +512] |
| Caja SICC | +361 [+253; +484] | −29 [−184; +189] | +304 [−26; +673] |

La lluvia de MERRA-2 tiene un salto (Pettitt 1998–2005, varias desviaciones típicas) y un sesgo seco del 22 % frente a IMERG. En los mismos años, IMERG no detecta tendencia; la correlación interanual entre ambos es solo 0,63. **Conclusión: las «tendencias» de lluvia, extremos de lluvia, SPEI, balance hídrico y humedad del suelo de MERRA-2 son en gran parte artificiales.** En el JSON llevan advertencias y no deben mostrarse como cambio climático. La conclusión vigente sobre lluvia es la de IMERG: con 24 años no se detecta tendencia (coincide con Aguilar et al., 2005, para 1961–2003).

### 4.2 Temperatura: calentamiento observado claro; MERRA-2 lo contradice

| Región | GISTEMP 1981–2024, °C/década [IC 95 %] | Con control por ENOS | Veredicto | MERRA-2 T2M |
|---|---|---|---|---|
| NIC | **+0,29 [+0,22; +0,37]** | +0,22 a +0,32 | tendencia detectada | −0,11 [−0,25; +0,04] |
| Pacífico | +0,30 [+0,22; +0,37] | +0,22 a +0,32 | tendencia detectada | −0,14 |
| Central | +0,29 [+0,21; +0,37] | +0,22 a +0,32 | tendencia detectada | −0,19 |
| Caribe | +0,29 [+0,22; +0,37] | +0,22 a +0,32 | tendencia detectada | −0,05 |

Los cuatro métodos coinciden con GISTEMP. Es una celda de 2° con radio de 250 km, así que las cuatro regiones comparten casi las mismas estaciones y **no son resultados independientes**. Las tendencias negativas de MERRA-2 en Tmax (−0,37 a −0,54 °C/década) y en TX90p son incompatibles con la observación y con Aguilar et al. (2005; +2,5 %/década de días cálidos). Se marcan como no fiables. Las noches cálidas (TN90p) suben en la caja SICC (+1,9 %/década, detectada) y en el Caribe (+1,6 %/década, los métodos discrepan), en la dirección que encontró Aguilar et al. (2005).

### 4.3 Canícula (definición publicada en `regiones[*].canicula.definicion`)

Se detecta en 44/44 años en Pacífico y Central y en 42/44 en el Caribe. Duración mediana: 64 días en el Pacífico, 62 en Central y 46 en el Caribe. Inicio mediano: día 175 (24 de junio). Tendencias 1981–2024: duración +3 días/década en el Pacífico y en Central (no significativa); +11 días/década en la caja SICC y +8 en NIC (detectada), con inicio más temprano (−5 a −6 días/década). Como depende de la lluvia de MERRA-2, es **exploratorio**: Maurer et al. (2022) encuentran con CHIRPS un retraso, no un adelanto. Hay que repetirlo con IMERG diario antes de afirmarlo.

### 4.4 Otros

- **NDVI (MODIS, un sitio por región):** Central (Estelí) −0,043/década [−0,054; −0,031], detectada; Pacífico y Caribe sin tendencia. Un solo sitio y posible cambio de uso del suelo: es un indicio, no un resultado regional.
- **Grados-día y radiación:** sin tendencia detectable (con el mismo problema de temperatura de MERRA-2).
- **Mapas (57 celdas):** con FDR, todas las celdas «significativas» en lluvia total y R95p. Es otra manifestación del salto de MERRA-2, no 57 detecciones independientes.

### 4.5 Pronóstico estacional (lluvia de junio–noviembre con índices de marzo–mayo, validación dejando un año fuera)

| Región | Solo Niño 3.4 MAM | Niño 3.4 + TNA MAM | Ídem sin tendencia | Solo tendencia lineal |
|---|---|---|---|---|
| NIC (MERRA-2, n = 44) | MSESS −0,05 (p 0,78) | +0,35 (p 0,001) | +0,25 (p 0,002) | +0,51 |
| Pacífico | −0,05 | +0,36 | +0,27 | +0,51 |
| Central | −0,06 | +0,37 | +0,28 | +0,51 |
| Caribe | −0,04 | +0,31 | +0,18 | +0,47 |
| **NIC (IMERG, n = 24)** | **−0,10 (p 0,79)** | **+0,10 (p 0,051)** | — | — |
| Caja SICC (IMERG) | −0,15 | +0,18 (p 0,02) | — | — |

Lectura honesta:
- **El Niño 3.4 de primavera no anticipa la lluvia de junio–noviembre** (MSESS < 0 en todas las regiones; barrera de predictibilidad de primavera). La correlación de r ≈ −0,56 es con el ENOS **simultáneo**, que no se conoce a inicios de junio. En la grilla de 0–6 meses con solo Niño 3.4, ninguna combinación es hábil tras FDR.
- Añadir el **Atlántico Norte tropical** sí da habilidad: con IMERG, MSESS +0,10 a +0,18 (≈ 10–18 % menos error que la climatología; aciertos de tercil 42–46 % frente a 33 % por azar), en el límite de la significancia.
- Con MERRA-2 la habilidad parece mayor, pero la tendencia lineal sola le gana. Su habilidad está inflada por la tendencia artificial que comparten la lluvia y el TNA; sin tendencia baja a +0,18 a +0,28.
- Útil como pronóstico probabilístico de terciles para orientar, no como cifra.

### 4.6 Escenarios CMIP6 (NEX-GDDP, 6 modelos, 2041–2060 frente a 1995–2014, corrección delta)

| Región | Lluvia anual SSP2-4.5 (mín. / mediana / máx.) | SSP5-8.5 | Jul–ago (canícula) SSP5-8.5 | Temperatura SSP2-4.5 | SSP5-8.5 |
|---|---|---|---|---|---|
| NIC | −12 / −5 / −3 % | −18 / −10 / −2 % | −22 / −16 / −5 % | +1,1 / +1,4 / +1,7 °C | +1,3 / +2,0 / +2,1 °C |
| Pacífico | −12 / −2 / +1 % | −18 / −7 / +7 % | −30 / −23 / +2 % | +1,1 / +1,4 / +1,8 °C | +1,3 / +2,0 / +2,2 °C |
| Central | −13 / −9 / −4 % | −18 / −13 / −8 % | −28 / −21 / −16 % | +1,2 / +1,5 / +1,8 °C | +1,4 / +2,1 / +2,3 °C |
| Caribe | −12 / −4 / −3 % | −18 / −10 / −1 % | −21 / −14 / 0 % | +1,0 / +1,3 / +1,7 °C | +1,2 / +1,9 / +2,0 °C |

Los seis modelos coinciden en un calentamiento de 1,0–2,3 °C y casi todos en menos lluvia, sobre todo en julio–agosto en la región Central (los seis secan entre −16 y −28 % con SSP5-8.5). Esto coincide con el alargamiento proyectado de la canícula (Hidalgo y Alfaro, 2019) y con la reducción de escorrentía (Hidalgo et al., 2013). **Son rangos de escenarios para promedios de 20 años, no pronósticos.** Seis modelos subestiman la incertidumbre del conjunto de 35.

## 5. Ejemplos de demostración para la interfaz

1. «¿Se está calentando el Pacífico?» → `GET /consulta?region=pacifico&variable=temperatura_gistemp` → +0,30 °C/década, significativo, con definición y serie.
2. «¿Llueve menos en Nicaragua?» → `lluvia_anual_imerg` en NIC → −65 mm/década, evidencia insuficiente. Muestra el contraste con `lluvia_anual` de MERRA-2 y su advertencia: un buen caso para enseñar a desconfiar de un solo producto.
3. «¿Cómo vendrá la estación lluviosa?» → `GET /pronostico?region=NIC&anio=2015&variable=lluvia_jun_nov_imerg` (retrospectivo, el año se excluye del ajuste) → esperado 1413 mm, intervalo del 80 % de 1179 a 1605, 65 % de probabilidad de tercil bajo; observado 1298 mm (año de El Niño). Contraejemplo honesto: 2023 sale «alto» (48 %) y fue bajo, porque El Niño se formó después de marzo–mayo. Para años sin Niño 3.4/TNA de marzo–mayo responde «aún no disponible». En regiones sin IMERG (Pacífico, Central, Caribe) el modelo usa MERRA-2 sin tendencia sobre el nivel de los últimos 15 años y lo indica en `producto`.
4. «¿Qué esperan los modelos para 2050?» → `GET /escenarios?region=central&variable=canicula_lluvia_15jul_15ago` → rango por SSP con la leyenda «no es un pronóstico».

## 6. Límites honestos

- **Registros cortos:** 24 años de IMERG y 44 de MERRA-2. Una tendencia de 2–4 décadas puede ser variabilidad decadal (AMO/PDO), que aquí solo se prueba como modulador.
- **ENOS domina la variabilidad interanual** y no se puede anticipar desde la primavera. Lo que sí se puede decir de una temporada es una inclinación de probabilidades, no su total.
- **Inhomogeneidad del reanálisis:** la lluvia y la temperatura de MERRA-2 tienen saltos. Toda tendencia de MERRA-2 sin confirmación independiente es sospechosa; por eso el backend contrasta y advierte automáticamente.
- **Multiplicidad:** se prueban cientos de series; algunas detecciones serán falsos positivos (FDR en mapas y en la grilla estacional, no entre variables).
- **No se puede predecir:** la lluvia de un año concreto a más de una estación; la trayectoria o el número de ciclones; eventos extremos individuales; impactos (cosechas, caudales) sin modelos específicos; el clima de un año concreto de 2050.
- **Cobertura:** ciclones sin datos NASA de trayectorias; lagos sin serie todavía; NDVI de un sitio por región; la región Central agrupa departamentos y no coincide con el Corredor Seco oficial definido por municipios.

## 7. Pendiente

1. **Cuenta Earthdata** (gratuita) y un `.netrc` en este equipo: con eso se activan IMERG 1998–2000 y diario (extremos y canícula a 0,1°, lo más urgente dado §4.1), CLLJ a 925 hPa, SMAP y GRACE-FO. Comando: `python -m clima_nic fuentes` para comprobar.
2. Rehacer extremos, SPEI, canícula y el pronóstico por región con IMERG diario/mensual y reemplazar las versiones de MERRA-2.
3. Nivel de lagos: obtener los identificadores de Cocibolca/Xolotlán en G-REALM (cuando responda) o en la PLD de SWOT.
4. Ampliar CMIP6 a más modelos y a 2081–2100; agregar Tmax/Tmin y lluvia diaria para extremos futuros.
5. Revisar la pestaña Resources del reto (13-11-2026) y añadir las fuentes que liste.
6. Que la interfaz (PR #2) decida si consume `fenomenos_nicaragua.json` o la API; no se tocó.

## 8. Reproducir

```text
cd backend
python -m clima_nic productos            # sin red, desde data/fenomenos/ (≈ 30 s)
python -m pytest ../tests -q
python ../scripts/datos/verificar_clima.py
```
