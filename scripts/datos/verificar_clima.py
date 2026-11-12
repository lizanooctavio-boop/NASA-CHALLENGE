"""Verifica data/clima.json sin necesitar los HDF5: estructura, integridad, 24 años completos y pendientes de referencia.

Reconstruye todo desde serie_mensual.csv y compara con el JSON publicado. Opciones:
    --diagnostico <resultado.json>   compara también con el diagnóstico original de SICC-952
    --hdf5 <carpeta>                 comprueba tamaño y SHA-256 de los HDF5 contra el manifiesto
Termina con código 1 si falla alguna comprobación.
"""
import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

from comun import ANIOS, DATOS, DOMINIOS, sha256
from generar_clima import REFERENCIA_MM_DECADA, construir

TOL = 1e-6
CLAVES_DOMINIO = {"id", "nombre", "tipo", "rol", "geometria", "bbox", "area_km2", "celdas_con_peso",
                  "cobertura_minima", "anios_validos", "serie_anual_mm", "tendencia"}
CLAVES_TENDENCIA = {"estado", "veredicto", "veredicto_texto", "nivel_confianza", "anios", "periodo", "media_anual_mm",
                    "mm_por_decada", "ic_mm_por_decada", "pct_por_decada", "ic_pct_por_decada", "p_valor",
                    "n_efectivo", "r1_residuos", "controles", "sensibilidad", "omitir_un_anio_mm_por_decada",
                    "interpretacion"}
RUTA_LOCAL = re.compile(r"\b[A-Za-z]:\\|\b[A-Za-z]:/(?!/)|/Users/|/home/|\\Users\\", re.I)  # unidad de disco, no https://


class Informe:
    def __init__(self):
        self.fallos, self.total = [], 0

    def comprobar(self, condicion, mensaje):
        self.total += 1
        if not condicion:
            self.fallos.append(mensaje)
            print("  FALLA:", mensaje)

    def seccion(self, titulo):
        print(f"\n{titulo}")


def comparar(a, b, ruta=""):
    """Lista de diferencias entre dos estructuras JSON; los números se comparan con tolerancia."""
    if isinstance(a, dict) and isinstance(b, dict):
        d = [f"{ruta}.{k}: clave ausente" for k in a.keys() ^ b.keys()]
        for k in a.keys() & b.keys():
            d += comparar(a[k], b[k], f"{ruta}.{k}")
        return d
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{ruta}: longitud {len(a)} ≠ {len(b)}"]
        return [x for i, (u, v) in enumerate(zip(a, b)) for x in comparar(u, v, f"{ruta}[{i}]")]
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return [] if math.isclose(a, b, rel_tol=TOL, abs_tol=TOL) else [f"{ruta}: {a} ≠ {b}"]
    return [] if a == b else [f"{ruta}: {a!r} ≠ {b!r}"]


def textos(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from textos(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from textos(v)


def coordenadas(g):
    if g and isinstance(g[0], (int, float)):
        yield g
    else:
        for x in g:
            yield from coordenadas(x)


def sin_nan(c):
    raise ValueError(f"constante no válida en JSON: {c}")


def verificar(directorio, diagnostico=None, hdf5=None):
    r, d = Informe(), Path(directorio)

    r.seccion("1. Archivos e integridad")
    archivos = ["clima.json", "dominios.geojson", "serie_mensual.csv", "contrato.md", "fuentes/oni_2001_2024.csv",
                "fuentes/manifiesto_imerg.csv", "fuentes/comprobaciones_extraccion.json",
                "fuentes/sensibilidad_geometria.json"]
    for a in archivos:
        r.comprobar((d / a).is_file(), f"falta data/{a}")
    if r.fallos:
        return r
    clima = json.loads((d / "clima.json").read_text(encoding="utf-8"), parse_constant=sin_nan)
    geo = json.loads((d / "dominios.geojson").read_text(encoding="utf-8"), parse_constant=sin_nan)
    integ = clima["metadatos"]["integridad"]
    for clave, ruta in [("dominios_geojson_sha256", "dominios.geojson"), ("serie_mensual_sha256", "serie_mensual.csv"),
                        ("oni_csv_sha256", "fuentes/oni_2001_2024.csv"),
                        ("manifiesto_imerg_sha256", "fuentes/manifiesto_imerg.csv"),
                        ("sensibilidad_geometria_sha256", "fuentes/sensibilidad_geometria.json")]:
        r.comprobar(integ[clave] == sha256(d / ruta), f"SHA-256 de {ruta} no coincide con metadatos.integridad")
    r.comprobar(integ["mapa_base_sha256"] == geo["fuente_mapa_sha256"], "SHA-256 del mapa base distinto en geojson y JSON")
    r.comprobar(not any(RUTA_LOCAL.search(t) for t in list(textos(clima)) + list(textos(geo))),
                "hay rutas locales dentro de los textos de clima.json o dominios.geojson")

    r.seccion("2. Estructura del contrato")
    r.comprobar(clima["esquema"] == "nasa-challenge/clima" and clima["version_esquema"] == "1.0.0", "esquema o versión inesperados")
    ids = [x["id"] for x in clima["dominios"]]
    r.comprobar(tuple(ids) == DOMINIOS, f"dominios {ids}")
    r.comprobar([f["id"] for f in geo["features"]] == list(DOMINIOS), "los features del geojson no coinciden con los dominios")
    por_id = {f["id"]: f for f in geo["features"]}
    for x in clima["dominios"]:
        k = x["id"]
        r.comprobar(CLAVES_DOMINIO <= x.keys(), f"{k}: faltan claves {CLAVES_DOMINIO - x.keys()}")
        r.comprobar(x["geometria"] == {"archivo": "dominios.geojson", "id": k}, f"{k}: referencia a geometría incorrecta")
        pts = list(coordenadas(por_id[k]["geometry"]["coordinates"]))
        caja = [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]
        r.comprobar(all(abs(u - v) < 1e-3 for u, v in zip(caja, x["bbox"])), f"{k}: bbox no coincide con la geometría")
        t = x["tendencia"]
        r.comprobar(t["estado"] == "ok" and CLAVES_TENDENCIA <= t.keys(), f"{k}: tendencia incompleta")
        r.comprobar(t["veredicto"] in {"tendencia_detectada", "evidencia_insuficiente", "metodos_discrepan"},
                    f"{k}: veredicto {t['veredicto']}")

    r.seccion("3. Veinticuatro años completos")
    for x in clima["dominios"]:
        k = x["id"]
        r.comprobar(x["anios_validos"] == ANIOS, f"{k}: años válidos {x['anios_validos'][:3]}…")
        r.comprobar(len(x["serie_anual_mm"]) == 24 and all(math.isfinite(v) and v > 0 for v in x["serie_anual_mm"]),
                    f"{k}: serie anual incompleta o no positiva")
        r.comprobar(x["cobertura_minima"] >= 0.999, f"{k}: cobertura mínima {x['cobertura_minima']}")
    with (d / "serie_mensual.csv").open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    for k in DOMINIOS:
        meses = sorted((int(f["anio"]), int(f["mes"])) for f in filas if f["dominio"] == k)
        r.comprobar(meses == [(a, m) for a in ANIOS for m in range(1, 13)], f"{k}: la serie mensual no tiene 288 meses distintos")
    for x in clima["dominios"]:
        suma = [sum(float(f["mm"]) for f in filas if f["dominio"] == x["id"] and int(f["anio"]) == a) for a in ANIOS]
        r.comprobar(np.allclose(suma, x["serie_anual_mm"], atol=5e-4), f"{x['id']}: la serie anual no es la suma de los 12 meses")

    r.seccion("4. Pendientes de referencia (mm/década)")
    for k, ref in REFERENCIA_MM_DECADA.items():
        valor = next(x for x in clima["dominios"] if x["id"] == k)["tendencia"]["mm_por_decada"]
        print(f"  {k:10s} {valor:10.3f}  (referencia {ref:.3f})")
        r.comprobar(abs(valor - ref) <= 5e-4, f"{k}: pendiente {valor} ≠ referencia {ref}")
    veredictos = {x["id"]: x["tendencia"]["veredicto"] for x in clima["dominios"]}
    r.comprobar(veredictos["CRI"] == "metodos_discrepan", "Costa Rica debe quedar como metodos_discrepan")
    r.comprobar(all(veredictos[k] == "evidencia_insuficiente" for k in ("caja_sicc", "NIC", "HND")),
                "caja, Nicaragua y Honduras deben quedar como evidencia_insuficiente")

    r.seccion("5. Regeneración desde los CSV derivados")
    dif = comparar(construir(d), clima)
    for x in dif[:10]:
        print("  dif:", x)
    r.comprobar(not dif, f"clima.json difiere de la regeneración en {len(dif)} campos")

    r.seccion("6. ONI y superposición")
    o = clima["oni"]
    r.comprobar(o["anios"] == ANIOS and len(o["oni_temporada"]) == 24 and len(o["categoria_descriptiva"]) == 24, "serie ONI incompleta")
    r.comprobar(set(o["correlacion_descriptiva"]) == set(DOMINIOS) and "descriptiva" in o["advertencia"], "correlación sin advertencia")
    sup = clima["superposicion"]
    r.comprobar(sup["pares"] == geo["superposicion"]["pares"], "superposición distinta de la del geojson")
    try:
        import shapely
        from shapely.geometry import shape
        from comun import area_km2
        g = {k: shape(por_id[k]["geometry"]) for k in DOMINIOS}
        for p in sup["pares"]:
            area = area_km2(g[p["a"]].intersection(g[p["b"]]))
            r.comprobar(abs(area - p["interseccion_km2"]) < 0.5, f"{p['a']}∩{p['b']}: {area:.1f} km² ≠ {p['interseccion_km2']}")
        for x in clima["dominios"]:
            r.comprobar(abs(area_km2(g[x["id"]]) - x["area_km2"]) < 0.5, f"{x['id']}: área distinta de la geometría")
    except ImportError:
        print("  (shapely no instalado: se omite el recálculo de áreas y superposición)")

    r.seccion("7. Manifiesto IMERG")
    with (d / "fuentes" / "manifiesto_imerg.csv").open(encoding="utf-8", newline="") as f:
        manifiesto = list(csv.DictReader(f))
    r.comprobar(len(manifiesto) == 288 and len({m["archivo"] for m in manifiesto}) == 288, "el manifiesto no lista 288 archivos distintos")
    r.comprobar(all(re.fullmatch(r"[0-9a-f]{64}", m["sha256"]) for m in manifiesto), "SHA-256 mal formados en el manifiesto")
    if hdf5:
        for m in manifiesto:
            ruta = Path(hdf5) / m["archivo"]
            r.comprobar(ruta.is_file() and ruta.stat().st_size == int(m["bytes"]) and sha256(ruta) == m["sha256"],
                        f"{m['archivo']}: ausente o distinto del manifiesto")
        print(f"  HDF5 comprobados contra el manifiesto: {len(manifiesto)}")

    if diagnostico:
        r.seccion("8. Comparación con el diagnóstico original")
        ref = json.loads(Path(diagnostico).read_text(encoding="utf-8"))
        for x in clima["dominios"]:
            s = ref["resumen"][x["id"]]
            r.comprobar(np.allclose(x["serie_anual_mm"], [s["serie_anual_mm"][str(a)] for a in ANIOS], atol=5e-4),
                        f"{x['id']}: serie anual distinta del diagnóstico")
            r.comprobar(abs(x["tendencia"]["mm_por_decada"] - s["tendencia_anual"]["mm_por_decada"]) < 5e-4 and
                        x["tendencia"]["ic_mm_por_decada"] == s["tendencia_anual"]["ic_mm_por_decada"] and
                        x["tendencia"]["veredicto"] == s["tendencia_anual"]["veredicto"], f"{x['id']}: tendencia distinta del diagnóstico")
            r.comprobar(abs(clima["oni"]["correlacion_descriptiva"][x["id"]]["r"] - s["correlacion_descriptiva_oni_jun_nov"]) < 5e-4,
                        f"{x['id']}: correlación ONI distinta del diagnóstico")
        r.comprobar(np.allclose(clima["oni"]["oni_temporada"], [ref["oni_estacional"][str(a)] for a in ANIOS], atol=5e-4),
                    "ONI estacional distinto del diagnóstico")
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datos", type=Path, default=DATOS)
    ap.add_argument("--diagnostico", type=Path)
    ap.add_argument("--hdf5", type=Path)
    a = ap.parse_args()
    informe = verificar(a.datos, a.diagnostico, a.hdf5)
    print(f"\n{informe.total - len(informe.fallos)} de {informe.total} comprobaciones correctas.")
    sys.exit(1 if informe.fallos else 0)
