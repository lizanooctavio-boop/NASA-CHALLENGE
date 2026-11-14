"""Desde raíz: python data/recursos/tierra/resumir.py. Solo datos locales; no accede a NASA.

Escribe SerieRegional de referencias y análisis con estadistica/tendencia_robusta sin modificarla.
Si están las series AppEEARS y GLDAS, añade diferencias y correlaciones descriptivas.
"""
import calendar
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "backend"))
from clima_nic.fuentes.appeears import SALIDA, guardar_json  # noqa: E402
from clima_nic.fuentes.base import SerieRegional  # noqa: E402
from clima_nic.estadistica.tendencia_robusta import analizar  # noqa: E402
from clima_nic.rutas import sha256  # noqa: E402


def referencias():
    mensual = defaultdict(list)
    archivo = RAIZ / "data/fenomenos/ndvi_modis.csv"
    with archivo.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["ndvi"]:
                mensual[(r["region"], r["fecha"][:7], "ndvi_sitio_ornl")].append(float(r["ndvi"]))
    diario = defaultdict(list)
    power = RAIZ / "data/fenomenos/serie_diaria_power.csv"
    with power.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            for var in ("gwettop", "gwetroot"):
                if r[var]:
                    diario[(r["region"], r["fecha"][:7], var)].append(float(r[var]))
    for (region, mes, variable), vals in diario.items():
        if len(vals) == calendar.monthrange(int(mes[:4]), int(mes[5:7]))[1]:
            mensual[(region, mes, variable)] = vals
    grupos = defaultdict(dict)
    for (region, mes, variable), valores in mensual.items():
        grupos[(region, variable)][mes] = float(np.mean(valores))
    series = []
    for (region, var), meses in sorted(grupos.items()):
        tiempos = sorted(meses)
        notas = (["NDVI por sitios ORNL, no media de área; original sin QA (corrida rápida modis.py)"]
                 if var == "ndvi_sitio_ornl" else
                 ["MERRA-2 vía NASA POWER; índice de humedad relativo 0–1, NO humedad volumétrica",
                  "serie regional diaria preexistente, media mensual solo con todos los días"])
        series.append(SerieRegional(region, var, "adimensional" if var.startswith("ndvi") else "0–1",
                                    "mensual", tiempos, [meses[t] for t in tiempos],
                                    "ornl/modis" if var.startswith("ndvi") else "NASA POWER/MERRA-2", "existente", notas).como_dict())
    return series, {archivo.relative_to(RAIZ).as_posix(): sha256(archivo), power.relative_to(RAIZ).as_posix(): sha256(power)}


def anual(s, desde=None, hasta=2024):
    por_anio = defaultdict(list)
    for t, v in zip(s["tiempos"], s["valores"]):
        if v is not None and np.isfinite(v) and (desde is None or int(t[:4]) >= desde) and int(t[:4]) <= hasta:
            por_anio[int(t[:4])].append(v)
    # Igual criterio de modis.py para referencia de sitio (>=10 meses); nuevas series exigen 12.
    minimo = 10 if s["variable"] == "ndvi_sitio_ornl" else 12
    return {a: float(np.sum(v) if s["unidad"] == "mm" else np.mean(v))
            for a, v in por_anio.items() if len(v) >= minimo}


def contraste(a, b, diferencia=False):
    xa = {t: v for t, v in zip(a["tiempos"], a["valores"]) if v is not None}
    xb = {t: v for t, v in zip(b["tiempos"], b["valores"]) if v is not None}
    comunes = sorted(xa.keys() & xb.keys())
    if len(comunes) < 3:
        return {"estado": "sin_solape_suficiente", "meses": len(comunes)}
    av, bv = np.array([xa[t] for t in comunes]), np.array([xb[t] for t in comunes])
    r = float(np.corrcoef(av, bv)[0, 1]) if av.std() > 0 and bv.std() > 0 else None
    resultado = {"estado": "descriptivo", "meses": len(comunes), "periodo": [comunes[0], comunes[-1]], "r_mensual": r,
                 "advertencia": "ciclo estacional y autocorrelación; no validación ni causalidad; punto frente a área"}
    if diferencia:
        resultado["diferencia_media_a_menos_b"] = float((av-bv).mean())
    return resultado


def main():
    refs, huellas = referencias()
    nuevas = []
    for archivo in ["series_appeears_nicaragua_mensual.json", "series_gldas_mensual.json", "series_appeears_canada_mensual.json"]:
        ruta = SALIDA / archivo
        if ruta.exists():
            nuevas += json.loads(ruta.read_text(encoding="utf-8"))
            huellas[archivo] = sha256(ruta)
    guardar_json(SALIDA / "series_referencia_mensual.json", refs)
    resultados = []
    for s in refs + nuevas:
        ventanas = [None, 2015] if s["variable"] in ("gwettop", "gwetroot") else [None]
        for desde in ventanas:
            vals = anual(s, desde)
            anios = sorted(vals)
            resumen = analizar(anios, [vals[a] for a in anios], s["unidad"]) if len(anios) >= 10 else {
                "veredicto": "datos_insuficientes", "anios": len(anios),
                "motivo": "menos de 10 años completos; no se calcula pendiente robusta"}
            resultados.append({"region": s["region"], "variable": s["variable"], "fuente": s["fuente"],
                               "ventana_desde": desde, "notas": s["notas"], "analisis": resumen})
    comparaciones = []
    pares = [("ndvi_regional", "ndvi_sitio_ornl", True), ("ndvi_cobertura_estable", "ndvi_sitio_ornl", True),
             ("ndvi_cobertura_estable", "ndvi_regional", True),
             ("humedad_gldas_0_10", "humedad_smap_superficial", True),
             ("humedad_gldas_10_40", "humedad_smap_raiz", False),
             ("humedad_gldas_0_10", "gwettop", False), ("humedad_smap_superficial", "gwettop", False),
             ("humedad_gldas_10_40", "gwetroot", False), ("humedad_smap_raiz", "gwetroot", False)]
    for a, b, diferencia in pares:
        for sa in nuevas:
            if sa["variable"] != a:
                continue
            for sb in refs + nuevas:
                if sb["region"] == sa["region"] and sb["variable"] == b:
                    comparaciones.append({"region": sa["region"], "a": a, "b": b,
                                          **contraste(sa, sb, diferencia)})
    guardar_json(SALIDA / "analisis.json", {"huellas_entradas": huellas, "series": resultados,
                 "contrastes": comparaciones, "estado_nuevas_series": "presentes" if nuevas else "pendientes_de_acceso_Earthdata"})
    lineas = ["| Región | Variable | Periodo | Sen / década | Veredicto |", "|---|---|---|---:|---|"]
    for r in resultados:
        a = r["analisis"]
        lineas.append(f"| {r['region']} | {r['variable']} | {a.get('periodo', 'insuficiente')} | {a.get('theil_sen', {}).get('por_decada', '—')} | {a['veredicto']} |")
    (SALIDA / "tabla_analisis.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"{len(resultados)} análisis; {len(comparaciones)} contrastes; {len(nuevas)} series nuevas")


if __name__ == "__main__":
    main()
