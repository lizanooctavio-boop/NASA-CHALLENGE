"""Bosque y lagos de Nicaragua con productos derivados de Landsat (15-11-2026).

Fuentes públicas sin cuenta, ambas a 30 m (0,00025°) y construidas con el archivo Landsat:
- Hansen Global Forest Change v1.12 (Hansen et al. 2013; 2001–2024): año de pérdida de cubierta arbórea y cubierta
  arbórea del año 2000. Tesela 20N_090W (10–20° N, 80–90° O), que contiene todo el país.
- JRC Global Surface Water, clasificación anual 1984–2021 (Pekel et al. 2016): 0 sin observación, 1 tierra,
  2 agua estacional, 3 agua permanente. Se leen por rangos de bytes solo las ventanas de los lagos.

Uso (desde la raíz del repositorio):
    python data/recursos/hallazgos/generar_landsat.py --cache <carpeta fuera del repo> [--solo bosque lagos]
"""
import argparse
import csv
import json
import os
import sys
import urllib.request
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
HANSEN = "https://storage.googleapis.com/earthenginepartners-hansen/GFC-2024-v1.12/Hansen_GFC-2024-v1.12_{}_20N_090W.tif"
GSW = ("https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GSWE/YearlyClassification/LATEST/tiles/"
       "yearlyClassification{a}/yearlyClassification{a}{sep}0000240000-0000360000.tif")  # 2021 usa «_», el resto «-»
REGIONES = ("NIC", "pacifico", "central", "caribe")
UMBRAL_BOSQUE = 30  # % de cubierta arbórea en 2000, umbral habitual de Hansen et al. (2013)
# Ventanas (lat mín, lat máx, lon mín, lon máx) que contienen cada lago; el lago es la mancha de agua más grande.
LAGOS = {"cocibolca": (10.95, 12.25, -86.05, -84.70), "xolotlan": (12.05, 12.50, -86.80, -86.15)}
GRADO_KM = 111.32
PASO = 0.00025


def bajar(url, destino):
    if not destino.is_file() or destino.stat().st_size == 0:
        with urllib.request.urlopen(url, timeout=3600) as r:
            destino.write_bytes(r.read())
    return destino


def escribir(nombre, columnas, filas):
    with open(AQUI / nombre, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(columnas)
        w.writerows(filas)


def bosque(cache):
    import rasterio
    from rasterio.features import geometry_mask
    from rasterio.windows import Window, from_bounds

    geo = json.loads((RAIZ / "data/regiones_nicaragua.geojson").read_text(encoding="utf-8"))
    formas = {f["properties"]["id"]: f["geometry"] for f in geo["features"] if f["properties"]["id"] in REGIONES}
    perdida = {r: np.zeros(25) for r in REGIONES}  # índice = código de año (1 → 2001 … 24 → 2024)
    bosque_2000 = dict.fromkeys(REGIONES, 0.0)
    with rasterio.open(bajar(HANSEN.format("lossyear"), cache / "hansen_lossyear_20N_090W.tif")) as fl, \
         rasterio.open(bajar(HANSEN.format("treecover2000"), cache / "hansen_treecover2000_20N_090W.tif")) as ft:
        total = from_bounds(-88.0, 10.5, -82.5, 15.2, fl.transform).round_offsets().round_lengths()
        for fila in range(int(total.row_off), int(total.row_off + total.height), 2000):
            v = Window(total.col_off, fila, total.width, min(2000, total.row_off + total.height - fila))
            perd, cub = fl.read(1, window=v), ft.read(1, window=v)
            tr = fl.window_transform(v)
            lat = tr.f + (np.arange(v.height) + 0.5) * tr.e
            area = (PASO * GRADO_KM) ** 2 * np.cos(np.deg2rad(lat))[:, None] * np.ones((1, int(v.width)))
            es_bosque = cub >= UMBRAL_BOSQUE
            for r, forma in formas.items():
                dentro = ~geometry_mask([forma], out_shape=perd.shape, transform=tr)
                sel = dentro & es_bosque
                if not sel.any():
                    continue
                bosque_2000[r] += float(area[sel].sum())
                perdida[r] += np.bincount(perd[sel], weights=area[sel], minlength=25)[:25]
    filas = [[r, 2000 + k, round(float(perdida[r][k]), 2), round(bosque_2000[r], 1)] for r in REGIONES for k in range(1, 25)]
    escribir("hansen_perdida_bosque_anual.csv", ["region", "anio", "perdida_km2", "bosque_2000_km2"], filas)


def lagos(cache):
    import rasterio
    from rasterio.windows import from_bounds
    from scipy import ndimage

    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
    anios = range(1984, 2022)
    filas = []
    for lago, (la0, la1, lo0, lo1) in LAGOS.items():
        agua, validos = {}, {}
        for a in anios:
            with rasterio.open("/vsicurl/" + GSW.format(a=a, sep="_" if a == 2021 else "-")) as f:
                v = from_bounds(lo0, la0, lo1, la1, f.transform).round_offsets().round_lengths()
                c = f.read(1, window=v)
                fila0 = f.window_transform(v).f
            agua[a], validos[a] = np.packbits(c >= 2), np.packbits(c > 0)
            forma = c.shape
        # Máscara fija del lago: la mancha más grande de todo lo que fue agua algún año (así se ven sequías y crecidas).
        alguna = np.zeros(forma, bool)
        for a in anios:
            alguna |= np.unpackbits(agua[a], count=alguna.size).reshape(forma).astype(bool)
        etiquetas, n = ndimage.label(alguna)
        mayor = np.argmax(np.bincount(etiquetas.ravel())[1:]) + 1
        mascara = etiquetas == mayor
        lat = fila0 - (np.arange(forma[0]) + 0.5) * PASO
        area = (PASO * GRADO_KM) ** 2 * np.cos(np.deg2rad(lat))[:, None] * np.ones((1, forma[1]))
        area_mascara = float(area[mascara].sum())
        for a in anios:
            w = np.unpackbits(agua[a], count=alguna.size).reshape(forma).astype(bool) & mascara
            v = np.unpackbits(validos[a], count=alguna.size).reshape(forma).astype(bool) & mascara
            vista = float(area[v].sum()) / area_mascara
            # Nubes y huecos: el agua se estima sobre lo observado y se escala a toda la máscara.
            agua_km2 = float(area[w].sum()) / float(area[v].sum()) * area_mascara if v.any() else float("nan")
            filas.append([lago, a, round(agua_km2, 2), round(vista, 3), round(area_mascara, 1)])
    escribir("gsw_lagos_nicaragua_anual.csv", ["lago", "anio", "agua_km2", "fraccion_observada", "area_maxima_km2"], filas)


PASOS = {"bosque": bosque, "lagos": lagos}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", type=Path, required=True, help="carpeta para las descargas (no se versiona)")
    ap.add_argument("--solo", nargs="*", choices=sorted(PASOS), help="ejecutar solo estos pasos")
    args = ap.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    for nombre in args.solo or PASOS:
        PASOS[nombre](args.cache)
        print("hecho:", nombre, file=sys.stderr)


if __name__ == "__main__":
    main()
