"""Estaciones de NOAA NCEI: GSOM (Global Summary of the Month) y GHCN-Daily, para contraste.

Dos vías de acceso:

- **CDO Web Services v2** (`https://www.ncei.noaa.gov/cdo-web/api/v2/...`): requiere el token gratuito en la
  cabecera `token`. Se lee de la variable de entorno `NOAA_CDO_TOKEN`; nunca se escribe ni se imprime. Sin
  token la API responde 400. `estaciones_cdo` usa el endpoint `/stations` con `extent`.
- **NCEI Access Data Service v1** (`https://www.ncei.noaa.gov/access/services/data/v1`) y su buscador
  (`/access/services/search/v1/data`): sirven los mismos conjunto `global-summary-of-the-month` y
  `daily-summaries` (GHCN-Daily) sin token. Es la vía usada cuando falta `NOAA_CDO_TOKEN`.

Los parsers (`leer_csv_ncei`, `mensual_desde_diario`, `anual_desde_mensual`) no usan red y se prueban con
textos sintéticos.
"""
import calendar
import csv
import io
import json
import math
import os
import urllib.error
import urllib.parse
import urllib.request

CDO = "https://www.ncei.noaa.gov/cdo-web/api/v2/"
ACCESO = "https://www.ncei.noaa.gov/access/services/data/v1"
BUSQUEDA = "https://www.ncei.noaa.gov/access/services/search/v1/data"

# Estaciones pedidas (ids GHCN; los mismos en GSOM y GHCN-Daily). Encontradas con el buscador de NCEI
# (bbox de Nicaragua y Honduras) el 13-11-2026.
ESTACIONES = {
    "NUM00078741": "Managua International",
    "NU000069034": "Juigalpa",
    "HO000078720": "Tegucigalpa",
    "NU000055002": "Hacienda San Francisco",
    "NU000055029": "Guasimón",
    "NU000055016": "San Dionisio",
}


def token_cdo():
    """Token de CDO desde el entorno, o None. No se registra en ninguna parte."""
    t = os.environ.get("NOAA_CDO_TOKEN", "").strip()
    return t or None


def estaciones_cdo(extent, datasetid="GSOM", limite=1000):
    """Estaciones de CDO v2 dentro de `extent` = (sur, oeste, norte, este). Requiere NOAA_CDO_TOKEN.

    Devuelve (lista, None) o (None, motivo) con la URL pedida y el código HTTP si falla.
    """
    q = {"datasetid": datasetid, "extent": ",".join(f"{v:g}" for v in extent), "limit": limite}
    url = CDO + "stations?" + urllib.parse.urlencode(q)
    tok = token_cdo()
    cab = {"token": tok} if tok else {}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=cab), timeout=120) as r:
            return json.load(r).get("results", []), None
    except urllib.error.HTTPError as e:
        return None, {"url": url, "http": e.code, "token_en_entorno": tok is not None}


def url_busqueda(dataset, bbox_nwse, limite=1000):
    """URL del buscador NCEI. bbox_nwse = (norte, oeste, sur, este), el orden que pide el servicio."""
    q = {"dataset": dataset, "bbox": ",".join(f"{v:g}" for v in bbox_nwse), "limit": limite, "offset": 0}
    return BUSQUEDA + "?" + urllib.parse.urlencode(q)


def leer_busqueda(texto):
    """JSON del buscador NCEI → [{id, nombre, inicio, fin}]."""
    d = json.loads(texto)
    out = []
    for r in d.get("results", []):
        for s in r.get("stations", []):
            out.append({"id": s.get("id"), "nombre": s.get("name"), "inicio": (r.get("startDate") or "")[:10],
                        "fin": (r.get("endDate") or "")[:10]})
    return out


def url_datos(dataset, estaciones, inicio, fin, tipos=("PRCP", "TAVG", "TMAX", "TMIN")):
    q = {"dataset": dataset, "stations": ",".join(estaciones), "startDate": inicio, "endDate": fin,
         "dataTypes": ",".join(tipos), "format": "csv", "units": "metric", "includeAttributes": "false",
         "includeStationName": "false", "includeStationLocation": "1"}
    return ACCESO + "?" + urllib.parse.urlencode(q)


def descargar(url, timeout=600):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "nasa-challenge-clima/1.0"}),
                                timeout=timeout) as r:
        return r.read().decode("utf-8")


def _num(v):
    v = (v or "").strip()
    if not v:
        return None
    try:
        x = float(v)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def leer_csv_ncei(texto, variables=("PRCP", "TAVG", "TMAX", "TMIN")):
    """CSV del servicio v1 → {estacion: {fecha: {variable: valor|None}}} (fecha «AAAA-MM» o «AAAA-MM-DD»)."""
    out = {}
    for fila in csv.DictReader(io.StringIO(texto.replace("\r\n", "\n"))):
        st = fila["STATION"].strip()
        out.setdefault(st, {})[fila["DATE"].strip()] = {v: _num(fila.get(v)) for v in variables}
    return out


def mensual_desde_diario(diario, variable, como="media", min_dias=20):
    """{fecha diaria: {var: valor}} → {«AAAA-MM»: valor}. Un mes vale si tiene al menos `min_dias` datos.

    `como` = "media" (temperatura) o "suma" (lluvia; exige el mes completo, sin días faltantes, porque un
    total con huecos subestima la lluvia).
    """
    por = {}
    for f, vals in diario.items():
        v = vals.get(variable)
        if v is not None:
            por.setdefault(f[:7], []).append(v)
    out = {}
    for mes, xs in por.items():
        a, m = int(mes[:4]), int(mes[5:7])
        dias = calendar.monthrange(a, m)[1]
        if como == "suma":
            if len(xs) == dias:
                out[mes] = float(sum(xs))
        elif len(xs) >= min_dias:
            out[mes] = float(sum(xs) / len(xs))
    return dict(sorted(out.items()))


def anual_desde_mensual(mensual, como="media", meses=range(1, 13)):
    """{«AAAA-MM»: valor} → {año: valor} solo con todos los meses pedidos presentes."""
    meses = list(meses)
    por = {}
    for t, v in mensual.items():
        if v is not None and int(t[5:7]) in meses:
            por.setdefault(int(t[:4]), {})[int(t[5:7])] = v
    out = {}
    for a, d in sorted(por.items()):
        if len(d) == len(meses):
            out[a] = float(sum(d.values()) / (len(d) if como == "media" else 1))
    return out


def anomalias(anual, base):
    """Resta la media de los años `base` (iterable) presentes. Devuelve {año: anomalía}."""
    ref = [anual[a] for a in base if a in anual]
    if not ref:
        raise ValueError("ningún año del período base tiene dato")
    m = sum(ref) / len(ref)
    return {a: v - m for a, v in anual.items()}
