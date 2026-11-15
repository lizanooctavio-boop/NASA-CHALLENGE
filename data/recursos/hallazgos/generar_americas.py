"""Genera los CSV versionados de las Américas y el Caribe en data/recursos/hallazgos/.

Casos cubiertos (todos sin cuenta):
1. cuenca_colorado_caudal: USGS 09380000 Colorado River at Lees Ferry, AZ (1922–2025 y tramo regulado 1963–2025).
2. canada_alaska_permafrost_magt: GTN-P 2021 (PANGAEA doi:10.1594/PANGAEA.930669; pozos de Alaska + Alert 2 en Canadá).
3. norteamerica_hielo_lagos_fenologia: NSIDC G01377 (Bayfield en Lake Superior, Monona, Mendota y series canadienses truncadas).
4. chile_central_megasequia: CHIRPS v2.0 (1981–2024) y CRU TS v4.10 (1951–2025) sobre Chile central (30°–38° S).
5. nordeste_brasil_semiarido_lluvia: CHIRPS v2.0 (1981–2024) y CRU TS v4.10 (1951–2025) sobre el Semiárido del Nordeste de Brasil.
6. huracanes_rapida_intensificacion_na_ep: NOAA IBTrACS v04r01 (Atlántico Norte NA y Pacífico Oriental EP, 1980–2024).
7. oeste_eeuu_nieve_swe_abril: USDA NRCS AWDB SNOTEL REST API v1 (SWE del 1 de abril, 1981–2025).
8. altiplano_lagos_titicaca_poopo: NASA GSFC G-REALM (Poopó, Titicaca, Mar Chiquita, Colhué Huapi, Argentino y Junín).

Uso:
    python data/recursos/hallazgos/generar_americas.py --cache <carpeta fuera del repo>
"""
import argparse
import csv
import gzip
import io
import json
import shutil
import ssl
import subprocess
import sys
import tarfile
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[3]
SALIDA = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "backend"))

from clima_nic.fuentes.lagos import leer_grealm  # noqa: E402

URL_USGS_LEES_FERRY = (
    "https://waterservices.usgs.gov/nwis/stat/?format=rdb&sites=09380000"
    "&statReportType=annual&statTypeCd=mean&parameterCd=00060"
)
URL_GTNP_PANGAEA = "https://doi.pangaea.de/10.1594/PANGAEA.930669?format=text"
URL_NSIDC_G01377 = "https://noaadata.apps.nsidc.org/NOAA/G01377/liag_freeze_thaw_table.csv"
URL_CHIRPS_ERDDAP_ANUAL = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/chirps20GlobalAnnualP05.csv"
URL_CHIRPS_ERDDAP_MENSUAL = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/chirps20GlobalMonthlyP05.csv"
URL_CRU_PRE_BASE = "https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/cruts.2604091129.v4.10/pre"
URL_IBTRACS_BASE = (
    "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs"
    "/v04r01/access/csv"
)
URL_SNOTEL_DATA = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data"
URL_GREALM_10D = "https://earth.gsfc.nasa.gov/gwm/zip/lake.10.tar.gz"
URL_GREALM_30D = "https://earth.gsfc.nasa.gov/gwm/zip/lake.30.tar.gz"

DECADAS_CRU = (
    (1951, 1960),
    (1961, 1970),
    (1971, 1980),
    (1981, 1990),
    (1991, 2000),
    (2001, 2010),
    (2011, 2020),
    (2021, 2025),
)

CAJAS_LLUVIA = {
    "chile_central": (-38.0, -30.0, -73.0, -69.5),
    "nordeste_brasil": (-16.0, -3.0, -45.0, -35.0),
}

POZOS_GTNP = {
    "Deadhorse": ("deadhorse", "Deadhorse (North Slope)", "Alaska, USA"),
    "WestDock": ("west_dock", "West Dock (Prudhoe Bay)", "Alaska, USA"),
    "FranklBluffs": ("franklin_bluffs", "Franklin Bluffs", "Alaska, USA"),
    "Chandalar Shelf": ("chandalar_shelf", "Chandalar Shelf (Brooks Range)", "Alaska, USA"),
    "Alert 2": ("alert_2", "Alert (borehole 2, Ellesmere Island)", "Nunavut, Canada"),
}

LAGOS_NSIDC = {
    "JJM33": ("Lake Superior at Bayfield", "Wisconsin, USA"),
    "DMR2": ("Lake Monona", "Wisconsin, USA"),
    "DMR1": ("Lake Mendota", "Wisconsin, USA"),
    "PJD28": ("Lake Simcoe", "Ontario, Canada"),
    "WRS310": ("Lake Utopia", "New Brunswick, Canada"),
}

ESTACIONES_SNOTEL = (
    ("352:WA:SNTL", "blewett_pass_wa", "Blewett Pass", "Washington, USA", 47.35, -120.68, 1292),
    ("304:OR:SNTL", "arbuckle_mtn_or", "Arbuckle Mountain", "Oregon, USA", 45.19, -119.25, 1759),
    ("316:NM:SNTL", "bateman_nm", "Bateman", "New Mexico, USA", 36.52, -106.32, 2835),
    ("307:MT:SNTL", "badger_pass_mt", "Badger Pass", "Montana, USA", 45.23, -113.02, 2094),
    ("309:WY:SNTL", "bald_mtn_wy", "Bald Mountain", "Wyoming, USA", 44.80, -107.85, 2853),
    ("663:CO:SNTL", "niwot_co", "Niwot Ridge", "Colorado, USA", 40.04, -105.54, 3021),
)

LAGOS_GREALM_10D = (
    ("poopo", "000051", "Bolivia"),
    ("mar_chiquita", "000344", "Argentina"),
    ("colhue_huapi", "000439", "Argentina"),
    ("argentino", "000753", "Argentina"),
    ("junin", "000032", "Peru"),
)
LAGOS_GREALM_30D = (
    ("titicaca", "000318", "Peru and Bolivia"),
)


def _descargar(url: str, destino: Path, timeout: int = 120) -> Path:
    """Descarga un archivo a la caché externa si no existe aún."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.is_file() and destino.stat().st_size > 0:
        return destino
    tmp = destino.with_suffix(destino.suffix + ".part")
    curl_bin = shutil.which("curl.exe") or shutil.which("curl")
    if curl_bin:
        res = subprocess.run(
            [curl_bin, "-sSL", "--retry", "3", "--max-time", str(timeout), url, "-o", str(tmp)],
            check=False,
        )
        if res.returncode == 0 and tmp.is_file() and tmp.stat().st_size > 0:
            tmp.replace(destino)
            return destino
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "clima-nic/1.0 (Space Apps 2026)"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r, tmp.open("wb") as f:
        shutil.copyfileobj(r, f)
    tmp.replace(destino)
    return destino


def _escribir_csv(ruta: Path, campos: list[str], filas: list[dict]) -> None:
    with ruta.open("w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, fieldnames=campos, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)


def generar_colorado(cache: Path) -> dict:
    """Descarga y convierte el caudal medio anual de USGS 09380000 (Lees Ferry, AZ) a km³/año."""
    ruta_rdb = _descargar(URL_USGS_LEES_FERRY, cache / "usgs_09380000_anual.rdb", timeout=30)
    filas = []
    for linea in ruta_rdb.read_text(encoding="utf-8", errors="replace").splitlines():
        if not linea or linea.startswith("#") or linea.startswith("agency_cd") or linea.startswith("5s"):
            continue
        partes = linea.split("\t")
        if len(partes) >= 7 and partes[5].strip().isdigit():
            anio = int(partes[5].strip())
            cfs = float(partes[6].strip())
            # 1 ft³ = 0,0283168466 m³; año juliano medio = 365,25 días
            km3 = cfs * 0.0283168466 * 86400.0 * 365.25 / 1e9
            filas.append({"anio": anio, "caudal_cfs": f"{cfs:.1f}", "volumen_km3": f"{km3:.4f}"})
    filas.sort(key=lambda r: r["anio"])
    _escribir_csv(SALIDA / "colorado_lees_ferry_anual.csv", ["anio", "caudal_cfs", "volumen_km3"], filas)
    return {
        "producto": "USGS National Water Information System (NWIS) gauge 09380000 at Lees Ferry, Arizona",
        "url": URL_USGS_LEES_FERRY,
        "periodo": f"{filas[0]['anio']}-{filas[-1]['anio']}",
    }


def generar_permafrost(cache: Path) -> dict:
    """Extrae las series anuales de temperatura profunda del permafrost (MAGT) en Alaska y Canadá desde GTN-P."""
    ruta_tsv = _descargar(URL_GTNP_PANGAEA, cache / "gtnp_pangaea_930669.tsv", timeout=45)
    lineas = ruta_tsv.read_text(encoding="utf-8", errors="replace").splitlines()
    inicio = next(i + 1 for i, l in enumerate(lineas) if l.strip() == "*/")
    cabecera = lineas[inicio].split("\t")
    cols_anio = [(i, int(c.split("(")[1].split(")")[0])) for i, c in enumerate(cabecera) if c.startswith("MAGT [")]
    filas = []
    for linea in lineas[inicio + 1 :]:
        if not linea.strip():
            continue
        cols = linea.split("\t")
        nombre_orig = cols[1].strip()
        if nombre_orig not in POZOS_GTNP:
            continue
        sitio_id, nombre_limpio, pais = POZOS_GTNP[nombre_orig]
        lat = float(cols[4])
        lon = float(cols[5])
        prof = float(cols[7])
        for idx, anio in cols_anio:
            if idx < len(cols) and cols[idx].strip() != "":
                val = float(cols[idx].strip())
                filas.append({
                    "sitio": sitio_id,
                    "nombre": nombre_limpio,
                    "pais": pais,
                    "lat": f"{lat:.2f}",
                    "lon": f"{lon:.2f}",
                    "profundidad_m": f"{prof:.1f}",
                    "anio": anio,
                    "magt_c": f"{val:.2f}",
                })
    filas.sort(key=lambda r: (r["sitio"], r["anio"]))
    _escribir_csv(
        SALIDA / "gtnp_permafrost_anual.csv",
        ["sitio", "nombre", "pais", "lat", "lon", "profundidad_m", "anio", "magt_c"],
        filas,
    )
    return {
        "producto": "GTN-P long-term permafrost borehole temperature archive (PANGAEA)",
        "url": "https://doi.org/10.1594/PANGAEA.930669",
        "periodo": "1978-2016",
    }


def generar_hielo_lagos(cache: Path) -> dict:
    """Extrae la duración anual del hielo lacustre en lagos de Norteamérica desde NSIDC G01377."""
    ruta_csv = _descargar(URL_NSIDC_G01377, cache / "liag_freeze_thaw_table.csv", timeout=60)
    texto = ruta_csv.read_text(encoding="utf-8", errors="replace")
    por_lago_anio = {}
    coords = {}
    for fila in csv.DictReader(io.StringIO(texto)):
        codigo = (fila.get("lakecode") or "").strip()
        if codigo not in LAGOS_NSIDC:
            continue
        dur_s = (fila.get("duration") or "").strip()
        anio_s = (fila.get("iceon_year") or "").strip()
        if dur_s in ("", "-999", "NA") or anio_s in ("", "-999", "NA"):
            continue
        dur = float(dur_s)
        anio = int(anio_s)
        if dur <= 0 or dur >= 366:
            continue
        por_lago_anio[(codigo, anio)] = dur
        if codigo not in coords:
            coords[codigo] = (float(fila["latitude"]), float(fila["longitude"]))

    filas = []
    for (codigo, anio), dur in sorted(por_lago_anio.items()):
        nombre, pais = LAGOS_NSIDC[codigo]
        lat, lon = coords[codigo]
        filas.append({
            "lakecode": codigo,
            "nombre": nombre,
            "pais": pais,
            "lat": f"{lat:.2f}",
            "lon": f"{lon:.2f}",
            "anio": anio,
            "duracion_dias": f"{dur:.0f}" if dur.is_integer() else f"{dur:.1f}",
        })
    _escribir_csv(
        SALIDA / "nsidc_hielo_lagos_anual.csv",
        ["lakecode", "nombre", "pais", "lat", "lon", "anio", "duracion_dias"],
        filas,
    )
    return {
        "producto": "Global Lake and River Ice Phenology Database, Version 1 (NSIDC G01377)",
        "url": URL_NSIDC_G01377,
        "periodo": "1851-2019",
    }


def _media_espacial_erddap_anual(ruta_csv: Path) -> dict[int, float]:
    """Promedia espacialmente con ponderación cos(lat) un CSV anual de CHIRPS descargado desde ERDDAP."""
    por_anio = {}
    with ruta_csv.open("r", encoding="latin-1") as f:
        lector = csv.reader(f)
        next(lector, None)
        next(lector, None)
        for fila in lector:
            if len(fila) < 4 or fila[3] in ("", "NaN"):
                continue
            anio = int(fila[0][:4])
            lat = float(fila[1])
            val = float(fila[3])
            if val < 0:
                continue
            peso = float(np.cos(np.deg2rad(lat)))
            num, den = por_anio.get(anio, (0.0, 0.0))
            por_anio[anio] = (num + val * peso, den + peso)
    return {a: num / den for a, (num, den) in sorted(por_anio.items()) if den > 0}


def _media_espacial_erddap_mensual(ruta_csv: Path) -> tuple[dict[int, float], dict[int, float]]:
    """Calcula suma anual (12 meses) y suma FMAM (feb–may) con ponderación cos(lat) desde CHIRPS mensual."""
    por_mes = {}
    with ruta_csv.open("r", encoding="latin-1") as f:
        lector = csv.reader(f)
        next(lector, None)
        next(lector, None)
        for fila in lector:
            if len(fila) < 4 or fila[3] in ("", "NaN"):
                continue
            ym = fila[0][:7]
            lat = float(fila[1])
            val = float(fila[3])
            if val < 0:
                continue
            peso = float(np.cos(np.deg2rad(lat)))
            num, den = por_mes.get(ym, (0.0, 0.0))
            por_mes[ym] = (num + val * peso, den + peso)
    medias_mes = {ym: num / den for ym, (num, den) in sorted(por_mes.items()) if den > 0}
    por_anio = {}
    for ym, v in medias_mes.items():
        anio, mes = int(ym[:4]), int(ym[5:7])
        por_anio.setdefault(anio, {})[mes] = v
    anual = {a: sum(m.values()) for a, m in sorted(por_anio.items()) if len(m) == 12}
    fmam = {
        a: sum(m[k] for k in (2, 3, 4, 5))
        for a, m in sorted(por_anio.items())
        if all(k in m for k in (2, 3, 4, 5)) and a <= max(anual)
    }
    return anual, fmam


def _series_cru_pre(cache: Path) -> dict[tuple[str, str], dict[int, float]]:
    """Extrae las series anuales y FMAM de CRU TS 4.10 (1951–2025) para Chile central y Nordeste de Brasil."""
    lat = -89.75 + 0.5 * np.arange(360)
    lon = -179.75 + 0.5 * np.arange(720)
    indices = {}
    for reg_id, (lat1, lat2, lon1, lon2) in CAJAS_LLUVIA.items():
        yi = np.where((lat >= lat1) & (lat <= lat2))[0]
        xi = np.where((lon >= lon1) & (lon <= lon2))[0]
        indices[reg_id] = (yi, int(xi[0]) * 8, int(xi[-1] + 1) * 8, np.cos(np.deg2rad(lat[yi])))

    salida = {
        ("chile_central", "anual"): {},
        ("nordeste_brasil", "anual"): {},
        ("nordeste_brasil", "fmam"): {},
    }
    for y0, y1 in DECADAS_CRU:
        nombre = f"cru_ts4.10.{y0}.{y1}.pre.dat.gz"
        ruta_gz = _descargar(f"{URL_CRU_PRE_BASE}/{nombre}", cache / nombre, timeout=90)
        with gzip.open(ruta_gz, "rt", encoding="ascii") as f:
            lineas = f.read().splitlines()
        n_anios = y1 - y0 + 1
        for reg_id, (yi, c0, c1, pesos_lat) in indices.items():
            mensuales = []
            for m in range(n_anios * 12):
                base = m * 360
                num, den = 0.0, 0.0
                for idx_r, fila_y in enumerate(yi):
                    trozo = lineas[base + int(fila_y)]
                    vals = [int(trozo[k : k + 8]) for k in range(c0, c1, 8)]
                    validos = [v * 0.1 for v in vals if v != -999]
                    if validos:
                        peso = float(pesos_lat[idx_r]) * len(validos)
                        num += (sum(validos) / len(validos)) * peso
                        den += peso
                mensuales.append(num / den if den > 0 else np.nan)
            for idx_a, anio in enumerate(range(y0, y1 + 1)):
                doce = mensuales[idx_a * 12 : (idx_a + 1) * 12]
                salida[(reg_id, "anual")][anio] = float(sum(doce))
                if reg_id == "nordeste_brasil":
                    salida[(reg_id, "fmam")][anio] = float(sum(doce[1:5]))
    return salida


def generar_lluvia_americas(cache: Path) -> dict:
    """Genera americas_lluvia_anual.csv con CHIRPS v2.0 y CRU TS 4.10 para Chile central y Nordeste de Brasil."""
    url_chile_chirps = (
        f"{URL_CHIRPS_ERDDAP_ANUAL}?precip%5B(1981-01-01T00:00:00Z):1:(2024-01-01T00:00:00Z)%5D"
        "%5B(-38.0):5:(-30.0)%5D%5B(-73.0):5:(-69.5)%5D"
    )
    ruta_chile = _descargar(url_chile_chirps, cache / "chirps_chile_central_anual.csv", timeout=60)
    chile_chirps = _media_espacial_erddap_anual(ruta_chile)

    url_ne_chirps = (
        f"{URL_CHIRPS_ERDDAP_MENSUAL}?precip%5B(1981-01-01T00:00:00Z):1:(2024-12-01T00:00:00Z)%5D"
        "%5B(-16.0):10:(-3.0)%5D%5B(-45.0):10:(-35.0)%5D"
    )
    ruta_ne = _descargar(url_ne_chirps, cache / "chirps_nordeste_brasil_mensual.csv", timeout=90)
    ne_chirps_anual, ne_chirps_fmam = _media_espacial_erddap_mensual(ruta_ne)

    series_cru = _series_cru_pre(cache)

    filas = []
    for anio, mm in sorted(chile_chirps.items()):
        filas.append({"region": "chile_central", "fuente": "chirps", "variable": "anual", "anio": anio, "mm": f"{mm:.1f}"})
    for anio, mm in sorted(series_cru[("chile_central", "anual")].items()):
        filas.append({"region": "chile_central", "fuente": "cru", "variable": "anual", "anio": anio, "mm": f"{mm:.1f}"})
    for anio, mm in sorted(ne_chirps_anual.items()):
        filas.append({"region": "nordeste_brasil", "fuente": "chirps", "variable": "anual", "anio": anio, "mm": f"{mm:.1f}"})
    for anio, mm in sorted(ne_chirps_fmam.items()):
        filas.append({"region": "nordeste_brasil", "fuente": "chirps", "variable": "fmam", "anio": anio, "mm": f"{mm:.1f}"})
    for anio, mm in sorted(series_cru[("nordeste_brasil", "anual")].items()):
        filas.append({"region": "nordeste_brasil", "fuente": "cru", "variable": "anual", "anio": anio, "mm": f"{mm:.1f}"})
    for anio, mm in sorted(series_cru[("nordeste_brasil", "fmam")].items()):
        filas.append({"region": "nordeste_brasil", "fuente": "cru", "variable": "fmam", "anio": anio, "mm": f"{mm:.1f}"})

    _escribir_csv(SALIDA / "americas_lluvia_anual.csv", ["region", "fuente", "variable", "anio", "mm"], filas)
    return {
        "chirps_erddap": {
            "producto": "CHIRPS v2.0 global precipitation (UCSB Climate Hazards Center via NOAA CoastWatch ERDDAP)",
            "url": "https://coastwatch.pfeg.noaa.gov/erddap/griddap/chirps20GlobalMonthlyP05.html",
        },
        "cru_ts410": {
            "producto": "CRU TS v4.10 monthly gridded precipitation at 0.5° (Climatic Research Unit, University of East Anglia)",
            "url": "https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/",
        },
    }


def generar_ibtracs_ri(cache: Path) -> dict:
    """Calcula pasos sinópticos de rápida intensificación (>=30 kt en 24 h) y % de tormentas con RI en NA y EP."""
    filas = []
    for cuenca in ("NA", "EP"):
        nombre = f"ibtracs.{cuenca}.list.v04r01.csv"
        ruta = _descargar(f"{URL_IBTRACS_BASE}/{nombre}", cache / nombre, timeout=90)
        lineas = ruta.read_text(encoding="utf-8", errors="replace").splitlines()
        cab = lineas[0].split(",")
        i_sid = cab.index("SID")
        i_seas = cab.index("SEASON")
        i_iso = cab.index("ISO_TIME")
        i_w = cab.index("USA_WIND")

        tormentas = {}
        for ln in lineas[2:]:
            cols = ln.split(",")
            if len(cols) <= i_w:
                continue
            seas, iso, w_s = cols[i_seas].strip(), cols[i_iso].strip(), cols[i_w].strip()
            if not seas.isdigit() or not (1980 <= int(seas) <= 2024):
                continue
            if not iso.endswith(("00:00:00", "06:00:00", "12:00:00", "18:00:00")) or not w_s:
                continue
            try:
                w = float(w_s)
            except ValueError:
                continue
            tormentas.setdefault((int(seas), cols[i_sid].strip()), []).append((iso, w))

        pasos_por_anio = {a: 0 for a in range(1980, 2025)}
        torm_ri_por_anio = {a: 0 for a in range(1980, 2025)}
        torm_tot_por_anio = {a: 0 for a in range(1980, 2025)}

        for (anio, _sid), pts in tormentas.items():
            pts.sort()
            torm_tot_por_anio[anio] += 1
            mapa_t = {datetime.fromisoformat(iso): w for iso, w in pts}
            tuvo_ri = False
            for t, w in mapa_t.items():
                dt = t + timedelta(hours=24)
                if dt in mapa_t and (mapa_t[dt] - w) >= 30.0:
                    pasos_por_anio[anio] += 1
                    tuvo_ri = True
            if tuvo_ri:
                torm_ri_por_anio[anio] += 1

        for anio in range(1980, 2025):
            tot = torm_tot_por_anio[anio]
            ri_t = torm_ri_por_anio[anio]
            pct = (100.0 * ri_t / tot) if tot > 0 else 0.0
            filas.append({
                "cuenca": cuenca,
                "anio": anio,
                "pasos_ri": pasos_por_anio[anio],
                "tormentas_ri": ri_t,
                "tormentas_total": tot,
                "pct_tormentas_ri": f"{pct:.2f}",
            })

    _escribir_csv(
        SALIDA / "ibtracs_ri_anual.csv",
        ["cuenca", "anio", "pasos_ri", "tormentas_ri", "tormentas_total", "pct_tormentas_ri"],
        filas,
    )
    return {
        "producto": "IBTrACS v04r01 tropical cyclone best-track archive (NOAA NCEI)",
        "url": f"{URL_IBTRACS_BASE}/",
        "periodo": "1980-2024",
    }


def generar_snotel(cache: Path) -> dict:
    """Descarga el equivalente de agua en nieve (SWE) del 1 de abril en estaciones SNOTEL del oeste de EE. UU."""
    filas = []
    for i in range(0, len(ESTACIONES_SNOTEL), 3):
        lote = ESTACIONES_SNOTEL[i : i + 3]
        triplets = ",".join(e[0] for e in lote)
        url = f"{URL_SNOTEL_DATA}?stationTriplets={triplets}&elements=WTEQ&duration=DAILY&beginDate=1981-04-01&endDate=2025-04-02"
        ruta_json = _descargar(url, cache / f"snotel_lote_{i}.json", timeout=45)
        datos = json.loads(ruta_json.read_text(encoding="utf-8"))
        mapa_meta = {e[0]: e for e in lote}
        for st_obj in datos:
            trip = st_obj.get("stationTriplet")
            if trip not in mapa_meta:
                continue
            _trip, id_sitio, nombre, estado, lat, lon, elev = mapa_meta[trip]
            for el in st_obj.get("data", []):
                for v in el.get("values", []):
                    if v.get("date", "").endswith("-04-01") and v.get("value") is not None:
                        anio = int(v["date"][:4])
                        swe_mm = float(v["value"]) * 25.4
                        filas.append({
                            "sitio": id_sitio,
                            "triplet": trip,
                            "nombre": nombre,
                            "estado": estado,
                            "lat": f"{lat:.2f}",
                            "lon": f"{lon:.2f}",
                            "elev_m": elev,
                            "anio": anio,
                            "swe_mm": f"{swe_mm:.1f}",
                        })
    filas.sort(key=lambda r: (r["sitio"], r["anio"]))
    _escribir_csv(
        SALIDA / "snotel_swe_abril_anual.csv",
        ["sitio", "triplet", "nombre", "estado", "lat", "lon", "elev_m", "anio", "swe_mm"],
        filas,
    )
    return {
        "producto": "USDA NRCS National Water and Climate Center SNOTEL telemetered snowpack network (AWDB REST API v1)",
        "url": "https://wcc.sc.egov.usda.gov/awdbRestApi/swagger-ui/index.html",
        "periodo": "1981-2025",
    }


def generar_lagos_grealm(cache: Path) -> dict:
    """Extrae series anuales de nivel de agua (m EGM2008) de lagos sudamericanos en NASA GSFC G-REALM."""
    filas = []
    for url_tar, nombre_tar, objetivos in (
        (URL_GREALM_10D, "lake.10.tar.gz", LAGOS_GREALM_10D),
        (URL_GREALM_30D, "lake.30.tar.gz", LAGOS_GREALM_30D),
    ):
        ruta_tar = _descargar(url_tar, cache / nombre_tar, timeout=300)
        with tarfile.open(ruta_tar, "r:gz") as tf:
            miembros = {m.name: m for m in tf.getmembers()}
            for lago_id, codigo, pais in objetivos:
                coincidencias = sorted(k for k in miembros if f"lake{codigo}." in k and k.endswith(".txt"))
                if not coincidencias:
                    continue
                texto = tf.extractfile(miembros[coincidencias[0]]).read().decode("latin-1", errors="ignore")
                fechas, alturas = leer_grealm(texto)
                if len(fechas) < 10:
                    fechas, alturas = [], []
                    # En lake.30.tar.gz las misiones Sentinel-3A usan código de 3 letras (S3A)
                    for ln in texto.splitlines():
                        p = ln.split()
                        if len(p) >= 15 and p[0].isalnum() and len(p[2]) == 8 and p[2].isdigit():
                            try:
                                var, alt = float(p[5]), float(p[14])
                            except ValueError:
                                continue
                            if abs(var) < 999 and alt < 9999:
                                fechas.append(f"{p[2][:4]}-{p[2][4:6]}-{p[2][6:]}")
                                alturas.append(alt)
                por_anio = {}
                max_anio = 2026 if lago_id == "titicaca" else 2025
                for f, h in zip(fechas, alturas):
                    anio = int(f[:4])
                    if anio <= max_anio:
                        por_anio.setdefault(anio, []).append(h)
                for anio, vals in sorted(por_anio.items()):
                    if len(vals) >= 4:
                        filas.append({
                            "lago": lago_id,
                            "id_grealm": codigo,
                            "pais": pais,
                            "anio": anio,
                            "nivel_m": f"{float(np.mean(vals)):.2f}",
                            "n_obs": len(vals),
                        })
    filas.sort(key=lambda r: (r["lago"], r["anio"]))
    _escribir_csv(
        SALIDA / "grealm_lagos_sudamerica_anual.csv",
        ["lago", "id_grealm", "pais", "anio", "nivel_m", "n_obs"],
        filas,
    )
    return {
        "producto": "NASA GSFC Global Water Monitor (G-REALM) satellite radar altimetry lake levels",
        "url": "https://earth.gsfc.nasa.gov/gwm/lake/Index",
        "periodo": "1992-2025",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", type=Path, required=True, help="Carpeta de caché fuera del repositorio")
    ap.add_argument(
        "--solo",
        choices=("colorado", "permafrost", "hielo_lagos", "lluvia", "ibtracs", "snotel", "grealm"),
        help="Ejecuta únicamente un subconjunto",
    )
    args = ap.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)

    ruta_fuentes = SALIDA / "fuentes.json"
    fuentes = json.loads(ruta_fuentes.read_text(encoding="utf-8")) if ruta_fuentes.is_file() else {}

    pasos = (
        ("colorado", "usgs_colorado", generar_colorado),
        ("permafrost", "gtnp_permafrost", generar_permafrost),
        ("hielo_lagos", "nsidc_g01377", generar_hielo_lagos),
        ("lluvia", None, generar_lluvia_americas),
        ("ibtracs", "ibtracs_ri", generar_ibtracs_ri),
        ("snotel", "snotel_swe", generar_snotel),
        ("grealm", "grealm_sudamerica", generar_lagos_grealm),
    )
    for clave, clave_fuente, fn in pasos:
        if args.solo in (None, clave):
            info = fn(args.cache)
            if clave_fuente is None:
                fuentes.update(info)
            else:
                fuentes[clave_fuente] = info

    ruta_fuentes.write_text(json.dumps(fuentes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
