"""GPM IMERG Final V07 (GES DISC). Requiere Earthdata.

- Mensual `GPM_3IMERGM` v07: desde enero de 1998 (comprobado en CMR el 12-11-2026: 324 gránulos 1998–2024).
  Los 288 archivos de 2001–2024 ya están procesados en data/serie_mensual.csv (contrato 1.0.0); este adaptador
  añade 1998–2000 y cualquier región nueva.
- Diario `GPM_3IMERGDF` v07: misma ventana; habilitaría extremos y canícula a 0,1°.

Variable `precipitation` (mm/h en el mensual, mm/día en el diario), dimensiones (time, lon, lat).
"""
import numpy as np

from .base import Adaptador, SerieRegional, recortar_malla
from .earthdata import abridor, granulos

COLECCIONES = {"mensual": ("GPM_3IMERGM", "07"), "diaria": ("GPM_3IMERGDF", "07")}
BBOX = (-88.0, 10.5, -82.5, 15.25)


class Imerg(Adaptador):
    id = "imerg"
    nombre = "GPM IMERG Final V07"
    producto = "GPM_3IMERGM / GPM_3IMERGDF"
    version = "V07B"
    variables = {"precipitation": "mm/h (mensual) o mm/día (diaria)"}
    resolucion_espacial = "0,1°"
    resolucion_temporal = "mensual y diaria"
    periodo = "1998-01 a la fecha"
    requiere_earthdata = True
    acceso = "GES DISC con cuenta Earthdata"
    documentacion = "https://gpm.nasa.gov/data/imerg"
    fenomenos = ("lluvia", "extremos_lluvia", "canicula", "sequia")

    def descargar(self, inicio, fin, frecuencia="mensual", **kw):
        from .base import descargar_url
        corto, version = COLECCIONES[frecuencia]
        lista = granulos(corto, version, f"{inicio}-01-01T00:00:00Z", f"{fin}-12-31T23:59:59Z", ".HDF5")
        op = abridor()
        return [descargar_url(url, self.cache() / frecuencia / nombre, abridor=op, timeout=900) for nombre, url in lista]

    @staticmethod
    def leer(ruta):
        import h5py
        with h5py.File(ruta, "r") as f:
            g = f["Grid"]
            lat = g["lat"][:]
            lon = g["lon"][:]
            ilat = (lat >= BBOX[1]) & (lat <= BBOX[3])
            ilon = (lon >= BBOX[0]) & (lon <= BBOX[2])
            p = g["precipitation"][0][np.ix_(ilon, ilat)].astype(float).T  # (lat, lon)
        p[p < 0] = np.nan
        return lat[ilat], lon[ilon], p

    def recortar(self, archivos, regiones=None, pesos=None, horas=None):
        """Lista de HDF5 → {region: [valor por archivo]} (mm si se pasan las horas de cada mes)."""
        out = {}
        for i, ruta in enumerate(archivos):
            lat, lon, p = self.leer(ruta)
            series, pesos = recortar_malla(lat, lon, p, regiones, pesos)
            for k, s in series.items():
                out.setdefault(k, []).append(float(s[0]) * (horas[i] if horas else 1.0))
        return out, pesos

    def agregar(self, recortado, frecuencia="mensual", tiempos=None):
        datos, _ = recortado
        return [SerieRegional(k, "precipitation", "mm", frecuencia, list(tiempos or range(len(v))), v, self.id, self.version)
                for k, v in datos.items()]
