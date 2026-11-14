"""Contraste de la humedad del suelo de GLDAS-2.1 con MERRA-2 (y con SMAP cuando existan sus series).

Entradas: data/recursos/tierra/series_gldas_anual.json, data/fenomenos/serie_diaria_power.csv (MERRA-2 GWETTOP y
GWETROOT por región, vía NASA POWER) y, si existe, series_appeears_nicaragua_anual.json (SMAP L4).
Salidas, con el esquema de contrastes del agente 2: contrastes_tierra.json y contrastes_tierra_series.csv.

GWETTOP (0–5 cm) y GWETROOT (zona radicular) son índices de saturación de 0 a 1; GLDAS da m³/m³. Por eso las
series se comparan como anomalías estandarizadas (z) y cada tendencia se calcula en sus propias unidades.
Correlación descriptiva: series anuales, sin corrección por autocorrelación.

    python data/recursos/tierra/contrastar_humedad.py
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "backend"))
from clima_nic.estadistica import tendencia_robusta as tr  # noqa: E402

AQUI = Path(__file__).resolve().parent
PERIODO = (2001, 2024)
PARES = [("humedad_gldas_0_10", "gwettop", "MERRA-2 surface soil wetness (GWETTOP), regional mean", "0–5 cm wetness index"),
         ("humedad_gldas_10_40", "gwetroot", "MERRA-2 root-zone soil wetness (GWETROOT), regional mean", "root-zone wetness index")]
PARES_SMAP = [("humedad_gldas_0_10", "humedad_smap_superficial", "NASA SMAP L4 surface soil moisture via AppEEARS"),
              ("humedad_gldas_10_40", "humedad_smap_raiz", "NASA SMAP L4 root-zone soil moisture via AppEEARS")]
VEREDICTO_EN = {"tendencia_detectada": "trend detected", "evidencia_insuficiente": "insufficient evidence",
                "metodos_discrepan": "methods disagree", "datos_insuficientes": "not enough data"}


def merra2_anual():
    por = {}
    with (RAIZ / "data" / "fenomenos" / "serie_diaria_power.csv").open(encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            anio = int(fila["fecha"][:4])
            if PERIODO[0] <= anio <= PERIODO[1]:
                for var in ("gwettop", "gwetroot"):
                    if fila[var]:
                        por.setdefault((fila["region"], var, anio), []).append(float(fila[var]))
    return {k: float(np.mean(v)) for k, v in por.items() if len(v) >= 365}


def z(x):
    x = np.asarray(x, float)
    return (x - x.mean()) / x.std(ddof=1)


def contraste(cid, investigacion, region, anios, nuestra, externa, nombre_ext, unidad_ext):
    tn = tr.analizar(anios, nuestra, "m³/m³")
    te = tr.analizar(anios, externa, unidad_ext)
    r = float(np.corrcoef(nuestra, externa)[0, 1])
    sn, se = tn["theil_sen"]["por_decada"], te["theil_sen"]["por_decada"]
    frase = (f"GLDAS-2.1 vs {nombre_ext.split(' (')[0]} over {region}, {anios[0]}–{anios[-1]}: r = {r:.2f} (annual values); "
             f"Sen slopes {sn:+.4f} m³/m³ vs {se:+.4f} {unidad_ext} per decade; "
             f"verdicts '{VEREDICTO_EN[tn['veredicto']]}' vs '{VEREDICTO_EN[te['veredicto']]}'. "
             "Shown as standardized anomalies because the units differ.")
    entrada = {"id": cid, "investigacion": investigacion, "papel": "contraste", "estado": "ok", "region": region,
               "periodo": [anios[0], anios[-1]],
               "serie_nuestra": {"fuente": "GLDAS-2.1 Noah (GES DISC), regional mean", "pendiente": None,
                                 "pendiente_propia": sn, "unidad": "z/década", "veredicto": tn["veredicto"]},
               "serie_externa": {"fuente": nombre_ext, "pendiente": None, "pendiente_propia": se,
                                 "unidad_propia": unidad_ext, "veredicto": te["veredicto"]},
               "diferencia": {"media": None, "r": round(r, 4), "anios_comunes": len(anios)},
               "frase_en": frase}
    filas = [[cid, "nuestra", a, round(float(v), 4)] for a, v in zip(anios, z(nuestra))]
    filas += [[cid, "externa", a, round(float(v), 4)] for a, v in zip(anios, z(externa))]
    return entrada, filas


def main():
    gldas = {(s["region"], s["variable"]): s for s in json.loads((AQUI / "series_gldas_anual.json").read_text(encoding="utf-8"))}
    merra = merra2_anual()
    entradas, filas = [], []
    for (region, var), s in sorted(gldas.items()):
        for var_g, var_m, nombre, unidad in PARES:
            if var != var_g:
                continue
            anios = [a for a in s["tiempos"] if (region, var_m, a) in merra]
            if len(anios) < 10:
                continue
            nuestra = [s["valores"][s["tiempos"].index(a)] for a in anios]
            externa = [merra[(region, var_m, a)] for a in anios]
            e, f = contraste(f"merra2_{var_g}_{region}", f"{var_g}_{region}", region, anios, nuestra, externa, nombre, unidad)
            entradas.append(e)
            filas += f
    smap = AQUI / "series_appeears_nicaragua_anual.json"
    if smap.is_file():
        series_smap = {(x["region"], x["variable"]): x for x in json.loads(smap.read_text(encoding="utf-8"))}
        for (region, var), s in sorted(gldas.items()):
            for var_g, var_s, nombre in PARES_SMAP:
                o = series_smap.get((region, var_s))
                if var != var_g or not o:
                    continue
                anios = [a for a, v in zip(o["tiempos"], o["valores"]) if v is not None and a in s["tiempos"]]
                if len(anios) < 5:
                    continue
                nuestra = [s["valores"][s["tiempos"].index(a)] for a in anios]
                externa = [o["valores"][o["tiempos"].index(a)] for a in anios]
                e, f = contraste(f"smap_{var_g}_{region}", f"{var_g}_{region}", region, anios, nuestra, externa, nombre, "m³/m³")
                entradas.append(e)
                filas += f
    (AQUI / "contrastes_tierra.json").write_text(json.dumps(
        {"esquema": "nasa-challenge/contrastes", "version": "1.0.0", "contrastes": entradas}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="\n")
    with (AQUI / "contrastes_tierra_series.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["contraste", "serie", "anio", "valor"])
        w.writerows(filas)
    for e in entradas:
        print(e["id"], "r =", e["diferencia"]["r"], e["serie_nuestra"]["veredicto"], "|", e["serie_externa"]["veredicto"])


if __name__ == "__main__":
    main()
