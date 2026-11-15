"""Pruebas de las series observadas de las Américas y el Caribe (recursos_americas.py)."""
import json

import pytest

from backend.clima_nic import recursos as rec
from backend.clima_nic import recursos_americas as ra
from backend.clima_nic.rutas import DATOS

HALLAZGOS = DATOS / "recursos" / "hallazgos"


def test_americas_carpeta_vacia_devuelve_listas_vacias(tmp_path):
    invs, entradas = ra.americas(tmp_path)
    assert invs == []
    assert entradas == []


def test_lugares_y_estudios_americas_cumplen_formato():
    assert set(ra.LUGARES) <= set(rec.LUGARES)
    for id_lugar, (nombre_en, pais, centro, zoom) in ra.LUGARES.items():
        assert isinstance(id_lugar, str) and id_lugar
        assert isinstance(nombre_en, str) and nombre_en
        assert isinstance(pais, str) and pais
        assert len(centro) == 2 and -90 <= centro[0] <= 90 and -180 <= centro[1] <= 180
        assert isinstance(zoom, int) and 2 <= zoom <= 12

    for clave, cita in ra.ESTUDIOS.items():
        assert cita.startswith("Published check:"), f"{clave} no empieza con 'Published check:'"
        assert "doi:10." in cita, f"{clave} no contiene un DOI válido"


@pytest.mark.parametrize(
    "id_serie,anio_ini,anio_fin,unidad,veredicto,signo_sen,clave_estudio",
    [
        # 1. Río Colorado en Lees Ferry (USGS 09380000)
        ("cuenca_colorado_caudal", 1922, 2025, "km³", "tendencia_detectada", -1, "colorado"),
        ("cuenca_colorado_caudal_pos1963", 1963, 2025, "km³", "evidencia_insuficiente", -1, "colorado"),
        # 2. Permafrost en Alaska y Canadá (GTN-P, PANGAEA 10.1594/PANGAEA.930669)
        ("canada_alaska_permafrost_magt_deadhorse", 1978, 2016, "°C", "tendencia_detectada", 1, "permafrost"),
        ("canada_alaska_permafrost_magt_west_dock", 1978, 2016, "°C", "tendencia_detectada", 1, "permafrost"),
        ("canada_alaska_permafrost_magt_franklin_bluffs", 1983, 2016, "°C", "tendencia_detectada", 1, "permafrost"),
        ("canada_alaska_permafrost_magt_chandalar_shelf", 1985, 2016, "°C", "tendencia_detectada", 1, "permafrost"),
        ("canada_alaska_permafrost_magt_alert_2", 1978, 2014, "°C", "metodos_discrepan", 1, "permafrost"),
        # 3. Hielo lacustre en Norteamérica (NSIDC G01377)
        ("norteamerica_hielo_lagos_bayfield", 1858, 2019, "days", "tendencia_detectada", -1, "hielo_lagos"),
        ("norteamerica_hielo_lagos_monona", 1851, 2018, "days", "tendencia_detectada", -1, "hielo_lagos"),
        ("norteamerica_hielo_lagos_mendota", 1855, 2018, "days", "tendencia_detectada", -1, "hielo_lagos"),
        ("norteamerica_hielo_lagos_simcoe", 1901, 1995, "days", "evidencia_insuficiente", -1, "hielo_lagos"),
        ("norteamerica_hielo_lagos_utopia", 1962, 1994, "days", "tendencia_detectada", -1, "hielo_lagos"),
        # 4. Megasequía de Chile central (CHIRPS + CRU TS 4.10)
        ("chile_central_megasequia", 1981, 2024, "mm", "tendencia_detectada", -1, "chile_central"),
        ("chile_central_megasequia_cru", 1951, 2025, "mm", "evidencia_insuficiente", -1, "chile_central"),
        # 5. Semiárido del Nordeste de Brasil (CHIRPS + CRU TS 4.10)
        ("nordeste_brasil_semiarido_lluvia", 1981, 2024, "mm", "evidencia_insuficiente", 0, "nordeste_brasil"),
        ("nordeste_brasil_semiarido_lluvia_fmam", 1981, 2024, "mm", "evidencia_insuficiente", 0, "nordeste_brasil"),
        ("nordeste_brasil_semiarido_lluvia_cru", 1951, 2025, "mm", "evidencia_insuficiente", -1, "nordeste_brasil"),
        # 6. Rápida intensificación de huracanes (IBTrACS NA y EP)
        ("huracanes_rapida_intensificacion_na_pasos", 1980, 2024, "steps", "metodos_discrepan", 1, "huracanes_ri"),
        ("huracanes_rapida_intensificacion_na_pct", 1980, 2024, "%", "evidencia_insuficiente", 0, "huracanes_ri"),
        ("huracanes_rapida_intensificacion_ep_pasos", 1980, 2024, "steps", "evidencia_insuficiente", 0, "huracanes_ri"),
        ("huracanes_rapida_intensificacion_ep_pct", 1980, 2024, "%", "evidencia_insuficiente", 0, "huracanes_ri"),
        # 7. Nieve al 1 de abril en el oeste de EE. UU. (USDA SNOTEL)
        ("oeste_eeuu_nieve_swe_abril_blewett_pass_wa", 1982, 2025, "mm", "tendencia_detectada", -1, "snotel_swe"),
        ("oeste_eeuu_nieve_swe_abril_arbuckle_mtn_or", 1981, 2025, "mm", "evidencia_insuficiente", -1, "snotel_swe"),
        ("oeste_eeuu_nieve_swe_abril_bateman_nm", 1981, 2025, "mm", "tendencia_detectada", -1, "snotel_swe"),
        ("oeste_eeuu_nieve_swe_abril_niwot_co", 1981, 2025, "mm", "evidencia_insuficiente", 0, "snotel_swe"),
        # 8. Lagos del Altiplano y Sudamérica (NASA GSFC G-REALM)
        ("altiplano_lagos_titicaca", 2016, 2025, "m", "metodos_discrepan", -1, "lagos_altiplano"),
        ("altiplano_lagos_colhue_huapi", 1993, 2025, "m", "tendencia_detectada", -1, "lagos_altiplano"),
        ("altiplano_lagos_argentino", 1993, 2025, "m", "evidencia_insuficiente", 0, "lagos_altiplano"),
        ("altiplano_lagos_junin", 2009, 2025, "m", "metodos_discrepan", -1, "lagos_altiplano"),
    ],
)
def test_series_americas_rango_unidad_tendencia_y_cita(
    id_serie, anio_ini, anio_fin, unidad, veredicto, signo_sen, clave_estudio
):
    invs, entradas = ra.americas(HALLAZGOS)
    assert len(entradas) == 7
    por_id = {i["id"]: i for i in invs}
    assert id_serie in por_id, f"Falta la serie {id_serie}"
    inv = por_id[id_serie]

    assert inv["categoria"] in {c["id"] for c in rec.CATEGORIAS}
    assert inv["lugar"] in rec.LUGARES
    assert inv["unidad"] == unidad
    assert inv["tiempos"][0] == anio_ini
    assert inv["tiempos"][-1] == anio_fin
    assert len(inv["tiempos"]) == len(inv["valores"]) >= 10

    t = inv["tendencia"]
    assert t["veredicto"] == veredicto
    sen = t["sen"]["por_decada"]
    if signo_sen > 0:
        assert sen > 0, f"Se esperaba pendiente positiva en {id_serie}, obtuvo {sen}"
    elif signo_sen < 0:
        assert sen < 0, f"Se esperaba pendiente negativa en {id_serie}, obtuvo {sen}"

    cita_esperada = ra.ESTUDIOS[clave_estudio]
    assert cita_esperada in inv["notas"], f"Falta 'Published check' ({clave_estudio}) en notas de {id_serie}"


def test_todas_las_citas_estudios_presentes_en_json_versionado():
    d = json.loads((DATOS / "recursos_integrados.json").read_text(encoding="utf-8"))
    invs_americas, _ = ra.americas(HALLAZGOS)
    ids_esperados = {i["id"] for i in invs_americas}
    por_id = {i["id"]: i for i in d["investigaciones"]}
    assert ids_esperados <= set(por_id)

    todas_las_notas = "\n".join(n for id_s in ids_esperados for n in por_id[id_s]["notas"])
    for clave, cita in ra.ESTUDIOS.items():
        assert cita in todas_las_notas, f"La cita {clave} no aparece en recursos_integrados.json"
    ep = por_id["huracanes_rapida_intensificacion_ep_pasos"]
    assert f"{ep['tendencia']['sen']['por_decada']} {ep['unidad']}" == "0 steps"
    assert "-0.0" not in json.dumps(ep)
