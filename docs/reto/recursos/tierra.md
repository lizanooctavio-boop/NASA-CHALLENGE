# Recursos de tierra: AppEEARS y Hydrology Time Series

Rama: `codex/recursos-tierra-v2`, rehecha sobre `codex/verificacion-entrega` con los dos commits propios de `codex/recursos-tierra` (sin el commit ajeno 544756a de `codex/demo-render`). Actualización de navegador: 13 de noviembre de 2026, America/Managua. No se modifican los adaptadores existentes, la estadística, los datos fuente ni la demo de Render.

## Estado de entrega

**160 solicitudes de área reales enviadas y cotejadas mediante la sesión del navegador: 150 de Nicaragua y 10 de Canadá.** Los recibos están en `data/recursos/tierra/tareas_navegador.json`, con identificadores, nombres, fechas y estados leídos de las dos páginas de Explore Requests. En la observación de `2026-11-13T06:30:48.277Z` (00:30:48 CST), había 158 pendientes y dos procesándose (17% y 28%); ninguna completada. La sesión AppEEARS está operativa: ya no falta iniciar sesión para tramitar los pedidos.

GLDAS sigue bloqueado: el visor autenticado no recupera el enlace del subconjunto; la API de series devuelve HTTP 500 y la comprobación de cuota rechaza con HTTP 401 el token generado en Earthdata. Se reproduce tras renovar la sesión. No hay todavía series regionales nuevas descargadas de AppEEARS ni GLDAS. Las cifras de tendencias de este documento son recálculos de las referencias existentes, no resultados de los pedidos pendientes. **La aceptación científica permanece abierta** hasta descargar y validar los bundles y resolver el acceso GLDAS.

| Requisito | Resultado verificable | Pendiente |
|---|---|---|
| Áreas AppEEARS | Adaptador; cinco productos; 150 solicitudes Nicaragua aceptadas por la web; 160 recibos incluyendo Canadá registrados en caché sin duplicados | NASA debe terminar de generar los bundles; descargar y validar |
| NDVI regional y cobertura estable | Media por área; cohorte fija multianual; QA y clase IGBP; prueba con cambio de cobertura | Valores reales y diferencia frente a los sitios ORNL |
| Canadá | Diez tareas NDVI/LST aceptadas por la web con la geometría exacta del agente 3 (PR #7) | Completar/descargar; no se fusiona el PR del agente 3 |
| GLDAS de punto | Catálogo y variables verificados; sesión web reconocida; intentos web y API con token Earthdata real documentados | Acceso que Giovanni acepte y recuperación del servicio; series aún no obtenidas |
| GLDAS regional (13-11) | 5 variables × 6 regiones, 2001–2024, medias ponderadas por área desde el OPeNDAP en la nube de GES DISC; balance hídrico cerrado (residuo medio de −1,5 a +1,6 % de la lluvia en 24 años) | Contrastar la humedad con SMAP (AppEEARS) y MERRA-2 antes de interpretar tendencias |
| Contraste de humedad | Referencias MERRA-2 recalculadas; comparador local listo | GLDAS y SMAP reales; no se inventan correlaciones |
| Estadística | 23 análisis de referencia con `estadistica/tendencia_robusta.py`, sin modificarla | Aplicar la misma función a las nuevas series cuando existan |

## Acceso y evidencia de los servicios

AppEEARS admite tareas de **área** con polígonos GeoJSON y autenticación propia mediante `POST /login` con credenciales Earthdata. El token devuelto por AppEEARS es distinto del token generado en el perfil Earthdata. Véase la [API oficial](https://appeears.earthdatacloud.nasa.gov/api/). Los JSON `catalogo_*.json` y `calidad_*.json` guardan las respuestas públicas verificadas en esta ejecución, incluidas las capas exactas y metadatos de escala/relleno.

El endpoint histórico `https://hydro1.gesdisc.eosdis.nasa.gov/daac-bin/access/timeseries.cgi` **no entrega una serie en la prueba realizada**: redirige a una página HTML de aviso de retirada del servicio y termina con HTTP 200. No se considera una descarga válida. El aviso se corrobora en la [guía de migración de NASA](https://github.com/nasa/gesdisc-tutorials/blob/main/user-guidance/GES_DISC_Migration_to_Earthdata_Website_and_Earthdata_Cloud.md). La API de series de punto recomendada por el equipo GES DISC es `https://api.giovanni.earthdata.nasa.gov/timeseries`; el [ejemplo oficial de soporte](https://forum.earthdata.nasa.gov/viewtopic.php?t=7938) explica la consulta. El catálogo público `configured-variables` ofrece las cinco variables solicitadas para `GLDAS_NOAH025_3H_2_1`. El sondeo de un día en León devuelve HTTP 403, cuerpo `Bad or missing token`. Requiere Earthdata Bearer.

`gldas_datarods.py` usa ese sustituto, conserva la trazabilidad del cambio y rechaza HTML/JSON de error incluso con HTTP 200. No fabrica URLs al archivo antiguo ni sustituye GLDAS por otro modelo.

Prueba posterior con el navegador y un token creado con autorización del usuario: GES DISC muestra la sesión iniciada; cambiar el punto a León (12.45, −86.85) produce `Failed to fetch subset job link contents:`. El gráfico conservaba el punto anterior (36.61, −80.24): **no se exportó ni se trató como dato de Nicaragua**. También apareció el aviso de cinco intentos fallidos de renovación de sesión. Tras recargar y volver a consultar León se reprodujo el error. `evidencia_tierra/hydrology_error.jpg` conserva evidencia de la interfaz (con el nombre del titular tapado).

La API `/timeseries` devolvió HTTP 500 `{"message":null}` para `SoilMoi0_10cm_inst` y `Evap_tavg` de tres horas y para humedad mensual, con y sin el parámetro de versión de API documentado. `/quota` devolvió HTTP 401 `Invalid bearer token`. Se comprobó que el token leído de la página estaba completo (704 caracteres, RS256, emisor Earthdata, sin elipsis); no se afirma que Giovanni lo acepte. No se almacenó en el repositorio ni en configuración permanente; la transferencia temporal se eliminó al leerla y se retiró de memoria al terminar su uso. Para continuar GLDAS hace falta una autenticación aceptada por Giovanni o resolver el fallo de su visor/API; no basta con ver una sesión iniciada en la web.

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

Tiempos reales parciales: el primer pedido, SMAP NIC 2015, ID `5c1e5da0-a4a3-40d2-bda1-eee9dec63163`, se envió el 12 de noviembre a las 23:50:34 CST y estaba al 28% a las 00:30:48 CST del día 13: **40 min 14 s transcurridos desde el envío**. El siguiente estaba al 17%; los otros 158 seguían pendientes. Ese tiempo incluye espera y trabajo; no se conoce el comienzo exacto de procesamiento, ni la duración final. No extrapolar una ETA a partir del porcentaje. Todavía no hay tiempos completos de cola/ejecución ni bundles finalizados. `evidencia_tierra/solicitudes_navegador.jpg` acredita el total de 160 pedidos; los sondeos públicos y pruebas sintéticas no se usan como medidas de procesamiento.

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

## GLDAS regional mensual desde GES DISC (13-11-2026)

Mientras Hydrology Time Series y la API de series de Giovanni sigan fallando, `backend/clima_nic/fuentes/gldas_mensual.py` obtiene el mismo modelo, GLDAS-2.1 Noah, en su producto mensual (`GLDAS_NOAH025_M` 2.1, colección CMR `C1342986036-GES_DISC`) desde el OPeNDAP en la nube de GES DISC. Recorta por índices la ventana de cada grupo de regiones, sin descargar el archivo global de 24 MB por mes. El OPeNDAP antiguo (`hydro1.gesdisc.eosdis.nasa.gov/opendap`) responde 410 y no se usa. El acceso usa Earthdata mediante `_netrc`, sin imprimir ni guardar credenciales. Las respuestas crudas quedan en `backend/.cache/gldas_mensual/`.

```powershell
cd backend
python -m clima_nic.fuentes.gldas_mensual --inicio 2001 --fin 2024
```

**Salidas.** `series_gldas_mensual.json` y `series_gldas_anual.json` (listas de `SerieRegional`) y `procedencia_gldas_mensual.json` (granulo y SHA-256 de cada respuesta, ventana de índices y balance hídrico de control). Regiones: `NIC`, `pacifico`, `central`, `caribe`, `caja_sicc` y `CAN_prairies`. A diferencia de las series de punto previstas, son **medias regionales** ponderadas por la intersección de cada celda de 0,25° con el polígono (EPSG:6933), con las celdas de agua del modelo excluidas y los pesos renormalizados.

**Conversiones** (README GLDAS-2, §3.5): las tasas `_tavg` se multiplican por 10 800 s × 8 × días del mes; los acumulados `_acc` (promedio de los acumulados de 3 h), por 8 × días del mes; la humedad, de kg m⁻² a m³/m³ dividiendo por 100 (0–10 cm) y por 300 (10–40 cm). Los años exigen los 12 meses. Humedad: media anual. Flujos: suma anual.

**Balance hídrico de control.** Lluvia del forzamiento − ET − escorrentía total, en promedio 2001–2024, deja un residuo medio de −1,5 a +1,6 % de la lluvia según la región. El residuo de cada año refleja cambios de almacenamiento: entre −11 % y +10 % en Nicaragua y entre −19 % y +18 % en las Praderas, donde también interviene la nieve.

**Corrección del 13-11 (meses repetidos).** El OPeNDAP en la nube de GES DISC respondió a veces con otro granulo: al pedir enero de 2001 devolvió junio de 2001. Así se repitieron 14 meses de Nicaragua (enero–junio de 2001, cuatro de 2002 y enero–junio de 2003) y 6 de Canadá, lo que explicaba el residuo anómalo que antes se atribuía a un ajuste inicial de 2001. Lo detectó el contraste con el servicio oficial de Giovanni (ver `contraste.md`). Ahora `gldas_mensual.descargar_mes` comprueba la línea `Dataset:` de cada respuesta, también en la caché, y reintenta si no coincide. Las 576 respuestas son distintas y la serie coincide con Giovanni (r = 1,000). La lluvia media del forzamiento en las Praderas (441 mm/año) es coherente con la de IMERG que calculó el agente 3 (435 mm/año).

**Tendencias preliminares** (Theil–Sen por década, `tendencia_robusta.analizar`):

| Región | Humedad 0–10 cm | ET | Escorrentía subterránea |
|---|---|---|---|
| NIC | −0,0044 m³/m³, métodos discrepan | +11,5 mm, evidencia insuficiente | −82,0 mm, métodos discrepan |
| Central | −0,0056 m³/m³, métodos discrepan | −2,3 mm, evidencia insuficiente | −58,6 mm, evidencia insuficiente |
| Praderas de Canadá | −0,0136 m³/m³, tendencia detectada | −25,3 mm, evidencia insuficiente | −0,26 mm, métodos discrepan |

Con la serie corregida, la humedad de Central deja de ser «tendencia detectada» (antes −0,0090 m³/m³ por década).

**Límites.** La prueba de Pettitt sitúa el cambio de la mayoría de las series de Nicaragua en 2011–2013. El README de GLDAS-2 advierte reescalados de la radiación AGRMET desde 2008 y un desplazamiento de origen desconocido después de 2011. Por eso, un descenso de humedad en Nicaragua puede ser un artefacto del forzamiento y no un cambio climático. Antes de interpretarlo hay que contrastar con SMAP (AppEEARS, desde 2015) y con la humedad de MERRA-2. La caída en las Praderas se mantiene sin 2001–2002 y es coherente con las sequías de la década, pero tampoco se ha contrastado. GLDAS es un modelo forzado con observaciones, no una medición.

**Contraste de humedad con MERRA-2** (`data/recursos/tierra/contrastar_humedad.py`, salidas `contrastes_tierra.json` y `contrastes_tierra_series.csv`). Se comparó GLDAS 0–10 cm con GWETTOP y GLDAS 10–40 cm con GWETROOT de MERRA-2 (vía NASA POWER, medias regionales ya existentes en el proyecto), 2001–2024. Como las unidades difieren (m³/m³ frente a un índice de saturación de 0 a 1), las series se comparan como anomalías estandarizadas y cada tendencia se calcula en sus propias unidades.

- La correlación anual entre ambos modelos es baja: r = 0,24 a 0,68 según la región y la capa.
- Las tendencias van en sentidos opuestos. MERRA-2 detecta humedecimiento en todas las regiones (GWETTOP en NIC +0,048 por década; media de 0,56 en 2001–2005 frente a 0,66 en 2020–2024). GLDAS da descenso (NIC −0,0044 m³/m³ por década, métodos discrepan).
- Cada modelo es coherente con su propia lluvia: la humedad anual de GLDAS se correlaciona con la lluvia de su forzamiento (r = 0,74 en NIC), y GWETTOP con la lluvia de MERRA-2 (r = 0,87–0,91). La lluvia de GLDAS y la de IMERG se correlacionan con r = 0,92 en NIC. La discrepancia viene de los forzamientos y de la física de cada modelo, no del procesado.

**Conclusión.** En Nicaragua, la tendencia de humedad del suelo depende del modelo y no se presenta como hallazgo climático. Dos modelos de NASA con forzamientos distintos discrepan incluso en el signo. La referencia observacional disponible es SMAP L4 desde 2015, pedida por AppEEARS; el mismo script añadirá ese contraste cuando existan sus series. En la interfaz, el contraste aparece en *Cross-checks* junto a cada serie de humedad de GLDAS. No hay MERRA-2 para las Praderas de Canadá en el proyecto, así que la caída de humedad allí sigue sin contraste.

**Recursos del reto.** Estas series proceden del archivo OPeNDAP de GES DISC. Giovanni (recurso 1) se usa para verificarlas: su promedio por área de GLDAS-2.1 en la caja SICC coincide con nuestra serie (contraste `giovanni_gldas_sm0_10_caja_sicc`). La herramienta Hydrology Time Series (recurso 2) aporta las series de punto descritas a continuación.

## GLDAS por punto: Hydrology Time Series (recurso 2) vía Giovanni

El servicio histórico de *data rods* (`hydro1.gesdisc.eosdis.nasa.gov/daac-bin/access/timeseries.cgi`) está retirado: devuelve una página de aviso. La [guía de migración de GES DISC](https://github.com/nasa/gesdisc-tutorials/blob/main/user-guidance/GES_DISC_Migration_to_Earthdata_Website_and_Earthdata_Cloud.md) remite a su sustituto, el servicio «Giovanni in the Cloud: Time Series» (`https://api.giovanni.earthdata.nasa.gov/timeseries`). Su uso está descrito en el cuaderno oficial `How_to_Access_GiC_Time_Series_Service.ipynb` (`nasa/gesdisc-tutorials`). El servicio da series de 3 h en un punto y exige un token Earthdata, además de haber aceptado el EULA de NASA GESDISC DATA ARCHIVE.

Manuel Paniagua descargó con `clima_nic.fuentes.gldas_datarods` las cinco variables en tres sitios: Siuna (Caribe), Estelí (corredor seco, Central) y León (llanura del Pacífico). Son 360 bloques anuales de 2001–2024, sin errores (`estado_descarga_gldas.json`; URL y SHA-256 de cada bloque en `procedencia_gldas.json`). Las salidas son `series_gldas_punto_mensual.json` y `series_gldas_punto_anual.json`, con nombre propio para no confundirse con las medias regionales. En la interfaz aparecen como «… at a sample point», con identificador `<variable>_punto_<región>`, y cuentan como uso de los recursos 2 y 1.

**Reproducibilidad (13-11).** Se pidieron de nuevo cuatro bloques al azar con un token nuevo y se agregaron con el mismo adaptador. Los 12 meses de cada bloque coinciden exactamente con las series guardadas. El SHA-256 del archivo completo no coincide porque la cabecera incluye `Request_time`, que cambia en cada petición.

## Formato y contraste para el agente 4

Las salidas `series_appeears_nicaragua_mensual.json`, `series_appeears_nicaragua_anual.json`, `series_gldas_mensual.json`, `series_gldas_anual.json` y sus variantes de Canadá son listas de `SerieRegional.como_dict()` (`region`, `variable`, `unidad`, `frecuencia`, `tiempos`, `valores`, `fuente`, `version`, `notas`), con faltantes JSON `null`. Los crudos nunca se copian a `data/`. Los adaptadores se importan directamente desde sus módulos; no se modifica el registro compartido de fuentes por la división de archivos de este encargo.

`data/recursos/tierra/resumir.py` importa `estadistica/tendencia_robusta.analizar` y escribe `analisis.json` con Sen, IC95%, MK modificado, MCO/HAC, Pettitt, veredicto y huellas SHA-256 de entradas. `tabla_analisis.md` contiene las 23 filas de referencia. También busca las nuevas salidas y calcula automáticamente diferencias NDVI regional/estable/sitio y correlaciones mensuales de humedad sobre fechas comunes. No resta índices MERRA-2 de humedad volumétrica. Las correlaciones incluyen estacionalidad/autocorrelación y se rotulan descriptivas, sin inferencia de validación o causalidad. GLDAS 0–10 cm, SMAP superficial ~0–5 cm, GLDAS 10–40 cm y SMAP raíz ~0–100 cm representan profundidades distintas. GWETTOP/GWETROOT de POWER/MERRA-2 son índices relativos 0–1, no m³/m³.

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

## Pruebas y límites de la verificación

```powershell
backend/.cache/tierra-venv/Scripts/python.exe -m pytest tests/test_recursos_tierra.py tests/test_indicadores_nicaragua.py -q
```

Resultado actualizado: `python -m pytest tests -q`: **82 passed, 1 skipped**. Se omite la prueba de la API web existente porque FastAPI/httpx son dependencias opcionales que no se instalaron en este entorno de verificación. Las 29 pruebas nuevas de tierra sí se ejecutan, incluida la importación de recibos UI sin reenviar ni sobrescribir un ID contradictorio.

Pruebas sin red ni credenciales: polígonos de área, Canadá con fixture, orden y reanudación del envío, estados vacío/error/timeout, QA de cinco productos, años de cobertura ausentes, cohortes cambiantes, lectura GeoTIFF física sin doble escala y empaquetada con escala, QA=0, peso de borde parcial, fechas subdiarias SMAP, reparto ET entre meses y fin de año, cadencia GLDAS, HTML/errores, datos faltantes y conversiones de humedad/ET/escorrentía. No demuestran aceptación remota de tareas, duración, integridad de datos NASA reales ni permisos de la cuenta.

Para cerrar la aceptación: esperar la terminación de las 160 tareas **ya enviadas**, descargar todos los periodos, inspeccionar visualmente un raster por producto y QA, obtener GLDAS con autenticación aceptada por el servicio, ejecutar `resumir.py`, incorporar cifras de diferencias/contrastes y cotejarlas con el agente 4. No se fabrican series a partir de tareas pendientes o gráficos de otro punto. El PR permanece en borrador hasta entonces. La fusión y el despliegue siguen a cargo del responsable.

## AppEEARS: procesar lo terminado sin esperar la cola (13-11-2026)

`python -m clima_nic.fuentes.appeears procesar-terminadas [--canada] [--hilos 4]` lee los identificadores de `tareas_*.json`, consulta el estado de cada tarea y descarga y procesa solo las terminadas. **Nunca envía tareas**, a diferencia de `procesar`, que reenvía cuando falta la caché de registros. La API responde HTTP 429 si se piden demasiados archivos a la vez; ante 429 o 503, `AppEEARS.api` espera (`Retry-After` o espera creciente) y reintenta. Cada tarea SMAP de un año tiene unos 8800 GeoTIFF de 3 h, así que su descarga tarda horas. Al consultar a las 22:00 del 13-11 había 4 tareas terminadas (SMAP de NIC, 2015–2018), 2 en proceso y 154 pendientes.
