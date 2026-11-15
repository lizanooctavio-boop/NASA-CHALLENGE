"""Series de Europa, África y Oriente Medio (14/15-11-2026). Descarga a una caché fuera del repositorio y escribe
solo CSV pequeños en esta carpeta.

Fuentes públicas sin cuenta:
- GlaMBIE 1.0.0 (WGMS), región 11 (Europa central), años civiles 2000–2023.
- NASA GSFC G-REALM, altimetría de 10 días de los lagos Caspio (000270), Victoria (000314) y Chad (000068).
- NOAA OISST v2.1 diario 0,25° (OPeNDAP de NOAA PSL; si falla, ERDDAP de NOAA CoastWatch): media diaria del Mediterráneo con máscara de cuenca, 1982–2025.
- CHIRPS v2.0 mensual 0,05° (UCSB CHC) en la IRI Data Library: medias por latitud calculadas en el servidor.
- CRU TS 4.10 (UEA) lluvia mensual 0,5° y número de estaciones, 1981–2025.
- GRACE/GRACE-FO mascones CSR RL06.03 (UT Austin): agua total en la cuenca Tigris–Éufrates y oeste de Irán.

Polvo del Sahara: MERRA-2 (GES DISC) y MODIS (LAADS, Giovanni) piden cuenta de Earthdata y el CSV de NEO ya no se
publica (redirige a science.nasa.gov), así que no hay paso de polvo; ver CORRECCIONES_INVESTIGACION_EUROPA_AFRICA.md.

Uso (desde la raíz del repositorio):
    python data/recursos/hallazgos/generar_europa_africa.py --cache <carpeta fuera del repo> [--solo oisst chirps ...]
"""
import argparse
import csv
import datetime
import gzip
import io
import sys
import tarfile
import time
import urllib.request
import zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
GLAMBIE = 'https://wgms.ch/downloads/GlaMBIE_Data_DOI_10.5904_wgms-glambie-2024-07.zip'
GREALM = 'https://earth.gsfc.nasa.gov/gwm/zip/lake.10.tar.gz'
OISST_PSL = 'https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.{a}.nc'
OISST_ERDDAP = ('https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.nc?sst%5B({a}-01-01T12:00:00Z):1:'
         '({a}-12-31T12:00:00Z)%5D%5B(0.0)%5D%5B(30.125):1:(45.875)%5D%5B(-5.375):1:(36.375)%5D')
CHIRPS = ('https://iridl.ldeo.columbia.edu/SOURCES/.UCSB/.CHIRPS/.v2p0/.monthly/.global/.precipitation/'
          'X/{x0}/{x1}/RANGEEDGES/Y/{y0}/{y1}/RANGEEDGES/T/(Jan%20{t0})/(Dec%20{t1})/RANGEEDGES/{op}data.nc')
CRU = 'https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/cruts.2604091129.v4.10/pre/'
CSR = 'https://download.csr.utexas.edu/outgoing/grace/RL0603_mascons/'
CSR_MASCONES, CSR_TIERRA = 'CSR_GRACE_GRACE-FO_RL0603_Mascons_all-corrections.nc', 'CSR_GRACE_GRACE-FO_RL06_Mascons_v02_LandMask.nc'

# Cajas de lluvia (lat sur, lat norte, lon oeste, lon este). Solo tierra: CHIRPS y CRU no tienen datos en el mar.
CAJAS_LLUVIA = {
    'africa_oriental': (-4, 6, 38, 48),   # este de Kenia y sur de Somalia (lluvias largas MAM y cortas OND)
    'sahel': (10, 20, -17, 20),           # Sahel occidental y central (lluvia de julio a septiembre)
}
CAJA_GRACE = (30, 38, 38, 48)             # Tigris–Éufrates y oeste de Irán (Voss et al. 2013)


def bajar(url, destino, timeout=3600):
    if not destino.is_file() or destino.stat().st_size == 0:
        temporal = destino.with_suffix(destino.suffix + '.part')
        with urllib.request.urlopen(url, timeout=timeout) as r, temporal.open('wb') as f:
            while bloque := r.read(1 << 20):
                f.write(bloque)
        temporal.replace(destino)
    return destino


def escribir(nombre, columnas, filas):
    with open(AQUI / nombre, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(columnas)
        w.writerows(filas)


def glaciares(cache):
    with zipfile.ZipFile(bajar(GLAMBIE, cache / 'glambie.zip')) as z:
        filas = list(csv.DictReader(io.StringIO(z.read(
            'glambie_results_20240716/calendar_years/11_central_europe.csv').decode())))
    escribir('glambie_europa_anual.csv', ['region', 'anio', 'balance_mwe', 'error_mwe'],
             [['central_europe', int(float(r['start_dates'])), r['combined_mwe'], r['combined_mwe_errors']]
              for r in filas])


def lagos(cache):
    """Medias mensuales de altimetría; sin rellenos ni observaciones de hielo."""
    filas = []
    with tarfile.open(bajar(GREALM, cache / 'lake.10.tar.gz')) as t:
        for zona, numero in [('caspio', '000270'), ('victoria', '000314'), ('chad', '000068')]:
            meses = defaultdict(list)
            texto = t.extractfile(f'lake{numero}.10d.2.txt').read().decode()
            for linea in texto.splitlines():
                c = linea.split()
                if len(c) != 16 or not c[2].isdigit():
                    continue
                try:
                    fecha = datetime.datetime.strptime(c[2], '%Y%m%d')
                    altura, error = float(c[14]), float(c[6])
                    if fecha.year > 2025 or abs(float(c[5])) >= 999 or altura >= 9999 or error >= 99 or c[13] == '1':
                        continue
                    meses[fecha.strftime('%Y-%m')].append(altura)
                except ValueError:
                    continue
            filas.extend([zona, mes, sum(v) / len(v), len(v)] for mes, v in sorted(meses.items()))
    escribir('grealm_europa_africa_mensual.csv', ['zona', 'mes', 'nivel_m', 'observaciones'], filas)


# ---------------------------------------------------------------- Mediterráneo (OISST)
def _mascara_mediterraneo(lat, lon):
    """Celdas del Mediterráneo dentro de 30–46° N, 5,5° O–36,5° E (sin Atlántico, Vizcaya, Mármara, mar Negro ni Suez)."""
    LON, LAT = np.meshgrid(lon, lat)
    fuera = ((LON < -5.5) | ((LON < 0) & (LAT > 42)) | ((LON >= 26) & (LAT >= 40.5)) | ((LON > 32.2) & (LAT < 31.2)))
    return ~fuera, LAT


def _media_cuenca(x, lat, lon):
    mar, LAT = _mascara_mediterraneo(lat, lon)
    peso = np.cos(np.deg2rad(LAT)) * mar
    valido = np.isfinite(x) & mar[None]
    return np.nansum(np.nan_to_num(x) * peso, axis=(1, 2)) / np.sum(valido * peso, axis=(1, 2))


def _oisst_psl(anio):
    """Año completo desde el OPeNDAP de NOAA PSL, por tramos de 31 días (rechaza peticiones de un año entero)."""
    import netCDF4
    with netCDF4.Dataset(OISST_PSL.format(a=anio)) as d:
        lat, lon = d['lat'][:], d['lon'][:]
        ii = np.flatnonzero((lat >= 30) & (lat <= 46))
        n, partes, lons = len(d['time']), [], []
        for sel in (np.flatnonzero(lon >= 354.5), np.flatnonzero(lon <= 36.5)):  # 5,5° O–0° y 0°–36,5° E
            partes.append(np.concatenate([d['sst'][t0:min(n, t0 + 31), ii.min():ii.max() + 1,
                                                   sel.min():sel.max() + 1].filled(np.nan) for t0 in range(0, n, 31)]))
            lons.append(np.where(lon[sel] > 180, lon[sel] - 360, lon[sel]))
        media = _media_cuenca(np.concatenate(partes, axis=2), lat[ii], np.concatenate(lons))
        return [str(t)[:10] for t in netCDF4.num2date(d['time'][:], d['time'].units)], media


def _oisst_erddap(cache, anio):
    """Mismo producto desde ERDDAP de CoastWatch; a esta agregación le faltan algunos días."""
    import netCDF4
    bruto = cache / 'oisst_erddap' / f'oisst_{anio}.nc'
    bruto.parent.mkdir(exist_ok=True)
    with netCDF4.Dataset(bajar(OISST_ERDDAP.format(a=anio), bruto, timeout=1800)) as d:
        media = _media_cuenca(np.ma.filled(d['sst'][:, 0].astype(float), np.nan), d['latitude'][:], d['longitude'][:])
        return [str(t)[:10] for t in netCDF4.num2date(d['time'][:], d['time'].units)], media


def _oisst_anio(cache, anio):
    """Media diaria de la cuenca para un año: primero NOAA PSL (años completos); si falla, ERDDAP."""
    destino = cache / f'oisst_mediterraneo_{anio}.npz'
    if not destino.is_file():
        try:
            fechas, media = _oisst_psl(anio)
        except (OSError, RuntimeError) as error:
            print('oisst', anio, 'PSL falló, se usa ERDDAP:', error, file=sys.stderr)
            fechas, media = _oisst_erddap(cache, anio)
        np.savez(destino, fechas=np.array(fechas), sst=media)
        print('oisst', anio, file=sys.stderr, flush=True)
    return destino


def oisst(cache):
    """SST media anual y días en ola de calor marina de la media de cuenca (umbral p90 de 1991–2020, ≥5 días)."""
    from concurrent.futures import ProcessPoolExecutor
    anios = range(1982, 2026)
    with ProcessPoolExecutor(3) as pool:
        rutas = list(pool.map(_oisst_anio, [cache] * len(anios), anios))
    diario = {}
    for ruta in rutas:
        d = np.load(ruta)
        diario.update((datetime.date.fromisoformat(f), float(v)) for f, v in zip(d['fechas'], d['sst']))
    # Calendario diario completo: los días que faltan quedan en NaN y cortan las rachas.
    fechas = [datetime.date(1982, 1, 1) + datetime.timedelta(k)
              for k in range((datetime.date(2025, 12, 31) - datetime.date(1982, 1, 1)).days + 1)]
    sst = np.array([diario.get(f, np.nan) for f in fechas])
    # Día del año en calendario de 365 días: el 29 de febrero comparte umbral con el 28.
    doy = np.array([f.timetuple().tm_yday - 1 - (1 if f.year % 4 == 0 and (f.month, f.day) >= (2, 29) else 0)
                    for f in fechas])
    base = np.array([1991 <= f.year <= 2020 for f in fechas]) & np.isfinite(sst)
    umbral = np.empty(365)
    for k in range(365):  # ventana de 11 días centrada (Hobday et al. 2016)
        cerca = np.minimum(np.abs(doy - k), 365 - np.abs(doy - k)) <= 5
        umbral[k] = np.percentile(sst[base & cerca], 90)
    umbral = np.convolve(np.r_[umbral[-15:], umbral, umbral[:15]], np.ones(31) / 31, 'valid')  # suavizado de 31 días
    caliente = np.nan_to_num(sst, nan=-99) > umbral[doy]
    ola = np.zeros_like(caliente)
    i = 0
    while i < len(caliente):
        j = i
        while j < len(caliente) and caliente[j]:
            j += 1
        if j - i >= 5:
            ola[i:j] = True
        i = max(j, i + 1)
    anios = np.array([f.year for f in fechas])
    escribir('oisst_mediterraneo_anual.csv', ['zona', 'anio', 'sst_c', 'dias_ola_calor', 'dias_con_dato'],
             [['mediterraneo', int(a), round(float(np.nanmean(sst[anios == a])), 4), int(ola[anios == a].sum()),
               int(np.isfinite(sst[anios == a]).sum())] for a in sorted(set(anios))])


# ---------------------------------------------------------------- lluvia (CHIRPS y CRU TS)
def _media_caja(campo, lat, lon, caja):
    """Media de área (cos lat) de las celdas con dato dentro de la caja; campo con forma (tiempo, lat, lon)."""
    s, n, o, e = caja
    ii, jj = np.flatnonzero((lat >= s) & (lat <= n)), np.flatnonzero((lon >= o) & (lon <= e))
    x = campo[:, ii][:, :, jj]
    peso = np.cos(np.deg2rad(lat[ii]))[None, :, None] * np.isfinite(x)
    return np.nansum(np.nan_to_num(x) * peso, axis=(1, 2)) / peso.sum(axis=(1, 2))


def chirps(cache):
    """Lluvia mensual media por caja: la IRI promedia en longitud y aquí se pondera cada latitud por cos(lat) y por su
    número de celdas de tierra (las del mar no tienen dato)."""
    import netCDF4
    filas = []
    for zona, (s, n, o, e) in CAJAS_LLUVIA.items():
        url = dict(x0=o, x1=e, y0=s, y1=n)
        rejilla = bajar(CHIRPS.format(**url, t0=2000, t1=2000, op='T/(Jan%202000)VALUE/'),
                        cache / f'chirps_{zona}_enero2000.nc')
        with netCDF4.Dataset(rejilla) as r:
            lat = r['Y'][:]
            campo = np.ma.filled(r['precipitation'][:].astype(float), np.nan).reshape(-1, len(r['Y']), len(r['X']))[0]
        peso = np.cos(np.deg2rad(lat)) * np.isfinite(campo).sum(axis=1)

        def tramo(t0):  # la IRI corta las peticiones largas: tramos de 5 años
            return bajar(CHIRPS.format(**url, t0=t0, t1=min(t0 + 4, 2025), op='%5BX%5Daverage/'),
                         cache / f'chirps_{zona}_xmedia_{t0}.nc', timeout=1800)
        with ThreadPoolExecutor(4) as pool:
            tramos = list(pool.map(tramo, range(1981, 2026, 5)))
        for ruta in tramos:
            with netCDF4.Dataset(ruta) as d:
                p = d['precipitation']
                x = np.ma.filled(p[:].astype(float), np.nan)
                if p.dimensions.index('T') > p.dimensions.index('Y'):
                    x = x.T
                assert np.allclose(d['Y'][:], lat)
                media = np.nansum(np.nan_to_num(x) * peso, axis=1) / np.sum(np.isfinite(x) * peso, axis=1)
                assert d['T'].units.startswith('months since 1960-01-01')  # convención de la IRI
                meses = np.floor(d['T'][:]).astype(int)
            filas += [[zona, f'{1960 + m // 12:04d}-{m % 12 + 1:02d}', round(float(v), 3)] for m, v in zip(meses, media)]
    escribir('chirps_africa_mensual.csv', ['zona', 'mes', 'lluvia_mm'], filas)


def cru(cache):
    import netCDF4
    (cache / 'cru').mkdir(exist_ok=True)
    filas = []
    for p in ('1981.1990', '1991.2000', '2001.2010', '2011.2020', '2021.2025'):
        gz = bajar(CRU + f'cru_ts4.10.{p}.pre.dat.nc.gz', cache / 'cru' / f'cru_ts4.10.{p}.pre.dat.nc.gz')
        nc_ = gz.with_suffix('')
        if not nc_.is_file():
            nc_.write_bytes(gzip.decompress(gz.read_bytes()))
        with netCDF4.Dataset(nc_) as d:
            lat, lon = d['lat'][:], d['lon'][:]
            fechas = netCDF4.num2date(d['time'][:], d['time'].units)
            pre = np.ma.filled(d['pre'][:].astype(float), np.nan)
            stn = np.ma.filled(d['stn'][:].astype(float), np.nan)
            for zona, caja in CAJAS_LLUVIA.items():
                lluvia = _media_caja(pre, lat, lon, caja)
                estaciones = _media_caja(np.where(np.isfinite(pre), stn, np.nan), lat, lon, caja)
                filas += [[zona, f'{f.year:04d}-{f.month:02d}', round(float(v), 3), round(float(s), 3)]
                          for f, v, s in zip(fechas, lluvia, estaciones)]
    escribir('cru_africa_mensual.csv', ['zona', 'mes', 'lluvia_mm', 'estaciones_por_celda'], sorted(filas))


# ---------------------------------------------------------------- agua total (GRACE CSR)
def grace(cache):
    import h5py
    with h5py.File(bajar(CSR + CSR_MASCONES, cache / 'csr_mascons.nc')) as f, \
         h5py.File(bajar(CSR + CSR_TIERRA, cache / 'csr_landmask.nc')) as m:
        lat, lon = f['lat'][:], f['lon'][:]
        fecha = np.datetime64('2002-01-01') + np.floor(f['time'][:]).astype(int).astype('timedelta64[D]')
        tierra = m['LO_val'][:] > 0.5
        LON, LAT = np.meshgrid(np.where(lon > 180, lon - 360, lon), lat)
        s, n, o, e = CAJA_GRACE
        sel = tierra & (LAT > s) & (LAT < n) & (LON > o) & (LON < e)
        area = np.cos(np.deg2rad(LAT))[sel]
        lwe = f['lwe_thickness']  # cm de agua equivalente respecto a 2004–2009
        filas = [['tigris_eufrates', str(d)[:7], round(float(np.sum(lwe[i][sel] * area) / area.sum()), 3)]
                 for i, d in enumerate(fecha)]
    escribir('grace_oriente_medio_mensual.csv', ['zona', 'mes', 'agua_cm'], filas)


PASOS = {'glaciares': glaciares, 'lagos': lagos, 'oisst': oisst, 'chirps': chirps, 'cru': cru, 'grace': grace}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cache', type=Path, required=True, help='carpeta para las descargas (no se versiona)')
    ap.add_argument('--solo', nargs='*', choices=sorted(PASOS), help='ejecutar solo estos pasos')
    args = ap.parse_args()
    cache = args.cache.resolve()
    if cache == RAIZ or RAIZ in cache.parents:
        raise ValueError('La caché debe estar fuera del repositorio')
    cache.mkdir(parents=True, exist_ok=True)
    for nombre in args.solo or PASOS:
        PASOS[nombre](cache)
        print('hecho:', nombre, file=sys.stderr)


if __name__ == '__main__':
    main()
