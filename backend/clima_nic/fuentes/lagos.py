"""Nivel del lago Cocibolca (lago de Nicaragua) por altimetría satelital: G-REALM (NASA GSFC).

G-REALM (Global Reservoir and Lake Monitor) pasó del sitio de USDA/IPAD (retirado en 2026) a NASA Goddard:
https://earth.gsfc.nasa.gov/gwm/lake/Index. Producto de 10 días (TOPEX/Poseidon, Jason-1/2/3, Sentinel-6A) desde
septiembre de 1992, sin cuenta. Cocibolca es el objetivo **000351 «Nicaragua»** (11,79° N, 85,71° O). La tabla
de lagos también marca posibles efectos de seiche y viento.

Formato del archivo `lake000351.10d.2.txt` (dentro de `/gwm/zip/lake.10.tar.gz`): 16 columnas; la 3 es la fecha
(AAAAMMDD), la 6 la variación respecto del nivel medio de referencia (m; 999,99 = sin dato), la 7 su error
estimado (m) y la **15 la altura en el datum EGM2008 (m s. n. m.; 9999,99 = sin dato)**, comparable con las
cotas de INETER (Cocibolca 32,91 m en octubre de 2010, según el análisis geocientífico del proyecto).

Xolotlán (lago de Managua) no figura en el catálogo de G-REALM (consulta del 12-11-2026). Para ese lago quedan
SWOT LakeSP (PO.DAAC, Earthdata, desde 2023) o Hydroweb (CNES, no NASA).
"""
import re
import tarfile
from pathlib import Path

import numpy as np

from .base import Adaptador, SerieRegional, descargar_url

URL_TAR = "https://earth.gsfc.nasa.gov/gwm/zip/lake.10.tar.gz"
LAGOS = {"cocibolca": "000351"}
HYDROCRON = "https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries"


def leer_grealm(texto):
    """Lee el texto de G-REALM. Devuelve lista de dicts {fecha, mision, variacion_m, error_m, altura_egm2008_m}.

    Formato GSFC de 16 columnas; también acepta el formato antiguo de dos columnas (fecha AAAAMMDD o decimal y
    altura). Excluye los valores de relleno (999,99 / 9999,99)."""
    obs = []
    gsfc = any(re.match(r"^[A-Z0-9]{4,6}\s+\d+\s+\d{8}\s", l) for l in texto.splitlines())
    for linea in texto.splitlines():
        p = linea.split()
        if gsfc and len(p) >= 15 and re.fullmatch(r"[A-Z0-9]{4,6}", p[0]) and re.fullmatch(r"\d{8}", p[2]):
            try:
                var, err, alt = float(p[5]), float(p[6]), float(p[14])
            except ValueError:
                continue
            if abs(var) >= 999 or alt >= 9999:
                continue
            obs.append({"fecha": f"{p[2][:4]}-{p[2][4:6]}-{p[2][6:]}", "mision": p[0], "variacion_m": var,
                        "error_m": err, "altura_egm2008_m": alt})
        elif not gsfc and len(p) >= 2 and re.match(r"^\d", p[0]):  # formato antiguo (dos columnas)
            try:
                if re.fullmatch(r"\d{8}", p[0]):
                    f = f"{p[0][:4]}-{p[0][4:6]}-{p[0][6:]}"
                    h = float(p[1])
                else:
                    dec = float(p[0])
                    f = str(np.datetime64(f"{int(dec)}-01-01") + np.timedelta64(int(round((dec - int(dec)) * 365.25)), "D"))
                    h = float(p[1])
            except ValueError:
                continue
            if abs(h) >= 999:
                continue
            obs.append({"fecha": f, "mision": "", "variacion_m": h, "error_m": None, "altura_egm2008_m": None})
    return obs


def extraer_de_tar(ruta_tar, id_lago, destino):
    """Extrae solo el texto del lago del archivo completo de G-REALM (sin descomprimir el resto)."""
    nombre = f"lake{id_lago}.10d.2.txt"
    with tarfile.open(ruta_tar, "r:gz") as t:
        miembro = t.getmember(nombre)
        f = t.extractfile(miembro)
        Path(destino).write_bytes(f.read())
    return Path(destino)


class NivelLagos(Adaptador):
    id = "lagos"
    nombre = "Nivel de lagos por altimetría (G-REALM, NASA GSFC)"
    producto = "G-REALM 10-day lake product"
    version = "TPJOJS.2.5"
    variables = {"altura_egm2008_m": "m s. n. m. (EGM2008)", "variacion_m": "m"}
    resolucion_espacial = "por lago (paso del satélite sobre el lago)"
    resolucion_temporal = "10 días"
    periodo = "1992-09 a la fecha"
    requiere_earthdata = False
    acceso = "descarga abierta (earth.gsfc.nasa.gov/gwm); SWOT por PO.DAAC con Earthdata"
    documentacion = "https://earth.gsfc.nasa.gov/gwm/lake/Index"
    fenomenos = ("nivel_lagos", "sequia")

    def descargar(self, inicio=None, fin=None, lago="cocibolca", archivo=None, tar=None, **kw):
        if archivo:
            return [Path(archivo)]
        id_lago = LAGOS[lago]
        destino = self.cache() / f"lake{id_lago}.10d.2.txt"
        if destino.exists():
            return [destino]
        tar = Path(tar) if tar else descargar_url(URL_TAR, self.cache() / "lake.10.tar.gz", timeout=3600)
        return [extraer_de_tar(tar, id_lago, destino)]

    def recortar(self, archivos, regiones=None, lago="cocibolca"):
        return lago, leer_grealm(Path(archivos[0]).read_text(encoding="utf-8", errors="replace"))

    def agregar(self, recortado, frecuencia="mensual", variable="altura_egm2008_m"):
        lago, obs = recortado
        por = {}
        for o in obs:
            if o[variable] is None:
                continue
            clave = o["fecha"][:7] if frecuencia == "mensual" else int(o["fecha"][:4])
            por.setdefault(clave, []).append(o[variable])
        t = sorted(por)
        return [SerieRegional(lago, variable, "m", frecuencia, t, [float(np.mean(por[k])) for k in t], self.id,
                              self.version, [f"n por periodo: {min(len(v) for v in por.values())}–{max(len(v) for v in por.values())}"])]


def escribir_derivados(tar=None, salida=None):
    """data/fenomenos/nivel_cocibolca_grealm.csv con cada observación de 10 días."""
    import csv
    from ..rutas import FENOMENOS
    salida = salida or FENOMENOS
    a = NivelLagos()
    lago, obs = a.recortar(a.descargar(tar=tar))
    with (salida / "nivel_cocibolca_grealm.csv").open("w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["fecha", "mision", "altura_egm2008_m", "variacion_m", "error_m"])
        for o in obs:
            w.writerow([o["fecha"], o["mision"], f"{o['altura_egm2008_m']:.2f}", f"{o['variacion_m']:.2f}", o["error_m"]])
    print(f"Cocibolca: {len(obs)} observaciones {obs[0]['fecha']} a {obs[-1]['fecha']}")
