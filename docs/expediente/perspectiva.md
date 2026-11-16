# Expediente por área: perspectiva climática de la próxima década

Segundo bloque del informe de **Area report**. El primer bloque (análisis histórico) no cambia. El segundo estima
la década que empieza el año siguiente a la generación del informe. Para un informe generado en 2026, esa década es 2027–2036.
Código: `src/expediente/perspectiva.js` (módulo `ETDPerspectiva`, versión `perspectiva-1.0.0`). Pruebas: `tests/test_perspectiva.py`.

## Qué es y qué no es

El bloque separa tres modalidades que no son equivalentes:

1. **Extrapolación estadística.** Es la que se calcula aquí. Cuatro modelos se ajustan a la serie observada del área. Cada uno se valida fuera de muestra y se elige el de menor error decenal.
2. **Proyección climática.** NEX-GDDP-CMIP6 para la región de Nicaragua que contiene el centro del área. Usa 6 modelos y los escenarios SSP2-4.5 y SSP5-8.5. Es un contraste físico condicionado al escenario. No es un pronóstico.
3. **Predicción decenal inicializada.** No se usa: la app no dispone de predicciones DCPP.

Nada se presenta como pronóstico de años concretos.

## Fechas

- Generación: el año de `generado_utc`. La década va del año siguiente al décimo año siguiente.
- El último año completo y la anticipación se calculan **por indicador**. La anticipación es el número de años entre el último año completo y el primer año de la década.
- La validación usa exactamente esa misma anticipación.

## Indicadores evaluados

| Indicador | Fuente | Escala |
|---|---|---|
| Variable y temporada de la consulta | NASA POWER mensual (MERRA-2), la misma serie del bloque 1 | área |
| Tmax, Tmin y T2M medias; TX90p y TN90p | Índices anuales por celda de NASA POWER diario (`data/fenomenos/indices_anuales_celdas.csv`), ponderados por la intersección | área |
| PRCPTOT, Rx1day, Rx5day, R95p y CDD | Mismo archivo | área |
| Anomalía GISTEMP v4 | `data/fenomenos/gistemp_nicaragua.csv`, de estaciones interpoladas a 250 km (observación independiente) | región |

La malla de índices cubre solo Nicaragua. Si cubre menos del 90 % del área, estos índices no se evalúan y el motivo aparece en la lista de variables excluidas.
Las variables que esta versión no proyecta se listan siempre con su motivo, para evitar sesgo de selección: olas de calor, SPI/SPEI, TSM, nivel del mar, lagos, vegetación, canícula y huracanes.

## Diagnóstico histórico

- **Tendencia.** Pendiente de Sen con IC 95 % y Mann-Kendall modificado por autocorrelación (Hamed y Rao, 1998); el factor de varianza se acota a ≥ 1. También se informan la pendiente MCO y la autocorrelación de los residuos.
- **Sensibilidad.** Se repite el cálculo con tres periodos fijados de antemano: desde 1981, desde 1991 y desde 2001.
- **Comparaciones múltiples.** La familia de hipótesis es una prueba por indicador evaluado en el área. Se informan los valores p y los valores q de Benjamini-Hochberg.
- **Calidad de datos.** Años válidos, faltantes y duplicados. Un año sin datos queda vacío; nunca se rellena.

## Modelos y validación

**Modelos:**

- Climatología: media de los últimos 30 años.
- Persistencia: media de los últimos 10 años, con ruido AR(1).
- Tendencia lineal con errores AR(1).
- Tendencia amortiguada ETS(A,Ad,N), con una rejilla de parámetros fija.

En el modelo de tendencia, la incertidumbre de los parámetros se infla por la autocorrelación (factor (1+φ)/(1−φ)). El φ de los residuos se corrige por su sesgo en series cortas y se propaga su incertidumbre. La varianza se extrae de una χ² con n−3 grados de libertad. Con series simuladas de 20 a 40 años que siguen exactamente ese modelo, la cobertura de los intervalos del 80 % y el 95 % queda entre 0,77 y 0,85 y entre 0,90 y 0,97.

**Validación retrospectiva con origen móvil.** Se entrena solo con los años anteriores a cada origen (al menos 20). Se pronostica la media de la década siguiente con la misma anticipación que la proyección real. Para cada modelo se informan:

- MAE, RMSE y sesgo de la media decenal;
- MAE y RMSE anuales;
- MSSS (habilidad) frente a la climatología;
- cobertura y anchura de los intervalos del 80 % y del 95 %.

Las ventanas se solapan, así que se informa también cuántas décadas independientes hay (unas 2 con datos de 1981–2024).
Se elige el modelo con menor RMSE decenal fuera de muestra. Si hay un empate de hasta el 2 %, se elige el más simple. La pendiente y el ajuste dentro de la muestra nunca se usan para elegir.

## Cantidades proyectadas

Se simulan 2000 trayectorias con semilla fija (mulberry32 y Box-Muller). Con ellas se calculan:

- el cambio de la media decenal frente a la referencia (1991–2020 por defecto) y frente a la última década observada;
- la pendiente dentro de la década;
- la probabilidad de detectar la tendencia en esos 10 años (potencia);
- la probabilidad de aumento.

Se distinguen tres tipos de intervalo:

- **Predictivo (80 % y 95 %).** Cubre la media decenal que se observará.
- **De confianza de la respuesta media.** Es el contraste del propio modelo entre la década y la referencia. En la tendencia amortiguada no está definido, y se usa el predictivo.
- **Dispersión entre modelos CMIP6.** Mínimo, mediana y máximo. No es un intervalo de confianza.

Las trayectorias se recortan a los límites físicos: los porcentajes de días entre 0 y 100, y la lluvia y los días no negativos.
Las frecuencias solo se leen como probabilidades cuando la validación muestra intervalos calibrados.

## Clasificación

| Clase | Regla |
|---|---|
| No proyectable | Menos de 30 años válidos o sin ventanas de validación. |
| Solo escenario exploratorio | Se dan uno o más de estos casos: <br>• se elige la climatología; <br>• el MSSS es menor que 0,1; <br>• los intervalos no están calibrados (cobertura del 80 % menor que 0,6 o cobertura del 95 % menor que 0,8); <br>• el signo contradice a ≥ 80 % de los modelos CMIP6 de la variable física; <br>• es lluvia de MERRA-2, por su inhomogeneidad conocida, aunque la validación sea favorable. |
| Apta para proyección validada | Supera todo lo anterior. |

Son **tendencias destacadas** (como máximo 10) las validadas cuyo IC 95 % del cambio frente a la referencia excluye el 0. Se ordenan por:

1. estabilidad del signo en la sensibilidad;
2. habilidad;
3. cambio estandarizado.

## CMIP6

`data/expediente/cmip6_regional_mensual.csv` se prepara con `scripts/expediente/preparar_cmip6.py`. Sus entradas son `data/fenomenos/cmip6_mensual.csv` (1995–2014 y 2041–2060) y `data/fenomenos/cmip6_mensual_2015_2040.csv`.
El segundo archivo se descargó el 2026-11-15 con `backend/clima_nic/fuentes/nex_gddp.py`: 624 recortes, 423 MB, sin fallos. Cubre los 6 modelos, SSP2-4.5 y SSP5-8.5, `pr` y `tas`, las 5 regiones y los 12 meses de cada año de 2015 a 2040.
Por eso cada SSP tiene años continuos de 2015 a 2060 y la década se calcula con los años reales de cada modelo. La interpolación lineal entre 1995–2014 y 2041–2060 solo se usaría si faltaran esos años, y el informe lo indicaría.

## Reproducibilidad

- `perspectiva_id = 'P-' + SHA-256` del objeto canónico, con los números redondeados a 10⁻⁶. `ETDPerspectiva.verificar` lo comprueba al abrir un `resultados.json` guardado.
- Las opciones (`consulta.perspectiva`: activa, modelo, escenarios, semilla, n_sim) viajan en el enlace. No cambian los identificadores `C-` ni `R-` del bloque histórico.
- El ZIP añade `perspectiva.json`, `observaciones_indicadores.csv`, `proyecciones.csv` y `validacion.csv`. El manifiesto registra la semilla, el generador y la procedencia de CMIP6.

## Ejemplo: departamento de Matagalpa, T2M anual, generado en 2026

Datos: fixture de POWER del 2026-11-15, índices de las 7 celdas (cobertura 100 %), GISTEMP de la Región Central y CMIP6 con los años reales 2027–2036.

- **Apta para proyección validada y destacada:** la anomalía GISTEMP de la Región Central.
  - Histórico: Sen +0,29 °C/década (IC 0,21 … 0,37), q < 10⁻⁴.
  - Modelo: tendencia con errores AR(1), con MSSS 0,94 y coberturas de 0,80 y 1,00.
  - Cambio de 2027–2036 frente a 1991–2020: +0,75 °C, con intervalo predictivo del 80 % de 0,54 a 0,96.
  - Probabilidad de detectar la tendencia dentro de la década: 13 %.
- **CMIP6 para la Región Central**, cambio de 2027–2036 frente a 1995–2014 (mediana, mínimo y máximo de los 6 modelos):
  - Temperatura: +0,87 °C (0,56 a 1,06) con SSP2-4.5 y +1,00 °C (0,73 a 1,21) con SSP5-8.5.
  - Lluvia anual: +1,6 % (−3,3 a +22,1) con SSP2-4.5 y −7,1 % (−15,0 a +11,2) con SSP5-8.5. Los modelos no coinciden en el signo.
- **Solo exploratorio:** la T2M de POWER y Tmax. Su tendencia histórica es negativa, en sentido contrario a GISTEMP y a CMIP6; en el caso de Tmax, además, sus intervalos no están calibrados. TX90p contradice a CMIP6. Toda la lluvia de MERRA-2 es exploratoria por inhomogeneidad.

Que POWER (MERRA-2) y GISTEMP den signos distintos es una **comparación entre fuentes**: difieren en producto, escala y periodo. No es un desacuerdo entre métodos.
