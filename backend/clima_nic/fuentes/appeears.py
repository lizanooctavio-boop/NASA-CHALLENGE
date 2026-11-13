"""Extracción de ÁREA AppEEARS, reanudable; crudos y tareas en CACHE/appeears.

Ejecutar desde backend: python -m clima_nic.fuentes.appeears --help.
Rasterio lee los valores empaquetados de GeoTIFF: aplicar Scale/Offset de la banda una vez.
Rasterio es opcional para descargar, obligatorio para recortar.
"""
import argparse
import base64
import calendar
import hashlib
import json
import netrc
import os
import re
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from ..rutas import DATOS, REGIONES_GEOJSON, proyectar_6933, sha256
from .base import Adaptador, RequiereEarthdata, SerieRegional, a_anual
from .earthdata import ruta_netrc, URS

API = "https://appeears.earthdatacloud.nasa.gov/api"
SALIDA = DATOS / "recursos" / "tierra"
# Orden: empezar SMAP (3 h), ET y LST antes de los productos mensual y anual.
PRODUCTOS = {
    "SPL4SMGP.008": {
        "desde": "2015-03-31", "dias": 0.125,
        "datos": {"Geophysical_Data_sm_surface": ("humedad_smap_superficial", "m³/m³"),
                  "Geophysical_Data_sm_rootzone": ("humedad_smap_raiz", "m³/m³")},
        "qa": ["Geophysical_Data_soil_temp_layer1", "Geophysical_Data_land_fraction_snow_covered"],
    },
    "MOD16A2GF.061": {"desde": "2000-01-01", "dias": 8,
        "datos": {"ET_500m": ("et_modis", "mm")}, "qa": ["ET_QC_500m"]},
    "MOD11A2.061": {"desde": "2000-02-18", "dias": 8,
        "datos": {"LST_Day_1km": ("lst_dia", "°C")}, "qa": ["QC_Day"]},
    "MOD13A3.061": {"desde": "2000-02-01", "dias": None,
        "datos": {"_1_km_monthly_NDVI": ("ndvi_regional", "adimensional")},
        "qa": ["_1_km_monthly_VI_Quality", "_1_km_monthly_pixel_reliability"]},
    "MCD12Q1.061": {"desde": "2001-01-01", "dias": 365,
        "datos": {"LC_Type1": ("cobertura_igbp", "clase")}, "qa": ["QC"]},
}


def guardar_json(ruta, datos):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(ruta.suffix + ".parcial")
    tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(ruta)


def secreto(nombre):
    """Token solo en memoria; admite archivo para procesos ya abiertos en Windows."""
    if os.environ.get(nombre):
        return os.environ[nombre].strip()
    archivo = os.environ.get(nombre + "_FILE")
    return Path(archivo).read_text(encoding="utf-8").strip() if archivo else None


class AppEEARS(Adaptador):
    id = "appeears"
    nombre = "AppEEARS: áreas MODIS y SMAP"
    producto = ", ".join(PRODUCTOS)
    version = "061 / 008"
    variables = {v: u for p in PRODUCTOS.values() for v, u in p["datos"].values()}
    resolucion_espacial = "MODIS 500 m–1 km; SMAP 9 km; media regional por área"
    resolucion_temporal = "3 horas, 8 días, mensual, anual según producto"
    periodo = "MODIS desde 2000/2001; SMAP desde 2015-03-31"
    requiere_earthdata = True
    acceso = "API AppEEARS: token propio obtenido mediante POST /login con Earthdata"
    documentacion = API + "/"
    fenomenos = ("vegetacion", "temperatura_superficie", "evapotranspiracion", "humedad_suelo", "cobertura")

    def __init__(self, token=None):
        self._token = token

    def autenticar(self):
        self._token = self._token or secreto("APPEEARS_TOKEN")
        if self._token:
            return
        ruta = ruta_netrc()
        auth = netrc.netrc(str(ruta)).authenticators(URS) if ruta else None
        if not auth:
            raise RequiereEarthdata("Configure APPEEARS_TOKEN o .netrc/_netrc con urs.earthdata.nasa.gov; no publique secretos.")
        usuario, _, clave = auth
        basic = base64.b64encode(f"{usuario}:{clave}".encode()).decode()
        req = urllib.request.Request(API + "/login", data=b"", method="POST",
                                     headers={"Authorization": "Basic " + basic})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                self._token = json.load(r)["token"]
        except urllib.error.HTTPError as e:
            raise RequiereEarthdata(f"AppEEARS /login: HTTP {e.code}; revise cuenta y autorización AppEEARS.") from None

    def disponible(self):
        from .earthdata import hay_credenciales
        ok = bool(self._token or secreto("APPEEARS_TOKEN") or hay_credenciales())
        return ok, "credencial presente; requiere validación remota" if ok else "falta token AppEEARS o Earthdata netrc"

    def api(self, ruta, datos=None, publico=False, binario=False):
        headers = {"User-Agent": "NASA-CHALLENGE/recursos-tierra"}
        if not publico:
            self.autenticar()
            headers["Authorization"] = "Bearer " + self._token
        if datos is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(API + "/" + ruta, headers=headers,
                                     data=json.dumps(datos).encode() if datos is not None else None)
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read() if binario else json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise RequiereEarthdata(f"AppEEARS HTTP {e.code}; renueve el token de su API (~48 h) o revise autorización.") from None
            raise RuntimeError(f"AppEEARS {ruta.split('/')[0]}: HTTP {e.code}; las tareas ya enviadas quedan guardadas.") from None

    def plan(self, inicio, fin, geojson=REGIONES_GEOJSON, productos=None, bloque_anios=5):
        """Un polígono por tarea: no depender de identificadores aid asignados por el servidor."""
        if inicio < 2001 or fin < inicio or bloque_anios < 1:
            raise ValueError("Periodo de cobertura estable: inicio >= 2001, fin >= inicio; bloque >= 1.")
        geo = json.loads(Path(geojson).read_text(encoding="utf-8"))
        tareas = []
        seleccion = set(PRODUCTOS if productos is None else productos)
        if seleccion - PRODUCTOS.keys():
            raise ValueError("Producto desconocido")
        for producto, cfg in PRODUCTOS.items():
            if producto not in seleccion:
                continue
            for feature in geo["features"]:
                region = str(feature.get("id") or feature["properties"]["id"])
                if feature["geometry"]["type"] not in ("Polygon", "MultiPolygon"):
                    raise ValueError("AppEEARS necesita polígonos")
                paso = 1 if producto == "SPL4SMGP.008" else bloque_anios
                for anio in range(max(inicio, int(cfg["desde"][:4])), fin + 1, paso):
                    desde = max(f"{anio}-01-01", cfg["desde"])
                    hasta = f"{min(anio + paso - 1, fin)}-12-31"
                    capas = list(cfg["datos"]) + cfg["qa"]
                    payload = {"task_type": "area", "task_name": f"tierra-{region}-{producto}-{anio}", "params": {
                        "dates": [{"startDate": date.fromisoformat(desde).strftime("%m-%d-%Y"),
                                   "endDate": date.fromisoformat(hasta).strftime("%m-%d-%Y")}],
                        "layers": [{"product": producto, "layer": k} for k in capas],
                        "geo": {"type": "FeatureCollection", "features": [feature]},
                        "output": {"format": {"type": "geotiff"}, "projection": "geographic"}}}
                    tareas.append({"region": region, "producto": producto, "desde": desde, "hasta": hasta,
                                   "geometria": feature["geometry"], "solicitud": payload})
        return tareas

    def enviar(self, tareas):
        """Envía todo antes de esperar; huella del payload permite reanudar sin duplicar."""
        catalogos = {}
        for tarea in tareas:
            p = tarea["producto"]
            if p not in catalogos:
                catalogos[p] = self.api("product/" + p, publico=True)
            catalogo = catalogos[p]
            for capa in tarea["solicitud"]["params"]["layers"]:
                if not catalogo.get(capa["layer"], {}).get("Available"):
                    raise ValueError(f"Capa no disponible: {p}/{capa['layer']}")
            huella = hashlib.sha256(json.dumps(tarea["solicitud"], sort_keys=True).encode()).hexdigest()[:20]
            registro = self.cache() / (huella + ".json")
            if registro.exists():
                estado = json.loads(registro.read_text(encoding="utf-8"))
            else:
                respuesta = self.api("task", tarea["solicitud"])
                estado = {**tarea, "task_id": respuesta["task_id"], "enviada_utc": datetime.now(timezone.utc).isoformat()}
                guardar_json(registro, estado)
            yield registro, estado

    def esperar(self, task_id, max_segundos=3600, intervalo=30):
        limite = time.monotonic() + max_segundos
        while True:
            estado = self.api("task/" + task_id)
            if estado["status"] == "done":
                if estado.get("summary", {}).get("empty"):
                    raise RuntimeError(f"AppEEARS {task_id}: terminó sin datos")
                return estado
            if estado["status"] == "error":
                raise RuntimeError(f"AppEEARS {task_id}: tarea fallida; consulte su panel")
            restante = limite - time.monotonic()
            if restante <= 0:
                raise TimeoutError(f"AppEEARS {task_id}: sigue {estado['status']}; vuelva a ejecutar para reanudar")
            time.sleep(min(intervalo, restante, 30))

    def bajar_bundle(self, task_id):
        bundle = self.api("bundle/" + task_id)
        directorio = self.cache() / task_id
        directorio.mkdir(parents=True, exist_ok=True)
        guardar_json(directorio / "bundle.json", bundle)
        rutas = []
        for archivo in bundle["files"]:
            # El nombre del bundle no puede escribir fuera del directorio de esta tarea.
            nombre = archivo["file_name"].replace("\\", "/").split("/")[-1]
            ruta = directorio / nombre
            if not ruta.exists() or ruta.stat().st_size != archivo["file_size"]:
                contenido = self.api(f"bundle/{task_id}/{archivo['file_id']}", binario=True)
                if len(contenido) != archivo["file_size"]:
                    raise RuntimeError("Descarga AppEEARS incompleta")
                tmp = ruta.with_suffix(ruta.suffix + ".parcial")
                tmp.write_bytes(contenido)
                tmp.replace(ruta)
            rutas.append(str(ruta))
        return rutas

    def descargar(self, inicio, fin, geojson=REGIONES_GEOJSON, productos=None, max_segundos=3600, **kw):
        tareas = self.plan(inicio, fin, geojson, productos)
        # No esperar entre envíos: las tareas largas empiezan a procesar primero.
        pendientes = list(self.enviar(tareas))
        for registro, estado in pendientes:
            detalle = self.esperar(estado["task_id"], max_segundos)
            estado["archivos"] = self.bajar_bundle(estado["task_id"])
            estado["tiempos"] = {k: detalle.get(k) for k in ("created", "updated", "completed")}
            guardar_json(registro, estado)
        return [e for _, e in pendientes]

    def recortar(self, archivos, regiones=None):
        """Lee GeoTIFF, aplica QA, área exacta y máscara de cobertura constante 500 m → 1 km."""
        return recortar_tareas(archivos, regiones)

    def agregar(self, recortado, frecuencia="mensual"):
        return agregar_registros(recortado, frecuencia)


def mascara_calidad(producto, capas):
    """Solo QA de buena calidad; ausencia de una capa es error, no aceptación tácita."""
    if producto == "MOD13A3.061":
        q = np.asarray(capas["_1_km_monthly_VI_Quality"])
        return ((q & 3) == 0) & (((q >> 2) & 15) <= 2) & (((q >> 6) & 3) <= 2) & \
            ((q & ((1 << 8) | (1 << 10) | (1 << 14) | (1 << 15))) == 0) & \
            (((q >> 11) & 7) == 1) & \
            (capas["_1_km_monthly_pixel_reliability"] == 0)
    if producto == "MOD11A2.061":
        q = np.asarray(capas["QC_Day"])
        return ((q & 3) == 0) & (((q >> 2) & 3) == 0) & (((q >> 4) & 3) <= 1) & (((q >> 6) & 3) == 0)
    if producto == "MOD16A2GF.061":
        q = np.asarray(capas["ET_QC_500m"])
        return ((q & 1) == 0) & ((q & (1 << 2)) == 0) & (((q >> 3) & 3) == 0) & (((q >> 5) & 7) == 0)
    if producto == "MCD12Q1.061":
        return (capas["QC"] == 0) & (capas["LC_Type1"] >= 1) & (capas["LC_Type1"] <= 16)
    if producto == "SPL4SMGP.008":
        # SMGP no expone bitfield QA en AppEEARS. Filtro físico conservador, no QA de recuperación L2/L3.
        t = capas["Geophysical_Data_soil_temp_layer1"]
        nieve = capas["Geophysical_Data_land_fraction_snow_covered"]
        return np.isfinite(t) & (t > 273.15) & (t < 350) & np.isfinite(nieve) & (nieve == 0)
    raise ValueError(producto)


def cobertura_estable(clases, calidad, anios, esperados):
    """Cohorte fija: todos los años exigidos, todos válidos y misma clase IGBP por píxel."""
    if list(anios) != list(esperados):
        raise ValueError("Faltan años MCD12Q1 o hay duplicados: no se puede afirmar cobertura estable")
    clases, calidad = np.asarray(clases), np.asarray(calidad)
    validos = (calidad == 0) & (clases >= 1) & (clases <= 16)
    return validos.all(axis=0) & (clases == clases[0]).all(axis=0)


def leer_tif(ruta, qa=False):
    import rasterio
    with rasterio.open(ruta) as src:
        # QA=0 es válido aunque el TIFF declare nodata=0 (MOD11A2).
        arr = src.read(1) if qa else src.read(1, masked=True).astype(float).filled(np.nan)
        if not qa:
            tags = src.tags() | src.tags(1)
            escala = src.scales[0]
            offset = src.offsets[0]
            if escala == 1 and "scale_factor" in tags:
                escala = float(tags["scale_factor"])
            if offset == 0 and "add_offset" in tags:
                offset = float(tags["add_offset"])
            if np.issubdtype(np.dtype(src.dtypes[0]), np.integer) and escala == 1 and offset == 0:
                raise ValueError("Raster científico entero sin escala: inspeccione los metadatos AppEEARS")
            arr = arr * escala + offset
        return arr, {"transform": src.transform, "crs": src.crs, "shape": arr.shape,
                     "dtype": src.dtypes[0], "scale": src.scales[0], "offset": src.offsets[0]}


def clave_malla(m):
    return (tuple(m["transform"]), str(m["crs"]), m["shape"])


def remuestrear(arr, origen, destino, metodo, nodata=None):
    from rasterio.warp import reproject
    out = np.full(destino["shape"], np.nan, dtype="float64")
    reproject(np.asarray(arr, dtype="float64"), out, src_transform=origen["transform"], src_crs=origen["crs"],
              dst_transform=destino["transform"], dst_crs=destino["crs"], resampling=metodo,
              src_nodata=nodata, dst_nodata=np.nan)
    return out


def pesos_area(malla, geometria):
    """Intersección polígono/celda en EPSG:6933. No ponderar simplemente por número de píxeles."""
    import shapely
    from shapely.geometry import shape
    from pyproj import Transformer
    from shapely.ops import transform
    h, w = malla["shape"]
    tr = malla["transform"]
    if tr.b or tr.d:
        raise ValueError("Se esperan GeoTIFF AppEEARS sin rotación")
    x = tr.c + np.arange(w + 1) * tr.a
    y = tr.f + np.arange(h + 1) * tr.e
    cajas = shapely.box(np.minimum(x[:-1], x[1:])[None, :], np.minimum(y[:-1], y[1:])[:, None],
                        np.maximum(x[:-1], x[1:])[None, :], np.maximum(y[:-1], y[1:])[:, None])
    pol = shape(geometria)
    to_geo = Transformer.from_crs(malla["crs"], 4326, always_xy=True).transform
    cajas = shapely.transform(cajas, lambda c: np.column_stack(to_geo(c[:, 0], c[:, 1])))
    inter = shapely.intersection(cajas, pol)
    # transformación vectorizada con utilitario del repositorio
    return shapely.area(proyectar_6933(inter))


def media_area(arr, pesos, minimo=0.5):
    ok = np.isfinite(arr) & (pesos > 0)
    total = pesos.sum()
    fraccion = float(pesos[ok].sum() / total) if total else 0.0
    return (float(np.sum(arr[ok] * pesos[ok]) / pesos[ok].sum())
            if fraccion >= minimo and ok.any() else None), fraccion


def inventario(tareas):
    out = {}
    for t in tareas:
        p = t["producto"]
        for nombre in t.get("archivos", []):
            ruta = Path(nombre)
            if ruta.suffix.lower() != ".tif":
                continue
            # Formato por defecto API: producto_capa_doyAAAAJJJ[hhmmss]_aid....tif
            m = re.search(r"_doy(\d{7})(\d{6})?_", ruta.name)
            if not m:
                raise ValueError(f"Nombre TIFF sin fecha doy: {ruta.name}")
            fecha = datetime.strptime(m[1] + (m[2] or "000000"), "%Y%j%H%M%S").isoformat()
            capa = ruta.name[:m.start()].removeprefix(p + "_")
            key = (t["region"], p, fecha)
            dest = out.setdefault(key, {"capas": {}, "geometria": t["geometria"]})
            if capa in dest["capas"]:
                raise ValueError(f"TIFF duplicado: {key}/{capa}")
            dest["capas"][capa] = ruta
    return out


def recortar_tareas(tareas, regiones=None, exigir_estable=True):
    from rasterio.enums import Resampling
    inv = inventario(tareas)
    coberturas = {}
    for (region, p, fecha), item in sorted(inv.items()):
        if p == "MCD12Q1.061":
            c, m = leer_tif(item["capas"]["LC_Type1"], qa=True)
            q, qm = leer_tif(item["capas"]["QC"], qa=True)
            if clave_malla(m) != clave_malla(qm):
                raise ValueError("Malla QA de cobertura distinta")
            coberturas.setdefault(region, []).append((int(fecha[:4]), c, q, m))
    registros, cache_pesos, cache_estable = [], {}, {}
    for (region, p, fecha), item in sorted(inv.items()):
        if regiones is not None and region not in regiones or p == "MCD12Q1.061":
            continue
        capas, mallas = {}, {}
        cfg = PRODUCTOS[p]
        for capa in list(cfg["datos"]) + cfg["qa"]:
            capas[capa], mallas[capa] = leer_tif(item["capas"][capa], qa=capa in cfg["qa"])
        malla = mallas[next(iter(cfg["datos"]))]
        if any(clave_malla(m) != clave_malla(malla) for m in mallas.values()):
            raise ValueError("Datos y calidad deben tener malla idéntica")
        ok = mascara_calidad(p, capas)
        key = region, clave_malla(malla)
        if key not in cache_pesos:
            cache_pesos[key] = pesos_area(malla, item["geometria"])
        pesos = cache_pesos[key]
        for capa, (variable, unidad) in cfg["datos"].items():
            arr = np.asarray(capas[capa], dtype=float)
            if p.startswith("MOD13"):
                arr = np.where((arr >= -0.2) & (arr <= 1), arr, np.nan)
            elif p.startswith("MOD11"):
                arr = np.where((arr >= 150) & (arr <= 400), arr - 273.15, np.nan)
            elif p.startswith("MOD16"):
                arr = np.where((arr >= 0) & (arr <= 3270), arr, np.nan)
            else:
                arr = np.where((arr >= 0) & (arr <= 1), arr, np.nan)
            arr[~ok] = np.nan
            v, f = media_area(arr, pesos)
            registros.append(dict(region=region, variable=variable, unidad=unidad, fecha=fecha, valor=v,
                                  fraccion_area=f, producto=p, dias=cfg["dias"]))
            if p == "MOD13A3.061" and exigir_estable:
                if key not in cache_estable:
                    lista = coberturas.get(region, [])
                    periodos = [t for t in tareas if t["region"] == region and t["producto"] == p]
                    esperados = list(range(min(int(t["desde"][:4]) for t in periodos),
                                           max(int(t["hasta"][:4]) for t in periodos) + 1))
                    if not lista:
                        raise ValueError("NDVI estable requiere MCD12Q1 para todos los años")
                    base = lista[0][3]
                    if any(clave_malla(e[3]) != clave_malla(base) for e in lista):
                        raise ValueError("MCD12Q1 cambió de malla entre años")
                    estable = cobertura_estable([e[1] for e in lista], [e[2] for e in lista],
                                               [e[0] for e in lista], esperados)
                    # Solo aceptar NDVI si TODOS los subpíxeles LC son estables y misma clase.
                    c = np.where(estable, lista[0][1], 0)
                    bajo = remuestrear(c, base, malla, Resampling.min)
                    alto = remuestrear(c, base, malla, Resampling.max)
                    cache_estable[key] = (bajo == alto) & (bajo >= 1) & (alto <= 16)
                pe = np.where(cache_estable[key], pesos, 0)
                ve, fe = media_area(arr, pe)
                registros.append({**registros[-1], "variable": "ndvi_cobertura_estable", "valor": ve,
                                  "fraccion_area": fe, "fraccion_area_cohorte": float(pe.sum() / pesos.sum()) if pesos.sum() else 0})
    return registros


def agregar_registros(registros, frecuencia="mensual"):
    """Ponderar intervalos por solape mensual; ET de 8 días es acumulación, no tasa.

    Se exige 90% de cobertura temporal (100% para sumas ET) y >=50% de área válida por compuesto.
    Las medias anuales exigen 12 meses. Meses ausentes quedan null, nunca interpolados.
    """
    if frecuencia not in ("mensual", "anual"):
        raise ValueError("Frecuencia mensual o anual")
    grupos = {}
    for r in registros:
        grupos.setdefault((r["region"], r["variable"], r["unidad"], r["producto"]), []).append(r)
    out = []
    for (region, variable, unidad, producto), filas in sorted(grupos.items()):
        meses = {}
        previo_fin = None
        for r in sorted(filas, key=lambda r: r["fecha"]):
            inicio = datetime.fromisoformat(r["fecha"])
            if producto == "SPL4SMGP.008":
                inicio -= timedelta(minutes=90)  # nombre gph: centro del intervalo de tres horas
            dias = r["dias"]
            if dias is None:
                dias = calendar.monthrange(inicio.year, inicio.month)[1]
            fin = min(inicio + timedelta(days=dias), datetime(inicio.year + 1, 1, 1))
            if previo_fin is not None and inicio < previo_fin:
                raise ValueError("Intervalos duplicados o solapados")
            previo_fin = fin
            cursor = inicio
            while cursor < fin:
                siguiente = datetime(cursor.year + (cursor.month == 12), cursor.month % 12 + 1, 1)
                hasta = min(siguiente, fin)
                peso = (hasta - cursor).total_seconds() / 86400
                mes = cursor.strftime("%Y-%m")
                bloque = meses.setdefault(mes, [0.0, 0.0])
                if r["valor"] is not None and np.isfinite(r["valor"]):
                    # El último compuesto anual ET dura 5/6 días, no ocho.
                    duracion = (fin - inicio).total_seconds() / 86400
                    bloque[0] += r["valor"] * (peso / duracion if variable == "et_modis" else peso)
                    bloque[1] += peso
                cursor = hasta
        tiempos = sorted(meses)
        vals = []
        for t in tiempos:
            suma, dias = meses[t]
            dias_mes = calendar.monthrange(int(t[:4]), int(t[5:7]))[1]
            if dias > dias_mes + 1e-6:
                raise ValueError(f"Intervalos duplicados o solapados en {t}")
            minimo = dias_mes if variable == "et_modis" else 0.9 * dias_mes
            vals.append(None if dias < minimo - 1e-6 else suma if variable == "et_modis" else suma / dias)
        if frecuencia == "anual":
            tiempos, vals = a_anual(tiempos, [np.nan if v is None else v for v in vals],
                                   como="suma" if variable == "et_modis" else "media")
        notas = ["media por área de intersección EPSG:6933; QA estricto; área válida mínima 50%; cobertura temporal mensual 90% (ET: 100%)"]
        if "estable" in variable:
            notas.append("cohorte de clase IGBP constante en todos los años; subpíxeles 500 m homogéneos dentro de celda NDVI")
        if producto.startswith("SPL"):
            notas.append("SMAP L4 asimilado: AppEEARS no expone QA bitfield; filtro sin nieve/suelo descongelado, no equivale a QA L2")
        out.append(SerieRegional(region, variable, unidad, frecuencia, tiempos, vals, "appeears/" + producto,
                                 producto.split(".")[-1], notas))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("accion", choices=["plan", "enviar", "procesar"])
    parser.add_argument("--inicio", type=int, default=2001)
    parser.add_argument("--fin", type=int, default=2024)
    parser.add_argument("--geojson", type=Path, help="geometría explícita; por defecto regiones_nicaragua o regiones_canada")
    parser.add_argument("--canada", action="store_true", help="NDVI y LST; exige data/regiones_canada.geojson")
    parser.add_argument("--max-segundos", type=int, default=3600)
    args = parser.parse_args()
    a = AppEEARS()
    geo = args.geojson or (DATOS / "regiones_canada.geojson" if args.canada else REGIONES_GEOJSON)
    if not geo.exists():
        parser.error(f"Falta {geo}; no se inventa una geometría de Canadá")
    productos = ["MOD13A3.061", "MOD11A2.061"] if args.canada else None
    sufijo = "canada" if args.canada else "nicaragua"
    if args.accion == "plan":
        tareas = a.plan(args.inicio, args.fin, geo, productos)
        guardar_json(SALIDA / f"plan_{sufijo}.json", {
            "geojson": geo.name, "sha256_geojson": sha256(geo), "estado": "no_enviado",
            "tareas": [{k: v for k, v in t.items() if k not in ("geometria", "solicitud")}
                       | {"tipo": "area", "capas": t["solicitud"]["params"]["layers"]} for t in tareas]})
        print(f"Plan: {len(tareas)} tareas de área; no enviadas")
    elif args.accion == "enviar":
        tareas = a.plan(args.inicio, args.fin, geo, productos)
        ids = [{"task_id": e["task_id"], "region": e["region"], "producto": e["producto"],
                "desde": e["desde"], "hasta": e["hasta"], "enviada_utc": e["enviada_utc"]}
               for _, e in a.enviar(tareas)]
        guardar_json(SALIDA / f"tareas_{sufijo}.json", ids)
        print(f"{len(ids)} tareas enviadas/reutilizadas; ejecute procesar para esperar y descargar")
    else:
        tareas = a.descargar(args.inicio, args.fin, geo, productos, args.max_segundos)
        registros = recortar_tareas(tareas, exigir_estable=not args.canada)
        guardar_json(SALIDA / f"registros_appeears_{sufijo}.json", registros)
        for frecuencia in ("mensual", "anual"):
            guardar_json(SALIDA / f"series_appeears_{sufijo}_{frecuencia}.json",
                         [s.como_dict() for s in a.agregar(registros, frecuencia)])
        guardar_json(SALIDA / f"procedencia_{sufijo}.json", [
            {k: v for k, v in e.items() if k in ("task_id", "region", "producto", "desde", "hasta", "tiempos", "enviada_utc")}
            | {"archivos": [{"nombre": Path(p).name, "sha256": sha256(p)} for p in e["archivos"]]}
            for e in tareas])


if __name__ == "__main__":
    try:
        main()
    except (RequiereEarthdata, TimeoutError, RuntimeError, ValueError) as error:
        raise SystemExit(str(error)) from None
