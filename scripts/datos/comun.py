"""Constantes y utilidades compartidas por los scripts de datos."""
import hashlib
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DATOS = RAIZ / "data"
ANIOS = list(range(2001, 2025))
MESES_ONI = tuple(range(6, 12))  # junio–noviembre (trimestres centrados MJJ…OND)
CAJA = {"lat": (10.7, 12.6), "lon": (-86.5, -83.6)}  # caja original de SICC-952
DOMINIOS = ("caja_sicc", "NIC", "HND", "CRI", "NIC_fuera_caja")
PAISES = ("NIC", "HND", "CRI")
COBERTURA_MINIMA = 0.999
PRODUCTO = "GPM_3IMERGM.07"
VARIABLE = "Grid/precipitation"


def sha256(ruta):
    h = hashlib.sha256()
    with Path(ruta).open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def a_6933(lon, lat):
    """lon/lat (grados) → x/y en EPSG:6933, cilíndrica de igual área (metros). Acepta escalares y arreglos."""
    from pyproj import Transformer
    return Transformer.from_crs(4326, 6933, always_xy=True).transform(lon, lat)


def proyectar_6933(geom):
    import numpy as np
    import shapely
    return shapely.transform(geom, lambda c: np.column_stack(a_6933(c[:, 0], c[:, 1])))


def area_km2(geom):
    return proyectar_6933(geom).area / 1e6
