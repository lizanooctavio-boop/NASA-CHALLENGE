"""Interfaz común de los adaptadores de datos NASA.

Cada adaptador declara sus metadatos (producto, versión, resolución, período, si requiere Earthdata) e
implementa tres pasos:

    descargar(inicio, fin)          → archivos crudos en la caché local (nunca en git)
    recortar(archivos, regiones)    → campo o series por región (media ponderada por área)
    agregar(recortado, "mensual"|"anual") → lista de SerieRegional

`recortar_malla` es la implementación genérica para cualquier malla regular lat/lon: pondera cada celda por
el área de su intersección con el polígono (EPSG:6933), igual que el contrato 1.0.0. Los adaptadores de
archivos (HDF5/NetCDF) solo leen el arreglo y llaman a esta función; por eso se pueden probar con mallas
sintéticas sin descargar nada.
"""
import json
import math
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from .. import regiones as reg
from ..rutas import CACHE


@dataclass
class SerieRegional:
    region: str
    variable: str
    unidad: str
    frecuencia: str            # "diaria" | "mensual" | "anual"
    tiempos: list              # "AAAA-MM-DD" | "AAAA-MM" | AAAA
    valores: list
    fuente: str
    version: str = ""
    notas: list = field(default_factory=list)

    def como_dict(self):
        d = asdict(self)
        d["valores"] = [None if (v is None or (isinstance(v, float) and not math.isfinite(v))) else v for v in self.valores]
        return d


class RequiereEarthdata(RuntimeError):
    """El adaptador necesita una cuenta de NASA Earthdata y no hay credenciales configuradas."""


class Adaptador:
    id = ""
    nombre = ""
    producto = ""
    version = ""
    variables = {}            # nombre → unidad
    resolucion_espacial = ""
    resolucion_temporal = ""
    periodo = ""
    requiere_earthdata = False
    acceso = ""
    documentacion = ""
    fenomenos = ()

    def metadatos(self):
        return {k: getattr(self, k) for k in ("id", "nombre", "producto", "version", "variables", "resolucion_espacial",
                                              "resolucion_temporal", "periodo", "requiere_earthdata", "acceso",
                                              "documentacion")} | {"fenomenos": list(self.fenomenos)}

    def disponible(self):
        if self.requiere_earthdata:
            from .earthdata import hay_credenciales
            return (True, "credenciales Earthdata presentes") if hay_credenciales() else \
                (False, "requiere cuenta Earthdata (.netrc con urs.earthdata.nasa.gov)")
        return True, "acceso abierto"

    def cache(self):
        c = CACHE / self.id
        c.mkdir(parents=True, exist_ok=True)
        return c

    def descargar(self, inicio, fin, **kw):
        raise NotImplementedError

    def recortar(self, archivos, regiones=None):
        raise NotImplementedError

    def agregar(self, recortado, frecuencia="mensual"):
        raise NotImplementedError


# ---------------------------------------------------------------- utilidades compartidas

def descargar_url(url, destino, intentos=8, abridor=None, validar_json=False, timeout=300):
    """Descarga con reintentos y escritura atómica. No reescribe si ya existe."""
    destino = Path(destino)
    if destino.exists() and destino.stat().st_size > 0:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    espera = 2.0
    abrir = (abridor.open if abridor else urllib.request.urlopen)
    for k in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "nasa-challenge-clima/1.0"})
            with abrir(req, timeout=timeout) as r:
                datos = r.read()
            if validar_json:
                json.loads(datos)
            tmp = destino.with_suffix(destino.suffix + ".parcial")
            tmp.write_bytes(datos)
            tmp.replace(destino)
            return destino
        except (urllib.error.URLError, ConnectionError, TimeoutError, json.JSONDecodeError) as e:
            if isinstance(e, urllib.error.HTTPError) and e.code in (400, 401, 403, 404):
                raise RuntimeError(f"{url}: HTTP {e.code}") from e
            if k == intentos - 1:
                raise RuntimeError(f"No se pudo descargar {url}: {e}") from e
            time.sleep(espera)
            espera *= 2


def bordes(centros):
    c = np.asarray(centros, float)
    d = np.diff(c)
    return np.r_[c[0] - d[0] / 2, c[:-1] + d / 2, c[-1] + d[-1] / 2]


def recortar_malla(lat, lon, campo, regiones=None, pesos=None):
    """Media ponderada por área de `campo` (t, lat, lon) o (lat, lon) en cada región.

    lon puede venir en 0–360; se convierte a −180–180. Devuelve ({region: serie}, pesos usados).
    Las celdas sin dato (NaN) se excluyen renormalizando los pesos en cada instante.
    """
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    lon = np.where(lon > 180, lon - 360, lon)
    campo = np.asarray(campo, float)
    if campo.ndim == 2:
        campo = campo[None]
    if pesos is None:
        dlat = float(abs(np.median(np.diff(lat)))) if len(lat) > 1 else 0.1
        dlon = float(abs(np.median(np.diff(lon)))) if len(lon) > 1 else 0.1
        pesos = reg.pesos_malla(lat, lon, dlat, dlon, regiones)
    if not pesos:
        raise ValueError("Ninguna celda de la malla toca las regiones pedidas.")
    ilat = {round(float(v), 4): i for i, v in enumerate(lat)}
    ilon = {round(float(v), 4): i for i, v in enumerate(lon)}
    idx = [(ilat[p["lat"]], ilon[p["lon"]]) for p in pesos]
    valores = np.stack([campo[:, i, j] for i, j in idx])  # (celdas, t)
    nombres = [k for k in pesos[0] if k not in ("lat", "lon")]
    out = {k: reg.media_ponderada(valores, [p[k] for p in pesos]) for k in nombres}
    return out, pesos


def a_mensual(fechas, valores, como="suma"):
    """Serie diaria → mensual. Devuelve (["AAAA-MM"...], valores). Meses incompletos → NaN."""
    from ..estadistica import indicadores as ind
    a, m, v = ind.mensual_desde_diario(fechas, valores, como)
    return [f"{x:04d}-{y:02d}" for x, y in zip(a, m)], v.tolist()


def a_anual(tiempos_mensuales, valores, como="suma", meses=range(1, 13)):
    """Serie mensual ("AAAA-MM") → anual con los meses indicados completos.

    Un año con un mes repetido se descarta: un duplicado no puede sustituir a un mes ausente."""
    por, duplicados = {}, set()
    for t, v in zip(tiempos_mensuales, valores):
        a, m = int(t[:4]), int(t[5:7])
        if m in meses:
            if m in por.setdefault(a, {}):
                duplicados.add(a)
            por[a][m] = v
    anios, vals = [], []
    for a in sorted(por):
        x = np.array(list(por[a].values()), float)
        if a not in duplicados and set(por[a]) == set(meses) and np.all(np.isfinite(x)):
            anios.append(a)
            vals.append(float(x.sum() if como == "suma" else x.mean()))
    return anios, vals
