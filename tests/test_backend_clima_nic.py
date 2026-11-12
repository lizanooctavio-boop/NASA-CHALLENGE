"""Pruebas del backend clima_nic: adaptadores (con mallas y archivos sintéticos), agro, FDR, horizontes del
modelo estacional, escenarios, regiones, consulta y API.

    python -m pytest tests -q
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

from clima_nic import agro, proyecciones, regiones  # noqa: E402
from clima_nic.estadistica import modelo_estacional as me  # noqa: E402
from clima_nic.estadistica.fdr import benjamini_hochberg  # noqa: E402
from clima_nic.fuentes import REGISTRO, base, obtener  # noqa: E402
from clima_nic.fuentes.lagos import leer_grealm  # noqa: E402
from clima_nic.fuentes.nex_gddp import _fechas_modelo  # noqa: E402
from clima_nic.fuentes.power import Power, cajas_regionales, indice_pdo  # noqa: E402
from clima_nic.fuentes.smap import recortar_puntos  # noqa: E402

shapely = pytest.importorskip("shapely")
from shapely.geometry import box  # noqa: E402

REGIONES_PRUEBA = {"oeste": box(-87, 11, -85.5, 13), "este": box(-85.5, 11, -84, 13)}


# ---------------------------------------------------------------- registro y metadatos

def test_registro_tiene_todas_las_fuentes_pedidas():
    for k in ("power", "imerg", "merra2", "modis", "smap", "grace_fo", "gistemp", "nex_gddp_cmip6", "lagos"):
        assert k in REGISTRO
        a = obtener(k)
        m = a.metadatos()
        assert m["id"] == k and m["periodo"] and m["resolucion_espacial"]
        ok, motivo = a.disponible()
        assert isinstance(ok, bool) and motivo


def test_adaptadores_earthdata_se_declaran(monkeypatch, tmp_path):
    monkeypatch.setenv("NETRC", str(tmp_path / "no_existe"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    for k in ("imerg", "merra2", "smap", "grace_fo"):
        a = obtener(k)
        assert a.requiere_earthdata
        assert a.disponible()[0] is False
    from clima_nic.fuentes import earthdata
    with pytest.raises(base.RequiereEarthdata):
        earthdata.abridor()


def test_hay_credenciales_lee_netrc_sin_exponerlo(monkeypatch, tmp_path):
    from clima_nic.fuentes import earthdata
    netrc = tmp_path / "netrc_prueba"
    netrc.write_text("machine urs.earthdata.nasa.gov login usuario_prueba password clave_prueba\n")
    monkeypatch.setenv("NETRC", str(netrc))
    assert earthdata.hay_credenciales()


# ---------------------------------------------------------------- recorte de mallas

def test_recortar_malla_media_ponderada_por_area():
    lat = np.arange(10.05, 14, 0.1)
    lon = np.arange(-87.95, -83.5, 0.1)
    campo = np.where(lon[None, :] < -85.5, 1.0, 3.0) * np.ones((len(lat), 1))
    series, pesos = base.recortar_malla(lat, lon, campo, REGIONES_PRUEBA)
    assert series["oeste"][0] == pytest.approx(1.0, abs=1e-9)
    assert series["este"][0] == pytest.approx(3.0, abs=1e-9)
    assert all(p["oeste"] >= 0 for p in pesos)


def test_recortar_malla_lon_0_360_y_nan():
    lat = np.arange(10.125, 14, 0.25)
    lon = np.arange(272.125, 276.5, 0.25)  # = −87,875 … −83,625
    campo = np.ones((2, len(lat), len(lon)))
    campo[1, :, :3] = np.nan
    series, _ = base.recortar_malla(lat, lon, campo, REGIONES_PRUEBA)
    assert series["oeste"].tolist() == pytest.approx([1.0, 1.0])


def test_recortar_puntos_ease():
    lat2d, lon2d = np.meshgrid(np.linspace(10.5, 13.5, 30), np.linspace(-87.5, -83.5, 40), indexing="ij")
    campo = np.where(lon2d < -85.5, 0.2, 0.4)
    out = recortar_puntos(lat2d, lon2d, campo, REGIONES_PRUEBA)
    assert out["oeste"][0] == pytest.approx(0.2)
    assert out["este"][0] == pytest.approx(0.4)


def test_a_mensual_y_anual():
    f = np.arange(np.datetime64("2001-01-01"), np.datetime64("2003-01-01"))
    t, v = base.a_mensual(f, np.ones(len(f)))
    assert t[0] == "2001-01" and v[0] == 31 and len(t) == 24
    anios, vals = base.a_anual(t, v)
    assert anios == [2001, 2002] and vals == [365, 365]


# ---------------------------------------------------------------- POWER

def test_power_cajas_regionales_respetan_limite():
    for la, lo in cajas_regionales((0, 60), (-80, 0)):
        assert 2 <= la[1] - la[0] <= 10 and 2 <= lo[1] - lo[0] <= 10
    bloques = cajas_regionales((20, 60), (120, 250))  # cruza 180°
    assert any(lo[0] < 0 for _, lo in bloques) and any(lo[0] > 0 for _, lo in bloques)


def test_power_leer_punto_sintetico(tmp_path):
    datos = {"geometry": {"coordinates": [-86.0, 12.5, 100.0]}, "header": {"fill_value": -999.0},
             "properties": {"parameter": {"T2M": {"20010101": 25.0, "20010102": -999.0},
                                          "PRECTOTCORR": {"20010101": 3.0, "20010102": 0.0}}}}
    r = tmp_path / "p.json"
    r.write_text(json.dumps(datos))
    f, d, elev = Power.leer_punto(r)
    assert str(f[0]) == "2001-01-01" and elev == 100.0
    assert d["T2M"][0] == 25.0 and math.isnan(d["T2M"][1])


def test_pdo_recupera_modo_principal():
    rng = np.random.default_rng(1)
    n = 360
    anios = np.repeat(np.arange(1981, 2011), 12)
    meses = np.tile(np.arange(1, 13), 30)
    lat = np.repeat(np.arange(22.0, 58.0, 4.0), 10)
    patron = np.where((lat >= 30) & (lat <= 45), -1.0, 0.5)
    pc = np.cumsum(rng.normal(0, 0.3, n))
    x = 15 + pc[:, None] * patron[None, :] + rng.normal(0, 0.1, (n, len(lat)))
    pdo = np.array(indice_pdo(anios, meses, x, lat, base=(1981, 2010)))
    assert np.corrcoef(pdo, pc)[0, 1] > 0.9  # signo: positivo con el centro del Pacífico Norte frío


# ---------------------------------------------------------------- otros adaptadores

def test_grealm_parser_formato_antiguo():
    texto = "Lake Nicaragua\nYYYYMMDD height\n19930105  0.52\n19930115 999.99\n2015.5 -0.80\nbasura\n"
    obs = leer_grealm(texto)
    assert [o["variacion_m"] for o in obs] == [0.52, -0.80]
    assert obs[0]["fecha"] == "1993-01-05" and obs[1]["fecha"].startswith("2015-07")


def test_grealm_parser_formato_gsfc():
    texto = ("000351 Nicaragua           : Target database id number and name\n"
             "  11.792  -85.714          : Latitude and longitude\n"
             "Column 15: Target height variation in EGM2008 datum\n"
             "POSDN   1 19921002  14 54   -0.19  0.051  11.88 ERA NIC ERA 3 9 0    31.84   0\n"
             "TOPEX   2 19921012  12 52  999.99 99.999 999.99 ERA DOR ERA 4 0 0  9999.99   0\n"
             "SEN6A 217 20261008  22  9    0.35  0.042  14.88 AMR GIM ECM 1 2 0    32.38   0\n")
    obs = leer_grealm(texto)
    assert len(obs) == 2  # la cabecera numérica y el relleno se excluyen
    assert obs[0] == {"fecha": "1992-10-02", "mision": "POSDN", "variacion_m": -0.19, "error_m": 0.051,
                      "altura_egm2008_m": 31.84}
    assert obs[1]["altura_egm2008_m"] == 32.38


def test_nex_calendarios_de_modelo():
    assert len(_fechas_modelo(2050, 360)) == 360
    d = _fechas_modelo(2048, 365)
    assert len(d) == 365 and np.datetime64("2048-02-29") not in d


# ---------------------------------------------------------------- agro

def test_penman_monteith_ejemplo_fao56():
    # FAO-56, ejemplo 18 (Bruselas, 6 de julio): ETo = 3,9 mm/día. Aquí ea sale de la HR media (73,5 %).
    eto = agro.eto_penman_monteith(21.5, 12.3, 73.5, 22.07, 2.078, 50.8, 187, 100)
    assert float(eto) == pytest.approx(3.9, abs=0.25)


def test_penman_monteith_tropical_y_hargreaves_coinciden_en_orden():
    pm = agro.eto_penman_monteith(32, 22, 70, 20, 2, 12.5, 100, 100)
    h = agro.eto_hargreaves(27, 32, 22, 12.5, 100)
    assert 3 < float(pm) < 7 and abs(float(pm) - float(h)) < 2


def test_grados_dia_y_balance():
    f = np.arange(np.datetime64("2001-01-01"), np.datetime64("2002-01-01"))
    g = agro.grados_dia(f, np.full(len(f), 32.0), np.full(len(f), 20.0))
    assert g[2001] == pytest.approx(365 * 15)  # techo 30: (30 + 20)/2 − 10
    assert agro.balance_hidrico([100], [130]).tolist() == [-30]


# ---------------------------------------------------------------- FDR

def test_benjamini_hochberg():
    p = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216]
    sig, umbral = benjamini_hochberg(p, q=0.05)
    assert sig[:2] == [True, True] and not any(sig[2:])
    assert umbral == 0.008
    assert benjamini_hochberg([0.5, 0.9])[0] == [False, False]


# ---------------------------------------------------------------- horizontes del modelo estacional

def test_ventana_predictor():
    assert me.nombre_ventana(me.ventana_predictor(6, 0)) == "MAM"
    assert me.nombre_ventana(me.ventana_predictor(6, 3)) == "DEF"
    assert me.ventana_predictor(6, 3)[0] == (-1, 12)  # diciembre del año anterior
    assert me.nombre_ventana(me.ventana_predictor(7, 6)) == "OND"


def test_serie_predictor_y_pronostico():
    rng = np.random.default_rng(3)
    anios = list(range(1981, 2025))
    idx = {(a, m): rng.normal() for a in range(1980, 2026) for m in range(1, 13)}
    x = me.serie_predictor(idx, anios + [2025], 6, 0)
    assert 2025 in x
    y = [1000 - 200 * x[a] + rng.normal(0, 50) for a in anios]
    p = me.pronostico(y, [[x[a]] for a in anios], [x[2025]])
    assert p["intervalo"][0] < p["valor_esperado"] < p["intervalo"][1]
    assert sum(p["prob_terciles"].values()) == pytest.approx(1)
    assert p["habilidad_loo"]["msess"] > 0.5


# ---------------------------------------------------------------- escenarios

def test_escenarios_delta():
    cm = {}
    for mo, (dp, dt) in {"A": (1.1, 1.5), "B": (0.9, 2.0), "C": (1.0, 1.0)}.items():
        for esc in ("historical", "ssp245", "ssp585"):
            a0, a1 = (1995, 2014) if esc == "historical" else (2041, 2060)
            fp = dp if esc != "historical" else 1
            ft = dt if esc != "historical" else 0
            cm[(mo, esc, "pr", "r")] = {(a, m): 100 * fp * (1.5 if mo == "A" else 1) for a in range(a0, a1 + 1) for m in range(1, 13)}
            cm[(mo, esc, "tas", "r")] = {(a, m): 26 + ft + (3 if mo == "B" else 0) for a in range(a0, a1 + 1) for m in range(1, 13)}
    obs_p = {(a, m): 120.0 for a in range(1995, 2015) for m in range(1, 13)}
    e = proyecciones.escenarios(cm, obs_p, "r", "pr")
    c = e["escenarios"]["ssp245"]["cambio"]
    assert c["minimo"] == pytest.approx(-10) and c["maximo"] == pytest.approx(10) and c["n_modelos"] == 3
    assert e["escenarios"]["ssp245"]["valor_proyectado"]["mediana"] == pytest.approx(1440)
    assert e["sesgo_modelos_historico"]["A"] == pytest.approx(25)  # sesgo informado, no trasladado
    obs_t = {(a, m): 27.0 for a in range(1995, 2015) for m in range(1, 13)}
    t = proyecciones.escenarios(cm, obs_t, "r", "tas")
    assert t["escenarios"]["ssp585"]["valor_proyectado"]["maximo"] == pytest.approx(29.0)
    assert "no es un pronóstico" in t["advertencia"]


# ---------------------------------------------------------------- regiones (archivo versionado)

GEO = RAIZ / "data" / "regiones_nicaragua.geojson"


@pytest.mark.skipif(not GEO.exists(), reason="sin regiones_nicaragua.geojson")
def test_regiones_particion_de_nic():
    d = json.loads(GEO.read_text(encoding="utf-8"))
    ids = [f["id"] for f in d["features"]]
    assert ids == ["NIC", "pacifico", "central", "caribe", "caja_sicc"]
    areas = {f["id"]: f["properties"]["area_km2"] for f in d["features"]}
    assert areas["pacifico"] + areas["central"] + areas["caribe"] == pytest.approx(areas["NIC"], rel=1e-4)
    g = regiones.cargar(GEO)
    assert g["pacifico"].intersection(g["caribe"]).area < 1e-6
    assert g["NIC"].contains(shapely.Point(-86.25, 12.13))  # Managua
    assert g["pacifico"].contains(shapely.Point(-86.88, 12.43))  # León


# ---------------------------------------------------------------- producto generado, consulta y API

FEN = RAIZ / "data" / "fenomenos_nicaragua.json"
requiere_producto = pytest.mark.skipif(not FEN.exists(), reason="data/fenomenos_nicaragua.json no generado")


def _sin_nan(v):
    if isinstance(v, dict):
        return all(_sin_nan(x) for x in v.values())
    if isinstance(v, list):
        return all(_sin_nan(x) for x in v)
    return not (isinstance(v, float) and not math.isfinite(v))


@requiere_producto
def test_producto_estructura_y_cuatro_preguntas():
    texto = FEN.read_text(encoding="utf-8")
    d = json.loads(texto)
    assert d["esquema"] == "nasa-challenge/fenomenos-nicaragua" and _sin_nan(d)
    assert [r["id"] for r in d["regiones"]] == ["NIC", "pacifico", "central", "caribe", "caja_sicc"]
    for r in d["regiones"]:
        v = r["variables"]["lluvia_jun_nov"]
        assert set(v["respuesta_reto"]) == {"que", "donde", "cuanto", "significativo"}
        assert "nino34" in v["tendencia"]["controlada_por_indices"]["covariables"]  # ENOS obligatorio en lluvia
    assert d["modelo_estacional"]["tipo"] == "pronostico"
    assert d["indices_climaticos"]["validacion_nino34_vs_oni_noaa"]["r"] > 0.95
    for m in d["mapas_tendencia"].values():
        assert m["n_significativas_fdr"] <= m["n_significativas_sin_fdr"]
    assert "C:\\" not in texto and "/Users/" not in texto


@requiere_producto
def test_consulta_y_api():
    from clima_nic import consulta
    r = consulta.consultar("pacifico", "lluvia_jun_nov", 1991, 2024, 2020)
    assert r["tendencia"]["periodo"] == [1991, 2024]
    assert r["tendencia"]["cuanto"]["unidad"] == "mm/década"
    p = r["pronostico_estacional"]
    assert p["disponible"] and p["intervalo"][0] <= p["valor_esperado"] <= p["intervalo"][1]
    futuro = consulta.pronostico_estacional("pacifico", 2031)
    assert futuro["disponible"] is False  # nunca extrapola sin predictores
    with pytest.raises(consulta.ConsultaInvalida):
        consulta.tendencia("marte", "lluvia_anual")
    fastapi = pytest.importorskip("fastapi")  # noqa: F841
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from clima_nic.api import app
    cli = TestClient(app)
    assert cli.get("/salud").json()["datos"] is True
    assert cli.get("/tendencia", params={"region": "central", "variable": "t2m_media"}).status_code == 200
    assert cli.get("/tendencia", params={"region": "x", "variable": "t2m_media"}).status_code == 400
    assert cli.get("/mapa", params={"variable": "prcptot"}).json()["celdas"]
