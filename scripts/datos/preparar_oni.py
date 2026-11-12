"""Extrae el ONI mensual 2001–2024 de oni.ascii.txt (NOAA CPC) a data/fuentes/oni_2001_2024.csv.

Cada trimestre móvil se asigna a su mes central (DJF → enero … NDJ → diciembre). Uso:
    python scripts/datos/preparar_oni.py                      # descarga el archivo de NOAA CPC
    python scripts/datos/preparar_oni.py --origen oni.ascii.txt
"""
import argparse
import csv
import urllib.request
from pathlib import Path

from comun import ANIOS, DATOS

URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
CENTRO = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
          "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}


def leer(texto):
    oni = {}
    for linea in texto.splitlines():
        p = linea.split()
        if len(p) == 4 and p[0] in CENTRO:  # SEAS YR TOTAL ANOM
            oni[int(p[1]), CENTRO[p[0]]] = float(p[3])
    return oni


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--origen", type=Path)
    a = ap.parse_args()
    if a.origen:
        texto = a.origen.read_text(encoding="utf-8")
    else:
        with urllib.request.urlopen(URL, timeout=60) as r:
            texto = r.read().decode("utf-8")
    oni = leer(texto)
    faltan = [(y, m) for y in ANIOS for m in range(1, 13) if (y, m) not in oni]
    if faltan:
        raise SystemExit(f"Faltan {len(faltan)} meses de ONI, p. ej. {faltan[:3]}")
    destino = DATOS / "fuentes" / "oni_2001_2024.csv"
    destino.parent.mkdir(exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["anio", "mes", "oni"])
        for y in ANIOS:
            for m in range(1, 13):
                w.writerow([y, m, oni[y, m]])
    print(f"{destino} ({len(ANIOS) * 12} meses)")
