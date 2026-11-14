"""Océano y costa alrededor de Nicaragua: temperatura del mar, nivel del mar y ciclones (14-11-2026).

Fuentes públicas sin cuenta:
- NOAA ERSSTv5, un NetCDF mensual por archivo desde NCEI (2°). Caja del Caribe frente a Nicaragua: celdas centradas en
  12 y 14° N, 82 y 80° O, todas de océano. OISST diario se descartó: el servidor THREDDS de PSL devolvía 502 y 429 al
  recortarlo y la descarga global diaria de NCEI ronda 26 GB.
- PSMSL, nivel del mar relativo anual (RLR) de mareógrafos del Caribe y Panamá con registro moderno largo. Los registros
  largos de la costa centroamericana terminan entre 1966 y 2000; los nuevos (Limón B desde 2010) aún son cortos.
- NOAA IBTrACS v04r01 (Atlántico Norte y Pacífico Este): ciclones con algún punto de trayectoria en el rectángulo de
  Nicaragua ampliado 1,5° (unos 150 km) y su viento máximo dentro de él.

Uso (desde la raíz del repositorio):
    python data/recursos/hallazgos/generar_oceano.py --cache <carpeta fuera del repo>
"""
import argparse
import csv
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np
from scipy.io import netcdf_file

AQUI = Path(__file__).resolve().parent
ERSST = "https://www.ncei.noaa.gov/pub/data/cmb/ersst/v5/netcdf/ersst.v5.{ym}.nc"
CAJA_SST = {"lat": (12.0, 14.0), "lon": (278.0, 280.0)}
PSMSL = "https://psmsl.org/data/obtaining/rlr.annual.data/{id}.rlrdata"
ESTACIONES = {1001: "San Juan", 759: "Magueyes Island", 1393: "Charlotte Amalie", 163: "Balboa", 188: "Key West"}
IBTRACS = "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.{b}.list.v04r01.csv"
ZONA = {"lat": (10.74 - 1.5, 15.0 + 1.5), "lon": (-87.68 - 1.5, -83.16 + 1.5)}


def bajar(url, destino, refrescar=False):
    if refrescar or not destino.is_file() or destino.stat().st_size == 0:
        with urllib.request.urlopen(url, timeout=900) as r:
            destino.write_bytes(r.read())
    return destino


def leer_ersst(ruta):
    """Los archivos antiguos son NetCDF3 y los recientes NetCDF4."""
    if ruta.read_bytes()[:3] == b"CDF":
        v = netcdf_file(ruta, "r", mmap=False).variables
        s = v["sst"][:].astype(float)
        if hasattr(v["sst"], "_FillValue"):
            s[s == v["sst"]._FillValue] = np.nan
        s = s * getattr(v["sst"], "scale_factor", 1.0) + getattr(v["sst"], "add_offset", 0.0)
        lat, lon = v["lat"][:].copy(), v["lon"][:].copy()
    else:
        with h5py.File(ruta) as f:
            s, lat, lon = f["sst"][:].astype(float), f["lat"][:], f["lon"][:]
    s = s.reshape(-1, len(lat), len(lon))[0]
    i = [int(np.flatnonzero(lat == x)[0]) for x in CAJA_SST["lat"]]
    j = [int(np.flatnonzero(lon == x)[0]) for x in CAJA_SST["lon"]]
    celdas = s[np.ix_(i, j)]
    celdas[(celdas < -5) | (celdas > 40)] = np.nan
    if np.isnan(celdas).any():
        raise ValueError(f"{ruta.name}: celda sin dato en la caja")
    return float(celdas.mean())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", type=Path, required=True, help="carpeta para las descargas (no se versiona)")
    args = ap.parse_args()
    (args.cache / "ersst").mkdir(parents=True, exist_ok=True)

    hoy = datetime.now(timezone.utc)
    meses = [f"{a}{m:02d}" for a in range(1981, hoy.year + 1) for m in range(1, 13) if (a, m) < (hoy.year, hoy.month)]

    def mes(ym):
        try:
            return ym, leer_ersst(bajar(ERSST.format(ym=ym), args.cache / "ersst" / f"ersst.v5.{ym}.nc"))
        except OSError:  # mes aún no publicado
            return ym, None

    with ThreadPoolExecutor(8) as ex:
        sst = [x for x in ex.map(mes, meses) if x[1] is not None]
    with open(AQUI / "ersst_caribe_nicaragua.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["anio", "mes", "sst_c"])
        w.writerows([ym[:4], int(ym[4:]), round(v, 4)] for ym, v in sst)

    with open(AQUI / "psmsl_nivel_mar_anual.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["estacion", "nombre", "anio", "nivel_mm", "dias_faltantes", "bandera"])
        for id_, nombre in ESTACIONES.items():
            ruta = bajar(PSMSL.format(id=id_), args.cache / f"psmsl_{id_}.rlrdata", refrescar=True)
            for linea in ruta.read_text().splitlines():
                anio, valor, faltan, bandera = (x.strip() for x in linea.split(";"))
                if int(valor) != -99999:
                    w.writerow([id_, nombre, anio, valor, faltan, bandera])

    tormentas = {}
    for cuenca in ("NA", "EP"):
        ruta = bajar(IBTRACS.format(b=cuenca), args.cache / f"ibtracs_{cuenca}.csv")  # ~60 MB: borrar para refrescar
        with ruta.open(encoding="utf-8") as f:
            r = csv.reader(f)
            cab = next(r)
            next(r)  # fila de unidades
            c = {k: cab.index(k) for k in ("SID", "SEASON", "NAME", "LAT", "LON", "USA_WIND", "WMO_WIND")}
            for fila in r:
                lat, lon = float(fila[c["LAT"]]), float(fila[c["LON"]])
                if not (ZONA["lat"][0] <= lat <= ZONA["lat"][1] and ZONA["lon"][0] <= lon <= ZONA["lon"][1]):
                    continue
                viento = fila[c["USA_WIND"]].strip() or fila[c["WMO_WIND"]].strip()
                sid = fila[c["SID"]]
                previo = tormentas.get(sid, (int(fila[c["SEASON"]]), fila[c["NAME"]], cuenca, 0.0))
                tormentas[sid] = previo[:3] + (max(previo[3], float(viento) if viento else 0.0),)
    with open(AQUI / "ibtracs_cerca_nicaragua.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["sid", "temporada", "nombre", "cuenca", "viento_max_kt"])
        w.writerows([sid, *v[:3], v[3]] for sid, v in sorted(tormentas.items(), key=lambda x: (x[1][0], x[0])))

    ruta = AQUI / "fuentes.json"
    fuentes = json.loads(ruta.read_text(encoding="utf-8"))
    fuentes.update({
        "ersst": {"producto": "NOAA ERSSTv5 (Extended Reconstructed SST), 2°", "url": "https://www.ncei.noaa.gov/products/extended-reconstructed-sst",
                  "caja": "12–14° N, 80–82° W (cell centres)", "ultimo_mes": sst[-1][0]},
        "psmsl": {"producto": "PSMSL Revised Local Reference annual means", "url": "https://psmsl.org/", "estaciones": ESTACIONES},
        "ibtracs": {"producto": "NOAA IBTrACS v04r01", "url": "https://www.ncei.noaa.gov/products/international-best-track-archive",
                    "zona": ZONA, "generado_utc": hoy.isoformat(timespec="seconds")},
    })
    ruta.write_text(json.dumps(fuentes, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
