"""Tendencia lineal de una serie anual con incertidumbre para pocas observaciones.

Pensado para series de unas dos décadas (p. ej. precipitación anual IMERG 2001–2024, n=24):

- Estimador principal: mínimos cuadrados con intervalo t cuyos grados de libertad usan el tamaño
  efectivo de muestra por autocorrelación de lag 1 de los residuos (Santer et al., 2000). Solo
  reduce los grados de libertad: nunca infla la muestra si la autocorrelación es negativa.
- Controles: errores HAC de Newey–West (Bartlett; asintótico, con 24 años tiende a subestimar la
  incertidumbre) y Theil–Sen con tau de Kendall (no paramétricos).
- Sensibilidad: recortes del período y omisión de un año.
- Años faltantes: los rezagos se miden en años calendario, no en posiciones del vector. La autocorrelación
  de lag 1 usa solo los pares de años consecutivos (suma de productos por par disponible, reescalada a los
  n−1 pares de una serie sin huecos) y el HAC pondera todo par de años a distancia calendario 1…L con el
  núcleo de Bartlett (estimador HAC por distancia temporal de Conley, 1999). Sin huecos ambos coinciden
  exactamente con las fórmulas habituales. Si quedan menos de MIN_PARES pares consecutivos, no se estima
  la autocorrelación: se conserva la pendiente descriptiva y no se informa intervalo ni veredicto.

El veredicto «tendencia_detectada» exige que los tres intervalos excluyan cero con el mismo signo.
Un intervalo que incluye cero no demuestra ausencia de cambio: indica que la ventana y el método
no bastan para detectarlo.
"""
import math

import numpy as np
from scipy import stats

NIVEL = 0.95
MIN_ANIOS = 10
MIN_PARES = 5  # pares de años consecutivos para estimar la autocorrelación de lag 1
RECORTE_SENSIBILIDAD = 3


def agregar_anual(registros, exigir_meses=12):
    """Suma mensual → anual solo con los doce meses presentes y válidos.

    registros: iterable de (anio, mes, valor_mm); valor None/NaN = mes inválido.
    Devuelve (anuales {anio: mm}, excluidos {anio: motivo}). Un mes duplicado excluye el año.
    """
    por_anio = {}
    for anio, mes, valor in registros:
        por_anio.setdefault(int(anio), []).append((int(mes), valor))
    anuales, excluidos = {}, {}
    for anio in sorted(por_anio):
        meses = [m for m, _ in por_anio[anio]]
        if len(meses) != len(set(meses)):
            excluidos[anio] = "mes duplicado"
            continue
        validos = {m: v for m, v in por_anio[anio]
                   if v is not None and math.isfinite(float(v)) and 1 <= m <= 12}
        if len(validos) != exigir_meses:
            faltan = sorted(set(range(1, 13)) - validos.keys())
            excluidos[anio] = f"{len(validos)} de 12 meses válidos (faltan {faltan})"
            continue
        anuales[anio] = float(sum(validos.values()))
    return anuales, excluidos


def _mco(x, y):
    xc = x - x.mean()
    sxx = float(xc @ xc)
    b = float(xc @ (y - y.mean())) / sxx
    a = float(y.mean() - b * x.mean())
    e = y - (a + b * x)
    return a, b, e, xc, sxx


class _SinInferencia(Exception):
    """No se puede estimar la autocorrelación con los años disponibles."""


def _pares_consecutivos(x):
    return np.diff(x) == 1


def _r1_calendario(x, e):
    """Autocorrelación de lag 1 con años calendario; idéntica al estimador habitual si no hay huecos."""
    consecutivos = _pares_consecutivos(x)
    pares = int(consecutivos.sum())
    if pares < MIN_PARES:
        raise _SinInferencia(pares)
    sce = float(e @ e)
    if sce <= 0:
        return 0.0
    return float((e[:-1] * e[1:])[consecutivos].sum()) * (len(x) - 1) / pares / sce


def _intervalo_clasico(x, y, nivel):
    a, b, e, xc, sxx = _mco(x, y)
    n = len(x)
    s2 = float(e @ e) / (n - 2)
    se = math.sqrt(s2 / sxx)
    r1 = _r1_calendario(x, e)
    n_ef = n * (1 - r1) / (1 + r1) if r1 > 0 else float(n)
    n_ef = min(float(n), n_ef)
    gl = n_ef - 2
    if gl < 1:
        return None
    se_aj = se * math.sqrt((n - 2) / gl)
    t = stats.t.ppf(0.5 + nivel / 2, gl)
    p = 2 * stats.t.sf(abs(b / se_aj), gl) if se_aj > 0 else (0.0 if b != 0 else 1.0)
    return {"pendiente": b, "ic": (b - t * se_aj, b + t * se_aj), "p": float(p), "error_estandar": se_aj,
            "r1_residuos": r1, "n_efectivo": n_ef, "gl": gl,
            "ic_sin_ajuste": (b - stats.t.ppf(0.5 + nivel / 2, n - 2) * se,
                              b + stats.t.ppf(0.5 + nivel / 2, n - 2) * se)}


def _intervalo_hac(x, y, nivel):
    a, b, e, xc, sxx = _mco(x, y)
    n = len(x)
    rezago = min(n - 2, int(math.floor(4 * (n / 100) ** (2 / 9))))
    u = xc * e
    distancia = np.abs(x[:, None] - x[None, :])  # años calendario entre observaciones
    pesos = np.where((distancia >= 1) & (distancia <= rezago), 1 - distancia / (rezago + 1), 0.0)
    s = float(u @ u) + float(u @ (pesos @ u))  # cada par cuenta dos veces: igual a Newey–West sin huecos
    var = s / sxx ** 2 * n / (n - 2)  # corrección de muestra pequeña
    se = math.sqrt(max(var, 0.0))
    t = stats.t.ppf(0.5 + nivel / 2, n - 2)
    return {"ic": (b - t * se, b + t * se), "rezago": rezago, "error_estandar": se}


def _signo_ic(ic):
    return 1 if ic[0] > 0 else -1 if ic[1] < 0 else 0


def _por_decada(v):
    return None if v is None else v * 10


def _ajustar(anios, valores, nivel):
    x = np.asarray(anios, float)
    y = np.asarray(valores, float)
    try:
        c = _intervalo_clasico(x, y, nivel)
    except _SinInferencia:
        return None
    if c is None:
        return None
    return x, y, c


def _resumen(x, y, c):
    return {"anios": int(len(x)), "periodo": [int(x[0]), int(x[-1])],
            "mm_por_decada": round(_por_decada(c["pendiente"]), 3),
            "ic_mm_por_decada": [round(_por_decada(v), 3) for v in c["ic"]]}


def analizar_tendencia(anios, valores, nivel=NIVEL):
    """Pendiente (unidades/década) con IC y controles. Lanza ValueError si la entrada es incoherente."""
    anios = list(anios)
    valores = list(valores)
    if len(anios) != len(valores):
        raise ValueError("anios y valores deben tener la misma longitud.")
    try:
        if any(isinstance(a, bool) or int(a) != a for a in anios) or len(set(anios)) != len(anios):
            raise ValueError("Los años deben ser enteros únicos.")
        if not all(v is not None and not isinstance(v, bool) and math.isfinite(float(v)) for v in valores):
            raise ValueError("Valores no finitos: agregue solo años completos antes de analizar.")
    except (TypeError, OverflowError) as e:  # None, cadenas no numéricas, inf en los años…
        raise ValueError(f"Entrada no numérica: {e}") from None
    orden = np.argsort(anios)
    anios = [int(anios[i]) for i in orden]
    valores = [float(valores[i]) for i in orden]
    if len(anios) < MIN_ANIOS:
        return {"estado": "datos_insuficientes", "anios": len(anios), "minimo_anios": MIN_ANIOS,
                "mensaje": f"Con {len(anios)} años completos (mínimo {MIN_ANIOS}) no se estima una tendencia."}
    if max(valores) == min(valores):
        # Sin variabilidad entre años no hay incertidumbre que estimar (Kendall daría NaN e IC degenerados en cero).
        return {"estado": "datos_insuficientes", "motivo": "serie_constante", "anios": len(anios), "minimo_anios": MIN_ANIOS,
                "mensaje": "La serie anual es constante: sin variabilidad entre años no se estima tendencia ni intervalo."}
    huecos = [a for a, b in zip(anios[1:], anios[:-1]) if a - b != 1]
    faltantes = sorted(set(range(anios[0], anios[-1] + 1)) - set(anios))
    try:
        c0 = _intervalo_clasico(np.asarray(anios, float), np.asarray(valores, float), nivel)
        ajuste = None if c0 is None else (np.asarray(anios, float), np.asarray(valores, float), c0)
    except _SinInferencia as e:
        xx, yy = np.asarray(anios, float), np.asarray(valores, float)
        pend = _mco(xx, yy)[1]
        return _exigir_finito({
            "estado": "inferencia_no_disponible", "motivo": "huecos_sin_pares_consecutivos", "anios": len(anios),
            "periodo": [anios[0], anios[-1]], "anios_faltantes": faltantes, "huecos_en_anios": huecos,
            "pares_consecutivos": int(e.args[0]), "minimo_pares": MIN_PARES,
            "mm_por_decada": round(_por_decada(pend), 3),
            "mensaje": (f"Faltan {len(faltantes)} años dentro del período ({', '.join(map(str, faltantes[:12]))}"
                        f"{'…' if len(faltantes) > 12 else ''}) y solo quedan {int(e.args[0])} pares de años consecutivos "
                        f"(mínimo {MIN_PARES}): no se estima la autocorrelación con rezagos en años calendario, así que no se "
                        f"informa intervalo ni veredicto. Pendiente descriptiva: {round(_por_decada(pend), 1)} mm/década.")})
    if ajuste is None:
        return {"estado": "datos_insuficientes", "anios": len(anios), "minimo_anios": MIN_ANIOS,
                "mensaje": "La autocorrelación de los residuos deja menos de tres observaciones efectivas."}
    x, y, c = ajuste
    media = float(y.mean())
    hac = _intervalo_hac(x, y, nivel)
    sen = stats.theilslopes(y, x, alpha=nivel)
    tau, p_mk = stats.kendalltau(x, y)
    ics = {"principal": c["ic"], "hac": hac["ic"], "theil_sen": (float(sen.low_slope), float(sen.high_slope))}
    signos = {k: _signo_ic(v) for k, v in ics.items()}
    if c["p"] < 1 - nivel and len(set(signos.values())) == 1 and signos["principal"] != 0:
        veredicto = "tendencia_detectada"
    elif all(s == 0 for s in signos.values()):
        veredicto = "evidencia_insuficiente"
    else:
        veredicto = "metodos_discrepan"
    sensibilidad = []
    r = RECORTE_SENSIBILIDAD
    ventanas = [("período completo", slice(None)), (f"sin los primeros {r} años", slice(r, None)),
                (f"sin los últimos {r} años", slice(None, -r))]
    for nombre, s in ventanas:
        xs, ys = x[s], y[s]
        aj = _ajustar(xs, ys, nivel) if len(xs) >= MIN_ANIOS else None
        sensibilidad.append({"ventana": nombre, **(_resumen(*aj) if aj else {"anios": int(len(xs))})})
    sueltos = [_por_decada(_mco(np.delete(x, i), np.delete(y, i))[1]) for i in range(len(x))]
    return _exigir_finito({
        "estado": "ok", "veredicto": veredicto,
        "nivel": nivel, "anios": len(x), "periodo": [int(x[0]), int(x[-1])],
        "huecos_en_anios": huecos, "anios_faltantes": faltantes,
        "pares_consecutivos": int(_pares_consecutivos(x).sum()),
        "rezagos_en": "años calendario",
        "media_anual": round(media, 3),
        "mm_por_decada": round(_por_decada(c["pendiente"]), 3),
        "ic_mm_por_decada": [round(_por_decada(v), 3) for v in c["ic"]],
        # Relativo a la media anual solo si esta es positiva: con media negativa (p. ej. una serie de diferencias) el
        # signo y el orden de los límites se invertirían, y con media cero no existe.
        "pct_por_decada": round(_por_decada(c["pendiente"]) / media * 100, 3) if media > 0 else None,
        "ic_pct_por_decada": [round(_por_decada(v) / media * 100, 3) for v in c["ic"]] if media > 0 else None,
        "p_valor_principal": round(c["p"], 4),
        "r1_residuos": round(c["r1_residuos"], 3), "n_efectivo": round(c["n_efectivo"], 1),
        "ic_sin_ajuste_mm_por_decada": [round(_por_decada(v), 3) for v in c["ic_sin_ajuste"]],
        "hac": {"rezago": hac["rezago"], "ic_mm_por_decada": [round(_por_decada(v), 3) for v in hac["ic"]]},
        "theil_sen": {"mm_por_decada": round(_por_decada(float(sen.slope)), 3),
                      "ic_mm_por_decada": [round(_por_decada(v), 3) for v in ics["theil_sen"]]},
        "mann_kendall": {"tau": round(float(tau), 3), "p_valor": round(float(p_mk), 4)},
        "sensibilidad": sensibilidad,
        "omitir_un_anio_mm_por_decada": [round(min(sueltos), 3), round(max(sueltos), 3)],
        "recta": {"intercepto": float(y.mean() - c["pendiente"] * x.mean()),
                  "pendiente_anual": c["pendiente"]},
        "interpretacion": interpretar(veredicto, c, nivel),
    })


def _exigir_finito(resultado):
    """Error controlado si algún número salió NaN o infinito (p. ej. desbordamiento con magnitudes extremas).
    Así nunca llega un NaN a la interfaz ni al JSON, que el servidor serializa con allow_nan=False."""
    def recorrer(v, ruta):
        if isinstance(v, dict):
            for k, w in v.items():
                recorrer(w, f"{ruta}.{k}")
        elif isinstance(v, (list, tuple)):
            for i, w in enumerate(v):
                recorrer(w, f"{ruta}[{i}]")
        elif isinstance(v, (float, np.floating)) and not math.isfinite(float(v)):
            raise ValueError(f"Cálculo no finito en {ruta.lstrip('.')}: revise la magnitud de los valores.")
    recorrer(resultado, "")
    return resultado


def interpretar(veredicto, c, nivel=NIVEL):
    pct = int(round(nivel * 100))
    if veredicto == "tendencia_detectada":
        sentido = "aumento" if c["pendiente"] > 0 else "disminución"
        return (f"El intervalo del {pct} % excluye cero con los tres métodos: hay un {sentido} distinguible de la "
                "variabilidad entre años en esta ventana. No prueba la causa ni que continúe fuera de ella.")
    if veredicto == "evidencia_insuficiente":
        return (f"El intervalo del {pct} % incluye cero con los tres métodos: con este método y esta ventana la "
                "evidencia es insuficiente para detectar una tendencia. No demuestra que no haya cambio.")
    return ("Los métodos no coinciden respecto de cero: la señal depende de supuestos y no es concluyente. "
            "Se informan todos los intervalos sin elegir el más favorable.")
