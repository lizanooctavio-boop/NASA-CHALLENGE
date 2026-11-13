# Recursos de tierra: AppEEARS y Hydrology Time Series

Rama: `codex/recursos-tierra`, base `codex/demo-render` (`544756a`). Actualización de navegador: 13 de noviembre de 2026, America/Managua. No se modifican los adaptadores existentes, la estadística, los datos fuente ni la demo de Render.

## Estado de entrega

**GLDAS completado: 360/360 bloques anuales válidos, 1 051 920 observaciones de tres horas, 15 series mensuales y 15 anuales de punto, 2001–2024.** Cada serie tiene 288 meses y 24 años completos, sin faltantes. Se guardan las URLs públicas y SHA-256 de los 360 CSV en `procedencia_gldas.json`; los crudos permanecen en caché ignorada. La descarga validó el año completo, cadencia, duplicados, unidades (`unit` del CSV) y las conversiones descritas abajo.

**AppEEARS: las 160 solicitudes de área reales siguen enviadas, sin duplicarlas (150 Nicaragua y 10 Canadá).** `estado_appeears.json` guarda el último inventario leído de las dos páginas: una terminada, tres procesándose y 156 pendientes. El pedido NIC SMAP 2015 terminó el 13 de noviembre a las 06:27:58 CST, tras **6 h 37 min 24 s** desde el envío; este intervalo incluye cola y procesamiento, cuyos tiempos separados no están disponibles. Contiene 8832 GeoTIFF (70.34 MB según la web). Los recibos originales se conservan en `tareas_navegador.json`. No se extrapola una ETA para los otros pedidos.

La descarga web por lote permaneció en 0/8832; una descarga individual tampoco produjo archivo. La lista de URLs sí se descargó; su primer enlace sin autenticación devolvió HTTP 403. Hace falta un token **AppEEARS**, distinto de Earthdata Bearer, para usar el adaptador y descargar los resultados ya preparados. No se extraen cookies ni credenciales ocultas del navegador. **La aceptación científica permanece abierta** para los productos AppEEARS, el NDVI estable y el contraste con SMAP.

| Requisito | Resultado verificable | Pendiente |
|---|---|---|
| Áreas AppEEARS | Cinco productos, 160 tareas aceptadas, recibos registrados sin duplicados, primer bundle terminado | Terminar cola NASA, descargar y validar los rasters con token AppEEARS |
| NDVI regional y cobertura estable | Media de área, cohorte fija multianual y QA probados | Series reales y diferencia frente a sitios ORNL |
| Canadá | Diez tareas NDVI/LST enviadas con geometría exacta del agente 3 | Completar y descargar |
| GLDAS de punto | 360 años descargados, 15 series mensuales y anuales completas | Cotejo científico del agente 4 |
| Contraste de humedad | Seis correlaciones GLDAS–MERRA-2 calculadas | SMAP real pendiente de descarga |
| Estadística | 38 análisis: 23 referencias y 15 series GLDAS con funciones existentes | Añadir AppEEARS cuando haya datos |

## Acceso y evidencia de los servicios

AppEEARS admite tareas de **área** con polígonos GeoJSON y autenticación propia mediante `POST /login` con credenciales Earthdata. El token devuelto por AppEEARS es distinto del token generado en el perfil Earthdata. Véase la [API oficial](https://appeears.earthdatacloud.nasa.gov/api/). Los JSON `catalogo_*.json` y `calidad_*.json` guardan las respuestas públicas verificadas en esta ejecución, incluidas las capas exactas y metadatos de escala/relleno.

El endpoint histórico `https://hydro1.gesdisc.eosdis.nasa.gov/daac-bin/access/timeseries.cgi` **no entrega una serie en la prueba realizada**: redirige a una página HTML de aviso de retirada del servicio y termina con HTTP 200. No se considera una descarga válida. El aviso se corrobora en la [guía de migración de NASA](https://github.com/nasa/gesdisc-tutorials/blob/main/user-guidance/GES_DISC_Migration_to_Earthdata_Website_and_Earthdata_Cloud.md). La API de series de punto recomendada por el equipo GES DISC es `https://api.giovanni.earthdata.nasa.gov/timeseries`; el [ejemplo oficial de soporte](https://forum.earthdata.nasa.gov/viewtopic.php?t=7938) explica la consulta. El catálogo público `configured-variables` ofrece las cinco variables solicitadas para `GLDAS_NOAH025_3H_2_1`. El sondeo de un día en León devuelve HTTP 403, cuerpo `Bad or missing token`. Requiere Earthdata Bearer.

`gldas_datarods.py` usa ese sustituto, conserva la trazabilidad del cambio y rechaza HTML/JSON de error incluso con HTTP 200. No fabrica URLs al archivo antiguo ni sustituye GLDAS por otro modelo.

Prueba posterior con el navegador y un token creado con autorización del usuario: GES DISC muestra `Hi, Manuel`; cambiar el punto a León (12.45, −86.85) produce `Failed to fetch subset job link contents:`. El gráfico conservaba el punto anterior (36.61, −80.24): **no se exportó ni se trató como dato de Nicaragua**. También apareció el aviso de cinco intentos fallidos de renovación de sesión. Tras recargar y volver a consultar León se reprodujo el error. `hydrology_error.jpg` conserva evidencia de la interfaz.

Los errores iniciales HTTP 500 en `/timeseries` y 401 en `/quota` quedaron **resueltos** después de que el usuario autorizara y aceptara el EULA de **NASA GESDISC DATA ARCHIVE** en Earthdata. La interfaz confirmó la aplicación autorizada (`archivo_gldas_autorizado.jpg`). El mismo token Earthdata pasó a devolver HTTP 200 para cuota y CSV de series; no fue necesario regenerarlo. El token se usó solo en memoria durante la descarga; la transferencia temporal fuera del repositorio se eliminó al leerla. Nunca se añade al código, procedencia, datos o configuración permanente.

La descarga real utilizó tres solicitudes simultáneas como máximo y caché por año. Los 360 bloques terminaron sin errores. Una primera consulta de prueba devolvió 24.553 kg/m² de humedad 0–10 cm en León el 2024-01-01 00:00 UTC (0.24553 m³/m³ tras convertir); se distingue de la extracción completa. El procedimiento reproducible sigue siendo el CLI `gldas_datarods` con Earthdata token y el EULA ya aceptado.

## Preparación y credenciales

Desde la raíz del repositorio, en PowerShell:

```powershell
python -m venv backend/.cache/tierra-venv
backend/.cache/tierra-venv/Scripts/python.exe -m pip install -r backend/requirements.txt -r data/recursos/tierra/requirements.txt
$env:PYTHONPATH = 'backend'
```

La caché y el entorno quedan en `backend/.cache/`, excluido por `backend/.gitignore`. El núcleo requiere NumPy, SciPy, Shapely y pyproj; Rasterio es necesario para leer/reproyectar GeoTIFF de AppEEARS. La descarga usa la biblioteca estándar de Python.

Crear o iniciar sesión en [Earthdata Login](https://urs.earthdata.nasa.gov/). Entrar también en [AppEEARS](https://appeears.earthdatacloud.nasa.gov/login) y completar la autorización solicitada. Para las aplicaciones de GES DISC, completar la autorización de NASA GESDISC DATA ARCHIVE si la cuenta la solicita.

Dos opciones de configuración local:

1. Un archivo `.netrc` o `_netrc` en el directorio personal (o una ruta indicada por `NETRC`) con la entrada `machine urs.earthdata.nasa.gov login TU_USUARIO password TU_CONTRASEÑA`. Ambos adaptadores leen ese archivo y solicitan sus respectivos tokens en memoria. No se imprime ni se versiona el archivo ni los tokens. No utilizar una cuenta federada sin contraseña de API válida como si tuviera credenciales Basic.
2. Variables `APPEEARS_TOKEN` y `EARTHDATA_TOKEN`. El primero procede de `POST https://appeears.earthdatacloud.nasa.gov/api/login`; el segundo de **Generate Token** en el perfil Earthdata ([guía oficial](https://urs.earthdata.nasa.gov/documentation/for_users/user_token)). También se admiten `APPEEARS_TOKEN_FILE` y `EARTHDATA_TOKEN_FILE`, rutas a archivos locales que contienen solo el token correspondiente. No guardar esos archivos en el repositorio. Un token Earthdata no se puede usar como token AppEEARS.

Las variables configuradas en otra terminal no aparecen automáticamente en un proceso ya abierto: usar archivos/netrc o reiniciar el proceso con las variables correctas. `disponible()` comprueba presencia local, no demuestra autorización remota. Los errores HTTP 401/403 piden renovar el token/revisar la autorización y conservan las descargas previas. Nunca pegar secretos en un issue, PR o chat.

## Ejecutar las peticiones largas primero

```powershell
# No hace peticiones autenticadas: manifiesto compacto con huella de las geometrías.
backend/.cache/tierra-venv/Scripts/python.exe -m clima_nic.fuentes.appeears plan
# Enviar antes de esperar; guarda los task_id en caché después de cada aceptación.
backend/.cache/tierra-venv/Scripts/python.exe -m clima_nic.fuentes.appeears enviar
# Puede ejecutarse mientras AppEEARS procesa sus tareas:
backend/.cache/tierra-venv/Scripts/python.exe -m clima_nic.fuentes.gldas_datarods --inicio 2001 --fin 2024
# Reutilizar las tareas, esperar, descargar y agregar. Repetir tras un timeout.
backend/.cache/tierra-venv/Scripts/python.exe -m clima_nic.fuentes.appeears procesar --max-segundos 3600
backend/.cache/tierra-venv/Scripts/python.exe data/recursos/tierra/resumir.py
```

El plan Nicaragua contiene 150 tareas de área: cinco polígonos originales (`NIC`, `pacifico`, `central`, `caribe`, `caja_sicc`); SMAP en bloques anuales 2015–2024 (desde el 31 de marzo de 2015), y los otros productos en bloques de hasta cinco años 2001–2024. Orden de envío: SMAP, ET, LST, NDVI, cobertura. La prioridad se basa en cadencia/resolución y volumen esperado, **no en duraciones medidas**. La disponibilidad histórica exacta y los límites/cuotas de la cuenta deben validarse al enviar. Si AppEEARS rechaza el volumen/número de peticiones, las ya aceptadas quedan en caché; no se deben borrar ni volver a crear desde cero. Se puede trabajar con `plan()`/`enviar()` sobre un subconjunto de tareas y procesarlo después. Una tarea con estado `done` pero vacía produce un error, no una serie ficticia.

Las 160 solicitudes ya se enviaron mediante **Upload a request file** de la web y se cotejaron por nombre, ID y total del inventario. No ejecutar envíos nuevos desde un clon sin importar antes los recibos:

```powershell
backend/.cache/tierra-venv/Scripts/python.exe -m clima_nic.fuentes.appeears registrar-navegador
backend/.cache/tierra-venv/Scripts/python.exe -m clima_nic.fuentes.appeears registrar-navegador --canada --geojson data/recursos/tierra/regiones_canada_agente3.geojson
```

Esta importación no usa red ni crea tareas. Valida nombre, UUID, duplicados y conflictos antes de escribir caché. Se comprobó de solo lectura que **160/160 payloads e IDs** coinciden entre plan, recibos UI y caché. Con esos registros, el adaptador utiliza los mismos IDs para esperar/descargar cuando disponga de acceso a la API. La sesión web no se convierte ni se copia a credenciales permanentes del CLI. Los botones de descarga de la web se pueden usar cuando NASA termine los pedidos.

Cada solicitud se identifica por SHA-256 del payload. La caché conserva solicitud, geometría, identificador y hora de envío; los archivos se añadirán cuando puedan descargarse. Tras completar, `procedencia_nicaragua.json` guarda fechas `created`, `updated`, `completed`, productos, periodos y SHA-256 de archivos.

Tiempos reales parciales: el primer pedido, SMAP NIC 2015, ID `5c1e5da0-a4a3-40d2-bda1-eee9dec63163`, se envió el 12 de noviembre a las 23:50:34 CST y estaba al 28% a las 00:30:48 CST del día 13: **40 min 14 s transcurridos desde el envío**. El siguiente estaba al 17%; los otros 158 seguían pendientes. Ese tiempo incluye espera y trabajo; no se conoce el comienzo exacto de procesamiento, ni la duración final. No extrapolar una ETA a partir del porcentaje. El primer tiempo completo de envío a finalización se documenta en el estado de entrega; los tiempos de cola y ejecución por separado siguen sin conocerse. `solicitudes_navegador.jpg` acredita el total de 160 pedidos; los sondeos públicos y pruebas sintéticas no se usan como medidas de procesamiento.

Canadá: el archivo no está en la base `codex/demo-render`, pero ya existe en el [PR #7 del agente 3](https://github.com/lizanooctavio-boop/NASA-CHALLENGE/pull/7). Se guarda una copia exacta en `data/recursos/tierra/regiones_canada_agente3.geojson`: commit `ddad804318868dae8be71162f41678a574978e34`, SHA-256 `05e0f0dc1cf0a7c7476436028b5443812d44b9087fb5c0812e9ab588bbf4b402`. La procedencia está en `procedencia_geometria_canada.json`. Es la ecozona Prairies de AAFC, 467127.9 km² según sus metadatos; se conserva la atribución/licencia del agente 3. Las diez tareas de `plan_canada.json` (cinco bloques por producto) ya están aceptadas por AppEEARS y registradas en los recibos. Los siguientes comandos se conservan como referencia del flujo; **no reenviar desde una caché vacía**:

```powershell
backend/.cache/tierra-venv/Scripts/python.exe -m clima_nic.fuentes.appeears plan --canada --geojson data/recursos/tierra/regiones_canada_agente3.geojson
backend/.cache/tierra-venv/Scripts/python.exe -m clima_nic.fuentes.appeears enviar --canada --geojson data/recursos/tierra/regiones_canada_agente3.geojson
backend/.cache/tierra-venv/Scripts/python.exe -m clima_nic.fuentes.appeears procesar --canada --geojson data/recursos/tierra/regiones_canada_agente3.geojson
```

Cuando `data/regiones_canada.geojson` esté integrado, puede omitirse `--geojson`. No se utiliza una región canadiense inventada ni se modifica el archivo ajeno. Esa ejecución solicita NDVI/LST y produce sus medias regionales; no afirma cobertura estable porque el encargo de Canadá no pide MCD12Q1. Si se quiere esa comparación adicional, debe pedirse también MCD12Q1 para todos los años.

## Productos, calidad y agregación

| Producto | Capas de datos | Control aplicado |
|---|---|---|
| MOD13A3.061, NDVI mensual, 1 km | `_1_km_monthly_NDVI` | `VI_Quality`: MODLAND bueno, utilidad ≤2, aerosol no alto, sin nubes adyacentes/mixtas, nieve ni sombra, clase tierra; `pixel_reliability=0`; rango −0.2 a 1 |
| MOD11A2.061, LST diurna, 1 km/8 días | `LST_Day_1km` | `QC_Day`: MODLAND y datos buenos; error emisividad ≤0.02 y error LST ≤1 K; rango físico 150–400 K, luego °C |
| MOD16A2GF.061, ET, 500 m/8 días | `ET_500m` | `ET_QC_500m`: MODLAND bueno, detector operativo, cielo claro, algoritmo principal sin saturación; excluye rellenos/clases especiales y ET negativa |
| MCD12Q1.061, cobertura anual, 500 m | `LC_Type1` (IGBP) | `QC=0`, tierra clasificada; clases 1–16; excluye agua, relleno y clases reconstruidas/no clasificadas |
| SPL4SMGP.008, 9 km/3 h | `Geophysical_Data_sm_surface`, `Geophysical_Data_sm_rootzone` | No hay asociación de calidad en `/quality/SPL4SMGP.008` (HTTP 404) ni bitfield QA en el catálogo AppEEARS; rango 0–1, `soil_temp_layer1 > 273.15 K` y `<350 K`, `land_fraction_snow_covered=0` |

Los filtros MODIS son deliberadamente conservadores. SMAP L4 es un producto de asimilación, no una observación independiente de un sensor en cada fecha. El filtro físico no reproduce todos los controles de asimilación ni certifica ausencia de RFI, agua, relieve, vegetación densa u otros errores. Véase la [guía SMAP L4 v8](https://nsidc.org/sites/default/files/documents/user-guide/multi_spl4smau-v008-userguide.pdf). En particular, parte del producto depende de modelo/forzamientos y no constituye validación independiente de otros modelos.

El catálogo describe los valores físicos, pero los **GeoTIFF de área conservan valores empaquetados**. Rasterio lee esos valores sin aplicar automáticamente la escala: se aplican `Scale`/`Offset` de la banda una sola vez (o `scale_factor`/`add_offset` de sus etiquetas si no hay atributos de banda). Un TIFF científico entero sin escala produce error en vez de una conversión adivinada. Los float físicos con escala 1 se conservan. Esta diferencia respecto al CSV está confirmada por [LP DAAC](https://forum.earthdata.nasa.gov/viewtopic.php?t=3934). Se lee `nodata` antes de escalar. Para QA no se escala y se conserva el cero válido aunque el GeoTIFF declare `nodata=0`, pues cero significa buena calidad en varias capas.

La media espacial pondera la **intersección** de cada celda y polígono en EPSG:6933, incluyendo bordes parciales y huecos de los polígonos. Se requiere al menos 50% del área con dato válido por compuesto. Los registros guardan esa fracción para auditar cambios de muestreo. La composición temporal pondera los días/horas que se solapan con cada mes: no asigna un compuesto de ocho días entero al mes de su fecha. ET es una acumulación repartida proporcionalmente a su duración, incluidos los 5/6 días del último compuesto del año; no una media de acumulados. Para SMAP, la hora del nombre es el centro del intervalo: 01:30 representa 00:00–03:00. Las medias mensuales exigen ≥90% de cobertura temporal; las sumas de ET exigen 100%, sin extrapolación de huecos. Los años exigen 12 meses válidos. Se rechazan compuestos duplicados o intervalos solapados.

NDVI estable: todos los años del periodo deben tener MCD12Q1 y QA válidos. La clase de cada píxel 500 m debe permanecer constante. Al pasar a la malla NDVI de 1 km se exigen todos los subpíxeles estables y una misma clase, usando mínimos/máximos categóricos, sin interpolación bilineal ni rellenar años ausentes. Se fija la cohorte para todo el periodo, y se entrega `ndvi_regional` y `ndvi_cobertura_estable`. Se registra la fracción de área de la cohorte. El filtro es más estricto que seleccionar el píxel 500 m más cercano. QA NDVI puede dejar muestras válidas distintas dentro de la cohorte fija en cada fecha; se conserva la fracción válida. Cobertura estable no elimina cambios de manejo agrícola, incendios o degradación dentro de una misma clase.

## GLDAS: puntos y unidades

Los tres puntos son el primer sitio existente de cada región en `fuentes/modis.py:SITIOS`, sin modificarlo:

| Región | Sitio | Latitud | Longitud |
|---|---|---:|---:|
| pacifico | leon_llanura | 12.45 | −86.85 |
| central | esteli_corredor_seco | 13.10 | −86.35 |
| caribe | siuna_bosque | 13.75 | −84.80 |

**Son series de punto/celda de 0.25°, no medias de las regiones ni de NIC.** Giovanni devuelve la celda seleccionada y sus coordenadas en los metadatos, que se conservan en las notas. Consulta por año, con `location=[lat,lon]` (orden distinto del WKT del servicio antiguo). [Variables GLDAS-2.1 Noah](https://disc.gsfc.nasa.gov/datasets/GLDAS_NOAH025_3H_2.1/summary).

| Variable original | Salida | Conversión |
|---|---|---|
| `SoilMoi0_10cm_inst` | `humedad_gldas_0_10`, m³/m³ | kg/m² ÷ 100 (agua, espesor 0.10 m) |
| `SoilMoi10_40cm_inst` | `humedad_gldas_10_40`, m³/m³ | kg/m² ÷ 300 (espesor 0.30 m) |
| `Evap_tavg` | `et_gldas`, mm/mes | tasa kg/m²/s × 10800 s por paso, suma |
| `Qs_acc` | `escorrentia_superficial_gldas`, mm/mes | acumulado kg/m² por paso de 3 h, suma |
| `Qsb_acc` | `escorrentia_subterranea_gldas`, mm/mes | acumulado kg/m² por paso de 3 h, suma |

`undef` y valores no finitos quedan ausentes. Humedad fuera de 0–1 y escorrentía negativa se excluyen; ET conserva posibles flujos negativos de condensación. Se exigen todos los pasos de tres horas por mes y 12 meses por año. Sin extrapolación ni interpolación. No hay una QA de observación de suelo para estos campos modelados. El código comprueba cadencia, duplicados y bloques solapados antes de agregar.

## Formato y contraste para el agente 4

Las salidas `series_appeears_nicaragua_mensual.json`, `series_appeears_nicaragua_anual.json`, `series_gldas_mensual.json`, `series_gldas_anual.json` y sus variantes de Canadá son listas de `SerieRegional.como_dict()` (`region`, `variable`, `unidad`, `frecuencia`, `tiempos`, `valores`, `fuente`, `version`, `notas`), con faltantes JSON `null`. Los crudos nunca se copian a `data/`. Los adaptadores se importan directamente desde sus módulos; no se modifica el registro compartido de fuentes por la división de archivos de este encargo.

`data/recursos/tierra/resumir.py` importa `estadistica/tendencia_robusta.analizar` y escribe `analisis.json` con Sen, IC95%, MK modificado, MCO/HAC, Pettitt, veredicto y huellas SHA-256 de entradas. `tabla_analisis.md` contiene 38 filas (23 referencias y 15 GLDAS). También busca las nuevas salidas y calcula automáticamente diferencias NDVI regional/estable/sitio y correlaciones mensuales de humedad sobre fechas comunes. No resta índices MERRA-2 de humedad volumétrica. Las correlaciones incluyen estacionalidad/autocorrelación y se rotulan descriptivas, sin inferencia de validación o causalidad. GLDAS 0–10 cm, SMAP superficial ~0–5 cm, GLDAS 10–40 cm y SMAP raíz ~0–100 cm representan profundidades distintas. GWETTOP/GWETROOT de POWER/MERRA-2 son índices relativos 0–1, no m³/m³.

Resultados de **referencia existente**, pendientes de contrastar con nuevas series:

| Referencia | Periodo | Sen por década | Veredicto robusto |
|---|---|---:|---|
| NDVI sitio Pacífico | 2000–2024 | +0.0076 | evidencia_insuficiente |
| NDVI sitio Central | 2000–2024 | −0.0438 | tendencia_detectada |
| NDVI sitio Caribe | 2000–2024 | +0.0009 | evidencia_insuficiente |
| GWETTOP Pacífico | 2015–2024 | +0.1191 | evidencia_insuficiente |
| GWETROOT Pacífico | 2015–2024 | +0.0878 | evidencia_insuficiente |
| GWETTOP Central | 2015–2024 | +0.1054 | evidencia_insuficiente |
| GWETROOT Central | 2015–2024 | +0.0711 | evidencia_insuficiente |
| GWETTOP Caribe | 2015–2024 | +0.0387 | evidencia_insuficiente |
| GWETROOT Caribe | 2015–2024 | +0.0335 | evidencia_insuficiente |

NDVI es adimensional; GWET son unidades de índice por década. La referencia NDVI replica la media mensual de los sitios preexistentes y el umbral anual ≥10 meses de `modis.py` (2000 es parcial); las nuevas series anuales requieren 12. La extracción ORNL original rápida no incluía QA de fiabilidad, por lo que una diferencia con el área filtrada también puede reflejar calidad, resolución, compositado y muestreo. No atribuir por sí sola la caída NDVI Central al clima.

En el periodo completo 1981–2024, GWETTOP/GWETROOT arrojan `tendencia_detectada` en todas las regiones existentes; por ejemplo NIC: +0.0572 y +0.0425 por década. En 2015–2024, las cinco regiones existentes arrojan `evidencia_insuficiente`. Es una descripción del reanálisis y de la dependencia de la ventana, no un hallazgo climático validado: MERRA-2 tiene discontinuidades ya documentadas en el proyecto. Para SMAP, 2015 es parcial, así que una serie anual estricta hasta 2024 puede tener solo 9 años y devolver `datos_insuficientes`; no se amplía artificialmente la muestra.

## Resultados GLDAS reales y contraste descriptivo

Las pendientes usan 24 años completos (2001–2024), la misma función `estadistica/tendencia_robusta.analizar` existente y sin modificarla. Humedad en m³/m³ por década; ET y escorrentía en mm/año por década. `metodos_discrepan` se conserva como veredicto del código y no se presenta como una tendencia confirmada.

| Región | Variable | Periodo | Sen / década | Veredicto |
|---|---|---|---:|---|
| caribe | et_gldas | [2001, 2024] | 56.5239 | metodos_discrepan |
| caribe | escorrentia_superficial_gldas | [2001, 2024] | 8.3067 | metodos_discrepan |
| caribe | escorrentia_subterranea_gldas | [2001, 2024] | -50.6151 | evidencia_insuficiente |
| caribe | humedad_gldas_0_10 | [2001, 2024] | -0.0031 | metodos_discrepan |
| caribe | humedad_gldas_10_40 | [2001, 2024] | -0.0039 | metodos_discrepan |
| central | et_gldas | [2001, 2024] | 0.1206 | evidencia_insuficiente |
| central | escorrentia_superficial_gldas | [2001, 2024] | -1.9013 | evidencia_insuficiente |
| central | escorrentia_subterranea_gldas | [2001, 2024] | -51.6736 | evidencia_insuficiente |
| central | humedad_gldas_0_10 | [2001, 2024] | -0.0027 | evidencia_insuficiente |
| central | humedad_gldas_10_40 | [2001, 2024] | -0.0047 | evidencia_insuficiente |
| pacifico | et_gldas | [2001, 2024] | 26.0469 | evidencia_insuficiente |
| pacifico | escorrentia_superficial_gldas | [2001, 2024] | -0.2436 | evidencia_insuficiente |
| pacifico | escorrentia_subterranea_gldas | [2001, 2024] | 10.2921 | evidencia_insuficiente |
| pacifico | humedad_gldas_0_10 | [2001, 2024] | 0.0005 | evidencia_insuficiente |
| pacifico | humedad_gldas_10_40 | [2001, 2024] | 0.0023 | evidencia_insuficiente |

GLDAS frente a POWER/MERRA-2, correlación mensual descriptiva en 288 meses comunes (2001-01 a 2024-12):

| Región | GLDAS 0–10 cm vs GWETTOP | GLDAS 10–40 cm vs GWETROOT |
|---|---:|---:|
| Pacífico | 0.9414 | 0.8874 |
| Central | 0.8446 | 0.7705 |
| Caribe | 0.8760 | 0.8343 |

La coincidencia incluye el ciclo estacional y autocorrelación, mezcla un punto GLDAS con agregados MERRA-2 y compara profundidades distintas. GWET es un índice relativo, por lo que no se calcula una diferencia en m³/m³. Estas correlaciones no validan independencia, exactitud ni causalidad climática. El contraste GLDAS–SMAP permanece pendiente; no se sustituye por el CSV de estadísticas del bundle ni por una serie parcial sin QA.

## Pruebas y límites de la verificación

```powershell
backend/.cache/tierra-venv/Scripts/python.exe -m pytest tests/test_recursos_tierra.py tests/test_indicadores_nicaragua.py -q
```

Resultado actualizado: `python -m pytest tests -q`: **82 passed, 1 skipped**. Se omite la prueba de la API web existente porque FastAPI/httpx son dependencias opcionales que no se instalaron en este entorno de verificación. Las 29 pruebas nuevas de tierra sí se ejecutan, incluida la importación de recibos UI sin reenviar ni sobrescribir un ID contradictorio.

Pruebas sin red ni credenciales: polígonos de área, Canadá con fixture, orden y reanudación del envío, estados vacío/error/timeout, QA de cinco productos, años de cobertura ausentes, cohortes cambiantes, lectura GeoTIFF física sin doble escala y empaquetada con escala, QA=0, peso de borde parcial, fechas subdiarias SMAP, reparto ET entre meses y fin de año, cadencia GLDAS, HTML/errores, datos faltantes y conversiones de humedad/ET/escorrentía. No demuestran aceptación remota de tareas, duración, integridad de datos NASA reales ni permisos de la cuenta.

Verificación de esta actualización: **61 pruebas pasadas** (`tests/test_recursos_tierra.py` y `tests/test_indicadores_nicaragua.py`), 360 CSV reales validados y comprobación de 288 meses/24 años sin nulos en las 15 series. `resumir.py` produjo 38 análisis y seis contrastes.

Para cerrar la aceptación: esperar la terminación de las tareas AppEEARS **ya enviadas**, descargar todos los periodos con token AppEEARS, inspeccionar visualmente un raster por producto y QA, volver a ejecutar `resumir.py`, incorporar diferencias NDVI/contrastes SMAP y cotejarlas con el agente 4. No se fabrican series a partir de tareas pendientes o gráficos de otro punto. El PR permanece en borrador hasta entonces. La fusión y el despliegue siguen a cargo del responsable.
