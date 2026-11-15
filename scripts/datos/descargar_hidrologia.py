"""Descarga vectores originales, sin digitalizar PDF, y prepara mapas web pequeños.

pip install requests shapely pyshp
python scripts/datos/descargar_hidrologia.py --cache /ruta/fuera/del/repositorio
Los ZIP/SHP originales se conservan en caché. Nunca se añaden al repositorio.
"""
import argparse
import concurrent.futures
import csv
import hashlib
import gzip
import io
import json
import math
from pathlib import Path
import sys
import time
from datetime import datetime, timezone
from xml.etree import ElementTree as ET
import zipfile
from collections import Counter

import requests
from shapely.geometry import shape, mapping

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'backend'))
from clima_nic.hidrologia import WFS, OBSERVACIONES, obtener_observaciones

ARCGIS = 'https://services3.arcgis.com/gcPaotyuZyboHMjH/arcgis/rest/services/'
ITEM = 'a367394491e5470c89ab165525c4c246'
REGIONES = {'af': 'Africa', 'ar': 'North American Arctic', 'as': 'Asia',
            'au': 'Australia and Oceania', 'eu': 'Europe and Middle East',
            'gr': 'Greenland', 'na': 'North and Central America and Caribbean',
            'sa': 'South America', 'si': 'Siberia'}


def codigo(valor):
    """Conserva cadenas y solo transforma números enteros sin notación científica."""
    if valor is None or str(valor).strip() == '':
        return None
    if isinstance(valor, str):
        s = valor.strip()
        if not s.isdigit():
            raise ValueError(f'Código no entero: {valor}')
        return s
    if not math.isfinite(valor) or valor != int(valor):
        raise ValueError(f'Código no entero: {valor}')
    return str(int(valor))


def normalizar_nicaragua(p):
    """No corrige diferencias entre code_pfafs y la concatenación de n3…n7."""
    p = dict(p)
    partes = [codigo(p.get('n' + str(n))) for n in range(3, 8)]
    concatenado = ''.join(x or '' for x in partes)
    c = codigo(p.get('code_pfafs'))
    p.update(codigo_completo=c, codigo_componentes=concatenado,
             codigo_discrepa=c != concatenado, sistema='INETER/SINAPRED Pfafstetter 2021')
    return p


def json_escribir(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    temporal = p.with_suffix(p.suffix + '.part')
    b = json.dumps(d, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
    temporal.write_bytes(gzip.compress(b, compresslevel=9, mtime=0) if p.suffix == '.gz' else b)
    temporal.replace(p)


class Descargas:
    def __init__(self, carpeta):
        self.carpeta = carpeta
        carpeta.mkdir(parents=True, exist_ok=True)

    def archivo(self, url, nombre=None):
        p = self.carpeta / (nombre or (hashlib.sha256(url.encode()).hexdigest() + '.json'))
        recibo = p.with_suffix(p.suffix + '.source.json')
        if not p.exists():
            for intento in range(3):
                try:
                    with requests.get(url, timeout=(15, 90), stream=True) as r:
                        r.raise_for_status()
                        with p.with_suffix(p.suffix + '.part').open('wb') as f:
                            for bloque in r.iter_content(1024 * 1024):
                                f.write(bloque)
                    p.with_suffix(p.suffix + '.part').replace(p)
                    json_escribir(recibo, {'url': url, 'descargado_utc': datetime.now(timezone.utc).isoformat(),
                                          'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size})
                    break
                except (requests.RequestException, OSError):
                    if intento == 2:
                        raise
                    time.sleep(2)
        if not recibo.exists() or json.loads(recibo.read_text())['url'] != url:
            raise ValueError(f'Caché sin procedencia válida: {p}')
        esperado = json.loads(recibo.read_text())
        with p.open('rb') as f:
            digest = hashlib.sha256()
            for bloque in iter(lambda: f.read(1024 * 1024), b''):
                digest.update(bloque)
        if p.stat().st_size != esperado['bytes'] or digest.hexdigest() != esperado['sha256']:
            raise ValueError(f'Caché alterada: {p}; usar una caché nueva para otra edición')
        return p

    def json(self, url):
        d = json.loads(self.archivo(url).read_text())
        if 'error' in d:
            raise ValueError(str(d['error']))
        return d


def query_url(url, **params):
    return requests.Request('GET', url, params=params).prepare().url


def descargar_arcgis(d, servicio):
    url = ARCGIS + requests.utils.quote(servicio, safe='') + '/FeatureServer/0'
    meta = d.json(url + '?f=json')
    ids = d.json(query_url(url + '/query', where='1=1', returnIdsOnly='true', f='json'))['objectIds']
    ids = sorted(ids)
    fs = []
    # Consultas por objectId: nunca se acepta silenciosamente el límite de transferencia.
    for inicio in range(0, len(ids), 100):
        grupo = ids[inicio:inicio + 100]
        r = d.json(query_url(url + '/query', objectIds=','.join(map(str, grupo)), outFields='*',
                             outSR=4326, returnGeometry='true', f='geojson'))
        if len(r.get('features', [])) != len(grupo) or r.get('exceededTransferLimit'):
            raise ValueError('Respuesta ArcGIS incompleta')
        fs.extend(r['features'])
    if len({f['properties'][meta['objectIdField']] for f in fs}) != len(ids):
        raise ValueError('IDs duplicados o ausentes')
    return {'type': 'FeatureCollection', 'features': fs}, meta


def simplificar(g, tolerancia):
    s = shape(g)
    # preserve_topology también conserva defectos de origen: no se usa make_valid,
    # buffer(0), ni se descartan polígonos pequeños. No sirve para medir áreas.
    reducido = mapping(s.simplify(tolerancia, preserve_topology=True))
    def redondear(x):
        return [redondear(y) for y in x] if isinstance(x, (tuple, list)) else round(x, 5)
    reducido['coordinates'] = redondear(reducido['coordinates'])
    return reducido


def nacional(d, salida):
    fc, meta = descargar_arcgis(d, 'Cuencas_PFAFSTETTER_NIC')
    for f in fc['features']:
        f['properties'] = normalizar_nicaragua(f['properties'])
        f['geometry'] = simplificar(f['geometry'], .0002)
    fc['metadata'] = {'source': meta['description'], 'url': ARCGIS + 'Cuencas_PFAFSTETTER_NIC/FeatureServer/0',
                      'edition': '2021-11', 'simplification_degrees': .0002,
                      'warning': 'Published 2021 layer, not a verified copy of the 2014 atlas. Despite its level-7 title, it includes 3-, 6- and 7-digit codes. Source code discrepancies are retained.'}
    json_escribir(salida / 'nicaragua_pfafstetter.geojson.gz', fc)
    with (salida / 'nicaragua_codigos.csv').open('w', encoding='utf-8', newline='') as f:
        campos = ['FID', 'codigo_completo', 'n3', 'n4', 'n5', 'n6', 'n7', 'codigo_componentes', 'codigo_discrepa', 'cuencas', 'phca', 'area']
        w = csv.DictWriter(f, fieldnames=campos, extrasaction='ignore'); w.writeheader()
        w.writerows(g['properties'] for g in fc['features'])
    return {'features': len(fc['features']), 'code_discrepancies': sum(f['properties']['codigo_discrepa'] for f in fc['features']),
            'unique_codes': len({f['properties']['codigo_completo'] for f in fc['features']}),
            'code_lengths': dict(Counter(len(f['properties']['codigo_completo']) for f in fc['features'])), 'metadata': meta}


def global_region(d, salida, region, nivel):
    import shapefile  # Dependencia de extracción; no es necesaria para servir los mapas.
    nombre = f'hybas_{region}_lev{nivel:02d}_v1c.zip'
    url = 'https://data.hydrosheds.org/file/hydrobasins/standard/' + nombre
    p = d.archivo(url, nombre)
    with zipfile.ZipFile(p) as z:
        prefijo = next(n[:-4] for n in z.namelist() if n.endswith('.shp'))
        # Se lee desde el ZIP, sin extractall y sin rutas proporcionadas por el archivo.
        lector = shapefile.Reader(shp=io.BytesIO(z.read(prefijo + '.shp')),
                                  shx=io.BytesIO(z.read(prefijo + '.shx')),
                                  dbf=io.BytesIO(z.read(prefijo + '.dbf')))
        if nivel == 12:
            return dict(region=region, level=nivel, features=len(lector), original_url=url,
                        original_only=True, license='HydroSHEDS License Agreement')
        fs = []
        for r in lector.iterShapeRecords():
            a = r.record.as_dict()
            for k in ['HYBAS_ID', 'NEXT_DOWN', 'NEXT_SINK', 'MAIN_BAS', 'PFAF_ID']:
                a[k] = codigo(a[k])
            a.update(codigo_completo=a['PFAF_ID'], sistema='HydroBASINS v1c', region=region, nivel=nivel)
            fs.append(dict(type='Feature', id=a['HYBAS_ID'], properties=a,
                           geometry=simplificar(r.shape.__geo_interface__, .01 if nivel == 4 else .003)))
        nombre_geo = f'hydrobasins_{region}_l{nivel}.geojson.gz'
        json_escribir(salida / nombre_geo, dict(type='FeatureCollection', features=fs,
                       metadata=dict(original_url=url, edition='v1c', level=nivel,
                                     simplification_degrees=.01 if nivel == 4 else .003,
                                     citation='doi:10.1002/hyp.9740')))
    return dict(region=region, level=nivel, features=len(fs), file=nombre_geo, original_url=url,
                license='HydroSHEDS License Agreement')


def inventario_ineter(d, salida):
    cap = d.archivo(WFS + '?service=WFS&request=GetCapabilities', 'ineter_wfs_capabilities.xml')
    raiz = ET.fromstring(cap.read_bytes())
    ns = {'w': 'http://www.opengis.net/wfs/2.0'}
    capas = []
    # Inventario amplio: se conserva el QName oficial para WFS/WMS y su título original.
    for ft in raiz.findall('.//w:FeatureType', ns):
        nombre = ft.findtext('w:Name', namespaces=ns)
        titulo = ft.findtext('w:Title', namespaces=ns)
        if nombre.startswith(('wsINETER-DGMT:', 'wsINETER-DGRH:', 'wsINETER-RH:', 'wsINETER-DGGG:')):
            capas.append({'id': nombre, 'title_source': titulo,
                          'wfs_url': query_url(WFS, service='WFS', version='2.0.0', request='GetFeature',
                                               typeNames=nombre, outputFormat='application/json', srsName='CRS:84'),
                          'type': 'Service layer; observation period must be checked before trend analysis'})
    json_escribir(salida / 'ineter_catalogo.json', {'capabilities_url': WFS + '?service=WFS&request=GetCapabilities',
                    'layers': capas, 'warning': 'Catalogue availability does not establish freshness, completeness or a climate trend.'})
    visor = d.json('https://www.arcgis.com/sharing/rest/content/items/99d7faca90ef4bde9c053e67dabc3006/data?f=json')
    sinapred = []
    for l in visor['operationalLayers']:
        titulo = l.get('title', '')
        if l.get('layerType') == 'ArcGISFeatureLayer' and any(t in titulo.lower() for t in
                ['corredor seco', 'inundaci', 'amenaza sísmica', 'fallas sísmicas', 'amenaza volcánica', 'tsunami',
                 'ríos y lagunas', 'ruta de huracanes']):
            item = d.json('https://www.arcgis.com/sharing/rest/content/items/' + l['itemId'] + '?f=json')
            url = requests.utils.requote_uri(l['url'])
            meta = d.json(url + '?f=json')
            sinapred.append(dict(id=l['itemId'], title_source=titulo, url=url,
                                 description=item.get('description'), license=item.get('licenseInfo'),
                                 copyright=meta.get('copyrightText'), fields=meta.get('fields'),
                                 editing_info=meta.get('editingInfo'),
                                 warning='Reference geometry; layer publication or edit time does not establish observation time.'))
    json_escribir(salida / 'sinapred_catalogo.json', {'web_map': '99d7faca90ef4bde9c053e67dabc3006', 'layers': sinapred})
    for id_ in OBSERVACIONES:
        try:
            json_escribir(salida / ('ineter_' + id_ + '.geojson'), obtener_observaciones(id_))
        except (requests.RequestException, ValueError) as e:
            print(f'Observaciones {id_} no disponibles: {e}', flush=True)
    return len(capas)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache', required=True, type=Path)
    p.add_argument('--sin-originales-nivel12', action='store_true', help='Omite los ZIP completos de máximo detalle mundial')
    p.add_argument('--solo', choices=['nacional', 'mundial', 'ineter'])
    args = p.parse_args()
    cache = args.cache.resolve()
    if cache == RAIZ or RAIZ in cache.parents:
        p.error('--cache debe estar fuera del repositorio')
    d = Descargas(cache); salida = RAIZ / 'data/hidrologia'; salida.mkdir(parents=True, exist_ok=True)
    manifiesto_p = salida / 'procedencia.json'
    m = json.loads(manifiesto_p.read_text()) if manifiesto_p.exists() else {}
    if args.solo in (None, 'nacional'):
        m['nicaragua'] = nacional(d, salida); print('Nicaragua:', m['nicaragua']['features'], flush=True)
    if args.solo in (None, 'mundial'):
        niveles = [4, 6] + ([] if args.sin_originales_nivel12 else [12])
        tareas = [(r, n) for r in REGIONES for n in niveles]
        def ejecutar(t):
            x = global_region(d, salida, *t); print(t, x['features'], flush=True); return x
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            m['global'] = sorted(ex.map(ejecutar, tareas), key=lambda x: (x['region'], x['level']))
    if args.solo in (None, 'ineter'):
        m['ineter_catalogue_layers'] = inventario_ineter(d, salida)
    m.update(schema='nasa-challenge/hydrology-v1', generated_utc=datetime.now(timezone.utc).isoformat(),
             regions=REGIONES, accounts_required=False,
             hydrobasins_coverage='Nine regions, excluding Antarctica; codes are independent from Nicaragua national coding.',
             geometry_note='Display vectors simplified independently; use originals for area/topology analysis.',
             licenses={'nicaragua': 'Public query access; no redistribution license stated in ArcGIS metadata. Rights remain with the source institutions; not covered by the code Apache license.',
                       'hydrobasins': 'HydroSHEDS License Agreement; attribution required. https://www.hydrosheds.org/products/hydrobasins'})
    m['downloads'] = [json.loads(f.read_text()) for f in sorted(cache.glob('*.source.json'))]
    m['station_snapshots'] = []
    for id_ in OBSERVACIONES:
        fp = salida / ('ineter_' + id_ + '.geojson')
        if fp.exists():
            b = fp.read_bytes(); x = json.loads(b)
            m['station_snapshots'].append(dict(file=fp.name, bytes=len(b), sha256=hashlib.sha256(b).hexdigest(),
                                               source_url=x['metadata']['source_url'], retrieved_utc=x['metadata']['retrieved_utc']))
    json_escribir(manifiesto_p, m)


if __name__ == '__main__':
    main()
