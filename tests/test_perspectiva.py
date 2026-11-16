"""Perspectiva climática de la próxima década (src/expediente/perspectiva.js).

Ejecuta tests/perspectiva_unidad.cjs con Node y contrasta sus salidas con implementaciones independientes en Python:
Mann-Kendall modificado (Hamed y Rao, 1998), Benjamini-Hochberg, reglas de clasificación y de tendencias destacadas,
identificador reproducible, límites físicos, faltantes sin relleno, el PDF (sección P) y el ZIP.
"""
import hashlib
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
    import pypdf
except ImportError:  # pragma: no cover
    pypdf = None
try:
    import pypdfium2
except ImportError:  # pragma: no cover
    pypdfium2 = None


def _phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def mk_hamed_rao(x, y, sen):
    """Mann-Kendall con la varianza corregida por autocorrelación de los rangos de la serie sin tendencia de Sen."""
    n = len(y)
    s = sum((1 if y[j] > y[i] else -1 if y[j] < y[i] else 0) for i in range(n - 1) for j in range(i + 1, n))
    cuentas = {}
    for v in y:
        cuentas[v] = cuentas.get(v, 0) + 1
    empates = sum(t * (t - 1) * (2 * t + 5) for t in cuentas.values() if t > 1)
    var_s = (n * (n - 1) * (2 * n + 5) - empates) / 18
    det = [v - sen * xx for v, xx in zip(y, x)]
    orden = sorted(range(n), key=lambda k: det[k])
    rango = [0] * n
    for r, k in enumerate(orden):
        rango[k] = r + 1
    mr = sum(rango) / n
    den = sum((r - mr) ** 2 for r in rango)
    lim = 1.959963984540054 / math.sqrt(n)
    suma = 0.0
    for k in range(1, n - 2):
        rho = sum((rango[i] - mr) * (rango[i - k] - mr) for i in range(k, n)) / den
        if abs(rho) > lim:
            suma += (n - k) * (n - k - 1) * (n - k - 2) * rho
    factor = max(1.0, 1 + 2 / (n * (n - 1) * (n - 2)) * suma)
    z = (s - 1) / math.sqrt(var_s * factor) if s > 0 else (s + 1) / math.sqrt(var_s * factor) if s < 0 else 0
    return s, factor, 2 * (1 - _phi(abs(z)))


def bh(ps):
    idx = sorted([i for i, p in enumerate(ps) if p is not None], key=lambda i: ps[i])
    m = len(idx)
    q = [None] * len(ps)
    acum = 1.0
    for k in range(m - 1, -1, -1):
        acum = min(acum, ps[idx[k]] * m / (k + 1))
        q[idx[k]] = min(1.0, acum)
    return q


@unittest.skipIf(NODE is None, "requiere node")
class Perspectiva(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="perspectiva_"))
        r = subprocess.run([NODE, str(RAIZ / "tests" / "perspectiva_unidad.cjs"), str(cls.tmp)], capture_output=True, check=True, timeout=900)
        cls.o = json.loads(r.stdout.decode("utf-8"))
        cls.pv = cls.o["matagalpa"]["perspectiva"]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ------------------------------------------------------------------ pruebas estadísticas
    def test_mann_kendall_modificado_coincide(self):
        for caso in self.o["mk"]:
            s, factor, p = mk_hamed_rao(caso["x"], caso["y"], caso["sen"])
            self.assertEqual(caso["r"]["S"], s)
            self.assertAlmostEqual(caso["r"]["factor_varianza"], factor, places=9)
            self.assertAlmostEqual(caso["r"]["p_modificado"], p, delta=2e-6)  # Φ por Abramowitz-Stegun (error < 1,5·10⁻⁷)
            self.assertGreaterEqual(caso["r"]["p_modificado"], caso["r"]["p_sin_correccion"] - 1e-12)
        # con autocorrelación fuerte la corrección infla la varianza
        self.assertGreater(self.o["mk"][2]["r"]["factor_varianza"], 1.5)

    def test_benjamini_hochberg(self):
        q = bh(self.o["bh"]["p"])
        for a, b in zip(self.o["bh"]["q"], q):
            if b is None:
                self.assertIsNone(a)
            else:
                self.assertAlmostEqual(a, b, places=12)

    def test_q_de_la_familia_del_area(self):
        pv = self.pv
        ps = [o["historico"]["mann_kendall"]["p_modificado"] if o["historico"].get("mann_kendall") else None for o in pv["indicadores"]]
        q = bh(ps)
        for o, qq in zip(pv["indicadores"], q):
            if qq is not None:
                self.assertAlmostEqual(o["historico"]["q_bh"], qq, places=9)
        self.assertEqual(pv["familia_hipotesis"]["pruebas"], sum(p is not None for p in ps))

    # ------------------------------------------------------------------ reglas
    def _clase_esperada(self, o):
        h, v = o["historico"], o.get("validacion")
        if not h.get("suficiente") or h["n_validos"] < 30:
            return "no_proyectable"
        if not v or not v.get("suficiente"):
            return "no_proyectable"
        m = v["modelos"][o["seleccion"]["modelo"]]
        cal = m["cobertura80"] is not None and m["cobertura80"] >= 0.6 and m["cobertura95"] >= 0.8
        if o["seleccion"]["modelo"] == "climatologia" or m["habilidad"] is None or m["habilidad"] < 0.1 or not cal:
            return "exploratorio"
        if o["clasificacion"]["motivo"] in ("contradice_proyeccion_fisica", "inhomogeneidad_lluvia_merra2"):
            return "exploratorio"
        return "validada"

    def test_clasificacion_coherente_con_las_metricas(self):
        for pv in [self.pv]:
            for o in pv["indicadores"]:
                self.assertEqual(o["clasificacion"]["clase"], self._clase_esperada(o), o["id"])
                if o.get("homogeneidad") == "lluvia_merra2":
                    self.assertNotEqual(o["clasificacion"]["clase"], "validada", o["id"])
        cl = self.o["reglas"]["clases"]
        self.assertEqual(cl["corta"]["clase"], "no_proyectable")
        self.assertNotEqual(cl["ruido"]["clase"], "validada")
        self.assertNotEqual(cl["lluvia"]["clase"], "validada")

    def test_seleccion_fuera_de_muestra_no_por_pendiente(self):
        for o in self.pv["indicadores"]:
            if not o.get("seleccion") or o["seleccion"]["motivo"] == "elegido_por_el_usuario":
                continue
            mods = o["validacion"]["modelos"]
            mejor = min(mods.values(), key=lambda m: m["rmse_decada"])["rmse_decada"]
            self.assertLessEqual(mods[o["seleccion"]["modelo"]]["rmse_decada"], mejor / 0.98 + 1e-12, o["id"])
        self.assertEqual(self.o["reglas"]["modelo_forzado"]["modelo"], "persistencia")

    def test_destacadas_superan_los_controles(self):
        pv = self.pv
        self.assertLessEqual(len(pv["destacadas"]), 10)
        for o in pv["indicadores"]:
            if o["clasificacion"]["clase"] != "validada":
                self.assertNotIn(o["id"], pv["destacadas"])
                continue
            pr = o["proyeccion"]
            c = pr["cambio_vs_referencia"]["respuesta_media"] if pr.get("respuesta_media_disponible", True) else pr["cambio_vs_referencia"]["prediccion"]
            excluye0 = c["p025"] > 0 or c["p975"] < 0
            self.assertEqual(o["id"] in pv["destacadas"], excluye0, o["id"])

    def test_faltantes_no_se_rellenan(self):
        h = self.o["reglas"]["hueco"]
        self.assertIsNone(h["obs10"]["valor"])
        self.assertIsNone(h["obs30"]["valor"])
        self.assertEqual((h["n_validos"], h["n_esperados"]), (42, 44))

    def test_limites_fisicos(self):
        self.assertGreaterEqual(self.o["reglas"]["acotada_min"], 0)
        self.assertGreaterEqual(self.o["reglas"]["acotada_central_min"], 0)
        for o in self.pv["indicadores"]:
            if o["id"] in ("tx90p", "tn90p", "prcptot", "rx1day", "rx5day", "r95p", "cdd") and o.get("proyeccion"):
                self.assertGreaterEqual(min(t["p025"] for t in o["proyeccion"]["trayectoria"]), 0, o["id"])

    def test_intervalos_ordenados_y_tipos_separados(self):
        for o in self.pv["indicadores"]:
            pr = o.get("proyeccion")
            if not pr:
                continue
            for t in pr["trayectoria"]:
                self.assertLessEqual(t["p025"], t["p10"])
                self.assertLessEqual(t["p10"], t["p90"])
                self.assertLessEqual(t["p90"], t["p975"])
            c = pr["cambio_vs_referencia"]
            if pr.get("respuesta_media_disponible", True):
                # la respuesta media (confianza) es más estrecha que la predicción de la media decenal
                self.assertLessEqual(c["respuesta_media"]["p975"] - c["respuesta_media"]["p025"], c["prediccion"]["p975"] - c["prediccion"]["p025"] + 1e-9, o["id"])
            self.assertTrue(0 <= pr["deteccion_10_anios"] <= 1)

    # ------------------------------------------------------------------ fechas, CMIP6 y exclusiones
    def test_fechas_y_horizonte(self):
        pv = self.pv
        self.assertEqual(pv["horizonte"], {"generacion": 2026, "inicio": 2027, "fin": 2036})
        for o in pv["indicadores"]:
            self.assertEqual(o["anticipacion_inicio"], 2027 - o["ultimo_anio_completo"])
            self.assertLessEqual(o["entrenamiento"][1], 2026)
        self.assertEqual(pv["modalidades"]["prediccion_decenal_inicializada"], False)

    def test_cmip6_es_dispersion_entre_modelos(self):
        pv = self.pv
        anios = {int(l.split(",")[5]) for l in (RAIZ / "data/expediente/cmip6_regional_mensual.csv").read_text(encoding="utf-8").splitlines()[1:] if l}
        self.assertEqual(pv["cmip6_fuente"]["interpolado"], 2027 not in anios)  # se interpola solo si faltan los años
        t2m = next(o for o in pv["indicadores"] if o["id"] == "consulta_T2M")
        for esc, c in t2m["cmip6"]["escenarios"].items():
            self.assertEqual(c["n_modelos"], 6)
            self.assertLessEqual(c["cambio_min"], c["cambio_mediana"])
            self.assertLessEqual(c["cambio_mediana"], c["cambio_max"])
            self.assertEqual(c["modelos_aumento"] + c["modelos_disminucion"], 6)
        self.assertGreater(t2m["cmip6"]["escenarios"]["ssp585"]["cambio_mediana"], t2m["cmip6"]["escenarios"]["ssp245"]["cambio_mediana"])

    def test_variables_excluidas_con_motivo(self):
        ids = {e["id"] for e in self.pv["excluidas"]}
        self.assertTrue({"spi", "tsm", "nivel_mar", "huracanes"} <= ids)
        for e in self.pv["excluidas"]:
            self.assertTrue(e["motivo"] and e["motivo_en"])

    # ------------------------------------------------------------------ identidad y estado
    def test_identificador_reproducible(self):
        i = self.o["identidad"]
        self.assertTrue(i["id"].startswith("P-"))
        self.assertTrue(i["igual"])
        self.assertTrue(i["verifica"])
        self.assertFalse(i["alterada"])
        self.assertTrue(i["otra_semilla"])

    def test_estado_de_la_consulta(self):
        e = self.o["estado"]
        self.assertEqual(e["defecto"]["modelo"], "auto")
        self.assertEqual(e["escenarios_filtrados"]["escenarios"], ["ssp585"])
        self.assertEqual(e["modelo_invalido"], "parametro_invalido")
        self.assertEqual(e["semilla_invalida"], "parametro_invalido")
        self.assertEqual(e["n_sim_invalido"], "parametro_invalido")
        self.assertTrue(e["mismo_consulta_id"])  # las opciones de la perspectiva no cambian C- ni R-

    # ------------------------------------------------------------------ paquete e informe
    def test_zip_con_la_perspectiva(self):
        z = zipfile.ZipFile(self.tmp / "matagalpa_perspectiva.zip")
        self.assertIsNone(z.testzip())
        for n in ["perspectiva.json", "observaciones_indicadores.csv", "proyecciones.csv", "validacion.csv"]:
            self.assertIn(n, z.namelist())
        man = json.loads(z.read("manifest.json"))
        for a in man["archivos"]:
            self.assertEqual(hashlib.sha256(z.read(a["nombre"])).hexdigest(), a["sha256"], a["nombre"])
        pv = json.loads(z.read("perspectiva.json"))
        self.assertEqual(pv["perspectiva_id"], self.pv["perspectiva_id"])
        self.assertEqual(man["perspectiva"]["perspectiva_id"], pv["perspectiva_id"])
        obs = z.read("observaciones_indicadores.csv").decode("utf-8")
        self.assertNotIn(",0,0,0,0", obs)

    @unittest.skipIf(pypdf is None, "requiere pypdf")
    def test_pdf_seccion_p(self):
        texto = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(self.tmp / "matagalpa_perspectiva.pdf")).pages)
        for frase in ["BLOQUE 1", "BLOQUE 2", "Perspectiva climática de la próxima década: 2027–2036", "Tabla de tendencias",
                      "Ficha por indicador", "Validación retrospectiva", self.pv["perspectiva_id"]]:
            self.assertIn(frase, texto)
        portada = pypdf.PdfReader(str(self.tmp / "matagalpa_portada.pdf")).pages[0]
        self.assertIn("Imagen ilustrativa del lugar: Imagen de prueba", portada.extract_text())
        self.assertNotIn("no se pudo incorporar", portada.extract_text())
        self.assertGreaterEqual(len(portada.images), 1)
        en = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(self.tmp / "matagalpa_perspectiva_en.pdf")).pages)
        self.assertIn("2027–2036", en)
        self.assertNotIn("Ficha por indicador", en)

    @unittest.skipIf(pypdfium2 is None, "requiere pypdfium2")
    def test_pdf_sin_texto_fuera_de_pagina(self):
        for nombre in ["matagalpa_perspectiva.pdf", "matagalpa_perspectiva_en.pdf", "matagalpa_portada.pdf"]:
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

    def test_insumos_publicados(self):
        s = (RAIZ / "scripts/preparar_render.mjs").read_text(encoding="utf-8")
        self.assertIn("data/expediente", s)
        self.assertIn("indices_anuales_celdas.csv", s)
        self.assertIn("src/expediente/perspectiva.js", (RAIZ / "index.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
