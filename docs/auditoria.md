# Auditoría de datos, cálculos y demo

Fecha: 2026-11-12 · Rama base: `origin/codex/demo-render` (`a61ecbc`) · Rama de esta entrega: `codex/verificacion-v2`

## Veredicto

**Los cálculos de `data/clima.json` y `data/fenomenos_nicaragua.json` son correctos, trazables y reproducibles.** Cada cifra de `data/clima.json` (contrato 1.0.0) se recalculó de forma independiente y coincide; el backend `backend/clima_nic` (contrato 1.1.0) calcula indicadores regionales ponderados por área, contrasta el reanálisis MERRA-2 contra fuentes satelitales y de estaciones independientes (GPM IMERG y NASA GISS GISTEMP v4), evalúa el pronóstico estacional fuera de muestra con control FDR y resume escenarios reales de NEX-GDDP-CMIP6 v2.0 (6 modelos, 2041–2060 frente a 1995–2014). En la interfaz espacial actual se verificaron en navegador headless las pestañas **Rainfall trend**, **Climate indicators** y **El Niño & cyclones**.

---

## 1. Qué se verificó y cómo

| Capa | Método | Resultado |
|---|---|---|
| Serie mensual → anual (`data/clima.json`) | Suma de 12 meses con código propio (`tests/test_datos.py`) | Coincide (diferencia < 0,001 mm) en los 5 dominios y 24 años (2001–2024). |
| Pendiente MCO e intervalo principal | MCO propio con grados de libertad ajustados por autocorrelación de lag 1 (Santer et al., 2000) | Coincide a 0,01 mm/década. Incluye `p_valor`, `r1_residuos` y `n_efectivo`. |
| HAC (Newey–West) | Implementación propia, rezago 2, corrección $n/(n-2)$ | Coincide a 0,01 mm/década. |
| Theil–Sen y Mann–Kendall | Mediana de pendientes por pares; $\tau$ y valor $p$ por conteo | Coinciden a 0,001. |
| Veredictos (`data/clima.json`) | Regla de decisión aplicada a los tres intervalos | Los 5 coinciden (`evidencia_insuficiente` en NIC, HND, caja y complemento; `metodos_discrepan` en CRI). |
| ONI (`data/clima.json` y `oni_2001_2024.csv`) | Media jun–nov, categorías y correlación de Pearson | Coincide. 288 valores mensuales sin huecos. |
| Geometría (`verificar_clima.py`) | Comprobación con `shapely` y `pyproj` (EPSG:6933) | **88 de 88** comprobaciones; Pacífico + Central + Caribe particionan exactamente la máscara `NIC` (`data/regiones_nicaragua.geojson`). |
| Integridad criptográfica | SHA-256 de insumos en `data/clima.json` y `data/fenomenos_nicaragua.json` | Todos los hashes coinciden; manifiesto IMERG de 288 archivos y `manifiesto_power.csv` verificados. |
| Backend `clima_nic` (`tests/test_backend_clima_nic.py` y `tests/test_indicadores_nicaragua.py`) | 54 pruebas unitarias y de integración (`pytest`) | SPI/SPEI, ETCCDI, canícula objetiva, Mann–Kendall modificado (Hamed & Rao, 1998), Pettitt, FDR (Benjamini–Hochberg), $ET_0$ FAO-56 Penman–Monteith, modelo estacional LOO y delta CMIP6 pasan al 100 %. |
| Contrato de interfaz (`tests/test_interfaz.py`) | `src/estadistica.js` y `src/contrato.js` en Node.js | Series, pendientes, intervalos (MCO, HAC, Theil–Sen), valor $p$ de Mann–Kendall, veredictos y recta ajustada iguales a `data/clima.json`. |
| Demo E2E en navegador (`tests/test_e2e_navegador.py`) | Edge headless sobre la compilación de `scripts/preparar_render.mjs` | Comprueba pestañas **Rainfall trend**, **Climate indicators** (regiones, variables, contraste con MERRA-2 y descarga CSV) y **El Niño & cyclones** (bloque ONI con datos reales). |

---

## 2. Resultados de referencia reproducidos (`data/clima.json`, IMERG 2001–2024)

| Dominio | Media (mm/año) | Pendiente MCO (mm/década) | IC 95 % principal | HAC | Theil–Sen | Veredicto |
|---|---:|---:|---|---|---|---|
| Caja original SICC (`caja_sicc`) | 2 230,9 | −13,132 | [−170,748; 144,485] | [−119,353; 93,090] | −28,705 [−184,428; 188,865] | `evidencia_insuficiente` |
| Nicaragua (`NIC`) | 2 094,1 | −62,332 | [−210,763; 86,100] | [−144,581; 19,917] | −64,923 [−233,240; 98,283] | `evidencia_insuficiente` |
| Honduras (`HND`) | 1 657,6 | −35,005 | [−173,729; 103,720] | [−142,101; 72,092] | −26,574 [−191,829; 122,265] | `evidencia_insuficiente` |
| Costa Rica (`CRI`) | 3 061,6 | −201,224 | [−378,357; −24,091] | [−332,371; −70,077] | −210,275 [−369,492; **20,815**] | **`metodos_discrepan`** |

Para Costa Rica, `p_valor` principal = 0,0279 y Mann–Kendall $p = 0{,}0972$: el resultado depende del método y la interfaz lo muestra como **Methods disagree**.

---

## 3. Auditoría de fuentes adicionales y correcciones de integración

### 3.1 Escenarios NEX-GDDP-CMIP6 reales vs. archivo sintético retirado
En la revisión previa se detectó que `data/globales/proyecciones_cmip6_nicaragua_2025_2100.json` y `generar_proyecciones_cmip6_nicaragua()` no provenían de descargas satelitales ni de modelos, sino de fórmulas escritas a mano, daban valores año por año (cuando los escenarios solo tienen sentido en ventanas multidecadales) y subestimaban la duración de la canícula (15 días frente a una mediana observada de 46 a 64 días en `data/fenomenos_nicaragua.json`).
- **Acción aplicada:** Se eliminaron por completo ese archivo y ese script.
- **Fuente real vigente:** El backend `backend/clima_nic/fuentes/nex_gddp.py` y `backend/clima_nic/proyecciones.py` procesan los recortes reales de **NASA NEX-GDDP-CMIP6 v2.0** (`data/fenomenos/cmip6_mensual.csv`, SHA-256 verificado en `data/fenomenos_nicaragua.json`) para 6 modelos (`ACCESS-CM2`, `CanESM5`, `EC-Earth3`, `GFDL-ESM4`, `MPI-ESM1-2-HR`, `MRI-ESM2-0`), aplicando el método delta entre `2041–2060` y `1995–2014` bajo `SSP2-4.5` y `SSP5-8.5` por región (`NIC`, `pacifico`, `central`, `caribe`, `caja_sicc`). En `NIC`, el calentamiento proyectado en mediana (rango de 6 modelos) es **+1,55 °C** (+1,15 a +2,06 °C) en `SSP2-4.5` y **+1,96 °C** (+1,42 a +2,67 °C) en `SSP5-8.5` (6 de 6 modelos más cálidos), mientras que los modelos discrepan en el signo del cambio de lluvia anual (mediana +0,9 % en `SSP2-4.5` y −4,3 % en `SSP5-8.5`).

### 3.2 NASA POWER: puntos individuales retirados vs. malla diaria ponderada por área y saltos de MERRA-2
Se retiraron los 4 archivos CSV mensuales de un solo punto por zona (`nasa_power_mensual_*.csv` y `nasa_power_nicaragua_2001_2024.json`) porque el repositorio ya cuenta en `data/fenomenos/serie_diaria_power.csv` con la serie diaria 1981–2024 de 62 celdas MERRA-2 ($0{,}5^\circ \times 0{,}625^\circ$) ponderadas por área en EPSG:6933 (`data/fenomenos/celdas_power.csv` y `manifiesto_power.csv`). Al comparar los 4 puntos retirados contra las series regionales ponderadas por área en el período común 2001–2024 se observan dos diferencias fundamentales:
1. **Unidades mensuales vs. acumulado anual:** La API mensual de POWER entrega `PRECTOTCORR` como tasa media diaria del mes ($\text{mm/día}$); sumar las 12 cifras sin multiplicar por los días de cada mes subestima el acumulado anual por un factor de ~30,4.
2. **Sesgo de representatividad espacial de un punto frente al polígono regional** (incluso multiplicando cada mes por sus días calendario):

| Comparación (2001–2024) | Lluvia anual punto (mm) | Lluvia anual ponderada por área (mm) | Diferencia (mm) | $r$ lluvia | $T_{2m}$ punto (°C) | $T_{2m}$ ponderada (°C) | Diferencia (°C) | $r$ $T_{2m}$ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Punto Centro ($12{,}5^\circ\text{N}, 85{,}0^\circ\text{O}$) vs. `NIC` | 1 414,7 | 1 627,8 | −213,0 | 0,964 | 25,41 | 25,89 | −0,48 | 0,963 |
| Punto Pacífico ($12{,}1^\circ\text{N}, 86{,}3^\circ\text{O}$) vs. `pacifico` | 1 533,0 | 1 514,5 | +18,5 | 0,985 | 28,39 | 27,56 | +0,83 | 0,984 |
| Punto Norte ($13{,}1^\circ\text{N}, 86{,}0^\circ\text{O}$) vs. `central` | 1 242,5 | 1 290,3 | −47,7 | 0,976 | 23,89 | 24,83 | −0,94 | 0,990 |
| Punto Caribe ($12{,}0^\circ\text{N}, 83{,}8^\circ\text{O}$) vs. `caribe` | 2 770,0 | 1 845,0 | **+925,0** | 0,784 | 26,47 | 26,01 | +0,45 | 0,852 |

En el Caribe, un solo punto costero cerca de Bluefields sobreestima en **+925 mm/año** (+50 %) la lluvia media de toda la región autónoma y reduce la correlación interanual a $r = 0{,}784$.

> [!IMPORTANT]
> **Inhomogeneidad estructural de MERRA-2 (1998–2005):** Las series de lluvia y temperatura de NASA POWER provienen del reanálisis MERRA-2 y presentan saltos artificiales al cambiar la constelación de satélites asimilados (AMSU/TRMM alrededor de 1998–2005). La prueba de Pettitt en `data/fenomenos_nicaragua.json` detecta en MERRA-2 un salto abrupto de lluvia en **2005** para `NIC` (+820 mm, $p < 0{,}0001$), `pacifico` (+964 mm) y `central` (+740 mm), y en **2002** para `caribe` (+850 mm), así como un salto negativo de temperatura en **1999** (−0,55 a −0,71 °C, $p \le 0{,}01$). Por ello:
> - En 2001–2024, MERRA-2 da una tendencia aparente de lluvia en `NIC` de **+313,0 mm/década** (`tendencia_detectada`), mientras que el producto satelital calibrado **GPM IMERG** da **−64,9 mm/década** (`evidencia_insuficiente`).
> - En 1981–2024, MERRA-2 da una tendencia de temperatura en `NIC` de **−0,11 °C/década**, mientras que las estaciones de **NASA GISTEMP v4** muestran un calentamiento claro de **+0,29 °C/década** (IC 95 % [+0,22; +0,37], `tendencia_detectada`).
> - En consecuencia, la pestaña **Climate indicators** (`app/indicadores.js`) expone únicamente variables de fuentes observacionales independientes (`temperatura_gistemp`, `lluvia_anual_imerg`, `lluvia_jun_nov_imerg`, `ndvi`) y muestra MERRA-2 en la gráfica de **Second opinion** para evidenciar la discrepancia.

### 3.3 Índices oceánicos: cálculo desde NASA MERRA-2 y validación con NOAA
El proyecto calcula todos los índices oceánicos (`nino34`, `tna`, `amo`, `pdo`, `cllj_u10m`) directamente desde datos NASA (`TS` y `U10M` de MERRA-2 vía la API regional de POWER, con máscara oceánica Natural Earth 10 m en `data/fenomenos/indices_oceanicos_merra2.csv`). Las series de NOAA (`data/fuentes/oni_2001_2024.csv`, `data/fuentes/tna_noaa_2001_2024.csv` y `data/fuentes/amo_noaa_2001_2024.csv`) se conservan en `data/fuentes/` **únicamente para validación externa**:

| Índice oceánico (MERRA-2 vs. referencia NOAA) | Período común | Meses ($n$) | Correlación ($r$) | RMSE centrado (°C) | Observación |
|---|---|---:|---:|---:|---|
| **Niño 3.4** (media móvil 3 meses MERRA-2 vs. ONI NOAA CPC) | 2001–2024 | 288 | **0,983** | 0,165 | 90,6 % de acuerdo exacto en categoría ($\ge +0{,}5$ / $\le -0{,}5$). |
| **TNA** (MERRA-2 $5{,}5\text{–}23{,}5^\circ\text{N}, 57{,}5\text{–}20^\circ\text{O}$ vs. NOAA PSL) | 2001–2024 | 288 | **0,949** | 0,139 | Desplazamiento medio de +0,049 °C por diferencia de período base (1991–2020 vs. NOAA). |
| **AMO** (MERRA-2 $0\text{–}60^\circ\text{N}, 80^\circ\text{O–}0^\circ$ sin tendencia vs. NOAA PSL) | 2001–2023 | 265 | **0,768** (ambos sin tendencia lineal en la ventana) / 0,615 bruto | 0,118 | MERRA-2 quita la tendencia en 1981–2024 y NOAA PSL usa Kaplan SST desde 1856; se excluyeron los meses de 2023 con relleno `-99.99` en NOAA. |

### 3.4 Alcance climático y limpieza del repositorio
- **Sin módulos ni referencias a estrés térmico de cultivos:** Se verificó que el repositorio y la documentación cumplen estrictamente el alcance climático del reto NASA (atmósfera, océano y superficie terrestre, sin modelos de cultivos).
- **Sin archivos compilados `.pyc`:** `tests/__pycache__/` no está versionado y el `.gitignore` raíz excluye `__pycache__/`, `*.py[cod]`, `*.h5`, `*.hdf5`, `*.nc` y credenciales.

---

## 4. Comprobación de la interfaz actual (`origin/codex/demo-render` + correcciones)

Se revisaron los tres puntos solicitados sobre la interfaz espacial en inglés (`index.html`, `app/`, `src/`):

| Punto revisado | Estado en `origin/codex/demo-render` | Acción en `codex/verificacion-v2` |
|---|---|---|
| **1. Bloque ONI con datos reales (pestaña «El Niño & cyclones»)** | En producción (`/clima-base/enos.json` generado por `preparar_meteo.mjs`) carga la serie histórica y semanal de NOAA. Sin embargo, al compilar solo con `node scripts/preparar_render.mjs` (sin `public/clima-base/enos.json`), `/api/enos` devolvía 404 y mostraba `ENSO data unavailable.`. | **Corregido:** `scripts/preparar_render.mjs` copia `data/fuentes/oni_2001_2024.csv` a `public/data/fuentes/`, y `src/fuentes-meteo.js` sirve ese CSV real de NOAA CPC cuando `/clima-base/enos.json` no está presente. La pestaña muestra las tarjetas reales de fase ENSO y ONI en ambos modos. |
| **2. CSV de pendientes (`rainfall_trends_by_area.csv`) con valor $p$ de Mann–Kendall** | Faltaba: `src/contrato.js` no extraía `t.controles.mann_kendall.p_valor` y `csvPendientes()` en `src/tendencias.js` solo exportaba `ls_p`. | **Corregido:** `src/contrato.js` asigna `p: t.controles.mann_kendall.p_valor` a `sen`, y `src/tendencias.js` incluye la columna `mann_kendall_p` en `rainfall_trends_by_area.csv`. |
| **3. Textos residuales de «datos de ejemplo»** | Ya eliminados en `09ac3b1` (`src/datos/ejemplo.js` fue borrado y la interfaz está en inglés sin notas ni avisos para el usuario). | **Verificado:** `test_sin_datos_sinteticos_ni_texto_de_ejemplo` comprueba en el DOM renderizado y en todas las descargas que no quedan textos de ejemplo. |

---

## 5. Cómo ejecutar todas las verificaciones

```text
python scripts/datos/verificar_clima.py       # 88 comprobaciones del contrato 1.0.0
python -m pytest tests -q                     # 88 pruebas (54 del backend clima_nic + 22 de datos + 6 de contrato JS + 6 E2E en navegador)
```
