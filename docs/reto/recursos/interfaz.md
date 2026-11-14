# Interfaz e integración de los recursos (agente 4)

Rama `codex/recursos-interfaz`, creada desde `codex/verificacion-entrega` (c03c7af). Trabajo del 13-11-2026, antes del evento del 14 y 15 de noviembre; hecho con Claude Code (herramienta de IA), lo que debe declararse en la entrega.

## Qué se hizo

| Pieza | Archivo | Estado |
|---|---|---|
| Integrador de las salidas de los agentes 1–3 | `backend/clima_nic/recursos.py`, orden `python -m clima_nic recursos` | Hecho |
| Datos de la pestaña | `data/recursos_integrados.json` (generado; no se edita a mano) | Hecho |
| Pestaña **Investigate**: preguntas guiadas qué/dónde, tarjeta de resultado, serie con recta de Theil–Sen, CSV, mapa, *Cross-checks* y dos recorridos guiados | `app/investigar.js`, `index.html`, `app/estilos.css` | Hecho |
| Pestaña **Learn** (9 apartados enlazados desde cada veredicto) | `index.html` | Hecho |
| Pestaña **Sources**: recursos del reto en uso y conjuntos de datos | `app/investigar.js`, `index.html` | Hecho |
| Publicación | `scripts/preparar_render.mjs` copia solo `data/recursos_integrados.json` | Hecho |
| Pruebas | `tests/test_recursos_interfaz.py` (8) y una prueba nueva en `tests/test_e2e_navegador.py` con `tests/e2e/sonda.js` | Hecho |

## Cómo funciona el integrador

- Lee `data/clima.json`, `data/fenomenos_nicaragua.json` y lo que exista en `data/recursos/{tierra,contraste,csa}/`. Si una carpeta no existe, la omite.
- Calcula todas las tendencias con `estadistica/tendencia_robusta.analizar`, el mismo motor que usan los agentes, y guarda un resumen compacto: Sen con IC 95 %, MCO con IC, HAC, Mann–Kendall modificado y veredicto robusto.
- Las series con papel `demostracion_registro_corto` (SWOT) nunca llevan tendencia.
- Rechaza cualquier JSON con `"sintetico": true` salvo en pruebas.
- Traduce los nombres de fuente de los agentes a nombres en inglés para la interfaz (`nombre_en`).
- Guarda el SHA-256 de cada entrada en `entradas`. La prueba `test_json_versionado_esta_al_dia` falla si alguien cambia una entrada sin regenerar.
- Marca cada uno de los 13 recursos como `en_uso` o `sin_datos` según los datos presentes. La interfaz solo muestra los que están en uso, de modo que los bloqueados aparecen solos al llegar sus datos, sin tocar el código.

Formatos que lee, tal como los entregaron los agentes (no siguen del todo el formato común del plan):

| Agente | Archivos | Uso |
|---|---|---|
| 1 · tierra | `series_*_anual.json` (listas de `SerieRegional`) | Una investigación por variable y región; todavía no existen porque falta Earthdata |
| 2 · contraste | `resumen_contrastes.json`, `series_anuales.csv` | `papel: contraste` con `estado: ok` → segunda opinión de una investigación; `papel: tendencia` → investigación nueva (clorofila; OMI y AIRS cuando se desbloqueen) |
| 3 · csa | `canada_imerg.json`, `canada_gistemp.json`, `cocibolca_grealm.csv`, `comparacion_cocibolca_grealm_swot.csv`, `swot_mensual.csv`, `data/regiones_canada.geojson` | Lluvia y temperatura de las Praderas, nivel del Cocibolca 1993–2025, contraste SWOT/G-REALM y SWOT de ambos lagos |

## Resultado con los datos de los tres agentes

Comprobado en una copia local que junta la base, los commits propios de los agentes 1–3 y esta rama: 20 investigaciones en 5 categorías, 12 contrastes y 2 recorridos guiados. La categoría *Air quality* queda oculta hasta que lleguen los datos de OMI.

| Investigación | Veredicto | Sen por década |
|---|---|---|
| Lluvia anual, Nicaragua (IMERG) | evidencia insuficiente | −64,9 mm |
| Lluvia anual, Costa Rica | métodos discrepan | −168,4 mm |
| Temperatura, Nicaragua 1981–2024 (GISTEMP) | tendencia detectada | +0,29 °C |
| Temperatura, Nicaragua 2001–2024 | tendencia detectada | +0,40 °C |
| Temperatura, Praderas de Canadá 2001–2024 | evidencia insuficiente | +0,18 °C |
| Lluvia anual, Praderas de Canadá 2001–2024 (IMERG) | evidencia insuficiente | −30,4 mm |
| Nivel del lago Cocibolca 1993–2025 (G-REALM) | evidencia insuficiente | +0,11 m |
| Clorofila, golfo de Fonseca | métodos discrepan | +0,68 mg/m³ |

Las pendientes y veredictos de lluvia y clorofila coinciden con los del agente 2, y los de Canadá con los del agente 3.

Recursos en uso: NOAA CDO (#4), artículo NTRS (#5), Statsig (#8), Geo.ca (#10), SWOT (#11) y la página de ecosistemas de la CSA (#12).
Sin datos todavía: Giovanni (#1), Hydrology Time Series (#2), AppEEARS (#3), KNMI (#6), Medium (#7), RCM (#9) y el tutorial SAR (#13).

KNMI no se marca en uso: el agente 2 no pudo pasar su verificación humana y descargó CRU y GPCC directamente. CRU y GPCC aparecen en *Sources* como conjuntos de datos, no como uso de KNMI.

## Lectura de los artículos (tarea 2)

**Statsig, «A Comprehensive Guide to Statistical Significance»** (leído el 13-11-2026). Está orientado a pruebas A/B entre grupos (t, z, chi-cuadrado), no a tendencias, así que no añade pruebas al motor. Sí aporta la base de la sección *Learn*:

- qué es y qué no es un p-valor;
- el intervalo de confianza como medida de precisión;
- errores de tipo I y II, y por qué un resultado no significativo no demuestra que no haya efecto;
- tamaño del efecto frente a significancia;
- comparaciones múltiples (aquí se usa FDR en los mapas);
- valores atípicos (aquí, Theil–Sen);
- variables de confusión (aquí, el control por El Niño).

**Medium, «Statistical test methods to detect trends in time series data»**: **no leído**. Medium devuelve una página de verificación de Cloudflare a las descargas automáticas, y la lectura mediante un espejo fue bloqueada por los permisos de la sesión. Por eso el recurso #7 figura como `sin_datos` y no se afirma qué pruebas describe. Pendiente: que una persona del equipo lo abra en el navegador y compruebe si menciona alguna prueba que el motor no tenga. El motor ya cubre MCO con gl ajustados, HAC, Theil–Sen, Mann–Kendall clásico y modificado, y Pettitt.

**Artículo NTRS (Acker et al.)**: lo leyó el agente 2. *Learn* usa su caso del golfo de Fonseca para explicar la autocorrelación: OLS mensual con p = 0,0007 frente a Mann–Kendall anual con p = 0,08.

## Desviaciones del plan

- Los datos sintéticos no se guardan en `data/recursos/fixtures/`: las pruebas los generan en una carpeta temporal. Así no hay forma de que lleguen a `public/`.
- No se tocaron `fuentes/__init__.py`, `productos.py` ni `requirements.txt`. Los adaptadores nuevos se integrarán en el registro cuando se fusionen sus PR. El integrador no necesita dependencias nuevas.
- La primera demostración es «Has Nicaragua's rainfall changed?» y no la lluvia del Pacífico, porque no hay serie IMERG por región dentro de Nicaragua.

## Integración tras fusionar los PR #7, #8 y #9

```text
cd backend
python -m clima_nic recursos       # regenera data/recursos_integrados.json
cd ..
python -m pytest tests -q          # incluye la comprobación de que el JSON está al día y el recorrido en navegador
```

Cada vez que un agente actualice sus datos (por ejemplo, al desbloquear Earthdata), hay que repetir esos dos pasos.

## Verificación realizada

- Rama sola (sin los datos de los agentes): 98 pruebas correctas y 1 omitida (la API necesita FastAPI).
- Copia combinada con los tres agentes: 165 correctas y 1 omitida, incluida la prueba E2E en Chrome sin interfaz.
- La prueba E2E recorre las 20 investigaciones y compara cada veredicto, el número de contrastes y el CSV con el JSON. También comprueba las dos demostraciones, las fuentes en uso y los 9 apartados de *Learn*.
- Revisión manual en Chrome: categorías, lugares, contrastes con gráfica, los dos recorridos guiados y *Sources*, sin errores en consola.

## Recurso 7 (artículo de Medium), 13-11-2026

Medium bloquea la lectura automática (HTTP 403), así que el artículo se leyó completo en el navegador del usuario: «Statistical test methods to detect trends in time series data», MCMC Addict, 19-07-2024. Trata la regresión de mínimos cuadrados con prueba t, Mann–Kendall (con `pymannkendall`), Mann–Kendall estacional y la prueba de raíz unitaria ADF, con series de metano simuladas. *Learn* incorpora la sección «Other trend tests» (`#aprender-otras-pruebas`) con lo que no estaba cubierto: por qué el ciclo estacional resta sensibilidad a Mann–Kendall en datos mensuales y por qué la ADF no decide si hay tendencia.

Nota crítica: el artículo afirma que la ADF da «los mismos resultados» que mínimos cuadrados y Mann–Kendall, pero en sus propias salidas la ADF rechaza la raíz unitaria con 0,2 ppb/año (p = 0,024) y no con 0,3 ppb/año (p = 0,087). Es lo contrario de las otras pruebas, porque la ADF contrasta otra hipótesis. Por eso la aplicación no usa la ADF.
