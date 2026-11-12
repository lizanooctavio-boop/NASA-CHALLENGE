"""NASA POWER (power.larc.nasa.gov): MERRA-2 y CERES/SRB sin cuenta.

Diario por celda MERRA-2 (0,5° × 0,625°) desde 1981 para las regiones de Nicaragua, y mensual regional
sobre el océano para índices climáticos:

- Niño 3.4 (5° S–5° N, 170°–120° O), TS sobre el mar (= TSM de borde de MERRA-2).
- Atlántico Norte tropical TNA (5,5–23,5° N, 57,5–20° O).
- AMO (0–60° N, 80° O–0°, solo océano; anomalía sin tendencia lineal, Enfield et al., 2001).
- Pacífico Norte para PDO (20–60° N, 120° E–110° O, solo océano; primer EOF de la anomalía tras restar la media
  de la cuenca, aproximación a Mantua et al., 1997, que resta la media global).
- CLLJ (corriente en chorro de bajo nivel del Caribe), caja 12,5–17,5° N, 80–70° O (Maldonado et al., 2014,
  definen el índice con el viento zonal a 925 hPa). POWER no ofrece 925 hPa: aquí se usa U a 10 m sobre el mar
  como **aproximación** (índice = −U10M, positivo cuando el chorro del este es más fuerte). El índice exacto
  a 925 hPa sale de MERRA-2 M2IMNPASM (adaptador merra2, requiere Earthdata).

Los puntos de tierra se excluyen con la máscara de Natural Earth admin-1 cuando se indica (`--tierra`).
"""
import csv
import json
import math
from pathlib import Path

import numpy as np

from .. import regiones as reg
from ..estadistica import indicadores as ind
from ..rutas import FENOMENOS, sha256
from .base import Adaptador, SerieRegional, a_anual, a_mensual, descargar_url

API = "https://power.larc.nasa.gov/api/temporal"
DLAT, DLON = 0.5, 0.625
PARAMETROS_DIARIOS = ("PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "RH2M", "GWETROOT", "GWETTOP",
                      "ALLSKY_SFC_SW_DWN", "WS2M", "T2MDEW", "PS")
CAJAS = {
    "nino34": {"lat": (-5, 5), "lon": (-170, -120), "param": "TS", "oceano": True},
    "tna": {"lat": (5.5, 23.5), "lon": (-57.5, -20), "param": "TS", "oceano": True},
    "amo": {"lat": (0, 60), "lon": (-80, 0), "param": "TS", "oceano": True},
    "pacifico_norte": {"lat": (20, 60), "lon": (120, 250), "param": "TS", "oceano": True},
    "cllj": {"lat": (12.5, 17.5), "lon": (-80, -70), "param": "U10M", "oceano": True},
}


def _rangos(a, b, paso):
    out, x = [], a
    while x < b - 1e-9:
        y = min(x + paso, b)
        if y - x < 2:  # la API regional exige al menos 2° de extensión
            x = max(a, y - 2)
        out.append((round(x, 4), round(y, 4)))
        x = y
    return out


def cajas_regionales(lat, lon):
    """Subdivide una caja en bloques de ≤ 10° × 10° (límite de la API regional)."""
    lo0, lo1 = lon
    lons = [(lo0 + 0, lo1 + 0)]
    if lo1 > 180:  # cruza la línea de cambio de fecha: dividir en dos tramos
        lons = [(lo0, 180 - DLON / 2), (-180, lo1 - 360)]
    bloques = []
    for la in _rangos(lat[0], lat[1], 10):
        for a, b in lons:
            for lo in _rangos(a, b, 10):
                bloques.append((la, lo))
    return bloques


class Power(Adaptador):
    id = "power"
    nombre = "NASA POWER (MERRA-2, CERES/SRB)"
    producto = "POWER Daily/Monthly API v2"
    version = "v2.10"
    variables = {"PRECTOTCORR": "mm/día", "T2M": "°C", "T2M_MAX": "°C", "T2M_MIN": "°C", "RH2M": "%",
                 "GWETROOT": "0–1", "GWETTOP": "0–1", "ALLSKY_SFC_SW_DWN": "MJ m⁻² día⁻¹", "WS2M": "m/s",
                 "T2MDEW": "°C", "PS": "kPa", "TS": "°C", "U10M": "m/s"}
    resolucion_espacial = "0,5° × 0,625° (malla nativa MERRA-2)"
    resolucion_temporal = "diaria y mensual"
    periodo = "1981 a la fecha (radiación desde 1984)"
    requiere_earthdata = False
    acceso = "API REST pública, sin cuenta"
    documentacion = "https://power.larc.nasa.gov/docs/"
    fenomenos = ("lluvia", "temperatura", "humedad", "radiacion", "viento", "eto", "sequia", "canicula",
                 "humedad_suelo", "enos", "amo", "pdo", "cllj")

    # ---------------- diario por celda
    def celdas(self, regiones=None):
        regiones = reg.cargar() if regiones is None else regiones
        w = min(g.bounds[0] for g in regiones.values())
        s = min(g.bounds[1] for g in regiones.values())
        e = max(g.bounds[2] for g in regiones.values())
        n = max(g.bounds[3] for g in regiones.values())
        lats = np.arange(math.floor((s + DLAT / 2) / DLAT) * DLAT, n + DLAT, DLAT)
        lons = -180 + DLON * np.arange(math.floor((w + 180) / DLON + 0.5) - 1, math.ceil((e + 180) / DLON) + 2)
        return reg.pesos_malla(lats, lons, DLAT, DLON, regiones)

    def url_punto(self, lat, lon, inicio, fin):
        return (f"{API}/daily/point?parameters={','.join(PARAMETROS_DIARIOS)}&community=AG"
                f"&longitude={lon}&latitude={lat}&start={inicio}0101&end={fin}1231&format=JSON")

    def descargar(self, inicio, fin, celdas=None, **kw):
        celdas = self.celdas() if celdas is None else celdas
        rutas = []
        for c in celdas:
            url = self.url_punto(c["lat"], c["lon"], inicio, fin)
            nombre = f"diario_v2_{c['lat']}_{c['lon']}_{inicio}_{fin}.json"
            rutas.append(descargar_url(url, self.cache() / nombre, validar_json=True))
        return rutas

    @staticmethod
    def leer_punto(ruta):
        d = json.loads(Path(ruta).read_text(encoding="utf-8"))
        par = d["properties"]["parameter"]
        claves = sorted(next(iter(par.values())))
        fill = d["header"].get("fill_value", -999.0)
        datos = {}
        for p, serie in par.items():
            v = np.array([serie[k] for k in claves], float)
            v[v == fill] = np.nan
            datos[p] = v
        fechas = np.array([f"{k[:4]}-{k[4:6]}-{k[6:]}" for k in claves], "datetime64[D]")
        elev = d["geometry"]["coordinates"][2] if len(d["geometry"]["coordinates"]) > 2 else None
        return fechas, datos, elev

    def recortar(self, archivos, regiones=None, celdas=None):
        """Media ponderada diaria por región. Devuelve (fechas, {region: {param: serie}}, por_celda)."""
        celdas = self.celdas(regiones) if celdas is None else celdas
        nombres = [k for k in celdas[0] if k not in ("lat", "lon")]
        fechas, por_celda = None, []
        for c, ruta in zip(celdas, archivos):
            f, datos, elev = self.leer_punto(ruta)
            if fechas is None:
                fechas = f
            elif not np.array_equal(fechas, f):
                raise ValueError(f"Fechas distintas en la celda {c['lat']}, {c['lon']}")
            por_celda.append({"celda": c, "datos": datos, "elevacion_m": elev})
        regional = {}
        for k in nombres:
            w = np.array([p["celda"][k] for p in por_celda])
            regional[k] = {par: reg.media_ponderada(np.stack([p["datos"][par] for p in por_celda]), w)
                           for par in por_celda[0]["datos"]}
            regional[k]["_elevacion_m"] = float(np.average([p["elevacion_m"] or 0 for p in por_celda],
                                                           weights=np.maximum(w, 1e-12)))
            regional[k]["_lat"] = float(np.average([p["celda"]["lat"] for p in por_celda], weights=np.maximum(w, 1e-12)))
        return fechas, regional, por_celda

    def agregar(self, recortado, frecuencia="mensual"):
        fechas, regional, _ = recortado
        out = []
        for region, params in regional.items():
            for p, serie in params.items():
                if p.startswith("_"):
                    continue
                como = "suma" if p == "PRECTOTCORR" else "media"
                tm, vm = a_mensual(fechas, serie, como)
                if frecuencia == "mensual":
                    out.append(SerieRegional(region, p, self.variables.get(p, ""), "mensual", tm, vm, self.id, self.version))
                else:
                    ta, va = a_anual(tm, vm, como)
                    out.append(SerieRegional(region, p, self.variables.get(p, ""), "anual", ta, va, self.id, self.version))
        return out

    # ---------------- mensual regional sobre el océano
    def descargar_caja(self, nombre, inicio, fin):
        c = CAJAS[nombre]
        rutas = []
        for (la0, la1), (lo0, lo1) in cajas_regionales(c["lat"], c["lon"]):
            url = (f"{API}/monthly/regional?parameters={c['param']}&community=AG&latitude-min={la0}&latitude-max={la1}"
                   f"&longitude-min={lo0}&longitude-max={lo1}&start={inicio}&end={fin}&format=JSON")
            archivo = f"{c['param'].lower()}_{nombre}_{la0}_{la1}_{lo0}_{lo1}_{inicio}_{fin}.json"
            rutas.append(descargar_url(url, self.cache() / archivo, validar_json=True))
        return rutas

    @staticmethod
    def campo_caja(rutas, param):
        """Une los bloques: devuelve (claves AAAAMM, lat, lon, matriz (meses, puntos))."""
        puntos = {}
        for r in rutas:
            d = json.loads(Path(r).read_text(encoding="utf-8"))
            fill = d["header"].get("fill_value", -999.0)
            for feat in d["features"]:
                lon, lat = feat["geometry"]["coordinates"][:2]
                serie = {k: v for k, v in feat["properties"]["parameter"][param].items() if not k.endswith("13")}
                v = np.array([serie[k] for k in sorted(serie)], float)
                v[v == fill] = np.nan
                puntos[(round(lat, 4), round(lon, 4))] = (sorted(serie), v)
        claves = next(iter(puntos.values()))[0]
        coords = sorted(puntos)
        lat = np.array([c[0] for c in coords])
        lon = np.array([c[1] for c in coords])
        m = np.column_stack([puntos[c][1] for c in coords])
        return claves, lat, lon, m


def mascara_oceano(lat, lon, tierra_geojson):
    """True en los puntos que no caen en tierra (Natural Earth admin-1 unido)."""
    import shapely
    from shapely.geometry import shape
    d = json.loads(Path(tierra_geojson).read_text(encoding="utf-8"))
    tierra = shapely.union_all([shapely.make_valid(shape(f["geometry"])) for f in d["features"]])
    shapely.prepare(tierra)
    lon180 = np.where(lon > 180, lon - 360, lon)
    return ~shapely.contains_xy(tierra, lon180, lat)


def anomalia_mensual(meses, v, anios, base=(1991, 2020)):
    v = np.asarray(v, float)
    sel = (anios >= base[0]) & (anios <= base[1])
    clim = np.array([np.nanmean(v[sel & (meses == m)], axis=0) for m in range(1, 13)])
    return v - clim[meses - 1]


def indices_oceanicos(campos, oceano=None, base=(1991, 2020)):
    """campos: {nombre: (claves, lat, lon, matriz)}. Devuelve (anios, meses, {indice: serie})."""
    out = {}
    anios = meses = None
    for nombre, (claves, lat, lon, m) in campos.items():
        anios = np.array([int(k[:4]) for k in claves])
        meses = np.array([int(k[4:]) for k in claves])
        ok = np.ones(len(lat), bool) if oceano is None or nombre not in oceano else oceano[nombre]
        w = np.cos(np.radians(lat[ok]))
        x = m[:, ok]
        if nombre == "pacifico_norte":
            out["pdo"] = indice_pdo(anios, meses, x, lat[ok], base)
            continue
        media = np.nansum(x * w, axis=1) / np.sum(np.where(np.isfinite(x), w, 0), axis=1)
        if nombre == "cllj":
            out["cllj_u10m"] = (-media).tolist()  # positivo = viento del este más fuerte
            continue
        an = anomalia_mensual(meses, media, anios, base)
        if nombre == "amo":
            t = np.arange(len(an))
            p = np.polyfit(t, an, 1)
            an = an - np.polyval(p, t)
        out[nombre] = an.tolist()
    return anios, meses, out


def indice_pdo(anios, meses, x, lat, base=(1991, 2020)):
    """Primer componente principal de la anomalía de TSM del Pacífico Norte (sin la media de la cuenca),
    estandarizado en la base; signo tal que es positivo con anomalía fría en el Pacífico Norte central."""
    an = anomalia_mensual(meses, x, anios, base)
    an = an - np.nanmean(an, axis=1, keepdims=True)
    an = np.where(np.isfinite(an), an, 0.0) * np.sqrt(np.cos(np.radians(lat)))[None, :]
    u, s, vt = np.linalg.svd(an - an.mean(axis=0), full_matrices=False)
    pc = u[:, 0] * s[0]
    # Patrón PDO+: centro del Pacífico Norte (30–45° N) frío. Cargas positivas allí → invertir.
    centro = (lat >= 30) & (lat <= 45)
    if vt[0][centro].mean() > 0:
        pc = -pc
    sel = (anios >= base[0]) & (anios <= base[1])
    return ((pc - pc[sel].mean()) / pc[sel].std()).tolist()


def escribir_derivados(adaptador, inicio, fin, tierra_geojson=None, salida=FENOMENOS):
    """Descarga lo necesario y escribe los CSV versionados de data/fenomenos/."""
    from ..agro import eto_penman_monteith, grados_dia
    salida.mkdir(parents=True, exist_ok=True)
    celdas = adaptador.celdas()
    rutas = adaptador.descargar(inicio, fin, celdas=celdas)
    fechas, regional, por_celda = adaptador.recortar(rutas, celdas=celdas)
    nombres = [k for k in celdas[0] if k not in ("lat", "lon")]
    manifiesto = [(r.name, sha256(r), adaptador.url_punto(c["lat"], c["lon"], inicio, fin)) for r, c in zip(rutas, celdas)]

    with (salida / "celdas_power.csv").open("w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["lat", "lon", "elevacion_m", *(f"peso_{k}_km2" for k in nombres)])
        for p in por_celda:
            c = p["celda"]
            w.writerow([c["lat"], c["lon"], p["elevacion_m"], *(c[k] for k in nombres)])

    columnas = ("PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "RH2M", "GWETROOT", "GWETTOP", "ALLSKY_SFC_SW_DWN",
                "WS2M", "T2MDEW", "PS")
    _, _, doy = ind.descomponer(fechas)
    indices_celda = {k: {} for k in nombres}
    anual_celda = []
    for p in por_celda:
        d = p["datos"]
        lluvia, _ = ind.indices_lluvia(fechas, d["PRECTOTCORR"], range(1991, 2021))
        calor = ind.indices_calor(fechas, d["T2M_MAX"], d["T2M_MIN"], d["T2M"], range(1991, 2021))
        gdd = grados_dia(fechas, d["T2M_MAX"], d["T2M_MIN"])
        for anio in sorted(set(lluvia) | set(calor)):
            fila = {**lluvia.get(anio, {}), **calor.get(anio, {}), "gdd10": gdd.get(anio, math.nan)}
            anual_celda.append((p["celda"]["lat"], p["celda"]["lon"], anio, fila))
            for k in nombres:
                peso = p["celda"][k]
                if peso <= 0:
                    continue
                dest = indices_celda[k].setdefault(anio, {})
                for n_, v in fila.items():
                    s, ws = dest.get(n_, (0.0, 0.0))
                    if math.isfinite(v):
                        dest[n_] = (s + peso * v, ws + peso)
    with (salida / "serie_diaria_power.csv").open("w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["region", "fecha", *(c.lower() for c in columnas), "eto_pm_mm"])
        for k in nombres:
            r = regional[k]
            eto = eto_penman_monteith(r["T2M_MAX"], r["T2M_MIN"], r["RH2M"], r["ALLSKY_SFC_SW_DWN"], r["WS2M"],
                                      r["_lat"], doy, r["_elevacion_m"], presion_kpa=r["PS"])
            for i, dia in enumerate(fechas):
                vals = [r[c][i] for c in columnas] + [eto[i]]
                w.writerow([k, str(dia), *("" if not math.isfinite(v) else f"{v:.3f}" for v in vals)])
    with (salida / "indices_anuales_regiones.csv").open("w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["region", "anio", "indice", "valor"])
        for k in nombres:
            for anio in sorted(indices_celda[k]):
                for n_, (s, ws) in sorted(indices_celda[k][anio].items()):
                    if ws > 0:
                        w.writerow([k, anio, n_, f"{s / ws:.4f}"])
    with (salida / "indices_anuales_celdas.csv").open("w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        claves = ("prcptot", "rx1day", "rx5day", "r95p", "cdd", "tx90p", "tn90p", "tmax_media", "tmin_media", "t2m_media")
        w.writerow(["lat", "lon", "anio", *claves])
        for lat, lon, anio, fila in anual_celda:
            w.writerow([lat, lon, anio, *(f"{fila.get(c, math.nan):.3f}" for c in claves)])

    campos, oceano = {}, {}
    for nombre, c in CAJAS.items():
        rutas_c = adaptador.descargar_caja(nombre, inicio, fin)
        manifiesto += [(r.name, sha256(r), "") for r in rutas_c]
        campos[nombre] = adaptador.campo_caja(rutas_c, c["param"])
        if tierra_geojson and c["oceano"]:
            oceano[nombre] = mascara_oceano(campos[nombre][1], campos[nombre][2], tierra_geojson)
    anios, meses, idx = indices_oceanicos(campos, oceano or None)
    absolutos = {}
    for nombre in ("nino34", "tna"):
        claves, lat, lon, m = campos[nombre]
        ok = oceano.get(nombre, np.ones(len(lat), bool))
        wl = np.cos(np.radians(lat[ok]))
        absolutos[nombre] = np.nansum(m[:, ok] * wl, axis=1) / np.sum(np.where(np.isfinite(m[:, ok]), wl, 0), axis=1)
    with (salida / "indices_oceanicos_merra2.csv").open("w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        nombres_idx = ("nino34", "tna", "amo", "pdo", "cllj_u10m")
        w.writerow(["anio", "mes", "nino34_ts_c", "tna_ts_c", *(f"{n}_anomalia" if n not in ("pdo", "cllj_u10m") else n
                                                                for n in nombres_idx)])
        for i in range(len(anios)):
            w.writerow([anios[i], meses[i], f"{absolutos['nino34'][i]:.4f}", f"{absolutos['tna'][i]:.4f}",
                        *(f"{idx[n][i]:.4f}" for n in nombres_idx)])
    puntos = {n: int(oceano[n].sum()) if n in oceano else len(campos[n][1]) for n in campos}
    with (salida / "manifiesto_power.csv").open("w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["archivo", "sha256", "url"])
        w.writerows(manifiesto)
    (salida / "fuentes_power.json").write_text(json.dumps(
        {"inicio": inicio, "fin": fin, "parametros_diarios": list(PARAMETROS_DIARIOS), "anios_base": [1991, 2020],
         "regiones": nombres, "celdas": len(celdas), "puntos_oceano_por_caja": puntos,
         "mascara_tierra": "Natural Earth 10 m admin-1" if tierra_geojson else None},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return puntos
