"""QA, geometrías, unidades, fallos de servicio y reanudación; no necesita NASA ni secretos."""
import calendar
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))
from clima_nic.fuentes.appeears import (  # noqa: E402
    AppEEARS, PRODUCTOS, agregar_registros, cobertura_estable, inventario,
    leer_tif, mascara_calidad, media_area, pesos_area, recortar_tareas,
)
from clima_nic.fuentes.gldas_datarods import GldasDatarods, leer_csv, url_serie  # noqa: E402


def test_plan_area_poligonos_reales_y_smap_primero():
    a = AppEEARS()
    plan = a.plan(2001, 2024)
    geo = json.loads((RAIZ / 'data/regiones_nicaragua.geojson').read_text(encoding='utf-8'))
    ids = {str(f['id']) for f in geo['features']}
    assert {t['region'] for t in plan} == ids
    assert plan[0]['producto'] == 'SPL4SMGP.008'
    for t in plan:
        s = t['solicitud']
        assert s['task_type'] == 'area'
        assert s['params']['geo']['features'][0]['geometry'] == next(f['geometry'] for f in geo['features'] if str(f['id']) == t['region'])
        assert len(s['params']['layers']) == len(PRODUCTOS[t['producto']]['datos']) + len(PRODUCTOS[t['producto']]['qa'])
        assert not (t['producto'] == 'SPL4SMGP.008' and t['desde'] < '2015-03-31')


def test_plan_canada_sin_crear_geometria(tmp_path):
    canada = {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'id': 'CA', 'properties': {},
              'geometry': {'type': 'Polygon', 'coordinates': [[[-80, 50], [-79, 50], [-79, 51], [-80, 50]]]}}]}
    ruta = tmp_path / 'ca.json'
    ruta.write_text(json.dumps(canada))
    tareas = AppEEARS().plan(2001, 2024, ruta, ['MOD11A2.061', 'MOD13A3.061'])
    assert {t['producto'] for t in tareas} == {'MOD11A2.061', 'MOD13A3.061'}
    assert all(t['region'] == 'CA' for t in tareas)
    with pytest.raises(FileNotFoundError):
        AppEEARS().plan(2001, 2024, tmp_path / 'ausente')


def test_envio_reanudable_sin_duplicar_y_sin_secretos(tmp_path, monkeypatch):
    a = AppEEARS(token='secreto-prueba')
    monkeypatch.setattr(a, 'cache', lambda: tmp_path)
    tareas = a.plan(2024, 2024, productos=['MOD13A3.061'])[:1]
    llamadas = []
    def api(ruta, datos=None, **kw):
        llamadas.append(ruta)
        if ruta.startswith('product/'):
            return {c['layer']: {'Available': True} for c in tareas[0]['solicitud']['params']['layers']}
        return {'task_id': 'task-123'}
    monkeypatch.setattr(a, 'api', api)
    primera = list(a.enviar(tareas))
    segunda = list(a.enviar(tareas))
    assert llamadas.count('task') == 1
    assert primera == segunda
    assert 'secreto-prueba' not in primera[0][0].read_text(encoding='utf-8')


def test_recibos_navegador_reutilizan_id_sin_reenviar(tmp_path, monkeypatch):
    a = AppEEARS()
    monkeypatch.setattr(a, 'cache', lambda: tmp_path)
    plan = a.plan(2024, 2024, productos=['MOD13A3.061'])[:1]
    recibo = {'task_name': plan[0]['solicitud']['task_name'],
              'task_id': '5c1e5da0-a4a3-40d2-bda1-eee9dec63163',
              'enviada_utc': '2026-11-13T05:50:34+00:00', 'estado_ui': 'Pending'}
    assert a.registrar_recibos(plan, [recibo]) == 1
    def api(ruta, datos=None, **kw):
        assert ruta.startswith('product/'), 'No se debe enviar otra tarea'
        return {c['layer']: {'Available': True} for c in plan[0]['solicitud']['params']['layers']}
    monkeypatch.setattr(a, 'api', api)
    assert list(a.enviar(plan))[0][1]['task_id'] == recibo['task_id']
    with pytest.raises(ValueError):
        a.registrar_recibos(plan, [recibo, recibo])
    with pytest.raises(ValueError, match='contradice'):
        a.registrar_recibos(plan, [recibo | {'task_id': '8b96ce89-736c-457c-80b2-095ac9f50d27'}])
    with pytest.raises(ValueError):
        a.registrar_recibos(plan, [recibo | {'task_name': 'tarea-ajena'}])


def test_espera_error_timeout_y_vacio(monkeypatch):
    a = AppEEARS()
    monkeypatch.setattr(a, 'api', lambda *args: {'status': 'processing'})
    with pytest.raises(TimeoutError):
        a.esperar('x', max_segundos=0)
    monkeypatch.setattr(a, 'api', lambda *args: {'status': 'error'})
    with pytest.raises(RuntimeError):
        a.esperar('x')
    monkeypatch.setattr(a, 'api', lambda *args: {'status': 'done', 'summary': {'empty': True}})
    with pytest.raises(RuntimeError):
        a.esperar('x')


@pytest.mark.parametrize('producto,capas,esperado', [
    ('MOD13A3.061', {'_1_km_monthly_VI_Quality': np.array([2048, 2049, 2048 | (1 << 8), 2048 | (1 << 15), 2048 | (3 << 6), 2048, 0]),
                     '_1_km_monthly_pixel_reliability': np.array([0, 0, 0, 0, 0, 1, 0])}, [True, False, False, False, False, False, False]),
    ('MOD11A2.061', {'QC_Day': np.array([0, 1, 1 << 6, 1 << 4, 1 << 2])}, [True, False, False, True, False]),
    ('MOD16A2GF.061', {'ET_QC_500m': np.array([0, 1, 4, 8, 32, 255])}, [True, False, False, False, False, False]),
    ('MCD12Q1.061', {'QC': np.array([0, 1, 0, 0]), 'LC_Type1': np.array([1, 1, 17, 255])}, [True, False, False, False]),
    ('SPL4SMGP.008', {'Geophysical_Data_soil_temp_layer1': np.array([280, 270, 280, 280, -9999]),
                     'Geophysical_Data_land_fraction_snow_covered': np.array([5.5e-8, 0, .1, -9999, 0])}, [True, False, False, False, False]),
])
def test_mascaras_calidad(producto, capas, esperado):
    assert mascara_calidad(producto, capas).tolist() == esperado


def test_calidad_ausente_no_se_acepta():
    with pytest.raises(KeyError):
        mascara_calidad('MOD13A3.061', {})


def test_cohorte_fija_excluye_cambio_y_falta_calidad():
    c = np.array([[[1, 2, 3]], [[1, 3, 3]]])
    q = np.array([[[0, 0, 1]], [[0, 0, 0]]])
    assert cobertura_estable(c, q, [2001, 2002], range(2001, 2003)).tolist() == [[True, False, False]]
    with pytest.raises(ValueError):
        cobertura_estable(c[:1], q[:1], [2001], range(2001, 2003))


def test_area_interseccion_y_faltantes():
    from rasterio.transform import from_origin
    m = dict(shape=(1, 2), transform=from_origin(0, 1, 1, 1), crs='EPSG:4326')
    g = {'type': 'Polygon', 'coordinates': [[[0, 0], [1.5, 0], [1.5, 1], [0, 1], [0, 0]]]}
    w = pesos_area(m, g)
    assert w[0, 0] / w[0, 1] == pytest.approx(2)
    v, f = media_area(np.array([[1, 4]]), w)
    assert v == pytest.approx(2)
    assert f == pytest.approx(1)
    v, f = media_area(np.array([[np.nan, 4]]), w)
    assert v is None
    assert f == pytest.approx(1 / 3)


def tif(ruta, a, qa=False):
    import rasterio
    from rasterio.transform import from_origin
    a = np.asarray(a, dtype='uint16' if qa else 'float32')
    with rasterio.open(ruta, 'w', driver='GTiff', width=a.shape[1], height=a.shape[0], count=1,
                       dtype=a.dtype, crs='EPSG:4326', transform=from_origin(0, 1, 1, 1), nodata=0) as f:
        f.write(a, 1)
    return str(ruta)


def test_qc_cero_valido_aunque_nodata_cero(tmp_path):
    p = tmp_path / 'qa.tif'
    tif(p, [[0, 1]], qa=True)
    assert leer_tif(p, qa=True)[0].tolist() == [[0, 1]]


def test_geotiff_empaquetado_aplica_escala_una_vez(tmp_path):
    import rasterio
    ruta = tmp_path / 'lst.tif'
    tif(ruta, [[15000, 0]], qa=True)
    with rasterio.open(ruta, 'r+') as f:
        f.scales = (.02,)
        f.offsets = (0,)
        f.update_tags(scale_factor=.02, add_offset=0)
    a, _ = leer_tif(ruta)
    assert a[0, 0] == pytest.approx(300)
    assert np.isnan(a[0, 1])


def test_raster_entero_sin_metadatos_se_rechaza(tmp_path):
    ruta = tmp_path / 'lst_sin_escala.tif'
    tif(ruta, [[15000]], qa=True)
    with pytest.raises(ValueError, match='sin escala'):
        leer_tif(ruta)


def test_recorte_geotiff_fisico_sin_doble_escala(tmp_path):
    p = 'MOD11A2.061'
    rutas = [tif(tmp_path / f'{p}_{c}_doy2024001_aid0001.tif', v, qa=(c == 'QC_Day'))
             for c, v in [('LST_Day_1km', [[300, 310]]), ('QC_Day', [[0, 1]])]]
    t = {'region': 'R', 'producto': p, 'archivos': rutas,
         'geometria': {'type': 'Polygon', 'coordinates': [[[0, 0], [2, 0], [2, 1], [0, 1], [0, 0]]]}}
    r = recortar_tareas([t])
    assert r[0]['valor'] == pytest.approx(26.85)
    assert r[0]['fraccion_area'] == pytest.approx(.5)


def test_fechas_smap_preservan_hora_y_no_se_colapsan(tmp_path):
    p = 'SPL4SMGP.008'
    t = {'region': 'R', 'producto': p, 'geometria': {}, 'archivos': [
        str(tmp_path / f'{p}_Geophysical_Data_sm_surface_doy2024001{h}_aid0001.tif')
        for h in ['013000', '043000']]}
    assert len(inventario([t])) == 2


def test_recorte_ndvi_estable_no_incluye_cambio_de_clase(tmp_path):
    pol = {'type': 'Polygon', 'coordinates': [[[0, 0], [2, 0], [2, 1], [0, 1], [0, 0]]]}
    tareas = []
    for anio, clase in [(2023, [[1, 2]]), (2024, [[1, 3]])]:
        p = 'MCD12Q1.061'
        rutas = [tif(tmp_path / f'{p}_{c}_doy{anio}001_aid0001.tif', a, qa=True)
                 for c, a in [('LC_Type1', clase), ('QC', [[0, 0]])]]
        tareas.append(dict(region='R', producto=p, archivos=rutas, geometria=pol))
    p = 'MOD13A3.061'
    rutas = [tif(tmp_path / f'{p}_{c}_doy2023001_aid0001.tif', a, qa=(c != '_1_km_monthly_NDVI'))
             for c, a in [('_1_km_monthly_NDVI', [[.4, .8]]), ('_1_km_monthly_VI_Quality', [[2048, 2048]]),
                          ('_1_km_monthly_pixel_reliability', [[0, 0]])]]
    tareas.append(dict(region='R', producto=p, archivos=rutas, geometria=pol, desde='2023-01-01', hasta='2024-12-31'))
    filas = recortar_tareas(tareas)
    assert filas[0]['valor'] == pytest.approx(.6)
    assert filas[1]['variable'] == 'ndvi_cobertura_estable'
    assert filas[1]['valor'] == pytest.approx(.4)
    assert filas[1]['fraccion_area_cohorte'] == pytest.approx(.5)
    with pytest.raises(ValueError, match='Faltan años'):
        recortar_tareas(tareas[1:])
    assert len(recortar_tareas(tareas[-1:], exigir_estable=False)) == 1


def test_smap_centro_intervalo_no_pasa_al_mes_siguiente():
    filas = [dict(region='R', variable='humedad_smap_superficial', unidad='m³/m³', producto='SPL4SMGP.008',
                  fecha=(datetime(2024, 1, 1, 1, 30) + timedelta(hours=3*i)).isoformat(),
                  valor=.25, dias=.125) for i in range(31*8)]
    s = agregar_registros(filas)[0]
    assert s.tiempos == ['2024-01']
    assert s.valores == pytest.approx([.25])


def registro(fecha, v, variable='et_modis', dias=8):
    return dict(region='R', variable=variable, unidad='mm', producto='MOD16A2GF.061',
                fecha=fecha, valor=v, dias=dias)


def test_et_compuesto_cruza_mes_y_fin_anio():
    # 8 mm / 8 días: enero recibe 4 mm y febrero 4 mm; meses incompletos → null.
    r = agregar_registros([registro('2024-01-28', 8)])
    assert r[0].tiempos == ['2024-01', '2024-02']
    assert r[0].valores == [None, None]
    filas = [registro((datetime(2023, 1, 1) + timedelta(days=i)).isoformat(), min(8, 365-i))
             for i in range(0, 365, 8)]
    anual = agregar_registros(filas, 'anual')[0]
    assert anual.valores == pytest.approx([365])


def test_medias_ponderadas_por_duracion_y_solapes():
    filas = [registro('2024-01-01', 10, 'lst_dia'), registro('2024-01-09', 20, 'lst_dia'),
             registro('2024-01-17', 20, 'lst_dia'), registro('2024-01-25', 20, 'lst_dia')]
    assert agregar_registros(filas)[0].valores[0] == pytest.approx((8 * 10 + 23 * 20) / 31)
    with pytest.raises(ValueError):
        agregar_registros(filas + filas)


def test_csv_html_login_y_error_no_son_datos():
    for t in ['<!DOCTYPE html><html>login</html>', '{"error":"401"}', 'invalid']:
        with pytest.raises(ValueError):
            leer_csv(t)


def test_csv_undef_orden_y_duplicados():
    texto = 'lat,12.375\nlon,-86.875\nundef,-9999\n\nTimestamp,Data\n2024-01-01T03:00:00Z,-9999\n2024-01-01T00:00:00Z,25\n'
    m, t, v = leer_csv(texto)
    assert m['lat'] == '12.375' and v[0] == 25 and np.isnan(v[1])
    with pytest.raises(ValueError):
        leer_csv(texto + '2024-01-01T00:00:00Z,25\n')


def test_giovanni_coordenadas_lat_lon_y_version():
    from urllib.parse import parse_qs, urlsplit
    q = parse_qs(urlsplit(url_serie('SoilMoi0_10cm_inst', 12.45, -86.85, '2024-01-01', '2024-02-01')).query)
    assert q['location'] == ['[12.45,-86.85]']
    assert q['data'] == ['GLDAS_NOAH025_3H_2_1_SoilMoi0_10cm_inst']


@pytest.mark.parametrize('variable,valor,esperado', [
    ('SoilMoi0_10cm_inst', 25, .25), ('SoilMoi10_40cm_inst', 75, .25),
    ('Evap_tavg', 1 / 10800, 31 * 8), ('Qs_acc', 2, 31 * 8 * 2),
])
def test_gldas_conversiones_y_mes_completo(variable, valor, esperado):
    t = [datetime(2024, 1, 1) + timedelta(hours=3 * i) for i in range(31 * 8)]
    rec = [dict(region='R', sitio='sitio', variable=variable, tiempos=t, valores=[valor] * len(t),
                lat=12, lon=-86, meta={'lat': '12.125', 'lon': '-85.875'})]
    a = GldasDatarods()
    s = a.agregar(rec)[0]
    assert s.valores == pytest.approx([esperado])
    assert 'PUNTO' in s.notas[0]
    rec[0]['valores'][0] = np.nan
    assert a.agregar(rec)[0].valores == [None]
