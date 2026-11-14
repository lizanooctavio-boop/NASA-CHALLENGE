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
CRW = "https://coralreefwatch.noaa.gov/product/vs/data/nicaragua.txt"


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


def olas_calor_marinas(ruta):
    """Olas de calor marinas (Hobday et al. 2016) y estrés térmico coralino por año desde la estación virtual CRW.

    SST diaria = «SST@90th_HS» del polígono. Umbral: percentil 90 de 1991–2020 por día del año (ventana de 11 días,
    suavizado de 31); episodio = 5 días o más sobre el umbral, uniendo huecos de 2 días o menos. Escribe solo años
    completos y devuelve el último estado diario (DHW y nivel de alerta).
    """
    filas = [l.split() for l in ruta.read_text().splitlines() if l[:2] in ("19", "20") and len(l.split()) == 10]
    fecha = np.array([np.datetime64(f"{y}-{m}-{d}") for y, m, d, *_ in filas])
    sst = np.array([float(x[5]) for x in filas])
    dhw = np.array([float(x[8]) for x in filas])
    alerta = np.array([int(x[9]) for x in filas])
    anio = fecha.astype("datetime64[Y]").astype(int) + 1970
    doy = np.minimum((fecha - fecha.astype("datetime64[Y]")).astype(int), 364)
    base = (anio >= 1991) & (anio <= 2020)
    p90 = np.array([np.percentile(sst[base & (np.abs((doy - k + 182) % 365 - 182) <= 5)], 90) for k in range(365)])
    p90 = np.convolve(np.r_[p90[-15:], p90, p90[:15]], np.ones(31) / 31, "valid")
    tramos, i, sobre = [], 0, sst > p90[doy]
    while i < len(sobre):
        if sobre[i]:
            j = i
            while j + 1 < len(sobre) and sobre[j + 1]:
                j += 1
            if j - i + 1 >= 5:
                if tramos and i - tramos[-1][1] - 1 <= 2:
                    tramos[-1][1] = j
                else:
                    tramos.append([i, j])
            i = j + 1
        else:
            i += 1
    ola = np.zeros(len(sst), bool)
    for i, j in tramos:
        ola[i:j + 1] = True
    with open(AQUI / "crw_caribe_nicaragua_anual.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["anio", "dias_ola_calor_marina", "dhw_max_c_semanas", "dias_alerta_1_o_mas", "sst_media_c"])
        for a in range(int(anio.min()), int(anio.max())):  # el último año está incompleto
            s = anio == a
            w.writerow([a, int(ola[s].sum()), round(float(dhw[s].max()), 2), int((alerta[s] >= 3).sum()),
                        round(float(sst[s].mean()), 4)])
    ultimo = anio == anio.max()
    return {"ultimo_dia": str(fecha[-1]), "dhw_ultimo": float(dhw[-1]), "alerta_ultima": int(alerta[-1]),
            "dias_ola_calor_anio_en_curso": int(ola[ultimo].sum()), "dhw_max_anio_en_curso": float(dhw[ultimo].max())}


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

    crw = olas_calor_marinas(bajar(CRW, args.cache / "crw_nicaragua.txt", refrescar=True))

    ruta = AQUI / "fuentes.json"
    fuentes = json.loads(ruta.read_text(encoding="utf-8"))
    fuentes.update({
        "crw": {"producto": "NOAA Coral Reef Watch v3.1 daily 5 km Regional Virtual Station «Nicaragua»",
                "url": "https://coralreefwatch.noaa.gov/product/vs/", "datos": CRW, **crw},
        "ersst": {"producto": "NOAA ERSSTv5 (Extended Reconstructed SST), 2°", "url": "https://www.ncei.noaa.gov/products/extended-reconstructed-sst",
                  "caja": "12–14° N, 80–82° W (cell centres)", "ultimo_mes": sst[-1][0]},
        "psmsl": {"producto": "PSMSL Revised Local Reference annual means", "url": "https://psmsl.org/", "estaciones": ESTACIONES},
        "ibtracs": {"producto": "NOAA IBTrACS v04r01", "url": "https://www.ncei.noaa.gov/products/international-best-track-archive",
                    "zona": ZONA, "generado_utc": hoy.isoformat(timespec="seconds")},
    })
    ruta.write_text(json.dumps(fuentes, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
