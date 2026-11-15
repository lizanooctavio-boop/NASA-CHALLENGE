"""Detección de tendencias robusta para series anuales cortas (24–44 años).

Complementa `tendencia.py` (que no se modifica: define el veredicto del contrato 1.0.0) con:

- Mann–Kendall modificado por autocorrelación (Hamed y Rao, 1998): la varianza de S se corrige con las
  autocorrelaciones significativas de los rangos de la serie sin tendencia de Sen. El factor de
  corrección no baja de 1: nunca se infla la muestra (mismo criterio que `tendencia.py`).
- Theil–Sen con intervalo del 95 % (Sen, 1968; vía scipy).
- Pettitt (1979): cambio de nivel único con su año y p-valor aproximado. Una tendencia suave también
  produce un «cambio» de Pettitt; se informa como descriptivo, no como causa.
- Regresión con control por ENOS: y = a + b·t + c·Niño3.4 (+ otros índices), errores HAC de Newey–West.
  Muestra si la pendiente cambia al retirar la parte de la variabilidad que explica ENOS.

Todas las pendientes se expresan por década en las unidades de la serie.
"""
import math

import numpy as np
from scipy import stats

import tendencia  # scripts/datos/tendencia.py (veredicto del contrato 1.0.0), vía clima_nic.rutas

NIVEL = 0.95


def _sgn(x):
    return np.sign(x).astype(float)


def mann_kendall_modificado(y, nivel=NIVEL):
    y = np.asarray(y, float)
    n = len(y)
    if n < 10:
        raise ValueError("Mann–Kendall requiere al menos 10 valores.")
    i, j = np.triu_indices(n, 1)
    s = float(_sgn(y[j] - y[i]).sum())
    _, cuentas = np.unique(y, return_counts=True)
    var_s = (n * (n - 1) * (2 * n + 5) - float(np.sum(cuentas * (cuentas - 1) * (2 * cuentas + 5)))) / 18
    x = np.arange(n, dtype=float)
    pendiente = float(stats.theilslopes(y, x).slope)
    residuos = y - pendiente * x
    r = stats.rankdata(residuos)
    r = r - r.mean()
    den = float(r @ r)
    suma = 0.0
    lim = 1.96 / math.sqrt(n)  # Hamed y Rao: solo rezagos significativos al 5 %
    rezagos = []
    for k in range(1, n - 2):
        rk = float(r[:-k] @ r[k:]) / den if den > 0 else 0.0
        if abs(rk) > lim:
            rezagos.append(k)
            suma += (n - k) * (n - k - 1) * (n - k - 2) * rk
    factor = max(1.0, 1 + 2 / (n * (n - 1) * (n - 2)) * suma)
    var_aj = var_s * factor
    if var_aj <= 0:
        z = 0.0
    else:
        z = (s - np.sign(s)) / math.sqrt(var_aj)
    p = float(2 * stats.norm.sf(abs(z)))
    tau = s / (n * (n - 1) / 2)
    return {"s": s, "tau": round(tau, 4), "z": round(float(z), 4), "p_valor": round(p, 4),
            "factor_correccion": round(factor, 4), "rezagos_significativos": rezagos,
            "significativo": p < 1 - nivel}


def theil_sen(anios, y, nivel=NIVEL):
    r = stats.theilslopes(np.asarray(y, float), np.asarray(anios, float), alpha=nivel)
    return {"por_decada": round(float(r.slope) * 10, 4),
            "ic_por_decada": [round(float(r.low_slope) * 10, 4), round(float(r.high_slope) * 10, 4)]}


def pettitt(anios, y):
    """Prueba de Pettitt. El año de cambio es el primero del segundo tramo."""
    y = np.asarray(y, float)
    n = len(y)
    signos = _sgn(y[None, :] - y[:, None])  # signos[i, j] = sgn(y_j − y_i)
    u = np.array([signos[:t + 1, t + 1:].sum() for t in range(n - 1)])
    t = int(np.argmax(np.abs(u)))
    k = float(abs(u[t]))
    p = min(1.0, 2 * math.exp(-6 * k ** 2 / (n ** 3 + n ** 2)))
    antes, despues = y[:t + 1], y[t + 1:]
    return {"anio_cambio": int(list(anios)[t + 1]), "k": k, "p_valor": round(p, 4),
            "media_antes": round(float(antes.mean()), 4), "media_despues": round(float(despues.mean()), 4),
            "salto": round(float(despues.mean() - antes.mean()), 4)}


def _hac(X, e, rezago):
    n = X.shape[0]
    u = X * e[:, None]
    s = u.T @ u
    for k in range(1, rezago + 1):
        w = 1 - k / (rezago + 1)
        g = u[k:].T @ u[:-k]
        s += w * (g + g.T)
    xtx_inv = np.linalg.pinv(X.T @ X)
    return xtx_inv @ s @ xtx_inv * n / (n - X.shape[1])


def regresion_controlada(anios, y, covariables, nivel=NIVEL):
    """y = a + b·año + Σ c_k·cov_k. Devuelve pendiente por década con IC HAC y coeficientes."""
    y = np.asarray(y, float)
    t = np.asarray(anios, float)
    n = len(y)
    nombres = list(covariables)
    cols = [np.ones(n), t - t.mean()] + [np.asarray(covariables[k], float) for k in nombres]
    X = np.column_stack(cols)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ beta
    rezago = min(n - 2, int(math.floor(4 * (n / 100) ** (2 / 9))))
    cov = _hac(X, e, rezago)
    gl = n - X.shape[1]
    if gl <= 0:
        raise ValueError("La regresión controlada requiere más observaciones que parámetros.")
    q = stats.t.ppf(0.5 + nivel / 2, gl)
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    sst = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - float(e @ e) / sst if sst > 0 else 0.0
    coef = {}
    for i, k in enumerate(nombres, start=2):
        coef[k] = {"coeficiente": round(float(beta[i]), 4),
                   "ic": [round(float(beta[i] - q * se[i]), 4), round(float(beta[i] + q * se[i]), 4)],
                   "p_valor": round(float(2 * stats.t.sf(abs(beta[i] / se[i]), gl)) if se[i] > 0 else 1.0, 4)}
    b = beta[1]
    return {"por_decada": round(float(b) * 10, 4),
            "ic_por_decada": [round(float(b - q * se[1]) * 10, 4), round(float(b + q * se[1]) * 10, 4)],
            "p_valor": round(float(2 * stats.t.sf(abs(b / se[1]), gl)) if se[1] > 0 else 1.0, 4),
            "r2": round(r2, 4), "rezago_hac": rezago, "covariables": coef}


def _renombrar(t):
    """tendencia.analizar_tendencia usa claves «mm_…»; aquí la unidad la fija quien llama."""
    if t.get("estado") != "ok":
        return {k: v for k, v in t.items() if k not in ("recta",)}
    return {
        "estado": "ok", "veredicto": t["veredicto"], "media": t["media_anual"],
        "por_decada": t["mm_por_decada"], "ic_por_decada": t["ic_mm_por_decada"],
        "p_valor": t["p_valor_principal"], "n_efectivo": t["n_efectivo"], "r1_residuos": t["r1_residuos"],
        "hac_ic_por_decada": t["hac"]["ic_mm_por_decada"],
        "sensibilidad": [{"ventana": s["ventana"], "anios": s["anios"],
                          **({"por_decada": s["mm_por_decada"], "ic_por_decada": s["ic_mm_por_decada"]}
                             if "mm_por_decada" in s else {})} for s in t["sensibilidad"]],
        "omitir_un_anio_por_decada": t["omitir_un_anio_mm_por_decada"],
    }


def veredicto_robusto(base, mmk, sen):
    """Veredicto ampliado: «tendencia_detectada» solo si el veredicto de tendencia.py lo es Y el
    Mann–Kendall modificado es significativo con el mismo signo que Theil–Sen."""
    if base.get("estado") != "ok":
        return "datos_insuficientes"
    signo_sen = 1 if sen["ic_por_decada"][0] > 0 else -1 if sen["ic_por_decada"][1] < 0 else 0
    if base["veredicto"] == "tendencia_detectada" and mmk["significativo"] and signo_sen != 0 \
            and np.sign(mmk["z"]) == signo_sen:
        return "tendencia_detectada"
    if base["veredicto"] == "evidencia_insuficiente" and not mmk["significativo"]:
        return "evidencia_insuficiente"
    return "metodos_discrepan"


def analizar(anios, y, unidad, covariables=None, nivel=NIVEL):
    """Resumen completo de detección de tendencia de una serie anual."""
    anios = [int(a) for a in anios]
    y = [float(v) for v in y]
    base = _renombrar(tendencia.analizar_tendencia(anios, y, nivel))
    out = {"unidad": unidad, "unidad_pendiente": f"{unidad}/década", "anios": len(anios),
           "periodo": [min(anios), max(anios)], "minimos_cuadrados": base}
    if base.get("estado") != "ok":
        out["veredicto"] = "datos_insuficientes"
        return out
    mmk = mann_kendall_modificado(y, nivel)
    sen = theil_sen(anios, y, nivel)
    out.update({"mann_kendall_modificado": mmk, "theil_sen": sen, "pettitt": pettitt(anios, y)})
    if covariables:
        out["controlada_por_indices"] = regresion_controlada(anios, y, covariables, nivel)
    out["veredicto"] = veredicto_robusto(base, mmk, sen)
    return out
