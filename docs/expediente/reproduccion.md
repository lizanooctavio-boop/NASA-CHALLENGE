# Expediente por área: reproducir un cálculo

## Desde la aplicación

1. Abre el enlace de la portada del informe (o escanea el QR). La pestaña **Area report** restaura la zona,
   la variable, el periodo, la temporada, la referencia, el nivel de confianza, la capa, el año visible, la
   vista del mapa y el idioma, y vuelve a pedir los datos a NASA POWER.
2. El mensaje dice si el resultado recalculado coincide con el del informe (`R-…`) o si es una revisión nueva.
3. Para ver exactamente el resultado del informe sin descargar nada, usa **Abrir expediente guardado** con
   `resultados.json` del ZIP.

## Desde el paquete ZIP, sin la aplicación

1. Comprueba `manifest.json`: el SHA-256 de cada archivo.
2. `LEEME.txt` lista las peticiones originales a NASA POWER (una por celda, comunidad AG, JSON).
3. Para cada celda: valores mensuales; −999 = faltante. En precipitación, mm/día × días del mes.
4. Valor del área por mes: Σ(peso · valor) / Σ(peso) sobre las celdas con dato, si esas celdas suman al
   menos `min_cobertura_espacial` del peso; si no, faltante. Los pesos están en `area_interes.geojson`
   (capa `celda_nasa_power`) y en `celdas_mensual.csv`.
5. Valor anual: media ponderada por días (temperatura) o suma (precipitación) de los meses seleccionados;
   faltante si falta cualquiera.
6. Tendencia: `src/estadistica.js` (`SofEstadistica.analizar`) sobre los años válidos; pendientes × 10 por década.
   `scipy.stats.theilslopes` y `scipy.stats.linregress` dan las mismas pendientes (prueba
   `tests/test_expediente.py::test_pendientes_coinciden_con_scipy`).

## Pruebas

```bash
python -m pytest tests/test_expediente.py                     # geometría, estado, análisis, ZIP y PDF (Node + Python)
ETD_E2E=1 python -m pytest tests/test_expediente.py -k Navegador   # recorrido completo en Chromium (varios minutos)
# Sin acceso a los CDN: ETD_NODE_MODULES=/ruta/a/node_modules con leaflet, chart.js, three@0.160.0 y proj4@2.9.2
```

Los datos de prueba son respuestas reales de NASA POWER v2.10.0 descargadas el 2026-11-15
(`tests/fixtures/expediente/`). Los límites se regeneran con:

```bash
python scripts/expediente/preparar_limites.py <carpeta con ineter_municipios.geojson e ineter_departamentos.geojson> 2026-11-15
```
