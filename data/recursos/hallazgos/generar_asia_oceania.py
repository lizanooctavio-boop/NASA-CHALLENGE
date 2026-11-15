"""Descarga observaciones sin cuenta y genera CSV anuales pequeños para el agente 3.

Uso: python data/recursos/hallazgos/generar_asia_oceania.py --cache /ruta/FUERA/del/repositorio
Dependencias de extracción: numpy, netCDF4, rasterio (solo Aral). No se necesitan para integrar los CSV.
La caché conserva originales y recibos; no se versionan NetCDF, GeoTIFF ni ZIP.
--solo permite reanudar familias; no borra las series de otras familias. --hasta limita a años completos.
"""
import argparse
import calendar
import csv
import gzip
import hashlib
import io
import json
import math
import re
import shutil
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

COHORTES = {}  # número de celdas realmente utilizadas, guardado junto a cada serie
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
PSMSL = 'https://psmsl.org/data/obtaining/rlr.annual.data/{id}.rlrdata'
ESTACIONES = {1839: 'nivel_mar_funafuti_b', 1804: 'nivel_mar_betio', 1805: 'nivel_mar_lautoka',
              145: 'nivel_mar_manila', 150: 'nivel_mar_auckland_ii'}
GMSL = 'https://sealevel.colorado.edu/files/2026_rel1/gmsl_2026rel1_seasons_retained.txt'
OHC = 'https://www.ncei.noaa.gov/data/oceans/woa/DATA_ANALYSIS/3M_HEAT_CONTENT/DATA/basin/yearly/h22-w0-2000m.dat'
GISS = 'https://data.giss.nasa.gov/pub/gistemp/gistemp250_GHCNv4.nc.gz'
CRU = 'https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/cruts.2604091129.v4.10/pre/'
CRW = 'https://coralreefwatch.noaa.gov/product/vs/data/{region}.txt'
JRC = 'https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GSWE/YearlyClassification/LATEST/tiles/'


def bajar(url, ruta):
    """Caché atómica, reintentos acotados y recibo con URL, fecha real y hash del original."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    recibo = ruta.with_suffix(ruta.suffix + '.recibo.json')
    if ruta.is_file() and recibo.is_file():
        meta = json.loads(recibo.read_text())
        if meta['url'] != url or meta['sha256'] != hashlib.sha256(ruta.read_bytes()).hexdigest():
            raise ValueError(f'Caché no coincide con su recibo: {ruta.name}')
        return ruta
    parcial = ruta.with_suffix(ruta.suffix + '.part')
    for intento in range(3):
        try:
            with urllib.request.urlopen(url, timeout=120) as remoto, parcial.open('wb') as f:
                shutil.copyfileobj(remoto, f)
            if parcial.stat().st_size == 0:
                raise ValueError('Respuesta vacía')
            parcial.replace(ruta)
            meta = dict(archivo=ruta.name, url=url, sha256=hashlib.sha256(ruta.read_bytes()).hexdigest(),
                        bytes=ruta.stat().st_size, descargado_utc=datetime.now(timezone.utc).isoformat(timespec='seconds'))
            recibo.write_text(json.dumps(meta, indent=2) + '\n')
            return ruta
        except (OSError, ValueError):
            if intento == 2:
                raise
            time.sleep(1 + intento)


def filas_psmsl(texto, hasta):
    """RLR: -99999 y banderas de atención no son datos aceptados; Y indica interpolación."""
    puntos = []
    for linea in texto.splitlines():
        if not linea.strip():
            continue
        a, v, interpolado, bandera = (s.strip() for s in linea.split(';'))
        a, v = int(a), float(v)
        if a <= hasta and v != -99999 and int(bandera) == 0:
            puntos.append((a, v))
    if len({a for a, _ in puntos}) != len(puntos):
        raise ValueError('Años duplicados en PSMSL')
    return sorted(puntos)


def psmsl(cache, hasta):
    salida = {}
    for numero, serie in ESTACIONES.items():
        ruta = bajar(PSMSL.format(id=numero), cache / f'psmsl_{numero}.rlrdata')
        puntos = filas_psmsl(ruta.read_text(), hasta)
        # Estaciones modernas desde 1993; conservar el registro largo de Auckland desde 1900.
        desde = 1900 if numero == 150 else 1993
        puntos = [(a, v) for a, v in puntos if a >= desde]
        base = [v for a, v in puntos if 1993 <= a <= 2020]
        if not base:
            raise ValueError(f'Sin referencia en estación {numero}')
        salida[serie] = [(a, v - float(np.mean(base))) for a, v in puntos]
    return salida


def gmsl(cache, hasta):
    # La edición NOAA consultada termina en febrero de 2025; CU/NASA 2026_rel1 sí contiene 2025 completo.
    texto = bajar(GMSL, cache / 'gmsl_2026rel1.txt').read_text()
    por_mes = {}
    for linea in texto.splitlines():
        if not linea.strip() or linea.startswith('#'):
            continue
        t, v = map(float, linea.split()); a = math.floor(t)
        if 1993 <= a <= hasta:
            mes = min(12, int((t - a) * 12) + 1)
            por_mes.setdefault((a, mes), []).append(v)
    return {'nivel_mar_global_altimetria': [(a, float(np.mean([np.mean(por_mes[a, m]) for m in range(1, 13)])))
            for a in range(1993, hasta + 1) if all((a, m) in por_mes for m in range(1, 13))]}


def ohc(cache, hasta):
    filas = np.loadtxt(bajar(OHC, cache / 'ohc_2000m.dat'), skiprows=1)
    return {'oceano_global_contenido_calor_2000m': [(int(r[0]), float(r[1])) for r in filas if int(r[0]) <= hasta]}


def leer_caja(ruta, variable, caja):
    from netCDF4 import Dataset, num2date
    sur, norte, oeste, este = caja
    with Dataset(ruta) as f:
        lat, lon = f['lat'][:], f['lon'][:]
        lon180 = np.where(lon > 180, lon - 360, lon)
        i = np.flatnonzero((lat >= sur) & (lat <= norte))
        j = np.flatnonzero((lon180 >= oeste) & (lon180 <= este))
        if not len(i) or not len(j):
            raise ValueError('Caja sin celdas')
        v = np.ma.asarray(f[variable][:, i, j], dtype=float).filled(np.nan)
        t = f['time']; fechas = list(num2date(t[:], t.units, calendar=getattr(t, 'calendar', 'standard')))
        stn = np.ma.asarray(f['stn'][:, i, j], dtype=float).filled(0) if 'stn' in f.variables else None
        return fechas, lat[i].astype(float), v, stn


def promedio_fijo(cubos, latitudes):
    """Cohorte de celdas observadas en TODAS las fechas seleccionadas; nunca llena huecos con cero."""
    v = np.asarray(cubos, float)
    mascara = np.all(np.isfinite(v), axis=0)
    pesos = np.cos(np.deg2rad(latitudes))[:, None] * mascara
    if pesos.sum() == 0:
        raise ValueError('No hay cohorte espacial común válida')
    return np.nansum(v * pesos, axis=(1, 2)) / pesos.sum(), int(mascara.sum())


def descomprimir(ruta):
    destino = ruta.with_suffix('')
    if not destino.exists():
        with gzip.open(ruta, 'rb') as src, destino.open('wb') as out:
            shutil.copyfileobj(src, out)
    return destino


def monzon(cache, hasta):
    fechas, bloques = [], []
    # Desde 1951 para comparar la ventana histórica y su prolongación sin mezclar productos.
    for inicio in range(1951, hasta + 1, 10):
        fin = min(inicio + 9, 2025)
        nombre = f'cru_ts4.10.{inicio}.{fin}.pre.dat.nc.gz'
        ruta = descomprimir(bajar(CRU + nombre, cache / nombre))
        f, lat, v, stn = leer_caja(ruta, 'pre', (19, 26, 76, 86))
        ruta.unlink()  # derivado regenerable; la caché conserva el original gzip con su recibo
        seleccion = [i for i, d in enumerate(f) if d.month in (6, 7, 8, 9) and d.year <= hasta]
        x = v[seleccion]
        if stn is None:
            raise ValueError('Falta el número de estaciones de CRU')
        x[stn[seleccion] <= 0] = np.nan  # climatología rellenada no cuenta como observación
        fechas.extend(f[i] for i in seleccion); bloques.append(x)
    medias, n = promedio_fijo(np.concatenate(bloques), lat)
    COHORTES['monzon_india_central_lluvia_total'] = n
    print(f'CRU: cohorte fija de {n} celdas', flush=True)
    por = {}
    for d, v in zip(fechas, medias):
        por.setdefault(d.year, {})[d.month] = v
    return {'monzon_india_central_lluvia_total': [(a, float(sum(ms.values()))) for a, ms in sorted(por.items()) if set(ms) == {6, 7, 8, 9}]}


def vectores_ascii(texto):
    """Lee coordenadas DAP ASCII; usa únicamente el cuerpo posterior al separador."""
    cuerpo = texto.split('---------------------------------------------', 1)[1]
    salida = {}
    for nombre, cantidad, valores in re.findall(r'(?m)^(lat|lon|time)\[(\d+)\]\n([^\n]+)', cuerpo):
        x = np.fromstring(valores, sep=',')
        if len(x) != int(cantidad):
            raise ValueError(f'Coordenada DAP truncada: {nombre}')
        salida[nombre] = x
    if set(salida) != {'lat', 'lon', 'time'}:
        raise ValueError('Faltan coordenadas DAP')
    return salida


def matriz_ascii(texto, variable):
    cuerpo = texto.split('---------------------------------------------', 1)[1]
    cab = re.search(rf'(?m)^{variable}\.{variable}\[(\d+)\]\[(\d+)\]\[(\d+)\]', cuerpo)
    if cab is None:
        raise ValueError('Falta la matriz DAP')
    nt, ny, nx = map(int, cab.groups()); v = np.full((nt, ny, nx), np.nan); vistas = set()
    for it, iy, valores in re.findall(r'(?m)^\[(\d+)\]\[(\d+)\],\s*([^\n]+)', cuerpo):
        it, iy = int(it), int(iy); x = np.fromstring(valores, sep=',')
        if (it, iy) in vistas or len(x) != nx or it >= nt or iy >= ny:
            raise ValueError('Fila DAP duplicada o dimensión incorrecta')
        vistas.add((it, iy)); v[it, iy] = x
    if len(vistas) != nt * ny:
        raise ValueError('Matriz DAP incompleta')
    v[~np.isfinite(v) | (np.abs(v) > 1e10)] = np.nan
    return v


def leer_dap(base, cache, prefijo, variable, caja, desde, hasta, meses=range(1, 13)):
    """OPeNDAP no crea el archivo temporal NCSS que fallaba por falta de espacio en NOAA."""
    from netCDF4 import num2date
    coords = vectores_ascii(bajar(base + '.ascii?lat,lon,time', cache / f'{prefijo}_coords.txt').read_text())
    das = bajar(base + '.das', cache / f'{prefijo}_metadata.txt').read_text()
    tiempo = re.search(r'\btime\s*\{(.*?)\}', das, re.S)
    unidades = re.search(r'String units "([^"]+)"', tiempo.group(1)).group(1)
    fechas = list(num2date(coords['time'], unidades))
    sur, norte, oeste, este = caja
    lat, lon = coords['lat'], coords['lon']; lon = np.where(lon > 180, lon - 360, lon)
    i = np.flatnonzero((lat >= sur) & (lat <= norte)); j = np.flatnonzero((lon >= oeste) & (lon <= este))
    k = np.array([n for n, d in enumerate(fechas) if desde <= d.year <= hasta and d.month in meses])
    if not len(i) or not len(j) or not len(k):
        raise ValueError('Selección DAP vacía')
    # Los conjuntos seleccionados aquí son contiguos en cada dimensión.
    if not all(np.all(np.diff(x) == 1) for x in (i, j, k)):
        raise ValueError('La selección DAP debe ser contigua')
    corte = ''.join(f'[{x.min()}:{x.max()}]' for x in (k, i, j))
    query = f'{variable}{corte},lat[{i.min()}:{i.max()}],lon[{j.min()}:{j.max()}],time[{k.min()}:{k.max()}]'
    url = base + '.ascii?' + urllib.parse.quote(query, safe=',:')
    texto = bajar(url, cache / f'{prefijo}_datos.txt').read_text()
    datos = matriz_ascii(texto, variable)
    if datos.shape != (len(k), len(i), len(j)):
        raise ValueError('Dimensiones del recorte DAP no coinciden')
    return [fechas[n] for n in k], lat[i], datos


def china(cache, hasta):
    def verano(a):
        base = f'https://psl.noaa.gov/thredds/dodsC/Datasets/cpc_global_precip/precip.{a}.nc'
        f, lat, x = leer_dap(base, cache, f'cpc_{a}', 'precip', (27, 34, 110, 122), a, a, (6, 7, 8))
        if len(f) != 92 or len({(d.year, d.month, d.day) for d in f}) != 92:
            raise ValueError(f'CPC: verano incompleto o duplicado: {a}')
        valido = np.isfinite(x).all(axis=0) & (x >= 0).all(axis=0)
        if not valido.any():
            print(f'CPC: {a} excluido por días sin datos en toda la caja', flush=True)
            return a, lat, None
        maximo = np.max(np.where(np.isfinite(x), x, -np.inf), axis=0); maximo[~valido] = np.nan
        return a, lat, maximo
    with ThreadPoolExecutor(3) as ex:
        bloques = [b for b in ex.map(verano, range(1981, hasta + 1)) if b[2] is not None]
    medias, n = promedio_fijo([x[2] for x in bloques], bloques[0][1])
    COHORTES['yangtze_lluvia_extrema_verano'] = n
    print(f'CPC: cohorte fija de {n} celdas', flush=True)
    return {'yangtze_lluvia_extrema_verano': [(b[0], float(v)) for b, v in zip(bloques, medias)]}


def ersst(cache, hasta):
    base = 'https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.ersst.v5/sst.mnmean.nc'
    f, lat, v = leer_dap(base, cache, 'ersst_japan', 'sst', (34, 46, 128, 140), 1981, hasta)
    v[(v < -3) | (v > 40)] = np.nan
    medias, n = promedio_fijo(v, lat)
    COHORTES['mar_japon_temperatura_superficial'] = n
    print(f'ERSST: cohorte fija de {n} celdas oceánicas', flush=True)
    por = {}
    for d, m in zip(f, medias):
        por.setdefault(d.year, {})[d.month] = m
    return {'mar_japon_temperatura_superficial': [(a, float(np.average([ms[m] for m in range(1, 13)],
             weights=[calendar.monthrange(a, m)[1] for m in range(1, 13)]))) for a, ms in sorted(por.items()) if len(ms) == 12]}


def siberia(cache, hasta):
    ruta = descomprimir(bajar(GISS, cache / 'gistemp250.nc.gz'))
    f, lat, v, _ = leer_caja(ruta, 'tempanomaly', (55, 70, 80, 140))
    # GISTEMP 250 km es análisis de estaciones terrestres; no es permafrost profundo ni banda zonal.
    sel = [i for i, d in enumerate(f) if 1981 <= d.year <= hasta]
    medias, n = promedio_fijo(v[sel], lat)
    COHORTES['siberia_temperatura_aire'] = n
    print(f'GISTEMP: cohorte fija de {n} celdas', flush=True)
    por = {}
    for i, m in zip(sel, medias):
        por.setdefault(f[i].year, {})[f[i].month] = m
    return {'siberia_temperatura_aire': [(a, float(np.average([ms[m] for m in range(1, 13)],
             weights=[calendar.monthrange(a, m)[1] for m in range(1, 13)]))) for a, ms in sorted(por.items()) if len(ms) == 12]}


def filas_coral(texto, hasta):
    """Formato oficial: fecha, MMM, estadísticas SST, HotSpot, DHW y alerta; no agrega regiones distintas."""
    por = {}
    for linea in texto.splitlines():
        campos = linea.split()
        if len(campos) != 10 or not campos[0].isdigit():
            continue
        a, m, d = map(int, campos[:3])
        if a <= hasta:
            fecha = (a, m, d)
            dhw = float(campos[8])
            if fecha in por:
                raise ValueError('Fecha CRW duplicada')
            por[fecha] = dhw if math.isfinite(dhw) and dhw >= 0 else None
    salida = []
    for a in sorted({d[0] for d in por}):
        dias = [(calendar.monthrange(a, m)[1]) for m in range(1, 13)]
        valores = [v for fecha, v in por.items() if fecha[0] == a]
        if len(valores) == sum(dias) and all(v is not None for v in valores):
            salida.append((a, max(valores)))
    return salida


def coral(cache, hasta):
    return {f'gran_barrera_dhw_{zona}': filas_coral(bajar(CRW.format(region=f'gbr_{zona}'),
            cache / f'crw_gbr_{zona}.txt').read_text(), hasta) for zona in ('northern', 'central', 'southern')}


def aral(cache, hasta):
    import rasterio
    from rasterio.windows import from_bounds
    # Indicador de caja, no polígono inventado de la costa histórica; incluye aguas interiores vecinas.
    anios = range(1984, min(hasta, 2021) + 1)
    nombres = [(a, sufijo) for a in anios for sufijo in ('0000120000-0000920000', '0000120000-0000960000')]
    def descarga(par):
        a, sufijo = par; nombre = f'yearlyClassification{a}{"_" if a == 2021 else "-"}{sufijo}.tif'
        return bajar(JRC + f'yearlyClassification{a}/' + nombre, cache / nombre)
    with ThreadPoolExecutor(3) as ex:
        rutas = list(ex.map(descarga, nombres))
    from contextlib import ExitStack
    por = {a: np.zeros(3) for a in anios}
    # El archivo enmascara zonas fuera de su huella clasificada. No deben contarse como días sin observación.
    # Se define una huella espacial FIJA mediante la unión de píxeles clasificados de todas las épocas.
    # Dos lecturas por bloque mantienen acotada la memoria sin almacenar cubos mundiales.
    for sufijo in ('0000120000-0000920000', '0000120000-0000960000'):
        archivos = [(a, ruta) for (a, s), ruta in zip(nombres, rutas) if s == sufijo]
        with rasterio.Env(GDAL_CACHEMAX=64 * 1024 ** 2), ExitStack() as pila:
            capas = [(a, pila.enter_context(rasterio.open(r))) for a, r in archivos]
            f = capas[0][1]
            ventana = from_bounds(max(57, f.bounds.left), 43, min(62, f.bounds.right), 47.5,
                                  f.transform).round_offsets().round_lengths()
            for inicio in range(0, int(ventana.height), 512):
                w = rasterio.windows.Window(ventana.col_off, ventana.row_off + inicio, ventana.width,
                                            min(512, ventana.height - inicio))
                soporte = np.zeros((int(w.height), int(w.width)), dtype=bool)
                for _, capa in capas:
                    soporte |= capa.read(1, window=w) != 0
                yy = f.transform.f + (w.row_off + np.arange(soporte.shape[0])) * f.transform.e
                area = 6371.0088 ** 2 * np.deg2rad(abs(f.transform.a)) * np.abs(np.sin(np.deg2rad(yy)) - np.sin(np.deg2rad(yy + f.transform.e)))
                total = float(soporte.sum(axis=1) @ area)
                for a, capa in capas:
                    x = capa.read(1, window=w)
                    agua = float(((x == 2) | (x == 3)).sum(axis=1) @ area)
                    cubierto = float(((x != 0) & soporte).sum(axis=1) @ area)
                    por[a] += (agua, cubierto, total)
    for a, v in por.items():
        print(f'JRC: {a}, cobertura de la huella fija {v[1] / v[2]:.4f}', flush=True)
    retenidos = [a for a, v in por.items() if v[2] > 0 and v[1] / v[2] >= .95]
    if len(retenidos) < 10:
        raise ValueError('JRC: menos de diez años con cobertura espacial suficiente')
    # La selección de años usa cobertura, nunca pendiente o significación. Segunda etapa:
    # intersección de píxeles válidos en todos los años retenidos, sin imputar los no observados.
    areas = {a: 0. for a in retenidos}; area_fija = 0.
    for sufijo in ('0000120000-0000920000', '0000120000-0000960000'):
        archivos = [(a, ruta) for (a, s), ruta in zip(nombres, rutas) if s == sufijo and a in retenidos]
        with rasterio.Env(GDAL_CACHEMAX=64 * 1024 ** 2), ExitStack() as pila:
            capas = [(a, pila.enter_context(rasterio.open(r))) for a, r in archivos]
            f = capas[0][1]
            if any(c.transform != f.transform or c.crs != f.crs for _, c in capas):
                raise ValueError('JRC: rejillas no alineadas')
            ventana = from_bounds(max(57, f.bounds.left), 43, min(62, f.bounds.right), 47.5,
                                  f.transform).round_offsets().round_lengths()
            for inicio in range(0, int(ventana.height), 512):
                w = rasterio.windows.Window(ventana.col_off, ventana.row_off + inicio, ventana.width,
                                            min(512, ventana.height - inicio))
                comun = np.ones((int(w.height), int(w.width)), dtype=bool)
                for _, c in capas:
                    comun &= c.read(1, window=w) != 0
                yy = f.transform.f + (w.row_off + np.arange(comun.shape[0])) * f.transform.e
                area = 6371.0088 ** 2 * np.deg2rad(abs(f.transform.a)) * np.abs(np.sin(np.deg2rad(yy)) - np.sin(np.deg2rad(yy + f.transform.e)))
                area_fija += float(comun.sum(axis=1) @ area)
                for a, c in capas:
                    x = c.read(1, window=w)
                    areas[a] += float((((x == 2) | (x == 3)) & comun).sum(axis=1) @ area)
    print(f'JRC: huella común clasificada {area_fija:.3f} km²; {len(retenidos)} años', flush=True)
    return {'mar_aral_superficie_agua': sorted(areas.items())}



PASOS = dict(psmsl=psmsl, gmsl=gmsl, ohc=ohc, monzon=monzon, china=china, ersst=ersst, siberia=siberia, coral=coral, aral=aral)


def escribir_csv(ruta, campos, filas):
    temporal = ruta.with_suffix('.tmp')
    with temporal.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n'); w.writerow(campos); w.writerows(filas)
    temporal.replace(ruta)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cache', type=Path, required=True)
    ap.add_argument('--hasta', type=int, default=2025)
    ap.add_argument('--solo', nargs='+', choices=sorted(PASOS))
    args = ap.parse_args(); cache = args.cache.resolve()
    if cache == RAIZ or RAIZ in cache.parents:
        ap.error('--cache debe estar FUERA del repositorio')
    if args.hasta >= datetime.now(timezone.utc).year:
        ap.error('--hasta debe ser un año completo anterior al actual')
    cache.mkdir(parents=True, exist_ok=True)
    ruta = AQUI / 'asia_oceania_anual.csv'
    series = {}
    if ruta.exists():
        with ruta.open() as f:
            for fila in csv.DictReader(f):
                series.setdefault(fila['id'], []).append((int(fila['anio']), float(fila['valor'])))
                if fila.get('celdas_cohorte'):
                    COHORTES[fila['id']] = int(fila['celdas_cohorte'])
    for nombre in args.solo or PASOS:
        nuevas = PASOS[nombre](cache / nombre, args.hasta)
        for id_, puntos in nuevas.items():
            if len(puntos) < 10 or len({a for a, _ in puntos}) != len(puntos) or not all(math.isfinite(v) for _, v in puntos):
                raise ValueError(f'{id_}: menos de diez años, duplicados o valores no finitos')
        series.update(nuevas)
        escribir_csv(ruta, ['id', 'anio', 'valor', 'celdas_cohorte'], [(id_, a, f'{v:.6f}', COHORTES.get(id_, '')) for id_, puntos in sorted(series.items()) for a, v in sorted(puntos)])
        recibos = [json.loads(p.read_text()) for p in sorted(cache.rglob('*.recibo.json'))]
        campos = ['archivo', 'url', 'sha256', 'bytes', 'descargado_utc']
        escribir_csv(AQUI / 'asia_oceania_fuentes.csv', campos, [[r[k] for k in campos] for r in recibos])
        print('hecho:', nombre, {k: (len(v), v[0][0], v[-1][0]) for k, v in nuevas.items()}, flush=True)


if __name__ == '__main__':
    main()
