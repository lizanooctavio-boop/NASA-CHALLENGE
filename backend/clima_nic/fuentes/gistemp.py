"""NASA GISS Surface Temperature Analysis v4 (GISTEMP v4).

Anomalía mensual de temperatura de superficie en malla de 2° × 2° (base 1951–1980) a partir de estaciones
GHCNv4 (y ERSSTv5 en el mar). Se usa la versión de radio de suavizado 250 km sobre tierra
(`gistemp250_GHCNv4.nc.gz`), que depende de estaciones cercanas: es la referencia de temperatura
**observada** con que se contrasta la tendencia del reanálisis MERRA-2. Sin cuenta.

Limitación: con celdas de 2° y pocas estaciones de Nicaragua en GHCNv4, varios meses quedan sin dato y la
serie regional mezcla estaciones de países vecinos dentro del radio de 250 km.
"""
import csv
import gzip
import shutil

import numpy as np

from .. import regiones as reg
from ..rutas import FENOMENOS
from .base import Adaptador, SerieRegional, descargar_url, recortar_malla

URL = "https://data.giss.nasa.gov/pub/gistemp/gistemp250_GHCNv4.nc.gz"


class Gistemp(Adaptador):
    id = "gistemp"
    nombre = "GISTEMP v4 (NASA GISS), suavizado 250 km"
    producto = "gistemp250_GHCNv4"
    version = "v4"
    variables = {"tempanomaly": "°C (anomalía respecto de 1951–1980)"}
    resolucion_espacial = "2° × 2°"
    resolucion_temporal = "mensual"
    periodo = "1880 a la fecha (en Nicaragua, con huecos)"
    requiere_earthdata = False
    acceso = "descarga directa (data.giss.nasa.gov)"
    documentacion = "https://data.giss.nasa.gov/gistemp/"
    fenomenos = ("temperatura",)

    def descargar(self, inicio=None, fin=None, **kw):
        gz = descargar_url(URL, self.cache() / "gistemp250_GHCNv4.nc.gz", timeout=900)
        nc = gz.with_suffix("")
        if not nc.exists():
            with gzip.open(gz, "rb") as fi, nc.open("wb") as fo:
                shutil.copyfileobj(fi, fo)
        return [nc]

    @staticmethod
    def leer(ruta):
        try:
            from scipy.io import netcdf_file
            with netcdf_file(ruta, "r", mmap=False) as f:
                lat = f.variables["lat"][:].astype(float)
                lon = f.variables["lon"][:].astype(float)
                v = f.variables["tempanomaly"]
                datos = v[:].astype(float) * float(getattr(v, "scale_factor", 1.0))
                relleno = getattr(v, "_FillValue", 32767)
                datos[v[:] == relleno] = np.nan
                tiempo = f.variables["time"][:].astype(int)
        except (TypeError, ValueError):  # NetCDF-4 (HDF5)
            import h5py
            with h5py.File(ruta, "r") as f:
                lat = f["lat"][:].astype(float)
                lon = f["lon"][:].astype(float)
                v = f["tempanomaly"]
                bruto = v[:]
                datos = bruto.astype(float) * float(v.attrs.get("scale_factor", 1.0))
                datos[bruto == v.attrs.get("_FillValue", 32767)] = np.nan
                tiempo = f["time"][:].astype(int)
        fechas = np.datetime64("1800-01-01") + tiempo.astype("timedelta64[D]")
        return lat, lon, datos, fechas

    def recortar(self, archivos, regiones=None):
        lat, lon, datos, fechas = self.leer(archivos[0])
        # solo la ventana que rodea a Nicaragua, para no ponderar toda la malla global
        ilat = (lat >= 6) & (lat <= 20)
        ilon = (lon >= -92) & (lon <= -78)
        series, pesos = recortar_malla(lat[ilat], lon[ilon], datos[:, ilat][:, :, ilon], regiones)
        meses = [str(f)[:7] for f in fechas.astype("datetime64[M]")]
        return meses, series

    def agregar(self, recortado, frecuencia="anual"):
        meses, series = recortado
        out = []
        for region, s in series.items():
            if frecuencia == "mensual":
                out.append(SerieRegional(region, "tempanomaly", "°C", "mensual", meses, s.tolist(), self.id, self.version))
                continue
            por = {}
            for t, v in zip(meses, s):
                por.setdefault(int(t[:4]), []).append(v)
            anios = [a for a in sorted(por) if len(por[a]) == 12 and np.sum(np.isfinite(por[a])) >= 10]
            vals = [float(np.nanmean(por[a])) for a in anios]
            out.append(SerieRegional(region, "tempanomaly", "°C", "anual", anios, vals, self.id, self.version,
                                     ["año admitido con ≥ 10 meses con dato"]))
        return out


def escribir_derivados(salida=FENOMENOS):
    a = Gistemp()
    meses, series = a.recortar(a.descargar(), reg.cargar())
    salida.mkdir(parents=True, exist_ok=True)
    with (salida / "gistemp_nicaragua.csv").open("w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        regiones = list(series)
        w.writerow(["anio", "mes", *regiones])
        for i, t in enumerate(meses):
            if int(t[:4]) < 1950:
                continue
            w.writerow([int(t[:4]), int(t[5:7]), *("" if not np.isfinite(series[k][i]) else f"{series[k][i]:.3f}"
                                                   for k in regiones)])
    print(f"GISTEMP: {len(meses)} meses, regiones {list(series)}")
