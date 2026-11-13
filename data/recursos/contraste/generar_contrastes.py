"""Genera los contrastes externos de data/recursos/contraste/ (agente 2 · contrastes).

Pasos (cada uno escribe sus CSV en esta carpeta; los archivos crudos van a backend/.cache/contraste, que no
se versiona):

    python data/recursos/contraste/generar_contrastes.py noaa      # NCEI GSOM + GHCN-Daily (sin token)
    python data/recursos/contraste/generar_contrastes.py cru       # CRU TS 4.10 (UEA), lluvia mensual
    python data/recursos/contraste/generar_contrastes.py gpcc      # GPCC 0,5° de PSL (OPeNDAP)
    python data/recursos/contraste/generar_contrastes.py giovanni  # IMERG, AIRS, OMI NO2 (Giovanni)
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
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ / "backend"))

from clima_nic.fuentes import giovanni as gv  # noqa: E402
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

# Cajas de 0,5° × 0,5° frente a las desembocaduras (lado mar) y el golfo de Fonseca. (oeste, sur, este, norte)
CAJAS_CHL = {
    "golfo_fonseca": (-87.9, 12.9, -87.3, 13.5),
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
    hechos = {(r["caja"], r["mes"]) for r in leer_csv(CHL_CSV)} if CHL_CSV.exists() else set()
    filas = [list(r.values()) for r in leer_csv(CHL_CSV)] if CHL_CSV.exists() else []
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
                filas.append([k, f"{a:04d}-{m:02d}", r4(media) if math.isfinite(media) else "", r4(frac), n])
            filas.sort(key=lambda f: (f[0], f[1]))
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
GIOVANNI_CSV = AQUI / "giovanni"


def paso_giovanni(claves=None):
    op, motivo = gv.iniciar_sesion()
    for k in claves or GIOVANNI_SERIES:
        var, i, f, bbox, shape = GIOVANNI_SERIES[k]
        url = gv.url_serie_area(var, i, f, bbox=bbox, shape=shape)
        destino = GIOVANNI_CSV / f"{k}.csv"
        if destino.exists():
            continue
        if op is None:
            anotar_bloqueo(f"giovanni_{k}", url=url, http=302,
                           motivo=f"Earthdata Login: {motivo}. Giovanni responde «Giovanni now requires a login for "
                                  "data access» y el flujo ArAvTs falla.")
            continue
        try:
            _, urls = gv.ejecutar(op, url)
            csvs = [u for u in urls if u.lower().endswith(".csv")] or urls
            texto = op.open(csvs[0] if csvs[0].startswith("http") else gv.GIOVANNI + csvs[0], timeout=600).read()
            gv.leer_csv_giovanni(texto.decode("utf-8"))  # valida el formato antes de guardar
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(texto.replace(b"\r\n", b"\n"))
            quitar_bloqueo(f"giovanni_{k}")
            anotar_consulta(f"giovanni_{k}", url=url)
        except Exception as e:  # noqa: BLE001
            anotar_bloqueo(f"giovanni_{k}", url=url, motivo=str(e)[:400])


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
    nombres = {"golfo_fonseca": "Gulf of Fonseca", "rio_coco": "Coco River mouth",
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
        c = {"id": cid, "papel": "tendencia", "region": nombres[caja], "caja": list(CAJAS_CHL[caja]),
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
             "metodos_coinciden": coinciden, "estado": "ok" if v else "bloqueado"}
        if not v:
            c["motivo"] = "menos de 10 años con datos suficientes"
        sig = "significant" if mco["significativa_5pct"] else "not significant"
        c["frase_en"] = (f"MODIS-Aqua chlorophyll-a, {nombres[caja]} ({c['periodo'][0]}–{c['periodo'][1]}): OLS on raw "
                         f"monthly data {mco['pendiente_por_decada']:+.2f} mg/m³ per decade ({sig}, p = "
                         f"{mco['p_valor_F']:.2f}); Theil–Sen on deseasonalized annual means {sen:+.2f}, verdict "
                         f"'{en(c['serie_nuestra']['veredicto'])}'.") if v else \
            f"MODIS-Aqua chlorophyll-a, {nombres[caja]}: not enough cloud-free months for a trend."
        out.append(c)
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
        return "pendiente de ejecutar el paso giovanni"

    g = {"fuente": "NASA Giovanni, Time Series Area-Averaged", "version": "GPM_3IMERGM V07B", "fecha_consulta": None}
    for cid, region, clave in (("giovanni_imerg_caja_sicc", "caja_sicc", "imerg_caja_sicc"),
                               ("giovanni_imerg_nic", "NIC", "imerg_nic")):
        if (GIOVANNI_CSV / f"{clave}.csv").exists():
            continue
        out.append(_bloqueado(cid, "contraste", region, (P0, P1), "GPM IMERG Final V07B (data/clima.json)",
                              g["fuente"], "mm", motivo(f"giovanni_{clave}"),
                              f"Giovanni area-averaged IMERG for {region}: blocked (Earthdata application not authorized).",
                              {**g, "url": gv.url_serie_area(*GIOVANNI_SERIES[clave][:3], bbox=GIOVANNI_SERIES[clave][3],
                                                             shape=GIOVANNI_SERIES[clave][4])}))
    if not (GIOVANNI_CSV / "imerg_tegucigalpa.csv").exists():
        out.append(_bloqueado("noaa_tegucigalpa_lluvia_vs_imerg_caja", "contraste", "Tegucigalpa (caja 0,3°)", (P0, P1),
                              "GPM IMERG V07B, caja 13.95–14.25 N, 87.35–87.05 O (Giovanni)", "NOAA NCEI GSOM PRCP",
                              "mm", motivo("giovanni_imerg_tegucigalpa"),
                              "Tegucigalpa gauge vs IMERG pixel box: blocked (Earthdata application not authorized).",
                              _meta("gsom")))
    if not (GIOVANNI_CSV / "airs_tas_a_nic.csv").exists():
        out.append(_bloqueado("airs_tas_nic", "tendencia", "NIC", (2003, P1), "AIRS3STM v7 SurfAirTemp (A+D)",
                              "GISTEMP v4 y MERRA-2 (data/fenomenos)", "°C", motivo("giovanni_airs_tas_a_nic"),
                              "AIRS surface air temperature over Nicaragua: blocked (Earthdata application not authorized).",
                              {"fuente": "GISTEMP v4 / NASA POWER (MERRA-2)", "version": None, "fecha_consulta": None,
                               "url": None}))
    if not (GIOVANNI_CSV / "omi_no2_managua.csv").exists():
        out.append(_bloqueado("omi_no2_managua", "tendencia", "Managua (12.05–12.20 N, 86.35–86.15 O)", (2005, P1),
                              "OMI OMNO2d v003 ColumnAmountNO2TropCloudScreened", "caja rural de fondo (OMNO2d)",
                              "molec cm-2", motivo("giovanni_omi_no2_managua"),
                              "OMI tropospheric NO2 over Managua: blocked (Earthdata application not authorized).",
                              {"fuente": "OMNO2d v003, caja rural 12.35–12.50 N, 85.10–84.90 O", "version": "003",
                               "fecha_consulta": None, "url": None}))
    return out


def paso_resumen():
    filas_series = []
    contrastes = contrastes_lluvia(filas_series) + contrastes_estaciones(filas_series) + \
        contrastes_clorofila(filas_series) + contrastes_bloqueados()
    escribir_csv(AQUI / "series_anuales.csv", ["contraste", "serie", "anio", "valor"], filas_series)
    bloq = json.loads(BLOQUEOS.read_text(encoding="utf-8")) if BLOQUEOS.exists() else {}
    doc = {"esquema": "nasa-challenge/contrastes", "version": "1.0.0", "generado": HOY,
           "metodo": ("Pendientes de Theil–Sen por década; veredicto del contrato 1.0.0 (tendencia.py: tres intervalos "
                      "del 95 %) y veredicto robusto (tendencia_robusta: además Mann–Kendall modificado). diferencia.media "
                      "= externa − nuestra en los años comunes; r de Pearson anual."),
           "bloqueos": bloq, "contrastes": contrastes}
    (AQUI / "resumen_contrastes.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                                                  encoding="utf-8", newline="\n")
    for c in contrastes:
        print(f"{c['id']:42s} {c['estado']:9s} {c.get('frase_en', '')[:150]}")


if __name__ == "__main__":
    PASOS = {"noaa": paso_noaa, "knmi": paso_knmi, "cru": paso_cru, "gpcc": paso_gpcc, "clorofila": paso_clorofila,
             "giovanni": paso_giovanni, "resumen": paso_resumen}
    for p in sys.argv[1:] or ["resumen"]:
        PASOS[p]()
