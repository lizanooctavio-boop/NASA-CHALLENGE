# Cuencas, lecturas hidrológicas y fuentes climáticas

## Qué se incorpora al mapa

La pestaña **Watersheds** carga vectores descargados directamente de ArcGIS REST y HydroSHEDS. No se rasterizó, calcó ni vectorizó ningún PDF. Permite elegir región y nivel, consultar polígonos, buscar códigos sin recortarlos, activar etiquetas de códigos y exportar la selección completa como GeoJSON o CSV. Las etiquetas permanentes se limitan a 150 visibles para evitar saturación; esa restricción no elimina unidades ni acorta códigos.

Se añaden lecturas de estaciones de INETER, diez accesos directos a mapas nacionales de referencia, el catálogo WFS de meteorología/hidrología/amenazas naturales de INETER y las capas naturales identificadas en el visor SINAPRED compartido. Las capas administrativas, escuelas, hospitales y carreteras se excluyen de este inventario climático.

Las 217 investigaciones estadísticas ya presentes en la base de esta rama se conservan sin cambios. Un mapa de amenaza, una normal climatológica o una lectura de estación no se convierte en una serie anual ni recibe un veredicto de tendencia. La clasificación de eventos, modelos, reanálisis y observaciones que ya utiliza la app se conserva.

## Nicaragua: fuente nacional encontrada y diferencias con 2014

- Visor compartido por el usuario: [SINAPRED, mapa interactivo 2024](https://www.arcgis.com/home/item.html?id=99d7faca90ef4bde9c053e67dabc3006). Su configuración se obtiene por [REST](https://www.arcgis.com/sharing/rest/content/items/99d7faca90ef4bde9c053e67dabc3006/data?f=pjson).
- La capa de cuencas se encontró buscando en el catálogo de la misma cuenta `crmendez_SINAPRED`: [Cuencas PFAFSTETTER_NIC](https://www.arcgis.com/home/item.html?id=a367394491e5470c89ab165525c4c246).
- [Servicio vectorial original](https://services3.arcgis.com/gcPaotyuZyboHMjH/arcgis/rest/services/Cuencas_PFAFSTETTER_NIC/FeatureServer/0). Consulta pública sin cuenta, sin ArcGIS Pro y sin token. La descripción declara elaboración en **noviembre de 2021**, escala **1:750.000** y “nivel 7”.
- La misma edición aparece en INETER WFS como `wsINETER-DGRH:Cuencas_nivel7_2021`, con 2.337 entidades. No se trata de una certificación de equivalencia geométrica con el atlas de 2014.
- El [álbum de 2014 alojado por CIRA/UNAN](https://cira.unan.edu.ni/wp-content/uploads/2016/07/Album-Cuencas-Nic-Revisado_ANA.pdf) sirve como referencia histórica, **no** como fuente de geometrías. Las condiciones editoriales del álbum no se confunden con una licencia de datos vectoriales.
- [INETER documentó una actualización de unidades en 2022](https://aplicacion.ineter.gob.ni/intranet/Noticia/View/391). Una edición posterior no debe presentarse como el mapa exacto de 2014.

Se descargaron **2.337 entidades** por sus identificadores originales, en lotes comprobados contra la lista completa de `objectIds`. Se conservan `FID`, `GmlID`, `OBJECTID_1`, `n3`–`n7`, `phca`, `code_pfafs`, `cuencas` y los atributos geométricos originales. `phca` pertenece a la codificación histórica y no se usa como código Pfafstetter.

`codigo_completo` es una representación textual, sin redondeo ni notación científica, del campo publicado `code_pfafs`. También se conservan los componentes originales. **44 entidades discrepan** entre `code_pfafs` y la concatenación de `n3`–`n7`: no se decide cuál es correcto ni se corrige el original. Ejemplo comprobable: `FID=2`, código publicado `9519581`, componentes `951` + `9` + `5` + `8` + `7` = `9519587`.

La capa titulada “nivel 7” contiene **2.250 códigos de siete dígitos, 86 de seis y uno de tres**. No se rellenan con ceros los niveles ausentes. Las partes vacías permanecen vacías en el CSV. La ficha del mapa advierte de esta mezcla. Para resolver discrepancias o exigir la edición exacta de 2014 se requiere una fuente oficial que publique esa edición; no se inventa una correspondencia.

## Cobertura mundial: fuente original y códigos independientes

[HydroBASINS v1c](https://www.hydrosheds.org/products/hydrobasins) proporciona vectores originales, doce niveles Pfafstetter y nueve regiones. No requiere cuenta. La cobertura excluye la Antártida; algunos territorios insulares o de alta latitud tienen limitaciones documentadas por el proveedor. Oceanía corresponde a la región distribuida por HydroBASINS, sin garantía añadida de cobertura de cada isla pequeña.

Los **19 archivos web** son un vector nacional y dos niveles para cada una de las nueve regiones. Se comprimen con gzip sin pérdida de atributos; el navegador los descomprime para dibujar. Los archivos SHP/ZIP originales se descargaron a una caché externa, con SHA-256 y recibos. Los ZIP completos de nivel 12 contienen **1.034.083 entidades**; se ofrecen sus enlaces directos por región, sin subir cientos de megabytes de originales al repositorio. El mapa web muestra los niveles **4 y 6**, no los polígonos de nivel 12. Elegir mayor detalle requiere abrir/descargar el original, no ampliar artificialmente el nivel 6.

| Región original | Nivel 4 en el mapa | Nivel 6 en el mapa | Nivel 12 en el ZIP original |
|---|---:|---:|---:|
| África (`af`) | 251 | 3597 | 230028 |
| Ártico norteamericano (`ar`) | 68 | 849 | 46882 |
| Asia (`as`) | 199 | 2489 | 160508 |
| Australia y Oceanía (`au`) | 143 | 1425 | 83929 |
| Europa y Oriente Medio (`eu`) | 240 | 2240 | 137658 |
| Groenlandia (`gr`) | 37 | 302 | 16990 |
| Norteamérica, Centroamérica y Caribe (`na`) | 185 | 2043 | 122251 |
| Sudamérica (`sa`) | 147 | 1946 | 136157 |
| Siberia (`si`) | 72 | 1506 | 99680 |
| **Total** | **1342** | **16397** | **1034083** |

URL directa, sustituyendo `<región>` por uno de los códigos de la tabla y `<nivel>` por `04`, `06` o `12`:

`https://data.hydrosheds.org/file/hydrobasins/standard/hybas_<región>_lev<nivel>_v1c.zip`

La tabla oficial de descargas también publica niveles 1–12 y paquetes combinados. El inventario procede del árbol de descargas enlazado por el propio sitio del productor; no de copias de terceros.

Se conservan `PFAF_ID` (código Pfafstetter), `HYBAS_ID` (identificador de diez dígitos), `NEXT_DOWN`, `NEXT_SINK`, `MAIN_BAS`, área y otros atributos originales. Los identificadores se convierten a cadenas enteras completas. **HYBAS_ID no es PFAF_ID.** La jerarquía nacional de Nicaragua y la global de HydroBASINS usan convenciones distintas; no se unen solo por prefijo ni se afirma que `951…` equivalga a un código global.

Los vectores web simplifican cada geometría conservando su topología local: tolerancia 0,0002° en Nicaragua, 0,01° en nivel 4 y 0,003° en nivel 6 global; coordenadas redondeadas a cinco decimales. No se eliminan entidades. La simplificación independiente puede producir diferencias entre bordes vecinos; no se usa para calcular áreas, conectividad o balances hidrológicos. Tampoco se reparan silenciosamente defectos del original. Los campos de área siguen siendo los valores originales, no áreas recalculadas sobre el mapa simplificado.

## Lecturas de estaciones y actualización

INETER publica [WFS GetCapabilities](https://mapserveride.ineter.gob.ni/geoserver/ows?service=WFS&request=GetCapabilities). Se usa WFS 2.0, GeoJSON y `srsName=CRS:84` para asegurar longitud/latitud.

| Lecturas incluidas | Nombre oficial WFS | Entidades descargadas | Tratamiento de fechas |
|---|---|---:|---|
| Nivel de río | `wsINETER-DGRH:Nivel_Rio` | 37 | `fechaultimatransmision` por estación; incluye valores/fechas ausentes |
| Lluvia de 24 horas | `wsINETER-DGMT:Lluvia_24_Horas` | 92 | Esta respuesta no aporta fecha de observación por estación; no se anuncia como lluvia del día actual |
| Temperatura del aire | `wsINETER-DGMT:temperaturacaelus` | 59 | `Ultima lectura`; hay registros antiguos aunque la consulta sea reciente |
| Viento | `wsINETER-DGMT:Vientos_Simet_ot` | 65 | `fechaformato` y `horaformato` no declaran huso; no se transforman en UTC supuesto |

Las fechas de obtención están en cada GeoJSON y se muestran separadas de las fechas de observación. La interfaz marca lecturas con más de 48 horas, fechas desconocidas y fechas futuras; 48 horas es un umbral visual de antigüedad, no un criterio de calidad hidrológica ni un umbral de alerta. Los campos y unidades no declarados por la respuesta se muestran como atributos originales, sin unidades inventadas. Se conservan geometrías Point/MultiPoint, valores nulos y fechas ausentes.

INETER WFS no devolvió cabecera CORS en las consultas verificadas. Por ello, la app incluye una pasarela de **solo lectura** en `clima_nic`, `GET /hidrologia/observaciones/{capa}`, con cuatro fuentes fijas, tiempo de espera, caché de cinco minutos y rechazo de respuestas incompletas. No acepta URLs arbitrarias. Las actualizaciones siguen dependiendo de la frecuencia, disponibilidad y calidad del proveedor.

Para activar la consulta desde una instalación propia:

```sh
python -m pip install -r backend/requirements.txt
cd backend
python -m clima_nic api --puerto 8000
```

Configurar `hidrologia_api` en `app/config.js` con el origen público de esa API (sin barra final); en producción debe usar HTTPS. La casilla de actualización consulta cada cinco minutos mientras el panel esté abierto y la página visible. No es una conexión continua ni una garantía de telemetría en tiempo real.

En una publicación **solo estática** y sin esta API se muestran las instantáneas fechadas incluidas. El botón de refresco lo comunica, y si falla una petición se conserva una instantánea con su fecha original. No se escribe “en vivo” sobre una instantánea ni se transforma un error del proveedor en ceros. Este PR no configura ni despliega un servidor público.

## INETER/SINAPRED: mapas y catálogo accesibles

`ineter_catalogo.json` inventaría **402 capas** publicadas en los espacios de hidrología, meteorología, recursos hídricos y geofísica de INETER. Cada una conserva su QName, título oficial y descarga WFS. Desde el catálogo de Watersheds se puede buscar y solicitar su representación WMS. Que una capa aparezca en GetCapabilities no garantiza que responda, sea reciente o constituya una serie temporal; los errores de mapas remotos se muestran como indisponibilidad.

Diez accesos directos incluyen regiones climáticas, precipitación anual, temperatura anual, amenaza de sequía, lluvias extremas (edición 2022), susceptibilidad a inundación (edición 2021), inundación histórica, deslizamientos, unidades de gestión de agua subterránea y red hidrológica. Sus consultas WMS de comprobación devolvieron imágenes PNG válidas. Se ofrece la leyenda del proveedor y el vector original WFS, evitando asignar clases o unidades por color sin respaldo.

La capa de humedad relativa anual figura en GetCapabilities, pero la consulta WMS verificada devolvió una excepción OGC con HTTP 200. Se conserva su acceso en el catálogo de fuentes y se retira de los accesos directos a mapas comprobados; no se presenta como una imagen disponible ni se sustituye con datos de otro periodo.

`sinapred_catalogo.json` contiene **9 capas naturales** descubiertas en el visor compartido: corredor seco, peligro de inundación, amenaza sísmica, fallas sísmicas, amenaza volcánica, tsunami del Pacífico, rutas históricas de huracanes, inundación del Caribe y ríos/lagunas. Sus campos, créditos, descripción y licencia declarada se conservan. Los vectores se solicitan al abrir una capa, por lotes completos, sin cuenta; no se muestran resultados parciales si se alcanza un límite. Las amenazas geológicas se identifican como referencia geofísica, no se atribuyen al cambio climático.

La capa separada de **Subcuencas Hidrográficas Nicaragua** de SINAPRED declara digitalización del mapa de 1991, realizada en 1999. **No** se utiliza como sustituto de Pfafstetter 2014 ni se le asignan códigos nuevos. Los radares de INETER del visor son imágenes WMS, no polígonos de cuencas ni series climáticas: se conservan como fuente identificada en el visor, pero no se añaden como una capa “en vivo” sin verificar la hora de cada imagen.

## Aspectos climáticos: qué ya existe y qué falta

La base auditada tiene 217 investigaciones: lluvia 55, temperatura 15, vegetación 10, agua 65, aire 2, costa 32, ciclones 7 y polos 31. Esas cifras describen las series disponibles, no cobertura completa de cada variable en cada cuenca. La nueva vista permite superponer las capas existentes de **NASA GPM IMERG, anomalía de SST y MODIS AOD**, con las fechas que ya publica el visor.

El catálogo nacional abre acceso a otras variables, pero no contiene por sí solo los diez o más años necesarios para detectar tendencias. Esta tabla registra vías concretas para ampliar la app sin inventar datos:

| Aspecto o hueco | Fuente y acceso directo/oficial | Naturaleza y límite antes de calcular una tendencia |
|---|---|---|
| Caudal/nivel de estaciones de Nicaragua | INETER WFS, capas `Nivel_Rio` y `EstacionesHidrologicas` | Lecturas/red, no un archivo histórico homogéneo de caudales; solicitar historia y unidades verificadas |
| Evapotranspiración, escorrentía, balance hídrico por cuenca | [NASA GLDAS](https://ldas.gsfc.nasa.gov/gldas), [GES DISC](https://disc.gsfc.nasa.gov/datasets?keywords=GLDAS) | Modelo de superficie terrestre forzado por observaciones; declarar su carácter modelado, no llamarlo caudal medido. Earthdata gratuito para descargar muchos productos |
| Humedad de suelo más reciente | [NASA SMAP](https://nsidc.org/data/smap), [Earthdata](https://search.earthdata.nasa.gov/search?q=SMAP) | Observación satelital superficial; no humedad a toda profundidad ni agua subterránea. Cuenta Earthdata gratuita según producto |
| Escorrentía histórica mundial | [GRDC](https://grdc.bafg.de/) | Caudal observado; acceso y condiciones por estación. No reemplazar estaciones con proyecciones |
| Pronóstico de inundación por cuenca | [Copernicus GloFAS](https://global-flood.emergency.copernicus.eu/), [EWDS](https://ewds.climate.copernicus.eu/) | Pronóstico/reanálisis hidrológico, no observación directa; cuenta gratuita para descarga según producto |
| Climatologías y propiedades hidroambientales por subcuenca | [HydroATLAS/BasinATLAS](https://www.hydrosheds.org/hydroatlas) | Atributos de distintas fuentes/periodos; no son tendencias anuales ni observaciones uniformes. CC BY 4.0; descarga pública |
| Radiación solar, humedad y viento climáticos | [NASA POWER API](https://power.larc.nasa.gov/docs/services/api/temporal/), [consulta diaria de ejemplo](https://power.larc.nasa.gov/api/temporal/daily/point?parameters=ALLSKY_SFC_SW_DWN&community=RE&longitude=-85&latitude=13&start=20200101&end=20201231&format=JSON) | Productos satelitales/reanálisis según variable; ya existe infraestructura POWER en el proyecto, pero faltan agregaciones por cada cuenca |
| Descargas atmosféricas | [NASA LIS/OTD](https://ghrc.nsstc.nasa.gov/lightning/) | Cambios de misión y muestreo; no unir sensores sin control. Acceso según producto |
| Nieve, evapotranspiración y cobertura terrestre mundial | [NASA Earthdata](https://search.earthdata.nasa.gov/) | Seleccionar versión y producto MODIS/VIIRS; cuentas gratuitas en muchos archivos. Comprobar continuidad de sensor |
| Sequía/inundación nacional cartográfica | INETER WFS/WMS y SINAPRED REST incluidos aquí | Mapas históricos/susceptibilidad; no se usan como medición anual ni como alerta actual |

No se ha implementado un balance de agua por cuenca ni se ha interpolado el valor de un punto a toda su superficie. Las cuencas transfronterizas tampoco se recortan arbitrariamente por fronteras nacionales en la capa global. Una evaluación por cuenca exigirá agregación espacial con geometrías originales, QA de observaciones, años completos y el motor estadístico existente.

## Descarga y regeneración reproducible

```sh
python -m pip install -r scripts/datos/requirements-hidrologia.txt
python scripts/datos/descargar_hidrologia.py --cache /ruta/fuera/del/repositorio
# Para actualizar solo las lecturas y catálogos nacionales:
python scripts/datos/descargar_hidrologia.py --cache /ruta/fuera/del/repositorio --solo ineter
node scripts/preparar_render.mjs
python -m http.server 8765 --directory public
```

El comando completo descarga los originales de niveles 4, 6 y 12 de las nueve regiones, los originales ArcGIS nacionales y los catálogos. No necesita cuenta ni una licencia de ArcGIS Pro. `--sin-originales-nivel12` permite omitir esos ZIP grandes si únicamente se quiere reconstruir los niveles web; por defecto sí se descargan. `--solo nacional` y `--solo mundial` permiten reanudar partes del trabajo. Los recibos de la caché identifican URL, fecha de descarga, bytes y SHA-256; `procedencia.json` los incorpora para auditoría. Con la misma caché se reutilizan originales; para una edición futura deben usarse una caché nueva y una revisión explícita de cambios.

## Licencias y referencias

Los datos no heredan la licencia Apache del código de la app. HydroBASINS se distribuye bajo [HydroSHEDS License Agreement](https://www.hydrosheds.org/products/hydrobasins), con atribución y condiciones de uso/redistribución del productor. La metadata ArcGIS consultada publica acceso anónimo pero no declara una licencia de redistribución en `licenseInfo`; se conserva ese dato y los créditos institucionales, sin afirmar que sean dominio público o CC BY. Las geometrías y atributos nacionales conservan los derechos de sus productores. Las capas remotas mantienen sus condiciones originales; el álbum PDF de 2014 no se reproduce.

Referencias verificadas en Crossref el **14 de noviembre de 2026**:

- Lehner, B. y Grill, G. (2013). Global river hydrography and network routing: baseline data and new approaches to study the world's large river systems. [doi:10.1002/hyp.9740](https://doi.org/10.1002/hyp.9740), comprobación: [Crossref](https://api.crossref.org/works/10.1002/hyp.9740).
- Linke, S. et al. (2019). Global hydro-environmental sub-basin and river reach characteristics at high spatial resolution. [doi:10.1038/s41597-019-0300-6](https://doi.org/10.1038/s41597-019-0300-6), comprobación: [Crossref](https://api.crossref.org/works/10.1038/s41597-019-0300-6). Respalda la vía de ampliación HydroATLAS, no una tendencia ya calculada aquí.

## Comprobaciones de esta entrega

La suite completa terminó con `296 passed, 4 warnings, 274 subtests passed in 36.85s`. Se conservaron las pruebas anteriores y se añadieron comprobaciones de integridad de códigos, cobertura y procedencia; la pasarela se prueba sin red para no depender de la disponibilidad de INETER.

El recorrido opcional `tests/e2e/hidrologia_navegador.py` se ejecutó con navegador real: nueve regiones y ambos niveles web, Nicaragua, vista mundial, búsquedas, etiquetas, exportaciones y cuatro capas de estaciones. También comprobó la consulta real de nivel de río por la API, una imagen PNG WMS de INETER y 451 entidades del corredor seco de SINAPRED, sin simular respuestas. Terminó sin errores de consola o JavaScript.

```sh
python -m pip install playwright
python -m playwright install chromium
python tests/e2e/hidrologia_navegador.py --url http://127.0.0.1:8765/ --api http://127.0.0.1:8000
```

El test usa movimiento reducido, renderizado por software y pausa el fondo 3D con la API de la app para facilitar la ejecución en un contenedor. El argumento `--api` es opcional: sin él, se comprueban las instantáneas y el mensaje que distingue la instalación estática de una consulta actualizada. Las verificaciones de servicios remotos pueden fallar si el proveedor está temporalmente indisponible.
