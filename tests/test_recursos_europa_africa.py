"""Comprueba el contrato de la primera serie regional y la ausencia de archivos."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / 'backend'))
from clima_nic.recursos_europa_africa import europa_africa, ESTUDIOS, LUGARES
from clima_nic import recursos


def test_ausencia_de_csv(tmp_path):
    assert europa_africa(tmp_path) == ([], [])


def test_glambie_europa_serie_y_contraste():
    investigaciones, entradas = europa_africa(RAIZ / 'data/recursos/hallazgos')
    s = investigaciones[0]
    assert s['tiempos'] == list(range(2000, 2024))
    assert s['unidad'] == 'm w.e.'
    assert s['tendencia']['sen']['por_decada'] < 0
    assert abs(s['tendencia']['sen']['por_decada'] + 0.48) < 0.02
    assert ESTUDIOS['glaciares'] in s['notas']
    assert s['lugar'] in recursos.LUGARES
    assert recursos.LUGARES[s['lugar']] == LUGARES[s['lugar']]
    assert entradas[0].is_file()

def test_lagos_serie_completa_y_citas():
    investigaciones, _ = europa_africa(RAIZ / 'data/recursos/hallazgos')
    for zona in ('caspio', 'victoria', 'chad'):
        s = next(x for x in investigaciones if x['id'] == f'nivel_{zona}_grealm')
        assert s['unidad'] == 'm'
        assert s['tiempos'][-1] == 2025
        assert s['tiempos'] == sorted(set(s['tiempos']))
        assert ESTUDIOS[zona] in s['notas']
        if zona == 'victoria':
            assert 2019 in s['tiempos'] and 2020 in s['tiempos']
        if zona == 'caspio':
            assert s['tendencia']['sen']['por_decada'] < 0


def _serie(id_):
    investigaciones, _ = europa_africa(RAIZ / 'data/recursos/hallazgos')
    return next(x for x in investigaciones if x['id'] == id_)


def test_mediterraneo_oisst():
    sst, olas = _serie('mediterraneo_sst'), _serie('mediterraneo_olas_calor')
    for s in (sst, olas):
        assert s['tiempos'] == list(range(1982, 2026))
        assert s['categoria'] == 'costa' and s['lugar'] == 'mediterraneo'
    assert sst['unidad'] == '°C' and olas['unidad'] == 'days'
    assert sst['tendencia']['sen']['por_decada'] > 0  # Pisano et al. 2020: calentamiento
    assert olas['tendencia']['sen']['por_decada'] > 0  # Dayan et al. 2023: más días de ola de calor
    assert all(0 <= v <= 366 for v in olas['valores'])
    assert ESTUDIOS['mediterraneo_sst'] in sst['notas'] and ESTUDIOS['mediterraneo_olas'] in olas['notas']


def test_lluvias_africa_oriental_separadas():
    largas, cortas = _serie('lluvias_largas_africa_oriental'), _serie('lluvias_cortas_africa_oriental')
    for s, clave in ((largas, 'lluvias_largas'), (cortas, 'lluvias_cortas')):
        assert s['tiempos'][0] == 1981 and s['tiempos'][-1] == 2025
        assert s['unidad'] == 'mm' and s['categoria'] == 'lluvia'
        assert ESTUDIOS[clave] in s['notas']
    assert largas['valores'] != cortas['valores']


def test_sahel_chirps_y_cru():
    for id_ in ('lluvia_jjas_sahel_chirps', 'lluvia_jjas_sahel_cru'):
        s = _serie(id_)
        assert s['tiempos'] == list(range(1981, 2026))
        assert s['unidad'] == 'mm'
        assert s['tendencia']['sen']['por_decada'] > 0  # Biasutti 2019: recuperación parcial tras los 80
        assert ESTUDIOS['sahel'] in s['notas']


def test_grace_tigris_eufrates():
    s = _serie('grace_agua_tigris_eufrates')
    assert s['unidad'] == 'cm' and s['categoria'] == 'agua'
    assert s['tiempos'][0] >= 2002 and s['tiempos'][-1] <= 2025
    assert 2017 not in s['tiempos']  # hueco entre GRACE y GRACE-FO
    assert s['tendencia']['sen']['por_decada'] < 0  # Voss et al. 2013: pérdida de agua
    assert ESTUDIOS['grace_oriente'] in s['notas']


def test_citas_con_doi():
    for texto in ESTUDIOS.values():
        assert texto.startswith('Published check:') and 'doi:10.' in texto
