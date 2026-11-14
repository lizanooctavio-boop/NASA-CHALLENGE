# Guía de reproducción

Estado: **verificada** con los datos derivados de `data/`. No necesita los HDF5 de IMERG, el repositorio privado de SICC-952 ni credenciales.

## Pasos
1. Clonar: `git clone https://github.com/lizanooctavio-boop/NASA-CHALLENGE` y cambiar a la rama con la demo (`codex/verificacion-v2` o `codex/demo-render`).
2. Comprobar los datos, el backend (`backend/clima_nic`), la interfaz y la prueba extremo a extremo en navegador:
   - `python -m unittest discover tests -v` (o `pytest tests -q`).
   - Verifica `data/clima.json`, `data/fenomenos_nicaragua.json`, los índices oceánicos y las pestañas de la interfaz espacial.
3. (Opcional) Verificación del contrato de precipitación de `data/clima.json`: `pip install -r scripts/datos/requirements.txt` y `python scripts/datos/verificar_clima.py` (80 comprobaciones; 88 si además se instalan `shapely` y `pyproj` de `requirements-extraccion.txt`).
4. Abrir la demo con **datos reales**:
   - `node scripts/preparar_render.mjs`
   - `node scripts/servidor.mjs` (o `python -m http.server 8000` dentro de `public/`) y abrir `http://localhost:8000/`.
5. Para empezar en la caja original: abrir `http://localhost:8000/?region=caja_original#tendencias`; luego hacer clic en **Nicaragua**.
6. Explorar las pestañas adicionales de la interfaz espacial en inglés:
   - **Rainfall trend** (`#tendencias`): los 4 dominios de precipitación IMERG (`caja_original`, `nicaragua`, `honduras`, `costa_rica`), gráfica temporal, comparación de intervalos y 3 descargas (con `mann_kendall_p` en `rainfall_trends_by_area.csv`).
   - **Climate indicators** (`#indicadores`): regiones (`NIC`, `pacifico`, `central`, `caribe`), variables independientes (`temperatura_gistemp`, `lluvia_anual_imerg`, `lluvia_jun_nov_imerg`, `ndvi`), contraste con reanálisis MERRA-2 (`#ind-contraste`) y descarga CSV (`#ind-csv`).
   - **El Niño & cyclones** (`#fenomenos`): bloque ONI visible con datos reales de NOAA CPC (`data/fuentes/oni_2001_2024.csv`) e historial de ciclones HURDAT2/IBTrACS.
   - **Climate scenarios** (`#proyecciones`): proyecciones multimodelo reales de NASA NEX-GDDP-CMIP6 v2.0 (6 GCMs, SSP2-4.5 y SSP5-8.5, 2041–2060 frente a 1995–2014).

## Fuentes
| Dato | Fuente | Uso |
|---|---|---|
| Precipitación satelital | NASA GES DISC, GPM IMERG Final Run mensual V07B (`GPM_3IMERGM.07`), 288 archivos (2001–2024) | Variable principal de precipitación |
| Temperatura superficial | NASA GISS, GISTEMP v4 (`gistemp_nicaragua.csv`, 1981–2024) | Variable principal de temperatura |
| Vegetación | NASA MODIS MOD13C2 v061 (`ndvi_modis_mensual.csv`, 2000–2024) | Índice de vegetación (NDVI) |
| Reanálisis y variables diarias | NASA POWER / GMAO MERRA-2 (`serie_diaria_power.csv`, 1981–2024) | Índices diarios y contraste de homogeneidad |
| Índices oceánicos | NASA GMAO MERRA-2 (`indices_oceanicos_merra2.csv`); validación externa con NOAA CPC (`oni_2001_2024.csv`) y NOAA PSL (`tna_noaa_2001_2024.csv`, `amo_noaa_2001_2024.csv`) | Teleconexiones (Niño 3.4 / ONI, TNA, AMO, CLLJ) |
| Proyecciones futuras | NASA NCCS NEX-GDDP-CMIP6 v2.0 (`cmip6_mensual.csv`, 6 GCMs, SSP2-4.5 y SSP5-8.5, 2041–2060 vs. 1995–2014) | Escenarios climáticos regionales |
| Máscaras | Natural Earth 1:50 m (países y lagos) y regiones climáticas de Nicaragua | Ponderación por área |

Citas completas: ver [checklist-entrega.md](checklist-entrega.md).

## Método (resumen; detalle en `data/contrato.md` y `backend/clima_nic/`)
1. Media ponderada por área de las celdas que intersecan cada dominio o región climática; las celdas parciales entran por su fracción de área.
2. Mes = tasa × horas del mes (IMERG). Año = suma de los 12 meses del año calendario. Se admiten solo años completos.
3. Tendencia: mínimos cuadrados con intervalo t de 95 % y grados de libertad ajustados por autocorrelación (Santer et al., 2000). Controles: HAC de Newey–West y Theil–Sen / Mann–Kendall.
4. Veredicto: `tendencia_detectada` solo si los tres intervalos excluyen cero con el mismo signo y p < 0,05; `evidencia_insuficiente` si los tres incluyen cero; `metodos_discrepan` en otro caso.
5. Control de homogeneidad: prueba de Pettitt sobre el reanálisis MERRA-2 para detectar saltos instrumentales (1998–2005) y contrastarlos con fuentes satelitales y observacionales independientes (IMERG y GISTEMP v4).

## Unidades
Precipitación: mm/año (pendiente en mm/década). Temperatura: °C (pendiente en °C/década). NDVI: adimensional. ONI / TNA / AMO: °C (anomalía de SST). Nivel de confianza: 95 %.

## Resultados de precipitación IMERG (2001–2024)
| Dominio | Media (mm/año) | Pendiente MCO (mm/década) | IC 95 % | Theil–Sen (mm/década) | p Mann–Kendall | Veredicto |
|---|---:|---:|---|---:|---:|---|
| Caja original SICC | 2 231 | −13,1 | [−170,7; 144,5] | −7,9 | 0,8622 | evidencia insuficiente |
| Nicaragua | 2 094 | −62,3 | [−210,8; 86,1] | −70,5 | 0,3586 | evidencia insuficiente |
| Honduras | 1 658 | −35,0 | [−173,7; 103,7] | −51,3 | 0,5350 | evidencia insuficiente |
| Costa Rica | 3 062 | −201,2 | [−378,4; −24,1] | −181,4 | 0,0970 | **métodos discrepan** |

**Costa Rica depende del método:** el intervalo principal y el HAC excluyen cero, pero el de Theil–Sen [−369,5; 20,8] lo incluye y Mann–Kendall da p = 0,0970. Se presenta como resultado sensible al método, nunca como tendencia confirmada.

## Límites
- 24 años de IMERG son pocos para separar tendencia secular de variabilidad multidecadal. Honduras pasa de −35,0 a −89,5 mm/década al quitar los tres primeros años.
- «Evidencia insuficiente» **no** significa «no hay cambio»: la ventana y el método no bastan para detectarlo con significancia al 95 %.
- Los dominios de `data/clima.json` se solapan (la caja comparte unos 41 000 km² con Nicaragua) y comparten el mismo clima regional: no son muestras independientes.
- MERRA-2 (entregado por NASA POWER) presenta saltos estructurales de asimilación entre 1998 y 2005 (detectados por el test de Pettitt con p < 0,01), por lo que no se usa como fuente de tendencia para precipitación ni temperatura sin contraste independiente (IMERG y GISTEMP v4).
- Los índices oceánicos (Niño 3.4 / ONI, TNA, AMO) se muestran como teleconexiones de contexto; correlación no implica causalidad única.
- Las geometrías son máscaras de referencia, no fronteras oficiales.
