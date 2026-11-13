"""Integra las salidas de los agentes de recursos en data/recursos_integrados.json (sin red).

Lee lo que exista en data/recursos/{tierra,contraste,csa}/ además de data/clima.json y
data/fenomenos_nicaragua.json, y organiza el resultado para la pestaña «Investigate»:

    categorias       → qué se quiere investigar (lluvia, temperatura, vegetación, agua, aire, costa)
    lugares          → dónde (nombre, centro y zoom para el mapa)
    investigaciones  → una serie por variable y lugar, con su tendencia calculada aquí con
                       estadistica/tendencia_robusta.analizar (el mismo motor que usan los agentes)
    contrastes       → segundas opiniones (otra fuente o método) asociadas a una investigación
    demostraciones   → recorridos guiados
    recursos         → los 13 recursos de la pestaña Resources con su estado real de uso

Una categoría o un recurso sin datos no se omite del JSON, pero la interfaz solo muestra lo que tiene
datos («en_uso»). Las series con papel «demostracion_registro_corto» nunca llevan tendencia.
Los datos sintéticos (`"sintetico": true`) se rechazan salvo que se pida expresamente en pruebas.
"""
import csv
import json
import math
from datetime import date
from pathlib import Path

from .estadistica import tendencia_robusta as tr
from .rutas import DATOS, sha256

VERSION = "1.0.0"
SALIDA = DATOS / "recursos_integrados.json"
MIN_ANIOS_TENDENCIA = 10

CATEGORIAS = [
    {"id": "lluvia", "nombre_en": "Rain", "pregunta_en": "Is it raining more or less than before?"},
    {"id": "temperatura", "nombre_en": "Temperature", "pregunta_en": "Is it getting warmer?"},
    {"id": "vegetacion", "nombre_en": "Vegetation & ecosystems", "pregunta_en": "Is the land getting greener or browner?",
     # Texto del agente 3 (docs/reto/recursos/csa.md), basado en la página de la CSA sobre ecosistemas.
     "descripcion_en": "Satellite observations can help identify changes in forest condition, land cover and habitat. "
                       "Ask whether a greenness change persists across years and whether it coincides with disturbance "
                       "or land-use change.",
     "recurso": 12},
    {"id": "agua", "nombre_en": "Water bodies", "pregunta_en": "Are lakes and soils holding more or less water?",
     "descripcion_en": "Satellite radar can map water extent, while SWOT measures water-surface elevation. Changes can "
                       "reflect seasonal inflows, evaporation and water management.",
     "recurso": 12},
    {"id": "aire", "nombre_en": "Air quality", "pregunta_en": "Is the air over the city changing?"},
    {"id": "costa", "nombre_en": "Coast & ocean", "pregunta_en": "Are coastal waters changing?"},
]

# id: (nombre en inglés, país, [lat, lon], zoom)
LUGARES = {
    "NIC": ("Nicaragua", "Nicaragua", [12.9, -85.2], 6),
    "caja_sicc": ("Study box (SW Nicaragua)", "Nicaragua", [11.65, -85.05], 7),
    "pacifico": ("Pacific lowlands", "Nicaragua", [12.3, -86.4], 7),
    "central": ("Central highlands", "Nicaragua", [13.0, -85.7], 7),
    "caribe": ("Caribbean coast", "Nicaragua", [12.9, -84.0], 7),
    "HND": ("Honduras", "Honduras", [14.8, -86.6], 6),
    "CRI": ("Costa Rica", "Costa Rica", [9.9, -84.2], 7),
    "cocibolca": ("Lake Nicaragua (Cocibolca)", "Nicaragua", [11.55, -85.4], 8),
    "xolotlan": ("Lake Managua (Xolotlán)", "Nicaragua", [12.33, -86.33], 9),
    "managua": ("Managua", "Nicaragua", [12.13, -86.25], 10),
    "CAN_prairies": ("Canadian Prairies", "Canada", [51.6, -105.6], 5),
}
NOMBRES_PAIS = {"NIC": "Nicaragua", "HND": "Honduras", "CRI": "Costa Rica"}

# Contrastes del agente 2 → investigación a la que aportan una segunda opinión.
CONTRASTE_A_INVESTIGACION = {
    "cru_nic": "lluvia_NIC", "gpcc_nic": "lluvia_NIC",
    "cru_caja_sicc": "lluvia_caja_sicc", "gpcc_caja_sicc": "lluvia_caja_sicc",
    "giovanni_imerg_nic": "lluvia_NIC", "giovanni_imerg_caja_sicc": "lluvia_caja_sicc",
    "noaa_tegucigalpa_lluvia_vs_imerg_hnd": "lluvia_HND",
    "noaa_managua_tavg": "temperatura_NIC", "noaa_juigalpa_tavg": "temperatura_NIC",
    # Agente 3: estaciones de las Praderas (data/recursos/csa/contrastes_canada.json)
    "noaa_canada_lluvia": "lluvia_CAN_prairies", "noaa_canada_tavg": "temperatura_CAN_prairies",
}
# Prefijo de id de una variable nueva del agente 2 → (categoría, lugar por defecto)
PREFIJO_CATEGORIA = {"clorofila_": "costa", "omi_no2": "aire", "airs_tas": "temperatura"}
# CRU y GPCC se descargaron directamente (KNMI pide verificación humana): no cuentan como uso de KNMI.
FUENTE_CONTRASTE = {"knmi_": 6, "giovanni_": 1, "noaa_": 4}

# Variables de los agentes 1 (AppEEARS, GLDAS) → (categoría, título, definición sencilla)
VARIABLES_TIERRA = {
    "ndvi_regional": ("vegetacion", "Vegetation greenness (NDVI), whole region",
                      "How green the vegetation is, from 0 (bare) to 1 (dense), averaged over the region."),
    "ndvi_cobertura_estable": ("vegetacion", "Vegetation greenness (NDVI), unchanged land cover",
                               "NDVI only where the land-cover class stayed the same every year, to separate climate "
                               "from land-use change."),
    "lst_dia": ("temperatura", "Daytime land surface temperature",
                "How hot the ground surface is during the day, measured from space."),
    "et_modis": ("agua", "Evapotranspiration (MODIS)",
                 "Water returned to the air by evaporation from soil and transpiration from plants."),
    "humedad_smap_superficial": ("agua", "Surface soil moisture (SMAP)", "Water in the top ~5 cm of soil."),
    "humedad_smap_raiz": ("agua", "Root-zone soil moisture (SMAP)", "Water in the top ~1 m of soil, where roots grow."),
    "humedad_gldas_0_10": ("agua", "Soil moisture 0–10 cm (GLDAS)", "Water in the top 10 cm of soil, from a land model."),
    "humedad_gldas_10_40": ("agua", "Soil moisture 10–40 cm (GLDAS)", "Water in the soil 10 to 40 cm deep, from a land model."),
    "et_gldas": ("agua", "Evapotranspiration (GLDAS)", "Water returned to the air by soil and plants, from a land model."),
    "escorrentia_superficial_gldas": ("agua", "Surface runoff (GLDAS)", "Rain that flows over the ground instead of soaking in."),
    "escorrentia_subterranea_gldas": ("agua", "Subsurface runoff (GLDAS)", "Water that drains through the soil toward rivers."),
}
RECURSO_TIERRA = {"appeears": 3, "gldas": 2}

RECURSOS = [
    (1, "Giovanni", "https://giovanni.gsfc.nasa.gov/", "NASA"),
    (2, "Hydrology Time Series", "https://disc.gsfc.nasa.gov/information/tools?title=Hydrology%20Time%20Series", "NASA"),
    (3, "AppEEARS", "https://appeears.earthdatacloud.nasa.gov/", "NASA"),
    (4, "Climate Data Online (CDO)", "https://www.ncei.noaa.gov/cdo-web/", "NOAA"),
    (5, "Time-Series Analysis of Remotely-Sensed SeaWiFS Chlorophyll in River-Influenced Coastal Regions",
     "https://ntrs.nasa.gov/api/citations/20090042747/downloads/20090042747.pdf", "NASA"),
    (6, "KNMI Climate Explorer", "https://climexp.knmi.nl/", "KNMI"),
    (7, "Statistical test methods to detect trends in time series data",
     "https://medium.com/@snp.kriss/statistical-test-methods-to-detect-trends-in-time-series-data-b361a0ec530b", "Medium"),
    (8, "A Comprehensive Guide to Statistical Significance",
     "https://www.statsig.com/perspectives/a-comprehensive-guide-to-statistical-significance", "Statsig"),
    (9, "Radarsat Constellation Mission (RCM) - Data", "https://donnees-data.asc-csa.gc.ca/en/dataset/rcm", "CSA"),
    (10, "Geo.ca", "http://geo.ca/", "Government of Canada"),
    (11, "SWOT Mission - Information", "https://www.asc-csa.gc.ca/eng/satellites/swot/", "CSA"),
    (12, "Monitoring and protecting our ecosystem from space",
     "https://www.asc-csa.gc.ca/eng/satellites/everyday-lives/monitoring-and-protecting-our-ecosystems-from-space.asp", "CSA"),
    (13, "Synthetic Aperture Radar python Tutorial", "https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial", "CSA"),
]


ESTACIONES = {"NUM00078741": "Managua", "NU000069034": "Juigalpa", "HO000078720": "Tegucigalpa"}


# ---------------------------------------------------------------- utilidades
def nombre_en(texto):
    """Nombre de fuente para la interfaz (en inglés, sin rutas internas) a partir del de los agentes."""
    t = texto or ""
    estacion = next((n for k, n in ESTACIONES.items() if k in t), None)
    if estacion and "GHCN-Daily" in t:
        return f"{estacion} weather station (NOAA GHCN-Daily)"
    if estacion:
        return f"{estacion} weather station (NOAA GSOM)"
    reglas = [("CRU TS", "CRU TS 4.10 (University of East Anglia)"), ("GPCC", "GPCC gauge analysis (via NOAA PSL)"),
              ("GPM IMERG", "NASA GPM IMERG Final V07B"), ("NASA POWER", "NASA POWER (MERRA-2), nearest grid cell"),
              ("MODIS-Aqua L3m CHL", "NASA MODIS-Aqua chlorophyll-a (OBPG, 4 km)"),
              ("GLDAS_NOAH025_M", "NASA GLDAS-2.1 Noah land model (GES DISC), regional mean")]
    if t.startswith("appeears/"):
        return f"NASA {t.split('/', 1)[1]} via AppEEARS"
    return next((n for clave, n in reglas if clave in t), t)


def _leer_json(ruta, permitir_sintetico):
    d = json.loads(Path(ruta).read_text(encoding="utf-8"))
    if not permitir_sintetico and _es_sintetico(d):
        raise ValueError(f"{ruta} está marcado como sintético y no puede entrar en el producto")
    return d


def _es_sintetico(d):
    if isinstance(d, dict):
        return d.get("sintetico") is True or any(_es_sintetico(v) for v in d.values() if isinstance(v, (dict, list)))
    if isinstance(d, list):
        return any(_es_sintetico(v) for v in d)
    return False


def _leer_csv(ruta):
    with Path(ruta).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _r(v, n=4):
    return None if v is None or not math.isfinite(float(v)) else round(float(v), n)


def tendencia_compacta(anios, valores, unidad):
    """Resumen de tendencia para la interfaz: Sen con IC, MCO con IC, HAC, Mann–Kendall y veredicto."""
    pares = [(int(a), float(v)) for a, v in zip(anios, valores) if v is not None and math.isfinite(float(v))]
    if len(pares) < MIN_ANIOS_TENDENCIA:
        return {"veredicto": "datos_insuficientes", "anios": len(pares), "unidad_pendiente": f"{unidad}/decade"}
    a, y = zip(*pares)
    t = tr.analizar(a, y, unidad)
    if t["veredicto"] == "datos_insuficientes":
        return {"veredicto": "datos_insuficientes", "anios": len(pares), "unidad_pendiente": f"{unidad}/decade"}
    m = t["minimos_cuadrados"]
    return {
        "veredicto": t["veredicto"], "veredicto_contrato": m["veredicto"], "anios": t["anios"], "periodo": t["periodo"],
        "unidad_pendiente": f"{unidad}/decade",
        "sen": {"por_decada": _r(t["theil_sen"]["por_decada"]), "ic": [_r(x) for x in t["theil_sen"]["ic_por_decada"]]},
        "mco": {"por_decada": _r(m["por_decada"]), "ic": [_r(x) for x in m["ic_por_decada"]], "p_valor": _r(m["p_valor"])},
        "hac_ic": [_r(x) for x in m["hac_ic_por_decada"]],
        "mann_kendall_p": _r(t["mann_kendall_modificado"]["p_valor"]),
        "media": _r(m["media"]),
    }


def _investigacion(id_, categoria, lugar, titulo, definicion, unidad, anios, valores, fuente, recursos=(), papel="tendencia",
                   notas=(), frecuencia="anual"):
    inv = {"id": id_, "categoria": categoria, "lugar": lugar, "titulo_en": titulo, "definicion_en": definicion,
           "unidad": unidad, "papel": papel, "frecuencia": frecuencia, "tiempos": list(anios),
           "valores": [_r(v, 4) for v in valores], "fuente": fuente, "recursos": sorted(set(recursos)),
           "contrastes": [], "notas": list(notas)}
    if papel == "tendencia":
        inv["tendencia"] = tendencia_compacta(anios, valores, unidad)
    return inv


# ---------------------------------------------------------------- bloques de datos
def _base_nicaragua(fen, clima):
    """Series ya existentes en el proyecto: lluvia IMERG, temperatura GISTEMP y NDVI por sitios."""
    invs = []
    regiones = {r["id"]: r for r in fen["regiones"]}
    imerg = {"producto": "NASA GPM IMERG Final V07B", "url": "https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGM_07/summary"}
    gistemp = {"producto": "NASA GISS GISTEMP v4 (250 km)", "url": "https://data.giss.nasa.gov/gistemp/"}
    for rid in ("NIC", "caja_sicc"):
        v = regiones[rid]["variables"].get("lluvia_anual_imerg")
        if v:
            invs.append(_investigacion(f"lluvia_{rid}", "lluvia", rid, "Annual rainfall", "All the rain that fell in a year.",
                                       "mm", v["anios"], v["valores"], imerg))
    v = regiones["NIC"]["variables"].get("lluvia_jun_nov_imerg")
    if v:
        invs.append(_investigacion("lluvia_jun_nov_NIC", "lluvia", "NIC", "Rainy-season rainfall (June–November)",
                                   "Rain during the main rainy season.", "mm", v["anios"], v["valores"], imerg))
    for d in clima["dominios"]:
        if d["id"] in ("HND", "CRI"):
            invs.append(_investigacion(f"lluvia_{d['id']}", "lluvia", d["id"], "Annual rainfall", "All the rain that fell in a year.",
                                       "mm", d["anios_validos"], d["serie_anual_mm"], imerg))
    for rid in ("NIC", "pacifico", "central", "caribe"):
        v = regiones[rid]["variables"].get("temperatura_gistemp")
        if v:
            invs.append(_investigacion(f"temperatura_{rid}", "temperatura", rid, "Air temperature anomaly",
                                       "How much warmer or cooler the air near the ground was than the 1951–1980 average.",
                                       "°C", v["anios"], v["valores"], gistemp))
    for rid in ("pacifico", "central", "caribe"):
        v = regiones[rid]["variables"].get("ndvi")
        if v:
            invs.append(_investigacion(f"ndvi_sitios_{rid}", "vegetacion", rid, "Vegetation greenness (NDVI) at sample sites",
                                       "How green the vegetation is, from 0 (bare) to 1 (dense), at representative sites.",
                                       "NDVI", v["anios"], v["valores"],
                                       {"producto": "NASA MODIS MOD13Q1 NDVI (ORNL DAAC subsets)", "url": "https://modis.ornl.gov/"}))
    return invs


def _tierra(carpeta, permitir_sintetico):
    """Series anuales de AppEEARS y GLDAS (listas de SerieRegional.como_dict())."""
    invs, entradas = [], []
    for ruta in sorted(Path(carpeta).glob("series_*_anual.json")):
        entradas.append(ruta)
        familia = "gldas" if "gldas" in ruta.name else "appeears"
        for s in _leer_json(ruta, permitir_sintetico):
            var = s["variable"]
            if var not in VARIABLES_TIERRA:
                continue
            cat, titulo, definicion = VARIABLES_TIERRA[var]
            region = s["region"]
            if region not in LUGARES:
                continue
            notas = list(s.get("notas", []))
            # GLDAS de punto viene de la API de Giovanni (recursos #2 y #1); el regional, del archivo de GES DISC.
            punto = familia == "gldas" and "giovanni" in s["fuente"].lower()
            if punto:
                titulo += " at a sample point"
            recursos = [RECURSO_TIERRA[familia], 1] if punto else [] if familia == "gldas" else [RECURSO_TIERRA[familia]]
            invs.append(_investigacion(f"{var}_{region}", cat, region, titulo, definicion, s["unidad"].replace("adimensional", "NDVI"),
                                       s["tiempos"], s["valores"], {"producto": nombre_en(s["fuente"]), "version": s.get("version", "")},
                                       recursos=recursos, notas=notas))
    return invs, entradas


def _contraste(carpeta, permitir_sintetico, nombre_json="resumen_contrastes.json", nombre_csv="series_anuales.csv"):
    """Contrastes y variables nuevas con el esquema del agente 2 (también lo usa el agente 3 para Canadá)."""
    carpeta = Path(carpeta)
    ruta = carpeta / nombre_json
    if not ruta.is_file():
        return [], [], [], {}
    resumen = _leer_json(ruta, permitir_sintetico)
    series_csv = carpeta / nombre_csv
    series = {}
    if series_csv.is_file():
        for f in _leer_csv(series_csv):
            series.setdefault((f["contraste"], f["serie"]), []).append((int(f["anio"]), float(f["valor"])))
    invs, contrastes, lugares = [], [], {}
    for c in resumen["contrastes"]:
        if c.get("estado") != "ok":
            continue
        cid = c["id"]
        recurso = next((n for p, n in FUENTE_CONTRASTE.items() if cid.startswith(p)), None)
        if c["papel"] == "tendencia":
            cat = next((v for p, v in PREFIJO_CATEGORIA.items() if cid.startswith(p)), None)
            puntos = sorted(series.get((cid, "nuestra"), []))
            if not cat or not puntos:
                continue
            caja = c.get("caja")
            lugar = cid if caja else c.get("region")
            if caja:
                lugares[cid] = (c["region"], "Nicaragua", [round((caja[1] + caja[3]) / 2, 2), round((caja[0] + caja[2]) / 2, 2)], 8)
            unidad = c["serie_nuestra"]["unidad"].split("/")[0].replace("mg m-3", "mg/m³")
            recursos = [recurso] if recurso else []
            if cid.startswith("clorofila_"):
                recursos.append(5)
                titulo, definicion = ("Chlorophyll-a in coastal water",
                                      "A green pigment in microscopic algae; more chlorophyll usually means more algae.")
            else:
                titulo, definicion = c.get("titulo_en", cid), c.get("definicion_en", "")
            inv = _investigacion(cid, cat, lugar, titulo, definicion, unidad, [a for a, _ in puntos], [v for _, v in puntos],
                                 {"producto": nombre_en(c["serie_nuestra"]["fuente"]), "url": "https://oceancolor.gsfc.nasa.gov/"},
                                 recursos=recursos)
            ext = c["serie_externa"]
            inv["contrastes"].append(cid + "_metodo")
            contrastes.append({"id": cid + "_metodo", "investigacion": cid, "tipo": "metodo", "frase_en": c.get("frase_en", ""),
                               "externa": {"nombre_en": "Method of Acker et al. (NASA NTRS 20090042747)" if cid.startswith("clorofila_") else nombre_en(ext["fuente"]),
                                           "por_decada": _r(ext.get("pendiente")), "p_valor": _r(ext.get("p_valor_F")),
                                           "significativa": (ext.get("p_valor_F") or 1) < 0.05},
                               "recursos": recursos})
            invs.append(inv)
        else:
            # El agente puede indicar la investigación de destino; si no, se usa la tabla fija.
            destino = c.get("investigacion") or CONTRASTE_A_INVESTIGACION.get(cid)
            if not destino:
                continue
            nuestra, ext, dif = c["serie_nuestra"], c["serie_externa"], c.get("diferencia", {})
            sn = sorted(series.get((cid, "nuestra"), []))
            se = sorted(series.get((cid, "externa"), []))
            contrastes.append({
                "id": cid, "investigacion": destino, "tipo": "fuente", "frase_en": c.get("frase_en", ""),
                "periodo": c.get("periodo"),
                "nuestra": {"nombre_en": nombre_en(nuestra["fuente"]), "por_decada": _r(nuestra.get("pendiente")), "veredicto": nuestra.get("veredicto_robusto") or nuestra.get("veredicto"),
                            "anios": [a for a, _ in sn], "valores": [v for _, v in sn]},
                "externa": {"nombre_en": nombre_en(ext["fuente"]), "por_decada": _r(ext.get("pendiente")), "veredicto": ext.get("veredicto_robusto") or ext.get("veredicto"),
                            "url": ext.get("url", ""), "anios": [a for a, _ in se], "valores": [v for _, v in se]},
                "r": _r(dif.get("r"), 2), "diferencia_media": _r(dif.get("media"), 2),
                "unidad": nuestra.get("unidad", "").split("/")[0], "recursos": [recurso] if recurso else []})
    entradas = [ruta] + ([series_csv] if series_csv.is_file() else [])
    return invs, contrastes, entradas, lugares


def _csa(carpeta, permitir_sintetico):
    """Agente 3: lluvia IMERG y GISTEMP en las Praderas de Canadá, nivel de lagos (G-REALM y SWOT)."""
    carpeta = Path(carpeta)
    invs, contrastes, entradas = [], [], []
    ruta = carpeta / "canada_imerg.json"
    if ruta.is_file():
        entradas.append(ruta)
        d = _leer_json(ruta, permitir_sintetico)
        invs.append(_investigacion("lluvia_CAN_prairies", "lluvia", "CAN_prairies", "Annual rainfall", "All the rain that fell in a year.",
                                   "mm", d["anios"], d["valores"],
                                   {"producto": "NASA GPM IMERG Final V07B", "url": "https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGM_07/summary"},
                                   recursos=[10]))
    ruta = carpeta / "canada_imerg_may_sep.json"
    if ruta.is_file():
        entradas.append(ruta)
        d = _leer_json(ruta, permitir_sintetico)
        invs.append(_investigacion("lluvia_may_sep_CAN_prairies", "lluvia", "CAN_prairies", "Warm-season rainfall (May–September)",
                                   "Rain from May to September, when most of the Prairies' rain falls and satellite estimates are most reliable.",
                                   "mm", d["anios"], d["valores"],
                                   {"producto": "NASA GPM IMERG Final V07B", "url": "https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGM_07/summary"},
                                   recursos=[10]))
    ruta = carpeta / "canada_gistemp.json"
    if ruta.is_file():
        entradas.append(ruta)
        d = _leer_json(ruta, permitir_sintetico)
        invs.append(_investigacion("temperatura_CAN_prairies", "temperatura", "CAN_prairies", "Air temperature anomaly",
                                   "How much warmer or cooler the air near the ground was than the 1951–1980 average.",
                                   "°C", d["anios"], d["valores"],
                                   {"producto": "NASA GISS GISTEMP v4 (250 km)", "url": d.get("fuente", "https://data.giss.nasa.gov/gistemp/")},
                                   recursos=[10]))
    ruta = carpeta / "cocibolca_grealm.csv"
    if ruta.is_file():
        entradas.append(ruta)
        meses = {}
        for f in _leer_csv(ruta):
            meses.setdefault(f["fecha"][:7], []).append(float(f["altura_egm2008_m"]))
        anual = {}
        for m, v in meses.items():
            anual.setdefault(int(m[:4]), []).append(sum(v) / len(v))
        anios = sorted(a for a, v in anual.items() if len(v) == 12)
        inv = _investigacion("nivel_cocibolca", "agua", "cocibolca", "Lake water level",
                             "Height of the lake surface above sea level (EGM2008), yearly average of monthly means.",
                             "m", anios, [sum(anual[a]) / 12 for a in anios],
                             {"producto": "G-REALM lake 000351 (USDA FAS / NASA GSFC satellite altimetry)",
                              "url": "https://ipad.fas.usda.gov/cropexplorer/global_reservoir/"},
                             notas=["Años con los 12 meses observados; la serie combina varias misiones de altimetría."])
        invs.append(inv)
        comp = carpeta / "comparacion_cocibolca_grealm_swot.csv"
        if comp.is_file():
            entradas.append(comp)
            filas = [f for f in _leer_csv(comp) if f["swot_m"] and f["grealm_m"]]
            g = [float(f["grealm_m"]) for f in filas]
            s = [float(f["swot_m"]) for f in filas]
            n = len(filas)
            if n >= 3:
                mg, ms = sum(g) / n, sum(s) / n
                cov = sum((a - mg) * (b - ms) for a, b in zip(g, s))
                r = cov / math.sqrt(sum((a - mg) ** 2 for a in g) * sum((b - ms) ** 2 for b in s))
                sesgo = ms - mg
                inv["contrastes"].append("swot_vs_grealm_cocibolca")
                contrastes.append({
                    "id": "swot_vs_grealm_cocibolca", "investigacion": "nivel_cocibolca", "tipo": "fuente",
                    "frase_en": f"SWOT vs G-REALM, Lake Nicaragua, {filas[0]['mes']} to {filas[-1]['mes']}: {n} common months, "
                                f"r = {r:.2f}, constant offset {sesgo:+.2f} m (different altimetry processing). "
                                f"SWOT confirms the level and seasonal cycle measured by G-REALM.",
                    "periodo": [filas[0]["mes"], filas[-1]["mes"]],
                    "nuestra": {"nombre_en": "G-REALM monthly mean", "tiempos": [f["mes"] for f in filas], "valores": g},
                    "externa": {"nombre_en": "SWOT (NASA/CNES) monthly mean", "tiempos": [f["mes"] for f in filas], "valores": s},
                    "r": round(r, 2), "diferencia_media": round(sesgo, 3), "unidad": "m", "recursos": [11]})
    ruta = carpeta / "swot_mensual.csv"
    if ruta.is_file():
        entradas.append(ruta)
        por_lago = {}
        for f in _leer_csv(ruta):
            por_lago.setdefault(f["lago"], []).append((f["mes"], float(f["wse_m"])))
        for lago, puntos in sorted(por_lago.items()):
            puntos.sort()
            invs.append(_investigacion(f"swot_{lago}", "agua", lago, "Lake water level from SWOT",
                                       "Height of the lake surface above sea level (EGM2008) measured by the SWOT satellite.",
                                       "m", [m for m, _ in puntos], [v for _, v in puntos],
                                       {"producto": "NASA/CNES SWOT L2 HR LakeSP via PO.DAAC Hydrocron",
                                        "url": "https://podaac.jpl.nasa.gov/SWOT"},
                                       recursos=[11], papel="demostracion_registro_corto", frecuencia="mensual"))
    region_canada = carpeta.parents[1] / "regiones_canada.geojson"
    if region_canada.is_file():
        entradas.append(region_canada)
    return invs, contrastes, entradas


def _demostraciones(invs):
    ids = {i["id"]: i for i in invs}
    demos = []
    if "lluvia_NIC" in ids:
        pasos = [{"investigacion": "lluvia_NIC", "texto_en": "Start with what NASA satellites measured: yearly rainfall over Nicaragua since 2001."},
                 {"investigacion": "lluvia_NIC", "ver": "veredicto", "texto_en": "The slope is negative, but its 95% confidence interval includes zero: the record cannot tell a trend apart from year-to-year swings."}]
        if ids["lluvia_NIC"]["contrastes"]:
            pasos.append({"investigacion": "lluvia_NIC", "ver": "contrastes", "texto_en": "A second opinion: gauge-based datasets reach the same verdict."})
        pasos.append({"investigacion": "lluvia_NIC", "ver": "aprender", "texto_en": "Not significant does not mean no change. A longer record could make the same change detectable."})
        demos.append({"id": "lluvia_nicaragua", "titulo_en": "Has Nicaragua's rainfall changed?", "pasos": pasos})
    if "temperatura_NIC" in ids and "temperatura_CAN_prairies" in ids:
        a, b = ids["temperatura_NIC"], ids["temperatura_CAN_prairies"]
        ventana = [max(min(a["tiempos"]), min(b["tiempos"])), min(max(a["tiempos"]), max(b["tiempos"]))]
        recorte = lambda i: [(t, v) for t, v in zip(i["tiempos"], i["valores"]) if ventana[0] <= t <= ventana[1]]
        comp = {i["id"]: tendencia_compacta(*zip(*recorte(i)), "°C") for i in (a, b)}
        demos.append({"id": "nicaragua_vs_praderas", "titulo_en": "Tropics vs. prairies: is warming the same everywhere?",
                      "ventana": ventana, "comparacion": comp,
                      "pasos": [{"investigacion": "temperatura_NIC", "texto_en": "Nicaragua's air temperature since 1981 shows a clear warming trend."},
                                {"investigacion": "temperatura_CAN_prairies", "texto_en": "The Canadian Prairies swing by several degrees from one year to the next."},
                                {"investigacion": "temperatura_CAN_prairies", "ver": "comparacion", "texto_en": f"Over the same {ventana[0]}–{ventana[1]} window, the same method detects warming in Nicaragua but not in the noisier Prairies record."}]})
    return demos


def _recursos(invs, contrastes, hay_csa):
    usados = {n for i in invs for n in i["recursos"]} | {n for c in contrastes for n in c.get("recursos", [])}
    usados.add(8)  # Statsig: base de la sección «Learn».
    if hay_csa:
        usados.add(12)  # textos de las categorías de vegetación y agua.
    usos = {
        1: "Area-averaged NASA time series and point series used as data sources and cross-checks.",
        2: "GLDAS land-model hydrology at sample points.",
        3: "Regional averages of MODIS vegetation, land temperature and evapotranspiration, and SMAP soil moisture.",
        4: "Weather-station records (GSOM, GHCN-Daily) to cross-check satellite and reanalysis data.",
        5: "Method for chlorophyll time series and significance tests in river-influenced coastal waters.",
        6: "Independent gridded datasets to cross-check rainfall trends.",
        7: "Overview of trend tests.",
        8: "Plain-language guide to p-values, confidence intervals and common misreadings (Learn section).",
        9: "Radar images of water extent.",
        10: "Boundary of the Canadian Prairies ecozone used as a contrast region.",
        11: "Lake water-surface elevation for Lake Nicaragua and Lake Managua.",
        12: "Framing of the vegetation & ecosystems and water-bodies questions.",
        13: "Workflow to map surface water from radar images.",
    }
    return [{"id": n, "nombre": nombre, "url": url, "organizacion": org, "uso_en": usos[n],
             "estado": "en_uso" if n in usados else "sin_datos"} for n, nombre, url, org in RECURSOS]


# ---------------------------------------------------------------- construcción
def construir(datos=DATOS, permitir_sintetico=False):
    datos = Path(datos)
    clima = _leer_json(datos / "clima.json", permitir_sintetico)
    fen = _leer_json(datos / "fenomenos_nicaragua.json", permitir_sintetico)
    entradas = [datos / "clima.json", datos / "fenomenos_nicaragua.json"]
    invs = _base_nicaragua(fen, clima)
    t_inv, t_ent = _tierra(datos / "recursos" / "tierra", permitir_sintetico)
    c_inv, c_con, c_ent, lugares_extra = _contraste(datos / "recursos" / "contraste", permitir_sintetico)
    s_inv, s_con, s_ent = _csa(datos / "recursos" / "csa", permitir_sintetico)
    k_inv, k_con, k_ent, _ = _contraste(datos / "recursos" / "csa", permitir_sintetico,
                                        "contrastes_canada.json", "contrastes_canada_series.csv")
    h_inv, h_con, h_ent, _ = _contraste(datos / "recursos" / "tierra", permitir_sintetico,
                                        "contrastes_tierra.json", "contrastes_tierra_series.csv")
    invs += t_inv + c_inv + s_inv + k_inv + h_inv
    contrastes = c_con + s_con + k_con + h_con
    entradas += t_ent + c_ent + s_ent + k_ent + h_ent
    por_id = {i["id"]: i for i in invs}
    for c in contrastes:
        inv = por_id.get(c["investigacion"])
        if inv and c["id"] not in inv["contrastes"]:
            inv["contrastes"].append(c["id"])
    contrastes = [c for c in contrastes if c["investigacion"] in por_id]
    usados = {i["lugar"] for i in invs}
    con_datos = {i["categoria"] for i in invs}
    return {
        "esquema": "nasa-challenge/recursos", "version_esquema": VERSION, "generado": date.today().isoformat(),
        "categorias": [{**c, "con_datos": c["id"] in con_datos} for c in CATEGORIAS],
        "lugares": [{"id": k, "nombre_en": v[0], "pais": v[1], "centro": v[2], "zoom": v[3]}
                    for k, v in {**LUGARES, **lugares_extra}.items() if k in usados],
        "investigaciones": invs,
        "contrastes": contrastes,
        "demostraciones": _demostraciones(invs),
        "recursos": _recursos(invs, contrastes, bool(s_ent)),
        "entradas": {str(Path(r).relative_to(datos)).replace("\\", "/"): sha256(r) for r in entradas},
    }


def escribir(datos=DATOS, salida=None):
    d = construir(datos)
    salida = Path(salida or Path(datos) / "recursos_integrados.json")
    salida.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return salida
