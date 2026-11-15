"""Series de Europa y África; integración sin acceso a red."""
import csv
from pathlib import Path
from . import recursos

LUGARES = {
    'glaciares_europa_central': ('Central European glaciers', 'RGI region 11', [46.5, 10.0], 5),
}
ESTUDIOS = {
    'glaciares': 'Published check: GlaMBIE documents glacier mass loss in Central Europe during 2000–2023 (doi:10.1038/s41586-024-08545-z).',
}
recursos.LUGARES.update(LUGARES)


def _glaciares(carpeta):
    """Devuelve investigaciones y archivos de entrada disponibles."""
    ruta = Path(carpeta) / 'glambie_europa_anual.csv'
    if not ruta.is_file():
        return [], []
    with ruta.open(encoding='utf-8') as f:
        filas = sorted(csv.DictReader(f), key=lambda r: int(r['anio']))
    if not filas:
        return [], []
    inv = recursos._investigacion(
        'glaciares_europa_central', 'polos', 'glaciares_europa_central',
        'Central European glacier mass balance',
        'Ice gained or lost each year, expressed as an equivalent depth of water. Negative values mean ice loss.',
        'm w.e.', [int(r['anio']) for r in filas], [float(r['balance_mwe']) for r in filas],
        {'producto': 'GlaMBIE 1.0.0, region 11, calendar years',
         'url': 'https://doi.org/10.5904/wgms-glambie-2024-07'},
        notas=[ESTUDIOS['glaciares'],
               'The trend measures changes in annual mass balance, not cumulative ice loss.',
               'Regional averages do not describe every glacier. Source uncertainty is retained in the CSV.'])
    return [inv], [ruta]


LAGOS = {
    'caspio': ('Caspian Sea', [42, 51], '10.1002/2017GL073958', 'The Caspian Sea level declined after the mid-1990s.'),
    'victoria': ('Lake Victoria', [-0.5, 33.5], '10.3390/s21134304', 'Lake Victoria rose sharply in 2019–2020.'),
    'chad': ('Lake Chad', [13, 14], '10.1038/s41598-020-62417-w', 'Modern Lake Chad variability differs from its earlier historical collapse.'),
}
for zona, (nombre, centro, doi, texto) in LAGOS.items():
    LUGARES[zona] = (nombre, 'G-REALM satellite track', centro, 5)
    ESTUDIOS[zona] = f'Published check: {texto} (doi:{doi}).'
recursos.LUGARES.update(LUGARES)


# ---------------------------------------------------------------- Mediterráneo, lluvia de África y GRACE
LUGARES.update({
    'mediterraneo': ('Mediterranean Sea', 'Box 30–46° N, 5.5° W–36.5° E, sea only', [38.0, 15.0], 4),
    'africa_oriental': ('Eastern Kenya and southern Somalia', 'Box 4° S–6° N, 38–48° E', [1.0, 43.0], 5),
    'sahel': ('Western and central Sahel', 'Box 10–20° N, 17° W–20° E', [15.0, 1.5], 4),
    'tigris_eufrates': ('Tigris–Euphrates basin and western Iran', 'Box 30–38° N, 38–48° E', [34.0, 43.0], 5),
})
recursos.LUGARES.update(LUGARES)
ESTUDIOS.update({
    'mediterraneo_sst': 'Published check: satellite sea surface temperature shows the Mediterranean Sea warming over '
                        '1982–2018 (Pisano et al. 2020, doi:10.3390/rs12010132).',
    'mediterraneo_olas': 'Published check: marine heatwaves in the Mediterranean Sea became more frequent and longer '
                         '(Dayan et al. 2023, doi:10.3389/fmars.2023.1045138); the heatwave rule follows Hobday et al. '
                         '2016 (doi:10.1016/j.pocean.2015.12.014).',
    'lluvias_largas': 'Published check: rain gauges and satellites show the East African long rains (March–May) '
                      'declining from the late 1990s (Lyon & DeWitt 2012, doi:10.1029/2011GL050337), mostly because '
                      'the season got shorter (Wainwright et al. 2019, doi:10.1038/s41612-019-0091-7).',
    'lluvias_cortas': 'Published check: the short rains (October–December) behave differently from the long rains and '
                      'are strongly driven by the Indian Ocean Dipole and El Niño (Palmer et al. 2023, '
                      'doi:10.1038/s43017-023-00397-x).',
    'sahel': 'Published check: observations show Sahel summer rain partly recovering after the 1970s–1980s droughts, '
             'without returning to the wet 1950s–1960s (Biasutti 2019, doi:10.1002/wcc.591).',
    'grace_oriente': 'Published check: GRACE measured a fast loss of total water, mostly groundwater, in the '
                     'Tigris–Euphrates basin and western Iran from 2003 to 2009 (Voss et al. 2013, '
                     'doi:10.1002/wrcr.20078).',
})
OISST = {'producto': 'NOAA OISST v2.1 daily 0.25° (NOAA CoastWatch ERDDAP)',
         'url': 'https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.html'}
CHIRPS = {'producto': 'CHIRPS v2.0 monthly 0.05° (UCSB Climate Hazards Center), via IRI Data Library',
          'url': 'https://www.chc.ucsb.edu/data/chirps'}
CRU = {'producto': 'CRU TS 4.10 monthly rainfall 0.5° (University of East Anglia)',
       'url': 'https://crudata.uea.ac.uk/cru/data/hrg/'}
GRACE = {'producto': 'GRACE/GRACE-FO mascons, CSR RL06.03 (University of Texas at Austin)',
         'url': 'https://www2.csr.utexas.edu/grace/RL06_mascons.html'}


def _leer(ruta):
    with Path(ruta).open(encoding='utf-8') as f:
        return list(csv.DictReader(f))


def _mediterraneo(carpeta):
    ruta = Path(carpeta) / 'oisst_mediterraneo_anual.csv'
    if not ruta.is_file():
        return [], []
    filas = sorted((r for r in _leer(ruta) if int(r['dias_con_dato']) >= 350), key=lambda r: int(r['anio']))
    anios = [int(r['anio']) for r in filas]
    huecos = [f"{r['anio']} ({(366 if int(r['anio']) % 4 == 0 else 365) - int(r['dias_con_dato'])})" for r in filas
              if int(r['dias_con_dato']) < (366 if int(r['anio']) % 4 == 0 else 365)]
    aviso = ('Days missing in the source, by year: ' + ', '.join(huecos) + '. Yearly values use the days available.'
             if huecos else 'No days are missing in the source.')
    comun = 'Average over all sea cells of the basin, weighted by area; the Black Sea and the Atlantic are left out.'
    return [
        recursos._investigacion(
            'mediterraneo_sst', 'costa', 'mediterraneo', 'Mediterranean sea surface temperature',
            'Yearly average temperature of the sea surface across the whole Mediterranean, from satellites, ships and '
            'buoys.', '°C', anios, [float(r['sst_c']) for r in filas], OISST,
            notas=[ESTUDIOS['mediterraneo_sst'], comun, aviso]),
        recursos._investigacion(
            'mediterraneo_olas_calor', 'costa', 'mediterraneo', 'Days in a Mediterranean marine heatwave',
            'Days of the year when the basin-average sea surface was in a marine heatwave: at least 5 days in a row '
            'warmer than 9 in 10 days of 1991–2020 for that time of year.', 'days', anios,
            [int(r['dias_ola_calor']) for r in filas], OISST,
            notas=[ESTUDIOS['mediterraneo_olas'], comun, aviso,
                   'This counts heatwaves of the basin average. Part of the sea can be in a heatwave while the '
                   'average stays below the threshold, so local counts are higher.',
                   'The threshold is fixed to 1991–2020, so it includes the long-term warming of the sea: more '
                   'heatwave days mean both a warmer background and more extreme spells.'])], [ruta]


def _estacional(filas, zona, meses):
    """Total de lluvia de la temporada por año; solo años con todos los meses."""
    por = {}
    for r in filas:
        if r['zona'] == zona and int(r['mes'][5:7]) in meses and r['lluvia_mm'] not in ('', 'nan'):
            por.setdefault(int(r['mes'][:4]), []).append(float(r['lluvia_mm']))
    return {a: sum(v) for a, v in sorted(por.items()) if len(v) == len(meses)}


def _lluvia_africa(carpeta):
    invs, entradas = [], []
    ruta_ch, ruta_cru = Path(carpeta) / 'chirps_africa_mensual.csv', Path(carpeta) / 'cru_africa_mensual.csv'
    aviso_chirps = ('CHIRPS mixes satellite estimates with rain-gauge reports; the number of gauges changed over '
                    'time and is low in Somalia and the Sahel.')
    if ruta_ch.is_file():
        entradas.append(ruta_ch)
        filas = _leer(ruta_ch)
        for id_, meses, titulo, definicion, estudio in (
                ('lluvias_largas_africa_oriental', (3, 4, 5), 'East African long rains (March–May)',
                 'Total rain from March to May, averaged over the land of eastern Kenya and southern Somalia.',
                 'lluvias_largas'),
                ('lluvias_cortas_africa_oriental', (10, 11, 12), 'East African short rains (October–December)',
                 'Total rain from October to December, averaged over the land of eastern Kenya and southern Somalia.',
                 'lluvias_cortas')):
            total = _estacional(filas, 'africa_oriental', meses)
            invs.append(recursos._investigacion(
                id_, 'lluvia', 'africa_oriental', titulo, definicion, 'mm', list(total), list(total.values()), CHIRPS,
                notas=[ESTUDIOS[estudio], 'The two rainy seasons are kept apart: a yearly total would mix two '
                       'seasons that can change in opposite ways.', aviso_chirps]))
        total = _estacional(filas, 'sahel', (6, 7, 8, 9))
        invs.append(recursos._investigacion(
            'lluvia_jjas_sahel_chirps', 'lluvia', 'sahel', 'Sahel rainy-season rain (CHIRPS)',
            'Total rain from June to September, averaged over the land of the western and central Sahel.', 'mm',
            list(total), list(total.values()), CHIRPS,
            notas=[ESTUDIOS['sahel'], 'The record starts in 1981, close to the driest years of the 1980s, so a '
                   'rise since then partly reflects recovery from that drought.', aviso_chirps]))
    if ruta_cru.is_file():
        entradas.append(ruta_cru)
        filas = _leer(ruta_cru)
        total = _estacional(filas, 'sahel', (6, 7, 8, 9))
        estaciones = {}
        for r in filas:
            if r['zona'] == 'sahel' and 6 <= int(r['mes'][5:7]) <= 9:
                estaciones.setdefault(int(r['mes'][:4]), []).append(float(r['estaciones_por_celda']))
        anios = list(total)
        primero, ultimo = (sum(estaciones[a]) / len(estaciones[a]) for a in (anios[0], anios[-1]))
        invs.append(recursos._investigacion(
            'lluvia_jjas_sahel_cru', 'lluvia', 'sahel', 'Sahel rainy-season rain (CRU, rain gauges)',
            'Total rain from June to September, averaged over the western and central Sahel, from a map built only '
            'from rain gauges.', 'mm', anios, list(total.values()), CRU,
            notas=[ESTUDIOS['sahel'], f'Gauges feeding each grid cell, on average: {primero:.1f} in {anios[0]} and '
                   f'{ultimo:.1f} in {anios[-1]}. With fewer gauges, the map leans more on long-term averages.',
                   'Compare with the CHIRPS series of the same box: two products can disagree, which is a separate '
                   'question from whether the trend tests agree.']))
    return invs, entradas


def _grace_oriente(carpeta):
    ruta = Path(carpeta) / 'grace_oriente_medio_mensual.csv'
    if not ruta.is_file():
        return [], []
    filas = _leer(ruta)
    ultimo = max(int(r['mes'][:4]) for r in filas)
    medias = recursos._anuales_mensuales(filas, 'agua_cm', minimo=9)
    anios = [a for a in medias if a < ultimo]
    return [recursos._investigacion(
        'grace_agua_tigris_eufrates', 'agua', 'tigris_eufrates', 'Total water stored on land (GRACE)',
        'All water held in soil, rivers, lakes, reservoirs and aquifers over the Tigris–Euphrates basin and western '
        'Iran, compared with its 2004–2009 average and weighed by gravity satellites.', 'cm', anios,
        [medias[a] for a in anios], GRACE,
        notas=[ESTUDIOS['grace_oriente'], 'Years with fewer than 9 months of data are left out, including the '
               '2017–2018 gap between the two missions, and the current year.',
               'Gravity satellites see blocks of about 300 km, so this is a regional total, not a map of wells.'])], [ruta]


def europa_africa(carpeta):
    investigaciones, entradas = _glaciares(carpeta)
    for parte in (_mediterraneo, _lluvia_africa, _grace_oriente):
        i, e = parte(carpeta)
        investigaciones += i
        entradas += e
    ruta = Path(carpeta) / 'grealm_europa_africa_mensual.csv'
    if ruta.is_file():
        entradas.append(ruta)
        with ruta.open(encoding='utf-8') as f:
            filas = list(csv.DictReader(f))
        for zona, (nombre, _, _, _) in LAGOS.items():
            propias = [r for r in filas if r['zona'] == zona]
            if zona == 'caspio':
                propias = [r for r in propias if 4 <= int(r['mes'][5:7]) <= 10]
            anual = recursos._anuales_mensuales(propias, 'nivel_m', minimo=7 if zona == 'caspio' else 12)
            if not anual:
                continue
            investigaciones.append(recursos._investigacion(
                f'nivel_{zona}_grealm', 'agua', zona, f'{nombre} water level' + (' (April–October)' if zona == 'caspio' else ''),
                'Average water level measured along a satellite track, relative to the EGM2008 geoid.',
                'm', list(anual), list(anual.values()),
                {'producto':'NASA GSFC G-REALM 10-day altimetry', 'url':'https://earth.gsfc.nasa.gov/gwm/zip/lake.10.tar.gz'},
                notas=[ESTUDIOS[zona], ('Caspian means require all seven months from April to October, excluding winter ice.' if zona == 'caspio' else 'Annual means require all 12 monthly means. Missing years are omitted, not interpolated.'),
                       'Water level is not lake area or volume. Rainfall, evaporation and water management can affect the level.',
                       'Shallow water and vegetation can affect radar measurements, especially at Lake Chad.']))
    return investigaciones, entradas
