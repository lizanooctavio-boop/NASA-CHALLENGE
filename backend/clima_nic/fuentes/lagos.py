"""Nivel de los lagos Cocibolca (Nicaragua) y Xolotlán (Managua) por altimetría satelital.

Dos vías:
- G-REALM (USDA FAS con NASA GSFC): series de altura relativa de lagos desde 1992 (TOPEX/Poseidon, Jason-1/2/3,
  Sentinel-6). Formato de texto con columnas de fecha decimal y altura (m). El servidor respondió 503 el
  12-11-2026 y no se encontró en su índice un identificador de Cocibolca: el adaptador lee un archivo de texto
  de G-REALM ya descargado o una URL que se le indique. El catálogo NASA GSFC
  respondió HTTP 200 durante la integración CSA; ver data/recursos/csa/acceso.json.
- SWOT (NASA/CNES, desde 2023): producto LakeSP en PO.DAAC (Earthdata) o la API Hydrocron de PO.DAAC por
  identificador de lago de la Prior Lake Database (PLD). Falta fijar el `lake_id` de cada lago.

Referencia para validar (análisis geocientífico del proyecto): Cocibolca 32,91 m s. n. m. y Xolotlán 42,73 m
en octubre de 2010 (INETER); fuertes descensos en 2014–2016. La altimetría da altura relativa a su propio
datum: para comparar con INETER hay que fijar un desplazamiento con un dato común.
"""
import re
import csv
import io
import json
import math
from datetime import datetime
from urllib.parse import urlencode
from pathlib import Path

import numpy as np

from .base import Adaptador, SerieRegional, descargar_url

HYDROCRON = "https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries"

# None means unresolved: never confuse the G-REALM target with a PLD lake_id.
LAKE_IDS = {"cocibolca": None, "xolotlan": None}


def leer_hydrocron(payload):
    """Parse Hydrocron JSON-wrapped CSV; retain only finite, dated WSE records.

    Keep uncertainties and quality flags for downstream screening. A valid
    numeric height alone is not a claim of scientific quality.
    """
    if isinstance(payload, str):
        payload = json.loads(payload)
    rows = csv.DictReader(io.StringIO(payload.get("results", {}).get("csv", "")))
    out = []
    for row in rows:
        try:
            time = row["time_str"]
            datetime.fromisoformat(time.replace("Z", "+00:00"))
            height = float(row["wse"])
            if row.get("no_data", "0").lower() not in ("0", "false", ""):
                continue
            if not math.isfinite(height) or abs(height) >= 1e6:
                continue
        except (KeyError, TypeError, ValueError):
            continue
        out.append({**row, "fecha": time[:10], "altura_m": height,
                    "papel": "demostracion_registro_corto"})
    return sorted(out, key=lambda r: r["time_str"])


def descargar_swot(lake_id, inicio, fin, destino):
    """Explicit PLD identifier required; no Earthdata login for Hydrocron."""
    if not re.fullmatch(r"\d{10}", str(lake_id)):
        raise ValueError("Provide a verified ten-digit PLD lake_id")
    query = urlencode(dict(feature="PriorLake", feature_id=lake_id,
        start_time=inicio, end_time=fin, output="csv",
        fields="lake_id,time_str,wse,wse_u,area_total,quality_f"))
    return descargar_url(HYDROCRON + "?" + query, Path(destino), validar_json=True)


def leer_grealm(texto):
    """Parser tolerante del texto de G-REALM: devuelve (fechas 'AAAA-MM-DD', alturas m).

    Acepta líneas de datos con fecha AAAAMMDD o fecha decimal seguida de la altura; ignora encabezados y
    valores de relleno (≥ 999)."""
    fechas, alturas = [], []
    gsfc = any(re.match(r"^[A-Z0-9]+\s+\d+\s+\d{8}\s", l) for l in texto.splitlines())
    for linea in texto.splitlines():
        partes = linea.split()
        if len(partes) >= 15 and re.fullmatch(r"\d{8}", partes[2]):
            # GSFC 16-column format: column 15 is EGM2008 height.
            try:
                h = float(partes[14])
                f = datetime.strptime(partes[2], "%Y%m%d").date().isoformat()
            except ValueError:
                continue
            if math.isfinite(h) and abs(h) < 9999:
                fechas.append(f)
                alturas.append(h)
            continue
        if gsfc:
            continue
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
        if not math.isfinite(h) or abs(h) >= 999:
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
        return False, "SWOT necesita lake_id PLD verificado; G-REALM admite URL o archivo local explícito"

    def descargar(self, inicio, fin, url=None, archivo=None, **kw):
        if archivo:
            return [Path(archivo)]
        if kw.get("lake_id"):
            return [descargar_swot(kw["lake_id"], f"{inicio}-01-01T00:00:00Z",
                                  f"{fin}-12-31T23:59:59Z",
                                  self.cache() / f"swot_{kw['lake_id']}_{inicio}_{fin}.json")]
        if not url:
            raise ValueError("Indique la URL del texto de G-REALM del lago o un archivo local.")
        return [descargar_url(url, self.cache() / url.rsplit("/", 1)[-1])]

    def recortar(self, archivos, regiones=None, lago="cocibolca"):
        text = Path(archivos[0]).read_text(encoding="utf-8", errors="replace")
        if text.lstrip().startswith("{"):
            obs = leer_hydrocron(text)
            return lago, [o["fecha"] for o in obs], [o["altura_m"] for o in obs]
        f, h = leer_grealm(text)
        return lago, f, h

    def agregar(self, recortado, frecuencia="mensual"):
        lago, fechas, alturas = recortado
        por = {}
        for f, h in zip(fechas, alturas):
            clave = f[:7] if frecuencia == "mensual" else int(f[:4])
            por.setdefault(clave, []).append(h)
        t = sorted(por)
        return [SerieRegional(lago, "altura", "m", frecuencia, t, [float(np.mean(por[k])) for k in t], self.id, self.version)]
