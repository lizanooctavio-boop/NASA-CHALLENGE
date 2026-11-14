"""Acquire monthly IMERG originals outside Git, then run the Canadian reader.

Usage: python data/recursos/csa/descargar_canada.py --destino ../imerg_canada
Earthdata credentials and GES DISC authorization must already be configured.
No credentials or signed URLs are written to the provenance manifest.
"""
import argparse
import concurrent.futures
import json
import threading
from pathlib import Path
import requests
import earthaccess
from canada import lluvia_canada


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--destino', type=Path, required=True)
    args = parser.parse_args()
    args.destino.mkdir(parents=True, exist_ok=True)
    auth = earthaccess.login(strategy='netrc')
    if not auth.authenticated:
        raise RuntimeError('Earthdata authentication failed')
    entries = []
    for page in (1, 2):
        r = requests.get('https://cmr.earthdata.nasa.gov/search/granules.json', params={
            'short_name':'GPM_3IMERGM', 'version':'07', 'page_size':200, 'page_num':page,
            'sort_key':'start_date',
            'temporal':'2001-01-01T00:00:00Z,2024-12-31T23:59:59Z'}, timeout=60)
        r.raise_for_status()
        entries.extend(r.json()['feed']['entry'])
    jobs = [next(l['href'] for l in e['links'] if l['href'].startswith('https://')
                 and l['href'].endswith('.HDF5')) for e in entries]
    if len(jobs) != 288:
        raise ValueError(f'Expected 288 monthly granules, found {len(jobs)}')
    local = threading.local()

    def download(url):
        path = args.destino / url.rsplit('/', 1)[-1]
        if path.exists() and path.stat().st_size > 100000:
            return path
        if not hasattr(local, 'session'):
            local.session = earthaccess.get_requests_https_session()
        r = local.session.get(url, timeout=180)
        r.raise_for_status()
        if r.content[:8] != b'\x89HDF\r\n\x1a\n':
            raise ValueError('Expected HDF5 granule')
        tmp = path.with_suffix('.partial')
        tmp.write_bytes(r.content)
        tmp.replace(path)
        return path

    paths = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for path in pool.map(download, jobs):
            paths.append(path)
            if len(paths) % 12 == 0:
                print(f'IMERG {len(paths)}/288', flush=True)
    out = Path(__file__).parent
    (out/'imerg_consulta.json').write_text(json.dumps({
        'cmr':'https://cmr.earthdata.nasa.gov/search/granules.json',
        'short_name':'GPM_3IMERGM', 'version':'07', 'urls':jobs,
        'periodo':[2001,2024]}, indent=2), encoding='utf-8')
    result = lluvia_canada(paths, out/'canada_imerg.json')
    print('Annual years:', result['anios'], flush=True)


if __name__ == '__main__':
    main()
