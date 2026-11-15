"""Expediente técnico por área de interés (src/expediente/): geometría, estado, análisis, paquete e informe.

Ejecuta tests/expediente_unidad.cjs con Node y contrasta sus salidas con implementaciones independientes:
áreas geodésicas con pyproj, pendientes con scipy y el PDF con pypdf/pypdfium2. Los datos son las respuestas
reales de NASA POWER guardadas en tests/fixtures/expediente/ (2026-11-15).
"""
import io
import json
import math
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")

try:
    from scipy import stats
except ImportError:  # pragma: no cover
    stats = None
try:
    import pypdf
except ImportError:  # pragma: no cover
    pypdf = None
try:
    import pypdfium2
except ImportError:  # pragma: no cover
    pypdfium2 = None


@unittest.skipIf(NODE is None, "requiere node")
class Expediente(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="expediente_"))
        r = subprocess.run([NODE, str(RAIZ / "tests" / "expediente_unidad.cjs"), str(cls.tmp)], capture_output=True, check=True, timeout=600)
        cls.o = json.loads(r.stdout.decode("utf-8"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ------------------------------------------------------------------ geometría
    def test_area_geodesica_coincide_con_pyproj(self):
        for m in self.o["areas_municipios"]:
            with self.subTest(m["cod"]):
                self.assertAlmostEqual(m["js"], m["pyproj"], delta=max(0.01, 2e-4 * m["pyproj"]))
        self.assertEqual(len(self.o["areas_municipios"]), 153)

    def test_area_frente_a_la_publicada_por_ineter(self):
        rel = sorted(abs(m["js"] - m["ineter"]) / m["ineter"] for m in self.o["areas_municipios"])
        self.assertLess(rel[len(rel) // 2], 0.005)  # mediana < 0,5 % (INETER mide en su propia proyección)

    def test_circulo_antimeridiano_multipoligono_y_agujeros(self):
        c = self.o["circulo"]
        self.assertAlmostEqual(c["area"], c["teorica"] * (360 / (2 * math.pi)) * math.sin(2 * math.pi / 360), delta=0.5)
        a = self.o["antimeridiano"]
        self.assertAlmostEqual(a["area"], a["referencia"], delta=1e-6)
        self.assertGreater(a["extension"][0], a["extension"][2])  # oeste > este: cruza el antimeridiano (RFC 7946)
        self.assertTrue(a["contiene"])
        self.assertGreater(a["celdas"], 0)
        m = self.o["multipoligono"]
        self.assertAlmostEqual(m["total"], sum(m["partes"]), delta=1e-6)
        h = self.o["agujero"]
        self.assertAlmostEqual(h["total"], h["exterior"] - h["interior"], delta=1e-3)
        self.assertEqual(self.o["orientacion"]["avisos"], ["orientacion_corregida"])

    def test_centro_representativo_cae_dentro(self):
        c = self.o["forma_c"]
        self.assertEqual(c["metodo"], "punto_interior")
        self.assertFalse(1 < c["lon"] < 3 and 1 < c["lat"] < 2)  # fuera de la muesca de la «C»

    def test_punto_sin_superficie_y_celda_que_lo_contiene(self):
        p = self.o["punto"]
        self.assertIsNone(p["area"])
        cel = p["celdas"][0]
        self.assertEqual((cel["lat"], cel["lon"]), (12.0, -86.25))
        self.assertTrue(cel["caja"][0] <= -86.2514 <= cel["caja"][2] and cel["caja"][1] <= 12.1364 <= cel["caja"][3])

    def test_geometrias_invalidas(self):
        self.assertEqual(self.o["errores"], {
            "vacia": "vacia", "nula": "vacia", "lazo": "autointerseccion", "rango": "fuera_de_rango", "abierto": "anillo_abierto",
            "linea": "tipo_no_admitido", "texto": "coordenada_invalida", "compleja": "demasiado_compleja", "grande": "demasiado_grande"})

    def test_pesos_por_superficie_de_interseccion(self):
        c = self.o["celdas_chontales"]
        self.assertAlmostEqual(c["suma_pesos"], 1, places=9)
        self.assertAlmostEqual(c["suma_inter"], c["area"], delta=1e-3 * c["area"])

    # ------------------------------------------------------------------ estado y enlaces
    def test_enlace_ida_y_vuelta_y_validacion(self):
        e = self.o["estado"]
        self.assertTrue(e["ida_vuelta"])
        self.assertTrue(e["compartible"])
        self.assertFalse(e["local"])
        self.assertTrue(e["url"].startswith("https://nasa-challenge-q6cx.onrender.com/#inv="))
        self.assertNotRegex(e["url"].lower(), r"key|token|password|apikey")
        self.assertEqual(e["resultado_ref"], self.o["masaya"]["id"])
        self.assertTrue(e["mismo_id_sin_vista"])
        self.assertTrue(e["id_cambia_con_periodo"])
        self.assertTrue(e["descarta_desconocidos"])
        self.assertEqual(e["errores"], {"corrupto": "estado_corrupto", "formato": "estado_corrupto", "futura": "version_futura",
                                        "vieja": "version_no_admitida", "variable": "parametro_invalido", "meses": "parametro_invalido",
                                        "periodo": "parametro_invalido", "esquema": "estado_corrupto"})
        self.assertEqual(e["sha_abc"], "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
        self.assertEqual(e["sha_vacio"], "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

    # ------------------------------------------------------------------ análisis
    def test_tendencia_es_la_de_src_estadistica(self):
        m = self.o["masaya"]
        self.assertAlmostEqual(m["tendencia"]["sen"]["pendiente_decada"], m["directo_sen_decada"], places=4)
        self.assertAlmostEqual(m["tendencia"]["mco"]["pendiente_decada"], m["directo_mco_decada"], places=4)
        self.assertEqual(m["tendencia"]["veredicto"]["estado"], m["directo_veredicto"])

    @unittest.skipIf(stats is None, "requiere scipy")
    def test_pendientes_coinciden_con_scipy(self):
        m = self.o["masaya"]
        x = [p[0] for p in m["serie"] if p[1] is not None]
        y = [p[1] for p in m["serie"] if p[1] is not None]
        ts = stats.theilslopes(y, x)
        lr = stats.linregress(x, y)
        self.assertAlmostEqual(m["tendencia"]["sen"]["pendiente_decada"], ts.slope * 10, places=3)
        self.assertAlmostEqual(m["tendencia"]["mco"]["pendiente_decada"], lr.slope * 10, places=3)
        self.assertAlmostEqual(m["tendencia"]["mco"]["p"], lr.pvalue, places=4)

    def test_identidad_del_resultado(self):
        m = self.o["masaya"]
        self.assertTrue(m["id_estable"])
        self.assertTrue(m["verifica"])
        self.assertTrue(m["detecta_alteracion"])

    def test_faltantes_no_se_rellenan(self):
        f = self.o["faltante"]
        self.assertIsNone(f["anio2003"]["valor"])
        self.assertEqual(f["anio2003"]["meses_faltantes"], [7])
        self.assertEqual(f["n"], 43)
        self.assertTrue(f["id_distinto"])
        self.assertIn("anios_excluidos", f["avisos"])

    def test_precipitacion_mm_dia_por_dias_y_punto(self):
        p = self.o["precip_punto"]
        self.assertAlmostEqual(p["valor2001"], p["esperado2001"], places=2)
        self.assertAlmostEqual(p["febrero2004"], p["bruto_feb2004"] * 29, places=6)
        self.assertIsNone(p["superficie"])
        self.assertIn("consulta_puntual", p["avisos"])
        self.assertIn("lluvia_merra2_inhomogeneidad", p["avisos"])

    def test_datos_insuficientes(self):
        i = self.o["insuficiente"]
        self.assertEqual(i["veredicto"]["estado"], "faltan")
        self.assertIsNone(i["sen"])
        self.assertTrue(i["insuficiente"])

    def test_cobertura_espacial_insuficiente_no_se_renormaliza_en_silencio(self):
        c = self.o["cobertura"]
        self.assertEqual(c["fallos"], 1)
        self.assertLess(c["fraccion"], 0.9)
        self.assertEqual(c["n"], 0)
        self.assertIn("celdas_sin_datos", c["avisos"])

    def test_red_caida(self):
        self.assertEqual(self.o["red"], {"fallos": ["red", "red"], "celdas": 0})

    # ------------------------------------------------------------------ paquete
    def test_paquete_zip_y_manifiesto(self):
        z = zipfile.ZipFile(self.tmp / "masaya.zip")
        self.assertIsNone(z.testzip())
        nombres = z.namelist()
        for n in ["informe.pdf", "area_interes.geojson", "consulta.json", "resultados.json", "serie_temporal.csv", "fuentes.csv", "manifest.json", "LEEME.txt"]:
            self.assertIn(n, nombres)
        man = json.loads(z.read("manifest.json"))
        import hashlib
        for a in man["archivos"]:
            self.assertEqual(hashlib.sha256(z.read(a["nombre"])).hexdigest(), a["sha256"], a["nombre"])
        res = json.loads(z.read("resultados.json"))
        geo = json.loads(z.read("area_interes.geojson"))
        self.assertEqual(geo["features"][0]["geometry"], res["area"]["geometria"])
        self.assertEqual(json.loads(z.read("consulta.json"))["area"]["geometria"], res["area"]["geometria"])
        serie = z.read("serie_temporal.csv").decode("utf-8").splitlines()
        cab = [l for l in serie if not l.startswith("#")]
        filas = {int(l.split(",")[0]): l.split(",")[1] for l in cab[1:]}
        for p in res["serie"]:
            if p["valor"] is None:
                self.assertEqual(filas[p["anio"]], "")  # faltante: celda vacía, nunca 0
            else:
                self.assertAlmostEqual(float(filas[p["anio"]]), p["valor"], places=6)
        self.assertEqual(self.o["paquete"]["crc_prueba"], "cbf43926")

    # ------------------------------------------------------------------ informe
    @unittest.skipIf(pypdf is None, "requiere pypdf")
    def test_pdf_cifras_enlace_y_tildes(self):
        res = json.loads((self.tmp / "masaya_resultados.json").read_text(encoding="utf-8"))
        lector = pypdf.PdfReader(str(self.tmp / "masaya.pdf"))
        texto = "\n".join(p.extract_text() for p in lector.pages)
        sen = res["tendencia"]["sen"]["pendiente_decada"]
        self.assertIn(f"{sen:.3f}".replace(".", ","), texto)  # misma cifra que resultados.json
        self.assertIn(res["resultado_id"], texto)
        self.assertIn("Metodología", texto)
        self.assertIn("Página 1 de", texto)
        self.assertIn("Notas del usuario", texto)
        self.assertIn("No es un aviso oficial", texto)
        uris = [a.get_object()["/A"]["/URI"] for p in lector.pages for a in p.get("/Annots", []) or [] if "/A" in a.get_object()]
        self.assertTrue(any(u == self.o["estado"]["url"] for u in uris))
        en = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(self.tmp / "punto_en.pdf")).pages)
        self.assertIn("Point query", en)
        self.assertIn("not an average", en)
        falta = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(self.tmp / "insuficiente.pdf")).pages)
        self.assertIn("Datos insuficientes", falta)

    @unittest.skipIf(pypdfium2 is None, "requiere pypdfium2")
    def test_pdf_sin_texto_fuera_de_pagina(self):
        for nombre in ["masaya.pdf", "punto_en.pdf", "insuficiente.pdf"]:
            doc = pypdfium2.PdfDocument(str(self.tmp / nombre))
            for i in range(len(doc)):
                pag = doc[i]
                w, h = pag.get_size()
                tp = pag.get_textpage()
                fuera = []
                for k in range(tp.count_chars()):
                    x0, y0, x1, y1 = tp.get_charbox(k)
                    if x1 - x0 > 0 and not (x0 >= 14 and x1 <= w - 14 and y0 >= 14 and y1 <= h - 14):
                        fuera.append(tp.get_text_range(k, 1))
                self.assertEqual(fuera, [], f"{nombre} página {i + 1}: texto fuera del margen de 5 mm")

    def test_traducciones_completas(self):
        self.assertEqual(self.o["i18n"]["solo_es"], [])
        self.assertEqual(self.o["i18n"]["solo_en"], [])
        self.assertEqual(self.o["i18n"]["num_es"], "-1 234,57")
        self.assertEqual(self.o["i18n"]["num_en"], "-1,234.57")

    def test_limites_publicados(self):
        mun = json.loads((RAIZ / "data/admin/nicaragua_municipios.geojson").read_text(encoding="utf-8"))
        dep = json.loads((RAIZ / "data/admin/nicaragua_departamentos.geojson").read_text(encoding="utf-8"))
        self.assertEqual(len(mun["features"]), 153)
        self.assertEqual(len(dep["features"]), 17)
        self.assertIn("INETER", mun["procedencia"]["fuente"])
        self.assertIn("admin", (RAIZ / "scripts/preparar_render.mjs").read_text(encoding="utf-8"))


class ExpedienteNavegador(unittest.TestCase):
    """Recorrido completo en Chromium. Se activa con ETD_E2E=1 (tarda varios minutos)."""

    @unittest.skipUnless(NODE and __import__("os").environ.get("ETD_E2E") == "1", "ETD_E2E=1 para ejecutar")
    def test_recorrido(self):
        salida = Path(tempfile.mkdtemp(prefix="exp_e2e_"))
        subprocess.run([NODE, str(RAIZ / "tests/e2e/expediente_navegador.cjs"), str(salida)], check=True, timeout=1800)
        r = json.loads((salida / "resumen.json").read_text(encoding="utf-8"))
        self.assertIsNone(r.get("fallo"), r.get("fallo"))
        c = r["casos"]
        m = c["municipio"]
        self.assertEqual(m["id"], m["ui_id"])
        self.assertEqual(m["zip"]["resultado_id"], m["id"])
        self.assertTrue(m["zip"]["hashes_ok"])
        self.assertEqual(m["zip"]["geom_zip"], m["geom"])
        self.assertEqual(c["restaurar"]["id"], m["id"])
        self.assertTrue(c["restaurar"]["consulta_igual"])
        self.assertEqual(c["restaurar"]["geom"], m["geom"])
        self.assertEqual(c["restaurar"]["zoom"], c["restaurar"]["zoom_original"])
        self.assertTrue(all(abs(a - b) < 1e-3 for a, b in zip(c["restaurar"]["centro"], c["restaurar"]["centro_original"])))
        self.assertTrue(c["restaurar"]["pestana"])
        self.assertIn("coincide", c["restaurar"]["mensaje"]["texto"])
        self.assertEqual(c["guardado"]["peticiones_nuevas"], 0)
        self.assertIn("consulta_puntual", c["punto"]["avisos"])
        self.assertEqual(c["insuficiente"]["estado"], "faltan")
        self.assertFalse(c["red"]["hay_resultado"])
        propios = [e for e in r["errores_consola"] if e["tipo"] == "pageerror" or "expediente" in (e.get("url") or "")]
        self.assertEqual(propios, [])
