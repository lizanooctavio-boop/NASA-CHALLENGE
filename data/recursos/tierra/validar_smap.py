"""Audita SMAP superficial frente a GLDAS regional sin consultar la red ni escribir datos.

Uso: python data/recursos/tierra/validar_smap.py
"""
import calendar
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[2] / "backend"))
from clima_nic.estadistica.tendencia_robusta import theil_sen  # noqa: E402
from clima_nic.fuentes.base import a_anual  # noqa: E402

SMAP = "humedad_smap_superficial"
GLDAS = "humedad_gldas_0_10"


def leer(nombre):
    return json.loads((AQUI / nombre).read_text(encoding="utf-8"))


def por_mes(serie):
    return dict(zip(serie["tiempos"], serie["valores"], strict=True))


def periodo_mensual(desde, hasta):
    anio, mes = map(int, desde.split("-"))
    while (etiqueta := f"{anio:04d}-{mes:02d}") <= hasta:
        yield etiqueta
        anio, mes = anio + (mes == 12), mes % 12 + 1


def auditar(smap, gldas, registros, procedencia):
    region = smap["region"]
    if smap["unidad"] != "m³/m³" or (gldas and gldas["unidad"] != smap["unidad"]):
        raise ValueError("El contraste requiere ambas series en m³/m³")
    tareas = [t for t in procedencia if t["region"] == region and t["producto"] == "SPL4SMGP.008"]
    if not tareas:
        raise ValueError(f"Falta la procedencia SMAP para {region}")
    meses = list(periodo_mensual(min(t["desde"] for t in tareas)[:7], max(t["hasta"] for t in tareas)[:7]))
    s, g = por_mes(smap), por_mes(gldas) if gldas else {}
    filas = [r for r in registros if r["region"] == region and r["variable"] == SMAP]
    disponibles = Counter(r["fecha"][:7] for r in filas)
    aceptados = Counter(r["fecha"][:7] for r in filas if r["valor"] is not None)
    vals = [s[m] for m in meses if s.get(m) is not None]
    lapsos = [r["valor"] for r in filas if r["valor"] is not None]
    if not vals or not lapsos or not np.isfinite(vals + lapsos).all():
        raise ValueError(f"SMAP sin datos válidos o con valores no finitos para {region}")
    huecos = {}
    for m in meses:
        if s.get(m) is None:
            anio, mes = map(int, m.split("-"))
            huecos[m] = {"validos_3h": aceptados[m], "presentes_3h": disponibles[m],
                         "esperados_3h": 8 * calendar.monthrange(anio, mes)[1]}
    comunes = [m for m in meses if s.get(m) is not None and g.get(m) is not None]
    comparacion = None
    if len(comunes) >= 2:
        x = np.array([s[m] for m in comunes])
        y = np.array([g[m] for m in comunes])
        r = float(np.corrcoef(x, y)[0, 1]) if np.std(x) > 0 and np.std(y) > 0 else None
        # Centrar cada mes del calendario dentro de la ventana común reduce el efecto del ciclo anual.
        calendario = np.array([int(m[5:7]) for m in comunes])
        ax, ay = [], []
        for mes in np.unique(calendario):
            grupo = calendario == mes
            if np.count_nonzero(grupo) >= 2:
                ax.extend(x[grupo] - x[grupo].mean())
                ay.extend(y[grupo] - y[grupo].mean())
        r_anom = float(np.corrcoef(ax, ay)[0, 1]) if ax and np.std(ax) > 0 and np.std(ay) > 0 else None
        anios, a = a_anual(comunes, x, como="media")
        _, b = a_anual(comunes, y, como="media")
        sen = [theil_sen(anios, v)["por_decada"] for v in (a, b)] if len(anios) >= 3 else None
        comparacion = {"periodo": [comunes[0], comunes[-1]], "pares_mensuales": len(comunes),
                       "pearson_r_mensual": r, "pearson_r_anomalias": r_anom, "pares_anomalias": len(ax),
                       "sesgo_smap_menos_gldas": float(np.mean(x - y)),
                       "anios_completos_comunes": anios, "sen_smap_y_gldas_por_decada": sen}
    estaciones = {}
    for nombre, seleccion in (("mayo_octubre", range(5, 11)), ("noviembre_abril", (11, 12, 1, 2, 3, 4))):
        valores = [s[m] for m in meses if s.get(m) is not None and int(m[5:]) in seleccion]
        estaciones[nombre] = {"meses": len(valores), "media": float(np.mean(valores)) if valores else None}
    validos = [m for m in meses if s.get(m) is not None]
    return {"region": region, "estado": "NO_VALIDADA", "periodo_mensual": [validos[0], validos[-1]],
            "meses_validos": len(validos), "huecos": huecos, "rango_3h": [min(lapsos), max(lapsos)],
            "rango_mensual": [min(vals), max(vals)], "estaciones": estaciones, "gldas": comparacion}


if __name__ == "__main__":
    gldas = {s["region"]: s for s in leer("series_gldas_mensual.json") if s["variable"] == GLDAS}
    registros = leer("registros_appeears_nicaragua.json")
    procedencia = leer("procedencia_nicaragua.json")
    series = leer("series_appeears_nicaragua_mensual.json")
    salida = [auditar(s, gldas.get(s["region"]), registros, procedencia) for s in series if s["variable"] == SMAP]
    if not salida:
        raise SystemExit("No hay series de humedad superficial SMAP para auditar")
    print(json.dumps(salida, indent=2, ensure_ascii=False, allow_nan=False))
