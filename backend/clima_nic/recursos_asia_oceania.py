"""Series observadas del agente 3; integración sin red a partir de CSV pequeños.

No modifica el motor estadístico. Los DOI se comprobaron en Crossref el 14-11-2026.
Las citas describen el alcance de cada publicación, no sustituyen el cálculo sobre nuestra serie.
"""
import csv
import math
from pathlib import Path

from . import recursos

LUGARES = {
    'ao_funafuti_b': ('Funafuti B tide gauge', 'Tuvalu', [-8.502472, 179.195167], 9),
    'ao_betio': ('Betio tide gauge', 'Kiribati', [1.365056, 172.933], 9),
    'ao_lautoka': ('Lautoka tide gauge', 'Fiji', [-17.604917, 177.43825], 9),
    'ao_manila': ('Manila South Harbor tide gauge', 'Philippines', [14.583333, 120.966667], 9),
    'ao_auckland_ii': ('Auckland II historical tide gauge', 'New Zealand', [-36.84307, 174.76946], 9),
    'ao_altimetria_global': ('Global satellite sea level', 'Reference altimeter missions', [0, 0], 2),
    'ao_calor_global': ('Global upper ocean', '0–2000 m depth', [0, 0], 2),
    'ao_india_central': ('Central India monsoon box', '19–26°N, 76–86°E', [22.5, 81], 5),
    'ao_yangtze': ('Middle and lower Yangtze study box', 'China: 27–34°N, 110–122°E', [30.5, 116], 5),
    'ao_mar_japon': ('East Sea / Sea of Japan', 'Ocean cells: 34–46°N, 128–140°E', [40, 134], 5),
    'ao_siberia': ('Siberian land temperature box', 'Russia: 55–70°N, 80–140°E', [62.5, 110], 3),
    'ao_gbr_northern': ('Northern Great Barrier Reef', 'Australia: NOAA virtual station', [-14.5, 145.5], 6),
    'ao_gbr_central': ('Central Great Barrier Reef', 'Australia: NOAA virtual station', [-18.5, 147.5], 6),
    'ao_gbr_southern': ('Southern Great Barrier Reef', 'Australia: NOAA virtual station', [-22, 151.5], 6),
    'ao_aral': ('Aral Sea study box', 'Kazakhstan / Uzbekistan: 43–47.5°N, 57–62°E', [45.25, 59.5], 6),
}
# Se fusiona al importar, antes de que construir() seleccione los lugares usados.
for _id, _lugar in LUGARES.items():
    if _id in recursos.LUGARES and recursos.LUGARES[_id] != _lugar:
        raise ValueError(f'ID de lugar ya utilizado: {_id}')
recursos.LUGARES.update(LUGARES)

ESTUDIOS = {
    'psmsl': 'Published check: PSMSL provides datum-controlled relative sea-level records; this citation documents the archive, not a slope at these Pacific stations. doi:10.2112/JCOASTRES-D-12-00175.1',
    'manila': 'Published check: coastal vertical land motion includes subsidence associated with groundwater extraction in Manila; relative sea level is not ocean rise alone. doi:10.1016/j.srs.2024.100176',
    'auckland': 'Published check: long tide-gauge records show relative sea-level rise in New Zealand, with regional differences; the national estimate is not an Auckland-specific slope. doi:10.1029/2011JC007591',
    'gmsl': 'Published check: reference satellite altimeters show rising global mean sea level; acceleration was estimated separately over 1993–2017. doi:10.1073/pnas.1717312115',
    'ohc': 'Published check: observed global 0–2000 m heat content increased over 1955–2010; the annual NOAA file used here starts in 2005. doi:10.1029/2012GL051106',
    'monzon': 'Published check: central Indian monsoon rainfall declined over 1950–2015 in an IMD analysis; this CRU box and extended period are an independent check. doi:10.1038/s41467-017-00744-9',
    'china': 'Published check: precipitation extremes in the middle and lower Yangtze generally increased in a 1960–2019 station analysis; this summer CPC box is a different spatial aggregate. doi:10.1016/j.scitotenv.2020.144244',
    'ersst': 'Published check: East Sea / Sea of Japan surface waters warmed over 1982–2018, with slower warming and winter cooling in some recent windows; that study used OISST, not this ERSST box. doi:10.3390/rs11222613',
    'siberia': 'Published check: GISTEMP v4 estimates surface air temperature from station observations and quantifies sampling uncertainty; it does not measure deep permafrost. doi:10.1029/2018JD029522',
    'coral': 'Published check: repeated Great Barrier Reef bleaching followed the spatial pattern of marine heat exposure; these virtual-station DHW series measure heat stress, not coral mortality. doi:10.1038/nature21707',
    'aral': 'Published check: satellite observations show strong Aral Sea contraction, while the northern basin behaved differently; this box also includes nearby inland waters. doi:10.1002/2014JC009988',
}

PSMSL = 'https://psmsl.org/data/obtaining/rlr.annual.data/{}.rlrdata'
SERIES = {}
for _numero, _nombre, _estudio in ((1839, 'funafuti_b', 'psmsl'), (1804, 'betio', 'psmsl'),
                                    (1805, 'lautoka', 'psmsl'), (145, 'manila', 'manila'), (150, 'auckland_ii', 'auckland')):
    SERIES[f'nivel_mar_{_nombre}'] = dict(
        categoria='costa', lugar=f'ao_{_nombre}', titulo='Relative sea level at the gauge',
        definicion='Yearly sea level measured against the land. It includes local sinking or rising of the ground.',
        unidad='mm', estudio=_estudio, producto='PSMSL Revised Local Reference annual means',
        version='RLR annual archive, snapshot 2026-11-14', url=PSMSL.format(_numero),
        notas=['Missing values and attention-flagged years are excluded. Some accepted annual means include interpolated months; gaps remain visible.',
               'No vertical land-motion correction is applied. A detected trend does not by itself establish human climate attribution.']
              + (['Historical record only: this downloaded annual series ends before the present. Values are relative to the mean of available 1993–2020 years.'] if _numero == 150 else
                 ['Values are relative to the mean of available 1993–2020 years. Changing this baseline does not change the trend.'])
              + (['PSMSL flags the site for attention. The gauge moved during 2002; reclamation, river deposits and land subsidence can affect this record.'] if _numero == 145 else []))

SERIES.update({
    'nivel_mar_global_altimetria': dict(categoria='costa', lugar='ao_altimetria_global', titulo='Global mean sea level',
        definicion='Average ocean height measured by reference satellite altimeters, averaged first by month and then by year.',
        unidad='mm', estudio='gmsl', producto='NASA-supported University of Colorado satellite GMSL', version='2026_rel1, seasons retained',
        url='https://sealevel.colorado.edu/files/2026_rel1/gmsl_2026rel1_seasons_retained.txt',
        notas=['Altimetry data are supplied with their published GIA treatment; no additional GIA correction is applied here. Changing missions requires cross-calibration.',
               'Only years with all calendar months are used. ENSO affects year-to-year ocean height. A Sen slope tests rise, not acceleration.']),
    'oceano_global_contenido_calor_2000m': dict(categoria='costa', lugar='ao_calor_global', titulo='Upper ocean heat content',
        definicion='Heat stored in the global ocean from the surface to 2000 metres, expressed as an anomaly from the provider reference.',
        unidad='10²² J', estudio='ohc', producto='NOAA NCEI World Ocean heat content, annual 0–2000 m', version='Operational annual file, snapshot 2026-11-14',
        url='https://www.ncei.noaa.gov/data/oceans/woa/DATA_ANALYSIS/3M_HEAT_CONTENT/DATA/basin/yearly/h22-w0-2000m.dat',
        notas=['These are already annual estimates: they are not summed again. Historical overlapping pentads are not treated as annual observations.',
               'Instrument changes, Argo coverage and retrospective analysis updates contribute uncertainty.']),
    'monzon_india_central_lluvia_total': dict(categoria='lluvia', lugar='ao_india_central', titulo='Monsoon rainfall at sampled cells',
        definicion='Total rain from June through September, averaged over a fixed set of land cells in central India.',
        unidad='mm', estudio='monzon', producto='CRU TS 4.10 monthly precipitation', version='4.10, 0.5°',
        url='https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/cruts.2604091129.v4.10/pre/',
        notas=['This is a station-based gridded analysis, not a climate projection. Cells with no contributing stations are excluded from the fixed spatial cohort.',
               'The strict fixed cohort is a sampled subset, not complete regional coverage. Monthly totals are summed over June–September; this cannot count extreme rain days. ENSO and the period matter.']),
    'yangtze_lluvia_extrema_verano': dict(categoria='lluvia', lugar='ao_yangtze', titulo='Summer maximum daily rain',
        definicion='The wettest summer day at each grid cell, averaged over a fixed study box; it need not be the same day across the region.',
        unidad='mm', estudio='china', producto='NOAA CPC Global Unified daily precipitation', version='V1.0, 0.5°',
        url='https://psl.noaa.gov/data/gridded/data.cpc.globalprecip.html',
        notas=['June–August only; each summer must contain every day. The box represents part of the Yangtze region, not the exact river basin.',
               'Summers with no fully observed cells are excluded, leaving gaps in 1985 and 1992. A fixed cohort covers the same land cells in retained summers. Gridding smooths extremes; station changes, ENSO and monsoon variability matter.']),
    'mar_japon_temperatura_superficial': dict(categoria='costa', lugar='ao_mar_japon', titulo='Sea surface temperature',
        definicion='Yearly mean temperature of ocean cells in the East Sea / Sea of Japan study box, weighted by area and days per month.',
        unidad='°C', estudio='ersst', producto='NOAA ERSSTv5 monthly sea surface temperature', version='v5, 2°',
        url='https://psl.noaa.gov/thredds/catalog/Datasets/noaa.ersst.v5/catalog.html',
        notas=['A fixed set of valid ocean cells is used. Coarse cells cannot resolve individual coastal bays or all currents.',
               'Ship and buoy observations are statistically reconstructed; this is not daily OISST. Winter circulation and the chosen period affect regional warming.']),
    'siberia_temperatura_aire': dict(categoria='temperatura', lugar='ao_siberia', titulo='Siberian air temperature anomaly',
        definicion='Yearly surface air temperature compared with 1951–1980 over a fixed set of Siberian land cells. This is not deep permafrost temperature.',
        unidad='°C', estudio='siberia', producto='NASA GISS GISTEMP v4 land air temperature', version='v4, 250 km smoothing, 2° grid',
        url='https://data.giss.nasa.gov/pub/gistemp/gistemp250_GHCNv4.nc.gz',
        notas=['Only cells valid in every selected month are retained. Sparse station coverage and homogenization changes affect the regional estimate.',
               'Air temperature is a declared alternative indicator, not a measurement of permafrost thaw, methane release or underground temperature.']),
    'mar_aral_superficie_agua': dict(categoria='agua', lugar='ao_aral', titulo='Water in the Aral study box',
        definicion='Area where satellites detected seasonal or permanent water during the year inside the fixed Aral study box.',
        unidad='km²', estudio='aral', producto='JRC Global Surface Water Yearly Classification', version='v1.4, 30 m nominal, 1984–2021',
        url='https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GSWE/YearlyClassification/LATEST/tiles/',
        notas=['This is a study-box indicator, not an exact historical shoreline polygon. It includes nearby inland waters; it is not water volume or mean annual area.',
               'Years need at least 95% coverage of the observable footprint. Water area is then measured only on cells classified in EVERY retained year, a fixed subset rather than the full lake. Irrigation, dams and basin differences prevent simple climate attribution.']),
})
for _zona in ('northern', 'central', 'southern'):
    SERIES[f'gran_barrera_dhw_{_zona}'] = dict(categoria='costa', lugar=f'ao_gbr_{_zona}', titulo='Peak coral heat stress',
        definicion='Highest daily Degree Heating Weeks value during a complete calendar year at this NOAA regional virtual station.',
        unidad='°C-weeks', estudio='coral', producto='NOAA Coral Reef Watch regional virtual station', version='v3.1, daily 5 km inputs',
        url=f'https://coralreefwatch.noaa.gov/product/vs/data/gbr_{_zona}.txt',
        notas=['The virtual station uses NOAA regional summary statistics. It is not the spatial mean of each reef pixel annual maximum; the three regions are kept separate.',
               'Only complete years are included. DHW measures accumulated heat exposure, not observed bleaching or coral mortality. ENSO and changes in satellite inputs matter.'])


def asia_oceania(carpeta):
    """Devuelve investigaciones y rutas de entrada; sin CSV no añade ninguna serie."""
    carpeta = Path(carpeta)
    ruta = carpeta / 'asia_oceania_anual.csv'
    if not ruta.is_file():
        return [], []
    por, cohortes = {}, {}
    with ruta.open(encoding='utf-8', newline='') as f:
        for fila in csv.DictReader(f):
            id_, anio, valor = fila['id'], int(fila['anio']), float(fila['valor'])
            if id_ not in SERIES or not math.isfinite(valor):
                raise ValueError(f'Serie desconocida o valor inválido: {id_}')
            puntos = por.setdefault(id_, {})
            if anio in puntos:
                raise ValueError(f'Año duplicado: {id_} {anio}')
            puntos[anio] = valor
            if fila.get('celdas_cohorte'):
                n = int(fila['celdas_cohorte'])
                if n <= 0 or (id_ in cohortes and cohortes[id_] != n):
                    raise ValueError(f'Cohorte inconsistente: {id_}')
                cohortes[id_] = n
    investigaciones = []
    for id_, puntos in sorted(por.items()):
        s = SERIES[id_]
        # Los huecos quedan como null para no dibujar continuidad instrumental inexistente.
        anios = list(range(min(puntos), max(puntos) + 1))
        fuente = {'producto': s['producto'], 'url': s['url'], 'version': s['version'], 'requiere_cuenta': False}
        notas = s['notas'] + [ESTUDIOS[s['estudio']]]
        if id_ in cohortes:
            notas += [f'This series uses a fixed cohort of {cohortes[id_]} grid cells.']
        investigaciones.append(recursos._investigacion(id_, s['categoria'], s['lugar'], s['titulo'], s['definicion'],
            s['unidad'], anios, [puntos.get(a) for a in anios], fuente,
            notas=notas))
    entradas = [ruta]
    recibos = carpeta / 'asia_oceania_fuentes.csv'
    if recibos.is_file():
        entradas.append(recibos)
    return investigaciones, entradas
