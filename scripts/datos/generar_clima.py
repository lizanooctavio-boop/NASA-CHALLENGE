"""Genera data/clima.json desde los archivos derivados (sin HDF5): serie_mensual.csv, ONI y dominios.geojson.

Requiere numpy y scipy. Uso:
    python scripts/datos/generar_clima.py [--salida data/clima.json]
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np

import tendencia
from comun import ANIOS, DATOS, DOMINIOS, MESES_ONI, PAISES, sha256

VERSION_ESQUEMA = "1.0.0"
UMBRAL_ONI = 0.5
REFERENCIA_MM_DECADA = {"caja_sicc": -13.132, "NIC": -62.332, "HND": -35.005, "CRI": -201.224}


def es(x, decimales=0):
    """Número con coma decimal y signo menos tipográfico, para textos mostrados al público."""
    return f"{x:.{decimales}f}".replace(".", ",").replace("-", "−")


def leer_mensual(ruta):
    series = {k: [] for k in DOMINIOS}
    with Path(ruta).open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            series[r["dominio"]].append((int(r["anio"]), int(r["mes"]), float(r["mm"]), float(r["cobertura"])))
    return series


def leer_oni(ruta):
    with Path(ruta).open(encoding="utf-8", newline="") as f:
        return {(int(r["anio"]), int(r["mes"])): float(r["oni"]) for r in csv.DictReader(f)}


def texto_veredicto(t):
    p, lo, hi = es(t["mm_por_decada"]), es(t["ic_mm_por_decada"][0]), es(t["ic_mm_por_decada"][1])
    if t["veredicto"] == "tendencia_detectada":
        return f"Con los tres métodos se detecta una tendencia de {p} mm/década (IC 95 %: {lo} a {hi})."
    if t["veredicto"] == "evidencia_insuficiente":
        return (f"Con esta ventana y estos métodos no se detecta una tendencia ({p} mm/década; IC 95 %: {lo} a {hi}). "
                "No demuestra que no haya cambio.")
    return (f"El resultado depende del método ({p} mm/década; IC 95 % del método principal: {lo} a {hi}). "
            "No es concluyente.")


def tendencia_dominio(filas):
    anual, excluidos = tendencia.agregar_anual([(a, m, mm) for a, m, mm, _ in filas])
    t = tendencia.analizar_tendencia(anual, anual.values())
    if t["estado"] != "ok":
        return anual, excluidos, {"estado": t["estado"], "anios": t["anios"], "mensaje": t.get("mensaje", "")}
    t["veredicto_texto"] = texto_veredicto(t)
    return anual, excluidos, {
        "estado": "ok", "veredicto": t["veredicto"], "veredicto_texto": t["veredicto_texto"],
        "nivel_confianza": t["nivel"], "anios": t["anios"], "periodo": t["periodo"],
        "media_anual_mm": t["media_anual"], "mm_por_decada": t["mm_por_decada"],
        "ic_mm_por_decada": t["ic_mm_por_decada"], "pct_por_decada": t["pct_por_decada"],
        "ic_pct_por_decada": t["ic_pct_por_decada"], "p_valor": t["p_valor_principal"],
        "n_efectivo": t["n_efectivo"], "r1_residuos": t["r1_residuos"],
        "controles": {"hac": t["hac"], "theil_sen": t["theil_sen"], "mann_kendall": t["mann_kendall"]},
        "sensibilidad": t["sensibilidad"],
        "omitir_un_anio_mm_por_decada": t["omitir_un_anio_mm_por_decada"],
        "interpretacion": t["interpretacion"],
    }


METODO = {
    "agregacion_espacial": (
        "Media ponderada por área de la tasa de precipitación (mm/h) de las celdas IMERG de 0,1° que intersecan el "
        "dominio. Países: peso = área de la intersección celda–polígono en EPSG:6933 (cilíndrica de igual área). "
        "Caja de SICC-952: peso = área esférica relativa de la celda dentro del rectángulo. Las celdas parciales "
        "entran con su fracción de área."),
    "agregacion_temporal": (
        "Acumulado mensual = tasa media ponderada × horas del mes (24 × días). Acumulado anual = suma de los 12 meses "
        "del año calendario; solo se admiten años con 12 meses válidos."),
    "calidad": ("Un mes es válido si la fracción de peso con dato válido es ≥ 0,999; si no, el procesamiento se "
                "detiene. El valor de relleno -9999,9 y los negativos se excluyen sin imputar."),
    "tendencia_principal": (
        "Mínimos cuadrados sobre la serie anual; intervalo t del 95 % con grados de libertad ajustados por la "
        "autocorrelación de lag 1 de los residuos (Santer et al., 2000), sin inflar la muestra."),
    "controles": "HAC de Newey–West (Bartlett), Theil–Sen con intervalo del 95 % y tau de Kendall.",
    "regla_veredicto": (
        "tendencia_detectada si los tres intervalos excluyen cero con el mismo signo y el p-valor principal es < 0,05; "
        "evidencia_insuficiente si los tres incluyen cero; metodos_discrepan en otro caso."),
}

FUENTES = [
    {"id": "imerg_v07b", "nombre": "GPM IMERG Final Run, mensual, versión 07B (GPM_3IMERGM.07)",
     "url": "https://www.earthdata.nasa.gov/data/catalog/ges-disc-gpm-3imergm-07",
     "documentacion": "https://gpm.nasa.gov/sites/default/files/2023-07/IMERG_TechnicalDocumentation_final_230713.pdf",
     "uso": "Precipitación mensual 2001–2024 (288 archivos HDF5, listados con SHA-256 en fuentes/manifiesto_imerg.csv).",
     "licencia_o_condiciones": "Datos abiertos de NASA Earthdata/GES DISC; citar el producto y su versión."},
    {"id": "oni_noaa", "nombre": "Oceanic Niño Index (ONI), NOAA Climate Prediction Center",
     "url": "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
     "documentacion": "https://origin.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php",
     "uso": "Contexto de El Niño y La Niña (fuentes/oni_2001_2024.csv).",
     "licencia_o_condiciones": "Datos públicos de NOAA; citar la fuente."},
    {"id": "natural_earth", "nombre": "Natural Earth 1:50 m (países y lagos), simplificado en SICC-952",
     "url": "https://www.naturalearthdata.com/",
     "uso": "Máscara de referencia de Nicaragua, Honduras y Costa Rica (dominios.geojson).",
     "licencia_o_condiciones": "Dominio público."},
]

LIMITES = [
    "Estado exploratorio: resultados de un diagnóstico, no una evaluación climática formal.",
    "Veinticuatro años (2001–2024) son pocos para separar tendencia de variabilidad natural.",
    "Un intervalo que incluye cero no demuestra ausencia de cambio: indica que la ventana y el método no bastan para detectarlo.",
    "Costa Rica depende del método: dos intervalos excluyen cero y uno no; no se presenta como tendencia confirmada.",
    "Los dominios se solapan y comparten el mismo sistema climático regional: no son muestras independientes.",
    "Las geometrías son máscaras de referencia simplificadas (Natural Earth 1:50 m), no fronteras oficiales; se restaron los lagos disponibles de los países.",
    "IMERG es una estimación satelital con celdas de 0,1° (~11 km); las celdas costeras mezclan tierra y mar y se ponderan solo por área.",
    "La correlación con el ONI es descriptiva (24 puntos); no establece causalidad ni se usa para pronosticar.",
]


def construir(directorio):
    d = Path(directorio)
    geo = json.loads((d / "dominios.geojson").read_text(encoding="utf-8"))
    props = {f["id"]: f["properties"] for f in geo["features"]}
    mensual = leer_mensual(d / "serie_mensual.csv")
    oni_mes = leer_oni(d / "fuentes" / "oni_2001_2024.csv")
    comprobaciones = json.loads((d / "fuentes" / "comprobaciones_extraccion.json").read_text(encoding="utf-8"))
    sens = json.loads((d / "fuentes" / "sensibilidad_geometria.json").read_text(encoding="utf-8"))

    oni_temp = [float(np.mean([oni_mes[a, m] for m in MESES_ONI])) for a in ANIOS]
    categorias = ["el_nino" if v >= UMBRAL_ONI else "la_nina" if v <= -UMBRAL_ONI else "neutral" for v in oni_temp]
    lluvia_temp, correlacion, dominios = {}, {}, []
    for k in DOMINIOS:
        filas = mensual[k]
        if sorted((a, m) for a, m, _, _ in filas) != [(a, m) for a in ANIOS for m in range(1, 13)]:
            raise ValueError(f"{k}: la serie mensual no cubre 2001–2024 sin huecos ni duplicados.")
        anual, excluidos, t = tendencia_dominio(filas)
        if excluidos or list(anual) != ANIOS:
            raise ValueError(f"{k}: años excluidos {excluidos}")
        lluvia_temp[k] = [sum(mm for a_, m, mm, _ in filas if a_ == a and m in MESES_ONI) for a in ANIOS]
        correlacion[k] = {"r": round(float(np.corrcoef(oni_temp, lluvia_temp[k])[0, 1]), 3), "n": len(ANIOS)}
        p = props[k]
        dominios.append({
            "id": k, "nombre": p["nombre"], "tipo": p["tipo"], "rol": p["rol"],
            "geometria": {"archivo": "dominios.geojson", "id": k}, "bbox": p["bbox"], "area_km2": p["area_km2"],
            "celdas_con_peso": comprobaciones["celdas_con_peso"][k],
            "cobertura_minima": round(min(c for _, _, _, c in filas), 6),
            "anios_validos": list(anual), "serie_anual_mm": [round(v, 3) for v in anual.values()],
            "tendencia": t})

    metodo = dict(METODO)
    metodo["comprobacion_pesos_caja"] = (
        "Con pesos de igual área (EPSG:6933) en lugar de esféricos, el acumulado anual de la caja cambia como máximo "
        f"{comprobaciones['caja_esferica_vs_6933']['max_dif_anual_mm']:.3f} mm "
        f"({comprobaciones['caja_esferica_vs_6933']['max_dif_anual_relativa']:.1e} en términos relativos).")
    rangos = {k: [min(e[k]["mm_por_decada"] for e in sens["escenarios"].values()),
                  max(e[k]["mm_por_decada"] for e in sens["escenarios"].values())] for k in (*PAISES, "NIC_fuera_caja")}
    metodo["sensibilidad_geometria"] = {
        "descripcion": (f"Pendientes recalculadas con el contorno de cada país dilatado y erosionado {es(sens['delta_grados'], 2)}° "
                        "(≈ 5,5 km). Es una prueba de sensibilidad del contorno, no una incertidumbre formal de la geometría."),
        "delta_grados": sens["delta_grados"], "rango_mm_por_decada": rangos,
        "veredictos_cambian": any(e[k]["veredicto"] != sens["escenarios"]["referencia"][k]["veredicto"]
                                  for e in sens["escenarios"].values() for k in rangos)}
    return {
        "esquema": "nasa-challenge/clima", "version_esquema": VERSION_ESQUEMA, "estado": "exploratorio",
        "metadatos": {
            "titulo": "Precipitación anual en Nicaragua y su contexto regional, 2001–2024",
            "producto": {"nombre": "GPM IMERG Final Run, mensual", "id": "GPM_3IMERGM", "version": "V07B",
                         "variable": "precipitation", "unidad_origen": "mm/hr", "proveedor": "NASA GES DISC"},
            "periodo": {"inicio": ANIOS[0], "fin": ANIOS[-1], "anios": len(ANIOS)},
            "unidad_serie": "mm/año", "unidad_pendiente": "mm/década",
            "resolucion": {"espacial_grados": 0.1, "temporal_origen": "mensual",
                           "temporal_salida": "anual (año calendario)"},
            "metodo": metodo, "fuentes": FUENTES,
            "integridad": {"mapa_base_sha256": geo["fuente_mapa_sha256"],
                           "dominios_geojson_sha256": sha256(d / "dominios.geojson"),
                           "serie_mensual_sha256": sha256(d / "serie_mensual.csv"),
                           "oni_csv_sha256": sha256(d / "fuentes" / "oni_2001_2024.csv"),
                           "manifiesto_imerg_sha256": sha256(d / "fuentes" / "manifiesto_imerg.csv"),
                           "sensibilidad_geometria_sha256": sha256(d / "fuentes" / "sensibilidad_geometria.json")},
            "limites": LIMITES},
        "dominios": dominios,
        "superposicion": {
            "nota": ("Los dominios no son muestras independientes: caja_sicc se solapa con Nicaragua y con el norte de "
                     "Costa Rica, y NIC_fuera_caja es el complemento de caja_sicc dentro de Nicaragua. Aunque los tres "
                     "países no comparten área, sí comparten el mismo sistema climático regional."),
            **geo["superposicion"]},
        "oni": {
            "fuente": FUENTES[1]["url"],
            "definicion_temporal": (
                "ONI: anomalía de la temperatura superficial del mar en la región Niño 3.4 (5° N–5° S, 120°–170° O) "
                "en medias móviles de tres meses. Cada trimestre se asigna a su mes central (DJF = enero … "
                "OND = noviembre, NDJ = diciembre). La temporada es la media de los seis valores de junio a noviembre "
                "(trimestres MJJ a OND)."),
            "temporada": {"nombre": "junio–noviembre", "meses": list(MESES_ONI), "agregacion": "media de los seis valores mensuales"},
            "anios": ANIOS, "oni_temporada": [round(v, 3) for v in oni_temp],
            "categoria_descriptiva": categorias, "umbral_categoria": UMBRAL_ONI,
            "nota_categoria": ("Etiqueta de la media estacional (≥ +0,5 El Niño, ≤ −0,5 La Niña); no es el criterio "
                               "oficial de NOAA, que exige cinco trimestres consecutivos."),
            "lluvia_jun_nov_mm": {k: [round(v, 3) for v in lluvia_temp[k]] for k in DOMINIOS},
            "correlacion_descriptiva": correlacion,
            "advertencia": ("La correlación es descriptiva: resume 24 temporadas, no establece causalidad, no se acompaña de "
                            "valor p y los dominios se solapan. La lluvia centroamericana también responde al Atlántico, al "
                            "Caribe y a la variabilidad local.")},
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--datos", type=Path, default=DATOS)
    ap.add_argument("--salida", type=Path, default=DATOS / "clima.json")
    a = ap.parse_args()
    r = construir(a.datos)
    a.salida.write_text(json.dumps(r, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    for d in r["dominios"]:
        t = d["tendencia"]
        print(f"{d['id']:15s} {len(d['anios_validos'])} años  {t['mm_por_decada']:9.3f} mm/década  "
              f"IC [{t['ic_mm_por_decada'][0]:.3f}; {t['ic_mm_por_decada'][1]:.3f}]  {t['veredicto']}")
