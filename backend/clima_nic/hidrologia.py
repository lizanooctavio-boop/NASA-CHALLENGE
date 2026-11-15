"""Lecturas INETER por WFS; fuentes fijas, fechas originales y caché breve.

Una lectura de estación no es una tendencia ni una alerta oficial. El servidor no
añade unidades ni fechas de observación que el proveedor no haya declarado.
"""
import copy
import threading
import time
from datetime import datetime, timezone

import requests

WFS = 'https://mapserveride.ineter.gob.ni/geoserver/ows'
OBSERVACIONES = {
    'nivel_rio': ('wsINETER-DGRH:Nivel_Rio', 'River level station readings', 'fechaultimatransmision'),
    'lluvia_24h': ('wsINETER-DGMT:Lluvia_24_Horas', '24-hour rainfall station readings', None),
    'temperatura': ('wsINETER-DGMT:temperaturacaelus', 'Air temperature station readings', 'Ultima lectura'),
    'viento': ('wsINETER-DGMT:Vientos_Simet_ot', 'Wind station readings (historical records possible)', 'fechaformato'),
}
_CACHE = {}
_LOCK = threading.Lock()


def obtener_observaciones(id_):
    if id_ not in OBSERVACIONES:
        raise ValueError('Unknown observation layer')
    with _LOCK:
        anterior = _CACHE.get(id_)
        if anterior and time.monotonic() - anterior[0] < 300:
            return copy.deepcopy(anterior[1])
    tipo, titulo, fecha = OBSERVACIONES[id_]
    params = dict(service='WFS', version='2.0.0', request='GetFeature', typeNames=tipo,
                  outputFormat='application/json', srsName='CRS:84', count=5000)
    r = requests.get(WFS, params=params, timeout=(8, 25))
    r.raise_for_status()
    try:
        d = r.json()
    except ValueError as e:
        raise ValueError('INETER returned a non-JSON response') from e
    if not isinstance(d, dict) or d.get('type') != 'FeatureCollection' or not isinstance(d.get('features'), list):
        raise ValueError('Invalid WFS feature collection')
    total = d.get('numberMatched', d.get('totalFeatures'))
    if str(total).isdigit() and int(total) != len(d['features']):
        raise ValueError('Incomplete WFS station response')
    if len(d['features']) >= 5000:
        raise ValueError('Station query limit reached')
    d['metadata'] = dict(source='INETER WFS', title_en=titulo, source_url=r.url,
                         retrieved_utc=datetime.now(timezone.utc).isoformat(),
                         observation_date_field=fecha, accounts_required=False,
                         warning='Check each station date. Retrieval time is not observation time. Units not supplied by WFS are not inferred. No trend or official warning is calculated.')
    with _LOCK:
        _CACHE[id_] = time.monotonic(), copy.deepcopy(d)
    return d
