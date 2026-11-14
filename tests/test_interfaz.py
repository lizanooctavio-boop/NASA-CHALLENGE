"""La interfaz debe mostrar exactamente lo que dice data/clima.json (requiere Node; se omite si falta)."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")
MAPA = {"nicaragua": "NIC", "caja_original": "caja_sicc", "honduras": "HND", "costa_rica": "CRI"}
ESTADO = {"tendencia_detectada": {"aumento", "disminucion"}, "evidencia_insuficiente": {"insuficiente"},
          "metodos_discrepan": {"discrepan"}}


@unittest.skipIf(NODE is None or not (RAIZ / "data" / "clima.json").is_file(), "requiere node y data/clima.json")
class InterfazCoincideConLosDatos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r = subprocess.run([NODE, str(RAIZ / "tests" / "interfaz_normalizada.cjs")], capture_output=True, check=True)
        cls.ui = json.loads(r.stdout.decode("utf-8"))
        cls.clima = json.loads((RAIZ / "data" / "clima.json").read_text(encoding="utf-8"))
        cls.dom = {d["id"]: d for d in cls.clima["dominios"]}

    def test_cuatro_regiones_sin_datos_de_ejemplo(self):
        self.assertFalse(self.ui["es_ejemplo"])
        self.assertEqual(self.ui["avisos"], [])
        self.assertEqual([r["id"] for r in self.ui["regiones"]], list(MAPA))

    def test_serie_pendiente_e_intervalos_son_los_del_json(self):
        for r in self.ui["regiones"]:
            d = self.dom[MAPA[r["id"]]]
            t = d["tendencia"]
            with self.subTest(r["id"]):
                self.assertEqual(r["n_validos"], 24)
                self.assertEqual([p["anio"] for p in r["serie"]], d["anios_validos"])
                self.assertEqual([p["valor"] for p in r["serie"]], d["serie_anual_mm"])
                self.assertEqual(r["mco"]["pendiente"], t["mm_por_decada"])
                self.assertEqual([r["mco"]["ic_inf"], r["mco"]["ic_sup"]], t["ic_mm_por_decada"])
                self.assertEqual(r["mco"]["p"], t["p_valor"])
                hac = t["controles"]["hac"]["ic_mm_por_decada"]
                self.assertEqual([r["hac"]["ic_inf"], r["hac"]["ic_sup"]], hac)
                sen = t["controles"]["theil_sen"]
                self.assertEqual(r["sen"]["pendiente"], sen["mm_por_decada"])
                self.assertEqual([r["sen"]["ic_inf"], r["sen"]["ic_sup"]], sen["ic_mm_por_decada"])
                self.assertEqual(r["sen"]["p"], t["controles"]["mann_kendall"]["p_valor"])
                self.assertEqual(r["origen"], "provided in the JSON")

    def test_veredicto_de_la_interfaz_es_el_del_json(self):
        for r in self.ui["regiones"]:
            t = self.dom[MAPA[r["id"]]]["tendencia"]
            with self.subTest(r["id"]):
                self.assertIn(r["veredicto"]["estado"], ESTADO[t["veredicto"]])

    def test_costa_rica_se_marca_como_dependiente_del_metodo(self):
        cri = next(r for r in self.ui["regiones"] if r["id"] == "costa_rica")
        self.assertEqual(cri["veredicto"]["estado"], "discrepan")

    def test_recta_ajustada_pasa_por_la_media(self):
        # La recta de MCO dibujada debe cruzar (media de años, media de lluvia): valida el intercepto de la interfaz.
        for r in self.ui["regiones"]:
            d = self.dom[MAPA[r["id"]]]
            media = d["tendencia"]["media_anual_mm"]
            x = (2001 + 2024) / 2
            y = r["ajustada_mco_2001"] + (r["ajustada_mco_2024"] - r["ajustada_mco_2001"]) * (x - 2001) / 23
            with self.subTest(r["id"]):
                self.assertAlmostEqual(y, media, delta=0.5)

    def test_la_interfaz_publica_los_limites_del_json(self):
        self.assertEqual(self.ui["meta"]["limites"], self.clima["metadatos"]["limites"])
        self.assertTrue(any("Costa Rica" in x for x in self.ui["meta"]["limites"]))


if __name__ == "__main__":
    unittest.main()
