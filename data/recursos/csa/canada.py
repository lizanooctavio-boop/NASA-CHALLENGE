"""Regional GISTEMP with existing read/aggregate adapters; no Nicaragua crop.

Run from repo root: python data/recursos/csa/canada.py
IMERG requires Canadian HDF5 subsets: existing Imerg.leer hardcodes Nicaragua.
Never reuse Nicaragua rainfall for Canada. See csa.md for the blocking issue.
"""
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'backend'))
from clima_nic.fuentes.gistemp import Gistemp
from clima_nic.fuentes.base import recortar_malla
from clima_nic.regiones import cargar
from clima_nic.estadistica.tendencia_robusta import analizar


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
    main()
