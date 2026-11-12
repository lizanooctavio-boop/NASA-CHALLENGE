"""Autenticación NASA Earthdata y búsqueda de gránulos en CMR.

Credenciales: archivo `.netrc` (o `_netrc` en Windows, o la ruta de la variable NETRC) con
`machine urs.earthdata.nasa.gov login <usuario> password <contraseña>`. Este módulo nunca imprime, registra
ni copia las credenciales: solo comprueba que existe una entrada para urs.earthdata.nasa.gov y se las pasa
al gestor HTTP de urllib. CMR (cmr.earthdata.nasa.gov) es público y no las necesita.
"""
import http.cookiejar
import json
import netrc
import os
import urllib.parse
import urllib.request
from pathlib import Path

CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
URS = "urs.earthdata.nasa.gov"


def ruta_netrc():
    if os.environ.get("NETRC") and Path(os.environ["NETRC"]).exists():
        return Path(os.environ["NETRC"])
    for nombre in (".netrc", "_netrc"):
        if (Path.home() / nombre).exists():
            return Path.home() / nombre
    return None


def hay_credenciales():
    r = ruta_netrc()
    if r is None:
        return False
    try:
        return netrc.netrc(str(r)).authenticators(URS) is not None
    except (netrc.NetrcParseError, OSError):
        return False


def abridor():
    """Abridor urllib que sigue la redirección OAuth de URS con las credenciales del .netrc."""
    from .base import RequiereEarthdata
    if not hay_credenciales():
        raise RequiereEarthdata("Configure .netrc con urs.earthdata.nasa.gov (cuenta gratuita en urs.earthdata.nasa.gov).")
    usuario, _, clave = netrc.netrc(str(ruta_netrc())).authenticators(URS)
    gestor = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    gestor.add_password(None, f"https://{URS}", usuario, clave)
    return urllib.request.build_opener(urllib.request.HTTPBasicAuthHandler(gestor),
                                       urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def granulos(short_name, version, inicio, fin, extension, bbox=None, max_paginas=50):
    """Lista (nombre, url) de gránulos vía CMR, ordenados por fecha. bbox = (oeste, sur, este, norte)."""
    salida = []
    for pagina in range(1, max_paginas + 1):
        q = {"short_name": short_name, "version": version, "page_size": 200, "page_num": pagina,
             "temporal": f"{inicio},{fin}", "sort_key": "start_date"}
        if bbox:
            q["bounding_box"] = ",".join(str(v) for v in bbox)
        with urllib.request.urlopen(f"{CMR}?{urllib.parse.urlencode(q)}", timeout=120) as r:
            entradas = json.load(r)["feed"]["entry"]
        if not entradas:
            break
        for e in entradas:
            url = next((l["href"] for l in e.get("links", [])
                        if l["href"].startswith("https") and l["href"].endswith(extension)), None)
            if url:
                salida.append((url.rsplit("/", 1)[1], url))
    return salida
