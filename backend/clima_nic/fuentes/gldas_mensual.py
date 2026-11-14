"""GLDAS-2.1 Noah mensual (GLDAS_NOAH025_M 2.1) con medias regionales ponderadas por área.

Sustituye a la serie de punto de Hydrology Time Series mientras ese servicio falle (500 en la API de series y
«Failed to fetch subset job link contents» en su visor, 13-11-2026). Lee el mismo conjunto de datos GLDAS desde el
OPeNDAP en la nube de GES DISC, que permite recortar por índice sin bajar el archivo global de 24 MB por mes.
El OPeNDAP antiguo (hydro1.gesdisc.eosdis.nasa.gov/opendap) responde 410 y no se usa.

Acceso: Earthdata con `.netrc`/`_netrc` (fuentes/earthdata.abridor); nada se imprime ni se guarda de las credenciales.
Las respuestas crudas van a backend/.cache/gldas_mensual/ (no versionada). Salidas en data/recursos/tierra/.

Conversiones (GLDAS-2 README; variables mensuales con «cell_methods: time: mean»):
    SoilMoi0_10cm_inst  kg m-2 → m³/m³: ÷ 100 (agua de 0,10 m)       media anual de 12 meses
    SoilMoi10_40cm_inst kg m-2 → m³/m³: ÷ 300 (agua de 0,30 m)       media anual de 12 meses
    Evap_tavg, Rainf_f_tavg  kg m-2 s-1 → mm/mes: × segundos del mes   suma anual
    Qs_acc, Qsb_acc  kg m-2 por paso de 3 h, promediado en el mes → mm/mes: × 8 × días del mes   suma anual
La lluvia de GLDAS (forzante) solo se usa para el balance hídrico de control, no como variable de la interfaz.

Uso:
    python -m clima_nic.fuentes.gldas_mensual --inicio 2001 --fin 2024
"""
import argparse
import calendar
import hashlib
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .. import regiones as reg
from ..rutas import CACHE, DATOS
from .appeears import SALIDA, guardar_json
from .base import SerieRegional, recortar_malla
from .earthdata import abridor

COLECCION = "C1342986036-GES_DISC"
PRODUCTO = "GLDAS_NOAH025_M 2.1"
VARIABLES = ["SoilMoi0_10cm_inst", "SoilMoi10_40cm_inst", "Evap_tavg", "Qs_acc", "Qsb_acc", "Rainf_f_tavg"]
RELLENO = -9999.0
# Malla global de 0,25°: lat[i] = −59,875 + 0,25 i (600), lon[j] = −179,875 + 0,25 j (1440)
LAT0, LON0, PASO = -59.875, -179.875, 0.25
# Ventanas de índices (inclusive) que cubren cada grupo de regiones con una celda de margen
VENTANAS = {
    "nicaragua": {"lat": (282, 301), "lon": (367, 390), "geojson": DATOS / "regiones_nicaragua.geojson"},
    "canada": {"lat": (434, 458), "lon": (259, 335), "geojson": SALIDA / "regiones_canada_agente3.geojson"},
}
SALIDAS = {
    "humedad_gldas_0_10": ("SoilMoi0_10cm_inst", "m³/m³", "media"),
    "humedad_gldas_10_40": ("SoilMoi10_40cm_inst", "m³/m³", "media"),
    "et_gldas": ("Evap_tavg", "mm", "suma"),
    "escorrentia_superficial_gldas": ("Qs_acc", "mm", "suma"),
    "escorrentia_subterranea_gldas": ("Qsb_acc", "mm", "suma"),
}
CACHE_GLDAS = CACHE / "gldas_mensual"


def url_granulo(anio, mes):
    nombre = f"GLDAS_NOAH025_M.A{anio:04d}{mes:02d}.021.nc4"
    return f"https://opendap.earthdata.nasa.gov/collections/{COLECCION}/granules/GLDAS_NOAH025_M.2.1%3A{nombre}", nombre


def url_recorte(anio, mes, ventana):
    base, _ = url_granulo(anio, mes)
    (a, b), (c, d) = ventana["lat"], ventana["lon"]
    ce = ";".join([f"/lat[{a}:1:{b}]", f"/lon[{c}:1:{d}]"] + [f"/{v}[0:1:0][{a}:1:{b}][{c}:1:{d}]" for v in VARIABLES])
    return base + ".dap.csv?dap4.ce=" + urllib.parse.quote(ce, safe="")


def leer_csv_dap(texto):
    """CSV de DAP4 → (lat, lon, {variable: matriz (lat, lon)}). Rechaza respuestas incompletas."""
    lat = lon = None
    filas = {}
    for linea in texto.splitlines():
        if not linea.startswith("/"):
            continue
        nombre, _, resto = linea.partition(",")
        valores = np.array([float(x) for x in resto.split(",")])
        if nombre == "/lat":
            lat = valores
        elif nombre == "/lon":
            lon = valores
        else:
            var, indices = nombre[1:].split("[", 1)
            fila = int(indices.split("][")[1].rstrip("]"))
            filas.setdefault(var, {})[fila] = valores
    if lat is None or lon is None or set(filas) != set(VARIABLES):
        raise ValueError("Respuesta OPeNDAP incompleta: faltan coordenadas o variables")
    campos = {}
    for var, por_fila in filas.items():
        if sorted(por_fila) != list(range(len(lat))) or any(len(v) != len(lon) for v in por_fila.values()):
            raise ValueError(f"Respuesta OPeNDAP incompleta en {var}")
        m = np.stack([por_fila[i] for i in range(len(lat))])
        campos[var] = np.where(np.isclose(m, RELLENO), np.nan, m)
    return lat, lon, campos


def descargar_mes(anio, mes, grupo, op, reintentos=3):
    """Descarga (o reutiliza de la caché) el recorte de un mes. Devuelve (ruta, sha256, url)."""
    ruta = CACHE_GLDAS / grupo / f"{anio:04d}{mes:02d}.csv"
    url = url_recorte(anio, mes, VENTANAS[grupo])
    if not ruta.exists():
        ultimo = None
        for _ in range(reintentos):
            try:
                with op.open(url, timeout=240) as r:
                    texto = r.read().decode("utf-8")
                leer_csv_dap(texto)
                ruta.parent.mkdir(parents=True, exist_ok=True)
                tmp = ruta.with_suffix(".parcial")
                tmp.write_text(texto, encoding="utf-8")
                tmp.replace(ruta)
                break
            except Exception as e:  # red o respuesta incompleta: se reintenta y, si persiste, se informa
                ultimo = e
        else:
            raise RuntimeError(f"No se pudo descargar GLDAS {anio}-{mes:02d} ({grupo}): {ultimo}")
    return ruta, hashlib.sha256(ruta.read_bytes()).hexdigest(), url


def a_mensual_fisico(var, valor, anio, mes):
    dias = calendar.monthrange(anio, mes)[1]
    if var.startswith("SoilMoi0_10"):
        return valor / 100.0
    if var.startswith("SoilMoi10_40"):
        return valor / 300.0
    if var.endswith("_tavg"):
        return valor * dias * 86400.0
    if var.endswith("_acc"):
        return valor * 8 * dias
    raise ValueError(var)


def series_grupo(grupo, inicio, fin, hilos=6):
    meses = [(a, m) for a in range(inicio, fin + 1) for m in range(1, 13)]
    op = abridor()
    with ThreadPoolExecutor(hilos) as ex:
        descargas = list(ex.map(lambda am: descargar_mes(am[0], am[1], grupo, op), meses))
    regiones = reg.cargar(VENTANAS[grupo]["geojson"])
    pesos = None
    mensual = {}   # (region, var) → lista por mes
    cobertura = {}  # region → fracción de peso con dato, por mes
    for (anio, mes), (ruta, _, _) in zip(meses, descargas):
        lat, lon, campos = leer_csv_dap(ruta.read_text(encoding="utf-8"))
        for var in VARIABLES:
            medias, pesos = recortar_malla(lat, lon, campos[var], regiones, pesos)
            for region, serie in medias.items():
                mensual.setdefault((region, var), []).append(a_mensual_fisico(var, float(serie[0]), anio, mes))
        validos = np.isfinite(campos["SoilMoi0_10cm_inst"])
        ilat = {round(float(v), 4): i for i, v in enumerate(lat)}
        ilon = {round(float(v), 4): i for i, v in enumerate(lon)}
        for region in regiones:
            w = np.array([p[region] for p in pesos])
            ok = np.array([validos[ilat[p["lat"]], ilon[p["lon"]]] for p in pesos])
            cobertura.setdefault(region, []).append(float(w[ok].sum() / w.sum()))
    procedencia = [{"mes": f"{a}-{m:02d}", "granulo": url_granulo(a, m)[1], "sha256_respuesta": h}
                   for (a, m), (_, h, _) in zip(meses, descargas)]
    return meses, mensual, cobertura, procedencia, len(pesos)


def construir(inicio=2001, fin=2024, hilos=6):
    consulta = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    mens, anu, balance, procedencia = [], [], {}, {}
    for grupo in VENTANAS:
        meses, mensual, cobertura, proc, n_celdas = series_grupo(grupo, inicio, fin, hilos)
        procedencia[grupo] = {"celdas_con_peso": n_celdas, "ejemplo_url": url_recorte(inicio, 1, VENTANAS[grupo]),
                              "ventana_indices": {k: VENTANAS[grupo][k] for k in ("lat", "lon")}, "consultas": proc}
        tiempos = [f"{a}-{m:02d}" for a, m in meses]
        for region in sorted({r for r, _ in mensual}):
            notas = [f"Media ponderada por área (EPSG:6933) de las celdas de 0,25° de GLDAS dentro de {region}; "
                     f"las celdas sin suelo del modelo (agua) se excluyen renormalizando los pesos.",
                     f"Cobertura mínima de celdas con dato: {min(cobertura[region]):.3f} del área de la región.",
                     f"Consulta OPeNDAP en la nube de GES DISC, {consulta}.",
                     "GLDAS-2.1 empieza en 2000: 2001 conserva ajuste de almacenamiento (residuo del balance alto ese año).",
                     "El README de GLDAS-2 advierte un desplazamiento de origen desconocido en la radiación AGRMET "
                     "después de 2011 y reescalados desde 2008: un salto en 2008–2013 puede ser artefacto del forzamiento "
                     "y no un cambio climático. Contrastar con SMAP y MERRA-2 antes de interpretar una tendencia."]
            for salida, (var, unidad, como) in SALIDAS.items():
                vals = mensual[(region, var)]
                fuente = f"GES DISC {PRODUCTO} (OPeNDAP en la nube), media regional"
                mens.append(SerieRegional(region, salida, unidad, "mensual", tiempos, vals, fuente, "2.1", notas))
                anios, valores = [], []
                for a in range(inicio, fin + 1):
                    x = np.array(vals[(a - inicio) * 12:(a - inicio + 1) * 12], float)
                    if np.all(np.isfinite(x)):
                        anios.append(a)
                        valores.append(round(float(x.mean() if como == "media" else x.sum()), 6))
                anu.append(SerieRegional(region, salida, unidad, "anual", anios, valores, fuente, "2.1", notas))
            # Balance hídrico de control: P − ET − Qs − Qsb ≈ variación de almacenamiento (pequeña en un año)
            p = np.array(mensual[(region, "Rainf_f_tavg")]).reshape(-1, 12).sum(1)
            et = np.array(mensual[(region, "Evap_tavg")]).reshape(-1, 12).sum(1)
            q = (np.array(mensual[(region, "Qs_acc")]) + np.array(mensual[(region, "Qsb_acc")])).reshape(-1, 12).sum(1)
            balance[region] = {"lluvia_media_mm": round(float(p.mean()), 1), "et_media_mm": round(float(et.mean()), 1),
                               "escorrentia_media_mm": round(float(q.mean()), 1),
                               "residuo_medio_mm": round(float((p - et - q).mean()), 1),
                               "residuo_relativo": round(float((p - et - q).mean() / p.mean()), 4)}
    guardar_json(SALIDA / "series_gldas_mensual.json", [s.como_dict() for s in mens])
    guardar_json(SALIDA / "series_gldas_anual.json", [s.como_dict() for s in anu])
    guardar_json(SALIDA / "procedencia_gldas_mensual.json", {
        "producto": PRODUCTO, "coleccion_cmr": COLECCION, "consulta_utc": consulta, "periodo": [inicio, fin],
        "variables": VARIABLES, "balance_hidrico_control": balance, "grupos": procedencia})
    return balance


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inicio", type=int, default=2001)
    ap.add_argument("--fin", type=int, default=2024)
    ap.add_argument("--hilos", type=int, default=6)
    a = ap.parse_args()
    print(json.dumps(construir(a.inicio, a.fin, a.hilos), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
