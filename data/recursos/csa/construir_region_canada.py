"""Construye data/regiones_canada.geojson: ecozona «Prairies» (Terrestrial Ecozones of Canada, AAFC).

Caso de contraste canadiense del plan de recursos (§3.10, recurso #10 Geo.ca). Pasos:
1. Lee el GeoJSON oficial de ecozonas del National Ecological Framework for Canada v2.2 (AAFC), EPSG:4326.
2. Toma los polígonos con ECOZONE_NAME_EN == "Prairies" y los disuelve en un solo (Multi)Polygon.
3. Simplifica con shapely.simplify(preserve_topology=True) y la tolerancia indicada (grados), valida con
   make_valid y fija precisión de 1e-4°.
4. Calcula áreas en EPSG:6933 (igual área, la misma proyección que usa clima_nic.rutas) antes y después.

Requiere shapely y pyproj. Uso (desde la raíz del repositorio):
    python data/recursos/csa/construir_region_canada.py --fuente nef_ca_ter_ecozone_v2_2.geojson \
        --fecha-descarga 2026-11-12
El archivo fuente no se versiona (4,7 MB); su SHA-256 queda en las propiedades.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "backend"))

URL_GEOJSON = ("https://agriculture.canada.ca/atlas/data_donnees/nationalEcologicalFramework/data_donnees/"
               "geoJSON/ez/nef_ca_ter_ecozone_v2_2.geojson")
URL_CONJUNTO = "https://open.canada.ca/data/en/dataset/7ad7ea01-eb23-4824-bccc-66adb7c5bdf8"
URL_GEOCA = "https://geo.ca/home/?keys=Terrestrial%20Ecozones%20of%20Canada"
URL_LICENCIA = "https://open.canada.ca/en/open-government-licence-canada"
ATRIBUCION = ("Contains information licensed under the Open Government Licence – Canada. "
              "Agriculture and Agri-Food Canada, National Ecological Framework for Canada, Terrestrial Ecozones v2.2.")


def construir(fuente, salida, tolerancia=0.01, fecha_descarga=None, ecozona="Prairies"):
    import shapely
    from shapely.geometry import mapping, shape

    from clima_nic.rutas import proyectar_6933

    datos = json.loads(Path(fuente).read_text(encoding="utf-8"))
    partes = [shape(f["geometry"]) for f in datos["features"]
              if f["properties"].get("ECOZONE_NAME_EN") == ecozona]
    if not partes:
        raise ValueError(f"No hay polígonos de la ecozona {ecozona!r} en {fuente}")
    ids = sorted({f["properties"]["ECOZONE_ID"] for f in datos["features"]
                  if f["properties"].get("ECOZONE_NAME_EN") == ecozona})
    nombre_fr = next(f["properties"]["ECOZONE_NAME_FR"] for f in datos["features"]
                     if f["properties"].get("ECOZONE_NAME_EN") == ecozona)
    original = shapely.make_valid(shapely.union_all(partes))
    simple = shapely.make_valid(shapely.simplify(original, tolerancia, preserve_topology=True))
    simple = shapely.set_precision(simple, 1e-4)
    # make_valid puede devolver GeometryCollection: conservar solo superficies.
    if simple.geom_type == "GeometryCollection":
        simple = shapely.union_all([g for g in simple.geoms if g.geom_type in ("Polygon", "MultiPolygon")])
    area0 = proyectar_6933(original).area / 1e6
    area1 = proyectar_6933(simple).area / 1e6
    n0 = shapely.get_num_coordinates(original)
    n1 = shapely.get_num_coordinates(simple)
    sha = hashlib.sha256(Path(fuente).read_bytes()).hexdigest()
    rid = "CAN_prairies"
    props = {
        "id": rid,
        "nombre": "Ecozona de las Praderas (Prairies), Canadá",
        "nombre_en": ecozona,
        "nombre_fr": nombre_fr,
        "tipo": "ecozona",
        "rol": "contraste",
        "pais": "CAN",
        "ecozone_id": ids[0] if len(ids) == 1 else ids,
        "bbox": [round(v, 3) for v in simple.bounds],
        "area_km2": round(area1, 1),
        "area_km2_original": round(area0, 1),
        "diferencia_area_pct": round(100 * (area1 - area0) / area0, 3),
        "vertices_original": int(n0),
        "vertices_simplificado": int(n1),
        "simplificacion": {"metodo": "shapely.simplify(preserve_topology=True) + make_valid + set_precision(1e-4)",
                           "tolerancia_grados": tolerancia},
        "area_proyeccion": "EPSG:6933 (EASE-Grid 2.0, igual área)",
        "crs": "EPSG:4326",
        "fuente": {"conjunto": "Terrestrial Ecozones of Canada — National Ecological Framework for Canada v2.2 (AAFC)",
                   "url_conjunto": URL_CONJUNTO, "url_descarga": URL_GEOJSON, "url_geoca": URL_GEOCA,
                   "sha256_descarga": sha},
        "licencia": {"nombre": "Open Government Licence – Canada", "url": URL_LICENCIA, "atribucion": ATRIBUCION},
        "fecha_descarga": fecha_descarga,
    }
    doc = {"type": "FeatureCollection",
           "nota": ("Caso de contraste canadiense (plan de recursos §3.10). Ecozona Prairies del National Ecological "
                    "Framework (AAFC) disuelta en una geometría y simplificada; no es un límite oficial a escala fina. "
                    "Toda la región está al sur de 60° N, dentro de la cobertura completa de IMERG (60° S–60° N)."),
           "features": [{"type": "Feature", "id": rid, "properties": props, "geometry": mapping(simple)}]}
    texto = json.dumps(doc, ensure_ascii=False, separators=(",", ":"))
    Path(salida).write_text(texto + "\n", encoding="utf-8", newline="\n")
    return props, len(texto.encode("utf-8"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fuente", required=True, type=Path)
    ap.add_argument("--salida", type=Path, default=RAIZ / "data" / "regiones_canada.geojson")
    ap.add_argument("--tolerancia", type=float, default=0.01)
    ap.add_argument("--fecha-descarga", default=None)
    a = ap.parse_args()
    props, tam = construir(a.fuente, a.salida, a.tolerancia, a.fecha_descarga)
    print(json.dumps({k: props[k] for k in ("bbox", "area_km2", "area_km2_original", "diferencia_area_pct",
                                            "vertices_original", "vertices_simplificado")}, ensure_ascii=False),
          f"{tam / 1024:.1f} KB")


if __name__ == "__main__":
    main()
