"""Procesado de las escenas RCM (recurso #9) del pedido EODMS 3787605: demostración, no tendencia.

Escenas: RCM GRD nivel I1, ScanSAR 30 m (franja de 125 km), HH+HV, 16-08-2023 y 22-08-2023, sobre el lago
Cocibolca. Mismo método que opera_demostracion.py para que los resultados sean comparables:

1. Calibración a sigma0 con la tabla lutSigma de cada polarización: sigma0 = (DN² + offset) / ganancia,
   con la ganancia interpolada por columna (pixelFirstLutValue, stepSize). DN = 0 es relleno.
2. Georreferenciación con los puntos de control (GCP) del GeoTIFF o, si faltan, con los imageTiePoint de
   product.xml; potencia promediada a 100 m en EPSG:6933 antes de pasar a dB.
3. Superficie candidata de agua en HH con umbrales de −19, −17 y −15 dB dentro del polígono del lago y solo en
   píxeles observados. Estado NO_VALIDADA: no hay referencia local independiente en esas fechas.
4. Emparejamiento con las observaciones SWOT de Cocibolca a ±2 días.

Las escenas no se versionan: se leen de una carpeta externa (por defecto ../rcm_crudo, junto al repositorio),
con los ZIP descargados de EODMS o ya descomprimidos.

    python scripts/sar/rcm_procesar.py --entrada ../rcm_crudo
"""
import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from clima_nic.fuentes.sar_agua import potencia_a_db  # noqa: E402

SALIDA = ROOT / "data" / "recursos" / "csa"
UMBRALES_DB = (-19.0, -17.0, -15.0)
RESOLUCION_M = 100
PEDIDO = {"eodms_order_id": 3787605, "productos": {"5616847": "2023-08-22", "5600935": "2023-08-16"}}


# ---------------------------------------------------------------- lectura
def _sin_ns(elemento):
    for e in elemento.iter():
        if isinstance(e.tag, str) and "}" in e.tag:
            e.tag = e.tag.split("}", 1)[1]
    return elemento


def leer_lut(ruta_xml, ancho):
    """Tabla lutSigma de RCM → (offset, ganancia por columna de imagen)."""
    raiz = _sin_ns(ET.parse(ruta_xml).getroot())
    offset = float(raiz.findtext(".//offset"))
    ganancias = np.array([float(x) for x in raiz.findtext(".//gains").split()])
    primero = int(float(raiz.findtext(".//pixelFirstLutValue") or 0))
    paso = int(float(raiz.findtext(".//stepSize") or 1))
    columnas_lut = primero + paso * np.arange(len(ganancias))
    if paso < 0:
        columnas_lut, ganancias = columnas_lut[::-1], ganancias[::-1]
    columnas = np.arange(ancho)
    return offset, np.interp(columnas, columnas_lut, ganancias)


def calibrar(dn, offset, ganancias):
    """DN entero → sigma0 lineal. DN = 0 (relleno) y potencias no positivas quedan como NaN."""
    dn = np.asarray(dn, dtype=float)
    sigma0 = (dn * dn + offset) / np.asarray(ganancias, dtype=float)[None, :]
    return np.where((dn > 0) & (sigma0 > 0), sigma0, np.nan)


def puntos_de_control(product_xml):
    """imageTiePoint de product.xml → lista de rasterio GroundControlPoint (columna, fila, lon, lat)."""
    from rasterio.control import GroundControlPoint
    raiz = _sin_ns(ET.parse(product_xml).getroot())
    gcps = []
    for tp in raiz.iter("imageTiePoint"):
        fila = float(tp.findtext(".//line"))
        columna = float(tp.findtext(".//pixel"))
        lat = float(tp.findtext(".//latitude"))
        lon = float(tp.findtext(".//longitude"))
        gcps.append(GroundControlPoint(row=fila, col=columna, x=lon, y=lat, z=0.0))
    if len(gcps) < 4:
        raise ValueError(f"{product_xml}: menos de 4 puntos de control")
    return gcps


def localizar(carpeta):
    """Producto RCM descomprimido → {'HH': tif, 'HV': tif}, {'HH': lut, ...}, product.xml."""
    carpeta = Path(carpeta)
    tifs = {m.group(1).upper(): p for p in carpeta.rglob("*.tif")
            if (m := re.search(r"_(HH|HV|VV|VH)\.tif$", p.name, re.I))}
    luts = {}
    for p in carpeta.rglob("lutSigma*.xml"):
        m = re.search(r"lutSigma_?(HH|HV|VV|VH)?", p.name, re.I)
        luts[(m.group(1) or "").upper() or "*"] = p
    productos = list(carpeta.rglob("product.xml"))
    if not tifs or not luts or not productos:
        raise FileNotFoundError(f"{carpeta}: falta imagen, lutSigma o product.xml")
    return tifs, luts, productos[0]


def fecha_producto(product_xml):
    raiz = _sin_ns(ET.parse(product_xml).getroot())
    texto = raiz.findtext(".//rawDataStartTime") or raiz.findtext(".//zeroDopplerTimeFirstLine")
    return datetime.fromisoformat(texto.strip()[:19])


# ---------------------------------------------------------------- georreferenciación
def a_malla_6933(sigma0, ruta_tif, product_xml):
    """sigma0 (filas, columnas) → potencia media en una malla de 100 m en EPSG:6933, con su transformación."""
    import rasterio
    from rasterio.warp import Resampling, calculate_default_transform, reproject
    with rasterio.open(ruta_tif) as src:
        gcps, crs_gcp = src.gcps
        transformacion, crs = (None, None)
        if not gcps:
            if src.crs and not src.transform.is_identity:
                transformacion, crs = src.transform, src.crs
            else:
                gcps, crs_gcp = puntos_de_control(product_xml), "EPSG:4326"
    filas, columnas = sigma0.shape
    if gcps:
        dst_t, ancho, alto = calculate_default_transform(crs_gcp, "EPSG:6933", columnas, filas, gcps=gcps,
                                                         resolution=RESOLUCION_M)
        extra = {"gcps": gcps, "src_crs": crs_gcp}
    else:
        bounds = rasterio.transform.array_bounds(filas, columnas, transformacion)
        dst_t, ancho, alto = calculate_default_transform(crs, "EPSG:6933", columnas, filas, *bounds,
                                                         resolution=RESOLUCION_M)
        extra = {"src_transform": transformacion, "src_crs": crs}
    destino = np.full((alto, ancho), np.nan, dtype="float32")
    reproject(sigma0.astype("float32"), destino, src_nodata=np.nan, dst_transform=dst_t, dst_crs="EPSG:6933",
              dst_nodata=np.nan, resampling=Resampling.average, **extra)
    return destino, dst_t


# ---------------------------------------------------------------- superficie
def superficie_candidata(db, dominio):
    """Área candidata de agua (km²) por umbral dentro de un dominio booleano, solo en píxeles observados."""
    km2 = (RESOLUCION_M / 1000) ** 2
    observado = dominio & np.isfinite(db)
    return {u: float(np.count_nonzero(observado & (db < u)) * km2) for u in UMBRALES_DB}, float(observado.sum() * km2)


def _sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def preparar(entrada):
    """Descomprime los ZIP de EODMS (si los hay) y devuelve las carpetas de producto y sus huellas."""
    entrada = Path(entrada)
    huellas = {}
    for z in sorted(entrada.glob("*.zip")):
        huellas[z.name] = _sha256(z)
        destino = entrada / z.stem
        if not destino.exists():
            with zipfile.ZipFile(z) as f:
                f.extractall(destino)
    productos = sorted({p.parent.parent if p.parent.name == "metadata" else p.parent
                        for p in entrada.rglob("product.xml")})
    return productos, huellas


def main():
    import rasterio
    from pyproj import Transformer
    from rasterio.features import geometry_mask
    from shapely.geometry import mapping, shape
    from shapely.ops import transform

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", type=Path, default=ROOT.parent / "rcm_crudo")
    a = ap.parse_args()
    productos, huellas = preparar(a.entrada)
    if not productos:
        raise SystemExit(f"No hay productos RCM en {a.entrada}; descárguelos desde EODMS (pedido {PEDIDO['eodms_order_id']}).")
    lago = shape(json.loads((SALIDA / "cocibolca_naturalearth.geojson").read_text(encoding="utf-8"))["features"][0]["geometry"])
    lago_6933 = transform(Transformer.from_crs(4326, 6933, always_xy=True).transform, lago)
    area_lago = lago_6933.area / 1e6
    filas, fuentes = [], []
    for carpeta in productos:
        tifs, luts, product_xml = localizar(carpeta)
        fecha = fecha_producto(product_xml)
        for pol in ("HH", "HV"):
            if pol not in tifs:
                continue
            with rasterio.open(tifs[pol]) as src:
                dn = src.read(1)
            offset, ganancias = leer_lut(luts.get(pol) or luts["*"], dn.shape[1])
            sigma0 = calibrar(dn, offset, ganancias)
            potencia, t = a_malla_6933(sigma0, tifs[pol], product_xml)
            db = potencia_a_db(potencia)
            dominio = geometry_mask([mapping(lago_6933)], out_shape=db.shape, transform=t, invert=True)
            areas, observado = superficie_candidata(db, dominio)
            for umbral, area in areas.items():
                filas.append({"fecha_utc": fecha.isoformat(timespec="seconds"), "producto": carpeta.name,
                              "polarizacion": pol, "umbral_db": umbral, "area_candidata_agua_km2": round(area, 2),
                              "area_observada_lago_km2": round(observado, 2),
                              "cobertura_fraccion_lago": round(observado / area_lago, 4),
                              "radiometria": "sigma0 dB (lutSigma), media de potencia a 100 m",
                              "papel": "demostracion_registro_corto", "estado": "NO_VALIDADA",
                              "motivo": "dos_fechas;sin_referencia_local_independiente;dominio_observado_parcial"})
            fuentes.append({"producto": carpeta.name, "polarizacion": pol, "fecha_utc": fecha.isoformat(timespec="seconds"),
                            "imagen": tifs[pol].name, "sha256_imagen": _sha256(tifs[pol]),
                            "lut": (luts.get(pol) or luts["*"]).name})
    swot = list(csv.DictReader((SALIDA / "swot_observaciones.csv").open(encoding="utf-8")))
    pares = []
    for f in filas:
        if f["polarizacion"] != "HH" or f["umbral_db"] != -17.0:
            continue
        t = datetime.fromisoformat(f["fecha_utc"])
        for o in swot:
            if o["lago"] != "cocibolca":
                continue
            ts = datetime.fromisoformat(o["time_str"].replace("Z", ""))
            if abs(ts - t) <= timedelta(days=2):
                pares.append({"fecha_rcm_utc": f["fecha_utc"], "area_candidata_agua_km2": f["area_candidata_agua_km2"],
                              "area_observada_lago_km2": f["area_observada_lago_km2"], "swot_time_utc": o["time_str"],
                              "swot_wse_m": o["wse"], "dias_diferencia": round((ts - t).total_seconds() / 86400, 2)})
    with (SALIDA / "rcm_superficie.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    with (SALIDA / "rcm_vs_swot.csv").open("w", encoding="utf-8", newline="") as f:
        campos = ["fecha_rcm_utc", "area_candidata_agua_km2", "area_observada_lago_km2", "swot_time_utc", "swot_wse_m", "dias_diferencia"]
        w = csv.DictWriter(f, fieldnames=campos, lineterminator="\n")
        w.writeheader()
        w.writerows(pares)
    (SALIDA / "rcm_fuentes.json").write_text(json.dumps({
        **PEDIDO, "coleccion": "EODMS RCM Image Products (Public Good)", "licencia": "Open Government Licence – Canada / EULA RCM",
        "zips_sha256": huellas, "imagenes": fuentes, "umbrales_db": list(UMBRALES_DB), "resolucion_m": RESOLUCION_M,
        "dominio": "cocibolca_naturalearth.geojson (Natural Earth 10 m, dominio público)",
        "area_lago_km2": round(area_lago, 2)}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(filas)} filas de superficie, {len(pares)} pares con SWOT")


if __name__ == "__main__":
    main()
