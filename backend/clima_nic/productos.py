"""Genera data/fenomenos_nicaragua.json desde los derivados versionados de data/fenomenos/ (sin red).

Organiza la respuesta a las cuatro preguntas del reto para cada región y variable:
    qué cambia      → variable (con definición sencilla)
    dónde           → región y mapa de celdas con control FDR
    cuánto          → pendiente de Sen por década con IC 95 % (y mínimos cuadrados como referencia)
    significativo   → Mann–Kendall modificado, intervalos de tres métodos y veredicto; Pettitt y regresión con
                      control por ENOS (obligatorio en lluvia) y por TNA/AMO/PDO/CLLJ como moduladores
y separa explícitamente la detección de tendencias del pronóstico estacional y de los escenarios CMIP6.
"""
import csv
import json
import math
from datetime import date
from pathlib import Path

import numpy as np

from . import proyecciones as pr
from .estadistica import indicadores as ind
from .estadistica import modelo_estacional as me
from .estadistica import tendencia_robusta as tr
from .estadistica.fdr import benjamini_hochberg
from .regiones import NOMBRES, ORDEN
from .rutas import DATOS, FENOMENOS, REGIONES_GEOJSON, sha256

VERSION = "1.0.0"
BASE = (1991, 2020)
JUN_NOV = tuple(range(6, 12))
TEMPORADAS = {"jun_nov": JUN_NOV, "mjj": (5, 6, 7), "jas": (7, 8, 9), "son": (9, 10, 11)}
MODULADORES = ("nino34", "tna", "amo", "pdo", "cllj")

# id: (unidad, fenómeno, nombre, definición sencilla para el público)
VARIABLES = {
    "lluvia_anual": ("mm", "lluvia", "Lluvia anual", "Toda la lluvia caída en el año."),
    "lluvia_jun_nov": ("mm", "lluvia", "Lluvia de junio a noviembre", "La lluvia de la estación lluviosa principal."),
    "lluvia_anual_imerg": ("mm", "lluvia", "Lluvia anual (satélite IMERG)", "Lluvia anual estimada por satélites GPM; referencia independiente del reanálisis."),
    "lluvia_jun_nov_imerg": ("mm", "lluvia", "Lluvia de junio a noviembre (satélite IMERG)", "Lluvia de la estación lluviosa estimada por satélites GPM."),
    "rx1day": ("mm", "extremos_lluvia", "Lluvia máxima en un día", "El aguacero diario más fuerte del año."),
    "rx5day": ("mm", "extremos_lluvia", "Lluvia máxima en 5 días", "La mayor lluvia acumulada en cinco días seguidos; se asocia a inundaciones y a ciclones."),
    "r95p": ("mm", "extremos_lluvia", "Lluvia de días muy húmedos (R95p)", "Lluvia caída en los días más lluviosos (por encima del percentil 95 de 1991–2020)."),
    "r10mm": ("días", "extremos_lluvia", "Días con lluvia fuerte (≥ 10 mm)", "Cuántos días del año llovió al menos 10 mm."),
    "r20mm": ("días", "extremos_lluvia", "Días con lluvia muy fuerte (≥ 20 mm)", "Cuántos días del año llovió al menos 20 mm."),
    "sdii": ("mm/día", "extremos_lluvia", "Intensidad de la lluvia", "Lluvia media de los días en que llovió."),
    "cdd": ("días", "sequia", "Racha seca más larga", "Máximo de días seguidos con menos de 1 mm."),
    "cdd_may_oct": ("días", "sequia", "Veranillo más largo (mayo–octubre)", "Racha seca más larga dentro de la estación lluviosa."),
    "cwd": ("días", "extremos_lluvia", "Racha húmeda más larga", "Máximo de días seguidos con lluvia."),
    "t2m_media": ("°C", "temperatura", "Temperatura media", "Temperatura del aire a 2 m, promedio del año."),
    "tmax_media": ("°C", "temperatura", "Temperatura máxima media", "Promedio de las temperaturas más altas de cada día."),
    "tmin_media": ("°C", "temperatura", "Temperatura mínima media", "Promedio de las temperaturas más bajas de cada día."),
    "txx": ("°C", "calor_extremo", "Día más caluroso", "La temperatura máxima más alta del año."),
    "tnn": ("°C", "temperatura", "Noche más fresca", "La temperatura mínima más baja del año."),
    "tx90p": ("% de días", "calor_extremo", "Días cálidos", "Porcentaje de días más calurosos que el 90 % de los días de 1991–2020."),
    "tn90p": ("% de días", "calor_extremo", "Noches cálidas", "Porcentaje de noches más cálidas que el 90 % de las de 1991–2020."),
    "dtr": ("°C", "temperatura", "Amplitud térmica diaria", "Diferencia media entre la máxima y la mínima del día."),
    "gdd10": ("°C·día", "agroclima", "Grados-día (base 10 °C)", "Calor acumulado útil para el crecimiento de cultivos."),
    "temperatura_gistemp": ("°C", "temperatura", "Anomalía de temperatura (GISTEMP)", "Anomalía observada con estaciones (NASA GISS) respecto de 1951–1980."),
    "humedad_relativa": ("%", "humedad", "Humedad relativa", "Cuánto vapor de agua tiene el aire respecto del máximo posible."),
    "radiacion_solar": ("MJ m⁻² día⁻¹", "agroclima", "Radiación solar", "Energía del sol que llega al suelo (desde 1984)."),
    "viento_2m": ("m/s", "agroclima", "Viento a 2 m", "Velocidad media del viento cerca del suelo."),
    "eto_penman_monteith": ("mm", "agroclima", "Evapotranspiración de referencia (FAO-56)", "Agua que pierde un pasto de referencia bien regado por evaporación y transpiración (desde 1984)."),
    "eto_hargreaves": ("mm", "agroclima", "Evapotranspiración (Hargreaves)", "Estimación de la ETo solo con temperatura; serie desde 1981."),
    "balance_hidrico": ("mm", "sequia", "Balance hídrico P − ETo", "Lluvia menos evapotranspiración (Penman–Monteith); negativo = déficit."),
    "humedad_suelo_raiz": ("0–1", "humedad_suelo", "Humedad del suelo (raíces)", "Qué tan húmeda está la capa donde crecen las raíces (modelo MERRA-2)."),
    "humedad_suelo_jul_ago": ("0–1", "humedad_suelo", "Humedad del suelo en canícula", "Humedad de la zona radicular en julio y agosto."),
    "spei6_nov": ("adimensional", "sequia", "SPEI de junio–noviembre", "Índice de sequía de la estación lluviosa: < −1 es sequía moderada o peor."),
    "spei12_min": ("adimensional", "sequia", "SPEI-12 mínimo del año", "El momento más seco del año en la escala de 12 meses."),
    "meses_sequia_spei3": ("meses", "sequia", "Meses en sequía (SPEI-3 ≤ −1)", "Cuántos meses del año hubo sequía moderada o peor."),
    "canicula_intensidad": ("fracción", "canicula", "Intensidad de la canícula", "Cuánto baja la lluvia a mitad del verano respecto de sus dos máximos."),
    "canicula_duracion": ("días", "canicula", "Duración de la canícula", "Días entre el inicio y el fin de la canícula (0 si no se detecta)."),
    "canicula_inicio": ("día del año", "canicula", "Inicio de la canícula", "Día del año en que empieza la canícula detectada."),
    "canicula_lluvia_15jul_15ago": ("mm", "canicula", "Lluvia del 15 de julio al 15 de agosto", "Ventana fija de la canícula."),
    "canicula_racha_seca": ("días", "canicula", "Racha seca en canícula", "Días seguidos sin lluvia entre el 15 de julio y el 15 de agosto."),
    "ndvi": ("adimensional", "vegetacion", "Verdor de la vegetación (NDVI)", "Índice de vegetación de MODIS en dos sitios por región; también cambia con el uso del suelo."),
}
PRECIP = {k for k, v in VARIABLES.items() if v[1] in ("lluvia", "extremos_lluvia", "sequia", "canicula", "humedad",
                                                      "humedad_suelo", "vegetacion")} | {"balance_hidrico"}
CELDAS_MAPA = {"prcptot": "mm", "rx1day": "mm", "r95p": "mm", "tmax_media": "°C", "tmin_media": "°C", "tx90p": "% de días"}


# ---------------------------------------------------------------- lectura

def _f(x):
    return float(x) if x not in ("", None) else math.nan


def leer_diario(ruta=FENOMENOS / "serie_diaria_power.csv"):
    filas = {}
    with Path(ruta).open(encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        cols = [c for c in lector.fieldnames if c not in ("region", "fecha")]
        for r in lector:
            d = filas.setdefault(r["region"], {"fecha": [], **{c: [] for c in cols}})
            d["fecha"].append(r["fecha"])
            for c in cols:
                d[c].append(_f(r[c]))
    return {k: {c: (np.array(v, "datetime64[D]") if c == "fecha" else np.array(v)) for c, v in d.items()}
            for k, d in filas.items()}


def leer_largo(ruta, clave="region"):
    out = {}
    with Path(ruta).open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            out.setdefault(r[clave], {}).setdefault(r["indice"], {})[int(r["anio"])] = _f(r["valor"])
    return out


def leer_oceano(ruta=FENOMENOS / "indices_oceanicos_merra2.csv"):
    with Path(ruta).open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    claves = {"nino34": "nino34_anomalia", "tna": "tna_anomalia", "amo": "amo_anomalia", "pdo": "pdo", "cllj": "cllj_u10m"}
    out = {k: {} for k in claves}
    for r in filas:
        a, m = int(r["anio"]), int(r["mes"])
        for k, c in claves.items():
            out[k][(a, m)] = _f(r[c])
    # el CLLJ se usa como anomalía respecto de 1991–2020
    clim = {m: np.mean([v for (a, mm), v in out["cllj"].items() if mm == m and BASE[0] <= a <= BASE[1]]) for m in range(1, 13)}
    out["cllj"] = {(a, m): v - clim[m] for (a, m), v in out["cllj"].items()}
    return out


def media_meses(indice, anio, meses):
    v = [indice.get((anio, m)) for m in meses]
    return float(np.mean(v)) if all(x is not None and np.isfinite(x) for x in v) else math.nan


# ---------------------------------------------------------------- series anuales por región

def series_region(d, celdas, region, lat_media):
    f = d["fecha"]
    anio, mes, doy = ind.descomponer(f)
    anios = [int(a) for a in np.unique(anio) if (anio == a).sum() >= 365]
    s = {}

    def anual(col, meses=range(1, 13), como="suma", minimo=None):
        out = {}
        for a in anios:
            sel = (anio == a) & np.isin(mes, list(meses))
            x = d[col][sel]
            if np.all(np.isfinite(x)):
                out[a] = float(x.sum() if como == "suma" else x.mean())
        return out

    s["lluvia_anual"] = anual("prectotcorr")
    s["lluvia_jun_nov"] = anual("prectotcorr", JUN_NOV)
    s["humedad_relativa"] = anual("rh2m", como="media")
    s["radiacion_solar"] = anual("allsky_sfc_sw_dwn", como="media")
    s["viento_2m"] = anual("ws2m", como="media")
    s["humedad_suelo_raiz"] = anual("gwetroot", como="media")
    s["humedad_suelo_jul_ago"] = anual("gwetroot", (7, 8), como="media")
    s["eto_penman_monteith"] = anual("eto_pm_mm")
    eto_h = ind.etp_hargreaves(d["t2m"], d["t2m_max"], d["t2m_min"], lat_media, doy)
    s["eto_hargreaves"] = {a: float(eto_h[anio == a].sum()) for a in anios}
    s["balance_hidrico"] = {a: s["lluvia_anual"][a] - s["eto_penman_monteith"][a]
                            for a in anios if a in s["eto_penman_monteith"] and a in s["lluvia_anual"]}
    for k in ("rx1day", "rx5day", "r95p", "r10mm", "r20mm", "sdii", "cdd", "cdd_may_oct", "cwd", "t2m_media",
              "tmax_media", "tmin_media", "txx", "tnn", "tx90p", "tn90p", "dtr", "gdd10"):
        s[k] = {a: v for a, v in celdas.get(k, {}).items() if a in anios and np.isfinite(v)}

    # sequía mensual (base 1991–2020); SPEI con ETo de Hargreaves para cubrir 1981–2024 con una sola fórmula
    ma, mm_, p_m = ind.mensual_desde_diario(f, d["prectotcorr"])
    _, _, e_m = ind.mensual_desde_diario(f, eto_h)
    base = (ma >= BASE[0]) & (ma <= BASE[1])
    sequia = {"anios": ma.tolist(), "meses": mm_.tolist(), "eto": "Hargreaves (FAO-56 ec. 52)"}
    for nombre, fn, x, esc in (("spi3", ind.spi, p_m, 3), ("spi12", ind.spi, p_m, 12), ("spei3", ind.spei, p_m - e_m, 3),
                               ("spei6", ind.spei, p_m - e_m, 6), ("spei12", ind.spei, p_m - e_m, 12)):
        v = fn(x, mm_, esc, base)
        sequia[nombre] = [None if not np.isfinite(z) else round(float(z), 3) for z in v]
    sp12, sp3, sp6 = (np.array([np.nan if z is None else z for z in sequia[k]]) for k in ("spei12", "spei3", "spei6"))
    s["spei6_nov"] = {a: float(sp6[(ma == a) & (mm_ == 11)][0]) for a in anios if np.isfinite(sp6[(ma == a) & (mm_ == 11)]).all()}
    s["spei12_min"] = {a: float(np.nanmin(sp12[ma == a])) for a in anios if np.isfinite(sp12[ma == a]).any()}
    s["meses_sequia_spei3"] = {a: float(np.sum(sp3[ma == a] <= -1)) for a in anios}
    orden = np.argsort(np.where(np.isfinite(sp12), sp12, np.inf))
    peores, usados = [], []
    for i in orden:
        if not np.isfinite(sp12[i]) or len(peores) == 5:
            break
        if any(abs(i - j) < 12 for j in usados):
            continue
        usados.append(i)
        peores.append({"anio": int(ma[i]), "mes": int(mm_[i]), "spei12": round(float(sp12[i]), 2),
                       "categoria": ind.categoria_sequia(float(sp12[i]))})
    sequia["peores_episodios_spei12"] = peores

    can = ind.canicula(f, d["prectotcorr"], range(BASE[0], BASE[1] + 1))
    tabla = {"anios": anios, "detectada": [], "inicio_doy": [], "fin_doy": [], "duracion_dias": [], "deficit_mm": [],
             "intensidad": [], "lluvia_15jul_15ago_mm": [], "racha_seca_15jul_15ago": []}
    for a in anios:
        o, w = can[a]["objetiva"], can[a]["ventana_fija"]
        tabla["detectada"].append(bool(o["detectada"]))
        for c in ("inicio_doy", "fin_doy", "duracion_dias", "deficit_mm"):
            tabla[c].append(round(float(o[c]), 2) if o["detectada"] else None)
        tabla["intensidad"].append(round(float(o["intensidad"]), 4) if "intensidad" in o else None)
        tabla["lluvia_15jul_15ago_mm"].append(round(w["lluvia_mm"], 1))
        tabla["racha_seca_15jul_15ago"].append(w["racha_seca_max_dias"])
    s["canicula_intensidad"] = {a: v for a, v in zip(anios, tabla["intensidad"]) if v is not None}
    s["canicula_duracion"] = {a: float(v or 0) for a, v in zip(anios, tabla["duracion_dias"])}
    s["canicula_inicio"] = {a: v for a, v in zip(anios, tabla["inicio_doy"]) if v is not None}
    s["canicula_lluvia_15jul_15ago"] = dict(zip(anios, tabla["lluvia_15jul_15ago_mm"]))
    s["canicula_racha_seca"] = {a: float(v) for a, v in zip(anios, tabla["racha_seca_15jul_15ago"])}
    det = [v for v in tabla["duracion_dias"] if v is not None]
    tabla["definicion"] = ("Objetiva: media móvil de 31 días; máximos entre el 15 de mayo y el 15 de julio y entre el 1 de "
                           "agosto y el 31 de octubre; hay canícula si la lluvia mínima entre ambos es al menos 15 % menor que "
                           "su promedio; inicio y fin donde la serie cruza el punto medio entre el mínimo y los máximos. "
                           "Ventana fija: 15 de julio a 15 de agosto. Definición fija y publicada para que sea comparable.")
    tabla["resumen"] = {"anios_con_canicula": int(sum(tabla["detectada"])), "anios": len(anios),
                        "duracion_mediana_dias": float(np.median(det)) if det else None,
                        "inicio_mediano_doy": float(np.median([v for v in tabla["inicio_doy"] if v is not None])) if det else None}
    temporadas = {t: anual("prectotcorr", m) for t, m in TEMPORADAS.items()}
    return s, sequia, tabla, temporadas


# ---------------------------------------------------------------- análisis de una variable

def analizar_variable(nombre, serie, indices, region, independiente=None):
    unidad, fenomeno, titulo, definicion = VARIABLES[nombre]
    anios = sorted(a for a, v in serie.items() if v is not None and np.isfinite(v))
    valores = [float(serie[a]) for a in anios]
    precip = nombre in PRECIP
    ventana = JUN_NOV if precip else tuple(range(1, 13))
    cov = {}
    for k in MODULADORES:
        c = [media_meses(indices[k], a, ventana) for a in anios]
        if all(np.isfinite(c)):
            cov[k] = c
    out = {"titulo": titulo, "definicion": definicion, "unidad": unidad, "fenomeno": fenomeno,
           "anios": anios, "valores": [round(v, 4) for v in valores]}
    if len(anios) < 10:
        out["tendencia"] = {"veredicto": "datos_insuficientes", "anios": len(anios)}
        return out
    t = tr.analizar(anios, valores, unidad, covariables={"nino34": cov["nino34"]} if "nino34" in cov else None)
    if len(cov) > 1:
        t["controlada_por_todos_los_moduladores"] = tr.regresion_controlada(anios, valores, cov)
    t["covariable_enos"] = ("Niño 3.4 medio de junio–noviembre (obligatorio en variables de lluvia)" if precip
                            else "Niño 3.4 medio anual")
    out["tendencia"] = t
    out["correlacion_moduladores"] = {k: round(float(np.corrcoef(c, valores)[0, 1]), 3) for k, c in cov.items()}
    advert = []
    pt = t.get("pettitt", {})
    if pt.get("p_valor", 1) < 0.01:
        sd = float(np.std(valores, ddof=1))
        if sd > 0 and abs(pt["salto"]) > sd:
            advert.append(f"Cambio abrupto en {pt['anio_cambio']} (Pettitt p = {pt['p_valor']}, salto de "
                          f"{abs(pt['salto']) / sd:.1f} desviaciones típicas): puede ser un artefacto del producto (cambios "
                          "en las observaciones que asimila el reanálisis o en los sensores) y no solo clima. Contrastar con "
                          "una fuente independiente antes de interpretarlo como tendencia.")
    if independiente:
        advert.append(independiente)
    out["advertencias"] = advert
    sen = t.get("theil_sen", {})
    mmk = t.get("mann_kendall_modificado", {})
    out["respuesta_reto"] = {
        "que": titulo, "donde": NOMBRES.get(region, region),
        "cuanto": {"sen_por_decada": sen.get("por_decada"), "ic95": sen.get("ic_por_decada"), "unidad": f"{unidad}/década"},
        "significativo": {"mann_kendall_modificado_p": mmk.get("p_valor"), "veredicto": t["veredicto"],
                          "con_control_enos": (t.get("controlada_por_indices") or {}).get("ic_por_decada")},
    }
    return out


# ---------------------------------------------------------------- mapas con FDR

def mapa_celdas(ruta=FENOMENOS / "indices_anuales_celdas.csv", q=0.10):
    datos = {}
    with Path(ruta).open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            datos.setdefault((float(r["lat"]), float(r["lon"])), []).append(r)
    mapas = {}
    for var, unidad in CELDAS_MAPA.items():
        celdas = []
        for (lat, lon), filas in sorted(datos.items()):
            pares = sorted((int(r["anio"]), _f(r[var])) for r in filas if np.isfinite(_f(r[var])))
            if len(pares) < 20:
                continue
            a, v = zip(*pares)
            mk = tr.mann_kendall_modificado(v)
            sen = tr.theil_sen(a, v)
            celdas.append({"lat": lat, "lon": lon, "sen_por_decada": sen["por_decada"], "ic95": sen["ic_por_decada"],
                           "p_mmk": mk["p_valor"]})
        sig, umbral = benjamini_hochberg([c["p_mmk"] for c in celdas], q)
        for c, s in zip(celdas, sig):
            c["significativo_fdr"] = s
            c["significativo_sin_fdr"] = c["p_mmk"] < q  # mismo nivel nominal, sin corrección
        mapas[var] = {"unidad_pendiente": f"{unidad}/década", "q_fdr": q, "umbral_p": umbral, "celdas": celdas,
                      "n_significativas_fdr": int(sum(sig)), "n_significativas_sin_fdr": int(sum(c["significativo_sin_fdr"] for c in celdas))}
    return mapas


# ---------------------------------------------------------------- modelo estacional

def modelo_estacional(objetivos, indices, permutaciones, imerg=None):
    """objetivos: {region: {temporada: {anio: mm}}}."""
    meses_inicio = {"jun_nov": 6, "mjj": 5, "jas": 7, "son": 9}
    grilla = []
    for region, temps in objetivos.items():
        for temp, serie in temps.items():
            for h in range(0, 7):
                for conjunto in (("nino34",), ("nino34", "tna")):
                    preds = {k: me.serie_predictor(indices[k], sorted(serie), meses_inicio[temp], h) for k in conjunto}
                    anios = sorted(set(serie).intersection(*[set(p) for p in preds.values()]))
                    if len(anios) < 15:
                        continue
                    y = [serie[a] for a in anios]
                    X = np.column_stack([[preds[k][a] for a in anios] for k in conjunto])
                    r = me.evaluar(y, X, permutaciones=permutaciones, bloques=(1,))
                    grilla.append({"region": region, "temporada": temp, "horizonte_meses": h,
                                   "ventana_predictor": me.nombre_ventana(me.ventana_predictor(meses_inicio[temp], h)),
                                   "predictores": list(conjunto), "n": len(anios),
                                   "msess": round(r["bloque_1"]["msess"], 4), "r": round(r["bloque_1"]["r"], 3),
                                   "aciertos_tercil": round(r["bloque_1"]["aciertos_tercil"], 3),
                                   "p_permutacion": round(r["p_permutacion_msess"], 4)})
    sig, umbral = benjamini_hochberg([g["p_permutacion"] for g in grilla], 0.10)
    for g, s in zip(grilla, sig):
        g["habil_tras_fdr"] = bool(s and g["msess"] > 0)

    # experimentos principales (más permutaciones) y controles de tendencia
    principales = []
    for region, temps in objetivos.items():
        serie = temps["jun_nov"]
        anios = sorted(serie)
        y = np.array([serie[a] for a in anios])
        n34 = me.serie_predictor(indices["nino34"], anios, 6, 0)
        tna = me.serie_predictor(indices["tna"], anios, 6, 0)
        anios_p = [a for a in anios if a in n34 and a in tna]
        yy = np.array([serie[a] for a in anios_p])
        x1 = np.array([n34[a] for a in anios_p])
        x2 = np.column_stack([x1, [tna[a] for a in anios_p]])
        tiempo = np.array(anios_p, float)
        for nombre, X, y_obj in (("nino34_mam", x1, yy), ("nino34_tna_mam", x2, yy), ("solo_tendencia_lineal", tiempo, yy),
                                 ("nino34_tna_mam_sin_tendencia", _sin_tendencia(x2, tiempo), _sin_tendencia(yy, tiempo))):
            r = me.resumen(me.evaluar(y_obj, X, permutaciones=permutaciones * 5))
            principales.append({"region": region, "temporada": "jun_nov", "modelo": nombre, "n": len(anios_p),
                                "periodo": [anios_p[0], anios_p[-1]], **r})
    if imerg:
        for region, serie in imerg.items():
            anios = sorted(serie)
            n34 = me.serie_predictor(indices["nino34"], anios, 6, 0)
            tna = me.serie_predictor(indices["tna"], anios, 6, 0)
            ap = [a for a in anios if a in n34 and a in tna]
            yy = np.array([serie[a] for a in ap])
            for nombre, X in (("nino34_mam", np.array([n34[a] for a in ap])),
                              ("nino34_tna_mam", np.column_stack([[n34[a] for a in ap], [tna[a] for a in ap]]))):
                r = me.resumen(me.evaluar(yy, X, permutaciones=permutaciones * 5))
                principales.append({"region": f"{region} (IMERG)", "temporada": "jun_nov", "modelo": nombre, "n": len(ap),
                                    "periodo": [ap[0], ap[-1]], **r})
    return {"tipo": "pronostico", "grilla_horizontes": grilla, "umbral_fdr_p": umbral, "principales": principales,
            "lectura": ("Pronóstico estadístico de totales de temporada, distinto de la detección de tendencias. MSESS > 0: "
                        "mejor que la climatología fuera de muestra (validación dejando un año fuera). p_permutacion: "
                        "probabilidad de obtener esa habilidad por azar. Con decenas de combinaciones se aplica FDR "
                        "(q = 0,10) y se informan todas, sin elegir la mejor. Los modelos con TNA se comparan con una "
                        "versión sin tendencia: si la habilidad desaparece al quitar la tendencia, el TNA solo aporta la "
                        "tendencia compartida (que en MERRA-2 puede ser parcialmente artificial).")}


def _sin_tendencia(v, t):
    v = np.asarray(v, float)
    t = np.asarray(t, float)
    A = np.column_stack([np.ones(len(t)), t - t.mean()])
    if v.ndim == 1:
        return v - A @ np.linalg.lstsq(A, v, rcond=None)[0]
    return np.column_stack([c - A @ np.linalg.lstsq(A, c, rcond=None)[0] for c in v.T])


# ---------------------------------------------------------------- construcción

def construir(permutaciones=200):
    diario = leer_diario()
    celdas = leer_largo(FENOMENOS / "indices_anuales_regiones.csv")
    indices = leer_oceano()
    with (FENOMENOS / "celdas_power.csv").open(encoding="utf-8", newline="") as f:
        filas_c = list(csv.DictReader(f))
    lat_media = {}
    for k in ORDEN:
        w = np.array([float(r[f"peso_{k}_km2"]) for r in filas_c])
        lat_media[k] = float((w * np.array([float(r["lat"]) for r in filas_c])).sum() / w.sum())

    # validación del Niño 3.4 MERRA-2 contra el ONI de NOAA (solo comparación)
    oni = {}
    with (DATOS / "fuentes" / "oni_2001_2024.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            oni[int(r["anio"]), int(r["mes"])] = float(r["oni"])
    claves = sorted(indices["nino34"])
    n34 = np.array([indices["nino34"][k] for k in claves])
    n34_3 = np.convolve(np.pad(n34, 1, mode="edge"), np.ones(3) / 3, "valid")
    pares = np.array([(n34_3[i], oni[k]) for i, k in enumerate(claves) if k in oni])
    cat = lambda v: np.where(v >= 0.5, 1, np.where(v <= -0.5, -1, 0))  # noqa: E731
    validacion_enos = {"n_meses": len(pares), "r": float(np.corrcoef(pares[:, 0], pares[:, 1])[0, 1]),
                       "rmse_c": float(np.sqrt(np.mean((pares[:, 0] - pares[:, 1]) ** 2))),
                       "acuerdo_categoria": float(np.mean(cat(pares[:, 0]) == cat(pares[:, 1])))}

    # IMERG (contrato 1.0.0) para NIC y caja
    imerg_m = {}
    with (DATOS / "serie_mensual.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            imerg_m.setdefault(r["dominio"], {})[(int(r["anio"]), int(r["mes"]))] = float(r["mm"])
    imerg_anual = {k: {a: sum(v[(a, m)] for m in range(1, 13)) for a in range(2001, 2025)} for k, v in imerg_m.items()
                   if k in ("NIC", "caja_sicc")}
    imerg_jjason = {k: {a: sum(v[(a, m)] for m in JUN_NOV) for a in range(2001, 2025)} for k, v in imerg_m.items()
                    if k in ("NIC", "caja_sicc")}

    # GISTEMP
    gis = {}
    ruta_g = FENOMENOS / "gistemp_nicaragua.csv"
    if ruta_g.exists():
        with ruta_g.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                for k in ORDEN:
                    gis.setdefault(k, {}).setdefault(int(r["anio"]), []).append(_f(r[k]))
    gis_anual = {k: {a: float(np.nanmean(v)) for a, v in por.items() if np.sum(np.isfinite(v)) >= 10 and 1981 <= a <= 2024}
                 for k, por in gis.items()}

    # NDVI
    ndvi = {}
    ruta_n = FENOMENOS / "ndvi_modis.csv"
    if ruta_n.exists():
        por = {}
        with ruta_n.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                if r["ndvi"]:
                    por.setdefault(r["region"], {}).setdefault(int(r["fecha"][:4]), []).append(float(r["ndvi"]))
        ndvi = {k: {a: float(np.mean(v)) for a, v in d.items() if len(v) >= 20 and a <= 2024} for k, d in por.items()}

    regiones_out, objetivos, comparaciones = [], {}, {}
    for k in ORDEN:
        s, sequia, can, temps = series_region(diario[k], celdas.get(k, {}), k, lat_media[k])
        if k in imerg_anual:
            s["lluvia_anual_imerg"] = imerg_anual[k]
            s["lluvia_jun_nov_imerg"] = imerg_jjason[k]
        if k in gis_anual:
            s["temperatura_gistemp"] = gis_anual[k]
        if k in ndvi:
            s["ndvi"] = ndvi[k]
        indep = {}
        if k in imerg_anual:
            comunes = sorted(set(imerg_anual[k]) & set(s["lluvia_anual"]))
            tp = tr.analizar(comunes, [s["lluvia_anual"][a] for a in comunes], "mm")
            ti = tr.analizar(comunes, [imerg_anual[k][a] for a in comunes], "mm")
            comparaciones[f"lluvia_{k}"] = {
                "periodo": [comunes[0], comunes[-1]],
                "r_anual": float(np.corrcoef([s["lluvia_anual"][a] for a in comunes], [imerg_anual[k][a] for a in comunes])[0, 1]),
                "media_power_mm": float(np.mean([s["lluvia_anual"][a] for a in comunes])),
                "media_imerg_mm": float(np.mean([imerg_anual[k][a] for a in comunes])),
                "sen_power_mm_decada": tp["theil_sen"]["por_decada"], "ic_power": tp["theil_sen"]["ic_por_decada"],
                "sen_imerg_mm_decada": ti["theil_sen"]["por_decada"], "ic_imerg": ti["theil_sen"]["ic_por_decada"],
                "veredicto_power": tp["veredicto"], "veredicto_imerg": ti["veredicto"]}
            c = comparaciones[f"lluvia_{k}"]
            if c["veredicto_power"] != c["veredicto_imerg"] or np.sign(c["sen_power_mm_decada"]) != np.sign(c["sen_imerg_mm_decada"]):
                indep["lluvia"] = (f"En {c['periodo'][0]}–{c['periodo'][1]} la tendencia de lluvia de MERRA-2 "
                                   f"({c['sen_power_mm_decada']:+.0f} mm/década) no coincide con la de IMERG "
                                   f"({c['sen_imerg_mm_decada']:+.0f} mm/década): la tendencia de lluvia del reanálisis no "
                                   "es fiable aquí.")
        if k in gis_anual:
            comunes = sorted(set(gis_anual[k]) & set(s["t2m_media"]))
            if len(comunes) >= 15:
                tg = tr.analizar(comunes, [gis_anual[k][a] for a in comunes], "°C")
                tm = tr.analizar(comunes, [s["t2m_media"][a] for a in comunes], "°C")
                comparaciones[f"temperatura_{k}"] = {
                    "periodo": [comunes[0], comunes[-1]], "n": len(comunes),
                    "sen_gistemp_c_decada": tg["theil_sen"]["por_decada"], "ic_gistemp": tg["theil_sen"]["ic_por_decada"],
                    "sen_merra2_c_decada": tm["theil_sen"]["por_decada"], "ic_merra2": tm["theil_sen"]["ic_por_decada"],
                    "veredicto_gistemp": tg["veredicto"], "veredicto_merra2": tm["veredicto"]}
                c = comparaciones[f"temperatura_{k}"]
                if c["veredicto_gistemp"] != c["veredicto_merra2"] or np.sign(c["sen_gistemp_c_decada"]) != np.sign(c["sen_merra2_c_decada"]):
                    indep["temperatura"] = (f"La tendencia de temperatura de MERRA-2 ({c['sen_merra2_c_decada']:+.2f} °C/década) "
                                            f"no coincide con la observada por GISTEMP ({c['sen_gistemp_c_decada']:+.2f} °C/década, "
                                            f"{c['periodo'][0]}–{c['periodo'][1]}).")
        variables = {}
        for nombre, serie in s.items():
            fen = VARIABLES[nombre][1]
            nota = indep.get("lluvia") if fen in ("lluvia", "extremos_lluvia") and not nombre.endswith("_imerg") else \
                indep.get("temperatura") if fen in ("temperatura", "calor_extremo") and nombre != "temperatura_gistemp" else None
            variables[nombre] = analizar_variable(nombre, serie, indices, k, nota)
        regiones_out.append({"id": k, "nombre": NOMBRES[k], "variables": variables, "canicula": can, "sequia_mensual": sequia})
        objetivos[k] = temps

    # escenarios CMIP6
    cmip6 = pr.leer_cmip6()
    escenarios = {}
    if cmip6:
        for k in ORDEN:
            d = diario[k]
            obs_pr, obs_t = {}, {}
            anio, mes, _ = ind.descomponer(d["fecha"])
            for a in range(1995, 2015):
                for m in range(1, 13):
                    sel = (anio == a) & (mes == m)
                    obs_pr[(a, m)] = float(d["prectotcorr"][sel].sum())
                    obs_t[(a, m)] = float(d["t2m"][sel].mean())
            escenarios[k] = {
                "lluvia_anual": pr.escenarios(cmip6, obs_pr, k, "pr", "anual"),
                "lluvia_jun_nov": pr.escenarios(cmip6, obs_pr, k, "pr", "jun_nov"),
                "lluvia_jul_ago": pr.escenarios(cmip6, obs_pr, k, "pr", "jul_ago"),
                "t2m_media": pr.escenarios(cmip6, obs_t, k, "tas", "anual"),
            }

    integridad = {p.name: sha256(p) for p in sorted(FENOMENOS.glob("*.csv"))}
    integridad["regiones_nicaragua.geojson"] = sha256(REGIONES_GEOJSON)
    integridad["serie_mensual.csv"] = sha256(DATOS / "serie_mensual.csv")
    from .fuentes import catalogo
    return {
        "esquema": "nasa-challenge/fenomenos-nicaragua", "version_esquema": VERSION, "estado": "exploratorio",
        "generado": date.today().isoformat(),
        "metadatos": {
            "titulo": "Tendencias, pronóstico estacional y escenarios del clima de Nicaragua con datos NASA",
            "base_climatologica": list(BASE),
            "fuentes": catalogo(),
            "integridad_sha256": integridad,
            "limites": LIMITES,
        },
        "reto": {"nombre": "Be An Earth System Trend Detective! (NASA Space Apps 2026)",
                 "preguntas": {"que": "variables[*].titulo y definicion", "donde": "regiones[*] y mapas_tendencia",
                               "cuanto": "tendencia.theil_sen.por_decada con IC 95 %",
                               "significativo": "tendencia.mann_kendall_modificado, intervalos y veredicto; FDR en mapas"}},
        "indices_climaticos": {
            "definiciones": {
                "nino34": "Anomalía de TSM en 5° S–5° N, 170°–120° O (MERRA-2 TS, base 1991–2020).",
                "tna": "Anomalía de TSM del Atlántico Norte tropical, 5,5–23,5° N, 57,5–20° O.",
                "amo": "Anomalía de TSM del Atlántico Norte 0–60° N, 80° O–0°, sin tendencia lineal.",
                "pdo": "Primer componente principal de la TSM del Pacífico Norte 20–60° N (tras restar la media de la cuenca), estandarizado.",
                "cllj": "Aproximación al chorro de bajo nivel del Caribe: −U a 10 m en 12,5–17,5° N, 80–70° O, anomalía (m/s). El índice de referencia usa 925 hPa (adaptador merra2, con cuenta)."},
            "validacion_nino34_vs_oni_noaa": validacion_enos,
            "mensual": {"anios": [a for a, _ in claves], "meses": [m for _, m in claves],
                        **{k: [round(indices[k][c], 3) for c in claves] for k in MODULADORES}}},
        "regiones": regiones_out,
        "mapas_tendencia": mapa_celdas(),
        "comparaciones_independientes": comparaciones,
        "modelo_estacional": modelo_estacional(objetivos, indices, permutaciones, imerg_jjason),
        "escenarios_cmip6": escenarios,
    }


LIMITES = [
    "Estado exploratorio. Detección de tendencias, pronóstico estacional y escenarios son productos distintos.",
    "44 años (MERRA-2) y 24–27 años (IMERG) son registros cortos: una tendencia puede ser variabilidad decadal.",
    "MERRA-2 es un reanálisis: cambios en las observaciones asimiladas pueden crear saltos artificiales. Toda tendencia del reanálisis se contrasta con IMERG (lluvia) y GISTEMP (temperatura).",
    "Con muchas variables y regiones algunas detecciones serán falsos positivos; los mapas usan FDR.",
    "Ciclones: NASA no publica trayectorias; solo se ven a través de la lluvia extrema.",
    "Ningún año futuro concreto se presenta como pronóstico determinista: el estacional da un valor esperado con intervalo y probabilidades de tercil; las décadas, un rango de escenarios.",
]


def escribir(permutaciones=200, salida=DATOS / "fenomenos_nicaragua.json"):
    r = construir(permutaciones)
    texto = json.dumps(_limpio(r), ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    Path(salida).write_text(texto + "\n", encoding="utf-8", newline="\n")
    return r


def _limpio(v):
    if isinstance(v, dict):
        return {k: _limpio(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_limpio(x) for x in v]
    if isinstance(v, (np.floating, float)):
        return None if not math.isfinite(float(v)) else round(float(v), 5)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.bool_):
        return bool(v)
    return v
