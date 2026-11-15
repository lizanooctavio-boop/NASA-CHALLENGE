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
