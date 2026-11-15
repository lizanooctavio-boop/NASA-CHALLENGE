"""Regresión del agente 3: observaciones, unidades, citas, calidad y lectura sin red."""
import calendar
import csv
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / 'backend'))
from clima_nic import recursos  # noqa: E402
from clima_nic.recursos_asia_oceania import ESTUDIOS, LUGARES, SERIES, asia_oceania  # noqa: E402

spec = importlib.util.spec_from_file_location('generar_asia_oceania', RAIZ / 'data/recursos/hallazgos/generar_asia_oceania.py')
generador = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generador)


@pytest.fixture(scope='module')
def integradas():
    invs, entradas = asia_oceania(RAIZ / 'data/recursos/hallazgos')
    assert len(invs) == len(SERIES) == 15
    assert len(entradas) == 2
    return {i['id']: i for i in invs}


@pytest.mark.parametrize('id_,desde,hasta,unidad', [
    ('nivel_mar_funafuti_b', 1994, 2025, 'mm'),
    ('nivel_mar_betio', 1995, 2025, 'mm'),
    ('nivel_mar_lautoka', 1993, 2025, 'mm'),
    ('nivel_mar_manila', 1993, 2022, 'mm'),
    ('nivel_mar_auckland_ii', 1904, 1998, 'mm'),
    ('nivel_mar_global_altimetria', 1993, 2025, 'mm'),
    ('oceano_global_contenido_calor_2000m', 2005, 2025, '10²² J'),
    ('monzon_india_central_lluvia_total', 1951, 2025, 'mm'),
    ('yangtze_lluvia_extrema_verano', 1981, 2025, 'mm'),
    ('mar_japon_temperatura_superficial', 1981, 2025, '°C'),
    ('siberia_temperatura_aire', 1981, 2025, '°C'),
    ('gran_barrera_dhw_northern', 1985, 2025, '°C-weeks'),
    ('gran_barrera_dhw_central', 1985, 2025, '°C-weeks'),
    ('gran_barrera_dhw_southern', 1985, 2025, '°C-weeks'),
])
def test_periodo_unidad_cita_y_datos_reales(integradas, id_, desde, hasta, unidad):
    i = integradas[id_]
    assert i['tiempos'][0] == desde and i['tiempos'][-1] == hasta
    assert i['unidad'] == unidad
    assert i['tendencia']['unidad_pendiente'] == unidad + '/decade'
    assert sum(v is not None for v in i['valores']) >= 10
    assert all(v is None or math.isfinite(v) for v in i['valores'])
    assert ESTUDIOS[SERIES[id_]['estudio']] in i['notas']
    assert i['fuente']['requiere_cuenta'] is False
    assert i['lugar'] in recursos.LUGARES


@pytest.mark.parametrize('id_,signo', [
    ('nivel_mar_global_altimetria', 1), ('oceano_global_contenido_calor_2000m', 1),
    ('mar_japon_temperatura_superficial', 1), ('nivel_mar_auckland_ii', 1),
    ('mar_aral_superficie_agua', -1), ('yangtze_lluvia_extrema_verano', 1),
])
def test_signo_cuando_la_cita_describe_cambio(integradas, id_, signo):
    assert signo * integradas[id_]['tendencia']['sen']['por_decada'] > 0


@pytest.mark.parametrize('id_', ['nivel_mar_funafuti_b', 'nivel_mar_betio', 'nivel_mar_lautoka'])
def test_pacifico_no_mezcla_reconstruccion_historica(integradas, id_):
    i = integradas[id_]
    assert i['tendencia']['veredicto'] == 'tendencia_detectada'
    assert i['tendencia']['sen']['por_decada'] > 0
    assert not any('1950' in n or '51 mm' in n or 'gloplacha' in n for n in i['notas'])
    # El centrado de RLR no modifica la pendiente, recalculada desde el CSV de entrada.
    with (RAIZ / 'data/recursos/hallazgos/asia_oceania_anual.csv').open() as f:
        puntos = [(int(r['anio']), float(r['valor'])) for r in csv.DictReader(f) if r['id'] == id_]
    a, v = zip(*puntos)
    esperado = recursos.tendencia_compacta(a, [x + 7000 for x in v], 'mm')
    assert esperado['sen']['por_decada'] == pytest.approx(i['tendencia']['sen']['por_decada'], abs=.001)


def test_aral_caja_calidad_y_no_volumen(integradas):
    i = integradas['mar_aral_superficie_agua']
    assert 1984 <= i['tiempos'][0] < i['tiempos'][-1] == 2021
    assert i['unidad'] == 'km²'
    assert all(v is None or 0 < v < 200000 for v in i['valores'])
    assert 'study-box' in ' '.join(i['notas'])
    assert '95%' in ' '.join(i['notas'])


def test_sin_archivo_no_inventa_series(tmp_path):
    assert asia_oceania(tmp_path) == ([], [])


@pytest.mark.parametrize('filas', [
    'nivel_mar_betio,2000,1\nnivel_mar_betio,2000,2\n',
    'nivel_mar_betio,2000,nan\n', 'desconocida,2000,1\n',
])
def test_csv_malformado_se_rechaza(tmp_path, filas):
    (tmp_path / 'asia_oceania_anual.csv').write_text('id,anio,valor\n' + filas)
    with pytest.raises(ValueError):
        asia_oceania(tmp_path)


def test_huecos_no_se_interpolan(tmp_path):
    (tmp_path / 'asia_oceania_anual.csv').write_text('id,anio,valor\nnivel_mar_betio,2000,1\nnivel_mar_betio,2002,3\n')
    i = asia_oceania(tmp_path)[0][0]
    assert i['tiempos'] == [2000, 2001, 2002]
    assert i['valores'] == [1, None, 3]
    assert i['tendencia']['veredicto'] == 'datos_insuficientes'


def test_psmsl_ausencias_banderas_y_corte():
    s = '2000;7000;N;000\n2001;-99999;N;000\n2002;7050;N;001\n2003;7100;Y;000\n2026;7200;N;000\n'
    assert generador.filas_psmsl(s, 2025) == [(2000, 7000), (2003, 7100)]
    with pytest.raises(ValueError, match='duplicados'):
        generador.filas_psmsl(s + '2000;7100;N;000\n', 2025)


def test_coral_excluye_anio_incompleto_y_valor_faltante():
    filas = [f'2024 {m:02} {d:02} 29 30 30 30 1 {d / 10} 0' for m in range(1, 13)
             for d in range(1, calendar.monthrange(2024, m)[1] + 1)]
    assert generador.filas_coral('\n'.join(filas), 2025) == [(2024, 3.1)]
    assert generador.filas_coral('\n'.join(filas[:-1]), 2025) == []
    filas[0] = '2024 01 01 29 30 30 30 1 -9999 0'
    assert generador.filas_coral('\n'.join(filas), 2025) == []


def test_cohorte_fija_y_peso_area():
    v = np.array([[[1., np.nan], [3., 9.]], [[3., 900.], [5., 11.]]])
    medias, n = generador.promedio_fijo(v, np.array([0., 60.]))
    assert n == 3
    assert medias == pytest.approx([3.5, 5.5])
    with pytest.raises(ValueError):
        generador.promedio_fijo(np.full((2, 1, 1), np.nan), [0])


def test_matriz_dap_no_confunde_coordenadas_con_datos():
    texto = 'Dataset {}\n---------------------------------------------\nprecip.precip[1][2][2]\n[0][0], 1, 2\n[0][1], -9.96921E36, 4\n'
    v = generador.matriz_ascii(texto, 'precip')
    assert v.shape == (1, 2, 2) and np.isnan(v[0, 1, 0])
    assert v[0, 0].tolist() == [1, 2]
    with pytest.raises(ValueError):
        generador.matriz_ascii(texto + '[0][0], 1, 2\n', 'precip')
    with pytest.raises(ValueError):
        generador.matriz_ascii(texto.replace('[0][1], -9.96921E36, 4\n', ''), 'precip')


def test_lugares_categorias_y_formato_de_citas():
    assert all(k.startswith('ao_') for k in LUGARES)
    assert all(n.startswith('Published check:') and 'doi:10.' in n for n in ESTUDIOS.values())
    assert set(s['categoria'] for s in SERIES.values()) <= {c['id'] for c in recursos.CATEGORIAS}
