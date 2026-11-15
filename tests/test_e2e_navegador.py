"""Recorrido de extremo a extremo en un navegador real (Edge o Chrome sin interfaz).

Construye la demo publicada (node scripts/preparar_render.mjs), la sirve por HTTP local y la abre en
un navegador Chromium headless. Comprueba:
1. Pestaña «Rainfall trend» (#tendencias): regiones (Nicaragua, Study box, Honduras, Costa Rica),
   veredictos, gráfica SVG, comparación de pendientes y las tres descargas (CSV serie, CSV pendientes
   con p de Mann-Kendall, JSON evidencia) frente a data/clima.json.
2. Pestaña «Climate indicators» (#indicadores): regiones (NIC, pacifico, central, caribe), variables
   independientes (temperatura_gistemp, lluvia_anual_imerg, lluvia_jun_nov_imerg, ndvi), contraste
   frente a MERRA-2 y descarga CSV frente a data/fenomenos_nicaragua.json.
3. Pestaña «El Niño & cyclones» (#fenomenos): bloque ONI visible con datos reales.
4. Pestañas «Investigate», «Learn» y «Sources»: cada investigación de data/recursos_integrados.json con
   su veredicto, sus contrastes y su CSV; solo los recursos en uso en «Sources».
5. Ausencia de textos residuales de «datos de ejemplo».
"""
import csv
import functools
import html
import http.server
import io
import json
import os
import shutil
import socketserver
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")
MAPA = {"nicaragua": "NIC", "caja_original": "caja_sicc", "honduras": "HND", "costa_rica": "CRI"}
NOMBRES_UI = {"nicaragua": "Nicaragua", "caja_original": "Study box", "honduras": "Honduras", "costa_rica": "Costa Rica"}


def buscar_navegador():
    for ruta in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                 r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                 r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                 r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"):
        if os.path.isfile(ruta):
            return ruta
    for nombre in ("chrome", "google-chrome", "chromium", "msedge"):
        ruta = shutil.which(nombre)
        if ruta:
            return ruta
    return None


NAVEGADOR = buscar_navegador()


class _TCPServerHilos(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


class _HandlerSilencioso(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/__resultado":
            n = int(self.headers.get("Content-Length", "0"))
            cuerpo = self.rfile.read(n).decode("utf-8", errors="replace")
            self.server.resultado_e2e = cuerpo
            self.server.evento_e2e.set()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok")
            return
        self.send_error(404)

    def log_message(self, format, *args):
        pass


@unittest.skipIf(NODE is None or NAVEGADOR is None or not (RAIZ / "data" / "clima.json").is_file(),
                 "requiere node, un navegador Chromium y data/clima.json")
class RecorridoEnNavegador(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([NODE, "scripts/preparar_render.mjs"], cwd=RAIZ, check=True, capture_output=True)
        public_dir = RAIZ / "public"
        pagina = (public_dir / "index.html").read_text(encoding="utf-8")
        sonda = (RAIZ / "tests" / "e2e" / "sonda.js").read_text(encoding="utf-8")
        (public_dir / "__e2e.html").write_text(
            pagina.replace("</body>", "<script>\n" + sonda + "\n</script></body>"), encoding="utf-8"
        )
        cls.tmp = tempfile.mkdtemp(prefix="nasa-e2e-")
        handler = functools.partial(_HandlerSilencioso, directory=str(public_dir))
        cls.httpd = _TCPServerHilos(("127.0.0.1", 0), handler)
        cls.httpd.resultado_e2e = None
        cls.httpd.evento_e2e = threading.Event()
        puerto = cls.httpd.server_address[1]
        cls.hilo = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.hilo.start()
        proc = None
        try:
            url = f"http://127.0.0.1:{puerto}/__e2e.html"
            proc = subprocess.Popen(
                # Este recorrido valida datos, gráficas y CSV. Sin GPU, evita que el globo
                # consuma la CPU con WebGL por software; la demo conserva su mapa 2D de respaldo.
                [NAVEGADOR, "--headless=new", "--disable-gpu", "--disable-software-rasterizer", "--no-first-run",
                 "--no-default-browser-check",
                 f"--user-data-dir={Path(cls.tmp) / 'perfil'}",
                 url],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            # La sonda recorre cada investigación (gráfica y CSV): el tiempo crece con el número de series.
            if not cls.httpd.evento_e2e.wait(timeout=90):
                raise AssertionError("la sonda no produjo salida en 90s; ¿falló la demo al cargar?")
            raw = cls.httpd.resultado_e2e
            if raw.startswith("ERROR "):
                raise AssertionError(f"Error en sonda JS: {raw}")
            cls.salida = json.loads(raw)
        finally:
            if proc is not None and proc.poll() is None:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
            (public_dir / "__e2e.html").unlink(missing_ok=True)
        cls.clima = json.loads((RAIZ / "data" / "clima.json").read_text(encoding="utf-8"))
        cls.dom = {d["id"]: d for d in cls.clima["dominios"]}
        cls.fen = json.loads((RAIZ / "data" / "fenomenos_nicaragua.json").read_text(encoding="utf-8"))
        cls.fen_reg = {r["id"]: r for r in cls.fen["regiones"]}

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "httpd"):
            cls.httpd.shutdown()
            cls.httpd.server_close()
        if hasattr(cls, "tmp"):
            shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_sin_datos_sinteticos_ni_texto_de_ejemplo(self):
        texto = self.salida["textoCompleto"].lower()
        self.assertNotIn("datos de ejemplo", texto)
        self.assertNotIn("synthetic example", texto)
        for r in self.salida["regiones"].values():
            for contenido in r["descargas"]:
                self.assertNotIn("SINTÉTICOS", contenido)
                self.assertNotIn("_EJEMPLO", contenido)
                self.assertNotIn("datos de ejemplo", contenido.lower())

    def test_seleccion_serie_y_comparacion_del_mismo_dominio(self):
        for rid, r in self.salida["regiones"].items():
            nombre = NOMBRES_UI[rid]
            with self.subTest(rid):
                self.assertEqual(r["aria"], "true")
                self.assertEqual(r["seriePuntos"], 24)
                self.assertTrue(r["veredicto"].startswith(nombre), r["veredicto"][:60])
                self.assertIn(f"Annual precipitation in {nombre} from 2001 to 2024", r["serieAria"])
                self.assertEqual(r["compFilas"], 4)

    def test_las_tres_descargas_coinciden_con_el_json_e_incluyen_mann_kendall_p(self):
        for rid, r in self.salida["regiones"].items():
            d = self.dom[MAPA[rid]]
            t = d["tendencia"]
            serie_csv, pend_csv, evidencia = r["descargas"]
            with self.subTest(rid):
                filas = [x for x in serie_csv.splitlines() if not x.startswith("#")]
                rd = list(csv.DictReader(io.StringIO("\n".join(filas))))
                self.assertEqual([int(x["year"]) for x in rd], d["anios_validos"])
                for x, v in zip(rd, d["serie_anual_mm"]):
                    self.assertAlmostEqual(float(x["rainfall_mm"]), v, delta=0.06)
                filas = [x for x in pend_csv.splitlines() if not x.startswith("#")]
                fila = {x["area_id"]: x for x in csv.DictReader(io.StringIO("\n".join(filas)))}[rid]
                self.assertAlmostEqual(float(fila["ls_slope_mm_decade"]), t["mm_por_decada"], delta=1e-3)
                self.assertAlmostEqual(float(fila["ls_ci_low"]), t["ic_mm_por_decada"][0], delta=1e-3)
                self.assertAlmostEqual(float(fila["hac_ci_high"]), t["controles"]["hac"]["ic_mm_por_decada"][1], delta=1e-3)
                self.assertAlmostEqual(float(fila["mann_kendall_p"]), t["controles"]["mann_kendall"]["p_valor"], delta=1e-3)
                ev = json.loads(evidencia)
                er = next(q for q in ev["areas"] if q["id"] == rid)
                self.assertEqual([p["valor"] for p in er["series"]], d["serie_anual_mm"])
                self.assertEqual(ev["period"], [2001, 2024])

    def test_costa_rica_aparece_como_dependiente_del_metodo(self):
        texto = self.salida["regiones"]["costa_rica"]["veredicto"]
        self.assertIn("methods disagree", texto.lower())
        self.assertNotIn("Insufficient evidence", texto)

    def test_contexto_oni_visible_con_datos_reales(self):
        self.assertTrue(self.salida["enos"]["visible"])
        self.assertGreaterEqual(self.salida["enos"]["numTarjetas"], 2)
        self.assertIn("ONI", self.salida["enos"]["tarjetas"])
        self.assertIn("NOAA", self.salida["enos"]["tarjetas"])
        self.assertNotIn("unavailable", self.salida["enos"]["tarjetas"].lower())

    def test_pestana_climate_indicators_regiones_variables_contraste_y_csv(self):
        esperadas_por_region = {
            "NIC": ["temperatura_gistemp", "lluvia_anual_imerg", "lluvia_jun_nov_imerg"],
            "pacifico": ["temperatura_gistemp", "ndvi"],
            "central": ["temperatura_gistemp", "ndvi"],
            "caribe": ["temperatura_gistemp", "ndvi"],
        }
        for rid, vars_esp in esperadas_por_region.items():
            info_reg = self.salida["indicadores"][rid]
            self.assertEqual(info_reg["variablesDisponibles"], vars_esp)
            for vid in vars_esp:
                with self.subTest(region=rid, variable=vid):
                    v_ui = info_reg["variables"][vid]
                    v_json = self.fen_reg[rid]["variables"][vid]
                    self.assertEqual(v_ui["regAria"], "true")
                    self.assertEqual(v_ui["varAria"], "true")
                    self.assertEqual(v_ui["csvNombre"], f"{vid}_{rid}.csv")
                    # Verificar contraste con MERRA-2
                    tiene_contraste = (
                        (vid == "temperatura_gistemp" and f"temperatura_{rid}" in self.fen["comparaciones_independientes"])
                        or (vid == "lluvia_anual_imerg" and f"lluvia_{rid}" in self.fen["comparaciones_independientes"])
                    )
                    self.assertEqual(v_ui["contrasteVisible"], tiene_contraste)
                    if tiene_contraste:
                        self.assertIn("MERRA-2", v_ui["contrasteSub"])
                        self.assertIn("MERRA-2", v_ui["contrasteTarjetas"])
                    # Verificar descarga CSV contra fenomenos_nicaragua.json
                    lineas = [
                        l.strip() for l in v_ui["csvTexto"].lstrip("\ufeff").splitlines()
                        if l.strip() and not l.startswith("#")
                    ]
                    lector = list(csv.reader(io.StringIO("\n".join(lineas))))
                    self.assertEqual(lector[0][0], "year")
                    anios_csv = [int(f[0]) for f in lector[1:]]
                    vals_csv = [float(f[1]) for f in lector[1:]]
                    self.assertEqual(anios_csv, v_json["anios"])
                    for a, b in zip(vals_csv, v_json["valores"]):
                        self.assertAlmostEqual(a, b, delta=1e-4)


    def test_pestana_investigate_veredictos_contrastes_csv_y_fuentes(self):
        datos = json.loads((RAIZ / "data" / "recursos_integrados.json").read_text(encoding="utf-8"))
        inv = self.salida["investigar"]
        self.assertIsNone(inv["error"])
        self.assertEqual(inv["categorias"], [c["id"] for c in datos["categorias"] if c["con_datos"]])
        textos = {"tendencia_detectada": "Trend detected", "evidencia_insuficiente": "Not enough evidence of a trend",
                  "metodos_discrepan": "Methods disagree", "datos_insuficientes": "Not enough data for a trend test"}
        for caso in datos["investigaciones"]:
            ui = inv["casos"][caso["id"]]
            with self.subTest(caso["id"]):
                self.assertEqual(ui["seleccion"], caso["id"])
                esperado = textos[caso["tendencia"]["veredicto"]] if "tendencia" in caso else "Record too short for a trend test"
                self.assertEqual(ui["estado"], esperado)
                if caso.get("validacion", {}).get("estado") == "NO_VALIDADA":
                    self.assertIn("Not validated", ui["detalle"])
                    desde, hasta = caso["periodo"]
                    self.assertIn(f"{desde}–{hasta}", ui["detalle"])
                    self.assertIn(f"{desde} to {hasta}", ui["serieAria"])
                self.assertEqual(ui["contrastes"], len(caso["contrastes"]))
                self.assertEqual(ui["csvNombre"], f"{caso['id']}.csv")
                filas = [l for l in ui["csvTexto"].lstrip("﻿").splitlines() if l and not l.startswith("#")][1:]
                self.assertEqual([f.split(",")[0] for f in filas], [str(t) for t in caso["tiempos"]])
                for f, v in zip(filas, caso["valores"]):
                    if v is not None:
                        self.assertAlmostEqual(float(f.split(",")[1]), v, delta=1e-6)
        self.assertEqual(inv["demos"], [d["id"] for d in datos["demostraciones"]])
        self.assertEqual(inv["fuentes"], [r["id"] for r in datos["recursos"] if r["estado"] == "en_uso"])
        self.assertGreaterEqual(inv["aprender"], 8)


if __name__ == "__main__":
    unittest.main()
