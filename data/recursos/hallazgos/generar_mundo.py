"""Hielo, agua, incendios y química del océano más allá de Nicaragua (14-11-2026), para quien amplíe el proyecto.

Fuentes públicas sin cuenta:
- GlaMBIE 1.0.0 (WGMS): balance de masa glaciar anual por región, año civil, 2000–2023.
- GRACE/GRACE-FO, mascones CSR RL06.03 (UT Austin) con su máscara de tierra: masa de Groenlandia (tierra al norte de
  59° N entre 75° y 10° O) y de la Antártida (tierra al sur de 60° S), y agua total almacenada sobre Nicaragua.
- GFED5 (Chen et al. 2023, Zenodo 7668424): área quemada mensual 0,25°, 2001–2020.
- OceanSODA-ETHZ v2025 (NCEI 0220059): pH y saturación de aragonito superficiales, 1°, mensual, 1982–2024; se leen por
  rangos de bytes solo las celdas del Caribe.

Uso (desde la raíz del repositorio):
    python data/recursos/hallazgos/generar_mundo.py --cache <carpeta fuera del repo> [--solo glaciares grace ...]
"""
import argparse
import csv
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

import h5py
import numpy as np
import shapely
from shapely.geometry import shape

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
GLAMBIE = "https://wgms.ch/downloads/GlaMBIE_Data_DOI_10.5904_wgms-glambie-2024-07.zip"
REGIONES_GLAMBIE = ["0_global", "1_alaska", "2_western_canada_us", "3_arctic_canada_north", "4_arctic_canada_south",
                    "5_greenland_periphery", "16_low_latitudes", "17_southern_andes"]
CSR = "https://download.csr.utexas.edu/outgoing/grace/RL0603_mascons/"
CSR_MASCONES, CSR_TIERRA = "CSR_GRACE_GRACE-FO_RL0603_Mascons_all-corrections.nc", "CSR_GRACE_GRACE-FO_RL06_Mascons_v02_LandMask.nc"
GFED5 = "https://zenodo.org/records/7668424/files/BA.zip?download=1"
OCEANSODA = "https://www.ncei.noaa.gov/data/oceans/ncei/ocads/data/0220059/OceanSODA_ETHZ-v2025.OCADS.01-1982-2024.nc"
CAJAS_OCEANO = {"mar_caribe_nic": ((10, 16), (-84, -78)), "caribe": ((10, 22), (-88, -60))}
RADIO = 6371e3


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


def glaciares(cache):
    with zipfile.ZipFile(bajar(GLAMBIE, cache / "glambie.zip")) as z:
        filas = []
        for region in REGIONES_GLAMBIE:
            with z.open(f"glambie_results_20240716/calendar_years/{region}.csv") as f:
                for r in csv.DictReader(line.decode() for line in f):
                    filas.append([region.split("_", 1)[1], int(float(r["start_dates"])), round(float(r["combined_gt"]), 3),
                                  round(float(r["combined_gt_errors"]), 3)])
    escribir("glambie_america_anual.csv", ["region", "anio", "cambio_masa_gt", "error_gt"], filas)


def grace(cache):
    with h5py.File(bajar(CSR + CSR_MASCONES, cache / "csr_mascons.nc")) as f, \
         h5py.File(bajar(CSR + CSR_TIERRA, cache / "csr_landmask.nc")) as m:
        lat, lon = f["lat"][:], f["lon"][:]
        fecha = np.datetime64("2002-01-01") + np.floor(f["time"][:]).astype(int).astype("timedelta64[D]")
        lwe = f["lwe_thickness"]  # cm de agua equivalente
        tierra = m["LO_val"][:] > 0.5
        lon180 = np.where(lon > 180, lon - 360, lon)
        LON, LAT = np.meshgrid(lon180, lat)
        area = RADIO ** 2 * np.deg2rad(0.25) ** 2 * np.cos(np.deg2rad(LAT))
        mantos = {"groenlandia": tierra & (LAT > 59) & (LON > -75) & (LON < -10), "antartida": tierra & (LAT < -60)}
        geo = json.loads((RAIZ / "data/regiones_nicaragua.geojson").read_text(encoding="utf-8"))
        nic = next(shape(x["geometry"]) for x in geo["features"] if x["properties"]["id"] == "NIC")
        caja = (LAT > 10) & (LAT < 15.5) & (LON > -88) & (LON < -82.5)
        celdas_nic = np.zeros_like(tierra)
        celdas_nic[caja] = [nic.contains(shapely.Point(float(x), float(y))) for x, y in zip(LON[caja], LAT[caja])]
        filas = []
        for i, d in enumerate(fecha):
            capa = lwe[i]
            fila = [str(d)[:7]]
            for sel in mantos.values():  # Gt = cm/100 · m² · 1000 kg/m³ / 1e12
                fila.append(round(float(np.sum(capa[sel] / 100 * area[sel]) * 1000 / 1e12), 2))
            fila.append(round(float(np.sum(capa[celdas_nic] * area[celdas_nic]) / area[celdas_nic].sum()), 3))
            filas.append(fila)
    escribir("grace_csr_mensual.csv", ["mes", "groenlandia_gt", "antartida_gt", "nicaragua_agua_cm"], filas)


def acidificacion(cache):
    import fsspec  # lectura remota por rangos: el archivo completo pesa 1,2 GB
    with fsspec.open(OCEANSODA, block_size=2 ** 22).open() as remoto, h5py.File(remoto) as h:
        lat, lon = h["lat"][:], h["lon"][:]
        fecha = np.datetime64("1982-01-15") + h["time"][:].astype(int).astype("timedelta64[D]")
        filas = []
        for zona, (la, lo) in CAJAS_OCEANO.items():
            i = np.flatnonzero((lat >= la[0]) & (lat <= la[1]))
            j = np.flatnonzero((lon >= lo[0]) & (lon <= lo[1]))
            series = {}
            for var in ("ph_total", "omega_ar"):
                x = h[var][:, i.min():i.max() + 1, j.min():j.max() + 1].astype(float)
                x[~np.isfinite(x) | (x > 1e10)] = np.nan
                peso = np.cos(np.deg2rad(lat[i]))[None, :, None] * np.isfinite(x)
                series[var] = np.nansum(np.nan_to_num(x) * peso, (1, 2)) / peso.sum((1, 2))
            filas += [[zona, str(d)[:7], round(float(series["ph_total"][k]), 5), round(float(series["omega_ar"][k]), 4)]
                      for k, d in enumerate(fecha)]
    escribir("oceansoda_caribe_mensual.csv", ["zona", "mes", "ph_total", "omega_aragonito"], filas)


PASOS = {"glaciares": glaciares, "grace": grace, "acidificacion": acidificacion}


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
