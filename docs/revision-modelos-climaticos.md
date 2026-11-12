# Revisión de los modelos climáticos

**Fecha:** 12 de noviembre de 2026 · **Rama revisada:** `codex/datos-climaticos` (copiada también en `codex/demo-render`) · **Estado:** propuesta, sin cambios en el código.

Objetivo pedido: un software centrado en Nicaragua que use solo datos de NASA de cobertura global para estimar las condiciones regionales del país, que abarque todos los fenómenos climáticos relevantes y que describa tendencias con la mayor capacidad posible.

## 1. Qué hace hoy

- Una sola variable: precipitación IMERG Final V07B mensual (`GPM_3IMERGM.07`), malla de 0,1°, enero de 2001 a diciembre de 2024 (288 archivos).
- Dominios: Nicaragua (principal), Honduras y Costa Rica (contexto), caja SICC-952 (referencia) y Nicaragua fuera de la caja (auxiliar), con ponderación por área.
- Serie anual y tendencia lineal con tres intervalos del 95 %: mínimos cuadrados con grados de libertad ajustados por autocorrelación, HAC de Newey–West y Theil–Sen, más Mann–Kendall y pruebas de sensibilidad (recortes y omitir un año).
- Contexto ENSO: correlación descriptiva entre el ONI de junio a noviembre y la lluvia de esa temporada.
- No hay predicción: es un diagnóstico de tendencias pasadas.

Resultados principales:

| Dominio | mm/década | IC 95 % | Veredicto | r con ONI (jun–nov) |
|---|---:|---|---|---:|
| Nicaragua | −62 | [−211; +86] | evidencia insuficiente | −0,56 |
| Honduras | −35 | [−174; +104] | evidencia insuficiente | −0,59 |
| Costa Rica | −201 | [−378; −24] | los métodos discrepan | −0,46 |
| Caja SICC | −13 | [−171; +144] | evidencia insuficiente | −0,59 |

La metodología estadística es correcta y prudente. La señal más fuerte no es la tendencia, sino la relación con El Niño.

## 2. Brechas frente al objetivo

### 2.1 Solo datos de NASA

| Insumo actual | Origen | Sustituto NASA |
|---|---|---|
| ONI (El Niño) | NOAA CPC | Índice Niño 3.4 calculado con la temperatura superficial del mar de MERRA-2 (GMAO, GES DISC) |
| Contornos de país | Natural Earth | Límites administrativos de SEDAC/CIESIN (GPW v4) |
| Caja SICC-952 | Repositorio externo | Se conserva solo como referencia histórica, o se retira |

### 2.2 Fenómenos que faltan

| Fenómeno | Producto NASA | Indicador propuesto |
|---|---|---|
| Temperatura y calor | MERRA-2, NASA POWER (1981–) | Tmedia, Tmáx, días de calor |
| Sequía | IMERG, MERRA-2 | SPI-3 y SPI-12, déficit de la primera temporada |
| Canícula (julio–agosto) | IMERG diario | Duración e intensidad del mínimo de mitad de verano |
| Lluvias extremas | IMERG diario o de media hora | Rx1day, Rx5day, días > p95 |
| Humedad del suelo | SMAP (2015–), MERRA-2 | Anomalía estacional |
| Agua subterránea | GRACE / GRACE-FO | Anomalía de almacenamiento de agua terrestre |
| Vegetación | MODIS (NDVI/EVI) | Respuesta de la vegetación a la sequía |
| El Niño | MERRA-2 | Niño 3.4 |
| Atlántico tropical y Caribe | MERRA-2 | Índices TNA y Caribe |
| Chorro de bajo nivel del Caribe | MERRA-2 (viento a 925 hPa) | Índice CLLJ |
| ZCIT | MERRA-2, IMERG | Posición latitudinal |
| Ciclones tropicales | MERRA-2 | Detección por vorticidad y núcleo cálido (NASA no tiene catálogo equivalente a IBTrACS) |

### 2.3 De datos globales a condiciones de Nicaragua

Hoy no se hace. Propuesta: reducción de escala estadística, con predictores globales y regionales de MERRA-2 (SST, viento, humedad, geopotencial) para estimar la lluvia y la temperatura en Nicaragua y sus regiones (Pacífico, centro y Caribe).

### 2.4 Capacidad de predicción

Una capacidad de predicción «altísima» no es alcanzable y prometerla contradice los propios datos: con 24 años anuales ni la tendencia de Nicaragua es significativa, y la lluvia del país tiene gran variabilidad natural. Lo que sí se puede hacer, y medir:

1. Alargar el registro: IMERG V07 desde 1998, MERRA-2 y GPCP desde 1979–1980.
2. Trabajar con datos mensuales y estacionales en lugar de anuales.
3. Validar con retro-pronóstico (entrenar con unos años y comprobar con años no usados) y publicar la habilidad (correlación, RPSS, error) en la interfaz.
4. Ofrecer perspectivas estacionales probabilísticas («junio–noviembre más seco de lo normal con probabilidad X»), que es donde ENSO y el Atlántico aportan habilidad real. La tendencia a largo plazo seguirá teniendo intervalos amplios.

## 3. Plan recomendado

Cada paso es independiente y se puede entregar por separado.

| Paso | Contenido | Requisitos |
|---|---|---|
| (a) | Sustituir el ONI de NOAA y Natural Earth por fuentes NASA | Cuenta NASA Earthdata |
| (b) | Extender IMERG a 1998–2025 y añadir temperatura y precipitación de MERRA-2 desde 1980 | Earthdata, varios GB de descarga |
| (c) | Sequía (SPI), canícula y extremos | IMERG diario |
| (d) | Modelo estacional para Nicaragua con predictores globales, validado con retro-pronóstico, y su habilidad en la interfaz | (a) y (b) |

Cada cambio en `data/clima.json` debe subir la versión del contrato (`data/contrato.md`) y avisar a la interfaz.
