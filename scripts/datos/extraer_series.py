"""Recalcula data/serie_mensual.csv desde los HDF5 mensuales de IMERG Final V07B (opcional: requiere los originales).

Pondera por el área de cada celda de 0,1° dentro de cada dominio de data/dominios.geojson. Uso:
    python scripts/datos/extraer_series.py --hdf5 <carpeta con los 288 .HDF5>
"""
import argparse
import calendar
import csv
import json
import re
from pathlib import Path

import h5py
import numpy as np
import shapely
from shapely import box
from shapely.geometry import shape

from comun import ANIOS, CAJA, COBERTURA_MINIMA, DATOS, DOMINIOS, VARIABLE, a_6933, proyectar_6933, sha256

PATRON = re.compile(r"3B-MO\.MS\.MRG\.3IMERG\.(\d{4})(\d{2})01-S\d{6}-E\d{6}\.\d{2}\.(V07[A-Z]?)\.HDF5$")
URL = "https://data.gesdisc.earthdata.nasa.gov/data/GPM_L3/GPM_3IMERGM.07/{anio}/{nombre}"
CAJA_6933 = "_caja_sicc_6933"  # solo para comprobar la ponderación esférica; no se publica como dominio


def bordes(centros):
    """Bordes de celda de una malla regular; se redondean centros y paso a 1e-4° (los centros son float32)."""
    c = np.asarray(centros, float)
    paso = np.diff(c)
    if len(c) < 2 or not np.allclose(paso, paso[0], atol=1e-4) or paso[0] == 0:
        raise ValueError("Coordenadas no regulares: no se infieren los bordes de celda.")
    c = np.round(c, 4)
    h = round(abs(float(paso[0])), 4) / 2
    return np.round(c - h, 6), np.round(c + h, 6)


def solape(a0, a1, b0, b1):
    return np.clip(np.minimum(a1, b1) - np.maximum(a0, b0), 0, None)


def pesos_caja_esferica(lat, lon):
    """Área esférica relativa (proporcional a Δλ·[sen φ₂ − sen φ₁]) de cada celda dentro de la caja."""
    la0, la1 = bordes(lat)
    lo0, lo1 = bordes(lon)
    (s, n), (o, e) = CAJA["lat"], CAJA["lon"]
    ini, fin = np.maximum(la0, s), np.minimum(la1, n)
    dlat = np.where(fin > ini, np.sin(np.radians(fin)) - np.sin(np.radians(ini)), 0.0)
    return np.outer(dlat, np.radians(solape(lo0, lo1, o, e)))


def cargar_geometrias(ruta):
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    g = {f["id"]: shape(f["geometry"]) for f in datos["features"]}
    if tuple(g) != DOMINIOS:
        raise ValueError(f"Dominios inesperados en {ruta}: {tuple(g)}")
    return g


def preparar_malla(lat, lon, geoms):
    sur = min(g.bounds[1] for g in geoms.values())
    norte = max(g.bounds[3] for g in geoms.values())
    oeste = min(g.bounds[0] for g in geoms.values())
    este = max(g.bounds[2] for g in geoms.values())
    la0, la1 = bordes(lat)
    lo0, lo1 = bordes(lon)
    j = np.flatnonzero((la0 < norte) & (la1 > sur))
    i = np.flatnonzero((lo0 < este) & (lo1 > oeste))
    x0, x1 = a_6933(lo0[i], np.zeros(len(i)))[0], a_6933(lo1[i], np.zeros(len(i)))[0]
    y0, y1 = a_6933(np.zeros(len(j)), la0[j])[1], a_6933(np.zeros(len(j)), la1[j])[1]
    celdas = box(x0[None, :], y0[:, None], x1[None, :], y1[:, None])  # celdas rectangulares exactas en EPSG:6933
    area = lambda g: shapely.area(shapely.intersection(celdas, proyectar_6933(g)))
    pesos = {k: area(g) for k, g in geoms.items() if k != "caja_sicc"}
    pesos["caja_sicc"] = pesos_caja_esferica(lat[j], lon[i])
    pesos[CAJA_6933] = area(geoms["caja_sicc"])
    return j, i, pesos


def leer(carpeta, geoms):
    rutas = sorted(Path(carpeta).glob("*.HDF5"))
    meses = [(a, m) for a in ANIOS for m in range(1, 13)]
    leidos = []
    for r in rutas:
        m = PATRON.search(r.name)
        if not m:
            raise ValueError(f"Nombre no reconocido como IMERG Final mensual V07: {r.name}")
        leidos.append((int(m[1]), int(m[2]), m[3]))
    if leidos != [(a, m, "V07B") for a, m in meses]:
        raise ValueError("Se esperaban exactamente los 288 mensuales V07B de 2001 a 2024, sin huecos ni duplicados.")
    with h5py.File(rutas[0]) as f:
        lat, lon = f["Grid/lat"][:], f["Grid/lon"][:]
    j, i, pesos = preparar_malla(lat, lon, geoms)
    series = {k: [] for k in pesos}
    for ruta, (anio, mes) in zip(rutas, meses):
        with h5py.File(ruta) as f:
            ds = f[VARIABLE]
            assert ds.shape == (1, len(lon), len(lat)), ds.shape
            unidades = ds.attrs["units"]
            unidades = unidades.decode() if isinstance(unidades, bytes) else str(np.asarray(unidades).ravel()[0])
            assert unidades == "mm/hr", unidades
            assert np.array_equal(lat, f["Grid/lat"][:]) and np.array_equal(lon, f["Grid/lon"][:])
            tasa = ds[0, i[0]:i[-1] + 1, j[0]:j[-1] + 1].T.astype(float)
        valido = np.isfinite(tasa) & (tasa >= 0)  # el relleno -9999.9 queda excluido
        horas = 24 * calendar.monthrange(anio, mes)[1]
        for k, w in pesos.items():
            sel = (w > 0) & valido
            cobertura = float(w[sel].sum() / w.sum())
            if cobertura < COBERTURA_MINIMA:
                raise ValueError(f"Cobertura insuficiente: {ruta.name}, {k}, {cobertura}")
            series[k].append((anio, mes, float(np.average(tasa[sel], weights=w[sel])) * horas, cobertura))
    return rutas, series, {k: int(np.count_nonzero(w)) for k, w in pesos.items()}


def anuales(filas):
    return np.array([sum(mm for y, _, mm, _ in filas if y == a) for a in ANIOS])


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hdf5", required=True, type=Path)
    ap.add_argument("--geometrias", type=Path, default=DATOS / "dominios.geojson")
    a = ap.parse_args()
    rutas, series, celdas = leer(a.hdf5, cargar_geometrias(a.geometrias))
    (DATOS / "fuentes").mkdir(exist_ok=True)
    with (DATOS / "serie_mensual.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["dominio", "anio", "mes", "mm", "cobertura"])
        for k in DOMINIOS:
            for anio, mes, mm, cob in series[k]:
                w.writerow([k, anio, mes, repr(mm), repr(cob)])
    with (DATOS / "fuentes" / "manifiesto_imerg.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["archivo", "bytes", "sha256", "url"])
        for r in rutas:
            w.writerow([r.name, r.stat().st_size, sha256(r), URL.format(anio=PATRON.search(r.name)[1], nombre=r.name)])
    esf, ig = anuales(series["caja_sicc"]), anuales(series[CAJA_6933])
    comp = {"celdas_con_peso": {k: v for k, v in celdas.items() if k != CAJA_6933},
            "caja_esferica_vs_6933": {"celdas_con_peso_6933": celdas[CAJA_6933],
                                      "max_dif_anual_mm": float(np.abs(esf - ig).max()),
                                      "max_dif_anual_relativa": float((np.abs(esf - ig) / esf).max())}}
    (DATOS / "fuentes" / "comprobaciones_extraccion.json").write_text(
        json.dumps(comp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(comp, ensure_ascii=False, indent=2))
