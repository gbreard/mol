# [FRENTE H P4] Los dos tests del laudo L4 (subordinacion) a nivel de pasadas:
# en v3.6.0 el match() con traductor_activo evalua L3 -> traductor -> resto.
# "Subordinada NO dispara cuando el traductor decidio" es ESTRUCTURAL (el resto
# de reglas ni se evalua si el traductor decide — el smoke de P4 lo verifica
# end-to-end en BD); aca se verifica la mecanica de las pasadas.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'database'))
from match_ofertas_v3 import MatcherV3


def _matcher_stub(reglas):
    m = MatcherV3.__new__(MatcherV3)
    m.business_rules = {'reglas_forzar_isco': reglas}
    m.code_to_occupation = {'9999.1': {'uri': 'u', 'label': 'x', 'esco_label': 'x',
                                       'isco_code': '9999', 'esco_code': '9999.1'}}
    m.verbose = False
    return m


REGLAS = {
    'R_SUB_subordinada': {
        'nombre': 'sub', 'prioridad': 1, 'activa': True,
        'subordinada_al_traductor': True,
        'condicion': {'titulo_contiene_alguno': ['vendedor']},
        'accion': {'forzar_isco': '9999', 'esco_code': '9999.1', 'esco_label': 'x'},
    },
    'R_L3_especializada': {
        'nombre': 'l3', 'prioridad': 1, 'activa': True,
        '_traductor_L3': 'especializada_vecindario',
        'condicion': {'titulo_contiene_alguno': ['vendedor de seguros']},
        'accion': {'forzar_isco': '9999', 'esco_code': '9999.1', 'esco_label': 'x'},
    },
}


def test_L4_subordinada_SI_dispara_en_pasada_resto():
    """Cuando el traductor NO decidio, el flujo llama solo_l3=False: la
    subordinada dispara ahi (sigue viva — ninguna se retira)."""
    m = _matcher_stub(REGLAS)
    r = m._evaluate_rule_only({'titulo_limpio': 'Vendedor'}, solo_l3=False)
    assert r and r['rule_id'] == 'R_SUB_subordinada'


def test_L4_subordinada_NO_esta_en_la_pasada_L3():
    """La pasada previa al traductor (solo_l3=True) NO incluye subordinadas ni
    reglas comunes: si el traductor decide despues, el resto jamas se evalua
    (la ley 'no dispara cuando el traductor decidio', estructural en match())."""
    m = _matcher_stub(REGLAS)
    r = m._evaluate_rule_only({'titulo_limpio': 'Vendedor'}, solo_l3=True)
    assert r is None


def test_L3_precede_en_su_pasada_y_no_se_subordina():
    m = _matcher_stub(REGLAS)
    r = m._evaluate_rule_only({'titulo_limpio': 'Vendedor de seguros'}, solo_l3=True)
    assert r and r['rule_id'] == 'R_L3_especializada'
    # y en la pasada resto NO vuelve a aparecer (no se evalua dos veces)
    r2 = m._evaluate_rule_only({'titulo_limpio': 'Vendedor de seguros'}, solo_l3=False)
    assert r2 is None or r2['rule_id'] != 'R_L3_especializada'
