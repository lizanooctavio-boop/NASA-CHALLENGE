"""Regional GISTEMP with existing read/aggregate adapters; no Nicaragua crop.

Run from repo root: python data/recursos/csa/canada.py
IMERG requires Canadian HDF5 subsets: existing Imerg.leer hardcodes Nicaragua.
Never reuse Nicaragua rainfall for Canada. See csa.md for the blocking issue.
"""
import json
import calendar
import re
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'backend'))
from clima_nic.fuentes.gistemp import Gistemp
from clima_nic.fuentes.base import recortar_malla
from clima_nic.regiones import cargar
from clima_nic.estadistica.tendencia_robusta import analizar
from clima_nic.fuentes.base import a_anual


def leer_imerg_canada(ruta):
    """Read Canadian cells from a monthly IMERG HDF5, without modifying Imerg.

    Includes a one-cell halo around Prairies; missing pixels remain NaN.
    Dataset units must be mm/hr or mm/h; no silent interpretation of daily data.
    """
    import h5py
    with h5py.File(ruta, 'r') as f:
        g = f['Grid']
        lat, lon = g['lat'][:], g['lon'][:]
        iy = np.flatnonzero((lat >= 48.8) & (lat <= 54.4))
        ix = np.flatnonzero((lon >= -114.8) & (lon <= -96.4))
        if not len(iy) or not len(ix):
            raise ValueError('IMERG file contains no Canadian study-region cells')
        v = g['precipitation']
        unit = v.attrs.get('units', '')
        if isinstance(unit, bytes):
            unit = unit.decode()
        if str(unit).strip().lower() not in ('mm/hr', 'mm/h'):
            raise ValueError(f'Expected monthly IMERG mm/hr, got {unit!r}')
        field = v[0, ix[0]:ix[-1]+1, iy[0]:iy[-1]+1].astype(float).T
        fill = v.attrs.get('_FillValue', -9999.9)
        field[(field < 0) | (field == fill)] = np.nan
        return lat[iy], lon[ix], field


def lluvia_canada(archivos, salida):
    """Area-weighted monthly rates -> annual mm; require twelve valid months.

    Track valid spatial fraction rather than silently accepting incomplete AOI.
    Monthly coverage below 95% makes that year ineligible for the trend.
    """
    from clima_nic.rutas import sha256, proyectar_6933
    regions = cargar(ROOT / 'data/regiones_canada.geojson')
    polygon_km2 = proyectar_6933(regions['CAN_prairies']).area / 1e6
    months, vals, coverage, sources = [], [], [], []
    weights, grid = None, None
    for path in sorted(map(Path, archivos)):
        match = re.search(r'\.(\d{4})(\d{2})\d{2}-S', path.name)
        if not match:
            raise ValueError(f'Unrecognized monthly IMERG filename: {path.name}')
        year, month = map(int, match.groups())
        key = f'{year:04d}-{month:02d}'
        if key in months:
            raise ValueError(f'Duplicate month: {key}')
        lat, lon, field = leer_imerg_canada(path)
        signature = (tuple(lat), tuple(lon))
        if signature != grid:
            weights = None
            grid = signature
        means, weights = recortar_malla(lat, lon, field, regions, weights)
        valid, _ = recortar_malla(lat, lon, np.isfinite(field).astype(float), regions, weights)
        grid_km2 = sum(p['CAN_prairies'] for p in weights)
        cov = min(1.0, float(valid['CAN_prairies'][0]) * grid_km2 / polygon_km2)
        value = float(means['CAN_prairies'][0]) * calendar.monthrange(year, month)[1] * 24
        months.append(key)
        vals.append(value if cov >= .95 else np.nan)
        coverage.append(cov)
        sources.append({'file': path.name, 'sha256': sha256(path)})
    years, annual = a_anual(months, vals)
    out = {'region':'CAN_prairies', 'papel':'tendencia', 'producto':'GPM_3IMERGM V07B',
           'unidad':'mm/year', 'anios':years, 'valores':annual,
           'meses':months, 'cobertura_valida':coverage, 'fuentes':sources,
           'criterio':'12 valid months per year; each month >=95% valid polygon area',
           'tendencia':analizar(years, annual, 'mm') if len(years) >= 10 else None}
    Path(salida).write_text(json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    return out


def main():
    a = Gistemp()
    lat, lon, values, dates = a.leer(a.descargar()[0])
    y = (lat >= 48) & (lat <= 56)
    x = (lon >= -116) & (lon <= -94)
    regions = cargar(ROOT / 'data/regiones_canada.geojson')
    means, _ = recortar_malla(lat[y], lon[x], values[:, y][:, :, x], regions)
    months = [str(d)[:7] for d in dates.astype('datetime64[M]')]
    series = a.agregar((months, means))[0]
    pairs = [(t, v) for t, v in zip(series.tiempos, series.valores) if 2001 <= t <= 2024 and np.isfinite(v)]
    years, vals = zip(*pairs)
    out = {'region':'CAN_prairies', 'papel':'tendencia', 'fuente': a.documentacion,
           'producto':a.producto, 'anios':years, 'valores':vals,
           'unidad':'°C anomaly vs 1951–1980', 'notas':series.notas,
           'tendencia':analizar(years, vals, '°C')}
    (Path(__file__).parent / 'canada_gistemp.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--imerg-dir', type=Path)
    args = parser.parse_args()
    if args.imerg_dir:
        files = list(args.imerg_dir.glob('*.HDF5'))
        if not files:
            parser.error('No monthly IMERG HDF5 files found')
        lluvia_canada(files, Path(__file__).parent / 'canada_imerg.json')
    else:
        main()
