"""Códigos de origen, integridad continental, fechas y pasarela WFS sin red en tests."""
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
import requests

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / 'backend'))
from clima_nic import hidrologia as h
from clima_nic.api import app
from fastapi.testclient import TestClient

spec = importlib.util.spec_from_file_location('descarga_hidro', RAIZ / 'scripts/datos/descargar_hidrologia.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def leer(nombre):
    p = RAIZ / 'data/hidrologia' / nombre
    return json.loads(gzip.decompress(p.read_bytes()) if p.suffix == '.gz' else p.read_text())


def test_nicaragua_no_inventa_la_edicion_2014_ni_corrige_codigos():
    d = leer('nicaragua_pfafstetter.geojson.gz')
    assert d['metadata']['edition'] == '2021-11'
    fs = d['features']
    assert len(fs) == 2337
    assert len({f['properties']['FID'] for f in fs}) == len(fs)
    assert sum(f['properties']['codigo_discrepa'] for f in fs) == 44
    for f in fs:
        p = f['properties']
        assert p['codigo_completo'] == str(int(p['code_pfafs']))
        assert len(p['codigo_completo']) in (3, 6, 7)
        assert p['codigo_discrepa'] == (p['codigo_componentes'] != p['codigo_completo'])
    segundo = next(f['properties'] for f in fs if f['properties']['FID'] == 2)
    assert segundo['codigo_completo'] == '9519581'
    assert segundo['codigo_componentes'] == '9519587'
    with (RAIZ / 'data/hidrologia/nicaragua_codigos.csv').open(encoding='utf-8') as f:
        filas = list(csv.DictReader(f))
    assert [r['codigo_completo'] for r in filas] == [f['properties']['codigo_completo'] for f in fs]


@pytest.mark.parametrize('region', list(g.REGIONES))
def test_cobertura_mundial_y_codigos_sin_recortar(region):
    m = leer('procedencia.json')
    assert any(x['region'] == region and x['level'] == 12 and x['features'] > 0 for x in m['global'])
    for nivel in (4, 6):
        d = leer(f'hydrobasins_{region}_l{nivel}.geojson.gz')
        publicado = next(x for x in m['global'] if x['region'] == region and x['level'] == nivel)
        assert len(d['features']) == publicado['features']
        for f in d['features']:
            p = f['properties']
            assert isinstance(p['PFAF_ID'], str)
            assert p['codigo_completo'] == p['PFAF_ID']
            assert len(p['PFAF_ID']) == nivel
            assert len(p['HYBAS_ID']) == 10 and p['HYBAS_ID'].isdigit()
            assert int(p['HYBAS_ID'][1:3]) == nivel
            assert p['sistema'] == 'HydroBASINS v1c'
            assert f['geometry']['type'] in ('Polygon', 'MultiPolygon')
    assert len({f['properties']['HYBAS_ID'] for f in d['features']}) == len(d['features'])


def test_catalogos_y_lecturas_tienen_procedencia_y_no_fabrican_fechas():
    m = leer('procedencia.json')
    assert sum(x['features'] for x in m['global'] if x['level'] == 12) == 1034083
    assert all(x['url'].startswith('https://') and len(x['sha256']) == 64 for x in m['downloads'])
    assert len(m['station_snapshots']) == 4
    for recibo in m['station_snapshots']:
        b = (RAIZ / 'data/hidrologia' / recibo['file']).read_bytes()
        assert hashlib.sha256(b).hexdigest() == recibo['sha256']
        assert len(b) == recibo['bytes']
    c = leer('ineter_catalogo.json')
    assert len(c['layers']) >= 400
    assert 'wsINETER-DGRH:Cuencas_nivel7_2021' in {x['id'] for x in c['layers']}
    assert len(leer('sinapred_catalogo.json')['layers']) >= 7
    for id_ in h.OBSERVACIONES:
        d = leer(f'ineter_{id_}.geojson')
        assert d['metadata']['source'] == 'INETER WFS'
        assert d['metadata']['accounts_required'] is False
        assert len(d['features']) == d['numberMatched']
        for f in d['features']:
            g_ = f['geometry']
            assert g_['type'] in ('Point', 'MultiPoint')
            puntos = [g_['coordinates']] if g_['type'] == 'Point' else g_['coordinates']
            for coordenada in puntos:
                x, y = coordenada[:2]  # La fuente también publica coordenadas con Z.
                assert -89 < x < -82 and 10 < y < 16


class Respuesta:
    url = 'https://mapserveride.ineter.gob.ni/geoserver/ows?service=WFS'
    def __init__(self, datos):
        self.datos = datos
    def raise_for_status(self):
        pass
    def json(self):
        return self.datos


@pytest.fixture(autouse=True)
def vaciar_cache():
    h._CACHE.clear()


def test_api_allowlist_cache_y_fechas_originales(monkeypatch):
    d = {'type': 'FeatureCollection', 'numberMatched': 1, 'features': [
        {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [-85, 13]},
         'properties': {'nivelrio': None, 'fechaultimatransmision': '2021-05-08T17:00:00Z'}}]}
    llamadas = []
    def get(url, **kw):
        llamadas.append((url, kw)); return Respuesta(d)
    monkeypatch.setattr(h.requests, 'get', get)
    c = TestClient(app)
    assert c.get('/hidrologia/observaciones/desconocida').status_code == 404
    r = c.get('/hidrologia/observaciones/nivel_rio')
    assert r.status_code == 200
    assert r.json()['features'][0]['properties'] == d['features'][0]['properties']
    assert c.get('/hidrologia/observaciones/nivel_rio').status_code == 200
    assert len(llamadas) == 1
    assert llamadas[0][0] == h.WFS
    assert llamadas[0][1]['params']['srsName'] == 'CRS:84'
    assert 'retrieved_utc' in r.json()['metadata']


def test_no_se_acepta_descarga_incompleta(monkeypatch):
    monkeypatch.setattr(h.requests, 'get', lambda *a, **k: Respuesta({'type': 'FeatureCollection', 'numberMatched': 2, 'features': []}))
    assert TestClient(app).get('/hidrologia/observaciones/lluvia_24h').status_code == 502


def test_error_proveedor_no_se_convierte_en_valores_cero(monkeypatch):
    def fallar(*a, **kw):
        raise requests.Timeout()
    monkeypatch.setattr(h.requests, 'get', fallar)
    assert TestClient(app).get('/hidrologia/observaciones/nivel_rio').status_code == 502
    assert h._CACHE == {}


def test_paginacion_arcgis_no_pierde_poligonos():
    class D:
        def json(self, url):
            from urllib.parse import urlparse, parse_qs
            q = parse_qs(urlparse(url).query)
            if not urlparse(url).path.endswith('query'):
                return {'objectIdField': 'FID'}
            if q.get('returnIdsOnly') == ['true']:
                return {'objectIds': list(range(1, 206))}
            ids = q['objectIds'][0].split(',')
            return {'type': 'FeatureCollection', 'features': [{'properties': {'FID': int(i)}} for i in ids]}
    fc, _ = g.descargar_arcgis(D(), 'synthetic_test_only')
    assert len(fc['features']) == 205
    class Incompleto(D):
        def json(self, url):
            d = super().json(url)
            if 'features' in d:
                d['features'] = []
            return d
    with pytest.raises(ValueError, match='incompleta'):
        g.descargar_arcgis(Incompleto(), 'synthetic_test_only')


def test_cache_corrupta_no_se_reutiliza(tmp_path):
    p = tmp_path / 'original.json'
    p.write_text('{"version":1}')
    recibo = {'url': 'https://example.invalid/synthetic-test', 'bytes': p.stat().st_size,
              'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
    p.with_suffix('.json.source.json').write_text(json.dumps(recibo))
    p.write_text('{"version":2}')
    with pytest.raises(ValueError, match='alterada'):
        g.Descargas(tmp_path).archivo(recibo['url'], p.name)


def test_utilidades_js_codigos_fechas_y_csv():
    subprocess.run(['node', '-e', r'''
const assert=require('node:assert/strict'),h=require('./src/hidrologia-datos.js');
assert.equal(h.codigo({PFAF_ID:'001234567890'}),'001234567890');
const ahora=Date.parse('2026-11-15T00:00:00Z');
assert.equal(h.antiguedad({fechaultimatransmision:'2021-01-01T00:00:00Z'},ahora),'Older than 48 hours');
assert.equal(h.antiguedad({fechaultimatransmision:'2026-11-14T22:00:00Z'},ahora),'Within the last 48 hours');
assert.equal(h.antiguedad({fechaformato:'14/11/2026'},ahora),'Observation time unknown');
assert.equal(h.antiguedad({fechaultimatransmision:'2027-01-01T00:00:00Z'},ahora),'Future timestamp: check source');
assert.equal(h.buscar([{properties:{codigo_completo:'9519581'}}],'9519581').length,1);
const csv=h.filasCSV([{properties:{codigo_completo:'0012',malicioso:'=1+1',valor:-2,falta:null}}]);
assert.ok(csv.includes('"0012"'));assert.ok(csv.includes('"\'=1+1"'));assert.ok(csv.includes('"-2"'));
'''], cwd=RAIZ, check=True)
