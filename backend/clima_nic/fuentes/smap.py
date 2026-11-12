"""SMAP L4 humedad del suelo (SPL4SMGP, NSIDC DAAC). Requiere Earthdata.

Humedad superficial (0–5 cm) y de la zona radicular (0–100 cm) cada 3 h en la malla EASE-Grid 2.0 global de
9 km (equivalente en área, no regular en latitud). Disponible desde marzo de 2015: con ~10 años sirve para
describir anomalías y validar la humedad de modelo de MERRA-2 (GWETROOT), no para tendencias climáticas.

Recorte: los píxeles EASE tienen igual área, así que la media regional es el promedio simple de los píxeles
cuyo centro cae dentro del polígono.
"""
import numpy as np

from .. import regiones as reg
from .base import Adaptador, SerieRegional, descargar_url
from .earthdata import abridor, granulos


def recortar_puntos(lat2d, lon2d, campo, regiones=None):
    """Promedio simple de los píxeles de igual área cuyo centro está dentro de cada región."""
    import shapely
    regiones = reg.cargar() if regiones is None else regiones
    lat2d, lon2d = np.asarray(lat2d, float), np.asarray(lon2d, float)
    campo = np.asarray(campo, float)
    if campo.ndim == lat2d.ndim:
        campo = campo[None]
    out = {}
    for k, g in regiones.items():
        dentro = shapely.contains_xy(g, lon2d, lat2d)
        if not dentro.any():
            out[k] = np.full(campo.shape[0], np.nan)
            continue
        x = campo[:, dentro]
        with np.errstate(invalid="ignore"):
            out[k] = np.nanmean(np.where(np.isfinite(x), x, np.nan), axis=1)
    return out


class Smap(Adaptador):
    id = "smap"
    nombre = "SMAP L4 Global 3-hourly 9 km Surface and Root Zone Soil Moisture"
    producto = "SPL4SMGP"
    version = "7"
    variables = {"sm_surface": "m³/m³", "sm_rootzone": "m³/m³"}
    resolucion_espacial = "9 km (EASE-Grid 2.0)"
    resolucion_temporal = "3 horas"
    periodo = "2015-03 a la fecha"
    requiere_earthdata = True
    acceso = "NSIDC DAAC con cuenta Earthdata"
    documentacion = "https://nsidc.org/data/spl4smgp"
    fenomenos = ("humedad_suelo", "sequia")

    def descargar(self, inicio, fin, **kw):
        op = abridor()
        lista = granulos("SPL4SMGP", self.version, f"{inicio}T00:00:00Z", f"{fin}T23:59:59Z", ".h5",
                         bbox=(-88, 10.5, -82.5, 15.25))
        return [descargar_url(u, self.cache() / n, abridor=op, timeout=900) for n, u in lista]

    @staticmethod
    def leer(ruta, variable="sm_rootzone"):
        import h5py
        with h5py.File(ruta, "r") as f:
            lat, lon = f["cell_lat"][:], f["cell_lon"][:]
            sel = (lat >= 10.5) & (lat <= 15.25) & (lon >= -88) & (lon <= -82.5)
            filas = np.any(sel, axis=1)
            cols = np.any(sel, axis=0)
            d = f["Geophysical_Data"][variable][np.ix_(filas, cols)].astype(float)
            lat, lon = lat[np.ix_(filas, cols)], lon[np.ix_(filas, cols)]
        d[d < 0] = np.nan
        return lat, lon, d

    def recortar(self, archivos, regiones=None, variable="sm_rootzone"):
        out = {}
        for r in archivos:
            lat, lon, d = self.leer(r, variable)
            for k, v in recortar_puntos(lat, lon, d, regiones).items():
                out.setdefault(k, []).append(float(v[0]))
        return [p.name for p in archivos], out

    def agregar(self, recortado, frecuencia="diaria", variable="sm_rootzone"):
        t, datos = recortado
        return [SerieRegional(k, variable, "m³/m³", frecuencia, t, v, self.id, self.version) for k, v in datos.items()]
