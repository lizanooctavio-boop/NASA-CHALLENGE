"""GRACE y GRACE-FO, mascones JPL RL06.3 (PO.DAAC). Requiere Earthdata.

Anomalía del almacenamiento total de agua terrestre (cm de equivalente de agua, base 2004–2009) en malla de
0,5° (los mascones reales son de 3°: la resolución efectiva es ~300 km, casi del tamaño de Nicaragua).
Período 2002-04 a la fecha con un hueco de 11 meses entre GRACE (fin 2017-06) y GRACE-FO (inicio 2018-06).
Útil para sequías plurianuales (2014–2016) y para contrastar con lluvia y humedad del suelo; con ~22 años y el
hueco, las tendencias son exploratorias. Se recomienda aplicar el factor de escala (CRI) del mismo producto.
"""
import numpy as np

from .base import Adaptador, SerieRegional, descargar_url, recortar_malla
from .earthdata import abridor, granulos

PRODUCTO = ("TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4", "RL06.3v04")


class GraceFo(Adaptador):
    id = "grace_fo"
    nombre = "GRACE/GRACE-FO JPL mascons RL06.3 CRI"
    producto = PRODUCTO[0]
    version = PRODUCTO[1]
    variables = {"lwe_thickness": "cm"}
    resolucion_espacial = "0,5° (mascones de 3°)"
    resolucion_temporal = "mensual"
    periodo = "2002-04 a la fecha (hueco 2017-07 a 2018-05)"
    requiere_earthdata = True
    acceso = "PO.DAAC con cuenta Earthdata"
    documentacion = "https://grace.jpl.nasa.gov/data/get-data/jpl_global_mascons/"
    fenomenos = ("almacenamiento_agua", "sequia")

    def descargar(self, inicio, fin, **kw):
        op = abridor()
        lista = granulos(PRODUCTO[0], PRODUCTO[1], f"{inicio}-01-01T00:00:00Z", f"{fin}-12-31T23:59:59Z", ".nc")
        return [descargar_url(u, self.cache() / n, abridor=op, timeout=1800) for n, u in lista[-1:]]  # archivo único acumulado

    @staticmethod
    def leer(ruta):
        import h5py
        with h5py.File(ruta, "r") as f:
            lat, lon = f["lat"][:], f["lon"][:]
            lon180 = np.where(lon > 180, lon - 360, lon)
            ilat = (lat >= 10) & (lat <= 15.5)
            ilon = (lon180 >= -88.5) & (lon180 <= -82)
            d = f["lwe_thickness"][:][:, ilat][:, :, ilon].astype(float)
            t = f["time"][:]
        fechas = np.datetime64("2002-01-01") + np.round(t).astype("timedelta64[D]")
        return lat[ilat], lon180[ilon], d, fechas

    def recortar(self, archivos, regiones=None):
        lat, lon, d, fechas = self.leer(archivos[0])
        series, _ = recortar_malla(lat, lon, d, regiones)
        return [str(f)[:7] for f in fechas.astype("datetime64[M]")], series

    def agregar(self, recortado, frecuencia="mensual"):
        t, series = recortado
        return [SerieRegional(k, "lwe_thickness", "cm", "mensual", t, v.tolist(), self.id, self.version)
                for k, v in series.items()]
