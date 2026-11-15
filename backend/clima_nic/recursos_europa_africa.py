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


def europa_africa(carpeta):
    investigaciones, entradas = _glaciares(carpeta)
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
