"""Pruebas para el buscador de lugares (Natural Earth) y conversión de coordenadas."""

import json
import math
import shutil
import subprocess
import unittest
from pathlib import Path

from pyproj import Transformer

RAIZ = Path(__file__).resolve().parents[1]
LUGARES_JSON = RAIZ / "data" / "lugares_mundo.json"
NODE = shutil.which("node")

# Puntos de referencia conocidos: Managua, Dhaka y Antártida (McMurdo).
PUNTOS_REFERENCIA = [
    {
        "nombre": "Managua",
        "lat": 12.1364,
        "lon": -86.2514,
        "utm_zona": 16,
        "utm_hem": "N",
        "epsg_utm": "EPSG:32616",
        "mgrs_gzd": "16P",
    },
    {
        "nombre": "Dhaka",
        "lat": 23.8103,
        "lon": 90.4125,
        "utm_zona": 46,
        "utm_hem": "N",
        "epsg_utm": "EPSG:32646",
        "mgrs_gzd": "46Q",
    },
    {
        "nombre": "Antarctica (McMurdo)",
        "lat": -77.8419,
        "lon": 166.6863,
        "utm_zona": 58,
        "utm_hem": "S",
        "epsg_utm": "EPSG:32758",
        "mgrs_gzd": "58C",
    },
]


def _mgrs_referencia_utm(zona: int, banda: str, este: float, norte: float) -> str:
    """Calcula la referencia MGRS estándar a partir de coordenadas UTM (WGS84)."""
    conjunto = ((zona - 1) % 6) + 1
    cols = ["ABCDEFGH", "JKLMNPQR", "STUVWXYZ"][(conjunto - 1) % 3]
    filas = "ABCDEFGHJKLMNPQRSTUV" if conjunto % 2 == 1 else "FGHJKLMNPQRSTUVABCDE"
    col = cols[int(este // 100000) - 1]
    fila = filas[int(norte // 100000) % 20]
    e5 = f"{int(este) % 100000:05d}"
    n5 = f"{int(norte) % 100000:05d}"
    return f"{zona}{banda} {col}{fila} {e5} {n5}"


class TestLugaresMundo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datos = json.loads(LUGARES_JSON.read_text(encoding="utf-8"))

    def test_tamano_y_estructura_compacta(self):
        self.assertLess(LUGARES_JSON.stat().st_size, 600 * 1024)
        paises = self.datos.get("paises", [])
        self.assertGreater(len(paises), 180)
        for p in paises:
            self.assertEqual(len(p["iso"]), 3)
            self.assertEqual(len(p["bbox"]), 4)
            self.assertEqual(len(p["centro"]), 2)
            self.assertLessEqual(len(p["ciudades"]), 30)
            pobs = [c["pob"] for c in p["ciudades"]]
            self.assertEqual(pobs, sorted(pobs, reverse=True))

    def test_paises_y_ciudades_clave(self):
        por_iso = {p["iso"]: p for p in self.datos["paises"]}
        self.assertIn("BGD", por_iso)
        bgd_ciudades = {c["nombre"] for c in por_iso["BGD"]["ciudades"]}
        self.assertIn("Dhaka", bgd_ciudades)
        self.assertIn("Khulna", bgd_ciudades)

        self.assertIn("NIC", por_iso)
        nic_ciudades = {c["nombre"] for c in por_iso["NIC"]["ciudades"]}
        self.assertIn("Managua", nic_ciudades)

        self.assertIn("CRI", por_iso)
        cri_ciudades = {c["nombre"] for c in por_iso["CRI"]["ciudades"]}
        self.assertIn("San José", cri_ciudades)


class TestCoordenadasYReferencia(unittest.TestCase):
    def test_referencia_utm_y_mgrs_tres_puntos(self):
        t_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        for pt in PUNTOS_REFERENCIA:
            t_utm = Transformer.from_crs("EPSG:4326", pt["epsg_utm"], always_xy=True)
            e, n = t_utm.transform(pt["lon"], pt["lat"])
            zona_calc = math.floor((pt["lon"] + 180) / 6) + 1
            self.assertEqual(zona_calc, pt["utm_zona"], pt["nombre"])
            self.assertGreater(e, 100000)
            self.assertLess(e, 900000)
            mgrs = _mgrs_referencia_utm(pt["utm_zona"], pt["mgrs_gzd"][-1], e, n)
            self.assertTrue(mgrs.startswith(pt["mgrs_gzd"] + " "), mgrs)

            mx, my = t_3857.transform(pt["lon"], pt["lat"])
            self.assertTrue(math.isfinite(mx) and math.isfinite(my))

    def test_archivos_integrados_en_index_y_sintaxis_js(self):
        html = (RAIZ / "index.html").read_text(encoding="utf-8")
        self.assertIn("app/buscador.css", html)
        self.assertIn("https://cdnjs.cloudflare.com/ajax/libs/proj4js/2.9.2/proj4.js", html)
        self.assertIn("app/buscador.js", html)
        self.assertIn("app/coordenadas.js", html)
        if NODE:
            for js in ("app/buscador.js", "app/coordenadas.js"):
                subprocess.run([NODE, "--check", str(RAIZ / js)], check=True)
