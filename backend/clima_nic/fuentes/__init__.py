"""Registro extensible de fuentes NASA. Para añadir un dataset: subclase de `Adaptador` y una línea en REGISTRO."""
from importlib import import_module

from .base import Adaptador, RequiereEarthdata, SerieRegional, recortar_malla  # noqa: F401

REGISTRO = {
    "power": "power:Power",
    "imerg": "imerg:Imerg",
    "merra2": "merra2:Merra2",
    "modis": "modis:Modis",
    "smap": "smap:Smap",
    "grace_fo": "grace:GraceFo",
    "gistemp": "gistemp:Gistemp",
    "nex_gddp_cmip6": "nex_gddp:NexGddp",
    "lagos": "lagos:NivelLagos",
}


def obtener(id_):
    modulo, clase = REGISTRO[id_].split(":")
    return getattr(import_module(f".{modulo}", __name__), clase)()


def catalogo():
    """Metadatos y disponibilidad de todas las fuentes registradas."""
    out = []
    for k in REGISTRO:
        a = obtener(k)
        ok, motivo = a.disponible()
        out.append({**a.metadatos(), "disponible": ok, "motivo": motivo})
    return out
