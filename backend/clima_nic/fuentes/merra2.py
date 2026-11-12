"""MERRA-2 directo desde GES DISC (requiere Earthdata). Complementa a POWER con lo que POWER no sirve:

- `M2TMNXOCN` (tavgM_2d_ocn_Nx), TSKINWTR: TSM para Niño 3.4 y otros índices, desde 1980-01.
- `M2IMNPASM` (instM_3d_asm_Np), U y V en 925 hPa: índice CLLJ exacto (Maldonado et al., 2014: viento zonal
  a 925 hPa en 12,5–17,5° N, 80–70° O; positivo con chorro del este más fuerte).
- `M2TMNXLND` (tavgM_2d_lnd_Nx): humedad del suelo y escorrentía.

El número de flujo del archivo (100/200/300/400/401) varía por período; se lista con CMR.
"""
import numpy as np

from .base import Adaptador, SerieRegional, descargar_url
from .earthdata import abridor, granulos

COLECCIONES = {"ocn": ("M2TMNXOCN", "5.12.4"), "pres": ("M2IMNPASM", "5.12.4"), "lnd": ("M2TMNXLND", "5.12.4")}
CAJAS = {"nino34": ((-5, 5), (-170, -120)), "cllj": ((12.5, 17.5), (-80, -70))}


def media_caja(lat, lon, campo, caja):
    (la0, la1), (lo0, lo1) = caja
    ilat = (lat >= la0) & (lat <= la1)
    ilon = (lon >= lo0) & (lon <= lo1)
    c = campo[np.ix_(ilat, ilon)].astype(float)
    w = np.cos(np.radians(lat[ilat]))[:, None] * np.ones(ilon.sum())
    ok = np.isfinite(c)
    return float((c[ok] * w[ok]).sum() / w[ok].sum())


class Merra2(Adaptador):
    id = "merra2"
    nombre = "MERRA-2 (GMAO) en GES DISC"
    producto = "M2TMNXOCN, M2IMNPASM, M2TMNXLND"
    version = "5.12.4"
    variables = {"TSKINWTR": "K", "U925": "m/s", "GWETROOT": "0–1", "RUNOFF": "kg m⁻² s⁻¹"}
    resolucion_espacial = "0,5° × 0,625°"
    resolucion_temporal = "mensual"
    periodo = "1980-01 a la fecha"
    requiere_earthdata = True
    acceso = "GES DISC con cuenta Earthdata"
    documentacion = "https://gmao.gsfc.nasa.gov/reanalysis/MERRA-2/"
    fenomenos = ("enos", "cllj", "humedad_suelo")

    def descargar(self, inicio, fin, coleccion="ocn", **kw):
        corto, version = COLECCIONES[coleccion]
        op = abridor()
        lista = granulos(corto, version, f"{inicio}-01-01T00:00:00Z", f"{fin}-12-31T23:59:59Z", ".nc4")
        return [descargar_url(u, self.cache() / coleccion / n, abridor=op, timeout=900) for n, u in lista]

    @staticmethod
    def leer(ruta, variable, nivel_hpa=None):
        import h5py
        with h5py.File(ruta, "r") as f:
            lat, lon = f["lat"][:], f["lon"][:]
            v = f[variable]
            datos = v[0]
            if nivel_hpa is not None:
                datos = datos[int(np.argmin(np.abs(f["lev"][:] - nivel_hpa)))]
            datos = datos.astype(float)
            relleno = v.attrs.get("_FillValue", np.array([1e15]))
            datos[datos >= float(np.ravel(relleno)[0]) / 10] = np.nan
        return lat, lon, datos

    def recortar(self, archivos, regiones=None, indice="nino34"):
        """Serie mensual de un índice de caja: Niño 3.4 (°C) o CLLJ (−U925, m/s)."""
        valores = []
        for r in archivos:
            if indice == "nino34":
                lat, lon, d = self.leer(r, "TSKINWTR")
                valores.append(media_caja(lat, lon, d, CAJAS["nino34"]) - 273.15)
            else:
                lat, lon, d = self.leer(r, "U", nivel_hpa=925)
                valores.append(-media_caja(lat, lon, d, CAJAS["cllj"]))
        tiempos = [p.stem.rsplit(".", 1)[-1] for p in archivos]
        return tiempos, valores

    def agregar(self, recortado, frecuencia="mensual", indice="nino34"):
        t, v = recortado
        return [SerieRegional("oceano", indice, "°C" if indice == "nino34" else "m/s", "mensual",
                              [f"{x[:4]}-{x[4:6]}" for x in t], v, self.id, self.version)]
