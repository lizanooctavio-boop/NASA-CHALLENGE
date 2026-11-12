"""Construye data/dominios.geojson desde el mapa base de SICC-952 (Natural Earth 1:50 m simplificado).

Solo se leen tres países y los lagos del mapa; el resto no se copia. Uso:
    python scripts/datos/geometrias.py --mapa <ruta>/mundo.geojson
"""
import argparse
import itertools
import json
from pathlib import Path

import shapely
from shapely import make_valid
from shapely.geometry import box, mapping, shape
from shapely.ops import unary_union

from comun import CAJA, DATOS, PAISES, area_km2, sha256

NOMBRES = {"caja_sicc": "Caja original de SICC-952", "NIC": "Nicaragua", "HND": "Honduras", "CRI": "Costa Rica",
           "NIC_fuera_caja": "Nicaragua fuera de la caja de SICC-952"}
UMBRAL_KM2 = 1.0  # intersecciones menores se consideran contacto de borde, no área compartida
TIPOS = {"caja_sicc": ("caja", "referencia"), "NIC": ("pais", "principal"), "HND": ("pais", "contexto"),
         "CRI": ("pais", "contexto"), "NIC_fuera_caja": ("complemento", "auxiliar")}


def construir(mapa):
    datos = json.loads(Path(mapa).read_text(encoding="utf-8"))
    paises = {f["properties"]["iso"]: make_valid(shape(f["geometry"]))
              for f in datos["features"] if f["properties"].get("iso") in PAISES}
    lagos = unary_union([make_valid(shape(f["geometry"])) for f in datos["features"]
                         if f["properties"].get("tipo") == "lago"])
    paises = {k: g.difference(lagos) for k, g in paises.items()}
    (sur, norte), (oeste, este) = CAJA["lat"], CAJA["lon"]
    caja = box(oeste, sur, este, norte)
    geoms = {"caja_sicc": caja, **paises, "NIC_fuera_caja": paises["NIC"].difference(caja)}
    features = []
    for k, g in geoms.items():
        g = shapely.set_precision(g, 1e-6)
        tipo, rol = TIPOS[k]
        features.append({"type": "Feature", "id": k, "geometry": mapping(g),
                         "properties": {"id": k, "nombre": NOMBRES[k], "tipo": tipo, "rol": rol,
                                        "bbox": [round(v, 4) for v in g.bounds], "area_km2": round(area_km2(g), 1)}})
        geoms[k] = g
    pares, sin_area = [], []
    for a, b in itertools.combinations(geoms, 2):
        inter = area_km2(geoms[a].intersection(geoms[b]))
        if inter < UMBRAL_KM2:
            sin_area.append([a, b])
        else:
            pares.append({"a": a, "b": b, "interseccion_km2": round(inter, 1),
                          "fraccion_de_a": round(inter / area_km2(geoms[a]), 4),
                          "fraccion_de_b": round(inter / area_km2(geoms[b]), 4)})
    return {"type": "FeatureCollection",
            "nota": ("Geometrías de referencia para ponderar celdas IMERG de 0,1°; no son fronteras oficiales. "
                     "Países: Natural Earth 1:50 m simplificado en SICC-952, con los lagos disponibles restados. "
                     "caja_sicc: rectángulo 10,7–12,6° N, 86,5–83,6° O."),
            "fuente_mapa_sha256": sha256(mapa),
            "superposicion": {"umbral_km2": UMBRAL_KM2, "pares": pares, "sin_area_compartida": sin_area},
            "features": features}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mapa", required=True, type=Path)
    ap.add_argument("--salida", type=Path, default=DATOS / "dominios.geojson")
    a = ap.parse_args()
    r = construir(a.mapa)
    a.salida.write_text(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    for f in r["features"]:
        print(f["id"], f["properties"]["area_km2"], "km²")
