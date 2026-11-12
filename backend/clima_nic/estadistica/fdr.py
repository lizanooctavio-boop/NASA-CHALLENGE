"""Control de la tasa de falsos descubrimientos (FDR) para mapas de tendencias.

Con decenas de celdas, ~5 % saldrían «significativas» al 5 % por azar. Benjamini y Hochberg (1995): se ordenan
los p-valores y se declara significativa la celda i si p_(i) ≤ (i / m)·q. Wilks (2016, BAMS) recomienda
q = 0,10 para campos con correlación espacial, que así controlan la FDR global en torno a 0,05.
"""
import numpy as np


def benjamini_hochberg(p_valores, q=0.10):
    """Devuelve (significativo: lista de bool, umbral p usado o 0 si ninguna)."""
    p = np.asarray(p_valores, float)
    m = len(p)
    if m == 0:
        return [], 0.0
    orden = np.argsort(p)
    limites = q * np.arange(1, m + 1) / m
    pasa = p[orden] <= limites
    if not pasa.any():
        return [False] * m, 0.0
    k = int(np.max(np.flatnonzero(pasa)))
    umbral = float(p[orden][k])
    return [bool(x <= umbral) for x in p], umbral
