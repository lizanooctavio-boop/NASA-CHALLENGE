"""Variables agroclimáticas: ETo FAO-56 Penman–Monteith, Hargreaves, balance hídrico y grados-día.

ETo Penman–Monteith (Allen et al., 1998, FAO-56, ec. 6) con datos diarios de POWER/MERRA-2:
Tmax, Tmin (°C), humedad relativa media (%), radiación solar global (MJ m⁻² día⁻¹, ALLSKY_SFC_SW_DWN),
viento a 2 m (m/s, WS2M) y presión (kPa) o elevación. La radiación neta usa albedo 0,23, radiación de cielo
despejado Rso = (0,75 + 2·10⁻⁵ z) Ra (ec. 37) y la radiación de onda larga neta con ea a partir de la HR media
(ec. 19). El flujo de calor del suelo diario se toma como 0 (ec. 42).

La radiación de POWER empieza en 1984 (GEWEX SRB hasta 2000, CERES después): antes de 1984 la ETo PM es NaN
y para series largas se usa Hargreaves (sin radiación ni viento), con la advertencia del cambio de fuente.
"""
import math

import numpy as np

from .estadistica.indicadores import descomponer, etp_hargreaves, radiacion_extraterrestre

SIGMA = 4.903e-9  # MJ K⁻⁴ m⁻² día⁻¹


def presion_por_elevacion(z):
    return 101.3 * ((293 - 0.0065 * np.asarray(z, float)) / 293) ** 5.26


def es_t(t):
    return 0.6108 * np.exp(17.27 * np.asarray(t, float) / (np.asarray(t, float) + 237.3))


def eto_penman_monteith(tmax, tmin, hr_media, rs, u2, lat_grados, doy, elevacion_m, presion_kpa=None):
    tmax, tmin, hr, rs, u2 = (np.asarray(v, float) for v in (tmax, tmin, hr_media, rs, u2))
    tmed = (tmax + tmin) / 2
    p = presion_por_elevacion(elevacion_m) if presion_kpa is None else np.asarray(presion_kpa, float)
    gamma = 0.665e-3 * p
    delta = 4098 * es_t(tmed) / (tmed + 237.3) ** 2
    es = (es_t(tmax) + es_t(tmin)) / 2
    ea = hr / 100 * es
    ra = radiacion_extraterrestre(lat_grados, doy)
    rso = (0.75 + 2e-5 * elevacion_m) * ra
    rns = (1 - 0.23) * rs
    cociente = np.clip(np.where(rso > 0, rs / rso, np.nan), 0.25, 1.0)
    rnl = SIGMA * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2 * (0.34 - 0.14 * np.sqrt(np.maximum(ea, 0))) \
        * (1.35 * cociente - 0.35)
    rn = rns - rnl
    num = 0.408 * delta * rn + gamma * 900 / (tmed + 273) * u2 * (es - ea)
    den = delta + gamma * (1 + 0.34 * u2)
    return np.maximum(num / den, 0)


def eto_hargreaves(tmed, tmax, tmin, lat_grados, doy):
    return etp_hargreaves(tmed, tmax, tmin, lat_grados, doy)


def balance_hidrico(p, eto):
    """P − ETo (mm). Negativo = déficit atmosférico."""
    return np.asarray(p, float) - np.asarray(eto, float)


def grados_dia(fechas, tmax, tmin, base=10.0, techo=30.0):
    """Grados-día de crecimiento anuales (método de promedio con techo, base 10 °C y techo 30 °C)."""
    anio, _, _ = descomponer(fechas)
    tx = np.minimum(np.asarray(tmax, float), techo)
    tn = np.maximum(np.asarray(tmin, float), base)
    gdd = np.maximum((tx + tn) / 2 - base, 0)
    out = {}
    for a in np.unique(anio):
        sel = anio == a
        x = gdd[sel]
        out[int(a)] = float(x.sum()) if sel.sum() >= 365 and np.all(np.isfinite(x)) else math.nan
    return out
