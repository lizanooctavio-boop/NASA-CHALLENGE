# Plan de integración de los recursos del reto — Earth System Trend Detective

Fecha: 12-11-2026 · Repositorio: `NASA-CHALLENGE`, rama base `codex/verificacion-entrega` (488e19f) · Estado: **propuesta, nada ejecutado**.

Se integran los 13 recursos de la pestaña Resources. Cada uno recibe un papel concreto en el producto: fuente de datos, comprobación independiente, caso de demostración o capa didáctica. La regla común es que un recurso solo cuenta como integrado cuando tiene adaptador o procedimiento reproducible, salida en `data/`, prueba, cita en la interfaz y una línea en `docs/reto/CUMPLIMIENTO.md`.

## 1. Punto de partida (comprobado en el repositorio)

- Backend `clima_nic` con adaptadores POWER, IMERG, MERRA-2, MODIS (ORNL, un sitio por región), SMAP, GRACE-FO, GISTEMP, NEX-GDDP y lagos (`fuentes/lagos.py`, implementado sin datos).
- Estadística: MCO con gl ajustados, HAC, Theil–Sen, Mann–Kendall clásico y modificado, Pettitt, FDR, control por índices oceánicos.
- Interfaz en inglés con pestañas *Rainfall trend*, *Climate indicators* y *El Niño & cyclones*. Contrato `data/clima.json` 1.0.0, que **no se modifica**: todo lo nuevo va en archivos aparte o en campos opcionales de `fenomenos_nicaragua.json`.
- Brechas que cubren los recursos: NDVI muestreado en un punto por región en lugar de media regional; IMERG sin contraste externo; sin estaciones; sin variables de océano, atmósfera urbana ni agua superficial; sin capa explicativa de significancia; un solo país como caso.

## 2. Mapa de recursos

| # | Recurso | Papel en el producto | Qué se integra | Acceso | Comprobado hoy |
|---|---|---|---|---|---|
| 1 | Giovanni | Comprobación independiente y variables nuevas | Serie IMERG de área promediada para contrastar la nuestra; OMI NO₂ sobre Managua, AIRS temperatura del aire, clorofila MODIS-Aqua en el golfo de Fonseca | Earthdata Login | La API de series respondió 401 sin token (existe y pide autenticación) |
| 2 | Hydrology Time Series (data rods) | Variables hidrológicas del enunciado | GLDAS: humedad del suelo, evapotranspiración, escorrentía | Por verificar | La página carga por JS; falta comprobar el servicio |
| 3 | AppEEARS | Medias regionales reales | NDVI MOD13A3, LST MOD11A2, ET MOD16A2GF, cobertura MCD12Q1, SMAP L4 sobre los polígonos de región | Earthdata Login (token API) | Los cinco productos figuran en el catálogo público (193 productos) |
| 4 | NOAA Climate Data Online | Validación con estaciones | GSOM: Managua 1982–2003, Juigalpa 1979–2002, Tegucigalpa 1957–2025 y otras tres hasta 1991 | Token gratuito por correo | Estaciones y periodos listados con el servicio de búsqueda |
| 5 | Artículo NTRS (SeaWiFS) | Referencia de método y caso costero | Procedimiento de serie + significancia citado; inspira el caso de clorofila costera | Público | Enlace activo; **falta leer el artículo** |
| 6 | KNMI Climate Explorer | Segunda opinión externa | Tendencia de la misma caja con otro conjunto (GPCC, CRU o ERA5) y correlación con Niño 3.4 | Web; registro gratuito para subir series | No probado |
| 7 | Artículo de Medium (pruebas de tendencia) | Capa didáctica y revisión de métodos | Tarjetas «How do we test a trend?»; contrastar sus pruebas con las nuestras | Público | Falta leerlo |
| 8 | Guía de Statsig (significancia) | Capa didáctica | Glosario: p-value, confidence interval, significance, sample size | Público | Falta leerla |
| 9 | CSA — datos RCM | Agua superficial por radar | Extensión de agua de Cocibolca o humedales de Los Guatuzos / río San Juan | EODMS, licencia abierta de Canadá con cuenta | El catálogo confirma acceso abierto a ciertos productos vía EODMS; cobertura sobre Nicaragua por verificar |
| 10 | Geo.ca | Caso de contraste en Canadá | Límites de una ecozona o provincia para correr el mismo flujo | Público | No probado |
| 11 | SWOT (CSA) | Nivel de lagos | Altura de agua de Cocibolca y Xolotlán en `fuentes/lagos.py` | API Hydrocron sin cuenta | Hydrocron respondió 200 sin login con un lago de prueba; falta el `lake_id` de Cocibolca |
| 12 | CSA — monitorizar ecosistemas | Marco narrativo | Categoría «Ecosystems» en las preguntas guiadas y texto de fuentes | Público | — |
| 13 | Tutorial SAR en Python (CSA) | Procedimiento de la capa de radar | Base del cuaderno que obtiene la máscara de agua (#9) | GitHub | No probado |

## 3. Fichas de trabajo

### 3.1 Giovanni (#1)
- **Contraste IMERG.** Pedir *Time Series, Area-Averaged* de `GPM_3IMERGM_07` para la caja SICC y para Nicaragua (forma de país de Giovanni), 2001–2024. Guardar CSV en `data/contraste/giovanni_imerg.csv` con fecha de descarga y URL de la petición.
- **Variables nuevas** que el enunciado nombra y aún faltan: OMI NO₂ troposférico sobre Managua (caso «atmósfera sobre una gran ciudad»), AIRS temperatura del aire en superficie para comparar con GISTEMP y MERRA-2, clorofila-a de MODIS-Aqua en el golfo de Fonseca (enlace con el artículo #5).
- **Código:** `fuentes/giovanni.py` con lectura del CSV de Giovanni; por API si el token funciona y, si no, desde la descarga manual documentada.
- **Aceptación:** diferencia media anual entre nuestra serie y la de Giovanni documentada y explicada (máscara y ponderación distintas); misma conclusión de veredicto o explicación si cambia.

### 3.2 Hydrology Time Series (#2)
- Series GLDAS-2.1 Noah (humedad del suelo 0–10 y 10–40 cm, ET, escorrentía) en los mismos sitios que MODIS y en un punto por región.
- **Código:** `fuentes/gldas_datarods.py`. Variables nuevas en `productos.VARIABLES` con definición sencilla.
- **Aceptación:** comparar humedad del suelo GLDAS con la de MERRA-2 ya integrada; anotar que son series de punto.

### 3.3 AppEEARS (#3)
- Peticiones de área con `data/regiones_nicaragua.geojson`: MOD13A3 (NDVI mensual, 1 km), MOD11A2 (LST), MOD16A2GF (ET), MCD12Q1 (cobertura) y SPL4SMGP (humedad SMAP, 2015–).
- **Mejora clave:** sustituye el NDVI de un sitio por región por una media regional. MCD12Q1 permite calcular el NDVI solo en píxeles de cobertura estable y separar mejor cambio de uso del suelo y señal climática.
- **Código:** `fuentes/appeears.py` (enviar tarea, esperar, descargar, recortar). Mantener ORNL como respaldo sin cuenta.
- **Aceptación:** NDVI regional y por sitio en la misma gráfica; FDR aplicado al conjunto ampliado de variables.

### 3.4 NOAA Climate Data Online (#4)
- Descargar GSOM y GHCN-Daily de las seis estaciones de Nicaragua y de Tegucigalpa.
- **Usos:** validar temperatura (GISTEMP, POWER/MERRA-2) y lluvia en los años comunes; Tegucigalpa permite comparar con IMERG en Honduras durante 2001–2024; vista didáctica de cuántas estaciones hay realmente.
- **Código:** `fuentes/noaa_cdo.py`; resultados en `docs/auditoria.md`.
- **Límite comprobado:** las estaciones de Nicaragua terminan en 2003 o antes; no sirven para la tendencia 2001–2024, sí para validar el periodo 1981–2003.

### 3.5 Artículo NTRS SeaWiFS (#5)
- Leerlo y extraer su procedimiento (desestacionalización, prueba y nivel de significancia). Citarlo en la nota metodológica.
- Caso costero con clorofila (Giovanni, #1): golfo de Fonseca y costa caribeña cerca de desembocaduras. SeaWiFS 1997–2010 y MODIS-Aqua 2002–; sin empalmar sensores sin validación.

### 3.6 KNMI Climate Explorer (#6)
- Calcular la tendencia de la caja SICC y de Nicaragua con un conjunto distinto de IMERG y la correlación con Niño 3.4 para la temporada junio–noviembre.
- Registrar en `docs/auditoria.md` cifras, conjunto, versión y fecha. En la interfaz, un indicador «Cross-checked with KNMI Climate Explorer» con el resultado.

### 3.7 Medium y Statsig (#7 y #8)
- Leer ambos y comprobar que cada prueba que mencionan está implementada o justificar por qué no (p. ej., Spearman rho como control adicional si aparece).
- Capa *Learn* en la interfaz: qué es una tendencia, p-value, intervalo de confianza, por qué «no significativo» no significa «sin cambio», autocorrelación y por qué usamos tres métodos. Enlaza cada término con el veredicto mostrado.

### 3.8 Radar: RCM, tutorial SAR y monitorización de ecosistemas (#9, #12, #13)
- Buscar en EODMS escenas RCM sobre Cocibolca y los humedales del sur. Si no hay productos abiertos, aplicar el mismo tutorial a Sentinel-1 (ASF, Earthdata) y decirlo en la fuente.
- Cuaderno `scripts/sar/agua_superficial.ipynb` adaptado del tutorial: umbral de retrodispersión → máscara de agua → superficie en km² por fecha.
- Presentarlo como caso de demostración: el registro de RCM empieza en 2019 y es corto para una tendencia. Encaja con la observación del enunciado de que una serie más larga puede volver significativa una tendencia.
- La página de ecosistemas de la CSA fundamenta la categoría *Ecosystems* (vegetación, humedales, agua) en las preguntas guiadas.

### 3.9 SWOT (#11)
- Localizar el `lake_id` de Cocibolca y Xolotlán en la Prior Lake Database y completar `fuentes/lagos.py` con Hydrocron.
- Serie de altura de agua desde 2023 junto a la superficie de agua del radar (#9) y, si responde, la serie larga de G-REALM.
- Mismo tratamiento de registro corto que el radar.

### 3.10 Geo.ca: caso de contraste en Canadá (#10)
- Elegir una región canadiense con datos IMERG de calidad (al sur de 60° N), p. ej. una ecozona de las praderas. Polígono de Geo.ca.
- Correr el mismo flujo: IMERG, GISTEMP y NDVI por AppEEARS. Mostrar cómo una variable puede ir en direcciones distintas en dos regiones, que es el punto central del enunciado.
- Integrar como segundo ejemplo de demostración, separado del caso principal de Nicaragua.

## 4. Cambios en la interfaz

1. **Preguntas guiadas** («What do you want to investigate?» / «Where?»): categorías Rain, Temperature, Vegetation & ecosystems, Water bodies, Air quality, Coast & ocean; regiones de Nicaragua y el caso de Canadá.
2. **Tarjetas de variable** con fuente, producto, versión, periodo y enlace al recurso.
3. **Panel Cross-checks:** Giovanni, KNMI y estaciones NOAA junto al resultado principal.
4. **Learn:** glosario y explicación de la prueba (#7, #8, #5).
5. **Sources:** los 13 recursos citados con licencia o condiciones.
6. Dos **demostraciones guiadas**: lluvia en el Pacífico de Nicaragua y contraste Nicaragua–Canadá.

## 5. Orden y calendario

| Cuándo | Trabajo |
|---|---|
| 13-11 | Crear o comprobar credenciales: Earthdata Login (Giovanni, AppEEARS, data rods, Sentinel-1), token NOAA CDO, cuenta EODMS. Leer las guías de entrega y evaluación. Leer #5, #7 y #8. |
| 14-11 mañana | Fase A, datos núcleo: AppEEARS (#3), contraste Giovanni (#1), SWOT (#11), NOAA (#4). |
| 14-11 tarde | Fase B, ampliaciones: variables Giovanni nuevas, GLDAS (#2), KNMI (#6), caso Canadá (#10), radar (#9, #13). |
| 15-11 mañana | Interfaz: preguntas guiadas, Cross-checks, Learn, Sources. |
| 15-11 tarde | Pruebas, prueba con una persona ajena, demo y entrega antes de las 23:59. |

Si el tiempo no alcanza, se mantiene el orden de la fase A. Un recurso sin datos se presenta como procedimiento documentado, sin cifras inventadas.

## 6. Verificación

- Prueba unitaria por adaptador con datos sintéticos y una prueba con datos reales en caché.
- `verificar_clima.py` sigue en 80/80: el contrato 1.0.0 no cambia.
- Pruebas E2E ampliadas a las pestañas y variables nuevas, con descarga de CSV cotejada con los JSON.
- Cada cifra de contraste anotada en `docs/auditoria.md` con fecha, versión y URL.

## 7. Riesgos

- **Credenciales:** casi la mitad del plan depende de Earthdata Login. Sin `_netrc` y token, las fases A y B se quedan en descargas manuales.
- **Volumen y tiempo:** las tareas de AppEEARS pueden tardar horas; lanzarlas primero.
- **Comparaciones múltiples:** más variables aumentan los falsos positivos; aplicar FDR a todo el conjunto.
- **Registros cortos** (SWOT, RCM, SMAP): no presentarlos como tendencias.
- **Bases de Canadá y radar:** confirmar licencias (Open Government Licence – Canada) y citar.
- **Normas del evento:** registrar qué se hace durante el evento y declarar el uso de herramientas de IA.
