# Expediente por área: modelo de estado y de resultados

Este documento describe los objetos que comparten el mapa, el panel, el informe PDF, el paquete ZIP y el
enlace «Compartir investigación». Los cinco leen el mismo objeto de resultados; ninguno recalcula cifras.

```
área (ETDGeo) ──► consulta (ETDEstado, etd-consulta v1) ──► datos por celda (ETDFuentes, NASA POWER)
                                                         └─► resultados (ETDAnalisis, etd-resultados v1)
                                                               ├─► panel y capa del mapa (app/expediente.js)
                                                               ├─► informe.pdf (ETDInforme)
                                                               ├─► ZIP (ETDPaquete) + manifest.json
                                                               └─► enlace #inv=… (ETDEstado.enlace)
```

## 1. Área de interés

| Campo | Contenido |
| --- | --- |
| `id` | `aoi-<tipo>-<8 hex>` al dibujar; `nic-municipio-<código INETER>` o `nic-departamento-<código>` para unidades oficiales. Se conserva al restaurar. |
| `nombre` | Editable. |
| `tipo` | `punto`, `circulo`, `rectangulo`, `poligono`, `administrativa`, `archivo`. |
| `geometria` | GeoJSON EPSG:4326, orden `[lon, lat]`; anillo exterior antihorario (se corrige y se avisa). |
| `extension` | `[oeste, sur, este, norte]`; si cruza el antimeridiano, `oeste > este` (RFC 7946 §5.2). |
| `centro` | `{lon, lat, metodo}`: `punto`, `centroide_laea` (centroide en proyección acimutal equivalente de Lambert local) o `punto_interior` cuando el centroide cae fuera. |
| `superficie_km2` | Área geodésica WGS84 con GeographicLib (Karney, 2013), aristas densificadas a ≤ 0,1°. `null` para un punto. |
| `admin` | `{pais, departamento, municipio, nivel, codigo, area_oficial_km2}`; para áreas dibujadas, la unidad que contiene el centro (`segun: "centro"`). |
| `procedencia` | `{tipo: dibujo | coordenadas | archivo | ineter, fuente, version, fecha_acceso}`. |
| `celdas` | Celdas de la rejilla del producto que tocan el área: `id`, centro, `caja`, `area_celda_km2`, `interseccion_km2`, `peso`, `fraccion_celda`. |

Validación (`ETDGeo.validar`): geometría vacía, tipo no admitido, coordenadas no numéricas, fuera de rango
(lat > 90 o lon > 540), anillo abierto, anillo con < 4 posiciones, autointersección, más de 20 000 vértices o
400 partes, superficie nula; `celdasRejilla` rechaza áreas de más de 64 celdas de NASA POWER.

Un punto no tiene superficie: se informa la **huella** del producto (la celda de 0,5° × 0,625° que lo
contiene, ~3 765 km² a 12° N) y el aviso `consulta_puntual`, que impide describirlo como promedio de un área.

## 2. Consulta (`etd-consulta`, versión 1)

```jsonc
{
  "esquema": "etd-consulta", "version": 1, "version_codigo": "expediente-1.0.0",
  "titulo": "…", "idioma": "es" | "en",
  "area": { "id", "nombre", "tipo", "geometria", "radio_km"?, "admin"?: {"nivel","codigo","nombre"}, "procedencia" },
  "variable": "T2M" | "PRECTOTCORR", "fuente": "nasa_power",
  "periodo": {"inicio": 1981, "fin": 2024},          // periodo de la tendencia
  "referencia": {"inicio": 1991, "fin": 2020},       // periodo de las anomalías
  "meses": [1, …, 12],                               // temporada; se agrupa por año calendario
  "calidad": {"min_cobertura_espacial": 0.9, "meses_completos": true, "min_anios": 10, "min_fraccion_referencia": 0.8},
  "estadistica": {"metodos": ["sen_mann_kendall", "mco"], "nivel": 0.95},
  "vista": {"centro": [lat, lon], "zoom": 8, "anio_visible": 2024, "capa": "anomalia_anual" | "tendencia_celda" | "peso_celda", "estilo": "divergente"},
  "panel": "resultados"
}
```

* La **fecha de la capa** (`vista.anio_visible`) solo cambia lo que se ve en el mapa; la tendencia usa siempre `periodo`.
* `consulta_id = "C-" + SHA-256(JSON canónico del núcleo científico)[0:24]`. El núcleo excluye `vista`,
  `idioma`, `titulo` y `panel`: dos enlaces con la misma zona y parámetros comparten identificador.
* `ETDEstado.validar` aplica una lista blanca: lo desconocido se descarta (nunca viaja una clave o un token);
  valores fuera de rango → `parametro_invalido`; versión mayor → `version_futura`; otra versión → `version_no_admitida`
  (punto de entrada `migrar()` para futuras versiones).

## 3. Enlace

`https://<url_publica>/#inv=<codificación>[&r=<resultado_id>]`

* `<codificación>` = `z` + base64url(deflate-raw(JSON)) o `j` + base64url(JSON) si el navegador no comprime.
* Las unidades administrativas viajan por **código + `hash_geometria`** (SHA-256 de la geometría): al abrir se
  reconstruye la geometría desde `data/admin/` y, si el hash no coincide, se avisa de que los límites cambiaron.
* Las geometrías dibujadas viajan completas, redondeadas a 6 decimales (~0,1 m). Por encima de 16 000
  caracteres no se ofrece el enlace y se pide compartir el expediente ZIP.
* `&r=` guarda el `resultado_id` del informe: al abrir, la app recalcula y dice si el resultado coincide o si
  es una **revisión nueva** (la fuente cambió), sin perder la identidad del original.
* La base sale de `SICC_CONFIG.url_publica` cuando la página se abre en `localhost`/`file:`; un enlace
  `localhost` se marca como no compartible con terceros.
* Se usa el fragmento (`#`) y no la consulta (`?`): no llega a los registros del servidor y no requiere backend.

## 4. Resultados (`etd-resultados`, versión 1)

Campos principales: `consulta_id`, `consulta`, `area`, `cobertura` (área solicitada, área cubierta por
datos, fracción, celdas con datos, huella del punto), `fuente` (versión de la API, fuentes declaradas,
fecha de acceso, periodo descargado, fallos), `variable`, `celdas` (peso, estado, media, tendencia y
anomalía del año visible por celda), `mensual` (serie espacial mensual con cobertura), `serie` (valor
anual o de temporada, anomalía, meses faltantes, estado), `resumen`, `referencia`, `tendencia`,
`ciclo_estacional`, `comparacion_periodos`, `calidad` (avisos y motivos), `datos_celdas` (valores mensuales
por celda) y `generado_utc`.

`resultado_id = "R-" + SHA-256(consulta_id, version_codigo, versión de la API, celdas y pesos, datos_celdas)[0:32]`.
No incluye la fecha de generación ni la de acceso: los mismos datos dan el mismo identificador.
`ETDAnalisis.verificar(res)` recalcula la huella al abrir un `resultados.json`.

## 5. Persistencia

El alojamiento actual (Render, sitio estático sin servidor de aplicación ni base de datos) no permite
guardar investigaciones en un identificador persistente. Por eso:

* **Enlace a la consulta**: implementado (autocontenido en la URL).
* **Resultado guardado**: implementado como archivo. El ZIP contiene `resultados.json` con su huella; «Abrir
  expediente guardado» lo muestra sin descargar datos y rechaza archivos alterados.
* **Enlace persistente a un resultado inmutable**: pendiente. Requiere un almacén (por ejemplo, un servicio
  web de Render con disco o un bucket de objetos) que guarde `resultados.json` bajo su `resultado_id` y una
  ruta `/r/<resultado_id>` que lo devuelva. El esquema ya separa consulta y resultado para ello.
