"""Hallazgos del 14-11-2026: frecuencia de la lluvia en Nicaragua (CHIRPS), ENSO, hielo marino y temperatura por latitud.

Fuentes públicas sin cuenta:
- CHIRPS v2.0 diario 0,25° (UCSB/CHC) recortado en la IRI Data Library, 1981-01-01 hasta el último día publicado.
- ONI de NOAA CPC (temporadas de tres meses).
- NSIDC Sea Ice Index v4 (G02135), extensión mensual de marzo y septiembre, Ártico y Antártico.
- NASA GISTEMP v4, medias anuales por bandas de latitud (ZonAnn.Ts+dSST).

Índices ETCCDI por celda con estadistica/indicadores.indices_lluvia (base 1991–2020) y media simple de las celdas cuyo
centro cae en cada región de data/regiones_nicaragua.geojson. Las celdas se promedian después de calcular el índice:
promediar antes la lluvia diaria inventaría días húmedos.

Uso (desde la raíz del repositorio):
    python data/recursos/hallazgos/generar_hallazgos.py --cache <carpeta fuera del repo>
"""
import argparse
import csv
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import shapely
from scipy.io import netcdf_file
from shapely.geometry import shape

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ / "backend"))
from clima_nic.estadistica import indicadores as ind  # noqa: E402

CHIRPS = ("https://iridl.ldeo.columbia.edu/SOURCES/.UCSB/.CHIRPS/.v2p0/.daily-improved/.global/.0p25/.prcp/"
          "X/-88/-82.5/RANGEEDGES/Y/10.5/15.25/RANGEEDGES/T/(1%20Jan%20{a})/(31%20Dec%20{a})/RANGEEDGES/data.nc")
ONI = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
NSIDC = "https://noaadata.apps.nsidc.org/NOAA/G02135/{h}/monthly/data/{p}_{m}_extent_v4.0.csv"
GISTEMP = "https://data.giss.nasa.gov/gistemp/tabledata_v4/ZonAnn.Ts+dSST.csv"
BANDAS = ["Glob", "64N-90N", "44N-64N", "24N-44N", "EQU-24N", "24S-EQU", "44S-24S", "64S-44S", "90S-64S"]
BASE = range(1991, 2021)


def bajar(url, destino, refrescar=False):
    if refrescar or not destino.is_file() or destino.stat().st_size == 0:
        with urllib.request.urlopen(url, timeout=600) as r:
            destino.write_bytes(r.read())
    return destino


def chirps(cache, fin):
    pr, fechas = [], []
    for a in range(1981, fin + 1):
        f = netcdf_file(bajar(CHIRPS.format(a=a), cache / f"chirps_{a}.nc", refrescar=a == fin), "r", mmap=False)
        p = f.variables["prcp"][:].astype(float)
        p[p < 0] = np.nan  # −9999 sobre el mar
        # T en días julianos (mediodía): JD 2440587,5 = 1970-01-01 00 UTC.
        dias = np.floor(f.variables["T"][:] - 2440587.5).astype(int)
        fechas.append(np.datetime64("1970-01-01") + dias.astype("timedelta64[D]"))
        pr.append(p)
        x, y = f.variables["X"][:].copy(), f.variables["Y"][:].copy()
    return np.concatenate(pr), np.concatenate(fechas).astype("datetime64[D]"), x, y


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", type=Path, required=True, help="carpeta para los NetCDF diarios (no se versiona)")
    ap.add_argument("--fin", type=int, default=datetime.now(timezone.utc).year)
    args = ap.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)

    pr, fechas, xs, ys = chirps(args.cache, args.fin)
    anio = fechas.astype("datetime64[Y]").astype(int) + 1970
    geo = json.loads((RAIZ / "data/regiones_nicaragua.geojson").read_text(encoding="utf-8"))
    regiones = {ft["properties"]["id"]: shape(ft["geometry"]) for ft in geo["features"]}
    celdas = {r: [] for r in regiones}
    for i, y in enumerate(ys):
        for j, x in enumerate(xs):
            s = pr[:, i, j]
            if np.isnan(s).mean() > 0.01:
                continue
            dentro = [r for r, g in regiones.items() if g.contains(shapely.Point(float(x), float(y)))]
            if not dentro:
                continue
            idx, _ = ind.indices_lluvia(fechas, np.nan_to_num(s), BASE)
            for a in idx:
                idx[a]["r1mm"] = int((s[anio == a] >= ind.UMBRAL_HUMEDO).sum())
            for r in dentro:
                celdas[r].append((s, idx))

    # Acumulado de enero hasta el último día publicado del año en curso, para comparar el año parcial con todos los demás.
    ultimo = fechas[-1]
    doy = (fechas - fechas.astype("datetime64[Y]")).astype(int)
    doy_fin = int((ultimo - ultimo.astype("datetime64[Y]")).astype(int))
    with open(AQUI / "chirps_indices_regiones.csv", "w", newline="", encoding="utf-8") as f, \
         open(AQUI / "chirps_acumulado_parcial.csv", "w", newline="", encoding="utf-8") as g:
        w, wg = csv.writer(f, lineterminator="\n"), csv.writer(g, lineterminator="\n")
        w.writerow(["region", "anio", "indice", "valor"])
        wg.writerow(["region", "anio", "desde", "hasta", "mm"])
        for r, cs in celdas.items():
            anios = sorted(set.intersection(*(set(idx) for _, idx in cs)))
            for a in anios:
                for k in cs[0][1][a]:
                    w.writerow([r, a, k, round(float(np.mean([idx[a][k] for _, idx in cs])), 4)])
            media = np.nanmean(np.stack([s for s, _ in cs], 1), 1)
            for a in range(1981, args.fin + 1):
                wg.writerow([r, a, "01-01", str(ultimo)[5:], round(float(media[(anio == a) & (doy <= doy_fin)].sum()), 2)])

    oni = bajar(ONI, args.cache / "oni.ascii.txt", refrescar=True)
    with open(AQUI / "oni_noaa_cpc.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["temporada", "anio", "oni"])
        for linea in oni.read_text().splitlines()[1:]:
            p = linea.split()
            if len(p) == 4:
                w.writerow([p[0], p[1], p[3]])

    with open(AQUI / "nsidc_extension_marzo_septiembre.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["hemisferio", "mes", "anio", "extension_mkm2"])
        for h, p in (("north", "N"), ("south", "S")):
            for m in ("03", "09"):
                ruta = bajar(NSIDC.format(h=h, p=p, m=m), args.cache / f"{p}_{m}.csv", refrescar=True)
                for fila in csv.reader(ruta.read_text().splitlines()[1:]):
                    if fila and float(fila[4]) > 0:  # −9999: mes sin datos
                        w.writerow([p, int(m), int(fila[0]), float(fila[4])])

    zon = list(csv.DictReader(bajar(GISTEMP, args.cache / "ZonAnn.csv", refrescar=True).read_text().splitlines()))
    with open(AQUI / "gistemp_bandas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["anio"] + BANDAS)
        for fila in zon:
            if all(fila[b].strip() not in ("", "***") for b in BANDAS):
                w.writerow([fila["Year"]] + [fila[b] for b in BANDAS])

    # Se actualiza, no se reemplaza: generar_oceano.py añade sus propias fuentes al mismo archivo.
    ruta = AQUI / "fuentes.json"
    fuentes = json.loads(ruta.read_text(encoding="utf-8")) if ruta.is_file() else {}
    fuentes.update({
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "chirps": {"producto": "CHIRPS v2.0 daily 0.25° (UCSB Climate Hazards Center)", "acceso": "IRI Data Library",
                   "url": "https://www.chc.ucsb.edu/data/chirps", "primer_dia": str(fechas[0]), "ultimo_dia": str(ultimo),
                   "base_percentiles": [BASE.start, BASE.stop - 1],
                   "celdas_por_region": {r: len(cs) for r, cs in celdas.items()}},
        "oni": {"producto": "NOAA CPC Oceanic Niño Index (ERSSTv5)", "url": ONI},
        "nsidc": {"producto": "NSIDC Sea Ice Index, Version 4 (G02135)", "url": "https://nsidc.org/data/g02135"},
        "gistemp": {"producto": "NASA GISS GISTEMP v4, zonal annual means", "url": GISTEMP},
    })
    ruta.write_text(json.dumps(fuentes, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
