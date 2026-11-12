"""Rutas compartidas. Los datos crudos (JSON de POWER, NetCDF/HDF5) van a la caché, que no se versiona."""
import hashlib
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DATOS = RAIZ / "data"
FENOMENOS = DATOS / "fenomenos"
HISTORIAL = DATOS / "historial"
REGIONES_GEOJSON = DATOS / "regiones_nicaragua.geojson"
SCRIPTS_DATOS = RAIZ / "scripts" / "datos"
CACHE = Path(os.environ.get("CLIMA_NIC_CACHE", RAIZ / "backend" / ".cache"))

# tendencia.py (veredicto del contrato 1.0.0) vive en scripts/datos y no se duplica.
if str(SCRIPTS_DATOS) not in sys.path:
    sys.path.append(str(SCRIPTS_DATOS))


def sha256(ruta):
    h = hashlib.sha256()
    with Path(ruta).open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def a_6933(lon, lat):
    from pyproj import Transformer
    return Transformer.from_crs(4326, 6933, always_xy=True).transform(lon, lat)


def proyectar_6933(geom):
    import numpy as np
    import shapely
    return shapely.transform(geom, lambda c: np.column_stack(a_6933(c[:, 0], c[:, 1])))
