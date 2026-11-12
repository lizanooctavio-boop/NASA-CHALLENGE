# Preparación de datos climáticos

Genera y verifica los archivos derivados de `data/` que consume la demo. La interfaz **no** necesita los HDF5 de IMERG, el repositorio privado de SICC-952 ni credenciales. El formato de los archivos está en [`data/contrato.md`](../../data/contrato.md).

## Qué hay aquí

| Script | Entrada | Salida | Dependencias |
|---|---|---|---|
| `verificar_clima.py` | `data/` | informe en pantalla; código de salida 1 si algo falla | numpy, scipy (shapely opcional) |
| `generar_clima.py` | `serie_mensual.csv`, ONI, `dominios.geojson`, comprobaciones | `data/clima.json` | numpy, scipy |
| `preparar_oni.py` | `oni.ascii.txt` de NOAA CPC (se descarga solo) | `data/fuentes/oni_2001_2024.csv` | biblioteca estándar |
| `geometrias.py` | `mundo.geojson` del proyecto SICC-952 (privado) | `data/dominios.geojson` | shapely, pyproj |
| `extraer_series.py` | los 288 HDF5 mensuales de IMERG | `serie_mensual.csv`, `fuentes/manifiesto_imerg.csv`, `fuentes/comprobaciones_extraccion.json` | + h5py |
| `sensibilidad_geometria.py` | los 288 HDF5 | `fuentes/sensibilidad_geometria.json` | + h5py |
| `tendencia.py`, `comun.py` | — | módulos compartidos | numpy, scipy |

`tendencia.py` es copia sin cambios de `sicc952/tendencia.py` (SHA-256 `0f493432cc9f496f1b6d0a83ed20d1669ff2bd0df67b73bb5f0a7b7ffe2f5abd`), el único código de SICC-952 incluido: es el que define el veredicto. No se copió ningún módulo de cultivos.

## Verificar (sin HDF5)

```text
pip install -r scripts/datos/requirements.txt
python scripts/datos/verificar_clima.py
```

Comprueba: archivos y SHA-256; estructura del contrato; 24 años completos por dominio y 288 meses; que cada serie anual sea la suma de sus 12 meses; las pendientes de referencia (caja −13,132; Nicaragua −62,332; Honduras −35,005; Costa Rica −201,224 mm/década, ±0,0005) y el veredicto `metodos_discrepan` de Costa Rica; que regenerar desde los CSV reproduzca `clima.json`; la superposición y las áreas (si hay shapely); y que no haya rutas locales en los textos.

Opciones: `--diagnostico <resultado.json>` compara con el diagnóstico original de SICC-952; `--hdf5 <carpeta>` comprueba tamaño y SHA-256 de los 288 archivos contra el manifiesto.

## Regenerar

```text
python scripts/datos/generar_clima.py                         # clima.json desde los CSV derivados
pip install -r scripts/datos/requirements-extraccion.txt
python scripts/datos/extraer_series.py --hdf5 <carpeta>       # serie_mensual.csv desde los HDF5
python scripts/datos/sensibilidad_geometria.py --hdf5 <carpeta>
python scripts/datos/geometrias.py --mapa <ruta>/mundo.geojson  # solo si cambia la geometría
python scripts/datos/preparar_oni.py                          # solo si se actualiza el ONI
```

Los HDF5 se descargan de NASA GES DISC (requiere cuenta Earthdata); sus nombres, tamaños y SHA-256 están en `data/fuentes/manifiesto_imerg.csv`. Tras regenerar, ejecutar siempre `verificar_clima.py`. Comprobado el 11-11-2026 con Python 3.13, numpy 2.5.4, scipy 1.18.1, shapely 2.2.0, pyproj 3.8.0 y h5py 3.16.0.

## Revisión de los supuestos del diagnóstico

Se revisó `comparar_dominios.py` (diagnóstico de SICC-952 del 11-11-2026) y se reutilizó su lógica. Resultado:

* **Reproducción.** Las series, pendientes, intervalos, veredictos y correlaciones ONI coinciden con `resultado.json` (`verificar_clima.py --diagnostico`). Las celdas con peso también: 551 (caja), 1116 (NIC), 1067 (HND), 512 (CRI) y 717 (NIC fuera de la caja).
* **Ponderación mixta.** Países con área en EPSG:6933 y caja con área esférica. Recalculada la caja en EPSG:6933, el acumulado anual cambia ≤ 0,016 mm: la mezcla no afecta.
* **Lagos.** Se restan de los países pero no de la caja. Sus celdas siguen teniendo lluvia IMERG; la diferencia cuenta en la comparación caja–Nicaragua.
* **Contorno.** Dilatar o erosionar los países 0,05° no cambia ningún veredicto, pero mueve la pendiente de Costa Rica entre −178 y −228 mm/década.
* **Costa Rica.** Con el intervalo principal y el HAC la tendencia es negativa; con Theil–Sen y Mann–Kendall (p = 0,097), no concluyente. Se informa como sensible al método.
* **ONI.** Coincide exactamente con el `oni.ascii.txt` vigente de NOAA CPC para 2001–2024 (288 valores). Se usa la media de los trimestres MJJ–OND, centrados en junio–noviembre, frente a la lluvia de junio a noviembre; es una elección de ventana, no la única posible.
* **No resuelto.** No se ha comparado IMERG con estaciones u otros productos (p. ej. CHIRPS); no se ha evaluado homogeneidad de IMERG entre 2001 y 2024; la geometría es la simplificada de SICC-952.

## Pendiente de decisión de Octavio

Visibilidad del repositorio, licencia y publicación de la demo. Los textos de licencia de las fuentes en `clima.json` describen las condiciones de los proveedores, no la licencia de este repositorio.
