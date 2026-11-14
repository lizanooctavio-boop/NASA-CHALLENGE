"""Pruebas sin red del procesado RCM (scripts/sar/rcm_procesar.py) con productos sintéticos.

    python -m pytest tests/test_rcm_procesar.py -q
"""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rcm_procesar", RAIZ / "scripts" / "sar" / "rcm_procesar.py")
rcm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rcm)

LUT = """<?xml version="1.0"?>
<lut xmlns="rcmGsProductSchema"><pixelFirstLutValue>0</pixelFirstLutValue><stepSize>2</stepSize>
<numberOfValues>3</numberOfValues><offset>{offset}</offset><gains>100 200 300</gains></lut>"""

PRODUCTO = """<?xml version="1.0"?>
<product xmlns="rcmGsProductSchema"><sourceAttributes><rawDataStartTime>2023-08-16T11:29:21.123456Z</rawDataStartTime>
</sourceAttributes><imageReferenceAttributes><geographicInformation><geolocationGrid>
{puntos}</geolocationGrid></geographicInformation></imageReferenceAttributes></product>"""
PUNTO = ("<imageTiePoint><imageCoordinate><line>{f}</line><pixel>{c}</pixel></imageCoordinate>"
         "<geodeticCoordinate><latitude>{lat}</latitude><longitude>{lon}</longitude></geodeticCoordinate></imageTiePoint>")


def test_lut_interpola_ganancias_por_columna(tmp_path):
    ruta = tmp_path / "lutSigma_HH.xml"
    ruta.write_text(LUT.format(offset=0), encoding="utf-8")
    offset, g = rcm.leer_lut(ruta, 5)
    assert offset == 0 and list(g) == [100, 150, 200, 250, 300]


def test_calibracion_sigma0_y_relleno():
    dn = np.array([[0, 10, 20]])
    s = rcm.calibrar(dn, 0.0, np.array([100.0, 100.0, 400.0]))
    assert np.isnan(s[0, 0])
    assert s[0, 1] == pytest.approx(1.0) and s[0, 2] == pytest.approx(1.0)
    assert rcm.potencia_a_db(np.array([0.01]))[0] == pytest.approx(-20.0)


def test_georreferencia_con_puntos_de_product_xml(tmp_path):
    rasterio = pytest.importorskip("rasterio")
    filas, columnas = 40, 50
    tif = tmp_path / "imagery" / "RCM_HH.tif"
    tif.parent.mkdir()
    with rasterio.open(tif, "w", driver="GTiff", width=columnas, height=filas, count=1, dtype="uint16") as f:
        f.write(np.full((filas, columnas), 100, dtype="uint16"), 1)
    puntos = "".join(PUNTO.format(f=f, c=c, lat=lat, lon=lon) for f, c, lat, lon in
                     [(0, 0, 11.6, -85.6), (0, 49, 11.6, -85.4), (39, 0, 11.4, -85.6), (39, 49, 11.4, -85.4)])
    xml = tmp_path / "metadata" / "product.xml"
    xml.parent.mkdir()
    xml.write_text(PRODUCTO.format(puntos=puntos), encoding="utf-8")
    assert len(rcm.puntos_de_control(xml)) == 4
    assert rcm.fecha_producto(xml).isoformat() == "2023-08-16T11:29:21"
    sigma0 = rcm.calibrar(np.full((filas, columnas), 100), 0.0, np.full(columnas, 1e6))
    potencia, t = rcm.a_malla_6933(sigma0, tif, xml)
    validos = np.isfinite(potencia)
    assert validos.mean() > 0.5 and np.allclose(potencia[validos], 0.01, rtol=1e-4)
    assert abs(t.a - 100) < 1e-6  # malla de 100 m


def test_superficie_candidata_solo_en_pixeles_observados():
    db = np.array([[-25.0, -18.0, -16.0, np.nan]])
    dominio = np.array([[True, True, True, True]])
    areas, observado = rcm.superficie_candidata(db, dominio)
    assert observado == pytest.approx(0.03)
    assert areas[-19.0] == pytest.approx(0.01) and areas[-17.0] == pytest.approx(0.02) and areas[-15.0] == pytest.approx(0.03)


def test_localizar_exige_imagen_lut_y_producto(tmp_path):
    with pytest.raises(FileNotFoundError):
        rcm.localizar(tmp_path)
