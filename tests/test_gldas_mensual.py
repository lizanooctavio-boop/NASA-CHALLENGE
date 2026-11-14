"""Pruebas de GLDAS-2.1 mensual regional (clima_nic.fuentes.gldas_mensual), sin red.

    python -m pytest tests/test_gldas_mensual.py -q
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

from clima_nic.fuentes import gldas_mensual as gm  # noqa: E402

SALIDA = RAIZ / "data" / "recursos" / "tierra"


def _csv(valor=1.0, faltan=()):
    lineas = ["Dataset: GLDAS_NOAH025_M.A200101.021.nc4", "/lon, -87.875, -87.625", "/lat, 12.125, 12.375"]
    for v in gm.VARIABLES:
        if v in faltan:
            continue
        lineas += [f"/{v}[0][0], {valor}, -9999", f"/{v}[0][1], {valor}, {valor}"]
    return "\n".join(lineas)


def test_lee_csv_dap4_y_convierte_relleno_en_nan():
    lat, lon, campos = gm.leer_csv_dap(_csv(2.5))
    assert list(lat) == [12.125, 12.375] and list(lon) == [-87.875, -87.625]
    assert set(campos) == set(gm.VARIABLES)
    m = campos["Evap_tavg"]
    assert m.shape == (2, 2) and np.isnan(m[0, 1]) and m[1, 1] == 2.5


def test_rechaza_respuesta_incompleta():
    with pytest.raises(ValueError, match="incompleta"):
        gm.leer_csv_dap(_csv(faltan=("Qsb_acc",)))
    with pytest.raises(ValueError, match="incompleta"):
        gm.leer_csv_dap(_csv().replace("/Qs_acc[0][1], 1.0, 1.0\n", ""))


def test_conversiones_del_readme_gldas2():
    # README GLDAS-2 §3.5: tasa × 10 800 s × 8 × días; acumulado de 3 h × 8 × días
    assert gm.a_mensual_fisico("Evap_tavg", 1e-5, 2001, 4) == pytest.approx(1e-5 * 10800 * 8 * 30)
    assert gm.a_mensual_fisico("Qs_acc", 0.5, 2024, 2) == pytest.approx(0.5 * 8 * 29)  # bisiesto
    assert gm.a_mensual_fisico("SoilMoi0_10cm_inst", 30.0, 2001, 1) == pytest.approx(0.30)
    assert gm.a_mensual_fisico("SoilMoi10_40cm_inst", 90.0, 2001, 1) == pytest.approx(0.30)
    with pytest.raises(ValueError):
        gm.a_mensual_fisico("Tair_f_inst", 300.0, 2001, 1)


def test_ventanas_de_indices_cubren_las_regiones():
    for grupo, v in gm.VENTANAS.items():
        (a, b), (c, d) = v["lat"], v["lon"]
        sur, norte = gm.LAT0 + gm.PASO * a, gm.LAT0 + gm.PASO * b
        oeste, este = gm.LON0 + gm.PASO * c, gm.LON0 + gm.PASO * d
        doc = json.loads(Path(v["geojson"]).read_text(encoding="utf-8"))
        for f in doc["features"]:
            coords = np.array([p for anillo in _anillos(f["geometry"]) for p in anillo])
            assert coords[:, 0].min() >= oeste and coords[:, 0].max() <= este, (grupo, f.get("id"))
            assert coords[:, 1].min() >= sur and coords[:, 1].max() <= norte, (grupo, f.get("id"))


def _anillos(g):
    if g["type"] == "Polygon":
        return g["coordinates"]
    return [a for pol in g["coordinates"] for a in pol]


@pytest.mark.skipif(not (SALIDA / "series_gldas_anual.json").is_file(), reason="sin salidas GLDAS versionadas")
def test_salidas_versionadas_coherentes():
    anual = json.loads((SALIDA / "series_gldas_anual.json").read_text(encoding="utf-8"))
    mensual = json.loads((SALIDA / "series_gldas_mensual.json").read_text(encoding="utf-8"))
    regiones = {"NIC", "pacifico", "central", "caribe", "caja_sicc", "CAN_prairies"}
    assert {s["region"] for s in anual} == regiones
    assert {s["variable"] for s in anual} == set(gm.SALIDAS)
    por_clave = {(s["region"], s["variable"]): s for s in mensual}
    for s in anual:
        m = por_clave[(s["region"], s["variable"])]
        assert len(m["tiempos"]) == 12 * len(s["tiempos"])
        como = gm.SALIDAS[s["variable"]][2]
        for i, anio in enumerate(s["tiempos"]):
            x = np.array(m["valores"][i * 12:(i + 1) * 12], float)
            esperado = x.mean() if como == "media" else x.sum()
            assert s["valores"][i] == pytest.approx(esperado, rel=1e-5)
        if s["variable"].startswith("humedad"):
            assert all(0 < v < 0.6 for v in s["valores"])
        else:
            assert all(v >= 0 for v in s["valores"])


def test_rechaza_respuesta_de_otro_granulo():
    # El OPeNDAP en la nube devolvió junio de 2001 al pedir enero: el adaptador debe detectarlo.
    nombre = gm.url_granulo(2001, 1)[1]
    assert gm.es_granulo(f"Dataset: {nombre}\n/lon, -88.125\n", nombre)
    assert not gm.es_granulo("Dataset: GLDAS_NOAH025_M.A200106.021.nc4\n/lon, -88.125\n", nombre)
