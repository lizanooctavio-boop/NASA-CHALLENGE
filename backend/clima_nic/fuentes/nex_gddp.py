"""NASA Earth Exchange Global Daily Downscaled Projections, CMIP6 (NEX-GDDP-CMIP6), v2.0.

Proyecciones diarias reducidas de escala (0,25°) y con corrección de sesgo BCSD contra GMFD, para 35 modelos y
los escenarios SSP2-4.5 y SSP5-8.5 (2015–2100) más el histórico (1950–2014). Acceso sin cuenta por el servidor
THREDDS de NCCS: el catálogo da el nombre exacto de cada archivo y el NetCDF Subset Service (NCSS) recorta la
caja de Nicaragua (~0,7 MB por año y variable en NetCDF-3, que se lee con scipy). Solo tierra: el océano y los
lagos grandes vienen sin dato y se excluyen al promediar.

Uso en este proyecto: **escenarios, no pronóstico**. Se calcula el cambio de cada modelo entre su histórico
1995–2014 y 2041–2060 (Δ en °C para la temperatura y en % para la lluvia) y se aplica a la climatología
observada (corrección de sesgo por método delta, en `proyecciones.py`). El resultado es un rango entre modelos
por escenario; ningún año futuro concreto es un pronóstico.
"""
import csv
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

from .. import regiones as reg
from ..rutas import FENOMENOS
from .base import Adaptador, SerieRegional, descargar_url, recortar_malla

THREDDS = "https://ds.nccs.nasa.gov/thredds"
RAIZ_CAT = "AMES/NEX/GDDP-CMIP6"
MODELOS = ("ACCESS-CM2", "CanESM5", "EC-Earth3", "GFDL-ESM4", "MPI-ESM1-2-HR", "MRI-ESM2-0")
ESCENARIOS = {"historical": (1995, 2014), "ssp245": (2041, 2060), "ssp585": (2041, 2060)}
VARIABLES = {"pr": "mm/mes", "tas": "°C"}
CAJA = {"north": 15.25, "south": 10.5, "west": -88.0, "east": -82.5}


class NexGddp(Adaptador):
    id = "nex_gddp_cmip6"
    nombre = "NEX-GDDP-CMIP6 (NASA Earth Exchange)"
    producto = "NEX-GDDP-CMIP6"
    version = "v2.0"
    variables = {"pr": "kg m⁻² s⁻¹ → mm", "tas": "K → °C", "tasmax": "K", "tasmin": "K", "hurs": "%", "rsds": "W m⁻²",
                 "sfcWind": "m/s"}
    resolucion_espacial = "0,25° (solo tierra)"
    resolucion_temporal = "diaria"
    periodo = "histórico 1950–2014; SSP2-4.5 y SSP5-8.5 2015–2100"
    requiere_earthdata = False
    acceso = "THREDDS/NCSS de NCCS (sin cuenta) o S3 público"
    documentacion = "https://www.nccs.nasa.gov/services/data-collections/land-based-products/nex-gddp-cmip6"
    fenomenos = ("escenarios_lluvia", "escenarios_temperatura")

    def __init__(self):
        self._catalogos = {}

    def archivos(self, modelo, escenario, variable):
        """{año: urlPath} según el catálogo THREDDS (el miembro r?i?p?f? y el sufijo de versión varían)."""
        clave = (modelo, escenario, variable)
        if clave not in self._catalogos:
            base = f"{THREDDS}/catalog/{RAIZ_CAT}/{modelo}/{escenario}/catalog.xml"
            with urllib.request.urlopen(base, timeout=120) as r:
                miembros = re.findall(r'xlink:href="([^"/]+)/catalog.xml"', r.read().decode())
            rutas = {}
            for miembro in miembros:
                url = f"{THREDDS}/catalog/{RAIZ_CAT}/{modelo}/{escenario}/{miembro}/{variable}/catalog.xml"
                try:
                    with urllib.request.urlopen(url, timeout=120) as r:
                        texto = r.read().decode()
                except Exception:  # noqa: BLE001 - miembro sin esa variable
                    continue
                for p in re.findall(r'urlPath="([^"]+\.nc)"', texto):
                    m = re.search(r"_(\d{4})(?:_v[\d.]+)?\.nc$", p)
                    if m:
                        anio = int(m.group(1))
                        # preferir la versión más reciente si hay varias
                        if anio not in rutas or ("_v" in p and "_v" not in rutas[anio]) or p > rutas[anio]:
                            rutas[anio] = p
                if rutas:
                    break
            self._catalogos[clave] = rutas
        return self._catalogos[clave]

    def url_ncss(self, url_path, variable):
        q = "&".join(f"{k}={v}" for k, v in CAJA.items())
        return f"{THREDDS}/ncss/grid/{url_path}?var={variable}&{q}&horizStride=1&temporal=all&accept=netcdf3"

    def descargar(self, inicio, fin, modelo=None, escenario=None, variable="pr", **kw):
        rutas = []
        for anio, p in sorted(self.archivos(modelo, escenario, variable).items()):
            if inicio <= anio <= fin:
                destino = self.cache() / modelo / escenario / p.rsplit("/", 1)[1]
                rutas.append((anio, descargar_url(self.url_ncss(p, variable), destino, timeout=600)))
        return rutas

    @staticmethod
    def leer(ruta, variable):
        from scipy.io import netcdf_file
        with netcdf_file(ruta, "r", mmap=False) as f:
            v = f.variables[variable]
            datos = v[:].astype(float)
            relleno = float(getattr(v, "_FillValue", 1e20))
            datos[datos >= relleno / 10] = np.nan
            lat = f.variables["lat"][:].astype(float)
            lon = f.variables["lon"][:].astype(float)
            tiempo = f.variables["time"][:].astype(float)
            unidades = f.variables["time"].units.decode()
        return lat, lon, datos, tiempo, unidades

    def recortar(self, archivos, regiones=None, variable="pr", pesos=None):
        """[(año, ruta)] → {region: {año: 12 valores mensuales}} y los pesos usados."""
        out = {}
        for anio, ruta in archivos:
            lat, lon, datos, _, _ = self.leer(ruta, variable)
            series, pesos = recortar_malla(lat, lon, datos, regiones, pesos)
            dias = np.arange(np.datetime64(f"{anio}-01-01"), np.datetime64(f"{anio + 1}-01-01"))
            if len(dias) != datos.shape[0]:  # calendarios de 365 o 360 días en algunos modelos
                dias = _fechas_modelo(anio, datos.shape[0])
            meses = dias.astype("datetime64[M]").astype(int) % 12 + 1
            for k, s in series.items():
                if variable == "pr":
                    mens = [float(np.sum(s[meses == m]) * 86400) for m in range(1, 13)]
                else:
                    mens = [float(np.mean(s[meses == m]) - 273.15) for m in range(1, 13)]
                out.setdefault(k, {})[anio] = mens
        return out, pesos

    def agregar(self, recortado, frecuencia="anual", variable="pr", fuente_id=""):
        datos, _ = recortado
        out = []
        for region, por_anio in datos.items():
            anios = sorted(por_anio)
            if frecuencia == "anual":
                vals = [sum(por_anio[a]) if variable == "pr" else float(np.mean(por_anio[a])) for a in anios]
                out.append(SerieRegional(region, variable, VARIABLES[variable], "anual", anios, vals, self.id, self.version,
                                         [fuente_id]))
            else:
                t = [f"{a}-{m:02d}" for a in anios for m in range(1, 13)]
                out.append(SerieRegional(region, variable, VARIABLES[variable], "mensual", t,
                                         [v for a in anios for v in por_anio[a]], self.id, self.version, [fuente_id]))
        return out


def _fechas_modelo(anio, n):
    """Asigna meses a un año de 365 (sin 29-feb) o 360 días (12 × 30) para agregar por mes."""
    if n == 360:
        return np.array([np.datetime64(f"{anio}-{m:02d}-01") for m in range(1, 13) for _ in range(30)])
    dias = np.arange(np.datetime64(f"{anio}-01-01"), np.datetime64(f"{anio + 1}-01-01"))
    dias = dias[~((dias.astype("datetime64[M]").astype(int) % 12 == 1) & ((dias - dias.astype("datetime64[M]")).astype(int) == 28))]
    return dias[:n]


def escribir_derivados(modelos=MODELOS, escenarios=ESCENARIOS, variables=tuple(VARIABLES), hilos=6, salida=FENOMENOS):
    """Descarga los recortes y escribe data/fenomenos/cmip6_mensual.csv (medias regionales mensuales)."""
    a = NexGddp()
    regiones = reg.cargar()
    tareas = []
    for mo in modelos:
        for esc, (i, f) in escenarios.items():
            for var in variables:
                try:
                    disponibles = a.archivos(mo, esc, var)
                except Exception as e:  # noqa: BLE001
                    print(f"  sin catálogo {mo} {esc} {var}: {e}")
                    continue
                for anio, p in sorted(disponibles.items()):
                    if i <= anio <= f:
                        tareas.append((mo, esc, var, anio, p))
    print(f"{len(tareas)} recortes por descargar")

    def bajar(t):
        mo, esc, var, anio, p = t
        destino = a.cache() / mo / esc / p.rsplit("/", 1)[1]
        return t, descargar_url(a.url_ncss(p, var), destino, timeout=600)

    rutas = {}
    with ThreadPoolExecutor(hilos) as ex:
        for k, fut in enumerate(as_completed([ex.submit(bajar, t) for t in tareas]), 1):
            try:
                t, r = fut.result()
                rutas[t] = r
            except Exception as e:  # noqa: BLE001
                print("  error:", e)
            if k % 50 == 0:
                print(f"  {k}/{len(tareas)}")
    pesos = None
    filas = []
    for (mo, esc, var, anio, p), r in sorted(rutas.items()):
        datos, pesos = a.recortar([(anio, r)], regiones, var, pesos)
        for region, por_anio in datos.items():
            for m, v in enumerate(por_anio[anio], 1):
                filas.append((mo, p.split("/")[5] if len(p.split("/")) > 5 else "", esc, var, region, anio, m, v))
    salida.mkdir(parents=True, exist_ok=True)
    with (salida / "cmip6_mensual.csv").open("w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["modelo", "miembro", "escenario", "variable", "region", "anio", "mes", "valor"])
        for fila in filas:
            w.writerow([*fila[:7], f"{fila[7]:.4f}"])
    print(f"{len(filas)} filas en cmip6_mensual.csv")
