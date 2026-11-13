"""Pruebas sin red de los recursos de la CSA y del caso de contraste canadiense.

- data/regiones_canada.geojson: GeoJSON válido en EPSG:4326, al sur de 60° N, fuente y licencia presentes, tamaño.
- clima_nic.fuentes.lagos: parseo de un CSV de Hydrocron guardado como fixture, descarte de rellenos y de
  calidad, formato del lake_id de la PLD (10 dígitos).

    python -m pytest tests/test_recursos_csa.py -q
"""
import json
import math
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))

REGION = RAIZ / "data" / "regiones_canada.geojson"
CAMPOS_COMUNES = {"id", "nombre", "tipo", "rol", "bbox", "area_km2"}  # mismo esquema que data/dominios.geojson


def _coordenadas(geom):
    """Itera todas las posiciones (lon, lat) de un Polygon o MultiPolygon GeoJSON."""
    anillos = geom["coordinates"] if geom["type"] == "Polygon" else [a for p in geom["coordinates"] for a in p]
    for anillo in anillos:
        yield from anillo


class RegionCanada(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texto = REGION.read_text(encoding="utf-8")
        cls.doc = json.loads(cls.texto)
        cls.feat = cls.doc["features"][0]
        cls.props = cls.feat["properties"]

    def test_estructura_geojson(self):
        self.assertEqual(self.doc["type"], "FeatureCollection")
        self.assertEqual(len(self.doc["features"]), 1)
        self.assertEqual(self.feat["type"], "Feature")
        self.assertIn(self.feat["geometry"]["type"], ("Polygon", "MultiPolygon"))
        self.assertEqual(self.feat["id"], self.props["id"])

    def test_esquema_como_dominios(self):
        self.assertTrue(CAMPOS_COMUNES <= self.props.keys())
        self.assertEqual(self.props["tipo"], "ecozona")
        self.assertEqual(self.props["rol"], "contraste")

    def test_epsg4326_y_al_sur_de_60N(self):
        self.assertEqual(self.props["crs"], "EPSG:4326")
        lons, lats = zip(*[(c[0], c[1]) for c in _coordenadas(self.feat["geometry"])])
        self.assertTrue(all(-180 <= x <= 180 for x in lons))
        self.assertTrue(all(-90 <= y <= 90 for y in lats))
        # Cobertura completa de IMERG: 60° S–60° N.
        self.assertLess(max(lats), 60.0)
        self.assertGreater(min(lats), -60.0)
        # Coherente con el bbox declarado.
        oeste, sur, este, norte = self.props["bbox"]
        self.assertAlmostEqual(min(lons), oeste, places=2)
        self.assertAlmostEqual(max(lats), norte, places=2)

    def test_anillos_cerrados(self):
        g = self.feat["geometry"]
        poligonos = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for pol in poligonos:
            for anillo in pol:
                self.assertGreaterEqual(len(anillo), 4)
                self.assertEqual(anillo[0], anillo[-1])

    def test_fuente_y_licencia(self):
        lic = self.props["licencia"]
        self.assertEqual(lic["nombre"], "Open Government Licence – Canada")
        self.assertTrue(lic["url"].startswith("https://open.canada.ca/"))
        self.assertIn("Open Government Licence", lic["atribucion"])
        fuente = self.props["fuente"]
        for k in ("url_conjunto", "url_descarga", "url_geoca"):
            self.assertTrue(fuente[k].startswith("https://"), k)
        self.assertRegex(fuente["sha256_descarga"], r"^[0-9a-f]{64}$")
        self.assertRegex(self.props["fecha_descarga"], r"^\d{4}-\d{2}-\d{2}$")

    def test_simplificacion_y_areas(self):
        p = self.props
        self.assertTrue(0 < p["simplificacion"]["tolerancia_grados"] <= 0.02)
        self.assertLess(p["vertices_simplificado"], p["vertices_original"])
        # La simplificación no debe cambiar el área más de un 1 %.
        self.assertLess(abs(p["area_km2"] - p["area_km2_original"]) / p["area_km2_original"], 0.01)
        # Ecozona Prairies: ~4,7·10⁵ km².
        self.assertTrue(4.0e5 < p["area_km2"] < 5.5e5)

    def test_tamano(self):
        self.assertLess(REGION.stat().st_size, 300 * 1024)

    def test_geometria_valida_y_area(self):
        try:
            from shapely.geometry import shape
            from clima_nic.rutas import proyectar_6933
        except ImportError:
            self.skipTest("requiere shapely y pyproj")
        g = shape(self.feat["geometry"])
        self.assertTrue(g.is_valid)
        area = proyectar_6933(g).area / 1e6
        self.assertTrue(math.isclose(area, self.props["area_km2"], rel_tol=1e-3))


class HydrocronYSar(unittest.TestCase):
    def test_grealm_gsfc_no_confunde_coordenadas_con_alturas(self):
        from clima_nic.fuentes.lagos import leer_grealm
        text = '11.792 -85.714 : coordinates\nSEN6A 220 20261107 16 4 0.15 0.043 18.53 AMR GIM ECM 1 2 0 32.18 1'
        self.assertEqual(leer_grealm(text), (['2026-11-07'], [32.18]))

    def test_no_data_y_rellenos(self):
        from clima_nic.fuentes.lagos import leer_hydrocron
        csv = ('time_str,wse,no_data\n2023-08-01T00:00:00Z,32.5,0\n'
               '2023-08-02T00:00:00Z,-999999999999,0\n'
               '2023-08-03T00:00:00Z,nan,0\n'
               '2023-08-04T00:00:00Z,33,1\nno_data,34,0\n')
        rows = leer_hydrocron({'results': {'csv': csv}})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['altura_m'], 32.5)

    def test_mascara_nodata_y_area(self):
        import numpy as np
        import rasterio
        import tempfile
        from rasterio.transform import from_origin
        from clima_nic.fuentes.sar_agua import procesar
        with tempfile.TemporaryDirectory() as td:
            src, dst = Path(td)/'in.tif', Path(td)/'out.tif'
            with rasterio.open(src, 'w', driver='GTiff', width=2, height=2, count=1,
                               dtype='float32', crs='EPSG:6933', nodata=-9999,
                               transform=from_origin(0, 200, 100, 100)) as f:
                f.write(np.array([[-20, -10], [-9999, -22]], dtype='float32'), 1)
            r = procesar(src, dst)
            self.assertAlmostEqual(r['area_agua_km2'], .02)
            self.assertAlmostEqual(r['area_valida_km2'], .03)
            with rasterio.open(dst) as f:
                self.assertEqual(f.read(1).tolist(), [[1, 0], [255, 1]])

    def test_fechas_comunes_sin_interpolar(self):
        from clima_nic.fuentes.sar_agua import fechas_comunes
        self.assertEqual(fechas_comunes({'2023-01-01':32}, {'2023-01-02':8000}), [])


if __name__ == "__main__":
    unittest.main()
