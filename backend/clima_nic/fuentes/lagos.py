"""Nivel de los lagos Cocibolca (Nicaragua) y Xolotlán (Managua) por altimetría satelital.

Dos vías:
- G-REALM (USDA FAS con NASA GSFC): series de altura relativa de lagos desde 1992 (TOPEX/Poseidon, Jason-1/2/3,
  Sentinel-6). Formato de texto con columnas de fecha decimal y altura (m). El servidor respondió 503 el
  12-11-2026 y no se encontró en su índice un identificador de Cocibolca: el adaptador lee un archivo de texto
  de G-REALM ya descargado o una URL que se le indique.
- SWOT (NASA/CNES, desde 2023): producto LakeSP en PO.DAAC (Earthdata) o la API Hydrocron de PO.DAAC por
  identificador de lago de la Prior Lake Database (PLD). Falta fijar el `lake_id` de cada lago.

Referencia para validar (análisis geocientífico del proyecto): Cocibolca 32,91 m s. n. m. y Xolotlán 42,73 m
en octubre de 2010 (INETER); fuertes descensos en 2014–2016. La altimetría da altura relativa a su propio
datum: para comparar con INETER hay que fijar un desplazamiento con un dato común.
"""
import re
from pathlib import Path

import numpy as np

from .base import Adaptador, SerieRegional, descargar_url

HYDROCRON = "https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries"


def leer_grealm(texto):
    """Parser tolerante del texto de G-REALM: devuelve (fechas 'AAAA-MM-DD', alturas m).

    Acepta líneas de datos con fecha AAAAMMDD o fecha decimal seguida de la altura; ignora encabezados y
    valores de relleno (≥ 999)."""
    fechas, alturas = [], []
    for linea in texto.splitlines():
        partes = linea.split()
        if len(partes) < 2 or not re.match(r"^\d", partes[0]):
            continue
        try:
            if re.fullmatch(r"\d{8}", partes[0]):
                f = f"{partes[0][:4]}-{partes[0][4:6]}-{partes[0][6:]}"
                h = float(partes[-1] if len(partes) == 2 else partes[1])
            else:
                dec = float(partes[0])
                anio = int(dec)
                dia = int(round((dec - anio) * 365.25))
                f = str(np.datetime64(f"{anio}-01-01") + np.timedelta64(dia, "D"))
                h = float(partes[1])
        except ValueError:
            continue
        if abs(h) >= 999:
            continue
        fechas.append(f)
        alturas.append(h)
    return fechas, alturas


class NivelLagos(Adaptador):
    id = "lagos"
    nombre = "Nivel de lagos por altimetría (G-REALM, SWOT)"
    producto = "G-REALM / SWOT LakeSP"
    version = "—"
    variables = {"altura": "m (relativa al datum del producto)"}
    resolucion_espacial = "por lago"
    resolucion_temporal = "10 días (G-REALM), ~21 días (SWOT)"
    periodo = "1992 a la fecha (G-REALM); 2023 a la fecha (SWOT)"
    requiere_earthdata = False
    acceso = "G-REALM abierto (texto); SWOT por Hydrocron o PO.DAAC"
    documentacion = "https://ipad.fas.usda.gov/cropexplorer/global_reservoir/"
    fenomenos = ("nivel_lagos", "sequia")

    def disponible(self):
        return False, "G-REALM no respondió (503) y falta el identificador de Cocibolca/Xolotlán; SWOT requiere lake_id"

    def descargar(self, inicio, fin, url=None, archivo=None, **kw):
        if archivo:
            return [Path(archivo)]
        if not url:
            raise ValueError("Indique la URL del texto de G-REALM del lago o un archivo local.")
        return [descargar_url(url, self.cache() / url.rsplit("/", 1)[-1])]

    def recortar(self, archivos, regiones=None, lago="cocibolca"):
        f, h = leer_grealm(Path(archivos[0]).read_text(encoding="utf-8", errors="replace"))
        return lago, f, h

    def agregar(self, recortado, frecuencia="mensual"):
        lago, fechas, alturas = recortado
        por = {}
        for f, h in zip(fechas, alturas):
            clave = f[:7] if frecuencia == "mensual" else int(f[:4])
            por.setdefault(clave, []).append(h)
        t = sorted(por)
        return [SerieRegional(lago, "altura", "m", frecuencia, t, [float(np.mean(por[k])) for k in t], self.id, self.version)]
