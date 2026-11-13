"""Pruebas de los contrastes externos (data/recursos/contraste/).

- Forma de resumen_contrastes.json (incluidas las tres variables nuevas).
- Ningún secreto en los archivos generados ni en los módulos de fuentes.
- Los veredictos y pendientes del resumen coinciden con recalcular sobre los CSV guardados.
- Parsers de Giovanni, OPeNDAP y NCEI sin red.

    python -m pytest tests/test_recursos_contraste.py -q
"""
import csv
import json
import math
import os
import re
import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]
CONTRASTE = RAIZ / "data" / "recursos" / "contraste"
sys.path.insert(0, str(RAIZ / "backend"))
sys.path.insert(0, str(CONTRASTE))

pytest.importorskip("scipy")
from clima_nic.fuentes import giovanni as gv  # noqa: E402
from clima_nic.fuentes import noaa_cdo as nc  # noqa: E402

RESUMEN = CONTRASTE / "resumen_contrastes.json"


def _resumen():
    return json.loads(RESUMEN.read_text(encoding="utf-8"))


def _series():
    with (CONTRASTE / "series_anuales.csv").open(encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    out = {}
    for r in filas:
        out.setdefault((r["contraste"], r["serie"]), {})[int(r["anio"])] = float(r["valor"])
    return out


# ---------------------------------------------------------------- forma del resumen

def test_resumen_forma():
    d = _resumen()
    assert d["esquema"] == "nasa-challenge/contrastes"
    ids = [c["id"] for c in d["contrastes"]]
    assert len(ids) == len(set(ids))
    for c in d["contrastes"]:
        assert {"id", "papel", "region", "periodo", "serie_nuestra", "serie_externa", "diferencia", "estado",
                "frase_en"} <= c.keys(), c["id"]
        assert c["papel"] in ("contraste", "tendencia")
        assert c["estado"] in ("ok", "bloqueado")
        if c["estado"] == "bloqueado":
            assert c.get("motivo"), c["id"]
        for k in ("fuente", "pendiente", "unidad", "veredicto"):
            assert k in c["serie_nuestra"], (c["id"], k)
            assert k in c["serie_externa"], (c["id"], k)
        for k in ("fuente", "version", "fecha_consulta", "url"):
            assert k in c["serie_externa"], (c["id"], k)
        for k in ("media", "r", "diferencia_pendiente"):
            assert k in c["diferencia"], (c["id"], k)
        assert c["frase_en"].strip()
        assert not re.search(r"[áéíóú¿¡]|ñ(?!o 3)", c["frase_en"]), f"frase_en en español: {c['id']}"


def test_resumen_incluye_variables_nuevas_y_papeles():
    cs = {c["id"]: c for c in _resumen()["contrastes"]}
    series = _series()
    req = {"omi_no2_managua", "omi_no2_rural", "airs_tas_nic",
           "clorofila_golfo_fonseca", "clorofila_pacifico_fonseca",
           "giovanni_imerg_caja_sicc", "giovanni_imerg_nic", "noaa_tegucigalpa_lluvia_vs_imerg_caja"}
    assert req.issubset(cs)
    for k in req:
        assert cs[k]["estado"] == "ok", k
    assert cs["clorofila_pacifico_fonseca"].get("cumple_criterio_ntrs_1mg") is True
    for k, c in cs.items():
        if k.startswith(("omi_no2", "airs_tas", "clorofila_")):
            assert c["papel"] == "tendencia", k
            if c.get("estado") == "ok":
                assert c.get("titulo_en") and c.get("definicion_en"), k
                assert c.get("region") and not re.search(r"[áéíóú¿¡ñ]", c["region"].lower()), k
                assert c["serie_nuestra"].get("unidad", "").count("/") == 1, k
                assert (k, "nuestra") in series, k
                if k.startswith("omi_no2"):
                    assert "caja" in c and c["serie_nuestra"].get("unidad") == "1e15 molec cm-2/década", k
        if k.startswith(("cru_", "gpcc_", "noaa_", "giovanni_imerg")):
            assert c["papel"] == "contraste", k


def test_bloqueos_documentan_url_codigo_y_fecha():
    d = _resumen()
    for k, b in d["bloqueos"].items():
        assert b.get("url", "").startswith("http"), k
        assert "fecha" in b and re.match(r"\d{4}-\d{2}-\d{2}$", b["fecha"]), k
        assert b.get("motivo"), k


# ---------------------------------------------------------------- sin secretos

PATRONES_SECRETOS = [
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),  # JWT (token EDL)
    re.compile(r"Authorization:\s*(Basic|Bearer)\s+[A-Za-z0-9+/=._-]{12,}", re.I),
    re.compile(r"\bpassword\s+\S+", re.I),  # línea de .netrc
    re.compile(r"machine\s+urs\.earthdata\.nasa\.gov\s+login\s+\S+", re.I),
    re.compile(r"[?&]token=[A-Za-z0-9]{16,}", re.I),
    re.compile(r"\"token\"\s*:\s*\"[A-Za-z0-9]{16,}\""),
]


def _archivos_revisados():
    rutas = [p for p in CONTRASTE.rglob("*") if p.is_file() and p.suffix in (".json", ".csv", ".py", ".md", ".txt")]
    rutas += [RAIZ / "backend" / "clima_nic" / "fuentes" / "giovanni.py",
              RAIZ / "backend" / "clima_nic" / "fuentes" / "noaa_cdo.py",
              RAIZ / "docs" / "reto" / "recursos" / "contraste.md"]
    return [p for p in rutas if p.exists()]


def test_sin_secretos():
    secretos_entorno = [os.environ[k] for k in ("NOAA_CDO_TOKEN", "EARTHDATA_TOKEN", "EDL_TOKEN")
                        if len(os.environ.get(k, "")) >= 8]
    for p in _archivos_revisados():
        texto = p.read_text(encoding="utf-8", errors="replace")
        for pat in PATRONES_SECRETOS:
            assert not pat.search(texto), f"posible secreto en {p}: {pat.pattern}"
        for s in secretos_entorno:
            assert s not in texto, f"token del entorno copiado en {p}"


# ---------------------------------------------------------------- veredictos = recalcular sobre los CSV

def _comprobar_serie(bloque, serie):
    anios = sorted(serie)
    v = gv.veredicto_serie(anios, [serie[a] for a in anios], "x")
    assert bloque["veredicto"] == v["veredicto_contrato"]
    assert bloque.get("veredicto_robusto", v["veredicto"]) == v["veredicto"]
    assert bloque["pendiente"] == pytest.approx(v["sen_por_decada"], abs=1e-3)


def test_veredictos_coinciden_con_csv():
    series = _series()
    revisados = 0
    for c in _resumen()["contrastes"]:
        if c["estado"] != "ok":
            continue
        for lado in ("nuestra", "externa"):
            bloque = c[f"serie_{lado}"]
            if bloque.get("pendiente") is None or bloque.get("veredicto") in (None, "no_aplica") \
                    or (c["papel"] == "tendencia" and lado == "externa" and "p_valor_F" in bloque):
                continue
            _comprobar_serie(bloque, series[(c["id"], lado)])
            revisados += 1
        if c["serie_nuestra"].get("pendiente") is not None and c["serie_externa"].get("pendiente") is not None \
                and not (c["papel"] == "tendencia" and "p_valor_F" in c["serie_externa"]):
            esperado = c["serie_externa"]["pendiente"] - c["serie_nuestra"]["pendiente"]
            assert c["diferencia"]["diferencia_pendiente"] == pytest.approx(esperado, abs=2e-4)
    assert revisados >= 10


def test_diferencia_media_y_r_desde_csv():
    series = _series()
    for c in _resumen()["contrastes"]:
        if c["estado"] != "ok" or (c["id"], "externa") not in series or (c["id"], "nuestra") not in series:
            continue
        n, e = series[(c["id"], "nuestra")], series[(c["id"], "externa")]
        com = sorted(set(n) & set(e))
        if len(com) < 3:
            continue
        x, y = np.array([n[a] for a in com]), np.array([e[a] for a in com])
        assert c["diferencia"]["media"] == pytest.approx(float(np.mean(y - x)), abs=1e-3)
        assert c["diferencia"]["r"] == pytest.approx(float(np.corrcoef(x, y)[0, 1]), abs=1e-3)


def test_imerg_nuestra_coincide_con_clima_json():
    cj = json.loads((RAIZ / "data" / "clima.json").read_text(encoding="utf-8"))
    dom = {d["id"]: d for d in cj["dominios"]}
    series = _series()
    for c in _resumen()["contrastes"]:
        if c["id"].startswith(("cru_", "gpcc_")):
            reg = c["region"]
            n = series[(c["id"], "nuestra")]
            assert [n[a] for a in sorted(n)] == pytest.approx(dom[reg]["serie_anual_mm"], abs=1e-3)
            assert c["serie_nuestra"]["veredicto"] == dom[reg]["tendencia"]["veredicto"]
            assert c["serie_nuestra"]["pendiente_mco"] == pytest.approx(dom[reg]["tendencia"]["mm_por_decada"], abs=0.01)
            assert c["nino34_jun_nov"]["r_nuestra"] == pytest.approx(
                c["nino34_jun_nov"]["r_nuestra_clima_json"], abs=1e-3)


def test_series_externas_de_lluvia_salen_de_los_csv_mensuales():
    series = _series()
    for fuente in ("cru", "gpcc"):
        ruta = CONTRASTE / f"lluvia_mensual_externa_{fuente}.csv"
        if not ruta.exists():
            continue
        with ruta.open(encoding="utf-8") as f:
            filas = list(csv.DictReader(f))
        for reg in ("caja_sicc", "NIC"):
            por = {}
            for r in filas:
                if r["region"] == reg:
                    por.setdefault(int(r["mes"][:4]), []).append(float(r["mm"]))
            e = series[(f"{fuente}_{reg.lower()}", "externa")]
            for a, v in e.items():
                assert v == pytest.approx(sum(por[a]), abs=0.01)


def test_clorofila_ntrs_recalculo():
    ruta = CONTRASTE / "clorofila_modis_mensual.csv"
    if not ruta.exists():
        pytest.skip("sin CSV de clorofila")
    import generar_contrastes as G
    cs = {c["id"]: c for c in _resumen()["contrastes"]}
    for caja in G.CAJAS_CHL:
        c = cs[f"clorofila_{caja}"]
        filas = [r for r in G.leer_csv(ruta) if r["caja"] == caja]
        maxpix = max(int(r["pixeles_validos"]) for r in filas)
        vals = [float(r["chl_mg_m3"]) if r["chl_mg_m3"] and int(r["pixeles_validos"]) >= 0.2 * maxpix else None
                for r in filas]
        nt = G.ntrs_clorofila([r["mes"] for r in filas], vals)
        assert c["serie_externa"]["pendiente"] == pytest.approx(nt["mco_mensual"]["pendiente_por_decada"], abs=1e-4)
        assert c["serie_externa"]["p_valor_F"] == pytest.approx(nt["mco_mensual"]["p_valor_F"], abs=1e-4)


# ---------------------------------------------------------------- parsers sin red

CSV_GIOVANNI = """Title:,Area-averaged of Merged precipitation monthly 0.1 deg. [GPM GPM_3IMERGM v07] mm/hr
User Start Date:,2001-01-01T00:00:00Z
User End Date:,2001-03-31T23:59:59Z
Bounding Box:,"-86.5,10.7,-83.6,12.6"
Fill Value (mean_GPM_3IMERGM_07_precipitation):,-9999.9

time,mean_GPM_3IMERGM_07_precipitation
2001-01-01 00:00:00,0.1
2001-02-01 00:00:00,-9999.9
2001-03-01 00:00:00,0.25
"""


def test_leer_csv_giovanni():
    d = gv.leer_csv_giovanni(CSV_GIOVANNI)
    assert d["meta"]["Bounding Box"] == "-86.5,10.7,-83.6,12.6"
    assert d["meta"]["columna"] == "mean_GPM_3IMERGM_07_precipitation"
    assert d["tiempos"][0] == "2001-01-01 00:00:00"
    assert d["valores"] == [0.1, None, 0.25]
    with pytest.raises(ValueError):
        gv.leer_csv_giovanni("Title:,x\n")


DAP2 = """Dataset {
    Float32 precipitation[time = 1][lon = 2][lat = 3];
    Float32 lon[lon = 2];
    Float32 lat[lat = 3];
} prueba.HDF5;
---------------------------------------------
precipitation[1][2][3]
[0][0], 0.1, 0.2, 0.3
[0][1], 0.4, 0.5, 0.6

lon[2]
-86.45, -86.35

lat[3]
10.75, 10.85, 10.95
"""


def test_parsear_dap2_ascii():
    d = gv.parsear_dap2_ascii(DAP2)
    assert d["precipitation"].shape == (1, 2, 3)
    assert d["precipitation"][0, 1, 2] == pytest.approx(0.6)
    assert d["lon"].tolist() == pytest.approx([-86.45, -86.35])
    assert d["lat"].shape == (3,)


def test_media_caja_coslat():
    lat = np.array([0.0, 60.0])
    lon = np.array([10.0, 11.0])
    campo = np.array([[1.0, 1.0], [3.0, np.nan]])
    media, frac = gv.media_caja_coslat(lat, lon, campo, (9, -1, 12, 61))
    w0, w1 = 1.0, math.cos(math.radians(60))
    assert float(media) == pytest.approx((2 * w0 * 1 + w1 * 3) / (2 * w0 + w1))
    assert float(frac) == pytest.approx((2 * w0 + w1) / (2 * w0 + 2 * w1))
    with pytest.raises(ValueError):
        gv.indices_rango(lat, 20, 30)


def test_mensual_tasa_a_anual_y_horas():
    assert gv.horas_mes(2024, 2) == 29 * 24
    tiempos = [f"2001-{m:02d}" for m in range(1, 13)] + ["2002-01"]
    anios, tot = gv.mensual_tasa_a_anual(tiempos, [1.0] * 13)
    assert anios == [2001] and tot[0] == pytest.approx(8760)
    a, v = gv.anual_media(tiempos, [1.0] * 13, 12)
    assert a == [2001] and v == [1.0]


def test_url_serie_area():
    u = gv.url_serie_area("GPM_3IMERGM_07_precipitation", "2001-01-01", "2024-12-31", bbox=(-86.5, 10.7, -83.6, 12.6))
    assert "service=ArAvTs" in u and "bbox=-86.5%2C10.7%2C-83.6%2C12.6" in u and "starttime=2001-01-01T00" in u
    u = gv.url_serie_area("X", "2001-01-01", "2001-12-31", shape="state_dept_countries_2017/shp_163")
    assert "shape=state_dept_countries_2017%2Fshp_163" in u and "bbox" not in u


def test_estado_resultado_giovanni():
    res = {"status": [{"code": [{"value": "2"}], "percentComplete": [{"value": "0"}],
                       "message": [{"value": "Workflow failed<br/>Please send <span>feedback</span>"}]}],
           "data": [{}]}
    codigo, pct, msj, urls = gv.estado_resultado(res)
    assert (codigo, pct, urls) == (2, 0, []) and "<" not in msj


CSV_NCEI = """"STATION","LATITUDE","LONGITUDE","ELEVATION","DATE","PRCP","TAVG","TMAX","TMIN"
"NUM00078741","12.141","-86.168","59.1","2001-02-01","1.0","27.0","",""
"NUM00078741","12.141","-86.168","59.1","2001-02-02","","28.0","",""
"HO000078720","14.05","-87.217","1007.0","2001-02-01","0.0","","25.1",""
"""


def test_leer_csv_ncei_y_mensual():
    d = nc.leer_csv_ncei(CSV_NCEI)
    assert d["NUM00078741"]["2001-02-01"]["PRCP"] == 1.0
    assert d["NUM00078741"]["2001-02-02"]["PRCP"] is None
    assert d["HO000078720"]["2001-02-01"]["TMAX"] == 25.1
    diario = {f"2001-02-{k:02d}": {"TAVG": 20.0 + k % 2, "PRCP": 1.0} for k in range(1, 29)}
    assert nc.mensual_desde_diario(diario, "TAVG", "media", 20)["2001-02"] == pytest.approx(20.5)
    assert nc.mensual_desde_diario(diario, "PRCP", "suma")["2001-02"] == 28.0
    del diario["2001-02-28"]
    assert "2001-02" not in nc.mensual_desde_diario(diario, "PRCP", "suma")  # mes incompleto
    assert nc.mensual_desde_diario({k: diario[k] for k in list(diario)[:19]}, "TAVG", "media", 20) == {}


def test_anual_desde_mensual_y_anomalias():
    m = {f"2001-{k:02d}": float(k) for k in range(1, 13)}
    m.update({f"2002-{k:02d}": 1.0 for k in range(1, 12)})
    assert nc.anual_desde_mensual(m, "media") == {2001: 6.5}
    assert nc.anual_desde_mensual(m, "suma") == {2001: 78.0}
    assert nc.anomalias({2001: 1.0, 2002: 3.0}, [2001, 2002]) == {2001: -1.0, 2002: 1.0}
    with pytest.raises(ValueError):
        nc.anomalias({2001: 1.0}, [1990])


def test_leer_busqueda_y_url_datos():
    texto = json.dumps({"results": [{"startDate": "1979-01-01T00:00:00", "endDate": "2002-10-31T23:59:59",
                                     "stations": [{"id": "NU000069034", "name": "JUIGALPA, NU"}]}]})
    assert nc.leer_busqueda(texto) == [{"id": "NU000069034", "nombre": "JUIGALPA, NU", "inicio": "1979-01-01",
                                        "fin": "2002-10-31"}]
    u = nc.url_datos("daily-summaries", ["A", "B"], "2001-01-01", "2001-12-31")
    assert "stations=A%2CB" in u and "units=metric" in u and "token" not in u


def test_token_cdo_desde_entorno(monkeypatch):
    monkeypatch.delenv("NOAA_CDO_TOKEN", raising=False)
    assert nc.token_cdo() is None
    monkeypatch.setenv("NOAA_CDO_TOKEN", "  abc  ")
    assert nc.token_cdo() == "abc"


def test_ntrs_clorofila_sintetica():
    import generar_contrastes as G
    meses = [f"{a}-{m:02d}" for a in range(2003, 2023) for m in range(1, 13)]
    t = np.array([int(x[:4]) + (int(x[5:]) - 0.5) / 12 for x in meses])
    estacional = np.array([0.3 * math.sin(2 * math.pi * int(x[5:]) / 12) for x in meses])
    vals = (1.0 + 0.02 * (t - 2003) + estacional).tolist()
    vals[5] = None
    nt = G.ntrs_clorofila(meses, vals)
    # La OLS cruda absorbe parte del ciclo estacional (no es ortogonal al tiempo dentro del año).
    assert nt["mco_mensual"]["pendiente_por_decada"] == pytest.approx(0.2, abs=0.03)
    assert nt["mco_mensual"]["significativa_5pct"]
    assert nt["theil_sen_mensual"]["pendiente_por_decada"] == pytest.approx(0.2, abs=0.02)
    an = nt["anomalias_anuales"]
    assert an[2012] - an[2011] == pytest.approx(0.02, abs=1e-3)
    assert nt["meses_por_anio"][2003] == 11


def test_parsear_hyrax_ascii_y_api_sin_token(monkeypatch):
    from clima_nic.fuentes import giovanni

    txt = (
        "Dataset: ejemplo.nc4\n"
        "lat, 12.125, 12.375\n"
        "lon, -86.375, -86.125\n"
        "precipitation[0][0], 100.0, 200.0\n"
        "precipitation[0][1], 300.0, -9999.9\n"
    )
    d = giovanni.parsear_hyrax_ascii(txt)
    assert d["lat"].tolist() == [12.125, 12.375]
    assert d["lon"].tolist() == [-86.375, -86.125]
    assert d["precipitation"][0, 0] == 100.0
    assert d["precipitation"][1, 1] == -9999.9

    txt3 = (
        "Dataset: air.nc\n"
        "Latitude, 12.5\n"
        "Longitude, -85.5\n"
        "T[time=0][0], 298.15\n"
    )
    d3 = giovanni.parsear_hyrax_ascii(txt3)
    assert d3["T"][0, 0] == 298.15

    monkeypatch.delenv("EARTHDATA_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="EARTHDATA_TOKEN"):
        giovanni.api_giovanni_serie("A", (-86, 12, -85, 13), "2020-01-01", "2020-01-31")
