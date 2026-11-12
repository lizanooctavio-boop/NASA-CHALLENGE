"""Pruebas de los indicadores, la detección de tendencias y el modelo estacional (datos sintéticos).

El archivo generado se prueba en test_backend_clima_nic.py.

    python -m pytest tests/test_indicadores_nicaragua.py -q
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

from clima_nic.estadistica import indicadores as ind  # noqa: E402
from clima_nic.estadistica import modelo_estacional as me  # noqa: E402
from clima_nic.estadistica import tendencia_robusta as tr  # noqa: E402


def fechas(inicio="1991-01-01", fin="2020-12-31"):
    return np.arange(np.datetime64(inicio), np.datetime64(fin) + np.timedelta64(1, "D"))


# ---------------------------------------------------------------- utilidades

def test_descomponer_y_bisiesto():
    a, m, d = ind.descomponer(np.array(["2024-02-29", "2023-12-31", "2024-12-31"], "datetime64[D]"))
    assert a.tolist() == [2024, 2023, 2024]
    assert m.tolist() == [2, 12, 12]
    assert d.tolist() == [60, 365, 366]


def test_mensual_desde_diario_suma_y_mes_incompleto():
    f = fechas("2020-01-01", "2020-03-31")
    v = np.ones(len(f))
    v[40] = np.nan  # febrero incompleto
    a, m, s = ind.mensual_desde_diario(f, v)
    assert m.tolist() == [1, 2, 3]
    assert s[0] == 31 and math.isnan(s[1]) and s[2] == 31


def test_suma_movil():
    out = ind.suma_movil([1, 2, 3, 4], 3)
    assert math.isnan(out[0]) and math.isnan(out[1])
    assert out[2:].tolist() == [6, 9]


# ---------------------------------------------------------------- sequía

def test_spi_de_datos_gamma_es_normal_estandar():
    rng = np.random.default_rng(1)
    n = 60 * 12
    p = rng.gamma(2.0, 50.0, n)
    meses = np.tile(np.arange(1, 13), 60)
    s = ind.spi(p, meses, 1)
    assert abs(np.mean(s)) < 0.1
    assert abs(np.std(s) - 1) < 0.1


def test_spi_con_ceros_y_monotonia():
    rng = np.random.default_rng(2)
    p = rng.gamma(1.5, 30.0, 40 * 12)
    p[rng.random(len(p)) < 0.2] = 0.0
    meses = np.tile(np.arange(1, 13), 40)
    s = ind.spi(p, meses, 1)
    for m in range(1, 13):
        sel = meses == m
        orden = np.argsort(p[sel])
        assert np.all(np.diff(s[sel][orden]) >= -1e-9)  # monótono en la lluvia
    assert np.all(np.isfinite(s))


def test_spi3_tiene_nan_al_inicio():
    p = np.random.default_rng(3).gamma(2, 40, 30 * 12)
    s = ind.spi(p, np.tile(np.arange(1, 13), 30), 3)
    assert np.isnan(s[:2]).all() and np.isfinite(s[2:]).all()


def test_radiacion_extraterrestre_fao56_ejemplo_8():
    # FAO-56, ejemplo 8: 20° S, 3 de septiembre (día 246) → Ra = 32,2 MJ m⁻² día⁻¹
    assert ind.radiacion_extraterrestre(-20, 246) == pytest.approx(32.2, abs=0.1)


def test_hargreaves_orden_de_magnitud_tropical():
    et = ind.etp_hargreaves(27, 32, 22, 12.5, 100)
    assert 4 < et < 6.5
    assert ind.etp_hargreaves(27, 22, 32, 12.5, 100) == 0  # rango negativo → 0


def test_loglogistica_recupera_parametros():
    alfa, beta, gamma = 80.0, 4.0, -50.0
    u = np.random.default_rng(4).random(5000)
    x = gamma + alfa * (u / (1 - u)) ** (1 / beta)  # inversa de la CDF
    a, b, g = ind.ajustar_loglogistica(x)
    assert b == pytest.approx(beta, rel=0.1)
    assert a == pytest.approx(alfa, rel=0.1)
    assert ind.cdf_loglogistica(np.median(x), a, b, g) == pytest.approx(0.5, abs=0.03)


def test_spei_aproximadamente_normal():
    rng = np.random.default_rng(5)
    n = 50 * 12
    balance = rng.normal(20, 60, n)
    s = ind.spei(balance, np.tile(np.arange(1, 13), 50), 3)
    ok = np.isfinite(s)
    assert ok.sum() == n - 2
    assert abs(np.mean(s[ok])) < 0.1 and abs(np.std(s[ok]) - 1) < 0.15


def test_categoria_sequia():
    assert ind.categoria_sequia(-2.1) == "extrema"
    assert ind.categoria_sequia(-1.6) == "severa"
    assert ind.categoria_sequia(-1.2) == "moderada"
    assert ind.categoria_sequia(-0.3) == "leve"
    assert ind.categoria_sequia(0.4) == "sin_sequia"
    assert ind.categoria_sequia(float("nan")) is None


# ---------------------------------------------------------------- extremos de lluvia

def test_indices_lluvia_serie_construida():
    f = fechas("2001-01-01", "2001-12-31")
    pr = np.zeros(len(f))
    pr[100:110] = 5.0          # 10 días húmedos seguidos
    pr[200] = 80.0             # máximo diario
    pr[201:205] = 10.0
    out, p95 = ind.indices_lluvia(f, pr, [2001])
    r = out[2001]
    assert r["rx1day"] == 80
    assert r["rx5day"] == 120
    assert r["prcptot"] == pytest.approx(50 + 80 + 40)
    assert r["cwd"] == 10
    assert r["cdd"] == 160     # días 206–365 secos (más larga que la de los días 1–100)
    assert r["r10mm"] == 5 and r["r20mm"] == 1
    assert r["sdii"] == pytest.approx(170 / 15)
    assert r["r95p"] == pytest.approx(80)      # solo el día por encima del p95 de los días húmedos
    assert p95 > 10


def test_indices_lluvia_omite_anio_con_faltantes():
    f = fechas("2001-01-01", "2002-12-31")
    pr = np.ones(len(f))
    pr[400] = np.nan
    out, _ = ind.indices_lluvia(f, pr, [2001, 2002])
    assert list(out) == [2001]


def test_racha_maxima():
    assert ind.racha_maxima([True, True, False, True, True, True]) == 3
    assert ind.racha_maxima([]) == 0


# ---------------------------------------------------------------- extremos de calor

def test_indices_calor_tx90p_cerca_de_10_en_clima_estable_y_sube_con_calentamiento():
    rng = np.random.default_rng(6)
    f = fechas("1991-01-01", "2024-12-31")
    a, _, doy = ind.descomponer(f)
    ciclo = 2 * np.sin(2 * np.pi * doy / 365.25)
    tx = 31 + ciclo + rng.normal(0, 1, len(f))
    tn = 21 + ciclo + rng.normal(0, 1, len(f))
    tx[a >= 2021] += 1.5       # calentamiento después del período base
    out = ind.indices_calor(f, tx, tn, (tx + tn) / 2, range(1991, 2021))
    base = np.mean([out[y]["tx90p"] for y in range(1991, 2021)])
    assert 7 < base < 13
    assert np.mean([out[y]["tx90p"] for y in range(2021, 2025)]) > 30
    assert np.mean([out[y]["tn90p"] for y in range(2021, 2025)]) < 15
    assert out[2001]["dtr"] == pytest.approx(10, abs=0.3)


# ---------------------------------------------------------------- canícula

def _lluvia_bimodal(anios, profundidad=0.6, ruido=0.0, semilla=7):
    rng = np.random.default_rng(semilla)
    f = fechas(f"{anios[0]}-01-01", f"{anios[-1]}-12-31")
    _, _, doy = ind.descomponer(f)
    p1 = np.exp(-0.5 * ((doy - 165) / 18) ** 2)
    p2 = np.exp(-0.5 * ((doy - 265) / 22) ** 2)
    hueco = 1 - profundidad * np.exp(-0.5 * ((doy - 213) / 12) ** 2)
    base = 10 * (p1 + p2) * hueco + 10 * np.exp(-0.5 * ((doy - 213) / 40) ** 2) * (1 - profundidad)
    pr = np.maximum(base + ruido * rng.normal(0, 1, len(f)), 0)
    return f, pr


def test_canicula_detectada_en_regimen_bimodal():
    f, pr = _lluvia_bimodal([2001, 2010])
    out = ind.canicula(f, pr, range(2001, 2011))
    c = out[2005]["objetiva"]
    assert c["detectada"]
    assert 180 <= c["inicio_doy"] < c["minimo_doy"] < c["fin_doy"] <= 250
    assert 195 <= c["minimo_doy"] <= 230
    assert c["intensidad"] > 0.3
    assert c["deficit_mm"] == pytest.approx(0, abs=1e-6)  # igual a su propia climatología
    assert out[2005]["ventana_fija"]["racha_seca_max_dias"] == 0


def test_canicula_ausente_en_regimen_unimodal():
    f = fechas("2001-01-01", "2005-12-31")
    _, _, doy = ind.descomponer(f)
    pr = 10 * np.exp(-0.5 * ((doy - 215) / 50) ** 2)
    out = ind.canicula(f, pr, range(2001, 2006))
    assert not out[2003]["objetiva"]["detectada"]


def test_canicula_deficit_positivo_si_el_anio_es_mas_seco():
    f, pr = _lluvia_bimodal([2001, 2010])
    a, _, doy = ind.descomponer(f)
    pr = pr.copy()
    pr[(a == 2007) & (doy >= 190) & (doy <= 240)] *= 0.2
    out = ind.canicula(f, pr, range(2001, 2011))
    assert out[2007]["objetiva"]["deficit_mm"] > 0
    assert out[2007]["ventana_fija"]["anomalia_mm"] < 0


# ---------------------------------------------------------------- tendencias

def test_mann_kendall_modificado_ruido_blanco_y_tendencia():
    rng = np.random.default_rng(8)
    ruido = rng.normal(0, 1, 40)
    assert not tr.mann_kendall_modificado(ruido)["significativo"]
    con = ruido + 0.15 * np.arange(40)
    r = tr.mann_kendall_modificado(con)
    assert r["significativo"] and r["z"] > 0


def test_mann_kendall_modificado_coincide_con_clasico_sin_autocorrelacion():
    y = np.array([3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9, 3, 2, 3, 8, 4], float)
    r = tr.mann_kendall_modificado(y)
    if r["factor_correccion"] == 1:
        tau, _ = stats.kendalltau(np.arange(len(y)), y)
        assert r["tau"] == pytest.approx(tau, abs=0.05)  # tau-a vs tau-b con empates


def test_mann_kendall_modificado_ensancha_con_autocorrelacion():
    rng = np.random.default_rng(9)
    e = np.zeros(44)
    for i in range(1, 44):
        e[i] = 0.8 * e[i - 1] + rng.normal()
    r = tr.mann_kendall_modificado(e + 0.05 * np.arange(44))
    assert r["factor_correccion"] >= 1


def test_theil_sen_ic_contiene_pendiente_verdadera():
    rng = np.random.default_rng(10)
    anios = np.arange(1981, 2025)
    y = 100 + 2.0 * (anios - 1981) + rng.normal(0, 5, len(anios))
    r = tr.theil_sen(anios, y)
    assert r["ic_por_decada"][0] < 20 < r["ic_por_decada"][1]


def test_pettitt_localiza_salto():
    rng = np.random.default_rng(11)
    anios = list(range(1981, 2025))
    y = np.r_[rng.normal(0, 1, 20), rng.normal(3, 1, 24)]
    r = tr.pettitt(anios, y)
    assert r["anio_cambio"] in (2000, 2001, 2002)
    assert r["p_valor"] < 0.01 and r["salto"] > 2


def test_pettitt_sin_cambio():
    y = np.random.default_rng(12).normal(0, 1, 44)
    assert tr.pettitt(list(range(1981, 2025)), y)["p_valor"] > 0.05


def test_regresion_controlada_recupera_coeficientes():
    rng = np.random.default_rng(13)
    anios = np.arange(1981, 2025)
    enso = rng.normal(0, 1, len(anios))
    y = 1500 + 3.0 * (anios - anios.mean()) - 120 * enso + rng.normal(0, 20, len(anios))
    r = tr.regresion_controlada(anios, y, {"nino34": enso})
    assert r["por_decada"] == pytest.approx(30, abs=10)
    assert r["ic_por_decada"][0] < r["por_decada"] < r["ic_por_decada"][1]
    c = r["covariables"]["nino34"]
    assert c["ic"][0] < -120 < c["ic"][1] and c["p_valor"] < 0.001
    assert r["r2"] > 0.9


def test_analizar_veredictos_y_campos():
    rng = np.random.default_rng(14)
    anios = list(range(1981, 2025))
    plano = tr.analizar(anios, rng.normal(25, 0.3, 44), "°C")
    assert plano["veredicto"] in ("evidencia_insuficiente", "metodos_discrepan")
    cal = tr.analizar(anios, 25 + 0.03 * np.arange(44) + rng.normal(0, 0.1, 44), "°C",
                      covariables={"nino34": rng.normal(0, 1, 44)})
    assert cal["veredicto"] == "tendencia_detectada"
    assert cal["unidad_pendiente"] == "°C/década"
    assert cal["minimos_cuadrados"]["por_decada"] == pytest.approx(0.3, abs=0.08)
    assert "controlada_por_indices" in cal and "pettitt" in cal


def test_analizar_pocos_anios():
    assert tr.analizar(list(range(2001, 2008)), [1, 2, 3, 4, 5, 6, 7], "mm")["veredicto"] == "datos_insuficientes"


# ---------------------------------------------------------------- modelo estacional

def test_validacion_cruzada_con_senal_supera_climatologia():
    rng = np.random.default_rng(15)
    x = rng.normal(0, 1, 44)
    y = 1000 - 150 * x + rng.normal(0, 80, 44)
    r = me.evaluar(y, x, permutaciones=200)
    assert r["bloque_1"]["msess"] > 0.5 and r["bloque_3"]["msess"] > 0.4
    assert r["bloque_1"]["aciertos_tercil"] > 0.5
    assert r["p_permutacion_msess"] < 0.01


def test_validacion_cruzada_sin_senal_no_supera_climatologia():
    rng = np.random.default_rng(16)
    r = me.evaluar(rng.normal(1000, 100, 44), rng.normal(0, 1, 44), permutaciones=200)
    assert r["bloque_1"]["msess"] < 0.05
    assert r["p_permutacion_msess"] > 0.05


def test_climatologia_loo_es_media_de_los_demas():
    y = np.array([1.0, 2.0, 3.0, 4.0, 10.0, 6.0, 7.0, 8.0, 9.0, 5.0])
    r = me.validacion_cruzada(y, None)
    assert r["climatologia"][4] == pytest.approx((y.sum() - 10) / 9)
    assert r["msess"] == pytest.approx(0.0)


def test_resumen_quita_listas():
    rng = np.random.default_rng(17)
    r = me.resumen(me.evaluar(rng.normal(size=20), rng.normal(size=20), permutaciones=10))
    assert "pronosticos" not in r["bloque_1"]


def test_msess_loo_cerrado_igual_al_bucle():
    rng = np.random.default_rng(18)
    x = rng.normal(size=(30, 2))
    y = 3 * x[:, 0] + rng.normal(size=30)
    assert me.msess_loo(y, x) == pytest.approx(me.validacion_cruzada(y, x, 1)["msess"], abs=1e-10)
