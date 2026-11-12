"""Verificación independiente de los datos derivados (solo biblioteca estándar).

Recalcula con código propio, sin importar nada de scripts/datos, lo que dice data/clima.json:
series anuales desde la serie mensual, pendientes, intervalos, veredictos, ONI y geometría.
Ejecutar:  python -m unittest discover tests -v
"""
import csv
import hashlib
import json
import math
import re
import statistics
import subprocess
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "data"
ANIOS = list(range(2001, 2025))
IDS = ["caja_sicc", "NIC", "HND", "CRI", "NIC_fuera_caja"]
TOL = 1e-3


# ---------- estadística mínima ----------
def mco(x, y):
    mx, my = sum(x) / len(x), sum(y) / len(y)
    sxx = sum((a - mx) ** 2 for a in x)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sxx
    a0 = my - b * mx
    e = [c - (a0 + b * a) for a, c in zip(x, y)]
    return b, a0, e, sxx, mx


def _betacf(a, b, x):
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > 1e-300 else 1e-300)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d; d = 1 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1 + aa / c; c = c if abs(c) > 1e-300 else 1e-300
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d; d = 1 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1 + aa / c; c = c if abs(c) > 1e-300 else 1e-300
        de = d * c
        h *= de
        if abs(de - 1) < 1e-14:
            break
    return h


def _betai(a, b, x):
    if x <= 0 or x >= 1:
        return float(x >= 1)
    lb = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
    if x < (a + 1) / (a + b + 2):
        return math.exp(lb) * _betacf(a, b, x) / a
    return 1 - math.exp(lb) * _betacf(b, a, 1 - x) / b


def p_dos_colas(t, gl):
    return _betai(gl / 2, 0.5, gl / (gl + t * t))


def t_cuantil(gl, nivel=0.95):
    lo, hi = 0.0, 100.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if p_dos_colas(mid, gl) > 1 - nivel:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def intervalo_principal(x, y):
    """MCO con grados de libertad ajustados por autocorrelación lag 1 (Santer et al., 2000)."""
    n = len(x)
    b, _, e, sxx, _ = mco(x, y)
    se = math.sqrt(sum(v * v for v in e) / (n - 2) / sxx)
    r1 = sum(e[i] * e[i + 1] for i in range(n - 1)) / sum(v * v for v in e)
    n_ef = min(float(n), n * (1 - r1) / (1 + r1)) if r1 > 0 else float(n)
    gl = n_ef - 2
    se_aj = se * math.sqrt((n - 2) / gl)
    t = t_cuantil(gl)
    return b, (b - t * se_aj, b + t * se_aj), p_dos_colas(b / se_aj, gl), r1, n_ef


def intervalo_hac(x, y):
    """Newey–West (Bartlett), rezago floor(4 (n/100)^(2/9)), corrección n/(n-2), t con n-2 gl."""
    n = len(x)
    b, _, e, sxx, mx = mco(x, y)
    u = [(a - mx) * v for a, v in zip(x, e)]
    L = min(n - 2, int(math.floor(4 * (n / 100) ** (2 / 9))))
    s = sum(v * v for v in u)
    for l in range(1, L + 1):
        s += 2 * (1 - l / (L + 1)) * sum(u[i] * u[i - l] for i in range(l, n))
    se = math.sqrt(max(s / sxx ** 2 * n / (n - 2), 0.0))
    t = t_cuantil(n - 2)
    return (b - t * se, b + t * se)


def theil_sen(x, y):
    n = len(x)
    pend = sorted((y[j] - y[i]) / (x[j] - x[i]) for i in range(n) for j in range(i + 1, n))
    return statistics.median(pend), pend


def mann_kendall_tau(x, y):
    n = len(x)
    s = sum((y[j] > y[i]) - (y[j] < y[i]) for i in range(n) for j in range(i + 1, n))
    return s / (n * (n - 1) / 2)


def pearson(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    return num / math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))


def signo_ic(ic):
    return 1 if ic[0] > 0 else -1 if ic[1] < 0 else 0


# ---------- carga ----------
def cargar():
    clima = json.loads((DATOS / "clima.json").read_text(encoding="utf-8"))
    mensual = {k: {} for k in IDS}
    with (DATOS / "serie_mensual.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            mensual[r["dominio"]][(int(r["anio"]), int(r["mes"]))] = (float(r["mm"]), float(r["cobertura"]))
    with (DATOS / "fuentes" / "oni_2001_2024.csv").open(encoding="utf-8", newline="") as f:
        oni = {(int(r["anio"]), int(r["mes"])): float(r["oni"]) for r in csv.DictReader(f)}
    return clima, mensual, oni


CLIMA, MENSUAL, ONI = cargar() if (DATOS / "clima.json").is_file() else (None, None, None)


def dominio(i):
    return next(d for d in CLIMA["dominios"] if d["id"] == i)


@unittest.skipIf(CLIMA is None, "falta data/clima.json")
class Estructura(unittest.TestCase):
    def test_cinco_dominios_en_orden(self):
        self.assertEqual([d["id"] for d in CLIMA["dominios"]], IDS)

    def test_24_anios_completos_en_cada_dominio(self):
        for d in CLIMA["dominios"]:
            with self.subTest(d["id"]):
                self.assertEqual(d["anios_validos"], ANIOS)
                self.assertEqual(len(d["serie_anual_mm"]), 24)
                self.assertGreaterEqual(d["cobertura_minima"], 0.999)

    def test_periodo_declarado(self):
        p = CLIMA["metadatos"]["periodo"]
        self.assertEqual((p["inicio"], p["fin"], p["anios"]), (2001, 2024, 24))
        self.assertEqual(CLIMA["metadatos"]["producto"]["version"], "V07B")

    def test_sin_valores_no_finitos(self):
        texto = (DATOS / "clima.json").read_text(encoding="utf-8")
        self.assertNotRegex(texto, r"\b(NaN|Infinity)\b")


@unittest.skipIf(CLIMA is None, "falta data/clima.json")
class Series(unittest.TestCase):
    def test_serie_mensual_completa_y_no_negativa(self):
        for k in IDS:
            with self.subTest(k):
                self.assertEqual(sorted(MENSUAL[k]), [(a, m) for a in ANIOS for m in range(1, 13)])
                self.assertTrue(all(v[0] >= 0 for v in MENSUAL[k].values()))
                self.assertTrue(all(v[1] >= 0.999 for v in MENSUAL[k].values()))

    def test_serie_anual_es_suma_de_los_12_meses(self):
        for k in IDS:
            esperado = [sum(MENSUAL[k][(a, m)][0] for m in range(1, 13)) for a in ANIOS]
            for a, e, j in zip(ANIOS, esperado, dominio(k)["serie_anual_mm"]):
                self.assertAlmostEqual(e, j, delta=0.001, msg=f"{k} {a}")

    def test_magnitudes_plausibles(self):
        # Precipitación anual centroamericana: de cientos a pocos miles de mm.
        for d in CLIMA["dominios"]:
            self.assertTrue(all(800 < v < 5000 for v in d["serie_anual_mm"]), d["id"])
        medias = {d["id"]: d["tendencia"]["media_anual_mm"] for d in CLIMA["dominios"]}
        self.assertGreater(medias["CRI"], medias["NIC"])
        self.assertGreater(medias["NIC"], medias["HND"])


@unittest.skipIf(CLIMA is None, "falta data/clima.json")
class Tendencias(unittest.TestCase):
    def setUp(self):
        self.x = [float(a) for a in ANIOS]

    def test_pendientes_y_controles_recalculados(self):
        for k in IDS:
            d = dominio(k)
            t = d["tendencia"]
            y = d["serie_anual_mm"]
            with self.subTest(k):
                b, ic, p, r1, n_ef = intervalo_principal(self.x, y)
                self.assertAlmostEqual(b * 10, t["mm_por_decada"], delta=TOL)
                self.assertAlmostEqual(ic[0] * 10, t["ic_mm_por_decada"][0], delta=0.01)
                self.assertAlmostEqual(ic[1] * 10, t["ic_mm_por_decada"][1], delta=0.01)
                self.assertAlmostEqual(r1, t["r1_residuos"], delta=TOL)
                self.assertAlmostEqual(n_ef, t["n_efectivo"], delta=0.06)
                self.assertAlmostEqual(p, t["p_valor"], delta=2e-4)
                self.assertAlmostEqual(b * 10 / t["media_anual_mm"] * 100, t["pct_por_decada"], delta=TOL)
                hac = intervalo_hac(self.x, y)
                self.assertAlmostEqual(hac[0] * 10, t["controles"]["hac"]["ic_mm_por_decada"][0], delta=0.01)
                self.assertAlmostEqual(hac[1] * 10, t["controles"]["hac"]["ic_mm_por_decada"][1], delta=0.01)
                sen, _ = theil_sen(self.x, y)
                self.assertAlmostEqual(sen * 10, t["controles"]["theil_sen"]["mm_por_decada"], delta=TOL)
                self.assertAlmostEqual(mann_kendall_tau(self.x, y), t["controles"]["mann_kendall"]["tau"], delta=TOL)

    def test_veredicto_sigue_la_regla_del_contrato(self):
        esperado = {"caja_sicc": "evidencia_insuficiente", "NIC": "evidencia_insuficiente",
                    "HND": "evidencia_insuficiente", "CRI": "metodos_discrepan",
                    "NIC_fuera_caja": "evidencia_insuficiente"}
        for k in IDS:
            t = dominio(k)["tendencia"]
            ics = [t["ic_mm_por_decada"], t["controles"]["hac"]["ic_mm_por_decada"],
                   t["controles"]["theil_sen"]["ic_mm_por_decada"]]
            signos = {signo_ic(i) for i in ics}
            if t["p_valor"] < 0.05 and len(signos) == 1 and 0 not in signos:
                regla = "tendencia_detectada"
            elif signos == {0}:
                regla = "evidencia_insuficiente"
            else:
                regla = "metodos_discrepan"
            with self.subTest(k):
                self.assertEqual(t["veredicto"], regla)
                self.assertEqual(t["veredicto"], esperado[k])

    def test_costa_rica_depende_del_metodo(self):
        t = dominio("CRI")["tendencia"]
        self.assertEqual(t["veredicto"], "metodos_discrepan")
        self.assertLess(t["ic_mm_por_decada"][1], 0)                       # MCO excluye cero
        self.assertLess(t["controles"]["hac"]["ic_mm_por_decada"][1], 0)   # HAC excluye cero
        self.assertGreater(t["controles"]["theil_sen"]["ic_mm_por_decada"][1], 0)  # Theil–Sen no
        self.assertGreater(t["controles"]["mann_kendall"]["p_valor"], 0.05)
        self.assertIn("método", t["veredicto_texto"])

    def test_ningun_veredicto_afirma_tendencia_confirmada(self):
        self.assertFalse([d["id"] for d in CLIMA["dominios"] if d["tendencia"]["veredicto"] == "tendencia_detectada"])


@unittest.skipIf(CLIMA is None, "falta data/clima.json")
class Geometria(unittest.TestCase):
    def test_superposicion_es_aritmeticamente_coherente(self):
        area = {d["id"]: d["area_km2"] for d in CLIMA["dominios"]}
        pares = {(p["a"], p["b"]): p for p in CLIMA["superposicion"]["pares"]}
        for (a, b), p in pares.items():
            with self.subTest((a, b)):
                self.assertAlmostEqual(p["interseccion_km2"] / area[a], p["fraccion_de_a"], delta=1e-3)
                self.assertAlmostEqual(p["interseccion_km2"] / area[b], p["fraccion_de_b"], delta=1e-3)
        self.assertAlmostEqual(area["NIC"] - pares[("caja_sicc", "NIC")]["interseccion_km2"], area["NIC_fuera_caja"], delta=1.0)

    def test_areas_plausibles_frente_a_cifras_oficiales(self):
        # Superficie terrestre aproximada: NIC ~120 mil, HND ~112 mil, CRI ~51 mil km².
        area = {d["id"]: d["area_km2"] for d in CLIMA["dominios"]}
        for k, ref in (("NIC", 120_000), ("HND", 112_000), ("CRI", 51_000)):
            self.assertLess(abs(area[k] - ref) / ref, 0.03, k)

    def test_geojson_tiene_los_cinco_dominios(self):
        geo = json.loads((DATOS / "dominios.geojson").read_text(encoding="utf-8"))
        self.assertEqual(sorted(f.get("id") or f["properties"]["id"] for f in geo["features"]), sorted(IDS))


@unittest.skipIf(CLIMA is None, "falta data/clima.json")
class Oni(unittest.TestCase):
    def test_oni_completo_y_temporada(self):
        self.assertEqual(len(ONI), 288)
        temporada = [sum(ONI[a, m] for m in range(6, 12)) / 6 for a in ANIOS]
        for a, b in zip(temporada, CLIMA["oni"]["oni_temporada"]):
            self.assertAlmostEqual(a, b, delta=1e-3)

    def test_categorias_y_correlaciones(self):
        o = CLIMA["oni"]
        for v, c in zip(o["oni_temporada"], o["categoria_descriptiva"]):
            self.assertEqual(c, "el_nino" if v >= 0.5 else "la_nina" if v <= -0.5 else "neutral")
        for k in IDS:
            lluvia = [sum(MENSUAL[k][(a, m)][0] for m in range(6, 12)) for a in ANIOS]
            self.assertAlmostEqual(pearson(o["oni_temporada"], lluvia), o["correlacion_descriptiva"][k]["r"], delta=TOL)
            self.assertAlmostEqual(lluvia[0], o["lluvia_jun_nov_mm"][k][0], delta=0.001)

    def test_advertencia_de_limites_presente(self):
        adv = CLIMA["oni"]["advertencia"].lower()
        for palabra in ("descriptiva", "causalidad"):
            self.assertIn(palabra, adv)


@unittest.skipIf(CLIMA is None, "falta data/clima.json")
class Integridad(unittest.TestCase):
    def test_hashes_de_entrada(self):
        h = CLIMA["metadatos"]["integridad"]
        pares = {"dominios_geojson_sha256": "dominios.geojson", "serie_mensual_sha256": "serie_mensual.csv",
                 "oni_csv_sha256": "fuentes/oni_2001_2024.csv", "manifiesto_imerg_sha256": "fuentes/manifiesto_imerg.csv",
                 "sensibilidad_geometria_sha256": "fuentes/sensibilidad_geometria.json"}
        for clave, ruta in pares.items():
            with self.subTest(clave):
                self.assertEqual(hashlib.sha256((DATOS / ruta).read_bytes()).hexdigest(), h[clave])

    def test_manifiesto_imerg_288_archivos(self):
        with (DATOS / "fuentes" / "manifiesto_imerg.csv").open(encoding="utf-8", newline="") as f:
            filas = list(csv.DictReader(f))
        self.assertEqual(len(filas), 288)
        self.assertEqual(len({r["archivo"] for r in filas}), 288)
        esperados = {f"{a}{m:02d}01" for a in ANIOS for m in range(1, 13)}
        vistos = {re.search(r"IMERG\.(\d{8})-", r["archivo"]).group(1) for r in filas}
        self.assertEqual(vistos, esperados)
        for r in filas:
            self.assertRegex(r["sha256"], r"^[0-9a-f]{64}$")
            self.assertIn("V07B", r["archivo"])
            self.assertTrue(r["url"].startswith("https://data.gesdisc.earthdata.nasa.gov/"))


class SeparacionDeSICC(unittest.TestCase):
    PROHIBIDOS = ("*.h5", "*.hdf5", "*.HDF5", ".env", "*.pem", "*.key")

    def archivos_versionados(self):
        try:
            salida = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=True).stdout
            return [Path(p) for p in salida.splitlines()]
        except (OSError, subprocess.CalledProcessError):
            return [p.relative_to(RAIZ) for p in RAIZ.rglob("*") if ".git" not in p.parts and p.is_file()]

    def test_sin_hdf5_ni_credenciales_versionados(self):
        malos = [str(p) for p in self.archivos_versionados()
                 if any(p.match(pat) for pat in self.PROHIBIDOS) or p.name.lower().startswith("credentials")]
        self.assertEqual(malos, [])

    def test_sin_modulos_de_cultivos(self):
        malos = [str(p) for p in self.archivos_versionados() if re.search(r"cultivo|crop", str(p), re.I)]
        self.assertEqual(malos, [])

    def test_gitignore_excluye_hdf5_y_credenciales(self):
        gi = RAIZ / ".gitignore"
        self.assertTrue(gi.is_file())
        contenido = gi.read_text(encoding="utf-8")
        for patron in ("*.h5", "*.hdf5", ".env", "__pycache__/", "*.py[cod]"):
            self.assertIn(patron, contenido)

    def test_sin_archivos_pyc_ni_cmip6_sintetico(self):
        versionados = [str(p).replace("\\", "/") for p in self.archivos_versionados()]
        pyc = [p for p in versionados if p.endswith(".pyc") or "__pycache__" in p]
        self.assertEqual(pyc, [])
        self.assertNotIn("data/globales/proyecciones_cmip6_nicaragua_2025_2100.json", versionados)
        self.assertNotIn("scripts/datos/descargar_globales.py", versionados)


class ValidacionIndicesOceanicos(unittest.TestCase):
    """Verifica que TNA y AMO de NOAA PSL sirvan como validación de los índices NASA MERRA-2."""

    def test_tna_y_amo_noaa_validan_merra2(self):
        merra_csv = DATOS / "fenomenos" / "indices_oceanicos_merra2.csv"
        tna_csv = DATOS / "fuentes" / "tna_noaa_2001_2024.csv"
        amo_csv = DATOS / "fuentes" / "amo_noaa_2001_2024.csv"
        self.assertTrue(merra_csv.is_file())
        self.assertTrue(tna_csv.is_file())
        self.assertTrue(amo_csv.is_file())

        with merra_csv.open(encoding="utf-8", newline="") as f:
            merra = {(int(r["anio"]), int(r["mes"])): (float(r["nino34_anomalia"]), float(r["tna_anomalia"]), float(r["amo_anomalia"]))
                     for r in csv.DictReader(f) if 2001 <= int(r["anio"]) <= 2024}
        with tna_csv.open(encoding="utf-8", newline="") as f:
            tna_noaa = {(int(r["anio"]), int(r["mes"])): float(r["tna_anomalia_c"]) for r in csv.DictReader(f)}
        with amo_csv.open(encoding="utf-8", newline="") as f:
            amo_noaa = {(int(r["anio"]), int(r["mes"])): float(r["amo_anomalia_c"]) for r in csv.DictReader(f)}

        self.assertEqual(len(tna_noaa), 288)
        self.assertEqual(len(amo_noaa), 265)
        self.assertTrue(all(v > -90 for v in tna_noaa.values()))
        self.assertTrue(all(v > -90 for v in amo_noaa.values()))

        claves_tna = sorted(tna_noaa.keys())
        r_tna = pearson([merra[k][1] for k in claves_tna], [tna_noaa[k] for k in claves_tna])
        self.assertGreater(r_tna, 0.94)

        claves_amo = sorted(amo_noaa.keys())
        r_amo = pearson([merra[k][2] for k in claves_amo], [amo_noaa[k] for k in claves_amo])
        self.assertGreater(r_amo, 0.60)


if __name__ == "__main__":
    unittest.main()
