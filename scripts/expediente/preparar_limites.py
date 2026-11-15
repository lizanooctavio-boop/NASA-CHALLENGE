"""Prepara los límites administrativos de Nicaragua para el expediente territorial.

Entrada: GeoJSON descargados del WFS público de INETER (EPSG:4326, orden lon/lat):
  wsINETER-DGGC:Municipios    → ineter_municipios.geojson
  wsINETER-DGGC:Departamentos → ineter_departamentos.geojson
  https://mapserveride.ineter.gob.ni/geoserver/ows?service=WFS&version=2.0.0&request=GetFeature
      &typeNames=<capa>&outputFormat=application/json&srsName=EPSG:4326

Salida: data/admin/nicaragua_municipios.geojson y data/admin/nicaragua_departamentos.geojson, simplificados
(Douglas-Peucker con preservación de topología, tolerancia 0,001° ≈ 110 m) para uso web. Cada entidad conserva
el nombre y el código oficiales, la superficie publicada por INETER y la superficie geodésica WGS84 de la
geometría original y de la simplificada, para que el informe pueda declarar la diferencia.

Uso: python scripts/expediente/preparar_limites.py <carpeta_descargas> [fecha_acceso_ISO]
"""
import json
import sys
from pathlib import Path

from pyproj import Geod
from shapely import set_precision
from shapely.geometry import mapping, shape
from shapely.validation import make_valid

RAIZ = Path(__file__).resolve().parents[2]
TOL = 0.001
GEOD = Geod(ellps="WGS84")


def area_km2(g):
    return abs(GEOD.geometry_area_perimeter(g)[0]) / 1e6


def redondear(coords, nd=5):
    if isinstance(coords, (list, tuple)) and coords and isinstance(coords[0], (int, float)):
        return [round(coords[0], nd), round(coords[1], nd)]
    return [redondear(c, nd) for c in coords]


def poligonal(g):
    g = make_valid(g)
    if g.geom_type == "GeometryCollection":
        from shapely.geometry import MultiPolygon
        partes = [p for p in g.geoms if p.geom_type in ("Polygon", "MultiPolygon")]
        polys = []
        for p in partes:
            polys.extend(p.geoms if p.geom_type == "MultiPolygon" else [p])
        g = MultiPolygon(polys)
    return g


def procesar(entrada, salida, campos, acceso):
    fc = json.loads(Path(entrada).read_text(encoding="utf-8"))
    feats = []
    for f in fc["features"]:
        g0 = poligonal(shape(f["geometry"]))
        # simplificación + rejilla de 1e-5° (~1 m): set_precision deja una geometría válida, sin anillos degenerados
        g1 = poligonal(set_precision(poligonal(g0.simplify(TOL, preserve_topology=True)), 1e-5))
        props = {k: f["properties"].get(k) for k in campos}
        if "area" in f["properties"]:
            props["area_ineter_km2"] = round(float(f["properties"]["area"]), 3)
        props["area_geodesica_original_km2"] = round(area_km2(g0), 3)
        props["area_geodesica_simplificada_km2"] = round(area_km2(g1), 3)
        geom = mapping(g1)
        feats.append({"type": "Feature", "properties": props,
                      "geometry": {"type": geom["type"], "coordinates": redondear(json.loads(json.dumps(geom["coordinates"])))}})
    feats.sort(key=lambda f: json.dumps([f["properties"].get(c) for c in campos], ensure_ascii=False))
    out = {
        "type": "FeatureCollection",
        "procedencia": {
            "fuente": "INETER, Dirección General de Geodesia y Cartografía (servicio WFS público IDE)",
            "capa": Path(entrada).stem,
            "servicio": "https://mapserveride.ineter.gob.ni/geoserver/ows",
            "version_limites": "Sin versión publicada en el servicio; marca de tiempo WFS " + str(fc.get("timeStamp")),
            "fecha_acceso": acceso,
            "crs": "EPSG:4326 (lon, lat)",
            "simplificacion": f"Douglas-Peucker con preservación de topología, tolerancia {TOL}° (~110 m)",
            "licencia": "Servicio público de INETER sin licencia explícita (AccessConstraints: NONE). Citar a INETER.",
        },
        "features": feats,
    }
    Path(salida).write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return len(feats)


if __name__ == "__main__":
    carpeta = Path(sys.argv[1])
    acceso = sys.argv[2] if len(sys.argv) > 2 else "2026-11-15"
    capas = {"ineter_municipios.geojson": ("nicaragua_municipios.geojson", ["cod_municipio", "nom_municipio", "nom_departamento"]),
             "ineter_departamentos.geojson": ("nicaragua_departamentos.geojson", ["nom_departamento"])}
    for ent, (sal, campos) in capas.items():
        n = procesar(carpeta / ent, RAIZ / "data" / "admin" / sal, campos, acceso)
        print(sal, n)
