"""Genera data/lugares_mundo.json a partir de Natural Earth (dominio público).

Descarga países (Admin 0, 110m/50m) y lugares poblados (10m populated places simple)
a una carpeta de caché fuera del repositorio y produce un JSON compacto (< 600 KB)
con país (nombre en inglés, código ISO-3, encuadre bbox y centro) y hasta 30 ciudades
más pobladas por país.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SALIDA_DEFECTO = RAIZ / "data" / "lugares_mundo.json"
CACHE_DEFECTO = Path(os.path.expanduser("~")) / ".cache" / "earth_trend_detective" / "natural_earth"

URL_PAISES = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson"
URL_CIUDADES = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_populated_places_simple.geojson"


def _descargar(url: str, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.is_file() and destino.stat().st_size > 1000:
        return destino
    req = urllib.request.Request(url, headers={"User-Agent": "EarthSystemTrendDetective/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        destino.write_bytes(resp.read())
    return destino


def _bbox_geom(geom: dict) -> list[float] | None:
    tipo = geom.get("type")
    coords = geom.get("coordinates")
    if not coords:
        return None
    lons: list[float] = []
    lats: list[float] = []

    def _recorrer(nodo):
        if isinstance(nodo, (list, tuple)) and nodo and isinstance(nodo[0], (int, float)):
            lons.append(float(nodo[0]))
            lats.append(float(nodo[1]))
        elif isinstance(nodo, (list, tuple)):
            for sub in nodo:
                _recorrer(sub)

    if tipo in ("Polygon", "MultiPolygon"):
        _recorrer(coords)
    if not lons or not lats:
        return None
    # Evitar cajas que cruzan el antimeridiano (ej. Fiji/Rusia/EEUU si abarcan >300°):
    # si min=-180 y max=180, usar centroide razonable.
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    if max_lon - min_lon > 300:
        pos = [x for x in lons if x >= 0]
        neg = [x for x in lons if x < 0]
        if pos and neg:
            # Tomar el bloque principal más numeroso para el encuadre visual
            bloque = pos if len(pos) >= len(neg) else neg
            min_lon, max_lon = min(bloque), max(bloque)
    return [round(min_lon, 2), round(min_lat, 2), round(max_lon, 2), round(max_lat, 2)]


def generar(cache_dir: Path = CACHE_DEFECTO, salida: Path = SALIDA_DEFECTO) -> dict:
    ruta_paises = _descargar(URL_PAISES, cache_dir / "ne_50m_admin_0_countries.geojson")
    ruta_ciudades = _descargar(URL_CIUDADES, cache_dir / "ne_10m_populated_places_simple.geojson")

    geo_paises = json.loads(ruta_paises.read_text(encoding="utf-8"))
    geo_ciudades = json.loads(ruta_ciudades.read_text(encoding="utf-8"))

    paises_por_iso: dict[str, dict] = {}
    nombre_a_iso: dict[str, str] = {}

    for feat in geo_paises.get("features", []):
        props = feat.get("properties") or {}
        nombre = (props.get("NAME_EN") or props.get("NAME") or props.get("ADMIN") or "").strip()
        iso = (props.get("ISO_A3_EH") or props.get("ADM0_A3") or props.get("ISO_A3") or "").strip()
        if not nombre or not iso or iso == "-99":
            continue
        bbox = _bbox_geom(feat.get("geometry") or {})
        if not bbox:
            continue
        centro_lat = round((bbox[1] + bbox[3]) / 2, 2)
        centro_lon = round((bbox[0] + bbox[2]) / 2, 2)
        if iso not in paises_por_iso:
            paises_por_iso[iso] = {
                "iso": iso,
                "nombre": nombre,
                "bbox": bbox,
                "centro": [centro_lat, centro_lon],
                "ciudades": [],
            }
        for clave in (props.get("NAME"), props.get("ADMIN"), props.get("NAME_EN"), props.get("SOVEREIGNT")):
            if clave and str(clave).strip():
                nombre_a_iso[str(clave).strip().lower()] = iso

    vistos_ciudad: dict[str, set[str]] = {}
    for feat in geo_ciudades.get("features", []):
        props = feat.get("properties") or {}
        geom = feat.get("geometry") or {}
        coords = geom.get("coordinates") or []
        if len(coords) < 2:
            continue
        nombre_c = (props.get("name") or props.get("nameascii") or "").strip()
        if not nombre_c:
            continue
        iso = (props.get("adm0_a3") or props.get("iso_a3") or "").strip()
        if iso not in paises_por_iso:
            pais_nom = (props.get("adm0name") or props.get("sov0name") or "").strip().lower()
            iso = nombre_a_iso.get(pais_nom, "")
        if iso not in paises_por_iso:
            continue
        pob = int(props.get("pop_max") or props.get("pop_min") or 0)
        lon = round(float(coords[0]), 3)
        lat = round(float(coords[1]), 3)
        clave_dup = nombre_c.lower()
        vistos = vistos_ciudad.setdefault(iso, set())
        if clave_dup in vistos:
            continue
        vistos.add(clave_dup)
        paises_por_iso[iso]["ciudades"].append({
            "nombre": nombre_c,
            "lat": lat,
            "lon": lon,
            "pob": pob,
        })

    paises_lista = []
    for p in sorted(paises_por_iso.values(), key=lambda x: x["nombre"].lower()):
        p["ciudades"].sort(key=lambda c: (-c["pob"], c["nombre"].lower()))
        p["ciudades"] = p["ciudades"][:30]
        paises_lista.append(p)

    doc = {
        "fuente": "Natural Earth 50m countries & 10m populated places (public domain)",
        "paises": paises_lista,
    }
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return doc


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera data/lugares_mundo.json desde Natural Earth.")
    parser.add_argument("--cache", type=Path, default=CACHE_DEFECTO, help="Carpeta de caché fuera del repositorio")
    parser.add_argument("--salida", type=Path, default=SALIDA_DEFECTO, help="Ruta del JSON de salida")
    args = parser.parse_args()
    doc = generar(args.cache, args.salida)
    tam = args.salida.stat().st_size
    total_ciudades = sum(len(p["ciudades"]) for p in doc["paises"])
    print(f"{args.salida}: {len(doc['paises'])} países, {total_ciudades} ciudades, {tam / 1024:.1f} KB")


if __name__ == "__main__":
    main()
