"""Indicadores de fenómenos climáticos a partir de series diarias o mensuales.

Funciones puras (numpy/scipy), sin red ni archivos, para poder probarlas con datos sintéticos:

- Sequía: SPI (McKee et al., 1993; gamma por mes calendario con probabilidad de ceros) y SPEI
  (Vicente-Serrano et al., 2010; log-logística de tres parámetros ajustada por momentos L) con la
  evapotranspiración de referencia de Hargreaves–Samani (FAO-56, ec. 52) y la radiación extraterrestre
  de FAO-56 (ec. 21).
- Extremos de lluvia ETCCDI: PRCPTOT, Rx1day, Rx5day, R95p, R10mm, R20mm, SDII, CDD y CWD; además
  CDD dentro de la estación lluviosa (mayo–octubre), que mide los «veranillos».
- Extremos de calor ETCCDI: TX90p y TN90p (percentil 90 por día del año con ventana de 5 días en el
  período base), TXx, TNn, y medias anuales.
- Canícula (sequía de medio verano): detección objetiva entre los dos máximos de lluvia (inicio,
  fin, duración, intensidad y déficit frente a la climatología de los mismos días) y una versión de
  ventana fija (15 de julio–15 de agosto) más simple y robusta.

Convenciones: lluvia en mm/día, temperatura en °C, fechas como numpy datetime64[D]. Un día húmedo
tiene ≥ 1 mm. Los índices ETCCDI se calculan por año calendario; las rachas (CDD, CWD) se cortan en
el 31 de diciembre (simplificación declarada: la estación seca de Nicaragua cruza el cambio de año).
"""
import math

import numpy as np
from scipy import special, stats

UMBRAL_HUMEDO = 1.0
PROB_MIN = 1e-6


# ---------------------------------------------------------------- utilidades de fechas

def descomponer(fechas):
    """datetime64[D] → (año, mes, día del año) como arreglos de enteros."""
    f = np.asarray(fechas, "datetime64[D]")
    anio = f.astype("datetime64[Y]").astype(int) + 1970
    mes = f.astype("datetime64[M]").astype(int) % 12 + 1
    doy = (f - f.astype("datetime64[Y]")).astype(int) + 1
    return anio, mes, doy


def mensual_desde_diario(fechas, valores, como="suma", min_fraccion=1.0):
    """Agrega una serie diaria a meses completos. Devuelve (anios, meses, valores) ordenados.

    Un mes con menos de `min_fraccion` de días finitos queda como NaN.
    """
    anio, mes, _ = descomponer(fechas)
    v = np.asarray(valores, float)
    claves = anio * 12 + (mes - 1)
    salida_a, salida_m, salida_v = [], [], []
    for c in np.unique(claves):
        sel = claves == c
        a, m = divmod(int(c), 12)
        dias = _dias_mes(a, m + 1)
        x = v[sel]
        ok = np.isfinite(x)
        if ok.sum() < min_fraccion * dias:
            val = math.nan
        else:
            val = float(x[ok].sum() if como == "suma" else x[ok].mean())
        salida_a.append(a)
        salida_m.append(m + 1)
        salida_v.append(val)
    return np.array(salida_a), np.array(salida_m), np.array(salida_v)


def _dias_mes(anio, mes):
    inicio = np.datetime64(f"{anio:04d}-{mes:02d}-01")
    fin = np.datetime64(f"{anio + (mes == 12):04d}-{mes % 12 + 1:02d}-01")
    return int((fin - inicio).astype(int))


def suma_movil(x, escala):
    """Suma de `escala` meses que terminan en cada mes; NaN en los primeros escala−1."""
    x = np.asarray(x, float)
    out = np.full_like(x, np.nan)
    if escala < 1 or len(x) < escala:
        return out
    c = np.convolve(x, np.ones(escala), "valid")
    out[escala - 1:] = c
    return out


# ---------------------------------------------------------------- SPI

def _spi_mes(valores, base):
    """SPI de un mes calendario: gamma (loc=0) ajustada a los valores >0 del período base, más la
    probabilidad de cero (McKee et al., 1993; Stagge et al., 2015 para los ceros)."""
    base = base[np.isfinite(base)]
    if len(base) < 10:
        return np.full_like(valores, np.nan)
    positivos = base[base > 0]
    n0 = int((base <= 0).sum())
    q = (n0 + 1) / (2 * (len(base) + 1)) if n0 > 0 else 0.0  # centro de masa de los ceros
    out = np.full_like(valores, np.nan)
    ok = np.isfinite(valores)
    if len(positivos) < 5 or np.ptp(positivos) == 0:
        return out
    forma, _, escala = stats.gamma.fit(positivos, floc=0)
    g = stats.gamma.cdf(np.maximum(valores[ok], 0), forma, loc=0, scale=escala)
    h = np.where(valores[ok] <= 0, q, q + (1 - q) * g)
    out[ok] = stats.norm.ppf(np.clip(h, PROB_MIN, 1 - PROB_MIN))
    return out


def spi(precip_mensual, meses, escala, base_mascara=None):
    """SPI a `escala` meses. precip_mensual y meses (1–12) alineados y consecutivos.

    base_mascara: booleano, qué meses (fin de la ventana) forman la distribución de referencia
    (por defecto todos). Devuelve un arreglo del mismo largo con NaN donde no hay ventana completa.
    """
    acum = suma_movil(precip_mensual, escala)
    meses = np.asarray(meses)
    base = np.ones(len(acum), bool) if base_mascara is None else np.asarray(base_mascara, bool)
    out = np.full_like(acum, np.nan)
    for m in range(1, 13):
        sel = meses == m
        out[sel] = _spi_mes(acum[sel], acum[sel & base])
    return out


# ---------------------------------------------------------------- SPEI

def radiacion_extraterrestre(lat_grados, doy):
    """Ra en MJ m⁻² día⁻¹ (FAO-56, ec. 21–25)."""
    phi = np.radians(lat_grados)
    doy = np.asarray(doy, float)
    dr = 1 + 0.033 * np.cos(2 * np.pi / 365 * doy)
    delta = 0.409 * np.sin(2 * np.pi / 365 * doy - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1, 1))
    return 24 * 60 / np.pi * 0.0820 * dr * (ws * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(ws))


def etp_hargreaves(tmed, tmax, tmin, lat_grados, doy):
    """Evapotranspiración de referencia diaria (mm/día), Hargreaves–Samani (FAO-56, ec. 52)."""
    ra_mm = 0.408 * radiacion_extraterrestre(lat_grados, doy)  # MJ → mm de agua evaporada
    rango = np.maximum(np.asarray(tmax, float) - np.asarray(tmin, float), 0)
    return np.maximum(0.0023 * (np.asarray(tmed, float) + 17.8) * np.sqrt(rango) * ra_mm, 0)


def _pwm(x):
    """Momentos ponderados por probabilidad w0, w1, w2 con F = (i − 0,35)/n (Vicente-Serrano et al., 2010)."""
    x = np.sort(x)
    n = len(x)
    f = (np.arange(1, n + 1) - 0.35) / n
    return [float(np.mean((1 - f) ** s * x)) for s in range(3)]


def ajustar_loglogistica(x):
    """Parámetros (alfa, beta, gamma) de la log-logística de 3 parámetros por momentos L."""
    w0, w1, w2 = _pwm(x)
    beta = (2 * w1 - w0) / (6 * w1 - w0 - 6 * w2)
    if not math.isfinite(beta) or beta <= 1:
        raise ValueError("Log-logística sin solución (beta ≤ 1).")
    g = special.gamma(1 + 1 / beta) * special.gamma(1 - 1 / beta)
    alfa = (w0 - 2 * w1) * beta / g
    gamma = w0 - alfa * g
    return alfa, beta, gamma


def cdf_loglogistica(x, alfa, beta, gamma):
    x = np.asarray(x, float)
    z = np.where(x > gamma, (alfa / np.maximum(x - gamma, 1e-12)) ** beta, np.inf)
    return 1 / (1 + z)


def spei(balance_mensual, meses, escala, base_mascara=None):
    """SPEI a `escala` meses a partir del balance mensual P − ETP (mm)."""
    acum = suma_movil(balance_mensual, escala)
    meses = np.asarray(meses)
    base = np.ones(len(acum), bool) if base_mascara is None else np.asarray(base_mascara, bool)
    out = np.full_like(acum, np.nan)
    for m in range(1, 13):
        sel = meses == m
        ref = acum[sel & base]
        ref = ref[np.isfinite(ref)]
        if len(ref) < 10:
            continue
        v = acum[sel]
        ok = np.isfinite(v)
        r = np.full(len(v), np.nan)
        try:
            par = ajustar_loglogistica(ref)
            r[ok] = stats.norm.ppf(np.clip(cdf_loglogistica(v[ok], *par), PROB_MIN, 1 - PROB_MIN))
        except ValueError:
            # Muestra con asimetría negativa: la log-logística no tiene solución. Se usa una normal
            # ajustada al período base (alternativa declarada; ocurre en meses muy húmedos y regulares).
            r[ok] = (v[ok] - ref.mean()) / ref.std(ddof=1)
        out[sel] = r
    return out


def categoria_sequia(indice):
    """Categoría del SPI/SPEI (McKee et al., 1993)."""
    if not math.isfinite(indice):
        return None
    if indice <= -2:
        return "extrema"
    if indice <= -1.5:
        return "severa"
    if indice <= -1:
        return "moderada"
    if indice < 0:
        return "leve"
    return "sin_sequia"


# ---------------------------------------------------------------- extremos de lluvia (ETCCDI)

def racha_maxima(condicion):
    mejor = actual = 0
    for c in condicion:
        actual = actual + 1 if c else 0
        mejor = max(mejor, actual)
    return mejor


def percentil_humedo(fechas, pr, anios_base, q=95):
    """Percentil q de los días húmedos (≥ 1 mm) del período base."""
    anio, _, _ = descomponer(fechas)
    pr = np.asarray(pr, float)
    sel = np.isin(anio, list(anios_base)) & np.isfinite(pr) & (pr >= UMBRAL_HUMEDO)
    return float(np.percentile(pr[sel], q))


def indices_lluvia(fechas, pr, anios_base):
    """Índices anuales de lluvia. Devuelve {anio: {indice: valor}} solo para años completos (sin NaN)."""
    anio, mes, _ = descomponer(fechas)
    pr = np.asarray(pr, float)
    p95 = percentil_humedo(fechas, pr, anios_base, 95)
    out = {}
    for a in np.unique(anio):
        sel = anio == a
        x = pr[sel]
        if len(x) < 365 or not np.all(np.isfinite(x)):
            continue
        humedo = x >= UMBRAL_HUMEDO
        x5 = np.convolve(x, np.ones(5), "valid")
        lluviosa = (mes[sel] >= 5) & (mes[sel] <= 10)
        out[int(a)] = {
            "prcptot": float(x[humedo].sum()),
            "rx1day": float(x.max()),
            "rx5day": float(x5.max()),
            "r95p": float(x[x > p95].sum()),
            "r95ptot": float(x[x > p95].sum() / x[humedo].sum() * 100) if humedo.any() else 0.0,
            "r10mm": int((x >= 10).sum()),
            "r20mm": int((x >= 20).sum()),
            "sdii": float(x[humedo].mean()) if humedo.any() else 0.0,
            "cdd": racha_maxima(~humedo),
            "cwd": racha_maxima(humedo),
            "cdd_may_oct": racha_maxima(~humedo[lluviosa]),
        }
    return out, p95


# ---------------------------------------------------------------- extremos de calor (ETCCDI)

def umbral_diario(fechas, t, anios_base, q=90, ventana=5):
    """Percentil q por día del año (1–366) con ventana centrada de `ventana` días, en el período base."""
    anio, _, doy = descomponer(fechas)
    t = np.asarray(t, float)
    base = np.isin(anio, list(anios_base)) & np.isfinite(t)
    mitad = ventana // 2
    umbral = np.full(367, np.nan)
    for d in range(1, 367):
        vecinos = [((d - 1 + k) % 366) + 1 for k in range(-mitad, mitad + 1)]
        sel = base & np.isin(doy, vecinos)
        if sel.sum() >= 10:
            umbral[d] = np.percentile(t[sel], q)
    umbral[366] = umbral[366] if np.isfinite(umbral[366]) else umbral[365]
    return umbral


def indices_calor(fechas, tmax, tmin, tmed, anios_base):
    """TX90p, TN90p (% de días), TXx, TNn y medias anuales. Sin remuestreo (bootstrap) dentro del
    período base (Zhang et al., 2005): los años base pueden tener un sesgo pequeño hacia el 10 %."""
    anio, _, doy = descomponer(fechas)
    tx, tn, tm = (np.asarray(v, float) for v in (tmax, tmin, tmed))
    ux = umbral_diario(fechas, tx, anios_base)
    un = umbral_diario(fechas, tn, anios_base)
    out = {}
    for a in np.unique(anio):
        sel = anio == a
        if sel.sum() < 365 or not (np.all(np.isfinite(tx[sel])) and np.all(np.isfinite(tn[sel]))):
            continue
        d = doy[sel]
        out[int(a)] = {
            "tx90p": float(np.mean(tx[sel] > ux[d]) * 100),
            "tn90p": float(np.mean(tn[sel] > un[d]) * 100),
            "txx": float(tx[sel].max()),
            "tnn": float(tn[sel].min()),
            "tmax_media": float(tx[sel].mean()),
            "tmin_media": float(tn[sel].mean()),
            "t2m_media": float(np.nanmean(tm[sel])),
            "dtr": float(np.mean(tx[sel] - tn[sel])),
        }
    return out


# ---------------------------------------------------------------- canícula

def _suavizar(x, ventana):
    k = np.ones(ventana) / ventana
    return np.convolve(np.pad(x, ventana // 2, mode="edge"), k, "valid")[: len(x)]


def climatologia_diaria(fechas, pr, anios_base, ventana=1):
    """Lluvia media por día del año (1–366); con ventana > 1, suavizada con media móvil circular.
    Por defecto sin suavizar: el déficit se suma sobre tramos de semanas, que ya promedian el ruido diario."""
    anio, _, doy = descomponer(fechas)
    pr = np.asarray(pr, float)
    clim = np.zeros(367)
    for d in range(1, 367):
        sel = (doy == d) & np.isin(anio, list(anios_base)) & np.isfinite(pr)
        clim[d] = pr[sel].mean() if sel.any() else np.nan
    clim[366] = clim[366] if np.isfinite(clim[366]) else clim[365]
    clim[0] = np.nan
    if ventana <= 1:
        return clim
    serie = clim[1:]
    mitad = ventana // 2
    ext = np.concatenate([serie[-mitad:], serie, serie[:mitad]])
    suav = np.convolve(ext, np.ones(ventana) / ventana, "valid")
    out = np.zeros(367)
    out[1:] = suav
    out[0] = np.nan
    return out


def canicula_anio(pr_anio, doy_anio, clim, suavizado=31, intensidad_minima=0.15):
    """Canícula de un año con lluvia diaria `pr_anio` (mm/día) y su día del año.

    Método (adaptado de Karnauskas et al., 2013, y Perdigón-Morales et al., 2018, a datos diarios):
    1. Media móvil de `suavizado` días.
    2. Primer máximo P1 entre el 15 de mayo y el 15 de julio (días 135–196); segundo P2 entre el 1 de
       agosto y el 31 de octubre (213–304); mínimo M entre ambos.
    3. Intensidad = 1 − M / media(P1, P2). Hay canícula si es ≥ `intensidad_minima`.
    4. Inicio y fin: primer y último día entre P1 y P2 con la serie suavizada por debajo de
       (M + media(P1, P2)) / 2. Duración = fin − inicio + 1.
    5. Déficit = Σ (climatología − observado) en los días de la canícula (mm; positivo = más seco
       que lo normal en esos días). Lluvia = Σ observado.
    """
    pr = np.asarray(pr_anio, float)
    doy = np.asarray(doy_anio)
    if len(pr) < 365 or not np.all(np.isfinite(pr)):
        return {"detectada": False, "motivo": "anio_incompleto"}
    s = _suavizar(pr, suavizado)
    v1 = (doy >= 135) & (doy <= 196)
    v2 = (doy >= 213) & (doy <= 304)
    i1 = int(np.flatnonzero(v1)[np.argmax(s[v1])])
    i2 = int(np.flatnonzero(v2)[np.argmax(s[v2])])
    if i2 - i1 < 10:
        return {"detectada": False, "motivo": "maximos_contiguos"}
    im = i1 + int(np.argmin(s[i1:i2 + 1]))
    pico = (s[i1] + s[i2]) / 2
    intensidad = float(1 - s[im] / pico) if pico > 0 else 0.0
    base = {"p1_doy": int(doy[i1]), "p2_doy": int(doy[i2]), "minimo_doy": int(doy[im]),
            "intensidad": round(intensidad, 4)}
    if intensidad < intensidad_minima or im in (i1, i2):
        return {"detectada": False, "motivo": "intensidad_baja", **base}
    umbral = (s[im] + pico) / 2
    bajo = np.flatnonzero(s[i1:i2 + 1] < umbral) + i1
    # tramo contiguo por debajo del umbral que contiene al mínimo
    inicio = fin = im
    while inicio - 1 >= i1 and s[inicio - 1] < umbral:
        inicio -= 1
    while fin + 1 <= i2 and s[fin + 1] < umbral:
        fin += 1
    if len(bajo) == 0:
        return {"detectada": False, "motivo": "sin_tramo", **base}
    sel = slice(inicio, fin + 1)
    clim_dias = clim[doy[sel]]
    return {"detectada": True, **base, "inicio_doy": int(doy[inicio]), "fin_doy": int(doy[fin]),
            "duracion_dias": int(fin - inicio + 1), "lluvia_mm": float(pr[sel].sum()),
            "deficit_mm": float(np.sum(clim_dias - pr[sel]))}


def canicula_ventana_fija(pr_anio, doy_anio, clim, inicio=196, fin=227):
    """Lluvia, anomalía y racha seca máxima (< 1 mm) del 15 de julio al 15 de agosto (días 196–227)."""
    pr = np.asarray(pr_anio, float)
    doy = np.asarray(doy_anio)
    sel = (doy >= inicio) & (doy <= fin)
    x = pr[sel]
    return {"lluvia_mm": float(x.sum()), "anomalia_mm": float(x.sum() - clim[doy[sel]].sum()),
            "racha_seca_max_dias": racha_maxima(x < UMBRAL_HUMEDO)}


def canicula(fechas, pr, anios_base, **kw):
    """Canícula por año: {anio: {"objetiva": {...}, "ventana_fija": {...}}}."""
    anio, _, doy = descomponer(fechas)
    pr = np.asarray(pr, float)
    clim = climatologia_diaria(fechas, pr, anios_base)
    out = {}
    for a in np.unique(anio):
        sel = anio == a
        if sel.sum() < 365:
            continue
        out[int(a)] = {"objetiva": canicula_anio(pr[sel], doy[sel], clim, **kw),
                       "ventana_fija": canicula_ventana_fija(pr[sel], doy[sel], clim)}
    return out
