"""MODIS: NDVI (MOD13Q1, 250 m, 16 días) y temperatura de superficie (MOD11A2, 1 km, 8 días).

Ruta sin cuenta: el servicio web de subconjuntos del ORNL DAAC (modis.ornl.gov/rst/api/v1), que devuelve los
píxeles alrededor de un punto (máximo 10 fechas por solicitud). Se muestrea una ventana de 3 × 3 km en dos
sitios representativos por región (no es una media regional completa: para eso hace falta AppEEARS o los
gránulos de LP DAAC, con cuenta Earthdata). Calidad: solo píxeles con fiabilidad 0 (buena) o 1 (marginal).

El NDVI describe la respuesta de la vegetación a la sequía, pero también cambia con el uso del suelo
(deforestación, agricultura): una tendencia de NDVI no es por sí sola una señal climática.
"""
import csv
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from ..rutas import FENOMENOS
from .base import Adaptador, SerieRegional, descargar_url

API = "https://modis.ornl.gov/rst/api/v1"
PRODUCTOS = {
    "MOD13Q1": {"banda": "250m_16_days_NDVI", "calidad": "250m_16_days_pixel_reliability", "escala": 1e-4,
                "validos": (0, 1), "relleno": -3000},
    "MOD11A2": {"banda": "LST_Day_1km", "calidad": None, "escala": 0.02, "desplazamiento": -273.15,
                "validos": None, "relleno": 0},
}
# Dos sitios por región, en zonas agrícolas o de vegetación representativas (lat, lon)
SITIOS = {
    "pacifico": [("leon_llanura", 12.45, -86.85), ("rivas_istmo", 11.45, -85.85)],
    "central": [("esteli_corredor_seco", 13.10, -86.35), ("chontales_juigalpa", 12.10, -85.35)],
    "caribe": [("siuna_bosque", 13.75, -84.80), ("bluefields_interior", 12.05, -84.10)],
}
# Subconjunto usado en la corrida del 12-11-2026: el servicio ORNL respondió a ~5 solicitudes/min, así que se
# tomó un sitio por región y solo la banda NDVI (sin la de fiabilidad; se excluye solo el valor de relleno).
SITIOS_RAPIDOS = {k: v[:1] for k, v in SITIOS.items()}


class Modis(Adaptador):
    id = "modis"
    nombre = "MODIS Terra (MOD13Q1 NDVI, MOD11A2 LST) vía ORNL DAAC"
    producto = "MOD13Q1 / MOD11A2"
    version = "C6.1"
    variables = {"NDVI": "adimensional", "LST_dia": "°C"}
    resolucion_espacial = "250 m (NDVI), 1 km (LST); muestreo de 3 × 3 km por sitio"
    resolucion_temporal = "16 días (NDVI), 8 días (LST)"
    periodo = "2000-02 a la fecha"
    requiere_earthdata = False
    acceso = "servicio web ORNL DAAC (sin cuenta); AppEEARS/LP DAAC con cuenta para medias regionales"
    documentacion = "https://modis.ornl.gov/data/modis_webservice.html"
    fenomenos = ("vegetacion", "temperatura_superficie")

    def fechas(self, producto, lat, lon):
        url = f"{API}/{producto}/dates?latitude={lat}&longitude={lon}"
        r = descargar_url(url, self.cache() / f"fechas_{producto}_{lat}_{lon}.json", validar_json=True)
        return [d["modis_date"] for d in json.loads(r.read_text(encoding="utf-8"))["dates"]]

    def descargar(self, inicio, fin, producto="MOD13Q1", sitios=SITIOS, hilos=4, con_calidad=True, **kw):
        cfg = PRODUCTOS[producto]
        tareas = []
        for region, lista in sitios.items():
            for nombre, lat, lon in lista:
                fechas = [f for f in self.fechas(producto, lat, lon) if inicio <= int(f[1:5]) <= fin]
                for banda in [b for b in (cfg["banda"], cfg["calidad"] if con_calidad else None) if b]:
                    for i in range(0, len(fechas), 10):
                        bloque = fechas[i:i + 10]
                        q = urllib.parse.urlencode({"latitude": lat, "longitude": lon, "band": banda,
                                                    "startDate": bloque[0], "endDate": bloque[-1],
                                                    "kmAboveBelow": 1, "kmLeftRight": 1})
                        destino = self.cache() / producto / f"{nombre}_{banda}_{bloque[0]}_{bloque[-1]}.json"
                        tareas.append((region, nombre, banda, f"{API}/{producto}/subset?{q}", destino))
        with ThreadPoolExecutor(hilos) as ex:
            list(ex.map(lambda t: descargar_url(t[3], t[4], validar_json=True), tareas))
        return tareas

    def recortar(self, tareas, regiones=None, producto="MOD13Q1"):
        """Media de los píxeles válidos de cada sitio por fecha: {region: {sitio: {fecha: valor}}}."""
        cfg = PRODUCTOS[producto]
        crudo = {}
        for region, nombre, banda, _, ruta in tareas:
            d = json.loads(ruta.read_text(encoding="utf-8"))
            for s in d["subset"]:
                crudo.setdefault((region, nombre, s["calendar_date"]), {})[banda] = np.array(s["data"], float)
        out = {}
        for (region, nombre, fecha), b in crudo.items():
            v = b.get(cfg["banda"])
            if v is None:
                continue
            ok = v != cfg["relleno"]
            if cfg["calidad"] and cfg["calidad"] in b:
                ok &= np.isin(b[cfg["calidad"]], cfg["validos"])
            valor = float(v[ok].mean() * cfg["escala"] + cfg.get("desplazamiento", 0)) if ok.sum() >= 3 else np.nan
            out.setdefault(region, {}).setdefault(nombre, {})[fecha] = valor
        return out

    def agregar(self, recortado, frecuencia="anual", variable="NDVI"):
        out = []
        for region, sitios in recortado.items():
            por_mes = {}
            for serie in sitios.values():
                for fecha, v in serie.items():
                    if np.isfinite(v):
                        por_mes.setdefault(fecha[:7], []).append(v)
            meses = sorted(por_mes)
            vals = [float(np.mean(por_mes[m])) for m in meses]
            if frecuencia == "mensual":
                out.append(SerieRegional(region, variable, self.variables[variable], "mensual", meses, vals, self.id, self.version))
            else:
                por_anio = {}
                for m, v in zip(meses, vals):
                    por_anio.setdefault(int(m[:4]), []).append(v)
                anios = [a for a in sorted(por_anio) if len(por_anio[a]) >= 10]
                out.append(SerieRegional(region, variable, self.variables[variable], "anual", anios,
                                         [float(np.mean(por_anio[a])) for a in anios], self.id, self.version,
                                         ["media anual de los meses con dato (≥ 10 meses)"]))
        return out


def escribir_derivados(inicio=2000, fin=2024, hilos=8, salida=FENOMENOS, sitios=SITIOS_RAPIDOS, con_calidad=False):
    a = Modis()
    tareas = a.descargar(inicio, fin, "MOD13Q1", sitios=sitios, hilos=hilos, con_calidad=con_calidad)
    rec = a.recortar(tareas)
    salida.mkdir(parents=True, exist_ok=True)
    with (salida / "ndvi_modis.csv").open("w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["region", "sitio", "fecha", "ndvi"])
        for region, sitios in rec.items():
            for nombre, serie in sitios.items():
                for fecha in sorted(serie):
                    v = serie[fecha]
                    w.writerow([region, nombre, fecha, "" if not np.isfinite(v) else f"{v:.4f}"])
    print(f"NDVI: {sum(len(s) for r in rec.values() for s in r.values())} valores")
