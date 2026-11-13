"""Nivel de los lagos Cocibolca (Nicaragua) y Xolotlán (Managua) por altimetría satelital.

Dos vías:
- G-REALM (Global Reservoir and Lake Monitor, NASA GSFC; antes en USDA/IPAD): series de 10 días desde 1992
  (TOPEX/Poseidon, Jason-1/2/3, Sentinel-6A), sin cuenta. Cocibolca es el objetivo **000351 «Nicaragua»**
  (11,79° N, 85,71° O) dentro de https://earth.gsfc.nasa.gov/gwm/zip/lake.10.tar.gz (`lake000351.10d.2.txt`).
  Formato GSFC de 16 columnas: la 3 es la fecha (AAAAMMDD), la 6 la variación respecto del nivel medio (m;
  999,99 = sin dato), la 7 su error (m) y la 15 la altura en el datum EGM2008 (m s. n. m.; 9999,99 = sin dato).
  Xolotlán no figura en el catálogo de G-REALM (consulta del 12-11-2026).
- SWOT (NASA/CNES, datos científicos desde julio de 2023): API Hydrocron de PO.DAAC, sin cuenta, por
  identificador de la Prior Lake Database (PLD). `lake_id` encontrados en el producto
  SWOT_L2_HR_LakeSP_prior 2.0 (pasada 027_522, 01-02-2025): Cocibolca **7530096743** («LAGO DE
  NICARAGUA;NICARAGUA», área de referencia PLD 7 808 km²) y Xolotlán **7530093763** («MANAGUA», 1 080 km²).
  La `wse` de LakeSP está referida al geoide EGM2008, igual que la columna 15 de G-REALM.

SWOT empieza en 2023: su serie es demasiado corta para la tendencia 2001–2024. Se usa como contraste y
validación de G-REALM en el periodo común, no como tendencia.

Referencia para validar (análisis geocientífico del proyecto): Cocibolca 32,91 m s. n. m. y Xolotlán 42,73 m
en octubre de 2010 (INETER); fuertes descensos en 2014–2016.

Consultar Hydrocron y escribir data/recursos/csa/ (requiere red):
    python -m clima_nic.fuentes.lagos swot --fin 2026-11-12
"""
import csv
import io
import json
import re
import tarfile
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .base import Adaptador, SerieRegional, descargar_url

# ------------------------------------------------------------------ G-REALM

URL_TAR_GREALM = "https://earth.gsfc.nasa.gov/gwm/zip/lake.10.tar.gz"
GREALM_IDS = {"cocibolca": "000351"}
_LINEA_GSFC = re.compile(r"^[A-Z0-9]{4,6}\s+\d+\s+\d{8}\s")


def leer_grealm_gsfc(texto):
    """Formato GSFC de 16 columnas → lista de dicts {fecha, mision, variacion_m, error_m, altura_egm2008_m}.

    Excluye los rellenos (variación ≥ 999 o altura ≥ 9999) y las líneas de cabecera."""
    obs = []
    for linea in texto.splitlines():
        p = linea.split()
        if len(p) < 15 or not _LINEA_GSFC.match(linea.strip()):
            continue
        try:
            var, err, alt = float(p[5]), float(p[6]), float(p[14])
        except ValueError:
            continue
        if abs(var) >= 999 or alt >= 9999:
            continue
        obs.append({"fecha": f"{p[2][:4]}-{p[2][4:6]}-{p[2][6:]}", "mision": p[0], "variacion_m": var,
                    "error_m": err, "altura_egm2008_m": alt})
    return obs


def leer_grealm(texto):
    """Parser tolerante del texto de G-REALM: devuelve (fechas 'AAAA-MM-DD', alturas m).

    Con el formato GSFC de 16 columnas devuelve la altura EGM2008 (columna 15). Con el formato antiguo acepta
    líneas con fecha AAAAMMDD o fecha decimal seguida de la altura; ignora encabezados y rellenos (≥ 999)."""
    if any(_LINEA_GSFC.match(l.strip()) for l in texto.splitlines()):
        obs = leer_grealm_gsfc(texto)
        return [o["fecha"] for o in obs], [o["altura_egm2008_m"] for o in obs]
    fechas, alturas = [], []
    for linea in texto.splitlines():
        partes = linea.split()
        if len(partes) < 2 or not re.match(r"^\d", partes[0]):
            continue
        try:
            if re.fullmatch(r"\d{8}", partes[0]):
                f = f"{partes[0][:4]}-{partes[0][4:6]}-{partes[0][6:]}"
                h = float(partes[-1] if len(partes) == 2 else partes[1])
            else:
                dec = float(partes[0])
                anio = int(dec)
                dia = int(round((dec - anio) * 365.25))
                f = str(np.datetime64(f"{anio}-01-01") + np.timedelta64(dia, "D"))
                h = float(partes[1])
        except ValueError:
            continue
        if abs(h) >= 999:
            continue
        fechas.append(f)
        alturas.append(h)
    return fechas, alturas


def extraer_grealm_de_tar(ruta_tar, id_lago, destino):
    """Extrae solo el texto del lago del archivo completo de G-REALM (sin descomprimir el resto)."""
    with tarfile.open(ruta_tar, "r:gz") as t:
        datos = t.extractfile(t.getmember(f"lake{id_lago}.10d.2.txt")).read()
    Path(destino).write_bytes(datos)
    return Path(destino)


# ------------------------------------------------------------------ SWOT (Hydrocron)

HYDROCRON = "https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries"
SWOT_LAKE_IDS = {"cocibolca": "7530096743", "xolotlan": "7530093763"}
CAMPOS_HYDROCRON = ("lake_id", "time_str", "wse", "wse_u", "area_total", "quality_f", "partial_f",
                    "dark_frac", "ice_clim_f", "xovr_cal_q", "cycle_id", "pass_id")
RELLENO = -999999999999.0
# quality_f de LakeSP: 0 bueno, 1 sospechoso, 2 degradado, 3 malo. Por defecto se aceptan 0 y 1.
CALIDAD_MAX = 1
INICIO_SWOT = "2023-07-26"  # inicio de la órbita científica de 21 días
ANIOS_MIN_TENDENCIA = 10    # por debajo de esto no se calcula tendencia


def es_lake_id(valor):
    """lake_id de la PLD: 10 dígitos (continente, cuenca Pfafstetter, número y tipo en el último dígito)."""
    return bool(re.fullmatch(r"[1-9]\d{9}", str(valor)))


def url_hydrocron(lake_id, inicio, fin, campos=CAMPOS_HYDROCRON, salida="csv"):
    if not es_lake_id(lake_id):
        raise ValueError(f"lake_id inválido: {lake_id!r} (se esperan 10 dígitos)")
    q = {"feature": "PriorLake", "feature_id": str(lake_id), "start_time": f"{inicio}T00:00:00Z",
         "end_time": f"{fin}T00:00:00Z", "output": salida, "fields": ",".join(campos)}
    return f"{HYDROCRON}?{urllib.parse.urlencode(q, safe=',:')}"


def leer_hydrocron(texto):
    """Respuesta de Hydrocron (sobre JSON con `results.csv`, o el CSV directo) → lista de dicts.

    Convierte a número wse, wse_u, area_total, dark_frac, quality_f, partial_f, ice_clim_f, xovr_cal_q y quita
    duplicados exactos (Hydrocron repite filas cuando un lago cae en dos granos de la misma pasada)."""
    texto = texto.strip()
    if texto.startswith("{"):
        sobre = json.loads(texto)
        texto = sobre.get("results", {}).get("csv", "")
    filas, vistos = [], set()
    for f in csv.DictReader(io.StringIO(texto)):
        clave = tuple(f.get(k) for k in ("lake_id", "time_str", "cycle_id", "pass_id", "wse"))
        if clave in vistos:
            continue
        vistos.add(clave)
        for k in ("wse", "wse_u", "area_total", "dark_frac"):
            if k in f:
                f[k] = _num(f[k])
        for k in ("quality_f", "partial_f", "ice_clim_f", "xovr_cal_q"):
            if k in f:
                v = _num(f[k])
                f[k] = None if v is None else int(v)
        filas.append(f)
    return filas


def _num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if np.isfinite(x) else None


def es_relleno(fila):
    """Pasada sin observación del lago: time_str 'no_data' o wse de relleno (-999999999999)."""
    w = fila.get("wse")
    return fila.get("time_str", "no_data") == "no_data" or w is None or w <= RELLENO / 10


def filtrar_hydrocron(filas, calidad_max=CALIDAD_MAX):
    """Descarta rellenos y observaciones con quality_f > calidad_max (o sin bandera). Devuelve (válidas, conteo)."""
    conteo = {"total": len(filas), "relleno": 0, "calidad": 0, "validas": 0}
    validas = []
    for f in filas:
        if es_relleno(f):
            conteo["relleno"] += 1
            continue
        q = f.get("quality_f")
        if q is None or q < 0 or q > calidad_max:
            conteo["calidad"] += 1
            continue
        validas.append(f)
    validas.sort(key=lambda f: f["time_str"])
    conteo["validas"] = len(validas)
    return validas, conteo


def mensual_hydrocron(filas, variable="wse"):
    """Media mensual (clave 'AAAA-MM') de una variable de las filas válidas → (meses, medias, n por mes)."""
    por = {}
    for f in filas:
        v = f.get(variable)
        if v is None:
            continue
        por.setdefault(f["time_str"][:7], []).append(v)
    meses = sorted(por)
    return meses, [float(np.mean(por[m])) for m in meses], [len(por[m]) for m in meses]


def tendencia_si_suficiente(meses, valores, anios_min=ANIOS_MIN_TENDENCIA):
    """Pendiente MCO (m/año) solo si la serie mensual cubre al menos `anios_min` años; si no, (None, motivo)."""
    if not meses:
        return None, "sin datos"
    t = np.array([int(m[:4]) + (int(m[5:7]) - 0.5) / 12 for m in meses])
    span = t.max() - t.min()
    if span < anios_min:
        return None, (f"serie de {span:.1f} años (< {anios_min}): demasiado corta para una tendencia; "
                      "se usa como contraste")
    b = np.polyfit(t, np.asarray(valores, float), 1)[0]
    return float(b), f"MCO sobre {len(meses)} meses ({span:.1f} años)"


# ------------------------------------------------------------------ adaptador

class NivelLagos(Adaptador):
    id = "lagos"
    nombre = "Nivel de lagos por altimetría (G-REALM, SWOT)"
    producto = "G-REALM 10-day lake product / SWOT L2 HR LakeSP (Hydrocron)"
    version = "G-REALM TPJOJS.2.5; SWOT LakeSP 2.0"
    variables = {"altura": "m s. n. m. (EGM2008)"}
    resolucion_espacial = "por lago"
    resolucion_temporal = "10 días (G-REALM), ~21 días por pasada (SWOT)"
    periodo = "1992 a la fecha (G-REALM); 2023-07 a la fecha (SWOT)"
    requiere_earthdata = False
    acceso = "G-REALM abierto (earth.gsfc.nasa.gov/gwm); SWOT por la API Hydrocron de PO.DAAC sin cuenta"
    documentacion = "https://podaac.github.io/hydrocron/"
    fenomenos = ("nivel_lagos", "sequia")

    def disponible(self):
        return True, ("Hydrocron abierto (lake_id PLD de Cocibolca y Xolotlán fijados); "
                      "G-REALM solo para Cocibolca (000351)")

    def descargar(self, inicio, fin, url=None, archivo=None, fuente="grealm", lago="cocibolca", tar=None, **kw):
        if archivo:
            return [Path(archivo)]
        if fuente == "swot":
            lake_id = SWOT_LAKE_IDS[lago]
            u = url_hydrocron(lake_id, inicio, fin)
            return [descargar_url(u, self.cache() / f"hydrocron_{lake_id}_{inicio}_{fin}.json", validar_json=True)]
        if url:
            return [descargar_url(url, self.cache() / url.rsplit("/", 1)[-1])]
        id_lago = GREALM_IDS[lago]
        destino = self.cache() / f"lake{id_lago}.10d.2.txt"
        if destino.exists():
            return [destino]
        tar = Path(tar) if tar else descargar_url(URL_TAR_GREALM, self.cache() / "lake.10.tar.gz", timeout=3600)
        return [extraer_grealm_de_tar(tar, id_lago, destino)]

    def recortar(self, archivos, regiones=None, lago="cocibolca"):
        texto = Path(archivos[0]).read_text(encoding="utf-8", errors="replace")
        if texto.lstrip().startswith("{") or texto.startswith("lake_id"):
            validas, _ = filtrar_hydrocron(leer_hydrocron(texto))
            return lago, [f["time_str"][:10] for f in validas], [f["wse"] for f in validas]
        f, h = leer_grealm(texto)
        return lago, f, h

    def agregar(self, recortado, frecuencia="mensual"):
        lago, fechas, alturas = recortado
        por = {}
        for f, h in zip(fechas, alturas):
            clave = f[:7] if frecuencia == "mensual" else int(f[:4])
            por.setdefault(clave, []).append(h)
        t = sorted(por)
        return [SerieRegional(lago, "altura", "m", frecuencia, t, [float(np.mean(por[k])) for k in t], self.id, self.version)]


# ------------------------------------------------------------------ derivados de data/recursos/csa

def escribir_swot(destino, inicio=INICIO_SWOT, fin=None, grealm=None, calidad_max=CALIDAD_MAX):
    """Consulta Hydrocron para los dos lagos y escribe en `destino`:
    respuestas crudas (hydrocron_<lake_id>.json), consultas.json (URL, fecha, sha256), swot_observaciones.csv,
    swot_mensual.csv y, si se da el texto de G-REALM de Cocibolca, comparacion_cocibolca_grealm_swot.csv."""
    import hashlib
    import urllib.request

    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    fin = fin or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    consultas, obs, mensual, resumen = [], [], [], {}
    for lago, lake_id in SWOT_LAKE_IDS.items():
        u = url_hydrocron(lake_id, inicio, fin)
        req = urllib.request.Request(u, headers={"User-Agent": "nasa-challenge-clima/1.0"})
        with urllib.request.urlopen(req, timeout=300) as r:
            crudo = r.read()
        ruta = destino / f"hydrocron_{lake_id}_{lago}.json"
        ruta.write_bytes(crudo)
        sobre = json.loads(crudo)
        consultas.append({"lago": lago, "lake_id": lake_id, "url": u, "archivo": ruta.name,
                          "consulta_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                          "http": 200, "hits": sobre.get("hits"), "sha256": hashlib.sha256(crudo).hexdigest()})
        filas = leer_hydrocron(crudo.decode("utf-8"))
        validas, conteo = filtrar_hydrocron(filas, calidad_max)
        for f in validas:
            obs.append({"lago": lago, **{k: f.get(k) for k in CAMPOS_HYDROCRON}})
        meses, medias, n = mensual_hydrocron(validas)
        for m, v, k in zip(meses, medias, n):
            mensual.append({"lago": lago, "lake_id": lake_id, "mes": m, "wse_m": round(v, 3), "n": k})
        b, motivo = tendencia_si_suficiente(meses, medias)
        wse = [f["wse"] for f in validas]
        resumen[lago] = {"lake_id": lake_id, **conteo, "meses": len(meses),
                         "primera": validas[0]["time_str"] if validas else None,
                         "ultima": validas[-1]["time_str"] if validas else None,
                         "wse_media_m": round(float(np.mean(wse)), 3) if wse else None,
                         "wse_min_m": round(min(wse), 3) if wse else None,
                         "wse_max_m": round(max(wse), 3) if wse else None,
                         "tendencia_m_anio": b, "tendencia_nota": motivo}
    with (destino / "swot_observaciones.csv").open("w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, ["lago", *CAMPOS_HYDROCRON], lineterminator="\n")
        w.writeheader()
        w.writerows(obs)
    with (destino / "swot_mensual.csv").open("w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, ["lago", "lake_id", "mes", "wse_m", "n"], lineterminator="\n")
        w.writeheader()
        w.writerows(mensual)
    if grealm:
        resumen["comparacion_cocibolca"] = comparar_grealm_swot(
            Path(grealm).read_text(encoding="utf-8", errors="replace"),
            [r for r in mensual if r["lago"] == "cocibolca"], destino / "comparacion_cocibolca_grealm_swot.csv")
    doc = {"servicio": HYDROCRON, "documentacion": "https://podaac.github.io/hydrocron/",
           "filtro": {"quality_f_max": calidad_max, "relleno": RELLENO, "duplicados": "eliminados"},
           "consultas": consultas, "resumen": resumen}
    (destino / "consultas_hydrocron.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                                                      encoding="utf-8", newline="\n")
    return doc


def comparar_grealm_swot(texto_grealm, mensual_swot, salida):
    """Medias mensuales de G-REALM (altura EGM2008) frente a SWOT (wse) en los meses comunes."""
    obs = leer_grealm_gsfc(texto_grealm)
    por = {}
    for o in obs:
        por.setdefault(o["fecha"][:7], []).append(o["altura_egm2008_m"])
    filas = []
    for r in mensual_swot:
        if r["mes"] in por:
            g = float(np.mean(por[r["mes"]]))
            filas.append({"mes": r["mes"], "grealm_m": round(g, 3), "n_grealm": len(por[r["mes"]]),
                          "swot_m": r["wse_m"], "n_swot": r["n"], "swot_menos_grealm_m": round(r["wse_m"] - g, 3)})
    with Path(salida).open("w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, ["mes", "grealm_m", "n_grealm", "swot_m", "n_swot", "swot_menos_grealm_m"],
                           lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    if not filas:
        return {"meses_comunes": 0}
    d = np.array([x["swot_menos_grealm_m"] for x in filas])
    g = np.array([x["grealm_m"] for x in filas])
    s = np.array([x["swot_m"] for x in filas])
    return {"meses_comunes": len(filas), "desde": filas[0]["mes"], "hasta": filas[-1]["mes"],
            "sesgo_medio_m": round(float(d.mean()), 3), "rmsd_m": round(float(np.sqrt((d ** 2).mean())), 3),
            "desv_dif_m": round(float(d.std(ddof=1)), 3) if len(d) > 1 else None,
            "correlacion": round(float(np.corrcoef(g, s)[0, 1]), 3) if len(d) > 2 else None,
            "grealm_obs_total": len(obs), "grealm_ultima": obs[-1]["fecha"] if obs else None}


if __name__ == "__main__":
    import argparse

    from ..rutas import DATOS

    ap = argparse.ArgumentParser(description="Consulta SWOT Hydrocron para Cocibolca y Xolotlán")
    ap.add_argument("accion", choices=["swot"])
    ap.add_argument("--inicio", default=INICIO_SWOT)
    ap.add_argument("--fin", default=None)
    ap.add_argument("--grealm", type=Path, default=None, help="lake000351.10d.2.txt de G-REALM (opcional)")
    ap.add_argument("--destino", type=Path, default=DATOS / "recursos" / "csa")
    a = ap.parse_args()
    print(json.dumps(escribir_swot(a.destino, a.inicio, a.fin, a.grealm)["resumen"], ensure_ascii=False, indent=1))
