# Auditoría integral con 20 agentes (`2026-11-15`)

- **Base auditada:** `origin/main` (`20bec48` — *Combinar codex/frontend-astra: corrida en la caché del globo, «Archived run» y mapa 2D sin WebGL*)
- **Fecha:** 2026-11-15
- **Modalidad:** Inspección estática y ejecución de sondas/pruebas no destructivas en worktree aislado (sin modificar el código fuente).

---

## Verificaciones globales ejecutadas

- `node --check` en 34 archivos `.js` / `.mjs` / `.cjs` (`app/`, `src/`, `scripts/`, `tests/`): **34/34 sin errores**.
- `python -m py_compile` en 87 archivos `.py` (`backend/`, `scripts/`, `tests/`, `data/recursos/`): **87/87 sin errores**.
- `python -B scripts/datos/verificar_clima.py`: **88 de 88 comprobaciones correctas**.
- `node --test tests/teselas-geometria.test.mjs`: **3/3 pruebas pasadas**.
- `python -m pytest -q`:
  - Corrida completa sin latencia de CDN: **310 passed, 3 warnings, 274 subtests passed** (`230.71s`).
  - Corrida afectada por carga de CDN > 10,5 s: **303 passed, 3 warnings, 7 errors, 40 subtests passed** (`409.25s`) en `tests/test_e2e_navegador.py::RecorridoEnNavegador` (confirma inestabilidad de `tests/e2e/sonda.js:138`).
- `node tests/globo-detalle.cjs`: falló (`exit 1`) por `Error: Cannot find module 'playwright'`.

---

## Hallazgos prioritarios consolidados (sin duplicados)

### Críticos / Altos — Frontend y Experiencia de Usuario
1. **Bloqueo total de arranque si falla `Three.js` y falta de SRI** (`index.html:18-23`, `app/espacio.js:4`, `app/teselas-globo.js:1`, `app/shell.js:204-212`): `<script type="module" src="app/espacio.js">` carece de `onerror`; ante fallo de CDN el spinner `#carga-globo` queda fijo en `"Loading 3D Earth…"`, y `three@0.160.0` carece de `integrity="sha384-..."`.
2. **Pérdida de contexto WebGL y excepción no capturada** (`app/espacio.js:16-24`): faltan listeners `webglcontextlost`/`webglcontextrestored` y el fallback de `THREE.WebGLRenderer` relanza el error.
3. **Caída de Leaflet rompe Hidrología y vista 2D** (`app/hidrologia.js:22,150`, `app/shell.js:155,197-202`): `L.layerGroup()` se ejecuta sin guardia al inicializar y `SICC_vista.marcar`/`irA` asumen `L` y `mapa` definidos.
4. **Teselas progresivas y retícula congeladas con `prefers-reduced-motion: reduce`** (`app/teselas-globo.js:122-174`, `app/espacio.js:306-327,530-536`): faltan disparo de redibujo al terminar teselas, reintento tras el throttle de `180ms` y soporte de `reducido` en `Espacio.reticula`; las teselas hijas mezclan contra Blue Marble (`uDia`) en vez de la tesela padre (`app/teselas-globo.js:19-24,89-97`).
5. **Desfase de `desp` al pasar a mapa (`265.69`) y carrera en `#map`** (`app/espacio.js:393-576`, `app/shell.js:172-177`): al iniciar con `#map`, `else intro()` cancela `aMapa()`.
6. **Cabecera rota en móvil horizontal y clipping en `aside` / `main`** (`app/estilos.css:30-199`, `app/buscador.css:12,44-45`, `app/ayuda.css:67`): `.acciones` queda empujado a X negativa (`667x375` y `740x360`), `aside` sin `overflow-y: auto` se recorta en portátiles cortos y `main { z-index: 4 }` atrapa listas desplegables bajo `#controles-mapa`.
7. **Ayuda *"Show me"* apunta a controles ocultos en móvil** (`app/ayuda.js:111-125`, `app/estilos.css:248`): no activa `soloMapa(true)`, no desminimiza paneles minimizados ni revela `#inv-contrastes`.
8. **XSS en `innerHTML` e inyección de fórmulas CSV** (`src/graficas.js:38-40`, `src/tendencias.js:134`, `app/fenomenos.js:111`, `app/investigar.js:262,283`, `app/indicadores.js:204`, `app/shell.js:94`): `mostrarTip` asigna HTML sin escapar; enlaces `aviso_url`/`requerimiento` carecen de validación `https?://`; los CSV no escapan comillas ni neutralizan `=`, `+`, `-`, `@`.
9. **Divergencia de 10x en fallback del navegador (`mm/yr` vs `mm/decade`) y errores en `estadistica.js`** (`src/contrato.js:47-59,102-106`, `src/estadistica.js:82-183`): `mco` retorna `p: 0` en series constantes, `sen` falla en `x` desordenado, `pearson` retorna `NaN` sin varianza.
10. **Coordenadas `EPSG:32616` con `"Infinity"` y MGRS polar erróneo** (`app/coordenadas.js:23-138`): falta `try/catch` y `Number.isFinite` (62 ciudades muestran `Infinity`); panel en móvil oculto o recortado.
11. **Bloqueos en Meteo en vivo y fallos en `/api/tiempo`** (`app/campo.js:43-279`, `src/fuentes-meteo.js:12-56`, `app/graficas-meteo.js:45-67`): `pidiendo` omite `corrida_utc`, `punto()` convierte vacío en `(0,0)`, `r.json()` fuera de `try/catch`, `enosLocal` convierte vacío en `0` (`Neutral`).
12. **Unidades truncadas y fallos sin manejo en `Investigar`, `Fenómenos` e `Indicadores`** (`app/investigar.js:121-283`, `backend/clima_nic/recursos.py:486`, `app/fenomenos.js:50-133`, `app/indicadores.js:94-198`): `.split("/")[0]` trunca `"m³/m³/década"` a `"m³"`; `lon == null` tumba ciclones; `404` de `regiones_nicaragua.geojson` falla en silencio.

### Críticos / Altos — Backend, Estadística, Adaptadores y Pipeline
13. **CLI `cp1252` en Windows y envenenamiento de caché WFS (`HTTP 500`)** (`backend/clima_nic/__main__.py:5-75`, `hidrologia.py:37-52`, `api.py:94-96`, `consulta.py:87-144`): `UnicodeEncodeError` al imprimir `→`/`⁻`, `NaN` WFS envenena `_CACHE` por 300 s, `"numberMatched": null` burla verificación y `/escenarios`/`/pronostico` devuelven `200` con parámetros inválidos.
14. **Fallos matemáticos y divisiones por cero en motor estadístico** (`modelo_estacional.py:44-86`, `indicadores.py:151-399`, `tendencia_robusta.py:69-175`, `tendencia.py:84`, `fdr.py:13-17`): `h_i == 1` en `msess_loo`, `ZeroDivisionError` en `ajustar_loglogistica`, desfase de DOY y 365 días en años bisiestos, falta de orden cronológico en `tendencia_robusta.analizar`, `gl <= 0` tras `_hac`, `_r1_calendario > 1.0`.
15. **Recorte de datos `2025+` y `ZeroDivisionError` en productos/proyecciones** (`productos.py:186-502`, `proyecciones.py:76-84`, `actualizar.py:53-54`, `agro.py:29-63`, `regiones.py:110`): límite duro a 2024 pese a existir 2025 en `gistemp_nicaragua.csv`, meses POWER faltantes convertidos en `0.0` mm, división por cero en cambio `%` CMIP6, caché GISTEMP sin refresco.
16. **Adaptadores NASA con errores estructurales** (`smap.py:53,65`, `giovanni.py:268-359`, `grace.py:37-47`, `nex_gddp.py:38-134`, `gistemp.py:41-66`, `appeears.py:109-584`, `power.py:186-234`, `imerg.py:53`, `earthdata.py:51`, `lagos.py:127,245`): `np.ix_` sobre `h5py.Dataset`, `_FillValue` sin filtrar en GRACE, `-273.15` aplicado a humedad/radiación/viento en `nex_gddp`, `add_offset`/NumPy 2 en `gistemp`, `(2001, 2024)` fijo en `appeears`.
17. **Build de meteorología y descarga de hidrología** (`scripts/preparar_meteo.mjs:46-79`, `scripts/datos/descargar_hidrologia.py:95-265`): `preparar_meteo.mjs` sobrescribe `global_meta.json` con salida `0` aunque fallen las 17 tareas; `descargar_hidrologia.py` omite `encoding='utf-8'` y rompe en Windows `cp1252`.

### Medios / Bajos — Accesibilidad, Hidrología Frontend, Datos, Pruebas y Documentación
- **Accesibilidad**: `hashchange` en `app/shell.js:213` saca de `#map` al activar `#contenido-principal`; pérdida de foco a `BODY` en `investigar.js:259`, `reticula.js:45-56` y `tutorial.js:38-40`; botones duplicados sin contexto en `hidrologia.js:131` (`9x "Show map"`) e `index.html:171-174` (`4x "Show"`); `role="listbox"` con `<button>` hijo en `buscador.js:155-169`; controles de retícula a `36px` en `768x1024`; textos sin traducir en Ayuda (`es`) y fallbacks en español (`config.js:6`, `contrato.js:137`).
- **Hidrología frontend** (`app/hidrologia.js`, `src/hidrologia-datos.js`): fuga de `L.Canvas`, caché sin límite (`~135.45 MB`), auto-refresco cada 5 min que fuerza cambio a mapa, niveles `4`/`6` habilitados al inicio para `nic`, `TypeError` si `feature.properties` es `null`.
- **Generadores/SAR**: `np.nan_to_num(s)` en `generar_hallazgos.py:78-86`, `-0.0` en `recursos.py:283-284`, handles sin cerrar en `scripts/sar/*.py`, celda 3 dependiente en `agua_superficial.ipynb`.
- **Pruebas y Docs**: `sonda.js:138` expira tras ~10,5 s, `taskkill` solo Windows, falta de pruebas JS reales para `estadistica.js`/`coordenadas.js`/`buscador.js`; `README.md` y `docs/` con hashes/puertos obsoletos (`#proyecciones`, `scripts/servidor.mjs`, puerto `8000`) y `requests>=2.31` listado como opcional en `backend/requirements.txt:8`.

---

## Informes completos por agente (20/20)

| # | Área auditada | Informe |
|---|---|---|
| 01 | HTML y secuencia de arranque | [01-html-boot.md](agentes-2026-11-15/01-html-boot.md) |
| 02 | Shell principal y maquetación CSS | [02-shell-layout.md](agentes-2026-11-15/02-shell-layout.md) |
| 03 | Globo 3D WebGL, teselas y fallback 2D | [03-globo-teselas.md](agentes-2026-11-15/03-globo-teselas.md) |
| 04 | Meteorología en vivo, campo, paletas y gráficas | [04-meteo-campo.md](agentes-2026-11-15/04-meteo-campo.md) |
| 05 | Investigar, Fenómenos e Indicadores | [05-investigar-fenomenos.md](agentes-2026-11-15/05-investigar-fenomenos.md) |
| 06 | Buscador de lugares y coordenadas/SRS | [06-buscador-coordenadas.md](agentes-2026-11-15/06-buscador-coordenadas.md) |
| 07 | Retícula geográfica, Ayuda, Tutorial e Inicio | [07-reticula-ayuda-tour.md](agentes-2026-11-15/07-reticula-ayuda-tour.md) |
| 08 | Hidrología / Cuencas (frontend) | [08-hidrologia-frontend.md](agentes-2026-11-15/08-hidrologia-frontend.md) |
| 09 | JS compartido (`contrato`, `estadistica`, `graficas`, `tendencias`, `globo-meteo`) | [09-src-compartido.md](agentes-2026-11-15/09-src-compartido.md) |
| 10 | Backend API (`FastAPI`), `consulta` y CLI (`__main__.py`) | [10-backend-api-consulta.md](agentes-2026-11-15/10-backend-api-consulta.md) |
| 11 | Motor estadístico (`tendencia`, `tendencia_robusta`, `indicadores`, `modelo_estacional`, `fdr`) | [11-motor-estadistico.md](agentes-2026-11-15/11-motor-estadistico.md) |
| 12 | Productos, proyecciones CMIP6, agro, actualizar y regiones | [12-productos-agro.md](agentes-2026-11-15/12-productos-agro.md) |
| 13 | Recursos globales y módulos regionales (`recursos*.py`) | [13-recursos-regional.md](agentes-2026-11-15/13-recursos-regional.md) |
| 14 | Adaptadores de fuentes NASA (`backend/clima_nic/fuentes/*`) | [14-adaptadores-fuentes.md](agentes-2026-11-15/14-adaptadores-fuentes.md) |
| 15 | Build, servidor local, Render y workflows CI | [15-build-servidor-ci.md](agentes-2026-11-15/15-build-servidor-ci.md) |
| 16 | Scripts de datos y procesamiento SAR | [16-scripts-datos-sar.md](agentes-2026-11-15/16-scripts-datos-sar.md) |
| 17 | Datos estáticos y generadores de recursos/contrastes | [17-datos-generadores.md](agentes-2026-11-15/17-datos-generadores.md) |
| 18 | Suite de pruebas y cobertura real | [18-suite-pruebas.md](agentes-2026-11-15/18-suite-pruebas.md) |
| 19 | Integración cruzada, accesibilidad WCAG 2.2 AA, responsive e i18n | [19-integracion-a11y.md](agentes-2026-11-15/19-integracion-a11y.md) |
| 20 | Seguridad, cadena de suministro y exactitud documental | [20-seguridad-docs.md](agentes-2026-11-15/20-seguridad-docs.md) |
