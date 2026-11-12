"""Modelo estacional estadístico y su validación fuera de muestra.

Esto es PRONÓSTICO, no detección de tendencias: pregunta si un índice conocido antes de la temporada
(por ejemplo Niño 3.4 de marzo–mayo, disponible a inicios de junio) anticipa la lluvia de junio–noviembre
mejor que la climatología.

Validación:
- Dejar un año fuera (LOO) y, como control más exigente, dejar fuera bloques de 3 años centrados en el
  año pronosticado (reduce la fuga por autocorrelación). En cada pliegue se reajustan la regresión, la
  climatología de referencia y los terciles.
- Habilidad: MSESS = 1 − ECM_modelo / ECM_climatología (> 0 significa mejor que la climatología),
  correlación entre pronóstico y observación, y aciertos de tercil (33 % es el azar).
- Significancia de la MSESS por permutación: se barajan los años del predictando (n permutaciones) y se
  repite toda la validación cruzada; p = fracción de permutaciones con MSESS ≥ la observada.
"""
import numpy as np


def _ajustar(X, y):
    A = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    return beta


def _predecir(beta, X):
    return beta[0] + np.atleast_2d(X) @ beta[1:]


def _tercil(valor, ref):
    t1, t2 = np.percentile(ref, [100 / 3, 200 / 3])
    return 0 if valor < t1 else 2 if valor > t2 else 1


def validacion_cruzada(y, X, bloque=1):
    """Pronósticos fuera de muestra. X: (n, k) o None para solo climatología. Devuelve dict."""
    y = np.asarray(y, float)
    n = len(y)
    X = None if X is None else np.asarray(X, float).reshape(n, -1)
    pred = np.empty(n)
    clim = np.empty(n)
    aciertos = 0
    mitad = bloque // 2
    for i in range(n):
        fuera = np.zeros(n, bool)
        fuera[max(0, i - mitad):i + mitad + 1] = True
        ent = ~fuera
        clim[i] = y[ent].mean()
        if X is None:
            pred[i] = clim[i]
        else:
            beta = _ajustar(X[ent], y[ent])
            pred[i] = float(_predecir(beta, X[i:i + 1])[0])
        aciertos += _tercil(pred[i], y[ent]) == _tercil(y[i], y[ent])
    ecm = float(np.mean((pred - y) ** 2))
    ecm_clim = float(np.mean((clim - y) ** 2))
    r = float(np.corrcoef(pred, y)[0, 1]) if np.std(pred) > 0 else 0.0
    return {"n": n, "bloque": bloque, "ecm": ecm, "ecm_climatologia": ecm_clim,
            "msess": 1 - ecm / ecm_clim if ecm_clim > 0 else 0.0, "r": r,
            "aciertos_tercil": aciertos / n, "pronosticos": pred.tolist(), "climatologia": clim.tolist()}


def msess_loo(y, X):
    """MSESS dejando un año fuera por fórmula cerrada (residuo / (1 − h_ii)); igual a validacion_cruzada(…, 1).
    Para la climatología, el error LOO es (y_i − media) · n / (n − 1)."""
    y = np.asarray(y, float)
    n = len(y)
    A = np.column_stack([np.ones(n), np.asarray(X, float).reshape(n, -1)])
    q, _ = np.linalg.qr(A)
    h = np.sum(q ** 2, axis=1)
    e = y - q @ (q.T @ y)
    ecm = float(np.mean((e / (1 - h)) ** 2))
    ecm_clim = float(np.mean(((y - y.mean()) * n / (n - 1)) ** 2))
    return 1 - ecm / ecm_clim if ecm_clim > 0 else 0.0


def evaluar(y, X, permutaciones=1000, semilla=2026, bloques=(1, 3)):
    y = np.asarray(y, float)
    X = np.asarray(X, float).reshape(len(y), -1)
    res = {f"bloque_{b}": validacion_cruzada(y, X, b) for b in bloques}
    obs = res["bloque_1"]["msess"]
    rng = np.random.default_rng(semilla)
    mayores = 0
    for _ in range(permutaciones):
        if msess_loo(rng.permutation(y), X) >= obs - 1e-12:
            mayores += 1
    res["p_permutacion_msess"] = (mayores + 1) / (permutaciones + 1)
    beta = _ajustar(X, y)
    res["coeficientes_muestra_completa"] = [float(b) for b in beta]
    return res


def resumen(res):
    """Versión compacta (sin listas de pronósticos) para el JSON público."""
    out = {}
    for k, v in res.items():
        if isinstance(v, dict):
            out[k] = {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()
                      if kk not in ("pronosticos", "climatologia")}
        elif isinstance(v, list):
            out[k] = [round(x, 4) for x in v]
        else:
            out[k] = round(v, 4) if isinstance(v, float) else v
    return out


# ---------------------------------------------------------------- horizontes y pronóstico operativo

MESES_ABREV = "EFMAMJJASOND"


def ventana_predictor(mes_inicio_temporada, horizonte):
    """Meses (año relativo, mes) del predictor: los 3 meses que terminan `horizonte` meses antes del primer mes
    de la temporada. horizonte = 0 → los 3 meses inmediatamente anteriores (p. ej. MAM para una temporada que
    empieza en junio). Devuelve [(desplazamiento_de_anio, mes)], con desplazamiento −1 si cae en el año anterior."""
    fin = mes_inicio_temporada - 1 - horizonte
    out = []
    for k in (2, 1, 0):
        m = fin - k
        d = 0
        while m < 1:
            m += 12
            d -= 1
        out.append((d, m))
    return out


def nombre_ventana(meses):
    return "".join(MESES_ABREV[m - 1] for _, m in meses)


def serie_predictor(indice_mensual, anios, mes_inicio, horizonte):
    """indice_mensual: {(anio, mes): valor}. Devuelve {anio: media de la ventana} solo si está completa."""
    ventana = ventana_predictor(mes_inicio, horizonte)
    out = {}
    for a in anios:
        vals = [indice_mensual.get((a + d, m)) for d, m in ventana]
        if all(v is not None and np.isfinite(v) for v in vals):
            out[a] = float(np.mean(vals))
    return out


def pronostico(y, X, x_nuevo, cuantiles=(0.1, 0.9)):
    """Ajuste con todos los años y pronóstico para x_nuevo, con intervalo empírico a partir de los errores
    fuera de muestra (LOO) y probabilidades de tercil (bajo, normal, alto) respecto de la climatología."""
    y = np.asarray(y, float)
    X = np.asarray(X, float).reshape(len(y), -1)
    beta = _ajustar(X, y)
    central = float(_predecir(beta, np.asarray(x_nuevo, float).reshape(1, -1))[0])
    cv = validacion_cruzada(y, X, 1)
    errores = y - np.asarray(cv["pronosticos"])
    muestras = central + errores
    t1, t2 = np.percentile(y, [100 / 3, 200 / 3])
    return {"valor_esperado": central,
            "intervalo": [float(np.quantile(muestras, cuantiles[0])), float(np.quantile(muestras, cuantiles[1]))],
            "nivel_intervalo": cuantiles[1] - cuantiles[0],
            "prob_terciles": {"bajo": float(np.mean(muestras < t1)), "normal": float(np.mean((muestras >= t1) & (muestras <= t2))),
                              "alto": float(np.mean(muestras > t2))},
            "climatologia": {"media": float(y.mean()), "tercil_inferior": float(t1), "tercil_superior": float(t2)},
            "habilidad_loo": {"msess": cv["msess"], "r": cv["r"], "aciertos_tercil": cv["aciertos_tercil"]},
            "coeficientes": [float(b) for b in beta]}
