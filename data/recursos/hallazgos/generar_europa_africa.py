"""Descarga balances GlaMBIE; conserva los originales fuera del repositorio."""
import argparse
import csv
import io
import urllib.request
import zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
URL = 'https://wgms.ch/downloads/GlaMBIE_Data_DOI_10.5904_wgms-glambie-2024-07.zip'


def generar(cache):
    cache = Path(cache).resolve()
    raiz = AQUI.parents[2]
    if cache == raiz or raiz in cache.parents:
        raise ValueError('La cache debe estar fuera del repositorio')
    cache.mkdir(parents=True, exist_ok=True)
    archivo = cache / 'glambie.zip'
    if not archivo.is_file():
        temporal = cache / 'glambie.part'
        urllib.request.urlretrieve(URL, temporal)
        temporal.replace(archivo)
    with zipfile.ZipFile(archivo) as z:
        filas = list(csv.DictReader(io.StringIO(z.read(
            'glambie_results_20240716/calendar_years/11_central_europe.csv').decode())))
    with (AQUI / 'glambie_europa_anual.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['region', 'anio', 'balance_mwe', 'error_mwe'])
        for r in filas:
            w.writerow(['central_europe', int(float(r['start_dates'])),
                        r['combined_mwe'], r['combined_mwe_errors']])


def lagos(cache):
    """Medias mensuales de altimetría; sin rellenos ni observaciones de hielo."""
    import tarfile
    import datetime
    from collections import defaultdict
    url = 'https://earth.gsfc.nasa.gov/gwm/zip/lake.10.tar.gz'
    archivo = cache / 'lake.10.tar.gz'
    if not archivo.is_file():
        temporal = cache / 'lake.part'
        urllib.request.urlretrieve(url, temporal)
        temporal.replace(archivo)
    filas = []
    with tarfile.open(archivo) as t:
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
            filas.extend([zona, mes, sum(v)/len(v), len(v)] for mes,v in sorted(meses.items()))
    with (AQUI / 'grealm_europa_africa_mensual.csv').open('w', newline='', encoding='utf-8') as f:
        w=csv.writer(f, lineterminator='\n')
        w.writerow(['zona','mes','nivel_m','observaciones'])
        w.writerows(filas)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache', required=True, type=Path)
    args = p.parse_args()
    generar(args.cache)
    lagos(args.cache.resolve())
