"""Contrastes con NASA Giovanni y su equivalente por OPeNDAP, y utilidades de comparación de series.

Giovanni (https://giovanni.gsfc.nasa.gov) calcula en el servidor series «Time Series, Area-Averaged»
(servicio `ArAvTs`). El cliente web usa `daac-bin/service_manager.pl`: una petición lanza el flujo y devuelve
los identificadores de sesión, conjunto y resultado; después se consulta el estado hasta el 100 % y se baja
el CSV. Desde 2024 Giovanni exige sesión de Earthdata Login: la cuenta tiene que haber autorizado la
aplicación de Giovanni (client_id `GIOVANNI_CLIENT_ID`) en urs.earthdata.nasa.gov. Si no lo está, URS
responde «Pre authorization required for this application» y el flujo falla con «Giovanni now requires a
login for data access». `iniciar_sesion` hace ese inicio de sesión OAuth con las credenciales del `.netrc`
(sin imprimirlas ni guardarlas) y devuelve el motivo si no se puede.

Cuando Giovanni no está disponible, `opendap_ascii` + `media_caja_coslat` reproducen su promedio por área
(pesos coseno de la latitud sobre las celdas cuyo centro cae en la caja) a partir de los mismos archivos.

Las utilidades de comparación (`comparar_anual`, `veredicto_serie`) reutilizan los métodos del backend
(`tendencia_robusta.analizar`: mínimos cuadrados con gl ajustados, HAC, Theil–Sen, Mann–Kendall
modificado), de modo que las cifras sean comparables con data/clima.json.

Ningún secreto se escribe en disco ni en la salida: el abridor de `earthdata.abridor()` lee el `.netrc`.
"""
import calendar
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request

import numpy as np

GIOVANNI = "https://giovanni.gsfc.nasa.gov/giovanni/"
SERVICIO = GIOVANNI + "daac-bin/service_manager.pl"
GIOVANNI_CLIENT_ID = "e2WVk8Pw6weeLUKZYOxvTQ"
URS = "https://urs.earthdata.nasa.gov"


class GiovanniNoDisponible(RuntimeError):
    """Giovanni no pudo atender la petición (sesión, autorización o fallo del flujo)."""


# ---------------------------------------------------------------- Earthdata: abridor con autenticación preventiva

def abridor_urs():
    """Abridor que envía Basic auth solo a urs.earthdata.nasa.gov, también tras redirecciones.

    `earthdata.abridor()` responde únicamente a desafíos 401; algunos servidores (OB.DAAC getfile) redirigen a
    URS sin `app_type=401` y reciben la página de inicio de sesión. Este abridor añade la cabecera a toda
    petición cuyo destino sea URS (nunca a otros hosts) y conserva las cookies de sesión.
    """
    import base64
    import http.cookiejar
    import netrc

    from .base import RequiereEarthdata
    from .earthdata import URS as URS_HOST, ruta_netrc
    ruta = ruta_netrc()
    cred = netrc.netrc(str(ruta)).authenticators(URS_HOST) if ruta else None
    if not cred:
        raise RequiereEarthdata("Configure .netrc con urs.earthdata.nasa.gov.")
    valor = "Basic " + base64.b64encode(f"{cred[0]}:{cred[2]}".encode()).decode()

    class _Urs(urllib.request.BaseHandler):
        handler_order = 100

        def https_request(self, req):
            if urllib.parse.urlsplit(req.full_url).hostname == URS_HOST:
                req.add_unredirected_header("Authorization", valor)
            else:
                req.remove_header("Authorization")
            return req

    return urllib.request.build_opener(_Urs(), urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


# ---------------------------------------------------------------- Giovanni: sesión y servicio

def iniciar_sesion(abridor=None):
    """Inicia sesión en Giovanni vía OAuth de Earthdata. Devuelve (abridor, None) o (None, motivo).

    El abridor resultante lleva las cookies de sesión de Giovanni. No reintenta ni autoriza nada en la
    cuenta: si la aplicación no está autorizada, devuelve el motivo y la URL de autorización.
    """
    import base64
    import http.cookiejar
    import netrc

    from .earthdata import URS as URS_HOST, ruta_netrc
    ruta = ruta_netrc()
    if ruta is None:
        return None, "no hay .netrc con urs.earthdata.nasa.gov"
    cred = netrc.netrc(str(ruta)).authenticators(URS_HOST)
    if not cred:
        return None, "el .netrc no tiene entrada para urs.earthdata.nasa.gov"
    cabecera = {"Authorization": "Basic " + base64.b64encode(f"{cred[0]}:{cred[2]}".encode()).decode()}

    class _SinRedireccion(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    jar = http.cookiejar.CookieJar()
    sin_red = urllib.request.build_opener(_SinRedireccion(), urllib.request.HTTPCookieProcessor(jar))
    cfg = json.load(urllib.request.urlopen(GIOVANNI + "daac-bin/getGiovanniConfig.pl?cfg=EARTHDATA_LOGIN",
                                           timeout=60))["EARTHDATA_LOGIN"]
    autorizar = (f"{URS}/oauth/authorize?response_type=code&client_id={cfg['clientId']}"
                 f"&redirect_uri={cfg['redirectURI']}")
    try:
        sin_red.open(urllib.request.Request(autorizar, headers=cabecera), timeout=60)
        return None, "URS no redirigió a Giovanni"
    except urllib.error.HTTPError as e:
        destino = e.headers.get("Location", "")
    q = urllib.parse.parse_qs(urllib.parse.urlsplit(destino).query)
    if "code" not in q:
        motivo = q.get("error_msg", q.get("error", ["sin código OAuth"]))[0]
        return None, f"{motivo} ({URS}/approve_app?client_id={cfg['clientId']})"
    abridor = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    perfil = json.load(abridor.open(GIOVANNI + "daac-bin/earthdataLogin.pl?code=" + q["code"][0], timeout=60))
    if not isinstance(perfil, dict) or not perfil.get("uid"):
        return None, "earthdataLogin.pl no devolvió perfil"
    return abridor, None


def url_serie_area(data, inicio, fin, bbox=None, shape=None, servicio="ArAvTs"):
    """URL de lanzamiento de una serie promediada por área. bbox = (oeste, sur, este, norte)."""
    q = {"service": servicio, "starttime": f"{inicio}T00:00:00Z", "endtime": f"{fin}T23:59:59Z", "data": data}
    if bbox is not None:
        q["bbox"] = ",".join(f"{v:g}" for v in bbox)
    if shape is not None:
        q["shape"] = shape
    q.update(portal="GIOVANNI", format="json")
    return SERVICIO + "?" + urllib.parse.urlencode(q)


def _resultado(respuesta):
    s = respuesta["session"]
    rs = s["resultset"][0]
    return s["id"], rs["id"], rs["result"][0]


def estado_resultado(resultado):
    """(código, porcentaje, mensaje sin HTML, urls de datos) de un elemento `result` de Giovanni."""
    st = resultado["status"][0]
    codigo = int(st["code"][0].get("value", "0"))
    pct = int(float(st["percentComplete"][0].get("value", "0") or 0))
    msj = re.sub(r"<[^>]+>", " ", st["message"][0].get("value", "")).strip()
    urls = []
    for d in resultado.get("data", []):
        for f in d.get("dataFile", []) if isinstance(d, dict) else []:
            for u in f.get("dataUrl", []):
                if u.get("value"):
                    urls.append(u["value"])
    return codigo, pct, re.sub(r"\s+", " ", msj), urls


def ejecutar(abridor, url, espera=5, max_espera=3600):
    """Lanza un servicio de Giovanni y espera el resultado. Devuelve (ids, urls de datos)."""
    r = json.load(abridor.open(url, timeout=180))
    sid, rsid, res = _resultado(r)
    t0 = time.time()
    while True:
        codigo, pct, msj, urls = estado_resultado(res)
        if codigo not in (0,) and pct < 100:
            raise GiovanniNoDisponible(f"Giovanni falló ({msj}); petición: {url}")
        if pct >= 100:
            return (sid, rsid, res["id"]), urls
        if time.time() - t0 > max_espera:
            raise GiovanniNoDisponible(f"tiempo agotado esperando a Giovanni; petición: {url}")
        time.sleep(espera)
        q = urllib.parse.urlencode({"session": sid, "resultset": rsid, "result": res["id"],
                                    "portal": "GIOVANNI", "format": "json"})
        _, _, res = _resultado(json.load(abridor.open(SERVICIO + "?" + q, timeout=180)))


def leer_csv_giovanni(texto):
    """CSV de «Time Series, Area-Averaged» → {"meta": {...}, "tiempos": [...], "valores": [...]}.

    Formato: líneas de cabecera «Clave:,valor», una línea en blanco y luego «time,<variable>». Los valores
    iguales al «Fill Value» o no numéricos se devuelven como None.
    """
    meta, tiempos, valores = {}, [], []
    lineas = texto.replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(lineas) and not lineas[i].lower().startswith("time,"):
        ln = lineas[i]
        if ":," in ln:
            k, v = ln.split(":,", 1)
            meta[k.strip()] = v.strip().strip('"')
        i += 1
    if i == len(lineas):
        raise ValueError("CSV de Giovanni sin fila «time,…»")
    meta["columna"] = lineas[i].split(",", 1)[1].strip()
    relleno = None
    for k, v in meta.items():
        if k.lower().startswith("fill value"):
            try:
                relleno = float(v)
            except ValueError:
                pass
    for ln in lineas[i + 1:]:
        if not ln.strip():
            continue
        t, v = ln.split(",", 1)
        try:
            x = float(v)
        except ValueError:
            x = None
        if x is not None and (not math.isfinite(x) or (relleno is not None and abs(x - relleno) < 1e-6)):
            x = None
        tiempos.append(t.strip())
        valores.append(x)
    return {"meta": meta, "tiempos": tiempos, "valores": valores}


# ---------------------------------------------------------------- OPeNDAP (DAP2 ASCII), equivalente local

def parsear_dap2_ascii(texto):
    """Respuesta `.ascii` de Hyrax/THREDDS (DAP2) → {nombre: np.ndarray}.

    Entiende arreglos «var[d1][d2]...» seguidos de filas «[i][j], v1, v2, ...» y vectores
    «var[n]» seguidos de una fila «v1, v2, ...». Los mapas de un Grid (`var.lat`) se devuelven con su nombre
    corto (`lat`).
    """
    partes = texto.split("---------------------------------------------", 1)
    cuerpo = partes[1] if len(partes) == 2 else texto
    out, nombre, forma, filas = {}, None, None, []

    def cerrar():
        if nombre is None:
            return
        plano = np.array([float(x) for f in filas for x in f], float)
        out[nombre.split(".")[-1]] = plano.reshape(forma) if forma and np.prod(forma) == plano.size else plano

    for ln in cuerpo.replace("\r\n", "\n").split("\n"):
        s = ln.strip()
        if not s:
            continue
        m = re.match(r"^([A-Za-z_][\w./-]*)((?:\[\d+\])+)\s*$", s)
        if m:
            cerrar()
            nombre = m.group(1)
            forma = [int(x) for x in re.findall(r"\[(\d+)\]", m.group(2))]
            filas = []
            continue
        if nombre is None:
            continue
        fila = re.sub(r"^(\[\d+\])+,\s*", "", s)
        filas.append([x for x in (v.strip() for v in fila.split(",")) if x])
    cerrar()
    return out


def opendap_ascii(url, restriccion, abridor=None, intentos=6, timeout=300):
    """GET `<url>.ascii?<restriccion>` con reintentos (429/5xx). Devuelve el texto."""
    pedir = abridor.open if abridor else urllib.request.urlopen
    u = f"{url}.ascii?{restriccion}"
    espera = 5.0
    for k in range(intentos):
        try:
            with pedir(urllib.request.Request(u, headers={"User-Agent": "nasa-challenge-clima/1.0"}),
                       timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or k == intentos - 1:
                raise RuntimeError(f"{u}: HTTP {e.code}") from e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if k == intentos - 1:
                raise RuntimeError(f"{u}: {e}") from e
        time.sleep(espera)
        espera *= 2
    raise RuntimeError(u)


def indices_rango(centros, minimo, maximo):
    """Primer y último índice de los centros dentro de [minimo, maximo] (centros ascendentes o descendentes)."""
    c = np.asarray(centros, float)
    i = np.where((c >= minimo) & (c <= maximo))[0]
    if i.size == 0:
        raise ValueError("ningún centro de celda cae en el rango")
    return int(i.min()), int(i.max())


def media_caja_coslat(lat, lon, campo, bbox):
    """Promedio por área al estilo Giovanni: celdas con centro dentro de la caja, peso cos(lat).

    campo con forma (..., lat, lon). Ignora NaN renormalizando pesos. bbox = (oeste, sur, este, norte).
    Devuelve (media, fracción de peso con dato).
    """
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    o, s, e, n = bbox
    ml = (lat >= s) & (lat <= n)
    mo = (lon >= o) & (lon <= e)
    sub = np.asarray(campo, float)[..., ml, :][..., mo]
    w = np.cos(np.radians(lat[ml]))[:, None] * np.ones(mo.sum())[None, :]
    ok = np.isfinite(sub)
    peso = np.where(ok, w, 0.0)
    tot = peso.sum(axis=(-2, -1))
    media = np.where(tot > 0, np.nansum(np.where(ok, sub, 0.0) * peso, axis=(-2, -1)) / np.where(tot > 0, tot, 1),
                     np.nan)
    return media, tot / w.sum()


def horas_mes(anio, mes):
    return 24 * calendar.monthrange(int(anio), int(mes))[1]


def mensual_tasa_a_anual(tiempos, mm_h):
    """Serie mensual de tasa (mm/h, «AAAA-MM») → acumulados anuales (mm) con los doce meses válidos."""
    por = {}
    for t, v in zip(tiempos, mm_h):
        a, m = int(t[:4]), int(t[5:7])
        por.setdefault(a, {})[m] = None if v is None or not math.isfinite(v) else v * horas_mes(a, m)
    anios, tot = [], []
    for a in sorted(por):
        meses = por[a]
        if len(meses) == 12 and all(v is not None for v in meses.values()):
            anios.append(a)
            tot.append(float(sum(meses.values())))
    return anios, tot


def anual_media(tiempos, valores, minimo_meses=12):
    """Serie mensual («AAAA-MM») → media anual con al menos `minimo_meses` meses válidos."""
    por = {}
    for t, v in zip(tiempos, valores):
        if v is not None and math.isfinite(v):
            por.setdefault(int(t[:4]), []).append(float(v))
    anios = [a for a in sorted(por) if len(por[a]) >= minimo_meses]
    return anios, [float(np.mean(por[a])) for a in anios]


# ---------------------------------------------------------------- comparación con los métodos del backend

def veredicto_serie(anios, valores, unidad, nivel=0.95):
    """Tendencia con los métodos del backend. Devuelve un resumen compacto y comparable con clima.json."""
    from ..estadistica import tendencia_robusta as tr
    a = tr.analizar(anios, valores, unidad, nivel=nivel)
    mc = a["minimos_cuadrados"]
    if mc.get("estado") != "ok":
        return {"veredicto": "datos_insuficientes", "veredicto_contrato": "datos_insuficientes",
                "anios": len(anios), "periodo": [min(anios), max(anios)] if anios else None}
    return {
        "periodo": a["periodo"], "anios": a["anios"], "unidad_pendiente": a["unidad_pendiente"],
        "media": round(mc["media"], 4),
        "mco_por_decada": round(mc["por_decada"], 4), "mco_ic": [round(x, 4) for x in mc["ic_por_decada"]],
        "mco_p_valor": mc["p_valor"],
        "sen_por_decada": a["theil_sen"]["por_decada"], "sen_ic": a["theil_sen"]["ic_por_decada"],
        "mann_kendall": {k: a["mann_kendall_modificado"][k] for k in ("tau", "z", "p_valor", "significativo")},
        "veredicto_contrato": mc["veredicto"],
        "veredicto": a["veredicto"],
    }


def comparar_anual(anios_a, a, anios_b, b, unidad, nivel=0.95):
    """Compara dos series anuales en los años comunes: diferencia media (b − a), r de Pearson y tendencias."""
    comunes = sorted(set(anios_a) & set(anios_b))
    da, db = dict(zip(anios_a, a)), dict(zip(anios_b, b))
    x = np.array([da[k] for k in comunes], float)
    y = np.array([db[k] for k in comunes], float)
    out = {"anios_comunes": len(comunes), "periodo": [comunes[0], comunes[-1]] if comunes else None}
    if len(comunes) < 3:
        out.update(diferencia_media=None, r=None)
        return out
    out["diferencia_media"] = round(float(np.mean(y - x)), 4)
    out["diferencia_relativa_pct"] = round(float(100 * np.mean(y - x) / np.mean(x)), 2) if np.mean(x) else None
    out["r"] = round(float(np.corrcoef(x, y)[0, 1]), 4)
    if len(comunes) >= 10:
        va, vb = veredicto_serie(comunes, x.tolist(), unidad, nivel), veredicto_serie(comunes, y.tolist(), unidad, nivel)
        out["serie_a"], out["serie_b"] = va, vb
        if "sen_por_decada" in va and "sen_por_decada" in vb:
            out["diferencia_pendiente_sen"] = round(vb["sen_por_decada"] - va["sen_por_decada"], 4)
    return out
