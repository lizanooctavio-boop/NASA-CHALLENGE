# Auditoría de robustez, fallos de red, uso extremo y exportación (Agente D)

**Aplicación auditada:** Earth System Trend Detective (NASA Space Apps 2026)  
**Rama base:** `origin/codex/herramientas-nasa` (`7324c64`, 217 series integradas)  
**Rama de trabajo:** `codex/audit-robustez`  
**Entorno de pruebas:** Windows · Chromium / Microsoft Edge Headless (`Playwright`) · servidor estático sobre `public/` en `http://127.0.0.1:8991` (construido con `node scripts/preparar_render.mjs`).

---

## 1. Tabla de hallazgos

| ID | gravedad (bloqueante / alta / media / baja) | dónde (pestaña, elemento, dispositivo) | qué pasa | cómo reproducirlo | propuesta |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **D-01** | `bloqueante` | Navegación general (`app/shell.js`), pestañas (`#investigar`, `#tendencias`, `#indicadores`, `#fenomenos`, `#proyecciones` / `#escenarios`, `#exportar`, `#aprender`, `#fuentes`) y vista `#map` (escritorio y móvil) | Al recargar con un hash en la URL (`#investigar`, `#tendencias`, `#indicadores`, `#fenomenos`, `#proyecciones`), la app ignora el hash y muestra siempre la pestaña `Weather` (`meteorologia`). Con `#map`, la transición a 2D espera `3700 ms` tras `espacio:listo`, quedando en el globo 3D durante casi 4 s (o indefinidamente si falla WebGL). Además, cambiar de pestaña o vista no actualiza el historial (`history.pushState` / `popstate` / `hashchange`), por lo que `history.back()` y `history.forward()` no restauran la pestaña ni la vista anterior. | Abrir `http://127.0.0.1:8991/#investigar` (o `#tendencias`, `#indicadores`, `#fenomenos`, `#proyecciones`, `#map`) y recargar; o pulsar `Investigate` → `Rainfall trend` y ejecutar `history.back()`. Ver `docs/auditoria/img/robustez-05.png`. | En `app/shell.js`, sincronizar la pestaña y la vista con `location.hash` al iniciar y en `hashchange`/`popstate` (incluyendo el alias `#proyecciones` → `escenarios` y `#map` → vista 2D inmediata), y registrar cada cambio de pestaña/vista en el historial del navegador. |
| **D-02** | `bloqueante` | Pestañas `Investigate` (`#investigar`), `Climate indicators` (`#indicadores`) y `Climate scenarios` (`#escenarios`), botones `#inv-mapa`, `#inv-csv`, `#ind-csv` (`app/investigar.js`, `app/indicadores.js`) | Si falla la descarga de `data/recursos_integrados.json` o `data/fenomenos_nicaragua.json`: (1) pulsar `#inv-mapa`, `#inv-csv` o `#ind-csv` lanza errores no capturados en consola (`unhandledrejection: TypeError: Cannot read properties of null (reading 'investigaciones')` y `unhandledrejection: TypeError: Failed to fetch`); (2) la promesa rechazada queda memorizada en `carga ??= fetch(...)`, impidiendo reintentar al volver a abrir la pestaña; (3) `#inv-veredicto`, `#ind-veredicto` y `#esc-tabla` quedan en blanco sin mensaje de estado local y `#error` muestra el error crudo `Failed to fetch`. | Bloquear `**/data/fenomenos_nicaragua.json` y `**/data/recursos_integrados.json` con `page.route(..., r => r.abort('failed'))`, abrir `Climate indicators` o `Investigate` y pulsar `Series (CSV)` o `Show on the map`. Ver `docs/auditoria/img/robustez-04.png`. | En `app/investigar.js` y `app/indicadores.js`, reiniciar `carga = null` cuando falle la petición, mostrar un estado vacío explicativo en inglés dentro del contenedor del panel (`Investigation data unavailable.`, `Climate indicator data unavailable.`), proteger `#inv-mapa`, `#inv-csv` e `#ind-csv` con `try/catch` y deshabilitarlos mientras no haya datos cargados. |
| **D-03** | `alta` | Pestaña `Weather` (`#consulta-punto`) y `El Niño & cyclones` (`#enos-tarjetas`), adaptador `src/fuentes-meteo.js` y `app/shell.js` | En `src/fuentes-meteo.js`, `enosLocal()` ejecuta `await fetch('/clima-base/enos.json')` sin `try/catch`: si la petición sufre un corte o aborto de red (en lugar de devolver un HTTP 404 limpio), lanza `TypeError: Failed to fetch` y nunca cae al respaldo local `data/fuentes/oni_2001_2024.csv`, dejando `ENSO data unavailable.` (ver `docs/auditoria/img/robustez-02.png`). Asimismo, cuando `api.open-meteo.com` cae o se bloquea, `punto(q)` propaga la excepción cruda de `fetch`, mostrando `Failed to fetch` en `#error` en vez de un mensaje claro en inglés (ver `docs/auditoria/img/robustez-01.png`). | Bloquear `**/clima-base/*.json` y `**/*api.open-meteo.com/**` con `page.route(..., r => r.abort('failed'))`, abrir `El Niño & cyclones` y consultar un pronóstico puntual en `Weather`. | En `src/fuentes-meteo.js`, envolver `fetch('/clima-base/enos.json')` en `try/catch` para activar siempre el respaldo `data/fuentes/oni_2001_2024.csv`, capturar errores de red en `punto(q)` y `solicitud(ruta)` devolviendo `Response.json({ error: ... }, { status: 503 })` con mensajes claros en inglés, y normalizar mensajes de red en `error(e)` de `app/shell.js`. |
| **D-04** | `alta` | Pestaña `Climate scenarios` (`#escenarios`: `#ventana-cmip`, `#ssp`, `#cambios`, `#graf-dT`, `#graf-dP`), `app/graficas-meteo.js` | Cuando `/api/series` (`/clima-base/series.json`) no está disponible, `app/graficas-meteo.js` silencia el fallo con `.catch(()=>{})` sin actualizar la interfaz: el selector `Season` (`#ventana-cmip`) queda vacío sin opciones, `#cambios` queda vacío y los lienzos `#graf-dT` y `#graf-dP` muestran recuadros en blanco sin explicación. Además, llama a `r.json()` antes de verificar `r.ok`. | Abrir `Climate scenarios` con `**/clima-base/*.json` bloqueado o sin `public/clima-base` y desplazar hacia la sección CMIP6 (SCA). Ver `docs/auditoria/img/robustez-03.png`. | En `app/graficas-meteo.js`, comprobar `r.ok` antes de parsear JSON; si `/api/series` falla, deshabilitar `#ssp` y `#ventana-cmip` con una opción `Unavailable`, mostrar un mensaje claro en inglés en `#cambios` (`Regional CMIP6 time-series data unavailable.`) y ocultar los contenedores de gráficas vacías. |
| **D-05** | `alta` | Exportación CSV en `Investigate` (`#inv-csv`, `app/investigar.js`) y enlaces estáticos `/clima-base/*.csv` (`#fenomenos`, `#escenarios`, `#exportar`, `app/shell.js`) | (1) En `app/investigar.js`, `value_${x.unidad.replace(/[^\w°³]+/g,'_')}` elimina `²` y `Ω` y deja guiones bajos finales: para `acidez_aragonito_mar_caribe_nic` (`Ω`) genera `year,value__` y para `hielo_september_artico` (`million km²`) genera `year,value_million_km_`. (2) Los enlaces `<a href="/clima-base/*.csv" download>` descargan un HTML 404 corrupto o navegan a una página rota cuando `/clima-base/` no está disponible. | (1) Descargar CSV de `acidez_aragonito_mar_caribe_nic` y `hielo_september_artico` en `Investigate`. (2) Pulsar `ONI (CSV)`, `Active cyclones (CSV)` o `Projections (CSV)` sin `public/clima-base`. | (1) En `app/investigar.js`, admitir `²` y `Ω` en la expresión regular del nombre de columna y recortar `_` sobrantes en los extremos. (2) En `app/shell.js`, interceptar clics en `a[href^="/clima-base/"][download]` para servir el respaldo local de ONI cuando exista o mostrar un error claro en inglés si el CSV no está disponible. |
| **D-06** | `alta` | Escena 3D (`#espacio`, `app/espacio.js`), conmutador `Globe`/`Map` (`app/shell.js`) y capas en vivo (`#chk-radar`, `#chk-imerg`, `#chk-sst`, `#chk-aod`, `app/fenomenos.js`) | (1) En `app/espacio.js`, `new THREE.WebGLRenderer(...)` se ejecuta sin `try/catch`; si WebGL falla o no está disponible, lanza `pageerror` y no conmuta al mapa 2D ni despacha `espacio:listo`. (2) En `app/shell.js`, pulsar `Globe`/`Map` durante una transición en curso descarta el clic sin encolar la vista final deseada. (3) En `app/fenomenos.js`, cuando fallan `api.rainviewer.com` o capas GIBS (`imerg`, `sst`, `aod`), la casilla queda marcada sin mostrar retroalimentación de fallo. | (1) Iniciar con WebGL deshabilitado. (2) Alternar 20 veces rápido entre `Globe` y `Map`. (3) Bloquear `api.rainviewer.com` y `gibs.earthdata.nasa.gov` y marcar `Radar` / `IMERG rain`. | (1) Envolver la creación del contexto WebGL en `app/espacio.js` con degradación automática a vista 2D. (2) Guardar `vistaPendiente` en `cambiarVista` (`app/shell.js`) para aplicar el último modo elegido al concluir la animación. (3) Desmarcar la capa fallida y avisar con mensaje claro en inglés en `app/fenomenos.js`. |
| **D-07** | `media` | Exportación CSV en `Rainfall trend` (`#tendencias`, `src/tendencias.js`) | Los archivos `annual_rainfall_<area>.csv` y `rainfall_trends_by_area.csv` se exportan en UTF-8 sin BOM (`\uFEFF`) y con saltos `\n`, a diferencia de `app/shell.js`, `app/indicadores.js` y `app/investigar.js` que incluyen BOM y `\r\n` para Excel. | En `Rainfall trend`, pulsar `Annual series` o `Trends by area` e inspeccionar los primeros bytes del archivo descargado. | Añadir `'\uFEFF'` al inicio del contenido CSV y normalizar saltos a `\r\n` en `descargar()` dentro de `src/tendencias.js` (se deja como propuesta por estar fuera de los archivos editables de esta auditoría). |
| **D-08** | `baja` | Alerta flotante `#error` sobre paneles largos (`app/estilos.css`) | `#error` se posiciona fijo en `bottom: 30px; left: calc(var(--izq) + 18px)`, coincidiendo con la posición de los botones inferiores del panel (`#ind-csv`, `#exp-punto`), por lo que puede taparlos hasta cerrarse. | Provocar un error en `Climate indicators` a `1280×800` y observar la superposición sobre `Series (CSV)`. Ver `docs/auditoria/img/robustez-04.png`. | En `app/estilos.css`, ubicar `#error` en la esquina superior derecha bajo la cabecera o desplazarlo fuera del área de botones del panel (se deja como propuesta por requerir cambios en `app/estilos.css`). |

---

## 2. Detalle de las pruebas ejecutadas

### 2.1. Bloqueo de fuentes externas (`page.route`)

Se bloquearon por turnos con `page.route(patron, route => route.abort('failed'))` las cinco familias de orígenes:

1. **`**/*gibs.earthdata.nasa.gov/**` (NASA GIBS WMTS):**
   - El mapa 2D sigue operativo y la capa vectorial base (`assets/mundo.geojson`) dibuja costas, fronteras y capitales.
   - Al activar `GOES satellite (live)` (`#chk-sat`), `ultimaGoes()` captura la excepción de red, cae a `/api/gibs_hora` y muestra `Unavailable` en `#hora-sat`.
   - Sin embargo, al activar `IMERG rain` (`#chk-imerg`), `Sea temp. anomaly` (`#chk-sst`) o `Dust & smoke` (`#chk-aod`), `estado[k]` pasa a `'unavailable'` internamente pero la casilla permanece marcada sin aviso visible (**D-06**).
2. **`**/*server.arcgisonline.com/**` (Esri World Imagery y etiquetas):**
   - Al hacer zoom (`z >= 6`), Leaflet ignora las teselas fallidas sin lanzar `pageerror` ni bloquear la interacción ni la malla meteorológica.
3. **`**/*api.open-meteo.com/**` (pronóstico puntual ECMWF IFS 0,25°):**
   - Al enviar el formulario `#consulta-punto` (`lat=12.13, lon=-86.25`), el botón `#consultar` pasa a `Loading…` (`disabled=true`) y en el bloque `finally` vuelve a `Get forecast` (`disabled=false`), deshabilitando `#exp-punto`.
   - No obstante, como `punto(q)` en `src/fuentes-meteo.js` no captura el fallo de `fetch`, se propaga `TypeError: Failed to fetch` y `#error-texto` muestra el texto técnico crudo `Failed to fetch` (**D-03**, captura `docs/auditoria/img/robustez-01.png`).
4. **`**/*api.rainviewer.com/**` (radar meteorológico):**
   - Al marcar `#chk-radar`, `radar()` captura el error y asigna `estado.radar = 'unavailable'` sin romper el mapa, pero deja la casilla `#chk-radar` marcada sin informar al usuario (**D-06**).
5. **`**/clima-base/*.json` y `/api/**` (además de `**/data/*.json`):**
   - Cabecera y línea de tiempo: `#indicador-datos` pasa a `data-nivel="error"` con texto `No model data` y `#lt-etiqueta` muestra `No forecast data` con los controles de reproducción deshabilitados.
   - Ciclones (`#lista-tormentas`): degrada con el mensaje en inglés `Cyclone data unavailable.`.
   - ENOS (`#enos-tarjetas`): cuando `/clima-base/enos.json` se aborta a nivel de red (`route.abort()`), `enosLocal()` falla antes de leer `data/fuentes/oni_2001_2024.csv` y muestra `ENSO data unavailable.` (**D-03**, captura `docs/auditoria/img/robustez-02.png`).
   - Escenarios CMIP6 SCA (`#escenarios`): cuando falta `/clima-base/series.json`, el selector `#ventana-cmip`, `#cambios` y los gráficos `#graf-dT` / `#graf-dP` quedan en blanco sin mensaje (**D-04**, captura `docs/auditoria/img/robustez-03.png`).
   - Indicadores e Investigación (`data/fenomenos_nicaragua.json`, `data/recursos_integrados.json`): al fallar la red, pulsar `#ind-csv`, `#inv-mapa` o `#inv-csv` genera `unhandledrejection` en consola y la promesa fallida queda bloqueada en caché (**D-02**, captura `docs/auditoria/img/robustez-04.png`).

---

### 2.2. Pruebas de uso extremo y estrés

1. **Clics rápidos repetidos:**
   - Se recorrieron las 9 pestañas del menú principal 3 veces seguidas sin pausas y se pulsaron en ráfaga todos los botones de categorías (`#inv-categorias`), lugares (`#inv-lugares`) y variables (`#inv-variables`).
   - Chart.js destruye correctamente la instancia previa (`graficas[id]?.destroy()`) antes de recrear cada lienzo; no se observaron fugas ni excepciones en consola (`page_errors: []`).
2. **Cambio de pestaña a mitad de carga:**
   - Al cambiar de pestaña mientras se resuelven `cargar()` o `sincronizar()`, el contador de turno (`mio === turno` en `app/globo.js` y `turno[k]` en `app/fenomenos.js`) evita condiciones de carrera.
3. **Alternancia entre globo 3D y mapa 2D (20 veces):**
   - Al pulsar 20 veces seguidas `#vista-mapa` y `#vista-globo` cada `50 ms`, el cerrojo `cambiando` evita corromper la animación de `THREE.ShaderMaterial`, pero descarta clics realizados durante la transición sin recordar el último botón pulsado (**D-06**).
4. **Zoom máximo/mínimo y redimensionado de ventana:**
   - En el mapa 2D se verificó `mapa.setZoom(18)` (`zoom_max = 18`) y `mapa.setZoom(2)` (`zoom_min = 2`), y en el globo 3D los límites `DIST_MIN = 1.28` y `DIST_MAX = 34`.
   - Se redimensionó la ventana entre `360×640` (móvil), `768×1024` (tableta), `1920×1080` y `1280×800`, recalculándose correctamente `--alto-controles-mapa`, `--alto-lt`, `--alto-ley` y el tamaño de los lienzos.
5. **Recarga con hashes en la URL y navegación `history.back()`:**
   - Al cargar directamente `http://127.0.0.1:8991/#map`, `#investigar`, `#tendencias`, `#indicadores`, `#fenomenos` y `#proyecciones`, todas las cargas permanecieron en `active_tab: "meteorologia"` y `vista_modo: "globo"` (**D-01**, captura `docs/auditoria/img/robustez-05.png`).
   - Al navegar por pestañas (`meteorologia` → `investigar` → `tendencias`) y ejecutar `history.back()`, el navegador retrocedió a la URL previa sin cambiar la pestaña activa (**D-01**).

---

### 2.3. Auditoría de exportación (14 descargas verificadas: 13 CSV + 1 JSON)

Se descargaron e inspeccionaron 14 archivos en `Rainfall trend`, `Climate indicators` e `Investigate`:

| # | Pestaña | Archivo descargado | Tipo | UTF-8 BOM (`\uFEFF`) | Encabezado de columnas | Filas totales | Filas sin dato (huecos) | Observaciones |
| :- | :--- | :--- | :--- | :--- | :--- | ---: | ---: | :--- |
| 1 | `Rainfall trend` | `annual_rainfall_nicaragua.csv` | CSV | No (**D-07**) | `year,rainfall_mm,least_squares_mm,theil_sen_mm` | 28 | 0 | 24 años (2001–2024) + 3 líneas `#` de metadatos. |
| 2 | `Rainfall trend` | `annual_rainfall_costa_rica.csv` | CSV | No (**D-07**) | `year,rainfall_mm,least_squares_mm,theil_sen_mm` | 28 | 0 | Valores e intervalos coinciden con `data/clima.json`. |
| 3 | `Rainfall trend` | `rainfall_trends_by_area.csv` | CSV | No (**D-07**) | `area_id,area,years,ls_slope_mm_decade,...` | 8 | 0 | Incluye pendientes MCO, Theil–Sen, IC HAC y `mann_kendall_p`. |
| 4 | `Rainfall trend` | `rainfall_trend_evidence.json` | JSON | N/A | Objeto raíz JSON (`question`, `areas`, `method`) | 582 | N/A | JSON válido con las 4 áreas y series completas. |
| 5 | `Climate indicators` | `temperatura_gistemp_NIC.csv` | CSV | Sí (`EF BB BF`) | `year,temperatura_gistemp_c` | 47 | 0 | 1981–2024, unidades y fuente GISTEMP v4 en cabecera `#`. |
| 6 | `Climate indicators` | `lluvia_anual_imerg_NIC.csv` | CSV | Sí (`EF BB BF`) | `year,lluvia_anual_imerg_mm` | 27 | 0 | 2001–2024, fuente GPM IMERG Final V07B. |
| 7 | `Climate indicators` | `ndvi_pacifico.csv` | CSV | Sí (`EF BB BF`) | `year,ndvi_ndvi` | 28 | 0 | 2000–2024, fuente MODIS MOD13Q1 NDVI. |
| 8 | `Climate indicators` | `temperatura_gistemp_central.csv` | CSV | Sí (`EF BB BF`) | `year,temperatura_gistemp_c` | 47 | 0 | 1981–2024, región Central. |
| 9 | `Investigate` | `temperatura_NIC.csv` | CSV | Sí (`EF BB BF`) | `year,value_°C` | 47 | 0 | Símbolo `°` codificado en UTF-8 con BOM para Excel. |
| 10 | `Investigate` | `clorofila_golfo_fonseca.csv` | CSV | Sí (`EF BB BF`) | `year,value_mg_m³` | 25 | 0 | Superíndice `³` preservado en UTF-8 con BOM. |
| 11 | `Investigate` | `humedad_smap_superficial_NIC.csv` | CSV | Sí (`EF BB BF`) | `month,value_m³_m³` | 61 | 2 (`2015-03,`, `2015-05,`) | Meses sin dato exportados limpiamente como celda vacía (`null` → `''`). |
| 12 | `Investigate` | `acidez_aragonito_mar_caribe_nic.csv` | CSV | Sí (`EF BB BF`) | `year,value__` (**D-05**) | 45 | 0 | La unidad `Ω` se reemplaza por `_`, produciendo `value__`. |
| 13 | `Investigate` | `hielo_september_artico.csv` | CSV | Sí (`EF BB BF`) | `year,value_million_km_` (**D-05**) | 51 | 0 | El superíndice `²` de `million km²` se pierde y deja `_` final. |
| 14 | `Investigate` | `grace_masa_groenlandia.csv` | CSV | Sí (`EF BB BF`) | `year,value_Gt` | 22 | 0 | Años sin misión (2017–2018) omitidos en datos crudos y rellenados con hueco en la gráfica (`conHuecos`). |

---

### 2.4. Compatibilidad de navegadores y motores JS/DOM

- **APIs modernas utilizadas:** `Array.prototype.at()` (ES2022), `Array.prototype.findLastIndex()` (ES2023), `Element.prototype.replaceChildren()` (DOM), `AbortSignal.timeout()` y `ResizeObserver`. Todas están soportadas nativamente en Chromium / Edge / Firefox / Safari actuales.
- **WebGL y degradación en `app/espacio.js`:** el uso de `THREE.GLSL3` (WebGL 2) funciona en Chromium/Edge con aceleración por hardware o SwiftShader, pero si el navegador bloquea la creación del contexto WebGL, `new THREE.WebGLRenderer` lanza una excepción síncrona no tratada que impide usar la aplicación (**D-06**).
- **Almacenamiento local (`localStorage`):** `app/shell.js` protege `getItem` y `setItem` con `try/catch`, por lo que no falla en modo privado estricto ni con cookies/almacenamiento bloqueados.
