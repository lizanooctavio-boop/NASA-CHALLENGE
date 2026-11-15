# Análisis geocientífico: tendencias climáticas de Nicaragua y sus impactos por región

Resumen de lo que usa el backend:

- **Pacífico.** ENOS domina la lluvia de junio–noviembre (r ≈ −0,56 con IMERG 2001–2024). La escorrentía del norte de Centroamérica muestra disminución desde ~1980 y se proyecta −10 a −30 % para 2050–2099 (Hidalgo et al., 2013, *J. Hydrol.* 495).
- **Central / Corredor Seco.** Canícula más tardía en CHIRPS 1981–2020 (Maurer et al., 2022, *HESS* 26) y más de una semana más larga a mitad de siglo en CMIP5 (Hidalgo y Alfaro, 2019). El resultado depende mucho de la definición: hay que fijarla y publicarla (aquí: `regiones[*].canicula.definicion`).
- **Caribe.** El riesgo dominante es por exceso de lluvia. Iota (2020) se intensificó 90 kt en 42 h (NHC). IPCC AR6: ciclones más intensos y menos frecuentes (confianza media).
- **País.** Días cálidos +2,5 %/década y noches cálidas +1,7 %/década en 1961–2003, significativos; lluvia total sin tendencia significativa; R95p +18,1 mm/década (Aguilar et al., 2005, *JGR* 110).
- **CLLJ** (chorro de bajo nivel del Caribe). Máximos en febrero y julio; índice = viento a 925 hPa en 12,5–17,5° N, 80–70° O (Maldonado et al., 2014). El Niño refuerza el CLLJ en verano. **PDO y AMO:** no hay cuantificación publicada para Nicaragua; se prueban como moduladores, no se asumen.
- **Lagos.** Cocibolca 32,91 m s. n. m. y Xolotlán 42,73 m en octubre de 2010 (INETER); fuertes descensos en 2014–2016. La altimetría (G-REALM, Hydroweb, desde 1992) y SWOT (desde 2023) permiten construir la serie.

## Cómo se aplicó en el backend

| Implicación | Dónde |
|---|---|
| Niño 3.4 como covariable obligatoria en tendencias de lluvia | `productos.analizar_variable`: toda variable de lluvia, sequía, canícula o humedad se ajusta con Niño 3.4 de junio–noviembre (`tendencia.controlada_por_indices`). Se aplica en todas las regiones, no solo Pacífico y Central. |
| Índice CLLJ desde MERRA-2 | `fuentes/merra2.py` (925 hPa exacto, requiere Earthdata) y `fuentes/power.py` (aproximación sin cuenta con U a 10 m en la misma caja). Entra como modulador. |
| PDO y AMO como moduladores, no supuestos | `fuentes/power.py` (índices desde la TSM de MERRA-2); `tendencia.controlada_por_todos_los_moduladores` y `correlacion_moduladores`. |
| Nivel de lagos | `fuentes/lagos.py` (G-REALM y SWOT). G-REALM respondió 503 al consultar y falta el identificador de cada lago: implementado con pruebas sintéticas, sin datos aún. |
| ETCCDI con las definiciones de Aguilar et al. (2005) | `estadistica/indicadores.py`: TX90p, TN90p, R95p, Rx1day, Rx5day, CDD, CWD, SDII, R10mm, R20mm con umbrales de la base 1991–2020 (Aguilar usó 1971–2000 y estaciones; para comparar cifras hay que tener en cuenta la base y que aquí son celdas de reanálisis). |
| Proyecciones solo como rangos por SSP | `proyecciones.py` y `escenarios_cmip6` en el JSON. |
