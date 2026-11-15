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
    {"id": "ciclones", "nombre_en": "Hurricanes", "pregunta_en": "Do tropical storms and hurricanes come near Nicaragua more often?",
     "descripcion_en": "Storm tracks from NOAA IBTrACS since 1981, counting every storm whose centre passed within about "
                       "150 km of a box around Nicaragua, from the Caribbean or the Pacific."},
    {"id": "polos", "nombre_en": "Ice", "pregunta_en": "Is Earth's ice shrinking?",
     "descripcion_en": "Sea ice is mapped by satellites every day since 1978: Arctic ice is smallest in September and "
                       "largest in March, and around Antarctica it is the other way round. Mountain glaciers and the "
                       "Greenland and Antarctic ice sheets are weighed by gravity satellites and surveys."},
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
    # Bandas de latitud de GISTEMP y océanos polares de NSIDC (data/recursos/hallazgos/).
    "artico": ("Arctic", "64–90°N", [78.0, -40.0], 2),
    "antartico": ("Antarctic", "64–90°S", [-75.0, -60.0], 2),
    "boreal": ("Canada and Alaska latitudes", "44–64°N", [55.0, -100.0], 3),
    "templado_norte": ("US and Mexico latitudes", "24–44°N", [34.0, -95.0], 3),
    "tropico_norte": ("Central America and Caribbean latitudes", "0–24°N", [12.0, -80.0], 3),
    "tropico_sur": ("Amazon and Andes latitudes", "0–24°S", [-12.0, -60.0], 3),
    "global": ("Whole planet", "Global mean", [15.0, -60.0], 2),
    # Océano y costa (data/recursos/hallazgos/generar_oceano.py).
    "mar_caribe_nic": ("Caribbean Sea off Nicaragua", "12–14°N, 80–82°W", [13.0, -81.0], 6),
    "arrecifes_nic": ("Caribbean reefs off Nicaragua", "NOAA Coral Reef Watch station", [14.13, -81.75], 7),
    "mar_caribe": ("Caribbean Sea", "10–22°N, 60–88°W", [16.0, -74.0], 4),
    "groenlandia": ("Greenland ice sheet", "Greenland", [72.0, -40.0], 3),
    "centroamerica": ("Central America", "7–18.5°N, 77–92.5°W", [13.0, -85.0], 5),
    "planeta": ("Whole planet", "Global total", [15.0, -60.0], 2),
    # Regiones de glaciares de GlaMBIE (RGI) en América y el total mundial.
    "glaciares_global": ("All glaciers on Earth", "Global", [15.0, -60.0], 2),
    "glaciares_alaska": ("Alaska glaciers", "USA", [61.0, -147.0], 4),
    "glaciares_oeste_canada_eeuu": ("Western Canada and US glaciers", "Canada and USA", [50.0, -120.0], 4),
    "glaciares_artico_canada_norte": ("Northern Arctic Canada glaciers", "Canada", [79.0, -80.0], 3),
    "glaciares_artico_canada_sur": ("Southern Arctic Canada glaciers", "Canada", [68.0, -68.0], 3),
    "glaciares_groenlandia_periferia": ("Greenland peripheral glaciers", "Greenland", [72.0, -40.0], 3),
    "glaciares_latitudes_bajas": ("Tropical glaciers (Andes and Mexico)", "Low latitudes", [-12.0, -75.0], 4),
    "glaciares_andes_sur": ("Southern Andes and Patagonia glaciers", "Chile and Argentina", [-45.0, -72.0], 4),
    "san_juan": ("San Juan tide gauge", "Puerto Rico", [18.46, -66.12], 10),
    "magueyes": ("Magueyes Island tide gauge", "Puerto Rico", [17.97, -67.05], 10),
    "charlotte_amalie": ("Charlotte Amalie tide gauge", "US Virgin Islands", [18.34, -64.92], 10),
    "balboa": ("Balboa tide gauge (Pacific)", "Panama", [8.97, -79.57], 10),
    "key_west": ("Key West tide gauge", "Florida, USA", [24.56, -81.81], 10),
}
# Mareógrafos PSMSL publicados → lugar.
MAREOGRAFOS = {"1001": "san_juan", "759": "magueyes", "1393": "charlotte_amalie", "163": "balboa", "188": "key_west"}
NOMBRES_PAIS = {"NIC": "Nicaragua", "HND": "Honduras", "CRI": "Costa Rica"}

# Contrastes del agente 2 → investigación a la que aportan una segunda opinión.
CONTRASTE_A_INVESTIGACION = {
    "cru_nic": "lluvia_NIC", "gpcc_nic": "lluvia_NIC",
    "cru_caja_sicc": "lluvia_caja_sicc", "gpcc_caja_sicc": "lluvia_caja_sicc",
    "giovanni_imerg_nic": "lluvia_NIC", "giovanni_imerg_caja_sicc": "lluvia_caja_sicc",
    "giovanni_gldas_sm0_10_caja_sicc": "humedad_gldas_0_10_caja_sicc",
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
              ("GLDAS_NOAH025_M", "NASA GLDAS-2.1 Noah land model (GES DISC), regional mean"),
              ("GLDAS_NOAH025_3H", "NASA GLDAS-2.1 Noah land model, sample point (Giovanni time series)"),
              ("GES DISC OPeNDAP", "NASA GPM IMERG monthly, area average from GES DISC OPeNDAP"),
              ("Giovanni, Area-Averaged", "NASA Giovanni area-averaged time series (GPM IMERG monthly)")]
    if t.startswith("appeears/"):
        return f"NASA {t.split('/', 1)[1]} via AppEEARS"
    return next((n for clave, n in reglas if clave in t), t)


def frase_en(contraste):
    """Frase del agente sin rutas internas del repositorio."""
    return contraste.get("frase_en", "").replace("data/clima.json", "the app's IMERG series")


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
    """Series regionales anuales y registro mensual de humedad superficial SMAP."""
    carpeta = Path(carpeta)
    invs, entradas = [], []
    ruta_smap = carpeta / "series_appeears_nicaragua_mensual.json"
    rutas = sorted(carpeta.glob("series_*_anual.json"))
    hay_smap_mensual = ruta_smap.is_file()
    if hay_smap_mensual:
        rutas.append(ruta_smap)
    for ruta in rutas:
        entradas.append(ruta)
        familia = "gldas" if "gldas" in ruta.name else "appeears"
        for s in _leer_json(ruta, permitir_sintetico):
            var = s["variable"]
            smap_superficial = var == "humedad_smap_superficial" and familia == "appeears"
            if ruta == ruta_smap and not smap_superficial:
                continue
            if hay_smap_mensual and ruta.name == "series_appeears_nicaragua_anual.json" and var.startswith("humedad_smap_"):
                continue
            if var not in VARIABLES_TIERRA:
                continue
            cat, titulo, definicion = VARIABLES_TIERRA[var]
            region = s["region"]
            if region not in LUGARES:
                continue
            if smap_superficial and ruta == ruta_smap:
                por_mes = dict(zip(s["tiempos"], s["valores"], strict=True))
                meses_validos = [m for m, v in sorted(por_mes.items()) if v is not None]
                if not meses_validos:
                    continue
                periodo = [meses_validos[0], meses_validos[-1]]
                anio, mes = map(int, min(por_mes).split("-"))
                tiempos = []
                ultimo_mes = max(por_mes)
                while (t := f"{anio:04d}-{mes:02d}") <= ultimo_mes:
                    tiempos.append(t)
                    anio, mes = anio + (mes == 12), mes % 12 + 1
                registro = _investigacion(
                    f"{var}_{region}", cat, region, titulo,
                    "Monthly water content in the top 5 cm of soil. SMAP Level 4 combines satellite measurements with a land model.",
                    s["unidad"], tiempos, [por_mes.get(m) for m in tiempos],
                    {"producto": nombre_en(s["fuente"]), "url": "https://doi.org/10.5067/T5RUATAQREF8",
                     "version": s.get("version", "")},
                    recursos=[RECURSO_TIERRA["appeears"]], papel="demostracion_registro_corto", frecuencia="mensual",
                )
                registro["periodo"] = periodo
                registro["validacion"] = {
                    "estado": "NO_VALIDADA",
                    "detalle_en": "Local soil measurements are needed to validate these estimates.",
                }
                invs.append(registro)
                continue
            notas = list(s.get("notas", []))
            # GLDAS de punto viene de la API de Giovanni (recursos #2 y #1); el regional, del archivo de GES DISC.
            punto = familia == "gldas" and "giovanni" in s["fuente"].lower()
            if punto:
                titulo += " at a sample point"
            recursos = [RECURSO_TIERRA[familia], 1] if punto else [] if familia == "gldas" else [RECURSO_TIERRA[familia]]
            invs.append(_investigacion(f"{var}_punto_{region}" if punto else f"{var}_{region}", cat, region, titulo, definicion, s["unidad"].replace("adimensional", "NDVI"),
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
            contrastes.append({"id": cid + "_metodo", "investigacion": cid, "tipo": "metodo", "frase_en": frase_en(c),
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
                "id": cid, "investigacion": destino, "tipo": "fuente", "frase_en": frase_en(c),
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
    # Agua del lago a partir de radar (OPERA DSWx-S1): flujo del tutorial SAR de la CSA (scripts/sar/agua_superficial.ipynb),
    # tres escenas en un dominio común; registro corto y sin validación local, así que nunca lleva tendencia.
    ruta = carpeta / "dswx_s1_serie_corta.csv"
    if ruta.is_file():
        entradas.append(ruta)
        filas = sorted(_leer_csv(ruta), key=lambda f: f["fecha"])
        if filas:
            cob = float(filas[0]["cobertura_fraccion_lago"])
            invs.append(_investigacion("radar_agua_cocibolca", "agua", "cocibolca", "Lake water area from radar",
                                       "Area of the lake classified as open water in radar images, inside the part of the "
                                       "lake observed on every date.", "km²", [f["fecha"] for f in filas],
                                       [float(f["superficie_clasificada_agua_km2"]) for f in filas],
                                       {"producto": "NASA OPERA DSWx-S1 (Sentinel-1 radar) via PO.DAAC",
                                        "url": "https://podaac.jpl.nasa.gov/dataset/OPERA_L3_DSWX-S1_V1"},
                                       recursos=[13], papel="demostracion_registro_corto", frecuencia="escena",
                                       notas=[f"Common observed area {float(filas[0]['area_valida_comun_km2']):.0f} km² "
                                              f"({cob:.0%} of the lake); not validated against local data."]))
    # RCM (recurso 9) procesado con scripts/sar/rcm_procesar.py: HH con el umbral central de −17 dB, una fila por escena.
    # Cada escena ve una parte distinta del lago (órbitas ascendente y descendente), así que se publica el porcentaje de la
    # parte observada clasificado como agua: el área absoluta no es comparable entre fechas.
    ruta = carpeta / "rcm_superficie.csv"
    if ruta.is_file():
        entradas.append(ruta)
        filas = sorted((f for f in _leer_csv(ruta) if f["polarizacion"] == "HH" and float(f["umbral_db"]) == -17.0),
                       key=lambda f: f["fecha_utc"])
        if filas:
            invs.append(_investigacion("radar_rcm_cocibolca", "agua", "cocibolca", "Open water seen by RCM radar",
                                       "Share of the lake area seen in each RADARSAT Constellation Mission image that is "
                                       "classified as open water.", "%",
                                       [f["fecha_utc"][:10] for f in filas],
                                       [100 * float(f["area_candidata_agua_km2"]) / float(f["area_observada_lago_km2"]) for f in filas],
                                       {"producto": "RADARSAT Constellation Mission (CSA), ScanSAR 30 m GRD, via EODMS",
                                        "url": "https://donnees-data.asc-csa.gc.ca/en/dataset/rcm"},
                                       recursos=[9, 13], papel="demostracion_registro_corto", frecuencia="escena",
                                       notas=[f"{f['fecha_utc'][:10]}: {float(f['area_candidata_agua_km2']):.0f} of "
                                              f"{float(f['area_observada_lago_km2']):.0f} km² observed classified as water "
                                              f"(HH, −17 dB); not validated against local data." for f in filas]))
    region_canada = carpeta.parents[1] / "regiones_canada.geojson"
    if region_canada.is_file():
        entradas.append(region_canada)
    return invs, contrastes, entradas


# Índices de CHIRPS publicados (data/recursos/hallazgos/generar_hallazgos.py): título, definición y unidad.
INDICES_CHIRPS = {
    "prcptot": ("Annual rainfall since 1981 (CHIRPS)",
                "All the rain that fell in a year, from satellite estimates blended with rain gauges.", "mm"),
    "r10mm": ("Days with heavy rain (≥ 10 mm)", "How many days a year brought at least 10 mm of rain.", "days"),
    "r20mm": ("Days with very heavy rain (≥ 20 mm)", "How many days a year brought at least 20 mm of rain.", "days"),
    "sdii": ("Rain per wet day", "Average rain on days with at least 1 mm: how hard it rains when it rains.", "mm/day"),
    "rx5day": ("Wettest 5 days of the year", "The most rain that fell in any 5 consecutive days of the year.", "mm"),
    "cdd": ("Longest dry spell", "The longest run of days in the year with less than 1 mm of rain.", "days"),
}
VEREDICTO_EN = {"tendencia_detectada": "trend detected", "evidencia_insuficiente": "not enough evidence of a trend",
                "metodos_discrepan": "methods disagree", "datos_insuficientes": "not enough data"}
MESES_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
            "November", "December"]
# Estudios revisados por pares que contrastan series de la app (DOI comprobados en Crossref el 14-11-2026).
ESTUDIOS = {
    "canicula": "Published check: the midsummer drought has grown longer across Central America since 1981, without a "
                "general rise in strength (Anderson et al. 2019, doi:10.1088/1748-9326/ab5023); how it is defined can "
                "change the sign of a trend (Maurer et al. 2022, doi:10.5194/hess-26-1425-2022).",
    "olas_calor": "Method: marine heatwave definition of Hobday et al. 2016 (doi:10.1016/j.pocean.2015.12.014); coral heat "
                  "stress and alerts as computed by NOAA Coral Reef Watch.",
    "mantos": "Published check: Greenland and Antarctica lost ice in 1992–2020, with Greenland losing more "
              "(IMBIE, Otosaka et al. 2023, doi:10.5194/essd-15-1597-2023).",
    "glaciares": "Published check: glaciers worldwide lost mass every year in 2000–2023 and the loss sped up in the second "
                 "half (GlaMBIE Team 2025, Nature, doi:10.1038/s41586-024-08545-z).",
    "acidificacion": "Published check: the surface ocean has become more acidic everywhere since the 1980s as it absorbs "
                     "carbon dioxide (Ma et al. 2023, doi:10.1029/2023GB007765). Data: OceanSODA-ETHZ (Gregor and "
                     "Gruber 2021, doi:10.5194/essd-13-777-2021).",
    "incendios": "Published check: the land burned worldwide each year shrank since the early 2000s, mostly in "
                 "savannas and grasslands turned to farms and pasture (Andela et al. 2017, Science, "
                 "doi:10.1126/science.aal4108). Data: GFED5 burned area (Chen et al. 2023, "
                 "doi:10.5194/essd-15-5227-2023).",
    "estaciones_mallas": "Published check: in 1980–2020, CHIRPS and GPCC show significant drying in eastern Honduras and "
                         "Nicaragua while CRU does not, and a single rain gauge can steer the gridded result "
                         "(González-Méndez et al. 2025, Earth and Space Science, doi:10.1029/2025EA004720).",
    "dias_fuertes_2001_2016": "Published check: a study of 2001–2016 found no trend in days above 10 or 20 mm over "
                              "Nicaragua, matching the result since 2001 here (Journal of Applied Meteorology and "
                              "Climatology 2024, doi:10.1175/JAMC-D-22-0112.1).",
    "racha_ciclones": "Published check: the cluster of storms near the Caribbean coasts of Nicaragua and Costa Rica "
                      "in 2016–2022 was rare, but no human influence was detected at 95% confidence "
                      "(Hidalgo et al. 2025, Natural Hazards, doi:10.1007/s11069-025-07427-5).",
    "lluvia_total_estaciones": "Published check: rain-gauge studies found no significant trend in total rainfall across "
                               "Central America in 1961–2003 (Aguilar et al. 2005, doi:10.1029/2005JD006119) or at 57 "
                               "stations in 1976–2015 (Maldonado et al. 2021, doi:10.15517/rmta.v28i2.42322).",
    "ventanas_cortas": "Published check: trends over windows shorter than about 17 years are easily dominated by "
                       "natural swings such as El Niño (Santer et al. 2011, doi:10.1029/2011JD016263; Foster and "
                       "Rahmstorf 2011, doi:10.1088/1748-9326/6/4/044022).",
    "subregistro_ciclones": "Published check: after correcting for storms missed before satellites, Atlantic major "
                            "hurricanes show no robust long-term rise since the late 1800s (Vecchi et al. 2021, "
                            "Nature Communications, doi:10.1038/s41467-021-24268-5).",
}
BANDAS_GISTEMP = {"global": "Glob", "artico": "64N-90N", "boreal": "44N-64N", "templado_norte": "24N-44N",
                  "tropico_norte": "EQU-24N", "tropico_sur": "24S-EQU", "antartico": "90S-64S"}


def _ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _menos(texto):
    """Signo menos tipográfico, como en las tarjetas de la interfaz."""
    return texto.replace("-", "−")


def _frase_tendencia(t, unidad):
    if t["veredicto"] == "datos_insuficientes":
        return VEREDICTO_EN[t["veredicto"]]
    pendiente = t['sen']['por_decada']
    texto = "0" if abs(pendiente) < 5e-4 else _menos(format(pendiente, '+.3g'))
    return f"{texto} {unidad}/decade, {VEREDICTO_EN[t['veredicto']]}"


def _hallazgos(carpeta, permitir_sintetico):
    """Frecuencia e intensidad de la lluvia con CHIRPS (con y sin ENSO), hielo marino NSIDC y GISTEMP por latitud."""
    carpeta = Path(carpeta)
    ruta_fuentes = carpeta / "fuentes.json"
    if not ruta_fuentes.is_file():
        return [], []
    fuentes = _leer_json(ruta_fuentes, permitir_sintetico)
    invs, entradas = [], [ruta_fuentes]
    chirps = {"producto": "CHIRPS v2.0 daily, 0.25° (UCSB Climate Hazards Center)", "url": fuentes["chirps"]["url"]}
    oni = {}
    ruta = carpeta / "oni_noaa_cpc.csv"
    if ruta.is_file():
        entradas.append(ruta)
        por_anio = {}
        for f in _leer_csv(ruta):
            if f["temporada"] in ("MJJ", "JJA", "JAS", "ASO"):  # temporadas centradas de junio a septiembre
                por_anio.setdefault(int(f["anio"]), []).append(float(f["oni"]))
        oni = {a: sum(v) / len(v) for a, v in por_anio.items() if len(v) == 4}

    def notas_lluvia(anios, valores, unidad, aviso=" CHIRPS blends rain-gauge reports whose number changed over time, "
                                                   "so a trend seen only in the full record should be confirmed."):
        notas = []
        pares = [(a, v) for a, v in zip(anios, valores) if a in oni]
        if len(pares) >= MIN_ANIOS_TENDENCIA:
            a, y = zip(*pares)
            x = [oni[k] for k in a]
            mx, my = sum(x) / len(x), sum(y) / len(y)
            sxx = sum((u - mx) ** 2 for u in x)
            b = sum((u - mx) * (v - my) for u, v in zip(x, y)) / sxx
            r2 = b * b * sxx / sum((v - my) ** 2 for v in y)
            sin_enso = [v - b * (u - mx) for u, v in zip(x, y)]
            t = tendencia_compacta(a, sin_enso, unidad)
            notas.append(f"El Niño and La Niña (NOAA ONI, June–September) explain {r2:.0%} of the year-to-year swings. "
                         f"With their effect removed: {_frase_tendencia(t, unidad)}.")
        desde_2001 = [(a, v) for a, v in zip(anios, valores) if a >= 2001]
        t = tendencia_compacta(*zip(*desde_2001), unidad)
        notas.append(f"Since 2001 only: {_frase_tendencia(t, unidad)}.{aviso}")
        return notas

    ruta = carpeta / "chirps_indices_regiones.csv"
    if ruta.is_file():
        entradas.append(ruta)
        series = {}
        for f in _leer_csv(ruta):
            series.setdefault((f["region"], f["indice"]), []).append((int(f["anio"]), float(f["valor"])))
        for region in ("NIC", "pacifico", "central", "caribe"):
            for indice, (titulo, definicion, unidad) in INDICES_CHIRPS.items():
                puntos = sorted(series.get((region, indice), []))
                if not puntos:
                    continue
                anios, valores = [a for a, _ in puntos], [v for _, v in puntos]
                notas = notas_lluvia(anios, valores, unidad)
                if indice in ("r10mm", "r20mm"):
                    notas.append(ESTUDIOS["dias_fuertes_2001_2016"])
                if region in ("NIC", "caribe"):
                    notas.append(ESTUDIOS["estaciones_mallas"])
                if indice == "prcptot":
                    notas.append(ESTUDIOS["lluvia_total_estaciones"])
                invs.append(_investigacion(f"chirps_{indice}_{region}", "lluvia", region, titulo, definicion, unidad,
                                           anios, valores, chirps, notas=notas))
    ruta = carpeta / "chirps_acumulado_parcial.csv"
    if ruta.is_file():
        entradas.append(ruta)
        por_region = {}
        for f in _leer_csv(ruta):
            por_region.setdefault(f["region"], []).append(f)
        for region in ("NIC", "pacifico", "central", "caribe"):
            filas = sorted(por_region.get(region, []), key=lambda f: int(f["anio"]))
            if not filas:
                continue
            anios, valores = [int(f["anio"]) for f in filas], [float(f["mm"]) for f in filas]
            hasta = filas[-1]["hasta"]
            mes = MESES_EN[int(hasta[:2]) - 1]
            normal = [v for a, v in zip(anios, valores) if 1991 <= a <= 2020]
            normal = sum(normal) / len(normal)
            ultimo = anios[-1]
            puesto = sorted(valores).index(valores[-1]) + 1
            notas = [f"{ultimo}: {valores[-1]:.0f} mm from 1 January to {int(hasta[3:])} {mes}, "
                     f"{_menos(format(valores[-1] / normal - 1, '+.0%'))} compared with 1991–2020 and the "
                     f"{'driest' if puesto == 1 else _ordinal(puesto) + ' driest'} of {len(anios)} years."]
            invs.append(_investigacion(f"chirps_parcial_{region}", "lluvia", region, f"Rainfall January–{mes}, {anios[0]}–{ultimo}",
                                       f"Rain from 1 January to {int(hasta[3:])} {mes} of each year, so the current year "
                                       f"can be compared with every past year.", "mm", anios, valores, chirps,
                                       notas=notas + notas_lluvia(anios, valores, "mm")))

    ruta = carpeta / "nsidc_extension_marzo_septiembre.csv"
    if ruta.is_file():
        entradas.append(ruta)
        nsidc = {"producto": "NSIDC Sea Ice Index, Version 4 (G02135)", "url": fuentes["nsidc"]["url"]}
        hielo = {}
        for f in _leer_csv(ruta):
            hielo.setdefault((f["hemisferio"], int(f["mes"])), []).append((int(f["anio"]), float(f["extension_mkm2"])))
        etiquetas = {("N", 9): ("artico", "September sea ice (yearly minimum)"), ("N", 3): ("artico", "March sea ice (yearly maximum)"),
                     ("S", 9): ("antartico", "September sea ice (yearly maximum)"), ("S", 3): ("antartico", "March sea ice (yearly minimum)")}
        for clave in (("N", 9), ("N", 3), ("S", 9), ("S", 3)):
            puntos = sorted(hielo.get(clave, []))
            if not puntos:
                continue
            lugar, titulo = etiquetas[clave]
            anios, valores = [a for a, _ in puntos], [v for _, v in puntos]
            puesto = sorted(valores).index(valores[-1]) + 1
            notas = [f"{anios[-1]}: {valores[-1]:.2f} million km², the {'lowest' if puesto == 1 else _ordinal(puesto) + ' lowest'} "
                     f"of {len(anios)} years."]
            if lugar == "antartico":
                t = tendencia_compacta([a for a in anios if a >= 2016], [v for a, v in puntos if a >= 2016], "million km²")
                notas.append(f"Antarctic sea ice grew slowly until 2015 and has been low since 2016. "
                             f"Since 2016 only: {_frase_tendencia(t, 'million km²')}; the record is still short.")
            id_ = f"hielo_{MESES_EN[clave[1] - 1].lower()}_{lugar}"
            definicion = "Ocean area where at least 15% of the surface is covered by ice, monthly mean."
            invs.append(_investigacion(id_, "polos", lugar, titulo, definicion, "million km²", anios, valores, nsidc, notas=notas))
            if clave == ("S", 9):
                # El mismo registro partido en el cambio de régimen: la conclusión depende del periodo elegido.
                for sufijo, desde, hasta, texto in (("_1979_2015", anios[0], 2015, f"{anios[0]}–2015"),
                                                    ("_desde_2016", 2016, anios[-1], "since 2016")):
                    tramo = [(a, v) for a, v in puntos if desde <= a <= hasta]
                    invs.append(_investigacion(id_ + sufijo, "polos", lugar, f"{titulo}, {texto} only", definicion,
                                               "million km²", [a for a, _ in tramo], [v for _, v in tramo], nsidc,
                                               notas=["The same record split where Antarctic sea ice changed behaviour. "
                                                      "Compare the verdict with the full record and with the other period."]))

    ruta = carpeta / "gistemp_bandas.csv"
    if ruta.is_file():
        entradas.append(ruta)
        gistemp = {"producto": "NASA GISS GISTEMP v4, latitude-band means", "url": "https://data.giss.nasa.gov/gistemp/"}
        filas = [f for f in _leer_csv(ruta) if int(f["anio"]) >= 1981]
        for lugar, col in BANDAS_GISTEMP.items():
            anios, valores = [int(f["anio"]) for f in filas], [float(f[col]) for f in filas]
            invs.append(_investigacion(f"temperatura_banda_{lugar}", "temperatura", lugar,
                                       "Air temperature anomaly" + ("" if lugar == "global" else " (latitude band)"),
                                       "How much warmer or cooler the air near the surface was than the 1951–1980 average, "
                                       "over land and ocean at every longitude in this band.", "°C", anios, valores, gistemp))
        # Ventana corta que empieza en el El Niño de 1997–98: el ejemplo clásico de elegir mal el periodo.
        tramo = [f for f in filas if 1998 <= int(f["anio"]) <= 2012]
        largo = tendencia_compacta([int(f["anio"]) for f in filas], [float(f["Glob"]) for f in filas], "°C")
        invs.append(_investigacion("temperatura_banda_global_1998_2012", "temperatura", "global",
                                   "Air temperature anomaly, 1998–2012 only",
                                   "The same global record, cut to the years often called the warming 'hiatus'. The "
                                   "window starts right after the strong El Niño of 1997–98.", "°C",
                                   [int(f["anio"]) for f in tramo], [float(f["Glob"]) for f in tramo], gistemp,
                                   notas=[f"Full record since {filas[0]['anio']}: {_frase_tendencia(largo, '°C')}. "
                                          "Compare the size of the slope, not only the verdict.",
                                          ESTUDIOS["ventanas_cortas"]]))

    ruta = carpeta / "ersst_caribe_nicaragua.csv"
    if ruta.is_file():
        entradas.append(ruta)
        ersst = {"producto": "NOAA ERSSTv5 sea surface temperature, 2°", "url": fuentes["ersst"]["url"]}
        filas = [(int(f["anio"]), int(f["mes"]), float(f["sst_c"])) for f in _leer_csv(ruta)]
        por_anio = {}
        for a, _, v in filas:
            por_anio.setdefault(a, []).append(v)
        anios = [a for a in sorted(por_anio) if len(por_anio[a]) == 12]
        valores = [sum(por_anio[a]) / 12 for a in anios]
        clima = {m: sum(v for a, mm, v in filas if mm == m and 1991 <= a <= 2020) / 30 for m in range(1, 13)}
        anomalias = [(a, m, v - clima[m]) for a, m, v in filas]
        base = sorted(x for a, _, x in anomalias if 1991 <= a <= 2020)
        p90 = base[int(round(0.9 * (len(base) - 1)))]
        calidos = {a: sum(1 for b, _, x in anomalias if b == a and x > p90) for a in anios}
        record = max(anios, key=lambda a: valores[anios.index(a)])
        ultimo, meses = filas[-1][0], [x for a, _, x in anomalias if a == filas[-1][0]]
        notas = [f"Warmest year: {record}."]
        if ultimo not in anios:
            notas.append(f"{ultimo} so far ({MESES_EN[0]}–{MESES_EN[filas[-1][1] - 1]}): "
                         f"{_menos(format(sum(meses) / len(meses), '+.2f'))} °C compared with 1991–2020.")
        invs.append(_investigacion("sst_mar_caribe_nic", "costa", "mar_caribe_nic", "Sea surface temperature",
                                   "Yearly mean temperature of the top layer of the sea, reconstructed from ships, buoys "
                                   "and satellites.", "°C", anios, valores, ersst,
                                   notas=notas + notas_lluvia(anios, valores, "°C", aviso="")))
        invs.append(_investigacion("meses_calidos_mar_caribe_nic", "costa", "mar_caribe_nic", "Unusually warm months",
                                   f"Months each year warmer than 9 in 10 months of 1991–2020 for the time of year "
                                   f"(more than {p90:.2f} °C above normal). Daily data would be needed to count marine "
                                   f"heatwaves.", "months", anios, [calidos[a] for a in anios], ersst,
                                   notas=[f"{max(anios, key=calidos.get)}: {max(calidos.values())} of 12 months."]))

    ruta = carpeta / "psmsl_nivel_mar_anual.csv"
    if ruta.is_file():
        entradas.append(ruta)
        psmsl = {"producto": "PSMSL tide-gauge annual means (Revised Local Reference)", "url": fuentes["psmsl"]["url"]}
        por_estacion = {}
        for f in _leer_csv(ruta):
            por_estacion.setdefault(f["estacion"], []).append((int(f["anio"]), float(f["nivel_mm"])))
        for estacion, lugar in MAREOGRAFOS.items():
            puntos = sorted(por_estacion.get(estacion, []))
            if not puntos:
                continue
            anios = [a for a, _ in puntos]
            base = [v for a, v in puntos if 1991 <= a <= 2020] or [v for _, v in puntos]
            valores = [v - sum(base) / len(base) for _, v in puntos]  # respecto de la media 1991–2020 de la estación
            reciente = [(a, v) for a, v in zip(anios, valores) if a >= 1981]
            t = tendencia_compacta(*zip(*reciente), "mm")
            invs.append(_investigacion(f"nivel_mar_{lugar}", "costa", lugar, "Sea level at the tide gauge",
                                       "Yearly mean sea level measured against the land at the gauge, compared with its "
                                       "1991–2020 average. It includes any rise or sinking of the land itself.", "mm",
                                       anios, valores, psmsl,
                                       notas=[f"Since 1981 only: {_frase_tendencia(t, 'mm')}.",
                                              "The long tide-gauge records on Central America's coasts end between 1966 "
                                              "and 2000; newer gauges such as Limón (Costa Rica, since 2010) are still "
                                              "too short. The nearest long records are in Panama and the northern Caribbean."]))

    ruta = carpeta / "ibtracs_cerca_nicaragua.csv"
    if ruta.is_file():
        entradas.append(ruta)
        ibtracs = {"producto": "NOAA IBTrACS v04r01 storm tracks", "url": fuentes["ibtracs"]["url"]}
        tormentas = [f for f in _leer_csv(ruta) if int(f["temporada"]) >= 1981]
        ultimo = max(int(f["temporada"]) for f in tormentas)
        anios = list(range(1981, ultimo + 1))
        for umbral, sufijo, titulo, definicion in (
                (34, "tormentas", "Tropical storms and hurricanes nearby",
                 "Storms per year with winds of at least 34 knots (63 km/h) while near Nicaragua."),
                (64, "huracanes", "Hurricanes nearby",
                 "Storms per year with hurricane winds of at least 64 knots (119 km/h) while near Nicaragua.")):
            fuertes = [f for f in tormentas if float(f["viento_max_kt"]) >= umbral]
            notas = []
            if umbral == 64:
                notas.append("Hurricanes: " + ", ".join(f"{f['nombre'].title().replace(':', '/')} {f['temporada']}" for f in fuertes) + ".")
            notas.append("Only a few storms come this close each year, so a trend would need a much longer record "
                         "to stand out.")
            notas.append(ESTUDIOS["racha_ciclones"])
            if str(ultimo) == fuentes["ibtracs"]["generado_utc"][:4]:
                notas.append(f"The {ultimo} season was still running when the tracks were downloaded "
                             f"({fuentes['ibtracs']['generado_utc'][:10]}).")
            invs.append(_investigacion(f"ciclones_{sufijo}_NIC", "ciclones", "NIC", titulo, definicion, "storms", anios,
                                       [sum(1 for f in fuertes if int(f["temporada"]) == a) for a in anios], ibtracs,
                                       notas=notas))
        # Registro completo sin corregir: antes de los satélites se perdían tormentas en mar abierto.
        historicas = [f for f in _leer_csv(ruta) if int(f["temporada"]) >= 1851 and float(f["viento_max_kt"]) >= 34]
        largo = list(range(1851, ultimo + 1))
        invs.append(_investigacion("ciclones_tormentas_NIC_1851", "ciclones", "NIC",
                                   "Tropical storms and hurricanes nearby, raw record since 1851",
                                   "The same count as above, back to 1851, with no correction for storms missed before "
                                   "satellites and aircraft reconnaissance.", "storms", largo,
                                   [sum(1 for f in historicas if int(f["temporada"]) == a) for a in largo], ibtracs,
                                   notas=["Compare with the record since 1981: an older record can suggest a rise "
                                          "that partly comes from better detection.", ESTUDIOS["subregistro_ciclones"]]))
    n_inv, n_ent = _mundo(carpeta, fuentes, chirps, notas_lluvia)
    from .recursos_europa_africa import europa_africa
    e_inv, e_ent = europa_africa(carpeta); n_inv += e_inv; n_ent += e_ent
    return invs + n_inv, entradas + n_ent


def _serie(filas, clave, valor):
    """{clave: [(anio, valor), …]} ordenado, a partir de filas CSV."""
    out = {}
    for f in filas:
        out.setdefault(f[clave], []).append((int(f["anio"]), float(f[valor])))
    return {k: sorted(v) for k, v in out.items()}


def _anuales_mensuales(filas, columna, minimo=12):
    """Media anual de una columna mensual («mes» = AAAA-MM) solo con años que tienen al menos `minimo` meses."""
    por = {}
    for f in filas:
        if f[columna] not in ("", "nan"):
            por.setdefault(int(f["mes"][:4]), []).append(float(f[columna]))
    return {a: sum(v) / len(v) for a, v in sorted(por.items()) if len(v) >= minimo}


def _mundo(carpeta, fuentes, chirps, notas_lluvia):
    """Canícula, olas de calor marinas, GRACE, glaciares y acidificación (generar_hallazgos/oceano/mundo.py)."""
    invs, entradas = [], []
    ruta = carpeta / "chirps_canicula_regiones.csv"
    if ruta.is_file():
        entradas.append(ruta)
        filas = _leer_csv(ruta)
        for region in ("NIC", "pacifico", "central"):
            propias = sorted((f for f in filas if f["region"] == region), key=lambda f: int(f["anio"]))
            if not propias:
                continue
            detectadas = sum(int(f["detectada"]) for f in propias)
            comun = [f"Midsummer drought found in {detectadas} of {len(propias)} years with an objective method "
                     f"(two rainfall peaks and the dip between them, CHIRPS daily rain averaged over the region).",
                     ESTUDIOS["canicula"]]
            for id_, titulo, definicion, unidad, valor, solo_detectadas in (
                    ("duracion", "Midsummer drought (canícula) length",
                     "Days of the summer dip in rain between the two rainy-season peaks (0 when there was no clear dip).",
                     "days", "duracion_dias", False),
                    ("intensidad", "Midsummer drought (canícula) strength",
                     "How much the rain drops in the dip compared with the two peaks (0 = no drop, 1 = no rain).",
                     "fraction", "intensidad", True),
                    ("lluvia_fija", "Rain from 15 July to 15 August",
                     "Rain in the fixed window when the midsummer drought usually happens.", "mm", "lluvia_15jul_15ago_mm",
                     False)):
                usadas = [f for f in propias if f[valor] != "" and (int(f["detectada"]) or not solo_detectadas)]
                anios, valores = [int(f["anio"]) for f in usadas], [float(f[valor]) for f in usadas]
                invs.append(_investigacion(f"canicula_{id_}_{region}", "lluvia", region, titulo, definicion, unidad,
                                           anios, valores, chirps, notas=comun + notas_lluvia(anios, valores, unidad)))

    ruta = carpeta / "crw_caribe_nicaragua_anual.csv"
    if ruta.is_file() and "crw" in fuentes:
        entradas.append(ruta)
        crw, estado = {"producto": fuentes["crw"]["producto"], "url": fuentes["crw"]["url"]}, fuentes["crw"]
        filas = sorted(_leer_csv(ruta), key=lambda f: int(f["anio"]))
        anios = [int(f["anio"]) for f in filas]
        ahora = (f"Latest day, {estado['ultimo_dia']}: {estado['dhw_ultimo']:.1f} °C-weeks of heat stress, alert level "
                 f"{max(0, estado['alerta_ultima'] - 2)} of 2 for coral bleaching.")
        for id_, titulo, definicion, unidad, valor in (
                ("olas_calor", "Days in a marine heatwave",
                 "Days of the year inside a marine heatwave: at least 5 days in a row warmer than 9 in 10 days of "
                 "1991–2020 for that time of year.", "days", "dias_ola_calor_marina"),
                ("dhw", "Peak coral heat stress",
                 "Highest Degree Heating Weeks of the year: heat above the usual warmest month, accumulated over 12 "
                 "weeks. Above 4 °C-weeks bleaching is likely; above 8, widespread bleaching and death.", "°C-weeks",
                 "dhw_max_c_semanas"),
                ("alerta", "Days on coral bleaching alert",
                 "Days of the year at NOAA bleaching Alert Level 1 or 2.", "days", "dias_alerta_1_o_mas")):
            valores = [float(f[valor]) for f in filas]
            notas = [ahora] if id_ != "olas_calor" else [
                ahora, f"{estado['ultimo_dia'][:4]} so far: {estado['dias_ola_calor_anio_en_curso']} days in a marine "
                       "heatwave.", "The threshold is fixed to 1991–2020, so it includes the long-term warming of the "
                       "sea: more heatwave days mean both a warmer background and more extreme spells."]
            invs.append(_investigacion(f"arrecifes_{id_}", "costa", "arrecifes_nic", titulo, definicion, unidad, anios,
                                       valores, crw, notas=notas + [ESTUDIOS["olas_calor"]]))

    ruta = carpeta / "grace_csr_mensual.csv"
    if ruta.is_file():
        entradas.append(ruta)
        grace = {"producto": "GRACE/GRACE-FO mascons, CSR RL06.03 (University of Texas at Austin)",
                 "url": "https://www2.csr.utexas.edu/grace/RL06_mascons.html"}
        filas = _leer_csv(ruta)
        ultimo = max(int(f["mes"][:4]) for f in filas)
        for lugar, columna, nombre in (("groenlandia", "groenlandia_gt", "Greenland"), ("antartico", "antartida_gt", "Antarctica")):
            medias = _anuales_mensuales(filas, columna, minimo=9)
            anios = [a for a in medias if a - 1 in medias and a < ultimo]
            cambios = [medias[a] - medias[a - 1] for a in anios]
            invs.append(_investigacion(f"grace_masa_{lugar}", "polos", lugar, f"{nombre} ice-sheet mass change per year",
                                       "Change in the mass of the ice sheet from one year to the next, weighed by the "
                                       "GRACE and GRACE-FO gravity satellites. Below zero means ice lost.", "Gt", anios,
                                       cambios, grace,
                                       notas=[f"Average {sum(cambios) / len(cambios):+.0f} Gt per year over "
                                              f"{anios[0]}–{anios[-1]} (1 Gt = 1 billion tonnes; 360 Gt raise the sea by "
                                              "about 1 mm).", "The trend asks whether the yearly loss is growing, not "
                                              "whether ice is being lost. Years 2017–2018 are missing: the gap between "
                                              "the two missions.", ESTUDIOS["mantos"]]))
        medias = _anuales_mensuales(filas, "nicaragua_agua_cm", minimo=9)
        anios = [a for a in medias if a < ultimo]
        parcial = [float(f["nicaragua_agua_cm"]) for f in filas if f["mes"].startswith(str(ultimo))]
        invs.append(_investigacion("grace_agua_NIC", "agua", "NIC", "Total water stored on land (GRACE)",
                                   "All water held in soil, rivers, lakes and aquifers over Nicaragua, compared with its "
                                   "2004–2009 average and weighed by gravity satellites.", "cm", anios,
                                   [medias[a] for a in anios], grace,
                                   notas=[f"{ultimo} so far ({len(parcial)} months): {_menos(format(sum(parcial) / len(parcial), '+.1f'))} cm; "
                                          "the wettest months are still missing.", "Gravity satellites see blocks of about "
                                          "300 km, so this is a national total, not a map of wells."]))

    ruta = carpeta / "glambie_america_anual.csv"
    if ruta.is_file():
        entradas.append(ruta)
        glambie = {"producto": "GlaMBIE 1.0.0 glacier mass balance (World Glacier Monitoring Service)",
                   "url": "https://doi.org/10.5904/wgms-glambie-2024-07"}
        for region, puntos in _serie(_leer_csv(ruta), "region", "cambio_masa_gt").items():
            lugar = "glaciares_" + {"global": "global", "alaska": "alaska", "western_canada_us": "oeste_canada_eeuu",
                                    "arctic_canada_north": "artico_canada_norte", "arctic_canada_south": "artico_canada_sur",
                                    "greenland_periphery": "groenlandia_periferia", "low_latitudes": "latitudes_bajas",
                                    "southern_andes": "andes_sur"}[region]
            anios, valores = [a for a, _ in puntos], [v for _, v in puntos]
            invs.append(_investigacion(f"glaciares_{region}", "polos", lugar, "Glacier mass change per year",
                                       "How much ice the glaciers of the region gained or lost each year. Below zero "
                                       "means ice lost.", "Gt", anios, valores, glambie,
                                       notas=[f"Total {anios[0]}–{anios[-1]}: {_menos(format(sum(valores), '+.0f'))} Gt; "
                                              f"{sum(1 for v in valores if v < 0)} of {len(valores)} years were losses.",
                                              "The trend asks whether the yearly loss is growing.", ESTUDIOS["glaciares"]]))

    ruta = carpeta / "oceansoda_caribe_mensual.csv"
    if ruta.is_file():
        entradas.append(ruta)
        soda = {"producto": "OceanSODA-ETHZ v2025 surface ocean carbonate system (NOAA NCEI)",
                "url": "https://www.ncei.noaa.gov/data/oceans/ncei/ocads/data/0220059/"}
        filas = _leer_csv(ruta)
        for zona in ("mar_caribe_nic", "mar_caribe"):
            propias = [f for f in filas if f["zona"] == zona]
            for columna, id_, titulo, definicion, unidad in (
                    ("ph_total", "ph", "Sea surface pH",
                     "Acidity of the sea surface: lower pH means more acidic water. 0.1 lower is about 26% more acid.",
                     "pH"),
                    ("omega_aragonito", "aragonito", "Aragonite saturation",
                     "How easily corals and shellfish can build their skeletons from the water. Below about 3 reefs "
                     "struggle to grow.", "Ω")):
                medias = _anuales_mensuales(propias, columna)
                anios = list(medias)
                invs.append(_investigacion(f"acidez_{id_}_{zona}", "costa", zona, titulo, definicion, unidad, anios,
                                           [medias[a] for a in anios], soda, notas=[ESTUDIOS["acidificacion"]]))

    ruta = carpeta / "gfed5_area_quemada_mensual.csv"
    if ruta.is_file():
        entradas.append(ruta)
        gfed = {"producto": "GFED5 burned area, MODIS era (Global Fire Emissions Database)",
                "url": "https://doi.org/10.5281/zenodo.7668424"}
        filas = _leer_csv(ruta)
        for zona, lugar in (("NIC", "NIC"), ("centroamerica", "centroamerica"), ("global", "planeta")):
            por = {}
            for f in filas:
                if f["zona"] == zona:
                    por.setdefault(int(f["mes"][:4]), []).append(float(f["area_quemada_km2"]))
            anios = [a for a, v in sorted(por.items()) if len(v) == 12]
            valores = [round(sum(por[a]), 1) for a in anios]
            pico = max(zip(valores, anios))
            invs.append(_investigacion(f"incendios_area_{zona}", "vegetacion", lugar, "Burned area per year",
                                       "Land burned by fires during the year, mapped from satellites (MODIS) at about "
                                       "25 km. Includes wildfires, farm burning and fires used to clear forest.",
                                       "km²", anios, valores, gfed,
                                       notas=[f"Most burned: {pico[1]}, {pico[0]:,.0f} km².",
                                              "One very dry or very wet year moves the total a lot, so 20 years is "
                                              "short for a fire trend.", ESTUDIOS["incendios"]]))
    return invs, entradas


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
    if all(k in ids for k in ("chirps_prcptot_NIC", "chirps_r10mm_NIC", "chirps_rx5day_caribe", "chirps_parcial_pacifico")):
        total, fuertes, caribe, parcial = (ids[k] for k in ("chirps_prcptot_NIC", "chirps_r10mm_NIC", "chirps_rx5day_caribe",
                                                            "chirps_parcial_pacifico"))
        pico = max(zip(caribe["valores"], caribe["tiempos"]))[1]

        def reciente(x, unidad):
            pares = [(a, v) for a, v in zip(x["tiempos"], x["valores"]) if a >= 2001]
            return f" Since 2001 only: {_frase_tendencia(tendencia_compacta(*zip(*pares), unidad), unidad)}."
        demos.append({"id": "frecuencia_lluvia", "titulo_en": "Same total, different rain?", "pasos": [
            {"investigacion": total["id"], "texto_en": f"A longer record: rain gauges and satellites since {total['tiempos'][0]}. "
                                                       f"Total yearly rain over Nicaragua: {VEREDICTO_EN[total['tendencia']['veredicto']]}."},
            {"investigacion": total["id"], "ver": "veredicto", "texto_en": "Year-to-year swings are large, and El Niño explains part of them. The notes show the result with El Niño removed."},
            {"investigacion": fuertes["id"], "texto_en": f"How often it rains hard is another question. Days with at least 10 mm: "
                                                         f"{_frase_tendencia(fuertes['tendencia'], 'days')}." + reciente(fuertes, "days")},
            {"investigacion": caribe["id"], "texto_en": f"On the Caribbean coast, the wettest 5-day spell of each year: "
                                                        f"{_frase_tendencia(caribe['tendencia'], 'mm')}." + reciente(caribe, "mm") +
                                                        f" The largest was in {pico}."},
            {"investigacion": parcial["id"], "texto_en": parcial["notas"][0] + " That is an El Niño year."},
            {"investigacion": parcial["id"], "ver": "aprender", "ancla": "aprender-variabilidad",
             "texto_en": "Why a record-dry year does not make a trend on its own."}]})
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
    usados.add(7)  # Artículo de Medium: base de «Other trend tests» en «Learn» (leído el 13-11-2026).
    if hay_csa:
        usados.add(12)  # textos de las categorías de vegetación y agua.
    usos = {
        1: "Area-averaged NASA time series and point series used as data sources and cross-checks.",
        2: "GLDAS land-model hydrology at sample points.",
        3: "Regional averages of MODIS vegetation, land temperature and evapotranspiration, and SMAP soil moisture.",
        4: "Weather-station records (GSOM, GHCN-Daily) to cross-check satellite and reanalysis data.",
        5: "Method for chlorophyll time series and significance tests in river-influenced coastal waters.",
        6: "Independent gridded datasets to cross-check rainfall trends.",
        7: "Seasonal Mann–Kendall and unit-root tests, explained in the Learn section.",
        8: "Plain-language guide to p-values, confidence intervals and common misreadings (Learn section).",
        9: "Radar images of water extent.",
        10: "Boundary of the Canadian Prairies ecozone used as a contrast region.",
        11: "Lake water-surface elevation for Lake Nicaragua and Lake Managua.",
        12: "Framing of the vegetation & ecosystems and water-bodies questions.",
        13: "Workflow to map surface water from radar images.",
    }
    series_appeears = [i for i in invs if RECURSO_TIERRA["appeears"] in i["recursos"]]
    if series_appeears and all(i["id"].startswith("humedad_smap_superficial_") for i in series_appeears):
        usos[3] = "Regional soil moisture from NASA SMAP Level 4."
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
    n_inv, n_ent = _hallazgos(datos / "recursos" / "hallazgos", permitir_sintetico)
    invs += t_inv + c_inv + s_inv + k_inv + h_inv + n_inv
    contrastes = c_con + s_con + k_con + h_con
    entradas += t_ent + c_ent + s_ent + k_ent + h_ent + n_ent
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
