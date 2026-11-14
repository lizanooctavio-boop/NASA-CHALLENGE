# Contrato de datos climáticos (`data/clima.json`)

**Versión del contrato:** 1.1.0 (borrador para revisión del equipo). La 1.1.0 solo **añade archivos opcionales** (§9); `clima.json` no cambia y sigue declarando `version_esquema` 1.0.0, con las mismas cifras de referencia.
**Rama:** `codex/datos-climaticos` · **Responsable:** datos (`data/` y `scripts/datos/`)

La interfaz debe leer únicamente los archivos derivados de `data/`. No necesita los HDF5 de IMERG, ni el repositorio privado de SICC-952, ni credenciales. Quien cambie un campo de este contrato debe subir la versión y avisar a quien lo consume.

## 1. Archivos

| Archivo | Contenido | ¿Lo consume la interfaz? |
|---|---|---|
| `data/clima.json` | Metadatos, dominios, series anuales, tendencias y contexto ONI. | Sí. Es el archivo principal. |
| `data/dominios.geojson` | Geometrías de referencia de los dominios (EPSG:4326, lon/lat). | Sí, para el mapa. |
| `data/serie_mensual.csv` | Acumulados mensuales por dominio (`dominio,anio,mes,mm,cobertura`). | No. Es la base para regenerar sin HDF5. |
| `data/fuentes/oni_2001_2024.csv` | ONI mensual (`anio,mes,oni`) de NOAA CPC, 2001–2024. | No. |
| `data/fuentes/manifiesto_imerg.csv` | Nombre, tamaño, SHA-256 y URL de los 288 archivos IMERG mensuales usados. | No. |
| `data/fuentes/comprobaciones_extraccion.json` | Celdas con peso por dominio y comprobación de la ponderación de la caja. | No. |
| `data/fuentes/sensibilidad_geometria.json` | Pendientes con el contorno de los países dilatado y erosionado 0,05°. | No. |

Convenciones: UTF-8, claves en `snake_case` sin tildes, valores de texto en español, números con punto decimal, años como enteros, sin `NaN` ni `Infinity`.

## 2. Estructura de `clima.json`

```text
{
  "esquema": "nasa-challenge/clima",
  "version_esquema": "1.0.0",
  "estado": "exploratorio",
  "metadatos": { ... },
  "dominios": [ ... ],            // 5 elementos, en orden fijo
  "superposicion": { ... },
  "oni": { ... }
}
```

### 2.1 `metadatos`

| Campo | Tipo | Significado |
|---|---|---|
| `titulo` | texto | Título corto del caso. |
| `producto` | objeto | `nombre`, `id` (`GPM_3IMERGM`), `version` (`V07B`), `variable`, `unidad_origen` (`mm/hr`), `proveedor`. |
| `periodo` | objeto | `inicio` 2001, `fin` 2024, `anios` 24. |
| `unidad_serie` | texto | `"mm/año"`. |
| `unidad_pendiente` | texto | `"mm/década"`. |
| `resolucion` | objeto | `espacial_grados` (0,1), `temporal_origen` (mensual), `temporal_salida` (anual, año calendario). |
| `metodo` | objeto | Cómo se obtuvieron las series y las tendencias (ver §4). Texto para mostrar en una ayuda o nota metodológica. |
| `fuentes` | lista | Cada fuente con `id`, `nombre`, `url`, `uso` y `licencia_o_condiciones`. |
| `integridad` | objeto | SHA-256 de las entradas: mapa base, `dominios.geojson`, `serie_mensual.csv`, ONI, manifiesto IMERG y sensibilidad de geometría. |
| `limites` | lista de textos | Advertencias que la interfaz debe poder mostrar. |

### 2.2 `dominios[]`

Los identificadores son estables y no cambian entre versiones: `caja_sicc`, `NIC`, `HND`, `CRI`, `NIC_fuera_caja`.

| Campo | Tipo | Significado |
|---|---|---|
| `id` | texto | Identificador estable (arriba). |
| `nombre` | texto | Nombre para mostrar. |
| `tipo` | `"caja"` \| `"pais"` \| `"complemento"` | Naturaleza de la geometría. |
| `rol` | `"principal"` \| `"contexto"` \| `"referencia"` \| `"auxiliar"` | `NIC` es principal; `HND` y `CRI` dan contexto; `caja_sicc` es la caja original de SICC-952 como referencia; `NIC_fuera_caja` es auxiliar y sirve solo para explicar la superposición. |
| `geometria` | objeto | `archivo` (`dominios.geojson`) e `id` del *feature* (igual al `id` del dominio). |
| `bbox` | `[oeste, sur, este, norte]` | Grados. |
| `area_km2` | número | Área de la geometría en proyección de igual área (EPSG:6933). |
| `celdas_con_peso` | entero | Celdas IMERG de 0,1° con peso mayor que cero. |
| `cobertura_minima` | número | Menor fracción de peso con dato válido en los 288 meses (esperado 1). |
| `anios_validos` | lista de enteros | Años con 12 meses válidos. Se espera 2001…2024 (24). |
| `serie_anual_mm` | lista de números | Acumulado anual en mm/año, **en el mismo orden** que `anios_validos`. |
| `tendencia` | objeto | Ver §2.3. |

### 2.3 `dominios[].tendencia`

| Campo | Tipo | Significado |
|---|---|---|
| `estado` | texto | `"ok"` o `"datos_insuficientes"`. Si no es `ok`, solo hay `anios` y `mensaje`. |
| `veredicto` | enumeración | `tendencia_detectada`, `evidencia_insuficiente` o `metodos_discrepan` (ver §3). |
| `veredicto_texto` | texto | Frase breve en español, lista para mostrar. |
| `nivel_confianza` | número | 0,95. |
| `media_anual_mm` | número | Media de la serie anual. |
| `mm_por_decada` | número | Pendiente por mínimos cuadrados, en mm/década. |
| `ic_mm_por_decada` | `[inferior, superior]` | Intervalo del 95 % del método principal. |
| `pct_por_decada`, `ic_pct_por_decada` | número, `[inf, sup]` | Lo mismo, relativo a la media anual. |
| `p_valor` | número | Del método principal. Informativo; el veredicto no depende de él por sí solo. |
| `n_efectivo`, `r1_residuos` | número | Tamaño efectivo y autocorrelación de lag 1 de los residuos. |
| `controles` | objeto | `hac` (`rezago`, `ic_mm_por_decada`), `theil_sen` (`mm_por_decada`, `ic_mm_por_decada`), `mann_kendall` (`tau`, `p_valor`). |
| `sensibilidad` | lista | Pendiente e intervalo del período completo, sin los 3 primeros y sin los 3 últimos años. |
| `omitir_un_anio_mm_por_decada` | `[mín, máx]` | Rango de la pendiente al quitar un año cada vez. |
| `interpretacion` | texto | Lectura prudente, redactada para el público. |

### 2.4 `superposicion`

Los dominios no son muestras independientes: `caja_sicc` cae casi entera dentro de Nicaragua y parte de Costa Rica; `NIC_fuera_caja` es el complemento de `caja_sicc` dentro de `NIC`.

```text
"superposicion": {
  "nota": "...",
  "umbral_km2": 1.0,
  "pares": [ { "a": "caja_sicc", "b": "NIC", "interseccion_km2": ..., "fraccion_de_a": ..., "fraccion_de_b": ... }, ... ],
  "sin_area_compartida": [ ["NIC", "HND"], ["NIC", "CRI"], ["HND", "CRI"], ... ]
}
```

`pares` lista las parejas con más de `umbral_km2` de área común; `sin_area_compartida`, el resto. Con la geometría de referencia: `caja_sicc` comparte ~41 000 km² con `NIC` (62 % de la caja, 34 % de Nicaragua) y ~6 900 km² con `CRI`; `NIC_fuera_caja` es `NIC` menos la caja. `caja_sicc` y `HND` no comparten área.

Los tres países no se solapan entre sí en la geometría de referencia, pero sí comparten el mismo sistema climático regional: la ausencia de área común **no implica** independencia estadística de sus series. La interfaz no debe contar «tres países con tendencia negativa» como tres resultados independientes, ni presentar `caja_sicc` y `NIC` como dos muestras distintas.

### 2.5 `oni`

Contexto de El Niño y La Niña. Es opcional para la interfaz; si falta el bloque, no se muestra.

| Campo | Significado |
|---|---|
| `fuente` | NOAA CPC, `oni.ascii.txt`, con URL. |
| `definicion_temporal` | Texto: ONI es la anomalía de la temperatura superficial del mar en la región Niño 3.4 en medias móviles de tres meses; cada valor mensual del archivo se asigna al **mes central** de su trimestre (DJF→enero … OND→noviembre, NDJ→diciembre). |
| `temporada` | `nombre` («junio–noviembre»), `meses` ([6…11]) y cómo se agrega: **media de los seis valores mensuales** (trimestres MJJ…OND). |
| `anios` | Lista 2001…2024. |
| `oni_temporada` | Valor de la temporada por año (misma longitud y orden que `anios`). |
| `categoria_descriptiva` | Por año: `"el_nino"` si ≥ +0,5, `"la_nina"` si ≤ −0,5, `"neutral"` en otro caso. Es una etiqueta de la media estacional, **no** el criterio oficial de NOAA (que exige cinco trimestres consecutivos). |
| `lluvia_jun_nov_mm` | Por id de dominio: suma de junio a noviembre en mm (misma longitud y orden). |
| `correlacion_descriptiva` | Por id de dominio: `r` de Pearson entre `oni_temporada` y `lluvia_jun_nov_mm`, y `n` (24). |
| `advertencia` | Texto obligatorio: la correlación es descriptiva. |

Límites de la asociación que la interfaz debe poder explicar: son 24 puntos, la lluvia de Centroamérica también responde al Atlántico, al Caribe y a la variabilidad local; el ONI no mide la lluvia ni la causa; la relación puede cambiar entre eventos; los dominios se solapan y comparten el mismo ONI; no se informan valores p ni se afirma causalidad.

## 3. Veredictos

Se calculan con tres intervalos del 95 %: el principal (mínimos cuadrados con grados de libertad ajustados por autocorrelación), HAC de Newey–West y Theil–Sen.

| `veredicto` | Condición | Qué puede decir la interfaz |
|---|---|---|
| `tendencia_detectada` | Los tres intervalos excluyen cero con el mismo signo y el p-valor principal es < 0,05. | «Con estos métodos se detecta una tendencia». |
| `evidencia_insuficiente` | Los tres intervalos incluyen cero. | «Con esta ventana y estos métodos no se detecta una tendencia». **No** «no hay cambio». |
| `metodos_discrepan` | Cualquier otro caso. | «El resultado depende del método». Mostrar los tres intervalos. |

### Resultados de referencia (deben reproducirse)

| Dominio | mm/década | IC 95 % principal | Veredicto |
|---|---:|---|---|
| `caja_sicc` | −13,132 | [−170,748; 144,485] | evidencia_insuficiente |
| `NIC` | −62,332 | [−210,763; 86,100] | evidencia_insuficiente |
| `HND` | −35,005 | [−173,729; 103,720] | evidencia_insuficiente |
| `CRI` | −201,224 | [−378,357; −24,091] | **metodos_discrepan** |

**Costa Rica.** El intervalo principal y el HAC excluyen cero, pero el intervalo de Theil–Sen [−369,492; 20,815] lo incluye, el p-valor de Mann–Kendall es 0,097 y al quitar los tres primeros años el intervalo principal pasa a [−445,151; 8,849]. La interfaz debe presentar Costa Rica como **resultado sensible al método**, nunca como tendencia confirmada, y mostrar los tres intervalos.

## 4. Cómo se construyen las series

1. **Datos.** IMERG Final V07B mensual (`GPM_3IMERGM.07`), tasa de precipitación en mm/h sobre malla de 0,1°. Se verifican 288 archivos (enero de 2001 a diciembre de 2024), unidades y malla idénticas.
2. **Ponderación por área.** Cada celda pesa por el área que comparte con el dominio. Para los países se intersecan las celdas con el polígono en EPSG:6933 (cilíndrica de igual área); para `caja_sicc` se usa el área esférica relativa de cada celda dentro del rectángulo. Ambas son medidas de área. Se comprobó recalculando la caja con pesos en EPSG:6933: el acumulado anual cambia como máximo 0,016 mm (8·10⁻⁶ en términos relativos) y las celdas con peso son las mismas (551). El resultado se guarda en `data/fuentes/comprobaciones_extraccion.json` y se resume en `metadatos.metodo`.
3. **Celdas parciales.** Una celda costera o fronteriza entra con la fracción de su área dentro del polígono, pero su valor de lluvia es único: IMERG no distingue tierra y mar dentro de una celda de 0,1° (unos 11 km).
4. **Mes.** Media ponderada de la tasa × horas del mes (24 × días). El mes es válido si la cobertura ponderada de celdas con dato es ≥ 0,999; si no, el cálculo se detiene.
5. **Año.** Suma de los 12 meses del año calendario. Un año con menos de 12 meses válidos se excluye (aquí no se excluye ninguno: 24 años completos).
6. **Tendencia.** Mínimos cuadrados sobre la serie anual; intervalo t con los grados de libertad ajustados por la autocorrelación de los residuos (Santer et al., 2000), HAC de Newey–West y Theil–Sen como controles. Detalle y fórmulas en `scripts/datos/tendencia.py`.

## 5. Límites de las geometrías

* Los polígonos de países proceden de Natural Earth 1:50 m, simplificados en el proyecto SICC-952. Son una máscara de referencia para ponderar celdas de 0,1°, no una frontera oficial ni un levantamiento.
* A los países se les restaron los lagos disponibles en esa base (en Nicaragua, el Lago de Nicaragua y el Lago de Managua). IMERG sí asigna lluvia a las celdas sobre los lagos, y la ponderación las excluye del promedio de país. `caja_sicc` es un rectángulo sin restar lagos ni mar.
* `caja_sicc` (10,7–12,6° N; 86,5–83,6° O) es un rectángulo de ~66 500 km²: el 62 % es Nicaragua, el 10 % es el norte de Costa Rica y el 28 % restante (~18 500 km²) no pertenece a ninguna máscara de país, porque son los lagos de Nicaragua y de Managua (restados a los países) y mar. Sus resultados no equivalen a los de Nicaragua.
* Con celdas de 0,1° y una geometría simplificada, cambios pequeños de contorno modifican el peso de las celdas de borde. Prueba realizada (dilatar y erosionar cada país 0,05° ≈ 5,5 km, `metadatos.metodo.sensibilidad_geometria`): los veredictos no cambian, pero la pendiente de Costa Rica oscila entre −178 y −228 mm/década, la de Nicaragua entre −58 y −68, y la de Honduras entre −32 y −38. Costa Rica es la más sensible por ser el país más pequeño. Esto no es una incertidumbre formal de la geometría.
* El período 2001–2024 es corto para tendencias climáticas; una tendencia de 24 años puede reflejar variabilidad interdecadal.

## 6. Reglas para quien consume el JSON

1. Mostrar siempre la unidad (`mm/año`, `mm/década`) y el intervalo junto a la pendiente.
2. Usar `veredicto` y `veredicto_texto`; no recalcular ni reinterpretar el signo de la pendiente.
3. No ordenar ni comparar dominios como si fueran muestras independientes; usar `superposicion`.
4. Si `estado` ≠ `ok` o `anios_validos` tiene menos de 24 elementos, mostrar `mensaje` y no dibujar tendencia.
5. Tratar campos desconocidos como opcionales: se pueden añadir campos en versiones menores sin romper la lectura.
6. Las rutas en `geometria.archivo` son relativas a `data/`.

## 7. Regenerar y verificar

Ver `scripts/datos/README.md`. Resumen:

```text
python scripts/datos/verificar_clima.py            # sin HDF5: reconstruye desde data/serie_mensual.csv y compara
python scripts/datos/generar_clima.py              # regenera data/clima.json desde los CSV derivados
python scripts/datos/extraer_series.py --hdf5 <carpeta>   # opcional: recalcula serie_mensual.csv desde los HDF5
```

## 8. Estado

Exploratorio. Las cifras de referencia vienen del diagnóstico ejecutado el 11 de noviembre de 2026 en la PC de Octavio y se reproducen con este procedimiento. Pendiente de revisión de los demás integrantes antes de que la interfaz dependa de campos concretos; la visibilidad del repositorio, la licencia y la publicación de la demo quedan a decisión de Octavio.

## 9. Archivos opcionales añadidos en 1.1.0 (backend `clima_nic`)

Generados por `backend/clima_nic` (ver `backend/README.md`). Ninguno es necesario para leer `clima.json`; quien no los use no tiene que cambiar nada.

| Archivo | Contenido |
|---|---|
| `data/fenomenos_nicaragua.json` | Esquema `nasa-challenge/fenomenos-nicaragua` 1.0.0: por región (`NIC`, `pacifico`, `central`, `caribe`, `caja_sicc`) y variable (lluvia, extremos ETCCDI, temperatura, calor extremo, humedad, radiación, viento, ETo, balance, SPI/SPEI, canícula, NDVI), la serie anual y su tendencia con `respuesta_reto` = {`que`, `donde`, `cuanto`, `significativo`}; `mapas_tendencia` por celda con FDR (celdas de MERRA-2 vía NASA POWER, con `fuente`, `uso: "demostracion_metodo"` y `advertencias`; no son tendencias por celda); `indices_climaticos` (Niño 3.4, TNA, AMO, PDO, CLLJ desde MERRA-2); `comparaciones_independientes`; `modelo_estacional` (`tipo`: `pronostico`); `escenarios_cmip6` (rangos, no pronóstico). |
| `data/regiones_nicaragua.geojson` | Polígonos de las cinco regiones. Pacífico, Central y Caribe son una partición de la máscara `NIC` de `dominios.geojson`. |
| `data/fenomenos/*.csv` | Derivados de NASA POWER, GISTEMP, MODIS y NEX-GDDP-CMIP6 para regenerar sin red; `manifiesto_power.csv` con SHA-256 de las respuestas crudas. |
| `data/historial/` | `habilidad.csv` y `corridas.jsonl`: habilidad del modelo estacional en cada corrida de `python -m clima_nic actualizar`. |

Reglas adicionales: `veredicto` en `fenomenos_nicaragua.json` puede ser `tendencia_detectada`, `evidencia_insuficiente`, `metodos_discrepan` o `datos_insuficientes`, y es más exigente que el de `clima.json` (añade Mann–Kendall modificado). Mostrar siempre `advertencias` cuando no esté vacía. Las variables de MERRA-2 con advertencia de inhomogeneidad no deben presentarse como tendencia climática.

