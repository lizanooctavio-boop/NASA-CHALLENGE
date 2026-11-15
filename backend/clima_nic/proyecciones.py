"""Escenarios de décadas con NEX-GDDP-CMIP6: rangos por escenario, nunca un pronóstico de un año concreto.

Método (corrección de sesgo por delta, «delta change»):
1. Para cada modelo y región: climatología del histórico del modelo (1995–2014) y del período futuro (2041–2060)
   en cada escenario (SSP2-4.5, SSP5-8.5).
2. Cambio del modelo: Δ = futuro − histórico para la temperatura (°C) y Δ% = futuro/histórico − 1 para la lluvia.
   Así se elimina el sesgo medio del modelo, que se informa aparte (histórico del modelo frente a la observación).
3. Valor proyectado = climatología observada 1995–2014 (POWER/MERRA-2) + Δ (o × (1 + Δ%)).
4. Se resume el conjunto de modelos con mínimo, cuartiles, mediana y máximo, y cuántos modelos coinciden en el
   signo del cambio. Con 6 modelos el rango es una muestra pequeña de la incertidumbre de modelo.
"""
import csv
from pathlib import Path

import numpy as np

from .rutas import FENOMENOS

HIST = (1995, 2014)
FUTURO = (2041, 2060)
TEMPORADAS = {"anual": tuple(range(1, 13)), "jun_nov": tuple(range(6, 12)), "jul_ago": (7, 8)}


def leer_cmip6(ruta=FENOMENOS / "cmip6_mensual.csv"):
    """{(modelo, escenario, variable, region): {(anio, mes): valor}}"""
    ruta = Path(ruta)
    if not ruta.exists():
        return {}
    out = {}
    with ruta.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            out.setdefault((r["modelo"], r["escenario"], r["variable"], r["region"]), {})[
                (int(r["anio"]), int(r["mes"]))] = float(r["valor"])
    return out


def climatologia(serie, periodo, meses, variable):
    """Media de la temporada (suma de meses para pr, media para tas) sobre los años completos del período."""
    vals = []
    for a in range(periodo[0], periodo[1] + 1):
        x = [serie.get((a, m)) for m in meses]
        if all(v is not None and np.isfinite(v) for v in x):
            vals.append(sum(x) if variable == "pr" else float(np.mean(x)))
    return float(np.mean(vals)) if vals else float("nan"), len(vals)


def resumen_conjunto(valores):
    v = np.asarray([x for x in valores if np.isfinite(x)], float)
    if len(v) == 0:
        return None
    return {"n_modelos": int(len(v)), "minimo": float(v.min()), "p25": float(np.percentile(v, 25)),
            "mediana": float(np.median(v)), "p75": float(np.percentile(v, 75)), "maximo": float(v.max()),
            "modelos_aumento": int((v > 0).sum()), "modelos_disminucion": int((v < 0).sum())}


def escenarios(cmip6, observado, region, variable, temporada="anual", hist=HIST, futuro=FUTURO):
    """observado: {(anio, mes): valor} de la observación (mm/mes para pr, °C para tas)."""
    meses = TEMPORADAS[temporada]
    obs, n_obs = climatologia(observado, hist, meses, variable)
    modelos = sorted({k[0] for k in cmip6 if k[2] == variable and k[3] == region})
    out = {"region": region, "variable": variable, "temporada": temporada, "periodo_historico": list(hist),
           "periodo_futuro": list(futuro), "observado_historico": obs, "anios_observados": n_obs,
           "unidad": "mm" if variable == "pr" else "°C", "metodo": "delta (cambio del modelo aplicado a la observación)",
           "escenarios": {}, "sesgo_modelos_historico": {}}
    for esc in ("ssp245", "ssp585"):
        deltas, proyectados = [], []
        for mo in modelos:
            h = cmip6.get((mo, "historical", variable, region))
            fut = cmip6.get((mo, esc, variable, region))
            if not h or not fut:
                continue
            ch, _ = climatologia(h, hist, meses, variable)
            cf, _ = climatologia(fut, futuro, meses, variable)
            if not (np.isfinite(ch) and np.isfinite(cf)):
                continue
            if variable == "pr" and ch <= 0:
                # Sin lluvia histórica en el modelo el cambio relativo no está definido: se excluye, sin inventar un %.
                out.setdefault("modelos_excluidos", {})[mo] = "lluvia histórica del modelo nula; cambio relativo indefinido"
                continue
            if variable == "pr":
                d = (cf / ch - 1) * 100
                proyectados.append(obs * (1 + d / 100))
            else:
                d = cf - ch
                proyectados.append(obs + d)
            deltas.append(d)
            if esc == "ssp245":
                if variable == "pr":
                    out["sesgo_modelos_historico"][mo] = None if obs == 0 else (ch / obs - 1) * 100
                else:
                    out["sesgo_modelos_historico"][mo] = ch - obs
        out["escenarios"][esc] = {"cambio": resumen_conjunto(deltas),
                                  "unidad_cambio": "%" if variable == "pr" else "°C",
                                  "valor_proyectado": resumen_conjunto(proyectados)}
    out["advertencia"] = ("Rango de escenarios de un conjunto de modelos para un promedio de 20 años; no es un pronóstico "
                          "de ningún año concreto. La variabilidad interanual (ENOS) seguirá produciendo años muy por "
                          "encima y por debajo de estos valores.")
    return out
