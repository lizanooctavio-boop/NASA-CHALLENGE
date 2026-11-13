"""Pruebas del integrador de recursos (clima_nic.recursos) y de su publicación en la demo.

Los datos de los agentes se simulan en una carpeta temporal marcada como sintética; nunca se escriben en
data/ ni llegan a public/.

    python -m pytest tests/test_recursos_interfaz.py -q
"""
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

from clima_nic import recursos as rec  # noqa: E402

NODE = shutil.which("node")


def _escribir_csv(ruta, columnas, filas):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(columnas)
        w.writerows(filas)


@pytest.fixture
def datos_sinteticos(tmp_path):
    """data/ mínima: clima.json y fenomenos reales más salidas sintéticas de los tres agentes."""
    for nombre in ("clima.json", "fenomenos_nicaragua.json"):
        shutil.copy(RAIZ / "data" / nombre, tmp_path / nombre)
    rng = np.random.default_rng(7)
    anios = list(range(2001, 2025))
    sube = [0.5 + 0.05 * (a - 2001) + rng.normal(0, 0.05) for a in anios]
    plano = [1.0 + rng.normal(0, 0.3) for _ in anios]
    contraste = tmp_path / "recursos" / "contraste"
    contraste.mkdir(parents=True)
    serie_ok = {"fuente": "GPM IMERG Final V07B (data/clima.json)", "pendiente": -60.0, "unidad": "mm/década",
                "veredicto": "evidencia_insuficiente"}
    resumen = {"esquema": "nasa-challenge/contrastes", "sintetico": True, "contrastes": [
        {"id": "cru_nic", "papel": "contraste", "estado": "ok", "region": "NIC", "periodo": [2001, 2024],
         "serie_nuestra": serie_ok, "serie_externa": {"fuente": "CRU TS 4.10 (University of East Anglia), pre, 0,5°",
                                                       "pendiente": -20.0, "veredicto": "evidencia_insuficiente"},
         "diferencia": {"media": 200.0, "r": 0.7}, "frase_en": "Synthetic cross-check."},
        {"id": "clorofila_prueba", "papel": "tendencia", "estado": "ok", "region": "Test bay", "caja": [-87.0, 12.0, -86.5, 12.5],
         "serie_nuestra": {"fuente": "NASA OBPG MODIS-Aqua L3m CHL chlor_a 4 km mensual (prueba)", "unidad": "mg m-3/década"},
         "serie_externa": {"fuente": "Método NTRS", "pendiente": 0.5, "p_valor_F": 0.01}, "frase_en": "Synthetic chlorophyll."},
        {"id": "giovanni_imerg_nic", "papel": "contraste", "estado": "bloqueado", "serie_nuestra": serie_ok, "serie_externa": {}},
    ]}
    (contraste / "resumen_contrastes.json").write_text(json.dumps(resumen), encoding="utf-8")
    _escribir_csv(contraste / "series_anuales.csv", ["contraste", "serie", "anio", "valor"],
                  [["clorofila_prueba", "nuestra", a, v] for a, v in zip(anios, sube)]
                  + [["cru_nic", s, a, 2000 + v * 100] for a, v in zip(anios, plano) for s in ("nuestra", "externa")])
    csa = tmp_path / "recursos" / "csa"
    csa.mkdir(parents=True)
    (csa / "canada_gistemp.json").write_text(json.dumps({"sintetico": True, "region": "CAN_prairies", "anios": anios,
                                                         "valores": plano, "fuente": "https://data.giss.nasa.gov/gistemp/"}), encoding="utf-8")
    _escribir_csv(csa / "swot_mensual.csv", ["lago", "lake_id", "mes", "wse_m", "n"],
                  [["cocibolca", "7530096743", f"2024-{m:02d}", 31 + m / 10, 1] for m in range(1, 13)])
    _escribir_csv(csa / "cocibolca_grealm.csv", ["fecha", "altura_egm2008_m"],
                  [[f"{a}-{m:02d}-15", 32 + 0.01 * (a - 2000)] for a in range(2000, 2025) for m in range(1, 13)])
    _escribir_csv(csa / "comparacion_cocibolca_grealm_swot.csv", ["mes", "grealm_m", "n_grealm", "swot_m", "n_swot", "swot_menos_grealm_m"],
                  [[f"2024-{m:02d}", 32 + m / 10, 3, 31.6 + m / 10 + 0.01 * (m % 2), 1, -0.4] for m in range(1, 13)])
    tierra = tmp_path / "recursos" / "tierra"
    tierra.mkdir(parents=True)
    (tierra / "series_appeears_nicaragua_anual.json").write_text(json.dumps([
        {"region": "central", "variable": "ndvi_regional", "unidad": "adimensional", "frecuencia": "anual", "tiempos": anios,
         "valores": [0.6 + 0.001 * v for v in plano], "fuente": "appeears/MOD13A3.061", "version": "061", "notas": [], "sintetico": True}]),
        encoding="utf-8")
    # agente 3: estación de las Praderas con el esquema del agente 2 y lluvia de mayo a septiembre
    (csa / "canada_imerg.json").write_text(json.dumps({"sintetico": True, "region": "CAN_prairies", "anios": anios,
                                                       "valores": [430 + 10 * v for v in plano]}), encoding="utf-8")
    (csa / "canada_imerg_may_sep.json").write_text(json.dumps({"sintetico": True, "region": "CAN_prairies", "anios": anios,
                                                               "valores": [300 + 10 * v for v in plano]}), encoding="utf-8")
    (csa / "contrastes_canada.json").write_text(json.dumps({"sintetico": True, "contrastes": [
        {"id": "noaa_canada_lluvia", "papel": "contraste", "estado": "ok", "periodo": [2001, 2024],
         "serie_nuestra": {"fuente": "GPM IMERG Final V07B, Prairies", "pendiente": -30.0, "unidad": "mm/década", "veredicto": "evidencia_insuficiente"},
         "serie_externa": {"fuente": "Regina weather station (NOAA GHCN-Daily)", "pendiente": -10.0, "veredicto": "evidencia_insuficiente"},
         "diferencia": {"media": 15.0, "r": 0.8}, "frase_en": "Synthetic Prairies station."}]}), encoding="utf-8")
    _escribir_csv(csa / "contrastes_canada_series.csv", ["contraste", "serie", "anio", "valor"],
                  [["noaa_canada_lluvia", s, a, 400 + v * 50] for a, v in zip(anios, plano) for s in ("nuestra", "externa")])
    # agente 1: GLDAS regional (archivo de GES DISC) y de punto (API de Giovanni)
    (tierra / "series_gldas_anual.json").write_text(json.dumps([
        {"region": "NIC", "variable": "et_gldas", "unidad": "mm", "frecuencia": "anual", "tiempos": anios,
         "valores": [1200 + 10 * v for v in plano], "fuente": "GES DISC GLDAS_NOAH025_M 2.1 (OPeNDAP en la nube), media regional",
         "version": "2.1", "notas": [], "sintetico": True},
        {"region": "pacifico", "variable": "et_gldas", "unidad": "mm", "frecuencia": "anual", "tiempos": anios,
         "valores": [1400 + 10 * v for v in plano], "fuente": "Giovanni time series API, GLDAS_NOAH025_3H 2.1",
         "version": "2.1", "notas": [], "sintetico": True}]), encoding="utf-8")
    # agente 1: contraste con destino explícito (humedad GLDAS frente a MERRA-2, en anomalías z)
    (tierra / "contrastes_tierra.json").write_text(json.dumps({"sintetico": True, "contrastes": [
        {"id": "merra2_et_gldas_NIC", "investigacion": "et_gldas_NIC", "papel": "contraste", "estado": "ok",
         "serie_nuestra": {"fuente": "GLDAS-2.1 Noah (GES DISC), regional mean", "pendiente": None, "unidad": "z/década"},
         "serie_externa": {"fuente": "MERRA-2 root-zone soil wetness (GWETROOT), regional mean", "pendiente": None},
         "diferencia": {"media": None, "r": 0.1}, "frase_en": "Synthetic model disagreement."}]}), encoding="utf-8")
    _escribir_csv(tierra / "contrastes_tierra_series.csv", ["contraste", "serie", "anio", "valor"],
                  [["merra2_et_gldas_NIC", s, a, v] for a, v in zip(anios, plano) for s in ("nuestra", "externa")])
    return tmp_path


def test_rechaza_datos_sinteticos_sin_permiso(datos_sinteticos):
    with pytest.raises(ValueError, match="sintético"):
        rec.construir(datos_sinteticos)


def test_integra_las_salidas_de_los_tres_agentes(datos_sinteticos):
    d = rec.construir(datos_sinteticos, permitir_sintetico=True)
    ids = {i["id"]: i for i in d["investigaciones"]}
    # agente 2: variable nueva con tendencia y contraste de método; contraste de fuente unido a la lluvia
    assert ids["clorofila_prueba"]["categoria"] == "costa"
    assert ids["clorofila_prueba"]["tendencia"]["veredicto"] == "tendencia_detectada"
    assert ids["clorofila_prueba"]["contrastes"] == ["clorofila_prueba_metodo"]
    assert "cru_nic" in ids["lluvia_NIC"]["contrastes"]
    # los bloqueados no aparecen
    assert all(c["id"] != "giovanni_imerg_nic" for c in d["contrastes"])
    # agente 3: Canadá, lago con G-REALM + SWOT, y SWOT como registro corto sin tendencia
    assert ids["temperatura_CAN_prairies"]["lugar"] == "CAN_prairies"
    assert ids["nivel_cocibolca"]["tendencia"]["anios"] == 25
    assert ids["nivel_cocibolca"]["contrastes"] == ["swot_vs_grealm_cocibolca"]
    swot = ids["swot_cocibolca"]
    assert swot["papel"] == "demostracion_registro_corto" and "tendencia" not in swot
    # agente 3: lluvia de mayo a septiembre y estación canadiense unida a la lluvia de las Praderas
    assert ids["lluvia_may_sep_CAN_prairies"]["tendencia"]["anios"] == 24
    canada = next(c for c in d["contrastes"] if c["id"] == "noaa_canada_lluvia")
    assert canada["investigacion"] == "lluvia_CAN_prairies" and canada["recursos"] == [4]
    assert canada["externa"]["nombre_en"] == "Regina weather station (NOAA GHCN-Daily)"
    # agente 1: serie de AppEEARS
    assert ids["ndvi_regional_central"]["recursos"] == [3]
    assert ids["ndvi_regional_central"]["fuente"]["producto"] == "NASA MOD13A3.061 via AppEEARS"
    # agente 1: GLDAS regional sin recurso del reto; el de punto acredita Hydrology Time Series y Giovanni
    assert ids["et_gldas_NIC"]["recursos"] == [] and "sample point" not in ids["et_gldas_NIC"]["titulo_en"]
    assert ids["et_gldas_NIC"]["fuente"]["producto"].startswith("NASA GLDAS-2.1")
    assert ids["et_gldas_pacifico"]["recursos"] == [1, 2] and ids["et_gldas_pacifico"]["titulo_en"].endswith("at a sample point")
    assert "merra2_et_gldas_NIC" in ids["et_gldas_NIC"]["contrastes"]
    merra = next(c for c in d["contrastes"] if c["id"] == "merra2_et_gldas_NIC")
    assert merra["unidad"] == "z" and merra["r"] == 0.1 and merra["externa"]["por_decada"] is None
    # la interfaz solo ve nombres en inglés
    cru = next(c for c in d["contrastes"] if c["id"] == "cru_nic")
    assert cru["externa"]["nombre_en"] == "CRU TS 4.10 (University of East Anglia)"
    assert cru["nuestra"]["nombre_en"] == "NASA GPM IMERG Final V07B"


def test_categorias_y_recursos_sin_datos_quedan_marcados(datos_sinteticos):
    d = rec.construir(datos_sinteticos, permitir_sintetico=True)
    cat = {c["id"]: c["con_datos"] for c in d["categorias"]}
    assert cat["aire"] is False and cat["costa"] is True
    estado = {r["id"]: r["estado"] for r in d["recursos"]}
    assert len(estado) == 13
    assert estado[3] == "en_uso" and estado[11] == "en_uso" and estado[5] == "en_uso"
    assert estado[6] == "sin_datos" and estado[9] == "sin_datos" and estado[13] == "sin_datos"
    lugares = {l["id"] for l in d["lugares"]}
    assert {i["lugar"] for i in d["investigaciones"]} <= lugares


def test_tendencia_compacta_series_cortas_y_con_huecos():
    assert rec.tendencia_compacta(range(2001, 2008), [1] * 7, "mm")["veredicto"] == "datos_insuficientes"
    anios = list(range(2001, 2025))
    vals = [float(a) for a in anios]
    vals[3] = None
    t = rec.tendencia_compacta(anios, vals, "mm")
    assert t["anios"] == 23 and t["sen"]["por_decada"] == pytest.approx(10.0)


def test_demostraciones_usan_investigaciones_existentes(datos_sinteticos):
    d = rec.construir(datos_sinteticos, permitir_sintetico=True)
    ids = {i["id"] for i in d["investigaciones"]}
    assert {x["id"] for x in d["demostraciones"]} == {"lluvia_nicaragua", "nicaragua_vs_praderas"}
    for dm in d["demostraciones"]:
        assert all(p["investigacion"] in ids for p in dm["pasos"])
    comp = next(x for x in d["demostraciones"] if x["id"] == "nicaragua_vs_praderas")["comparacion"]
    assert all(t["periodo"] == [2001, 2024] for t in comp.values())


def test_json_versionado_esta_al_dia():
    """Si un agente cambia sus salidas, hay que regenerar: python -m clima_nic recursos."""
    guardado = json.loads((RAIZ / "data" / "recursos_integrados.json").read_text(encoding="utf-8"))
    nuevo = rec.construir()
    guardado.pop("generado"), nuevo.pop("generado")
    assert guardado["entradas"] == nuevo["entradas"]
    assert guardado == json.loads(json.dumps(nuevo))


def test_el_json_versionado_no_tiene_datos_sinteticos():
    texto = (RAIZ / "data" / "recursos_integrados.json").read_text(encoding="utf-8")
    assert '"sintetico"' not in texto


@pytest.mark.skipif(NODE is None, reason="requiere node")
def test_javascript_de_la_pestana_es_valido():
    subprocess.run([NODE, "--check", str(RAIZ / "app" / "investigar.js")], check=True)
