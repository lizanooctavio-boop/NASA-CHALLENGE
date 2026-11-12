"""Regiones de análisis y pesos de malla.

Regiones (data/regiones_nicaragua.geojson, EPSG:4326):

| id | Departamentos (Natural Earth 10 m, admin-1) |
|---|---|
| NIC | máscara completa del contrato 1.0.0 (dominios.geojson, lagos restados) |
| pacifico | Chinandega, León, Managua, Masaya, Granada, Carazo, Rivas |
| central | Nueva Segovia, Madriz, Estelí, Jinotega, Matagalpa, Boaco, Chontales (contiene el Corredor Seco del norte y centro) |
| caribe | Región Autónoma de la Costa Caribe Norte y Sur, Río San Juan |
| caja_sicc | rectángulo 10,7–12,6° N, 86,5–83,6° O (referencia de SICC-952; incluye lagos, mar y norte de Costa Rica) |

Pacífico, Central y Caribe son una partición de NIC: cada región es la intersección de la máscara NIC con la
unión de sus departamentos, y los retazos de NIC que no caen en ningún departamento (diferencias de contorno
entre Natural Earth 10 m y la máscara simplificada) se asignan a la región más cercana. Así las tres suman
exactamente el área de NIC. Son agrupaciones político-administrativas aproximadas de las tres regiones
climáticas; el Corredor Seco oficial (FAO/SICA) se define por municipios y no coincide con un departamento.

Construir (solo si cambia la geometría; requiere shapely y pyproj y el admin-1 de Natural Earth 10 m):
    python -m clima_nic.regiones --admin1 ne_10m_admin_1_states_provinces.geojson
"""
import argparse
import json
from pathlib import Path

import numpy as np

from .rutas import DATOS, REGIONES_GEOJSON, proyectar_6933, sha256

GRUPOS = {
    "pacifico": ("NI-CI", "NI-LE", "NI-MN", "NI-MS", "NI-GR", "NI-CA", "NI-RI"),
    "central": ("NI-NS", "NI-MD", "NI-ES", "NI-JI", "NI-MT", "NI-BO", "NI-CO"),
    "caribe": ("NI-AN", "NI-AS", "NI-SJ"),
}
NOMBRES = {
    "NIC": "Nicaragua (país completo, lagos restados)",
    "pacifico": "Región del Pacífico",
    "central": "Región Central (incluye el Corredor Seco del norte y centro)",
    "caribe": "Región del Caribe (costas Norte y Sur y Río San Juan)",
    "caja_sicc": "Caja SICC-952 (10,7–12,6° N; 86,5–83,6° O)",
}
ORDEN = ("NIC", "pacifico", "central", "caribe", "caja_sicc")


def construir(admin1, dominios=DATOS / "dominios.geojson", salida=REGIONES_GEOJSON):
    import shapely
    from shapely.geometry import mapping, shape
    dom = json.loads(Path(dominios).read_text(encoding="utf-8"))
    geoms = {f["id"]: shape(f["geometry"]) for f in dom["features"]}
    nic = geoms["NIC"]
    ne = json.loads(Path(admin1).read_text(encoding="utf-8"))
    deptos = {f["properties"]["iso_3166_2"]: shape(f["geometry"]) for f in ne["features"]
              if f["properties"].get("adm0_a3") == "NIC"}
    faltan = {c for g in GRUPOS.values() for c in g} - deptos.keys()
    if faltan:
        raise ValueError(f"Faltan departamentos en el admin-1: {sorted(faltan)}")
    reg = {k: shapely.make_valid(nic.intersection(shapely.union_all([deptos[c] for c in cods])))
           for k, cods in GRUPOS.items()}
    resto = nic.difference(shapely.union_all(list(reg.values())))
    piezas = list(getattr(resto, "geoms", [resto])) if not resto.is_empty else []
    for p in piezas:
        if p.area <= 0:
            continue
        destino = min(reg, key=lambda k: reg[k].distance(p))
        reg[destino] = reg[destino].union(p)
    reg = {k: shapely.make_valid(v).buffer(0) for k, v in reg.items()}
    salida_geoms = {"NIC": nic, **reg, "caja_sicc": geoms["caja_sicc"]}
    feats = []
    for k in ORDEN:
        g = salida_geoms[k]
        area = proyectar_6933(g).area / 1e6
        feats.append({"type": "Feature", "id": k,
                      "properties": {"id": k, "nombre": NOMBRES[k], "area_km2": round(area, 1),
                                     "departamentos": list(GRUPOS.get(k, ())),
                                     "bbox": [round(v, 3) for v in g.bounds]},
                      "geometry": mapping(shapely.set_precision(g, 1e-4))})
    suma = sum(f["properties"]["area_km2"] for f in feats if f["id"] in GRUPOS)
    doc = {"type": "FeatureCollection",
           "nota": ("Pacífico, Central y Caribe forman una partición de NIC (máscara de dominios.geojson). Departamentos "
                    "de Natural Earth 10 m admin-1 (dominio público); retazos de contorno asignados a la región más cercana. "
                    "Agrupación aproximada, no límites oficiales."),
           "fuentes": {"dominios_geojson_sha256": sha256(dominios), "natural_earth_admin1_sha256": sha256(admin1)},
           "comprobacion": {"suma_regiones_km2": round(suma, 1),
                            "nic_km2": next(f["properties"]["area_km2"] for f in feats if f["id"] == "NIC")},
           "features": feats}
    Path(salida).write_text(json.dumps(doc, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return doc


def cargar(ruta=REGIONES_GEOJSON):
    from shapely.geometry import shape
    doc = json.loads(Path(ruta).read_text(encoding="utf-8"))
    return {f["id"]: shape(f["geometry"]) for f in doc["features"]}


def pesos_malla(lats, lons, dlat, dlon, regiones=None, minimo_km2=0.5):
    """Área (km², EPSG:6933) de cada celda (centro lat, lon; tamaño dlat × dlon) dentro de cada región.

    Devuelve lista de dicts {lat, lon, <region>: km2} solo para celdas con peso en alguna región.
    """
    import shapely
    from shapely.geometry import box
    regiones = cargar() if regiones is None else regiones
    proy = {k: proyectar_6933(g) for k, g in regiones.items()}
    out = []
    for la in lats:
        for lo in lons:
            c = proyectar_6933(box(lo - dlon / 2, la - dlat / 2, lo + dlon / 2, la + dlat / 2))
            p = {k: shapely.intersection(c, g).area / 1e6 for k, g in proy.items()}
            if max(p.values()) > minimo_km2:
                out.append({"lat": round(float(la), 4), "lon": round(float(lo), 4),
                            **{k: round(v, 3) if v > minimo_km2 else 0.0 for k, v in p.items()}})
    return out


def media_ponderada(valores_por_celda, pesos):
    """valores_por_celda: (n_celdas, ...) ; pesos: (n_celdas,). Ignora NaN renormalizando pesos."""
    v = np.asarray(valores_por_celda, float)
    w = np.asarray(pesos, float).reshape((-1,) + (1,) * (v.ndim - 1))
    ok = np.isfinite(v) & (w > 0)
    num = np.where(ok, v * w, 0).sum(axis=0)
    den = np.where(ok, w, 0).sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, num / den, np.nan)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--admin1", type=Path, required=True)
    a = ap.parse_args()
    d = construir(a.admin1)
    for f in d["features"]:
        print(f"{f['id']:10s} {f['properties']['area_km2']:10.1f} km²  {f['properties']['bbox']}")
    print("comprobación:", d["comprobacion"])
