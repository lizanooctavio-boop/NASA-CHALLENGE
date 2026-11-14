"""Genera los contrastes externos de data/recursos/contraste/ (agente 2 · contrastes).

Pasos (cada uno escribe sus CSV en esta carpeta; los archivos crudos van a backend/.cache/contraste, que no
se versiona):

    python data/recursos/contraste/generar_contrastes.py noaa      # NCEI GSOM + GHCN-Daily (sin token)
    python data/recursos/contraste/generar_contrastes.py cru       # CRU TS 4.10 (UEA), lluvia mensual
    python data/recursos/contraste/generar_contrastes.py gpcc      # GPCC 0,5° de PSL (OPeNDAP)
    python data/recursos/contraste/generar_contrastes.py opendap   # IMERG, AIRS, OMI NO2 (GES DISC OPeNDAP)
    python data/recursos/contraste/generar_contrastes.py nube      # Giovanni en la nube (Harmony): IMERG y GLDAS
    python data/recursos/contraste/generar_contrastes.py clorofila # MODIS-Aqua L3m CHL 4 km (OB.DAAC)
    python data/recursos/contraste/generar_contrastes.py resumen   # series_anuales.csv + resumen_contrastes.json

`resumen` no usa red: recalcula todo desde los CSV guardados, data/clima.json y data/fenomenos/ (que solo se
leen). Los métodos de tendencia son los del backend (`clima_nic.fuentes.giovanni.veredicto_serie`, que llama a
`tendencia_robusta.analizar`).
"""
import csv
import datetime as dt
import gzip
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ / "backend"))

from clima_nic.fuentes import giovanni as gv  # noqa: E402
from clima_nic.fuentes import knmi  # noqa: E402
from clima_nic.fuentes import noaa_cdo as nc  # noqa: E402
from clima_nic.rutas import CACHE, DATOS, FENOMENOS  # noqa: E402

CACHE_C = CACHE / "contraste"
NOAA = AQUI / "noaa"
HOY = dt.date.today().isoformat()
P0, P1 = 2001, 2024
BLOQUEOS = AQUI / "bloqueos.json"

# Regiones de clima.json (dominios.geojson) usadas en la comparación de lluvia.
REGIONES_LLUVIA = ("caja_sicc", "NIC", "HND")

FUENTES = {
    "cru": {"fuente": "CRU TS 4.10 (University of East Anglia), pre, 0,5°", "version": "4.10 (cruts.2604091129)",
            "url": "https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/cruts.2604091129.v4.10/pre/"},
    "gpcc": {"fuente": "GPCC Full Data Reanalysis 0,5° (copia NOAA PSL)", "version": "v2025 según el atributo del archivo PSL",
             "url": "https://psl.noaa.gov/thredds/dodsC/Datasets/gpcc/full_v2025/precip.mon.total.0.50x0.50.v2025.nc"},
    "ghcnd": {"fuente": "NOAA NCEI GHCN-Daily (daily-summaries)", "version": "GHCN-Daily v3 (servicio NCEI v1)",
              "url": "https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries"},
    "gsom": {"fuente": "NOAA NCEI Global Summary of the Month", "version": "GSOM 1.0 (servicio NCEI v1)",
             "url": "https://www.ncei.noaa.gov/access/services/data/v1?dataset=global-summary-of-the-month"},
}


# ---------------------------------------------------------------- utilidades de archivo

def escribir_csv(ruta, cabecera, filas):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", newline="\n", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cabecera)
        w.writerows(filas)


def leer_csv(ruta):
    with Path(ruta).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fecha_consulta(clave):
    meta = AQUI / "consultas.json"
    d = json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else {}
    return d.get(clave)


def anotar_consulta(clave, **info):
    meta = AQUI / "consultas.json"
    d = json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else {}
    d[clave] = {"fecha": HOY, **info}
    meta.write_text(json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def anotar_bloqueo(clave, **info):
    d = json.loads(BLOQUEOS.read_text(encoding="utf-8")) if BLOQUEOS.exists() else {}
    d[clave] = {"fecha": HOY, **info}
    BLOQUEOS.write_text(json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8",
                        newline="\n")


def quitar_bloqueo(clave):
    if BLOQUEOS.exists():
        d = json.loads(BLOQUEOS.read_text(encoding="utf-8"))
        if d.pop(clave, None) is not None:
            BLOQUEOS.write_text(json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                                encoding="utf-8", newline="\n")


VEREDICTO_EN = {"tendencia_detectada": "trend detected", "evidencia_insuficiente": "insufficient evidence",
                "metodos_discrepan": "methods disagree", "datos_insuficientes": "insufficient data"}


def en(veredicto):
    """Veredicto del backend → texto en inglés para frase_en."""
    return VEREDICTO_EN.get(veredicto, str(veredicto).replace("_", " "))


def r4(x):
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) else round(float(x), 4)


# ---------------------------------------------------------------- paso NOAA

def paso_noaa():
    # 1) CDO v2 /stations: documenta el bloqueo si no hay token.
    lista, error = nc.estaciones_cdo((10.7, -89.4, 16.5, -83.1), "GSOM")
    if error:
        anotar_bloqueo("noaa_cdo_v2", url=error["url"], http=error["http"],
                       motivo="NOAA_CDO_TOKEN no está en el entorno; CDO v2 exige el token. Se usó el servicio NCEI v1 "
                              "(mismos conjuntos GSOM y GHCN-Daily, sin token).")
    else:
        quitar_bloqueo("noaa_cdo_v2")
    # 2) Buscador NCEI v1 (equivalente a /stations con extent de Nicaragua y Honduras).
    estaciones = {}
    for ds in ("global-summary-of-the-month", "daily-summaries"):
        url = nc.url_busqueda(ds, (16.6, -89.5, 10.6, -83.0))
        for e in nc.leer_busqueda(nc.descargar(url)):
            estaciones.setdefault(e["id"], {"nombre": e["nombre"]})[ds] = [e["inicio"], e["fin"]]
    escribir_csv(NOAA / "estaciones_ncei.csv", ["id", "nombre", "gsom_inicio", "gsom_fin", "ghcnd_inicio", "ghcnd_fin",
                                                "pedida"],
                 [[k, v["nombre"], *v.get("global-summary-of-the-month", ["", ""]),
                   *v.get("daily-summaries", ["", ""]), int(k in nc.ESTACIONES)] for k, v in sorted(estaciones.items())])
    # 3) Datos.
    for ds, nombre in (("global-summary-of-the-month", "gsom"), ("daily-summaries", "ghcnd")):
        url = nc.url_datos(ds, list(nc.ESTACIONES), "1940-01-01", "2025-12-31")
        texto = nc.descargar(url).replace("\r\n", "\n")
        destino = (NOAA if nombre == "gsom" else CACHE_C / "noaa") / f"{nombre}_estaciones.csv"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto, encoding="utf-8", newline="\n")
        anotar_consulta(nombre, url=url)
    construir_mensual_estaciones()


def construir_mensual_estaciones():
    """GHCN-Daily → mensual (TAVG media con ≥ 20 días; PRCP solo meses completos) + GSOM PRCP."""
    diario = nc.leer_csv_ncei((CACHE_C / "noaa" / "ghcnd_estaciones.csv").read_text(encoding="utf-8"))
    gsom = nc.leer_csv_ncei((NOAA / "gsom_estaciones.csv").read_text(encoding="utf-8"))
    filas = []
    for st in nc.ESTACIONES:
        d = diario.get(st, {})
        tavg = nc.mensual_desde_diario(d, "TAVG", "media", 20)
        ndias = {}
        for f, v in d.items():
            if v.get("TAVG") is not None:
                ndias[f[:7]] = ndias.get(f[:7], 0) + 1
        prcp_d = nc.mensual_desde_diario(d, "PRCP", "suma")
        prcp_m = {k: v["PRCP"] for k, v in gsom.get(st, {}).items() if v.get("PRCP") is not None}
        for mes in sorted(set(tavg) | set(prcp_d) | set(prcp_m)):
            filas.append([st, mes, r4(tavg.get(mes)), ndias.get(mes, 0), r4(prcp_d.get(mes)), r4(prcp_m.get(mes))])
    escribir_csv(NOAA / "estaciones_mensual.csv",
                 ["estacion", "mes", "tavg_c_ghcnd", "dias_tavg", "prcp_mm_ghcnd_mes_completo", "prcp_mm_gsom"], filas)


# ---------------------------------------------------------------- pasos CRU y GPCC (lluvia en malla)

def _pesos_regiones(lat, lon, paso):
    from shapely.geometry import shape

    from clima_nic import regiones as reg
    dom = json.loads((DATOS / "dominios.geojson").read_text(encoding="utf-8"))
    geoms = {f["id"]: shape(f["geometry"]) for f in dom["features"] if f["id"] in REGIONES_LLUVIA}
    return reg.pesos_malla(lat, lon, paso, paso, geoms)


def _medias_regionales(lat, lon, campo, paso):
    from clima_nic.fuentes.base import recortar_malla
    pesos = _pesos_regiones(lat, lon, paso)
    out, _ = recortar_malla(lat, lon, campo, pesos=pesos)
    return out


def paso_cru():
    import netCDF4
    filas, filas_stn = [], []
    for p in ("2001.2010", "2011.2020", "2021.2025"):
        gz = CACHE_C / "cru" / f"cru_ts4.10.{p}.pre.dat.nc.gz"
        if not gz.exists():
            from clima_nic.fuentes.base import descargar_url
            descargar_url(FUENTES["cru"]["url"] + gz.name, gz, timeout=1800)
        nc_ = gz.with_suffix("")
        if not nc_.exists():
            nc_.write_bytes(gzip.decompress(gz.read_bytes()))
        d = netCDF4.Dataset(nc_)
        lat, lon = d["lat"][:], d["lon"][:]
        jl = np.where((lat >= 7.5) & (lat <= 17.5))[0]
        jo = np.where((lon >= -90.5) & (lon <= -82.0))[0]
        la, lo = np.asarray(lat[jl], float), np.asarray(lon[jo], float)
        t = d["time"]
        fechas = netCDF4.num2date(t[:], t.units)
        pre = np.ma.filled(d["pre"][:, jl.min():jl.max() + 1, jo.min():jo.max() + 1].astype(float), np.nan)
        stn = np.ma.filled(d["stn"][:, jl.min():jl.max() + 1, jo.min():jo.max() + 1].astype(float), np.nan)
        medias = _medias_regionales(la, lo, pre, 0.5)
        mstn = _medias_regionales(la, lo, stn, 0.5)
        for i, f in enumerate(fechas):
            if P0 <= f.year <= P1:
                mes = f"{f.year:04d}-{f.month:02d}"
                for r in REGIONES_LLUVIA:
                    filas.append(["cru_ts_4.10", r, mes, r4(medias[r][i])])
                    filas_stn.append(["cru_ts_4.10", r, mes, r4(mstn[r][i])])
    escribir_csv(AQUI / "lluvia_mensual_externa_cru.csv", ["fuente", "region", "mes", "mm"], filas)
    escribir_csv(AQUI / "cru_estaciones_mensual.csv", ["fuente", "region", "mes", "estaciones_media_ponderada"], filas_stn)
    anotar_consulta("cru", url=FUENTES["cru"]["url"])


def paso_gpcc():
    import netCDF4
    u = FUENTES["gpcc"]["url"]
    d = netCDF4.Dataset(u)
    attrs = {k: str(getattr(d, k)) for k in ("title", "version", "history", "data_modified")}
    t = d["time"]
    fechas = netCDF4.num2date(t[:], t.units)
    idx = [i for i, f in enumerate(fechas) if P0 <= f.year <= P1]
    lat, lon = d["lat"][:], d["lon"][:]
    jl = np.where((lat >= 7.5) & (lat <= 17.5))[0]
    jo = np.where((lon >= 269.5) & (lon <= 278.0))[0]
    campo = np.ma.filled(d["precip"][idx[0]:idx[-1] + 1, jl.min():jl.max() + 1, jo.min():jo.max() + 1]
                         .astype(float), np.nan)
    la = np.asarray(lat[jl.min():jl.max() + 1], float)
    lo = np.asarray(lon[jo.min():jo.max() + 1], float) - 360
    orden = np.argsort(la)
    medias = _medias_regionales(la[orden], lo, campo[:, orden, :], 0.5)
    filas = []
    for k, i in enumerate(idx):
        f = fechas[i]
        for r in REGIONES_LLUVIA:
            filas.append(["gpcc_psl_v2025", r, f"{f.year:04d}-{f.month:02d}", r4(medias[r][k])])
    escribir_csv(AQUI / "lluvia_mensual_externa_gpcc.csv", ["fuente", "region", "mes", "mm"], filas)
    anotar_consulta("gpcc", url=u, atributos=attrs, ultimo_mes=f"{fechas[-1].year}-{fechas[-1].month:02d}")


KNMI = "https://climexp.knmi.nl/start.cgi?id=someone@somewhere"


def paso_knmi():
    """Comprueba KNMI Climate Explorer. No resuelve verificaciones de «humano»: si aparecen, anota el bloqueo."""
    import shutil
    import subprocess
    if shutil.which("curl"):
        r = subprocess.run(["curl", "-sS", "-m", "60", "-w", "\n%{http_code}", KNMI], capture_output=True, text=True)
        cuerpo, _, codigo = r.stdout.rpartition("\n")
    else:
        try:
            with urllib_request().urlopen(KNMI, timeout=60) as resp:
                cuerpo, codigo = resp.read().decode("utf-8", "replace"), str(resp.status)
        except Exception as e:  # noqa: BLE001
            cuerpo, codigo = str(e), "error"
    if "verify that I am human" in cuerpo or codigo != "200":
        anotar_bloqueo("knmi_climate_explorer", url=KNMI, http=codigo,
                       motivo="KNMI Climate Explorer exige verificar que el usuario es humano (control antibots) antes "
                              "de usarlo; no se automatiza. Python además rechaza su cadena de certificados. Se usó la "
                              "descarga directa equivalente: CRU TS 4.10 (UEA) y GPCC (PSL), con la correlación con "
                              "Niño 3.4 calculada localmente.")
    else:
        quitar_bloqueo("knmi_climate_explorer")


def urllib_request():
    import urllib.request
    return urllib.request


# ---------------------------------------------------------------- paso clorofila (MODIS-Aqua L3m, OB.DAAC)

# Cajas de 0,5° × 0,5° frente a las desembocaduras (lado mar), el golfo de Fonseca y el Pacífico abierto. (oeste, sur, este, norte)
CAJAS_CHL = {
    "golfo_fonseca": (-87.9, 12.9, -87.3, 13.5),
    "pacifico_fonseca": (-88.3, 12.2, -87.8, 12.7),
    "rio_coco": (-83.15, 14.75, -82.65, 15.25),
    "rio_grande_matagalpa": (-83.5, 12.65, -83.0, 13.15),
    "rio_escondido_bluefields": (-83.68, 11.75, -83.18, 12.25),
}
OBDAAC = "https://oceandata.sci.gsfc.nasa.gov/getfile/"
CHL_ARCHIVO = "AQUA_MODIS.{a:04d}{m:02d}01_{a:04d}{m:02d}{d:02d}.L3m.MO.CHL.chlor_a.4km.nc"
CHL_CSV = AQUI / "clorofila_modis_mensual.csv"


def nombre_chl(a, m):
    import calendar
    return CHL_ARCHIVO.format(a=a, m=m, d=calendar.monthrange(a, m)[1])


def recortar_chl(ruta):
    """Archivo L3m → {caja: (media cos-lat mg m⁻³, fracción de píxeles válidos, n válidos)}."""
    import netCDF4
    d = netCDF4.Dataset(ruta)
    lat, lon = np.asarray(d["lat"][:], float), np.asarray(d["lon"][:], float)
    out = {}
    for k, (o, s, e, n) in CAJAS_CHL.items():
        i0, i1 = gv.indices_rango(lat, s, n)
        j0, j1 = gv.indices_rango(lon, o, e)
        sub = np.ma.filled(d["chlor_a"][i0:i1 + 1, j0:j1 + 1].astype(float), np.nan)
        media, frac = gv.media_caja_coslat(lat[i0:i1 + 1], lon[j0:j1 + 1], sub, (o, s, e, n))
        out[k] = (float(media), float(frac), int(np.isfinite(sub).sum()))
    d.close()
    return out


def paso_clorofila(a0=2003, a1=2024, hilos=3):
    from concurrent.futures import ThreadPoolExecutor

    from clima_nic.fuentes.base import descargar_url
    hechos = {(r["caja"], r["mes"]): [r["caja"], r["mes"], r["chl_mg_m3"], r["fraccion_valida"], r["pixeles_validos"]]
              for r in leer_csv(CHL_CSV)} if CHL_CSV.exists() else {}
    pend = [(a, m) for a in range(a0, a1 + 1) for m in range(1, 13)
            if any((k, f"{a:04d}-{m:02d}") not in hechos for k in CAJAS_CHL)]
    op = gv.abridor_urs()
    tmp = CACHE_C / "chl"

    def uno(am):
        a, m = am
        nombre = nombre_chl(a, m)
        ruta = tmp / nombre
        try:
            descargar_url(OBDAAC + nombre, ruta, abridor=op, timeout=1800)
            res = recortar_chl(ruta)
        except Exception as e:  # noqa: BLE001  (se anota y se sigue con el resto)
            return am, None, str(e)
        finally:
            if ruta.exists():
                ruta.unlink()
        return am, res, None

    errores = []
    with ThreadPoolExecutor(hilos) as ex:
        for (a, m), res, err in ex.map(uno, pend):
            if err:
                errores.append(f"{a}-{m:02d}: {err}")
                continue
            for k, (media, frac, n) in res.items():
                mes = f"{a:04d}-{m:02d}"
                if (k, mes) not in hechos:
                    hechos[(k, mes)] = [k, mes, r4(media) if math.isfinite(media) else "", r4(frac), n]
            filas = [hechos[clave] for clave in sorted(hechos)]
            escribir_csv(CHL_CSV, ["caja", "mes", "chl_mg_m3", "fraccion_valida", "pixeles_validos"], filas)
            print(f"clorofila {a}-{m:02d}", flush=True)
    anotar_consulta("clorofila", url=OBDAAC + CHL_ARCHIVO, errores=errores[:20])


# ---------------------------------------------------------------- paso Giovanni (IMERG, AIRS, OMI NO2)

CAJA_SICC = (-86.5, 10.7, -83.6, 12.6)
# Managua: el casco urbano y el aeropuerto caben en ~0,15°; con celdas OMNO2d de 0,25° la caja toca 2 celdas
# (centros 12,125 N; 86,375 y 86,125 O). Caja rural de fondo del mismo tamaño en zona ganadera de Chontales, a ~1,25°
# al este, sin ciudades grandes (elección razonada, no un fondo validado; revisar el mapa medio de NO2).
CAJA_MANAGUA = (-86.35, 12.05, -86.15, 12.20)
CAJA_RURAL = (-85.10, 12.35, -84.90, 12.50)
CAJA_TEGUCIGALPA = (-87.35, 13.95, -87.05, 14.25)
# Forma de país de Giovanni (US State Department 2017): Nicaragua = shp_163 (Honduras = shp_97), según
# daac-bin/getProvisionedShapefiles.py consultado el 13-11-2026.
SHAPE_NIC = "state_dept_countries_2017/shp_163"
GIOVANNI_SERIES = {
    # clave: (id de variable de Giovanni, inicio, fin, bbox, shape)
    "imerg_caja_sicc": ("GPM_3IMERGM_07_precipitation", "2001-01-01", "2024-12-31", CAJA_SICC, None),
    "imerg_nic": ("GPM_3IMERGM_07_precipitation", "2001-01-01", "2024-12-31", None, SHAPE_NIC),
    "imerg_tegucigalpa": ("GPM_3IMERGM_07_precipitation", "2001-01-01", "2024-12-31", CAJA_TEGUCIGALPA, None),
    "airs_tas_a_nic": ("AIRS3STM_7_0_SurfAirTemp_A", "2003-01-01", "2024-12-31", None, SHAPE_NIC),
    "airs_tas_d_nic": ("AIRS3STM_7_0_SurfAirTemp_D", "2003-01-01", "2024-12-31", None, SHAPE_NIC),
    "omi_no2_managua": ("OMNO2d_003_ColumnAmountNO2TropCloudScreened", "2005-01-01", "2024-12-31", CAJA_MANAGUA, None),
    "omi_no2_rural": ("OMNO2d_003_ColumnAmountNO2TropCloudScreened", "2005-01-01", "2024-12-31", CAJA_RURAL, None),
}
OPENDAP_CSV = AQUI / "opendap"


def _escribir_csv_giovanni(ruta, titulo, var, relleno, filas):
    """Escribe un CSV compatible con `gv.leer_csv_giovanni`."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    lineas = [f'Title:,"{titulo}"', f"Fill Value ({var}):,{relleno}", "", f"time,{var}"]
    for t, v in filas:
        lineas.append(f"{t},{relleno if v is None or not math.isfinite(v) else f'{v:.6g}'}")
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8", newline="\n")


def _nic_exterior():
    from shapely.geometry import Polygon, shape
    from shapely.ops import unary_union
    dom = json.loads((DATOS / "dominios.geojson").read_text(encoding="utf-8"))
    nic = next(shape(f["geometry"]) for f in dom["features"] if f["id"] == "NIC")
    partes = list(getattr(nic, "geoms", [nic]))
    return unary_union([Polygon(p.exterior) for p in partes])


def _hyrax_get_con_reintento(tl_session_fn, url, restriccion, intentos=5, timeout=30):
    import time
    import urllib.parse
    u = f"{url}.ascii?" + urllib.parse.quote(restriccion, safe="/:,")
    espera = 1.0
    for k in range(intentos):
        try:
            r = tl_session_fn().get(u, timeout=timeout)
            if r.status_code == 200 and r.text.lstrip().startswith("Dataset:"):
                return r.text
            if r.status_code not in (429, 500, 502, 503, 504) and not r.text.lstrip().startswith("<"):
                raise RuntimeError(f"{u}: HTTP {r.status_code}")
        except Exception as e:  # noqa: BLE001
            if k == intentos - 1:
                raise RuntimeError(f"{u}: {e}") from e
        time.sleep(espera)
        espera *= 1.5
    raise RuntimeError(u)


def _paso_imerg_opendap(tl_s, pend):
    if not any(k in pend for k in ("imerg_caja_sicc", "imerg_nic", "imerg_tegucigalpa")):
        return
    from concurrent.futures import ThreadPoolExecutor
    from shapely.geometry import Point

    grans = gv.cmr_granulos_opendap("GPM_3IMERGM", "07", "2001-01-01T00:00:00Z,2024-12-31T23:59:59Z")
    lon = np.array([-179.95 + 0.1 * j for j in range(920, 971)])
    lat = np.array([-89.95 + 0.1 * i for i in range(1000, 1061)])
    nic_ext = _nic_exterior()
    mascara_nic = np.array([[nic_ext.contains(Point(lo, la)) for lo in lon] for la in lat])
    pesos_nic = np.where(mascara_nic, np.cos(np.radians(lat))[:, None], 0.0)

    def uno(item):
        ts, u = item
        d = gv.parsear_hyrax_ascii(_hyrax_get_con_reintento(
            tl_s, u, "/Grid/precipitation[0:1:0][920:1:970][1000:1:1060]"))
        pr = np.where(d["precipitation"] < -9000, np.nan, d["precipitation"]).T
        sicc, _ = gv.media_caja_coslat(lat, lon, pr, CAJA_SICC)
        teg, _ = gv.media_caja_coslat(lat, lon, pr, CAJA_TEGUCIGALPA)
        ok = np.isfinite(pr) & (pesos_nic > 0)
        nic_v = float(np.sum(pr[ok] * pesos_nic[ok]) / np.sum(pesos_nic[ok])) if ok.any() else math.nan
        return f"{ts[:10]} 00:00:00", float(sicc), nic_v, float(teg)

    with ThreadPoolExecutor(12) as ex:
        res = sorted(ex.map(uno, grans), key=lambda x: x[0])
    print(f"opendap IMERG: {len(res)} meses", flush=True)
    url_base = "https://opendap.earthdata.nasa.gov/collections/C2723754851-GES_DISC (CMR GPM_3IMERGM.07)"
    if "imerg_caja_sicc" in pend:
        _escribir_csv_giovanni(OPENDAP_CSV / "imerg_caja_sicc.csv",
                               "GPM_3IMERGM v07 precipitation mm/hr (GES DISC OPeNDAP, cos-lat box SICC)",
                               "mean_GPM_3IMERGM_07_precipitation", -9999.9, [(t, s) for t, s, _, _ in res])
        anotar_consulta("opendap_imerg_caja_sicc", url=url_base, metodo="opendap")
    if "imerg_nic" in pend:
        _escribir_csv_giovanni(OPENDAP_CSV / "imerg_nic.csv",
                               "GPM_3IMERGM v07 precipitation mm/hr (GES DISC OPeNDAP, cos-lat NIC con lagos)",
                               "mean_GPM_3IMERGM_07_precipitation", -9999.9, [(t, n) for t, _, n, _ in res])
        anotar_consulta("opendap_imerg_nic", url=url_base, metodo="opendap")
    if "imerg_tegucigalpa" in pend:
        _escribir_csv_giovanni(OPENDAP_CSV / "imerg_tegucigalpa.csv",
                               "GPM_3IMERGM v07 precipitation mm/hr (GES DISC OPeNDAP, cos-lat caja Tegucigalpa)",
                               "mean_GPM_3IMERGM_07_precipitation", -9999.9, [(t, g) for t, _, _, g in res])
        anotar_consulta("opendap_imerg_tegucigalpa", url=url_base, metodo="opendap")


def _paso_airs_opendap(tl_s, pend):
    if not any(k in pend for k in ("airs_tas_a_nic", "airs_tas_d_nic")):
        return
    from concurrent.futures import ThreadPoolExecutor
    from clima_nic import regiones as reg

    grans = gv.cmr_granulos_opendap("AIRS3STM", "7.0", "2003-01-01T00:00:00Z,2024-12-31T23:59:59Z")
    lat = np.array([16.5 - i for i in range(8)])
    lon = np.array([-89.5 + j for j in range(9)])
    pesos = reg.pesos_malla(lat, lon, 1.0, 1.0, {"NIC": _nic_exterior()})
    lat_idx = {round(float(v), 4): i for i, v in enumerate(lat)}
    lon_idx = {round(float(v), 4): j for j, v in enumerate(lon)}
    wl = [(lat_idx[p["lat"]], lon_idx[p["lon"]], p["NIC"]) for p in pesos if p["NIC"] > 0]

    def uno(item):
        ts, u = item
        da = gv.parsear_hyrax_ascii(_hyrax_get_con_reintento(
            tl_s, u, "/ascending/Data_Fields/SurfAirTemp_A[73:1:80][90:1:98],"
                     "/descending/Data_Fields/SurfAirTemp_D[73:1:80][90:1:98]"))
        out = {}
        for k in ("SurfAirTemp_A", "SurfAirTemp_D"):
            arr = np.where(da[k] < 0, np.nan, da[k])
            num = sum(arr[i, j] * w for i, j, w in wl if np.isfinite(arr[i, j]))
            den = sum(w for i, j, w in wl if np.isfinite(arr[i, j]))
            out[k] = float(num / den) if den > 0 else math.nan
        return f"{ts[:7]}-01 00:00:00", out["SurfAirTemp_A"], out["SurfAirTemp_D"]

    with ThreadPoolExecutor(12) as ex:
        por_mes = {t: (a, d) for t, a, d in ex.map(uno, grans)}
    res = sorted(por_mes.items())
    print(f"opendap AIRS: {len(res)} meses", flush=True)
    url_base = "https://opendap.earthdata.nasa.gov/collections/C1701805662-GES_DISC (CMR AIRS3STM.7.0)"
    if "airs_tas_a_nic" in pend:
        _escribir_csv_giovanni(OPENDAP_CSV / "airs_tas_a_nic.csv",
                               "AIRS3STM v7 SurfAirTemp_A K (GES DISC OPeNDAP, area-weighted NIC)",
                               "mean_AIRS3STM_7_0_SurfAirTemp_A", -9999.0, [(t, a) for t, (a, _) in res])
        anotar_consulta("opendap_airs_tas_a_nic", url=url_base, metodo="opendap")
    if "airs_tas_d_nic" in pend:
        _escribir_csv_giovanni(OPENDAP_CSV / "airs_tas_d_nic.csv",
                               "AIRS3STM v7 SurfAirTemp_D K (GES DISC OPeNDAP, area-weighted NIC)",
                               "mean_AIRS3STM_7_0_SurfAirTemp_D", -9999.0, [(t, d) for t, (_, d) in res])
        anotar_consulta("opendap_airs_tas_d_nic", url=url_base, metodo="opendap")


def _paso_omi_opendap(tl_s, pend):
    if not any(k in pend for k in ("omi_no2_managua", "omi_no2_rural")):
        return
    from concurrent.futures import ThreadPoolExecutor
    from shapely.geometry import box
    from clima_nic import regiones as reg

    lat_o = np.array([11.875 + 0.25 * i for i in range(5)])
    lon_o = np.array([-86.375 + 0.25 * j for j in range(8)])
    pesos = reg.pesos_malla(lat_o, lon_o, 0.25, 0.25, {"managua": box(*CAJA_MANAGUA), "rural": box(*CAJA_RURAL)})
    lat_idx = {round(float(v), 4): i for i, v in enumerate(lat_o)}
    lon_idx = {round(float(v), 4): j for j, v in enumerate(lon_o)}
    w_m = [(lat_idx[round(p["lat"], 4)], lon_idx[round(p["lon"], 4)], p["managua"]) for p in pesos if p["managua"] > 0]
    w_r = [(lat_idx[round(p["lat"], 4)], lon_idx[round(p["lon"], 4)], p["rural"]) for p in pesos if p["rural"] > 0]
    cache_omi = CACHE_C / "omi"
    cache_omi.mkdir(parents=True, exist_ok=True)
    todas_m, todas_r = [], []

    for anio in range(2005, P1 + 1):
        c_anio = cache_omi / f"{anio}.csv"
        if c_anio.exists():
            filas = leer_csv(c_anio)
            todas_m.extend((f["fecha"], float(f["managua"]) if f["managua"] else None) for f in filas)
            todas_r.extend((f["fecha"], float(f["rural"]) if f["rural"] else None) for f in filas)
            continue
        grans = gv.cmr_granulos_opendap("OMNO2d", "003", f"{anio}-01-01T00:00:00Z,{anio}-12-31T23:59:59Z")

        def uno(item):
            ts, u = item
            do = gv.parsear_hyrax_ascii(_hyrax_get_con_reintento(
                tl_s, u, "/HDFEOS/GRIDS/ColumnAmountNO2/Data_Fields/ColumnAmountNO2TropCloudScreened[407:1:411][374:1:381]"))
            arr = np.where(do["ColumnAmountNO2TropCloudScreened"] < -1e20, np.nan, do["ColumnAmountNO2TropCloudScreened"])
            def avg(wl):
                num = sum(arr[i, j] * w for i, j, w in wl if np.isfinite(arr[i, j]))
                den = sum(w for i, j, w in wl if np.isfinite(arr[i, j]))
                return float(num / den) if den > 0 else None
            return f"{ts[:10]} 00:00:00", avg(w_m), avg(w_r)

        with ThreadPoolExecutor(16) as ex:
            rows = sorted(ex.map(uno, grans), key=lambda x: x[0])
        escribir_csv(c_anio, ["fecha", "managua", "rural"],
                     [[t, f"{m:.6g}" if m is not None else "", f"{r:.6g}" if r is not None else ""] for t, m, r in rows])
        todas_m.extend((t, m) for t, m, _ in rows)
        todas_r.extend((t, r) for t, _, r in rows)
        print(f"opendap OMI {anio}: {len(rows)} dias", flush=True)

    url_base = "https://opendap.earthdata.nasa.gov/collections/C1266136111-GES_DISC (CMR OMNO2d.003)"
    if "omi_no2_managua" in pend:
        _escribir_csv_giovanni(OPENDAP_CSV / "omi_no2_managua.csv",
                               "OMI OMNO2d v003 ColumnAmountNO2TropCloudScreened molec/cm2 (OPeNDAP, Managua)",
                               "mean_OMNO2d_003_ColumnAmountNO2TropCloudScreened", -1.26765e+30, todas_m)
        anotar_consulta("opendap_omi_no2_managua", url=url_base, metodo="opendap")
    if "omi_no2_rural" in pend:
        _escribir_csv_giovanni(OPENDAP_CSV / "omi_no2_rural.csv",
                               "OMI OMNO2d v003 ColumnAmountNO2TropCloudScreened molec/cm2 (OPeNDAP, Chontales rural)",
                               "mean_OMNO2d_003_ColumnAmountNO2TropCloudScreened", -1.26765e+30, todas_r)
        anotar_consulta("opendap_omi_no2_rural", url=url_base, metodo="opendap")


def paso_giovanni_opendap(claves=None):
    import threading
    pend = {k for k in (claves or GIOVANNI_SERIES) if not (OPENDAP_CSV / f"{k}.csv").exists()}
    if not pend:
        return
    tls = threading.local()
    def tl_s():
        if not hasattr(tls, "s"):
            tls.s = gv.sesion_urs_http(conexiones=4)
        return tls.s
    _paso_imerg_opendap(tl_s, pend)
    _paso_airs_opendap(tl_s, pend)
    _paso_omi_opendap(tl_s, pend)


def paso_giovanni(claves=None, max_espera=45, usar_opendap=True):
    pend = [k for k in (claves or GIOVANNI_SERIES) if not (OPENDAP_CSV / f"{k}.csv").exists()]
    if not pend:
        return
    tok = os.environ.get("EARTHDATA_TOKEN", "").strip()
    if tok:
        for k in list(pend):
            var, i, f, bbox, shape = GIOVANNI_SERIES[k]
            try:
                txt = gv.api_giovanni_serie(var, i, f, bbox=bbox, shape=shape, token=tok)
                gv.leer_csv_giovanni(txt)
                destino = OPENDAP_CSV / f"{k}.csv"
                destino.parent.mkdir(parents=True, exist_ok=True)
                destino.write_text(txt.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
                quitar_bloqueo(f"giovanni_{k}")
                anotar_consulta(f"giovanni_{k}", url="https://api.giovanni.earthdata.nasa.gov/timeseries")
                pend.remove(k)
            except Exception as e:  # noqa: BLE001
                anotar_bloqueo(f"giovanni_{k}", url="https://api.giovanni.earthdata.nasa.gov/timeseries", motivo=str(e)[:400])
    else:
        anotar_bloqueo("giovanni_api_token", url="https://api.giovanni.earthdata.nasa.gov/timeseries", http=403,
                       motivo="EARTHDATA_TOKEN no está en el entorno; api.giovanni.earthdata.nasa.gov exige Bearer token.")

    if pend:
        op, motivo = gv.iniciar_sesion()
        if op is None:
            for k in pend:
                var, i, f, bbox, shape = GIOVANNI_SERIES[k]
                anotar_bloqueo(f"giovanni_{k}", url=gv.url_serie_area(var, i, f, bbox=bbox, shape=shape), http=302,
                               motivo=f"Earthdata Login: {motivo}.")
        else:
            k0 = pend[0]
            var, i, f, bbox, shape = GIOVANNI_SERIES[k0]
            url0 = gv.url_serie_area(var, i, f, bbox=bbox, shape=shape)
            try:
                _, urls = gv.ejecutar(op, url0, espera=5, max_espera=max_espera)
                for k in list(pend):
                    var, i, f, bbox, shape = GIOVANNI_SERIES[k]
                    u = gv.url_serie_area(var, i, f, bbox=bbox, shape=shape)
                    _, urls = gv.ejecutar(op, u, espera=5, max_espera=300)
                    csvs = [x for x in urls if x.lower().endswith(".csv")] or urls
                    texto = op.open(csvs[0] if csvs[0].startswith("http") else gv.GIOVANNI + csvs[0], timeout=600).read()
                    gv.leer_csv_giovanni(texto.decode("utf-8"))
                    destino = OPENDAP_CSV / f"{k}.csv"
                    destino.parent.mkdir(parents=True, exist_ok=True)
                    destino.write_bytes(texto.replace(b"\r\n", b"\n"))
                    quitar_bloqueo(f"giovanni_{k}")
                    anotar_consulta(f"giovanni_{k}", url=u)
                    pend.remove(k)
            except Exception as e:  # noqa: BLE001
                for k in pend:
                    var, i, f, bbox, shape = GIOVANNI_SERIES[k]
                    anotar_bloqueo(f"giovanni_{k}", url=gv.url_serie_area(var, i, f, bbox=bbox, shape=shape), http=200,
                                   motivo=f"Giovanni ArAvTs ({str(e)[:220]}). Se usó el equivalente GES DISC OPeNDAP.")
    if pend and usar_opendap:
        paso_giovanni_opendap(pend)


# ---------------------------------------------------------------- resumen (sin red)

def _clima():
    return json.loads((DATOS / "clima.json").read_text(encoding="utf-8"))


def _anual_lluvia(ruta, region):
    filas = [r for r in leer_csv(ruta) if r["region"] == region]
    por = {}
    for r in filas:
        por.setdefault(int(r["mes"][:4]), {})[int(r["mes"][5:7])] = float(r["mm"]) if r["mm"] else None
    anual = {a: sum(d.values()) for a, d in por.items() if len(d) == 12 and None not in d.values()}
    jun_nov = {a: sum(d[m] for m in range(6, 12)) for a, d in por.items()
               if all(d.get(m) is not None for m in range(6, 12))}
    return anual, jun_nov


def _power_celdas(variable):
    out = {}
    for r in leer_csv(FENOMENOS / "indices_anuales_celdas.csv"):
        if r[variable]:
            out.setdefault((float(r["lat"]), float(r["lon"])), {})[int(r["anio"])] = float(r[variable])
    return out


def _gistemp_anual(columna="NIC"):
    tiempos, vals = [], []
    for r in leer_csv(FENOMENOS / "gistemp_nicaragua.csv"):
        tiempos.append(f"{int(r['anio']):04d}-{int(r['mes']):02d}")
        vals.append(float(r[columna]) if r[columna] else None)
    a, v = gv.anual_media(tiempos, vals, 12)
    return dict(zip(a, v))


def _power_region(indice, region="NIC"):
    return {int(r["anio"]): float(r["valor"]) for r in leer_csv(FENOMENOS / "indices_anuales_regiones.csv")
            if r["region"] == region and r["indice"] == indice}


def _corr(x, y):
    comunes = sorted(set(x) & set(y))
    if len(comunes) < 3:
        return None, len(comunes)
    return r4(np.corrcoef([x[a] for a in comunes], [y[a] for a in comunes])[0, 1]), len(comunes)


def _ventana(serie, a0=P0, a1=P1):
    return {a: v for a, v in serie.items() if a0 <= a <= a1}


def _serie_resumen(v, fuente, unidad, /, **extra):
    """Bloque serie_nuestra/serie_externa a partir de gv.veredicto_serie."""
    extra = {k: x for k, x in extra.items() if k != "fuente"}
    if v is None:
        return {"fuente": fuente, "pendiente": None, "unidad": unidad, "veredicto": None, **extra}
    return {"fuente": fuente, "pendiente": v.get("sen_por_decada"), "pendiente_mco": v.get("mco_por_decada"),
            "unidad": f"{unidad}/década", "veredicto": v.get("veredicto_contrato"),
            "veredicto_robusto": v.get("veredicto"), "periodo": v.get("periodo"), "anios": v.get("anios"),
            "mann_kendall_p": (v.get("mann_kendall") or {}).get("p_valor"), **extra}


def _guardar_series(filas, cid, nuestra, externa):
    for a, v in sorted(nuestra.items()):
        filas.append([cid, "nuestra", a, r4(v)])
    for a, v in sorted(externa.items()):
        filas.append([cid, "externa", a, r4(v)])


def _contraste(cid, papel, region, periodo, nuestra, externa, unidad, fuente_n, fuente_e, frase, filas_series,
               externa_meta, **extra):
    """Compara dos series anuales {año: valor} en la ventana `periodo` con los métodos del backend."""
    n = _ventana(nuestra, *periodo)
    e = _ventana(externa, *periodo)
    _guardar_series(filas_series, cid, n, e)
    comunes = sorted(set(n) & set(e))
    c = gv.comparar_anual(comunes, [n[a] for a in comunes], comunes, [e[a] for a in comunes], unidad) \
        if len(comunes) >= 3 else {"anios_comunes": len(comunes)}
    vn = gv.veredicto_serie(sorted(n), [n[a] for a in sorted(n)], unidad) if len(n) >= 10 else None
    ve = gv.veredicto_serie(sorted(e), [e[a] for a in sorted(e)], unidad) if len(e) >= 10 else None
    dif_p = r4(ve["sen_por_decada"] - vn["sen_por_decada"]) if vn and ve and "sen_por_decada" in vn and \
        "sen_por_decada" in ve else None
    return {"id": cid, "papel": papel, "region": region, "periodo": list(periodo),
            "serie_nuestra": _serie_resumen(vn, fuente_n, unidad),
            "serie_externa": _serie_resumen(ve, fuente_e, unidad, **externa_meta),
            "diferencia": {"media": c.get("diferencia_media"), "r": c.get("r"), "diferencia_pendiente": dif_p,
                           "anios_comunes": c.get("anios_comunes"), "unidad_media": unidad},
            "estado": "ok", "frase_en": frase, **extra}


def _bloqueado(cid, papel, region, periodo, fuente_n, fuente_e, unidad, motivo, frase, externa_meta):
    return {"id": cid, "papel": papel, "region": region, "periodo": list(periodo),
            "serie_nuestra": {"fuente": fuente_n, "pendiente": None, "unidad": f"{unidad}/década", "veredicto": None},
            "serie_externa": {"fuente": fuente_e, "pendiente": None, "unidad": f"{unidad}/década", "veredicto": None,
                              **externa_meta},
            "diferencia": {"media": None, "r": None, "diferencia_pendiente": None},
            "estado": "bloqueado", "motivo": motivo, "frase_en": frase}


def _meta(clave, fuente=None, version=None, url=None):
    base = FUENTES.get(clave, {})
    cons = fecha_consulta(clave) or {}
    return {"fuente": fuente or base.get("fuente"), "version": version or base.get("version"),
            "fecha_consulta": cons.get("fecha"), "url": url or cons.get("url") or base.get("url")}


def contrastes_lluvia(filas_series):
    cj = _clima()
    dom = {d["id"]: d for d in cj["dominios"]}
    oni = dict(zip(cj["oni"]["anios"], cj["oni"]["oni_temporada"]))
    out = []
    nombres = {"caja_sicc": "SICC box (10.7–12.6°N, 86.5–83.6°W)", "NIC": "Nicaragua", "HND": "Honduras"}
    for fuente, ruta, etiqueta in (("cru", AQUI / "lluvia_mensual_externa_cru.csv", "CRU TS 4.10"),
                                   ("gpcc", AQUI / "lluvia_mensual_externa_gpcc.csv", "GPCC (PSL copy)")):
        if not ruta.exists():
            continue
        for reg in ("caja_sicc", "NIC"):
            imerg = dict(zip(dom[reg]["anios_validos"], dom[reg]["serie_anual_mm"]))
            anual, jun_nov = _anual_lluvia(ruta, reg)
            imerg_jn = dict(zip(cj["oni"]["anios"], cj["oni"]["lluvia_jun_nov_mm"][reg]))
            r_ext, n_ext = _corr(oni, _ventana(jun_nov))
            r_nue, _ = _corr(oni, imerg_jn)
            meta = _meta(fuente)
            c = _contraste(f"{fuente}_{reg.lower()}", "contraste", reg, (P0, P1), imerg, anual, "mm",
                           "GPM IMERG Final V07B (data/clima.json)", meta["fuente"], "", filas_series, meta)
            c["serie_nuestra"]["veredicto_clima_json"] = dom[reg]["tendencia"]["veredicto"]
            c["nino34_jun_nov"] = {"indice": "ONI (Niño 3.4) media jun–nov, data/clima.json", "n": n_ext,
                                   "r_externa": r_ext, "r_nuestra": r_nue,
                                   "r_nuestra_clima_json": cj["oni"]["correlacion_descriptiva"][reg]["r"]}
            if fuente == "cru":
                stn = {}
                for r in leer_csv(AQUI / "cru_estaciones_mensual.csv"):
                    if r["region"] == reg:
                        stn.setdefault(int(r["mes"][:4]), []).append(float(r["estaciones_media_ponderada"]))
                c["cru_estaciones_por_celda"] = {"2001_2014": r4(np.mean([np.mean(v) for a, v in stn.items() if a <= 2014])),
                                                 "2015_2024": r4(np.mean([np.mean(v) for a, v in stn.items() if a >= 2015]))}
            d = c["diferencia"]
            sn, se = c["serie_nuestra"], c["serie_externa"]
            c["frase_en"] = (f"{etiqueta} vs IMERG over {nombres[reg]}, 2001–2024: r = {d['r']:.2f}, mean difference "
                             f"{d['media']:+.0f} mm/yr; Sen slopes {se['pendiente']:+.0f} vs {sn['pendiente']:+.0f} "
                             f"mm/decade; both '{en(se['veredicto'])}'"
                             if se["veredicto"] == sn["veredicto"] else
                             f"{etiqueta} vs IMERG over {nombres[reg]}, 2001–2024: r = {d['r']:.2f}, mean difference "
                             f"{d['media']:+.0f} mm/yr; verdicts differ ({en(se['veredicto'])} vs {en(sn['veredicto'])})")
            c["frase_en"] += f"; June–November correlation with Niño 3.4: {r_ext:+.2f} ({etiqueta}) vs {r_nue:+.2f} (IMERG)."
            out.append(c)
    return out


def coordenadas_estaciones():
    """{estacion: (lat, lon, elevación m)} del CSV de GSOM guardado."""
    out = {}
    for r in leer_csv(NOAA / "gsom_estaciones.csv"):
        out[r["STATION"]] = (float(r["LATITUDE"]), float(r["LONGITUDE"]), float(r["ELEVATION"]))
    return out


def celda_power_cercana(lat, lon):
    """Celda POWER (de data/fenomenos/celdas_power.csv) más cercana: (lat, lon), distancia km, elevación m."""
    mejor = None
    for r in leer_csv(FENOMENOS / "celdas_power.csv"):
        la, lo = float(r["lat"]), float(r["lon"])
        dlat, dlon = math.radians(la - lat), math.radians(lo - lon)
        h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat)) * math.cos(math.radians(la)) * math.sin(dlon / 2) ** 2
        km = 2 * 6371.0 * math.asin(math.sqrt(h))
        if mejor is None or km < mejor[1]:
            mejor = ((la, lo), km, float(r["elevacion_m"]))
    return mejor


def _imerg_mensual(dominio):
    return {f"{int(r['anio']):04d}-{int(r['mes']):02d}": float(r["mm"])
            for r in leer_csv(DATOS / "serie_mensual.csv") if r["dominio"] == dominio}


def contrastes_estaciones(filas_series):
    mens = leer_csv(NOAA / "estaciones_mensual.csv")
    coords = coordenadas_estaciones()
    gis = _gistemp_anual("NIC")
    t2m_celdas = _power_celdas("t2m_media")
    pr_celdas = _power_celdas("prcptot")
    cj = _clima()
    dom = {d["id"]: d for d in cj["dominios"]}
    out = []
    for st, nombre in (("NUM00078741", "Managua International"), ("NU000069034", "Juigalpa"),
                       ("HO000078720", "Tegucigalpa")):
        filas = [r for r in mens if r["estacion"] == st]
        tav = {r["mes"]: float(r["tavg_c_ghcnd"]) for r in filas if r["tavg_c_ghcnd"]}
        anual = nc.anual_desde_mensual(tav, "media")
        la, lo, elev = coords[st]
        celda, km, elev_celda = celda_power_cercana(la, lo)
        power = t2m_celdas[celda]
        meta = _meta("ghcnd")
        cid = f"noaa_{nombre.split()[0].lower()}_tavg"
        c = _contraste(cid, "contraste", nombre, (P0, P1), power, anual, "°C",
                       f"NASA POWER T2M (MERRA-2), celda {celda[0]} N {celda[1]} O", f"{meta['fuente']} TAVG {st}",
                       "", filas_series, meta)
        c["estacion"] = {"id": st, "lat": la, "lon": lo, "elevacion_m": elev, "celda_power": list(celda),
                         "distancia_km": round(km, 1), "elevacion_celda_m": elev_celda}
        # Validación en todo el período común y contra GISTEMP (anomalías).
        r_power_todo, n_power_todo = _corr(power, anual)
        an_est = {a: v - np.mean([anual[x] for x in anual if P0 <= x <= P1]) for a, v in anual.items()}
        r_gis, n_gis = _corr(gis, an_est)
        gv_gis = gv.veredicto_serie(sorted(_ventana(gis)), [gis[a] for a in sorted(_ventana(gis))], "°C")
        c["otras_referencias"] = [
            {"fuente": "NASA POWER T2M, misma celda, todos los años comunes", "r": r_power_todo,
             "anios_comunes": n_power_todo},
            {"fuente": "GISTEMP v4 (anomalías, región NIC, data/fenomenos)", "r_anomalias": r_gis,
             "anios_comunes": n_gis, "pendiente_2001_2024": gv_gis.get("sen_por_decada"),
             "veredicto_2001_2024": gv_gis.get("veredicto_contrato"),
             "diferencia_pendiente_estacion_menos_gistemp": r4(c["serie_externa"]["pendiente"] -
                                                                gv_gis["sen_por_decada"])
             if c["serie_externa"]["pendiente"] is not None else None}]
        anios_completos = sorted(a for a in anual if P0 <= a <= P1)
        c["anios_completos_2001_2024"] = len(anios_completos)
        c["nota"] = ("TAVG de GHCN-Daily para estas estaciones proviene de mensajes SYNOP (media diaria), sin "
                     "homogeneizar; un mes vale con >= 20 días y un año con los 12 meses. diferencia.media = estación − "
                     f"celda POWER; la celda está a {km:.0f} km y su elevación media es {elev_celda:.0f} m frente a "
                     f"{elev:.0f} m de la estación.")
        se, sn, d = c["serie_externa"], c["serie_nuestra"], c["diferencia"]
        if se["pendiente"] is not None:
            calor = "warmer" if d["media"] >= 0 else "cooler"
            c["frase_en"] = (f"{nombre} station (GHCN-Daily mean temperature, {len(anios_completos)} complete years in "
                             f"2001–2024) vs NASA POWER/MERRA-2: r = {d['r']:.2f}, station {abs(d['media']):.1f} °C "
                             f"{calor}; trends {se['pendiente']:+.2f} vs {sn['pendiente']:+.2f} °C/decade "
                             f"({en(se['veredicto'])} vs {en(sn['veredicto'])}).")
        else:
            c["frase_en"] = f"{nombre} station has too few complete years in 2001–2024 for a trend."
        out.append(c)

    # Lluvia de Tegucigalpa (GSOM) frente a IMERG Honduras (clima.json y serie mensual).
    teg = {r["mes"]: float(r["prcp_mm_gsom"]) for r in mens if r["estacion"] == "HO000078720" and r["prcp_mm_gsom"]}
    teg_anual = nc.anual_desde_mensual(teg, "suma")
    hnd = dict(zip(dom["HND"]["anios_validos"], dom["HND"]["serie_anual_mm"]))
    meta = _meta("gsom")
    c = _contraste("noaa_tegucigalpa_lluvia_vs_imerg_hnd", "contraste", "Tegucigalpa / Honduras", (P0, P1), hnd,
                   teg_anual, "mm", "GPM IMERG Final V07B, Honduras (data/clima.json)",
                   f"{meta['fuente']} PRCP HO000078720", "", filas_series, meta)
    hnd_m = _imerg_mensual("HND")
    comunes = sorted(m for m in teg if m in hnd_m and P0 <= int(m[:4]) <= P1)
    x = np.array([hnd_m[m] for m in comunes])
    y = np.array([teg[m] for m in comunes])
    clim_x = {k: np.mean([hnd_m[m] for m in comunes if int(m[5:7]) == k]) for k in range(1, 13)}
    clim_y = {k: np.mean([teg[m] for m in comunes if int(m[5:7]) == k]) for k in range(1, 13)}
    ax = np.array([hnd_m[m] - clim_x[int(m[5:7])] for m in comunes])
    ay = np.array([teg[m] - clim_y[int(m[5:7])] for m in comunes])
    c["mensual"] = {"meses_comunes": len(comunes), "r_mensual": r4(np.corrcoef(x, y)[0, 1]),
                    "r_anomalias_mensuales": r4(np.corrcoef(ax, ay)[0, 1]),
                    "cociente_medio_estacion_imerg": r4(y.sum() / x.sum())}
    c["nota"] = ("Una estación (valle a 1 007 m, sombra pluviométrica) frente a la media de todo Honduras: la diferencia "
                 "media es sobre todo de representatividad, no un error de IMERG. GSOM da pocos años con los 12 meses, "
                 "por eso se añade la comparación mensual.")
    d, m = c["diferencia"], c["mensual"]
    c["frase_en"] = (f"Tegucigalpa rain gauge (GSOM) vs IMERG Honduras average, {m['meses_comunes']} common months in "
                     f"2001–2024: r = {m['r_mensual']:.2f} (anomalies {m['r_anomalias_mensuales']:.2f}); the valley "
                     f"station gets {100 * m['cociente_medio_estacion_imerg']:.0f}% of the national mean rain "
                     f"(representativeness, not bias). Only {d['anios_comunes']} complete years: no trend comparison.")
    out.append(c)

    # Lluvia de las estaciones de Nicaragua frente a la celda POWER más cercana (validación, sin tendencia).
    por_est = []
    for st in ("NUM00078741", "NU000069034", "NU000055002", "NU000055029", "NU000055016"):
        pm = {r["mes"]: float(r["prcp_mm_gsom"]) for r in mens if r["estacion"] == st and r["prcp_mm_gsom"]}
        an = nc.anual_desde_mensual(pm, "suma")
        la, lo, elev = coords[st]
        celda, km, elev_celda = celda_power_cercana(la, lo)
        pw = pr_celdas[celda]
        com = sorted(set(an) & set(pw))
        r_, _ = _corr(an, pw)
        por_est.append({"estacion": st, "nombre": nc.ESTACIONES[st], "lat": la, "lon": lo, "elevacion_m": elev,
                        "celda_power": list(celda), "distancia_km": round(km, 1), "anios_comunes": len(com),
                        "periodo": [com[0], com[-1]] if com else None, "r": r_,
                        "diferencia_media_mm": r4(np.mean([pw[a] - an[a] for a in com])) if com else None,
                        "ultimo_mes_con_lluvia": max(pm) if pm else None,
                        "ultimo_anio_completo": max(an) if an else None,
                        "meses_con_lluvia_2001_2024": sum(1 for k in pm if P0 <= int(k[:4]) <= P1)})
        for a in com:
            filas_series.append(["noaa_estaciones_nic_lluvia", f"externa_{st}", a, r4(an[a])])
            filas_series.append(["noaa_estaciones_nic_lluvia", f"nuestra_{st}", a, r4(pw[a])])
    ultimo_mes = max(p["ultimo_mes_con_lluvia"] for p in por_est if p["ultimo_mes_con_lluvia"])
    rs = [p["r"] for p in por_est if p["r"] is not None]
    difs = [p["diferencia_media_mm"] for p in por_est if p["diferencia_media_mm"] is not None]
    out.append({"id": "noaa_estaciones_nic_lluvia", "papel": "contraste", "region": "Nicaragua (5 estaciones)",
                "periodo": [min(p["periodo"][0] for p in por_est if p["periodo"]),
                            max(p["periodo"][1] for p in por_est if p["periodo"])],
                "serie_nuestra": {"fuente": "NASA POWER PRECTOTCORR, celda más cercana", "pendiente": None,
                                  "unidad": "mm/década", "veredicto": "no_aplica"},
                "serie_externa": {**_meta("gsom"), "fuente": "NOAA NCEI GSOM PRCP", "pendiente": None,
                                  "unidad": "mm/década", "veredicto": "no_aplica"},
                "diferencia": {"media": r4(np.median(difs)), "r": r4(np.median(rs)), "diferencia_pendiente": None,
                               "estadistico": "mediana entre estaciones", "unidad_media": "mm"},
                "por_estacion": por_est, "estado": "ok",
                "nota": (f"La lluvia de las estaciones de Nicaragua en NCEI termina en {ultimo_mes} (último mes con "
                         "dato; los últimos años completos son de 1989 a 1991): no sirve para la tendencia de lluvia "
                         "2001–2024. Solo valida POWER en los años comunes de la década de 1980."),
                "frase_en": (f"Nicaraguan rain gauges in NOAA archives end by {ultimo_mes[:4]} (last complete years "
                             f"1989–1991), so they cannot test the 2001–2024 rain trend; in the 1980s their annual "
                             f"totals correlate only weakly with NASA POWER (median r = {np.median(rs):.2f}).")})
    return out


# ---- clorofila: método NTRS 20090042747 (Acker et al.) + Theil–Sen + Mann–Kendall

def ntrs_clorofila(meses, valores):
    """OLS sobre la serie mensual cruda (ANOVA F), anomalías por mes calendario promediadas por año (OLS) y
    Theil–Sen (robusta). meses «AAAA-MM»; valores con None/NaN = mes sin dato."""
    from scipy import stats
    t = np.array([int(m[:4]) + (int(m[5:7]) - 0.5) / 12 for m, v in zip(meses, valores) if v is not None])
    y = np.array([v for v in valores if v is not None], float)
    n = len(y)
    res = stats.linregress(t, y)
    f = (res.rvalue ** 2 / (1 - res.rvalue ** 2)) * (n - 2) if res.rvalue ** 2 < 1 else float("inf")
    p_f = float(stats.f.sf(f, 1, n - 2))
    ts = stats.theilslopes(y, t)
    clim = {}
    for m, v in zip(meses, valores):
        if v is not None:
            clim.setdefault(int(m[5:7]), []).append(v)
    clim = {k: float(np.mean(v)) for k, v in clim.items()}
    por = {}
    for m, v in zip(meses, valores):
        if v is not None:
            por.setdefault(int(m[:4]), []).append(v - clim[int(m[5:7])])
    return {
        "n_meses": n,
        "mco_mensual": {"pendiente_por_decada": r4(res.slope * 10), "r2": r4(res.rvalue ** 2), "F": r4(f),
                        "p_valor_F": r4(p_f), "significativa_5pct": p_f < 0.05},
        "theil_sen_mensual": {"pendiente_por_decada": r4(ts.slope * 10),
                              "ic95_por_decada": [r4(ts.low_slope * 10), r4(ts.high_slope * 10)]},
        "anomalias_anuales": {a: float(np.mean(v)) for a, v in sorted(por.items())},
        "meses_por_anio": {a: len(v) for a, v in sorted(por.items())},
    }


def contrastes_clorofila(filas_series, min_meses=9):
    if not CHL_CSV.exists():
        return []
    filas = leer_csv(CHL_CSV)
    meta = _meta("clorofila", "NASA OBPG MODIS-Aqua L3m CHL chlor_a 4 km mensual", "R2022.0",
                 OBDAAC + CHL_ARCHIVO)
    nombres = {"golfo_fonseca": "Gulf of Fonseca", "pacifico_fonseca": "Open Pacific off Gulf of Fonseca",
               "rio_coco": "Coco River mouth",
               "rio_grande_matagalpa": "Grande de Matagalpa River mouth",
               "rio_escondido_bluefields": "Escondido River / Bluefields Bay"}
    out = []
    for caja in CAJAS_CHL:
        sub = [r for r in filas if r["caja"] == caja]
        maxpix = max(int(r["pixeles_validos"]) for r in sub)
        meses = [r["mes"] for r in sub]
        vals = [float(r["chl_mg_m3"]) if r["chl_mg_m3"] and int(r["pixeles_validos"]) >= 0.2 * maxpix else None
                for r in sub]
        nt = ntrs_clorofila(meses, vals)
        anom = {a: v for a, v in nt["anomalias_anuales"].items() if nt["meses_por_anio"][a] >= min_meses}
        clim_media = float(np.mean([v for v in vals if v is not None]))
        anual = {a: clim_media + v for a, v in anom.items()}  # media anual desestacionalizada (mg m⁻³)
        cid = f"clorofila_{caja}"
        _guardar_series(filas_series, cid, anual, {})
        v = gv.veredicto_serie(sorted(anual), [anual[a] for a in sorted(anual)], "mg m-3") if len(anual) >= 10 else None
        sen = v.get("sen_por_decada") if v else None
        mco = nt["mco_mensual"]
        coinciden = (v is not None and (v.get("mann_kendall") or {}).get("significativo") == mco["significativa_5pct"]
                     and (sen or 0) * (mco["pendiente_por_decada"] or 0) >= 0)
        tit_chl = f"Chlorophyll-a ({nombres[caja]}, MODIS-Aqua)"
        def_chl = ("NASA OBPG MODIS-Aqua R2022.0 monthly 4 km chlor_a deseasonalized annual mean (mg/m^3) over the "
                   f"{nombres[caja]} 0.5x0.5 deg box, 2003-2024.")
        c = {"id": cid, "papel": "tendencia", "region": nombres[caja], "caja": list(CAJAS_CHL[caja]),
             "titulo_en": tit_chl, "definicion_en": def_chl,
             "periodo": [min(anual), max(anual)] if anual else None,
             "serie_nuestra": {**_serie_resumen(v, f"{meta['fuente']} ({caja}), anual desestacionalizada", "mg m-3"),
                               "anios_validos": len(anual), "meses_validos": nt["n_meses"]},
             "serie_externa": {"fuente": "Método NTRS 20090042747 (Acker et al.): OLS mensual cruda + ANOVA F",
                               **{k: meta[k] for k in ("version", "fecha_consulta", "url")},
                               "pendiente": mco["pendiente_por_decada"], "unidad": "mg m-3/década",
                               "veredicto": "significativa_p<0.05" if mco["significativa_5pct"] else "no_significativa",
                               "r2": mco["r2"], "p_valor_F": mco["p_valor_F"],
                               "theil_sen_mensual": nt["theil_sen_mensual"]},
             "diferencia": {"media": None, "r": None,
                            "diferencia_pendiente": r4(mco["pendiente_por_decada"] - sen) if sen is not None else None},
             "metodos_coinciden": coinciden, "estado": "ok" if v else "bloqueado",
             "media_serie_mg_m3": r4(clim_media),
             # Acker et al.: cajas con chl media <= 1 mg m-3 para limitar la turbidez y el CDOM.
             "cumple_criterio_ntrs_1mg": clim_media <= 1.0}
        if not v:
            c["motivo"] = "menos de 10 años con datos suficientes"
        sig = "significant" if mco["significativa_5pct"] else "not significant"
        p_txt = "p < 0.001" if mco["p_valor_F"] < 0.001 else f"p = {mco['p_valor_F']:.2f}"
        c["frase_en"] = (f"MODIS-Aqua chlorophyll-a, {nombres[caja]} ({c['periodo'][0]}–{c['periodo'][1]}): OLS on raw "
                         f"monthly data {mco['pendiente_por_decada']:+.2f} mg/m³ per decade ({sig}, {p_txt}); "
                         f"Theil–Sen on deseasonalized annual means {sen:+.2f}, verdict "
                         f"'{en(c['serie_nuestra']['veredicto'])}'.") if v else \
            f"MODIS-Aqua chlorophyll-a, {nombres[caja]}: not enough cloud-free months for a trend."
        if v and clim_media > 1.0:
            c["frase_en"] += (f" Caution: mean {clim_media:.1f} mg/m³ exceeds the 1 mg/m³ limit used by Acker et al. "
                              "to avoid turbid water, so sediment may be read as chlorophyll.")
        out.append(c)
    return out


# ---------------------------------------------------------------- Giovanni en la nube (servicio oficial)
# Servicio «Area-Averaged Time Series» de Giovanni a través de Harmony, según el cuaderno oficial de GES DISC
# How_To_Access_the_Giovanni_Averaging_Service_Using_Python.ipynb (nasa/gesdisc-tutorials, abril de 2026).
# Solo admite cajas (no polígonos), así que se usa la caja SICC, que es una caja exacta en data/dominios.geojson.
# Requiere `earthaccess` y `harmony-py` y una cuenta Earthdata en el .netrc; el token no se guarda.
GIOVANNI_NUBE = AQUI / "giovanni"
GIOVANNI_NUBE_SERIES = {
    # clave: (short_name, versión, variable de Giovanni, caja oeste-sur-este-norte)
    "imerg_caja_sicc": ("GPM_3IMERGM", "07", "GPM_3IMERGM_07_precipitation", (-86.5, 10.7, -83.6, 12.6)),
    "gldas_sm0_10_caja_sicc": ("GLDAS_NOAH025_M", "2.1", "GLDAS_NOAH025_M_2_1_SoilMoi0_10cm_inst", (-86.5, 10.7, -83.6, 12.6)),
}
GIOVANNI_CUOTA = "https://api.giovanni.earthdata.nasa.gov/quota"


def paso_giovanni_nube():
    import earthaccess
    import requests
    from harmony import BBox, Client, Collection, Request

    earthaccess.login(strategy="netrc")
    token = earthaccess.get_edl_token()["access_token"]
    cuota = requests.get(GIOVANNI_CUOTA, headers={"Authorization": f"Bearer {token}"}, timeout=60).json()
    print("Cuota de Giovanni usada este mes:", cuota.get("quota"))
    cliente = Client(token=token)
    GIOVANNI_NUBE.mkdir(exist_ok=True)
    CACHE_C.mkdir(parents=True, exist_ok=True)
    for clave, (corto, ver, var, caja) in GIOVANNI_NUBE_SERIES.items():
        cid = earthaccess.search_datasets(short_name=corto, version=ver)[0].concept_id
        pet = Request(collection=Collection(id=cid), temporal={"start": dt.datetime(P0, 1, 1), "stop": dt.datetime(P1, 12, 31)},
                      spatial=BBox(*caja), variables=[var], format="text/csv", average="area")
        trabajo = cliente.submit(pet)
        for res in cliente.download_all(trabajo, directory=str(CACHE_C), overwrite=True):
            texto = Path(res.result()).read_text(encoding="utf-8")
        (GIOVANNI_NUBE / f"{clave}.csv").write_text(texto.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
        anotar_consulta(f"giovanni_{clave}", metodo="Giovanni Area-Averaged Time Series vía Harmony",
                        url=f"https://harmony.earthdata.nasa.gov/jobs/{trabajo}", variable=var, caja=list(caja))
        print("Giovanni", clave, ":", GIOVANNI_NUBE / f"{clave}.csv")


def contrastes_giovanni_nube(filas_series):
    out = []
    cj = _clima()
    caja = next(d for d in cj["dominios"] if d["id"] == "caja_sicc")
    imerg = dict(zip(caja["anios_validos"], caja["serie_anual_mm"]))
    fuente = "NASA Giovanni, Area-Averaged Time Series ({}; consulta {})"
    ruta = GIOVANNI_NUBE / "imerg_caja_sicc.csv"
    if ruta.exists():
        d = gv.leer_csv_giovanni(ruta.read_text(encoding="utf-8"))
        ext = dict(zip(*gv.mensual_tasa_a_anual(d["tiempos"], d["valores"])))
        cons = fecha_consulta("giovanni_imerg_caja_sicc") or {}
        meta = {"fuente": fuente.format("GPM_3IMERGM 07", cons.get("fecha")), "version": "GPM_3IMERGM 07",
                "fecha_consulta": cons.get("fecha"), "url": cons.get("url")}
        c = _contraste("giovanni_imerg_caja_sicc", "contraste", "caja_sicc", (P0, P1), imerg, ext, "mm",
                       "GPM IMERG Final V07B (data/clima.json)", meta["fuente"], "", filas_series, meta,
                       investigacion="lluvia_caja_sicc")
        dif = c["diferencia"]
        c["frase_en"] = (f"NASA Giovanni's own area average of IMERG monthly over the SICC box reproduces this app's "
                         f"series: r = {dif['r']:.3f}, mean difference {dif['media']:+.1f} mm/yr over 2001–2024.")
        out.append(c)
    ruta = GIOVANNI_NUBE / "gldas_sm0_10_caja_sicc.csv"
    tierra = DATOS / "recursos" / "tierra" / "series_gldas_anual.json"
    if ruta.exists() and tierra.exists():
        nuestra = next(s for s in json.loads(tierra.read_text(encoding="utf-8"))
                       if s["region"] == "caja_sicc" and s["variable"] == "humedad_gldas_0_10")
        d = gv.leer_csv_giovanni(ruta.read_text(encoding="utf-8"))
        # SoilMoi0_10cm_inst viene en kg/m² para una capa de 0,1 m: /100 da m³/m³.
        anios, medias = gv.anual_media(d["tiempos"], [None if v is None else v / 100 for v in d["valores"]])
        cons = fecha_consulta("giovanni_gldas_sm0_10_caja_sicc") or {}
        meta = {"fuente": fuente.format("GLDAS_NOAH025_M 2.1, SoilMoi0_10cm_inst", cons.get("fecha")),
                "version": "GLDAS_NOAH025_M 2.1", "fecha_consulta": cons.get("fecha"), "url": cons.get("url")}
        c = _contraste("giovanni_gldas_sm0_10_caja_sicc", "contraste", "caja_sicc", (P0, P1),
                       dict(zip(nuestra["tiempos"], nuestra["valores"])), dict(zip(anios, medias)), "m³/m³",
                       "GLDAS-2.1 por OPeNDAP, media por área sin celdas de agua", meta["fuente"], "", filas_series, meta,
                       investigacion="humedad_gldas_0_10_caja_sicc")
        dif = c["diferencia"]
        c["frase_en"] = (f"NASA Giovanni's area average of GLDAS-2.1 0–10 cm soil moisture over the SICC box vs this "
                         f"app's area-weighted GLDAS series: r = {dif['r']:.3f}, mean difference {dif['media']:+.3f} m³/m³ "
                         f"(Giovanni averages every cell in the box; this app excludes model water cells).")
        out.append(c)
    return out


# ---------------------------------------------------------------- KNMI Climate Explorer (recurso 6)
# Climate Explorer exige verificación humana: una persona descarga la serie «raw data» y la guarda como
# knmi/<producto>_<region>.txt (región caja_sicc o nic). Aquí solo se lee y se compara con data/clima.json.
KNMI_DIR = AQUI / "knmi"
KNMI_PRODUCTOS = {"chirps": "CHIRPS v2.0 (UCSB Climate Hazards Center) vía KNMI Climate Explorer",
                  "gpcc": "GPCC vía KNMI Climate Explorer", "cru": "CRU TS vía KNMI Climate Explorer"}
KNMI_REGIONES = {"caja_sicc": "caja_sicc", "nic": "NIC"}


def contrastes_knmi(filas_series):
    out = []
    if not KNMI_DIR.is_dir():
        return out
    dom = {d["id"]: d for d in _clima()["dominios"]}
    for ruta in sorted(KNMI_DIR.glob("*.txt")):
        producto, _, reg = ruta.stem.partition("_")
        if producto not in KNMI_PRODUCTOS or reg not in KNMI_REGIONES:
            continue
        region = KNMI_REGIONES[reg]
        serie = knmi.leer_serie(ruta.read_text(encoding="utf-8", errors="replace"))
        imerg = dict(zip(dom[region]["anios_validos"], dom[region]["serie_anual_mm"]))
        cons = fecha_consulta(f"knmi_{ruta.stem}") or {}
        meta = {"fuente": KNMI_PRODUCTOS[producto], "version": None, "fecha_consulta": cons.get("fecha"),
                "url": "https://climexp.knmi.nl/start.cgi"}
        c = _contraste(f"knmi_{ruta.stem}", "contraste", region, (P0, P1), imerg, knmi.anual(serie["mensual"]), "mm",
                       "GPM IMERG Final V07B (data/clima.json)", meta["fuente"], "", filas_series, meta,
                       investigacion=f"lluvia_{region}")
        dif, sn, se = c["diferencia"], c["serie_nuestra"], c["serie_externa"]
        if dif.get("r") is None:
            continue
        c["frase_en"] = (f"{KNMI_PRODUCTOS[producto]} over {'the SICC box' if region == 'caja_sicc' else 'Nicaragua'}, "
                         f"2001–2024: r = {dif['r']:.2f} with IMERG, mean difference {dif['media']:+.0f} mm/yr; Sen slopes "
                         f"{se['pendiente']:+.0f} vs {sn['pendiente']:+.0f} mm/decade.")
        out.append(c)
    return out


def _meta_opendap(clave, producto_ver, url_def):
    cons = fecha_consulta(f"opendap_{clave}") or {}
    fecha = cons.get("fecha")
    fuente = f"GES DISC OPeNDAP ({producto_ver}; consulta {fecha})" if fecha else f"GES DISC OPeNDAP ({producto_ver})"
    return {"fuente": fuente, "version": producto_ver, "fecha_consulta": fecha,
            "url": cons.get("url") or url_def}


def _giovanni_mensual_mm_h(clave):
    d = gv.leer_csv_giovanni((OPENDAP_CSV / f"{clave}.csv").read_text(encoding="utf-8"))
    out = {}
    for t, v in zip(d["tiempos"], d["valores"]):
        if v is not None:
            a, m = int(t[:4]), int(t[5:7])
            out[f"{a:04d}-{m:02d}"] = v * gv.horas_mes(a, m)
    return d, out


def _ols_f(meses, vals):
    nt = ntrs_clorofila(meses, vals)
    return nt, nt["mco_mensual"]


def contrastes_giovanni(filas_series):
    cj = _clima()
    dom = {d["id"]: d for d in cj["dominios"]}
    out = []

    # a) IMERG GES DISC OPeNDAP vs clima.json (caja_sicc y NIC)
    nombres = {"caja_sicc": "SICC box (10.7–12.6 N, 86.5–83.6 W)", "NIC": "Nicaragua"}
    for cid, reg, clave in (("opendap_imerg_caja_sicc", "caja_sicc", "imerg_caja_sicc"),
                            ("opendap_imerg_nic", "NIC", "imerg_nic")):
        ruta = OPENDAP_CSV / f"{clave}.csv"
        if not ruta.exists():
            continue
        d = gv.leer_csv_giovanni(ruta.read_text(encoding="utf-8"))
        an_idx, an_val = gv.mensual_tasa_a_anual(d["tiempos"], d["valores"])
        ext = dict(zip(an_idx, an_val))
        imerg = dict(zip(dom[reg]["anios_validos"], dom[reg]["serie_anual_mm"]))
        url_def = gv.url_serie_area(*GIOVANNI_SERIES[clave][:3], bbox=GIOVANNI_SERIES[clave][3],
                                    shape=GIOVANNI_SERIES[clave][4])
        meta = _meta_opendap(clave, "GPM_3IMERGM 07", url_def)
        c = _contraste(cid, "contraste", reg, (P0, P1), imerg, ext, "mm",
                       "GPM IMERG Final V07B (data/clima.json)", meta["fuente"], "", filas_series, meta,
                       investigacion=f"lluvia_{reg}")
        dif, sn, se = c["diferencia"], c["serie_nuestra"], c["serie_externa"]
        ver_txt = f"both '{en(sn['veredicto'])}'" if sn["veredicto"] == se["veredicto"] \
            else f"verdicts differ ({en(se['veredicto'])} vs {en(sn['veredicto'])})"
        nota_mascara = ("polygon includes lakes and uses cell-center cos(lat) weights" if reg == "NIC"
                        else "cos(lat) cell-center box mean vs EPSG:6933 polygon-overlap weights")
        c["frase_en"] = (f"GES DISC OPeNDAP (GPM_3IMERGM 07) area-averaged IMERG vs data/clima.json over "
                         f"{nombres[reg]}, 2001–2024: r = {dif['r']:.3f}, mean difference {dif['media']:+.0f} mm/yr "
                         f"({nota_mascara}); Sen slopes {se['pendiente']:+.0f} vs {sn['pendiente']:+.0f} mm/decade, "
                         f"{ver_txt}.")
        out.append(c)

    # d) Tegucigalpa gauge (GSOM) vs caja IMERG 0.3° (GES DISC OPeNDAP)
    ruta_teg = OPENDAP_CSV / "imerg_tegucigalpa.csv"
    if ruta_teg.exists():
        d_t, im_m = _giovanni_mensual_mm_h("imerg_tegucigalpa")
        an_i, an_v = gv.mensual_tasa_a_anual(d_t["tiempos"], d_t["valores"])
        im_an = dict(zip(an_i, an_v))
        mens = leer_csv(NOAA / "estaciones_mensual.csv")
        teg_m = {r["mes"]: float(r["prcp_mm_gsom"]) for r in mens if r["estacion"] == "HO000078720" and r["prcp_mm_gsom"]}
        teg_an = nc.anual_desde_mensual(teg_m, "suma")
        meta_gsom = _meta("gsom")
        cons_teg = fecha_consulta("opendap_imerg_tegucigalpa") or {}
        f_teg = cons_teg.get("fecha")
        fuente_teg = (f"GES DISC OPeNDAP (GPM_3IMERGM 07, caja 13,95–14,25 N, 87,35–87,05 O; consulta {f_teg})"
                      if f_teg else "GES DISC OPeNDAP (GPM_3IMERGM 07, caja 13,95–14,25 N, 87,35–87,05 O)")
        c = _contraste("noaa_tegucigalpa_lluvia_vs_imerg_caja", "contraste", "Tegucigalpa (0.3° box)", (P0, P1),
                       im_an, teg_an, "mm", fuente_teg, f"{meta_gsom['fuente']} PRCP HO000078720",
                       "", filas_series, meta_gsom)
        com = sorted(m for m in teg_m if m in im_m and P0 <= int(m[:4]) <= P1)
        x = np.array([im_m[m] for m in com])
        y = np.array([teg_m[m] for m in com])
        cx = {k: np.mean([im_m[m] for m in com if int(m[5:7]) == k]) for k in range(1, 13)}
        cy = {k: np.mean([teg_m[m] for m in com if int(m[5:7]) == k]) for k in range(1, 13)}
        ax = np.array([im_m[m] - cx[int(m[5:7])] for m in com])
        ay = np.array([teg_m[m] - cy[int(m[5:7])] for m in com])
        c["mensual"] = {"meses_comunes": len(com), "r_mensual": r4(np.corrcoef(x, y)[0, 1]),
                        "r_anomalias_mensuales": r4(np.corrcoef(ax, ay)[0, 1]),
                        "cociente_medio_estacion_imerg": r4(y.sum() / x.sum())}
        m, dif = c["mensual"], c["diferencia"]
        c["frase_en"] = (f"Tegucigalpa rain gauge (GSOM) vs GES DISC OPeNDAP (GPM_3IMERGM 07) 0.3° pixel box, {m['meses_comunes']} common months "
                         f"in 2001–2024: r = {m['r_mensual']:.2f} (anomalies {m['r_anomalias_mensuales']:.2f}); gauge "
                         f"gets {100 * m['cociente_medio_estacion_imerg']:.0f}% of the 0.3° box mean rainfall "
                         f"(point-vs-box representativeness, consistent with valley rain shadow; {dif['anios_comunes']} complete gauge years in window).")
        out.append(c)

    # b) AIRS3STM 7.0 SurfAirTemp (A+D) over Nicaragua, 2003-2024 (tercera opinión GISTEMP vs POWER)
    ra, rd = OPENDAP_CSV / "airs_tas_a_nic.csv", OPENDAP_CSV / "airs_tas_d_nic.csv"
    if ra.exists() and rd.exists():
        da = gv.leer_csv_giovanni(ra.read_text(encoding="utf-8"))
        dd = gv.leer_csv_giovanni(rd.read_text(encoding="utf-8"))
        def _to_c(parsed):
            vals = [v for v in parsed["valores"] if v is not None]
            off = -273.15 if vals and np.mean(vals) > 150 else 0.0
            return {t[:7]: v + off for t, v in zip(parsed["tiempos"], parsed["valores"]) if v is not None}
        ma, md = _to_c(da), _to_c(dd)
        meses = sorted(set(ma) & set(md))
        vals = [(ma[m] + md[m]) / 2.0 for m in meses]
        nt, mco = _ols_f(meses, vals)
        clim = float(np.mean(vals))
        anom = {a: v for a, v in nt["anomalias_anuales"].items() if 2003 <= a <= P1 and nt["meses_por_anio"][a] >= 9}
        anual = {a: clim + v for a, v in anom.items()}
        _guardar_series(filas_series, "airs_tas_nic", anual, {})
        vn = gv.veredicto_serie(sorted(anual), [anual[a] for a in sorted(anual)], "°C")
        meta = _meta_opendap("airs_tas_a_nic", "AIRS3STM 7.0",
                             gv.url_serie_area(*GIOVANNI_SERIES["airs_tas_a_nic"][:3], shape=SHAPE_NIC))
        f_cons = meta["fecha_consulta"]
        fuente_airs = (f"GES DISC OPeNDAP (AIRS3STM 7.0, SurfAirTemp A+D; consulta {f_cons})"
                       if f_cons else "GES DISC OPeNDAP (AIRS3STM 7.0, SurfAirTemp A+D)")
        fuente_airs_ols = (f"OLS mensual cruda + ANOVA F (GES DISC OPeNDAP, AIRS3STM 7.0; consulta {f_cons})"
                           if f_cons else "OLS mensual cruda + ANOVA F (GES DISC OPeNDAP, AIRS3STM 7.0)")
        gis = _ventana(_gistemp_anual("NIC"), 2003, P1)
        pw = _ventana(_power_region("t2m_media", "NIC"), 2003, P1)
        vg = gv.veredicto_serie(sorted(gis), [gis[a] for a in sorted(gis)], "°C")
        vp = gv.veredicto_serie(sorted(pw), [pw[a] for a in sorted(pw)], "°C")
        rg, _ = _corr(anual, gis)
        rp, _ = _corr(anual, pw)
        sen = vn.get("sen_por_decada")
        coinciden = (vn is not None and (vn.get("mann_kendall") or {}).get("significativo") == mco["significativa_5pct"]
                     and (sen or 0) * (mco["pendiente_por_decada"] or 0) >= 0)
        sig = "significant" if mco["significativa_5pct"] else "not significant"
        p_txt = "p < 0.001" if mco["p_valor_F"] < 0.001 else f"p = {mco['p_valor_F']:.3f}"
        mk_p = (vn.get("mann_kendall") or {}).get("p_valor")
        ic_m = nt["theil_sen_mensual"]["ic95_por_decada"]
        c = {
            "id": "airs_tas_nic", "papel": "tendencia", "region": "NIC",
            "titulo_en": "Surface air temperature (AIRS, Nicaragua)",
            "definicion_en": ("NASA AIRS3STM 7.0 monthly near-surface air temperature over Nicaragua via GES DISC "
                              "OPeNDAP (mean of daytime 13:30 and nighttime 01:30 overpasses, °C), 2003–2024."),
            "periodo": [min(anual), max(anual)],
            "serie_nuestra": {**_serie_resumen(vn, fuente_airs, "°C"),
                              "anios_validos": len(anual), "meses_validos": nt["n_meses"],
                              "climatologia_c": r4(clim)},
            "serie_externa": {"fuente": fuente_airs_ols,
                              "version": meta["version"], "fecha_consulta": meta["fecha_consulta"],
                              "url": meta["url"], "pendiente": mco["pendiente_por_decada"], "unidad": "°C/década",
                              "veredicto": "significativa_p<0.05" if mco["significativa_5pct"] else "no_significativa",
                              "r2": mco["r2"], "p_valor_F": mco["p_valor_F"],
                              "theil_sen_mensual": nt["theil_sen_mensual"]},
            "diferencia": {"media": None, "r": None,
                           "diferencia_pendiente": r4(mco["pendiente_por_decada"] - sen) if sen is not None else None},
            "tercera_opinion": {
                "periodo_comun": [2003, P1],
                "airs_sen_c_decada": sen, "airs_veredicto": vn["veredicto_contrato"],
                "airs_mk_p": mk_p,
                "gistemp_sen_c_decada": vg.get("sen_por_decada"), "gistemp_veredicto": vg.get("veredicto_contrato"),
                "gistemp_mk_p": (vg.get("mann_kendall") or {}).get("p_valor"), "r_airs_gistemp": rg,
                "power_sen_c_decada": vp.get("sen_por_decada"), "power_veredicto": vp.get("veredicto_contrato"),
                "power_mk_p": (vp.get("mann_kendall") or {}).get("p_valor"), "r_airs_power": rp,
                "diferencia_power_menos_airs_c": r4(np.mean([pw[a] - anual[a] for a in sorted(set(pw) & set(anual))])),
            },
            "metodos_coinciden": coinciden, "estado": "ok",
            "frase_en": (f"Fragile warming signal in AIRS3STM 7.0 surface air temperature over Nicaragua (2003–2024, "
                         f"GES DISC OPeNDAP): annual Theil–Sen {sen:+.2f} °C/decade ('{en(vn['veredicto_contrato'])}', "
                         f"MK p = {mk_p:.4f}), whereas monthly OLS is {sig} ({mco['pendiente_por_decada']:+.2f} "
                         f"°C/decade, {p_txt}) and the monthly Theil–Sen 95% CI spans {ic_m[0]:+.2f} to {ic_m[1]:+.2f} "
                         f"°C/decade. Matches GISTEMP in sign and interannual variability (r = {rg:.2f}) at roughly "
                         f"one-third its rate ({sen:+.2f} vs {vg['sen_por_decada']:+.2f} °C/decade; GISTEMP magnitude "
                         f"is not supported); NASA POWER MERRA-2 gives {vp['sen_por_decada']:+.2f} °C/decade "
                         f"('{en(vp['veredicto_contrato'])}', r = {rp:.2f}). Caveat: long-term AIRS instrument "
                         f"stability, orbit drift, and cloudy retrieval sampling."),
        }
        out.append(c)

    # c) OMI OMNO2d v003 (Managua urbana y Chontales rural), 2005-2024
    omi_specs = [
        ("omi_no2_managua", "Managua (urban box)", CAJA_MANAGUA, "Tropospheric NO2 column (Managua, OMI)",
         "OMI OMNO2d v003 cloud-screened tropospheric NO2 column (10^15 molecules/cm^2) over the Managua urban box "
         "(12.05–12.20 N, 86.35–86.15 W), 2005–2024."),
        ("omi_no2_rural", "Chontales (rural box)", CAJA_RURAL, "Tropospheric NO2 column (rural background, OMI)",
         "OMI OMNO2d v003 cloud-screened tropospheric NO2 column (10^15 molecules/cm^2) over the Chontales rural "
         "background box (12.35–12.50 N, 85.10–84.90 W), 2005–2024."),
    ]
    omi_anuales = {}
    omi_cards = []
    for cid, region_en, caja, tit, defn in omi_specs:
        ruta = OPENDAP_CSV / f"{cid}.csv"
        if not ruta.exists():
            continue
        d = gv.leer_csv_giovanni(ruta.read_text(encoding="utf-8"))
        por_mes = {}
        for t, v in zip(d["tiempos"], d["valores"]):
            if v is not None:
                por_mes.setdefault(t[:7], []).append(v * 1e-15)
        meses = sorted(por_mes)
        vals = [float(np.mean(por_mes[m])) for m in meses]
        nt, mco = _ols_f(meses, vals)
        clim = float(np.mean(vals))
        anom = {a: v for a, v in nt["anomalias_anuales"].items() if 2005 <= a <= P1 and nt["meses_por_anio"][a] >= 9}
        anual = {a: clim + v for a, v in anom.items()}
        omi_anuales[cid] = anual
        _guardar_series(filas_series, cid, anual, {})
        vn = gv.veredicto_serie(sorted(anual), [anual[a] for a in sorted(anual)], "1e15 molec cm-2")
        sen = vn.get("sen_por_decada")
        meta = _meta_opendap(cid, "OMNO2d 003",
                             gv.url_serie_area(*GIOVANNI_SERIES[cid][:3], bbox=caja))
        f_cons = meta["fecha_consulta"]
        reg_es = "Managua urbana" if cid == "omi_no2_managua" else "Chontales rural"
        fuente_omi = (f"GES DISC OPeNDAP (OMNO2d 003, {reg_es}; consulta {f_cons})"
                      if f_cons else f"GES DISC OPeNDAP (OMNO2d 003, {reg_es})")
        fuente_omi_ols = (f"OLS mensual cruda + ANOVA F (GES DISC OPeNDAP, OMNO2d 003; consulta {f_cons})"
                          if f_cons else "OLS mensual cruda + ANOVA F (GES DISC OPeNDAP, OMNO2d 003)")
        coinciden = (vn is not None and (vn.get("mann_kendall") or {}).get("significativo") == mco["significativa_5pct"]
                     and (sen or 0) * (mco["pendiente_por_decada"] or 0) >= 0)
        sig = "significant" if mco["significativa_5pct"] else "not significant"
        p_txt = "p < 0.001" if mco["p_valor_F"] < 0.001 else f"p = {mco['p_valor_F']:.2f}"
        c = {
            "id": cid, "papel": "tendencia", "region": region_en, "caja": list(caja),
            "titulo_en": tit, "definicion_en": defn, "periodo": [min(anual), max(anual)],
            "serie_nuestra": {**_serie_resumen(vn, fuente_omi, "1e15 molec cm-2"),
                              "anios_validos": len(anual), "meses_validos": nt["n_meses"],
                              "dias_validos_totales": sum(len(v) for v in por_mes.values()),
                              "mediana_dias_mes": int(np.median([len(v) for v in por_mes.values()])),
                              "media_serie_1e15": r4(clim)},
            "serie_externa": {"fuente": fuente_omi_ols,
                              "version": meta["version"], "fecha_consulta": meta["fecha_consulta"],
                              "url": meta["url"], "pendiente": mco["pendiente_por_decada"],
                              "unidad": "1e15 molec cm-2/década",
                              "veredicto": "significativa_p<0.05" if mco["significativa_5pct"] else "no_significativa",
                              "r2": mco["r2"], "p_valor_F": mco["p_valor_F"],
                              "theil_sen_mensual": nt["theil_sen_mensual"]},
            "diferencia": {"media": None, "r": None,
                           "diferencia_pendiente": r4(mco["pendiente_por_decada"] - sen) if sen is not None else None},
            "metodos_coinciden": coinciden, "estado": "ok",
            "frase_en": (f"OMI tropospheric NO2 over {region_en} ({min(anual)}–{max(anual)}, mean {clim:.2f} x 10^15 "
                         f"molec/cm^2): monthly OLS {mco['pendiente_por_decada']:+.3f} ({sig}, {p_txt}); "
                         f"annual Theil–Sen {sen:+.3f} x 10^15 molec/cm^2 per decade, verdict "
                         f"'{en(vn['veredicto_contrato'])}'."),
        }
        omi_cards.append(c)
    if len(omi_cards) == 2:
        um, ur = omi_anuales["omi_no2_managua"], omi_anuales["omi_no2_rural"]
        com = sorted(set(um) & set(ur))
        r_ur, n_ur = _corr(um, ur)
        mm, mr = float(np.mean([um[a] for a in com])), float(np.mean([ur[a] for a in com]))
        extra_ur = {"media_managua_1e15": r4(mm), "media_rural_1e15": r4(mr), "diferencia_1e15": r4(mm - mr),
                    "cociente_urbano_rural": r4(mm / mr) if mr else None, "r_anual": r_ur, "anios_comunes": n_ur}
        for c in omi_cards:
            c["contraste_urbano_rural"] = extra_ur
            c["frase_en"] += f" Managua averages {mm:.2f} vs {mr:.2f} x 10^15 molec/cm^2 in Chontales rural box."
    out.extend(omi_cards)
    return out


def contrastes_bloqueados():
    """Contrastes que dependen de Giovanni / GES DISC cuando no hay acceso (o sus CSV aún no existen)."""
    bloq = json.loads(BLOQUEOS.read_text(encoding="utf-8")) if BLOQUEOS.exists() else {}
    out = []

    def motivo(*claves):
        for k in claves:
            if k in bloq:
                b = bloq[k]
                return f"{b.get('motivo', '')} Petición: {b.get('url', '')} (HTTP {b.get('http', '?')}, {b['fecha']})."
        return "pendiente de ejecutar el paso opendap"

    g = {"fuente": "GES DISC OPeNDAP (GPM_3IMERGM 07)", "version": "GPM_3IMERGM 07", "fecha_consulta": None}
    for cid, region, clave in (("opendap_imerg_caja_sicc", "caja_sicc", "imerg_caja_sicc"),
                               ("opendap_imerg_nic", "NIC", "imerg_nic")):
        if (OPENDAP_CSV / f"{clave}.csv").exists():
            continue
        out.append(_bloqueado(cid, "contraste", region, (P0, P1), "GPM IMERG Final V07B (data/clima.json)",
                              g["fuente"], "mm", motivo(f"giovanni_{clave}"),
                              f"GES DISC OPeNDAP area-averaged IMERG for {region}: blocked.",
                              {**g, "url": gv.url_serie_area(*GIOVANNI_SERIES[clave][:3], bbox=GIOVANNI_SERIES[clave][3],
                                                             shape=GIOVANNI_SERIES[clave][4])}))
    if not (OPENDAP_CSV / "imerg_tegucigalpa.csv").exists():
        out.append(_bloqueado("noaa_tegucigalpa_lluvia_vs_imerg_caja", "contraste", "Tegucigalpa (caja 0,3°)", (P0, P1),
                              "GES DISC OPeNDAP (GPM_3IMERGM 07, caja 13,95–14,25 N, 87,35–87,05 O)", "NOAA NCEI GSOM PRCP",
                              "mm", motivo("giovanni_imerg_tegucigalpa"),
                              "Tegucigalpa gauge vs IMERG pixel box: blocked.",
                              _meta("gsom")))
    if not (OPENDAP_CSV / "airs_tas_a_nic.csv").exists():
        out.append(_bloqueado("airs_tas_nic", "tendencia", "NIC", (2003, P1), "GES DISC OPeNDAP (AIRS3STM 7.0, SurfAirTemp A+D)",
                              "GISTEMP v4 y MERRA-2 (data/fenomenos)", "°C", motivo("giovanni_airs_tas_a_nic"),
                              "AIRS surface air temperature over Nicaragua: blocked.",
                              {"fuente": "GISTEMP v4 / NASA POWER (MERRA-2)", "version": None, "fecha_consulta": None,
                               "url": None}))
    if not (OPENDAP_CSV / "omi_no2_managua.csv").exists():
        out.append(_bloqueado("omi_no2_managua", "tendencia", "Managua (urban box)", (2005, P1),
                              "GES DISC OPeNDAP (OMNO2d 003)", "OLS mensual cruda + ANOVA F",
                              "1e15 molec cm-2", motivo("giovanni_omi_no2_managua"),
                              "OMI tropospheric NO2 over Managua: blocked.",
                              {"fuente": "OMNO2d 003, Managua urban box 12.05–12.20 N, 86.35–86.15 W",
                               "version": "OMNO2d 003", "fecha_consulta": None, "url": None}))
    if not (OPENDAP_CSV / "omi_no2_rural.csv").exists():
        out.append(_bloqueado("omi_no2_rural", "tendencia", "Chontales (rural box)", (2005, P1),
                              "GES DISC OPeNDAP (OMNO2d 003)", "OLS mensual cruda + ANOVA F",
                              "1e15 molec cm-2", motivo("giovanni_omi_no2_rural"),
                              "OMI tropospheric NO2 over rural Chontales: blocked.",
                              {"fuente": "OMNO2d 003, Chontales rural box 12.35–12.50 N, 85.10–84.90 W",
                               "version": "OMNO2d 003", "fecha_consulta": None, "url": None}))
    return out


def paso_resumen():
    filas_series = []
    contrastes = contrastes_lluvia(filas_series) + contrastes_estaciones(filas_series) + \
        contrastes_clorofila(filas_series) + contrastes_giovanni(filas_series) +         contrastes_giovanni_nube(filas_series) + contrastes_knmi(filas_series) + contrastes_bloqueados()
    escribir_csv(AQUI / "series_anuales.csv", ["contraste", "serie", "anio", "valor"], filas_series)
    bloq = json.loads(BLOQUEOS.read_text(encoding="utf-8")) if BLOQUEOS.exists() else {}
    doc = {"esquema": "nasa-challenge/contrastes", "version": "1.0.0", "generado": HOY,
           "metodo": ("Pendientes de Theil–Sen por década; veredicto del contrato 1.0.0 (tendencia.py: tres intervalos "
                      "del 95 %) y veredicto robusto (tendencia_robusta: además Mann–Kendall modificado). diferencia.media "
                      "= externa − nuestra en los años comunes; r de Pearson anual."),
           "bloqueos": bloq, "contrastes": contrastes}
    (AQUI / "resumen_contrastes.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                                                  encoding="utf-8", newline="\n")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for c in contrastes:
        print(f"{c['id']:42s} {c['estado']:9s} {c.get('frase_en', '')[:150]}")


if __name__ == "__main__":
    PASOS = {"noaa": paso_noaa, "knmi": paso_knmi, "cru": paso_cru, "gpcc": paso_gpcc, "clorofila": paso_clorofila,
             "giovanni": paso_giovanni, "opendap": paso_giovanni_opendap, "nube": paso_giovanni_nube,
             "resumen": paso_resumen}
    for p in sys.argv[1:] or ["resumen"]:
        PASOS[p]()
