"""GLDAS-2.1 Noah puntual: reemplazo Giovanni del servicio Hydrology Data Rods retirado.

Earthdata token (NO token AppEEARS), o .netrc para obtener uno de URS.
Descarga por año, verifica CSV antes de cachearlo, agrega datos de 3 h.
"""
import argparse
import base64
import calendar
import csv
import json
import netrc
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

import numpy as np

from .appeears import SALIDA, guardar_json, secreto
from .base import Adaptador, RequiereEarthdata, SerieRegional, a_anual
from .earthdata import ruta_netrc, URS
from .modis import SITIOS

API = "https://api.giovanni.earthdata.nasa.gov"
HISTORICO = "https://hydro1.gesdisc.eosdis.nasa.gov/daac-bin/access/timeseries.cgi"
PREFIJO = "GLDAS_NOAH025_3H_2_1_"
VARIABLES = {
    "SoilMoi0_10cm_inst": ("humedad_gldas_0_10", "m³/m³", 100.0),
    "SoilMoi10_40cm_inst": ("humedad_gldas_10_40", "m³/m³", 300.0),
    "Evap_tavg": ("et_gldas", "mm", None),
    "Qs_acc": ("escorrentia_superficial_gldas", "mm", None),
    "Qsb_acc": ("escorrentia_subterranea_gldas", "mm", None),
}


def url_serie(variable, lat, lon, inicio, fin):
    if variable not in VARIABLES or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("Variable o coordenadas no válidas")
    q = urllib.parse.urlencode({"data": PREFIJO + variable, "location": f"[{lat},{lon}]",
                               "time": f"{inicio}/{fin}", "version": "2.0"})
    return API + "/timeseries?" + q


def leer_csv(texto):
    """Metadatos key,value + línea vacía + CSV Timestamp,Data; rechaza HTML y duplicados."""
    if texto.lstrip().startswith(("<", "{")):
        raise ValueError("El servicio devolvió HTML/JSON, no una serie CSV de Giovanni")
    lineas = texto.splitlines()
    cabecera = next((i for i, l in enumerate(lineas)
                     if len(next(csv.reader([l]), [])) == 2
                     and next(csv.reader([l]))[-1].strip() == "Data"), None)
    if cabecera is None:
        raise ValueError("CSV sin cabecera Timestamp,Data; no se guarda como datos")
    meta = {}
    for l in lineas[:cabecera]:
        if l.strip() and "," in l:
            k, v = next(csv.reader([l]))[:2]
            meta[k.strip()] = v.strip()
    relleno = float(meta.get("undef", "-9999"))
    filas = list(csv.reader(lineas[cabecera + 1:]))
    puntos = {}
    for fila in filas:
        if not fila:
            continue
        if len(fila) != 2:
            raise ValueError("Fila Giovanni no tiene dos columnas")
        t = datetime.fromisoformat(fila[0].strip().replace("Z", "+00:00"))
        if t.tzinfo is not None:
            from datetime import timezone
            t = t.astimezone(timezone.utc).replace(tzinfo=None)
        valor = float(fila[1]) if fila[1].strip() else np.nan
        if t in puntos:
            raise ValueError("Marca temporal Giovanni duplicada")
        puntos[t] = np.nan if valor == relleno or not np.isfinite(valor) else valor
    if not puntos:
        raise ValueError("CSV sin observaciones")
    tiempos = sorted(puntos)
    if any((b - a).total_seconds() % 10800 != 0 for a, b in zip(tiempos, tiempos[1:])):
        raise ValueError("Se esperaba una serie GLDAS de 3 horas")
    return meta, tiempos, [puntos[t] for t in tiempos]


class GldasDatarods(Adaptador):
    id = "gldas_datarods"
    nombre = "GLDAS-2.1 Noah, punto (Giovanni; sustituye Hydrology Data Rods)"
    producto = "GLDAS_NOAH025_3H"
    version = "2.1"
    variables = {v: u for v, u, _ in VARIABLES.values()}
    resolucion_espacial = "0.25°; un punto/celda por región, no media regional"
    resolucion_temporal = "3 horas → mensual/anual"
    periodo = "2000-01 a la fecha"
    requiere_earthdata = True
    acceso = "Giovanni Cloud timeseries, Earthdata Bearer; data rods histórico retirado"
    documentacion = "https://github.com/nasa/gesdisc-tutorials/blob/main/user-guidance/GES_DISC_Migration_to_Earthdata_Website_and_Earthdata_Cloud.md"
    fenomenos = ("humedad_suelo", "evapotranspiracion", "escorrentia")

    def __init__(self, token=None):
        self._token = token

    def autenticar(self):
        self._token = self._token or secreto("EARTHDATA_TOKEN")
        if self._token:
            return
        r = ruta_netrc()
        auth = netrc.netrc(str(r)).authenticators(URS) if r else None
        if not auth:
            raise RequiereEarthdata("Giovanni requiere EARTHDATA_TOKEN o .netrc/_netrc (urs.earthdata.nasa.gov), distinto de APPEEARS_TOKEN")
        usuario, _, clave = auth
        basic = base64.b64encode(f"{usuario}:{clave}".encode()).decode()
        req = urllib.request.Request("https://urs.earthdata.nasa.gov/api/users/find_or_create_token", data=b"",
                                     headers={"Authorization": "Basic " + basic, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                self._token = json.load(res)["access_token"]
        except urllib.error.HTTPError as e:
            raise RequiereEarthdata(f"URS HTTP {e.code}; revise credenciales y aplicaciones autorizadas") from None

    def disponible(self):
        from .earthdata import hay_credenciales
        ok = bool(self._token or secreto("EARTHDATA_TOKEN") or hay_credenciales())
        return ok, "credencial presente; validar con Giovanni" if ok else "falta token Earthdata o netrc"

    def descargar(self, inicio, fin, sitios=None, **kw):
        if inicio < 2000 or fin < inicio:
            raise ValueError("GLDAS-2.1 empieza en 2000")
        sitios = sitios or {r: s[0] for r, s in SITIOS.items()}
        with urllib.request.urlopen(API + "/configured-variables", timeout=60) as res:
            catalogo = json.load(res)["configured_variables"]
        if not all(PREFIJO + v in catalogo for v in VARIABLES):
            raise ValueError("El catálogo Giovanni ya no ofrece todas las variables GLDAS pedidas")
        self.autenticar()
        tareas = []
        for region, (sitio, lat, lon) in sitios.items():
            for variable in VARIABLES:
                for anio in range(inicio, fin + 1):
                    destino = self.cache() / f"{sitio}_{lat}_{lon}_{variable}_{anio}.csv"
                    url = url_serie(variable, lat, lon, f"{anio}-01-01T00:00:00", f"{anio}-12-31T23:59:59")
                    if destino.exists():
                        leer_csv(destino.read_text(encoding="utf-8"))
                    else:
                        req = urllib.request.Request(url, headers={"Authorization": "Bearer " + self._token})
                        try:
                            with urllib.request.urlopen(req, timeout=180) as res:
                                contenido = res.read().decode("utf-8-sig")
                            leer_csv(contenido)
                        except urllib.error.HTTPError as e:
                            if e.code in (401, 403):
                                raise RequiereEarthdata(f"Giovanni HTTP {e.code}; renueve Earthdata token y autorice GES DISC") from None
                            raise RuntimeError(f"Giovanni HTTP {e.code}; descargas anteriores guardadas en caché") from None
                        tmp = destino.with_suffix(".parcial")
                        tmp.write_text(contenido, encoding="utf-8")
                        tmp.replace(destino)
                    tareas.append({"region": region, "sitio": sitio, "lat": lat, "lon": lon,
                                   "variable": variable, "archivo": str(destino), "url": url})
        return tareas

    def recortar(self, archivos, regiones=None):
        out = []
        for t in archivos:
            if regiones is not None and t["region"] not in regiones:
                continue
            meta, tiempos, valores = leer_csv(Path(t["archivo"]).read_text(encoding="utf-8"))
            out.append({**t, "meta": meta, "tiempos": tiempos, "valores": valores})
        return out

    def agregar(self, recortado, frecuencia="mensual"):
        if frecuencia not in ("mensual", "anual"):
            raise ValueError("Frecuencia mensual o anual")
        grupos = {}
        for t in recortado:
            key = t["region"], t["sitio"], t["variable"]
            g = grupos.setdefault(key, {"datos": {}, "tarea": t})
            for fecha, valor in zip(t["tiempos"], t["valores"]):
                if fecha in g["datos"]:
                    raise ValueError("Bloques GLDAS solapados")
                g["datos"][fecha] = valor
        out = []
        for (region, sitio, variable), g in sorted(grupos.items()):
            nombre, unidad, espesor = VARIABLES[variable]
            meses = {}
            for fecha, v in sorted(g["datos"].items()):
                mes = fecha.strftime("%Y-%m")
                bloque = meses.setdefault(mes, [])
                if np.isfinite(v):
                    # kg m-2 / (1000 kg m-3 * espesor m) → m3/m3
                    if espesor:
                        v /= espesor
                        if v < 0 or v > 1:
                            continue
                    elif variable == "Evap_tavg":
                        v *= 10800  # kg m-2 s-1 → mm / intervalo de 3 horas
                    elif v < 0:
                        continue
                    bloque.append(v)
            tiempos = sorted(meses)
            vals = []
            for mes in tiempos:
                valores = meses[mes]
                esperados = calendar.monthrange(int(mes[:4]), int(mes[5:7]))[1] * 8
                vals.append(None if len(valores) != esperados else
                            float(np.mean(valores) if espesor else np.sum(valores)))
            if frecuencia == "anual":
                tiempos, vals = a_anual(tiempos, [np.nan if v is None else v for v in vals],
                                       como="media" if espesor else "suma")
            t = g["tarea"]
            notas = [f"Serie de PUNTO {sitio} ({t['lat']}, {t['lon']}), celda Noah 0.25°; no media regional",
                     f"coordenadas devueltas por Giovanni: {t['meta'].get('lat', '?')}, {t['meta'].get('lon', '?')}",
                     "meses exigen todos los intervalos de 3 h; años exigen 12 meses; sin interpolar",
                     "GLDAS es modelo; sin bitfield QA; se excluyen undef y valores no físicos"]
            out.append(SerieRegional(region, nombre, unidad, frecuencia, tiempos, vals, self.id, self.version, notas))
        return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inicio", type=int, default=2001)
    p.add_argument("--fin", type=int, default=2024)
    args = p.parse_args()
    a = GldasDatarods()
    tareas = a.descargar(args.inicio, args.fin)
    recortado = a.recortar(tareas)
    for frecuencia in ("mensual", "anual"):
        guardar_json(SALIDA / f"series_gldas_{frecuencia}.json", [s.como_dict() for s in a.agregar(recortado, frecuencia)])
    from ..rutas import sha256
    guardar_json(SALIDA / "procedencia_gldas.json", [{k: v for k, v in t.items() if k != "archivo"}
                                                  | {"sha256": sha256(t["archivo"])} for t in tareas])


if __name__ == "__main__":
    try:
        main()
    except (RequiereEarthdata, RuntimeError, ValueError) as error:
        raise SystemExit(str(error)) from None
